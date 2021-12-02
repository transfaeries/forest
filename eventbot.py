from collections import defaultdict
from typing import NewType, Optional, NamedTuple, Literal
import logging
from forest.core import Message, PayBot, Response, run_bot

shoe_spec = """! Today we're selling a limited number of hand-painted shoes!
-> https://lh5.googleusercontent.com/ZyXMq3SnkOjvTSbHsMoLCugs_wAU7BKQlLhIWokrAV5XfCVHq3SP4TN8pnnEk1LTqMbkS8-cB6i8zHkEXve9Sa_5uBqWaRlqf2qryjueXPPHJLpHv_QHqtOUHhEBjQsSlA=w640
entry.1941031617🔜? Which color would you like to order?
 - Please specify the color, referencing the above image. 
  - (Rehu, Arazan, Ketu, Kaspian, Lapis)
entry.1810633354🔜? What size shoes do you wear? (specify M/F as needed)
entry.599451360🔜? What name should we put on your package?
entry.1742808960🔜? What is your mailing address?
entry.1022864849🔜$ $200 MOB
entry.1870700300🔜? Any questions or comments?
https://docs.google.com/forms/d/e/1FAIpQLSdY53W49HhpwZ3g6H_w4GxrnPbVZt-xPvoen-KkhTHp4l72bg/formResponse 🔜 ? confirm"""


test_spec = """
entry.1097373330🔜? why does what who
entry.2131770336🔜? have you stopped drinking litres of vodka every morning yet?
https://docs.google.com/forms/d/e/1FAIpQLSfzlSloyv4w8SmLNR4XSSnSlKJ7WFa0wPMvEJO-5cK-Zb6ZdQ/formResponse🔜? confirm
"""

Action = Literal["!", "?", "$"]
Prompt = NamedTuple("Prompt", [("qid", str), ("action", Action), ("text", str)])
User = NewType("User", str)

# moneyprompt - metadata, message, value


def load_spec(spec: str) -> list[Prompt]:
    return [
        Prompt(qid, *text.split(" ", 1))  # type: ignore
        for qid, text in [
            # gauranteed safe seperator, no escaping necessary
            line.split("🔜", 1)
            for line in spec.split("\n")
            if "🔜" in line
        ]
        if text.startswith("?")
    ]


class FormBot(PayBot):
    spec: list[Prompt] = load_spec(test_spec)
    issued_prompt_for_user: dict[User, Prompt] = {}
    next_states_for_user: dict[User, list[Prompt]] = defaultdict(list)
    user_data: dict[User, dict[str, str]] = defaultdict(dict)

    """create table if not exists form_messages
    (ts timestamp, source text, message text, question text"""

    async def do_get_spec(self, _: Message) -> str:
        return repr(self.spec)

    async def do_load_spec(self, msg: Message) -> Response:
        self.spec = load_spec(msg.text)
        return "loaded spec, only processing ?"

    # maybe this could take FormTakingUser?
    def issue_prompt_text(self, user: User) -> Optional[str]:
        if len(self.next_states_for_user[user]):
            next_prompt = self.next_states_for_user[user].pop(0)
            self.issued_prompt_for_user[user] = next_prompt
            if next_prompt.action == "$":
                return f"Please pay {next_prompt.text}"
            if next_prompt.action == "?":
                return next_prompt.text
        return None

    # maybe this could take PromptedUser?
    async def use_prompt_response(self, user: User, resp: str) -> bool:
        logging.info("using response %s", resp)
        if user in self.issued_prompt_for_user:
            prompt = self.issued_prompt_for_user.pop(user)
            logging.info("using prompt %s", prompt)
            if prompt.text == "confirm" and resp.lower() in "yes":
                logging.info("submitting: %s", self.user_data[user])
                logging.info(
                    await self.client_session.post(
                        prompt.qid, data=self.user_data[user]
                    )
                )
                return True
            self.user_data[user][prompt.qid] = resp
            return True
        return False

    async def next_question(self, message: Message) -> Response:
        user = User(message.source)
        if user not in self.next_states_for_user:
            self.next_states_for_user[user] = list(self.spec)
        # validate input somehow
        prompt_used = await self.use_prompt_response(user, message.text)
        if prompt_used:
            ack = f"recorded: {message.text}"
        else:
            ack = f"{message.text} yourself"
        logging.info(self.next_states_for_user[user])
        maybe_prompt = self.issue_prompt_text(user)
        if maybe_prompt:
            logging.info(maybe_prompt)
            if maybe_prompt == "confirm":
                return [
                    "thanks for filling out this form. you said:",
                    self.user_data[user],
                    "Submit?",
                ]
            return f"{ack}. {maybe_prompt}"
        return "thanks for filling out this form"

    async def default(self, message: Message) -> Response:
        if not message.text or message.group:
            return None
        return await self.next_question(message)

    # issue: handling
    async def payment_response(self, msg: Message, amount_pmob: int) -> Response:
        del amount_pmob
        pay_prompt = self.issued_prompt_for_user.get(User(msg.source))
        if not pay_prompt or pay_prompt.action != "$":
            return "not sure what that payment was for"
        price = float(pay_prompt.text.removesuffix(" MOB").strip().lstrip("$").strip())
        diff = await self.get_user_balance(msg.source) - price
        if diff < price * -0.005:
            diff_mob = await self.mobster.usd2mob(abs(diff))
            return f"Another {abs(diff)} USD ({diff_mob} MOB) buy a phone number"
        if diff < price * 0.005:  # tolerate half a percent difference
            resp = f"Thank you for paying! You've overpayed by {diff} USD. Contact an administrator for a refund"
        else:
            resp = "Payment acknowledged"
        await self.mobster.ledger_manager.put_usd_tx(
            msg.source, -int(price * 100), "form payment"
        )
        self.user_data[User(msg.source)]["pay"] = msg.payment["receipt"]
        await self.respond(msg, resp)
        return await self.next_question(msg)


if __name__ == "__main__":
    run_bot(FormBot)
