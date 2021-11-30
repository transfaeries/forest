from collections import defaultdict
from typing import NewType, Optional
import logging
from forest.core import Message, PayBot, Response, run_bot

Prompt = NewType("Prompt", str)
# probably has a validate thing
User = NewType("User", str)


class FormBot(PayBot):
    spec: list[Prompt] = []
    issued_prompt_for_user: dict[User, Prompt] = {}
    next_states_for_user: dict[User, list[Prompt]] = defaultdict(list)
    user_data: dict[User, dict[Prompt, str]] = defaultdict(dict)

    def load_spec(self, spec: str) -> None:
        self.spec = [
            Prompt(spec.removeprefix("? "))
            for spec in spec.split("\n")
            if spec.startswith("?")
        ]

    async def do_load_spec(self, msg: Message) -> Response:
        self.load_spec(msg.text)
        return "loaded spec, only processing ?"

    # maybe this could take FormTakingUser?
    def issue_prompt(self, user: User) -> Optional[Prompt]:
        if len(self.next_states_for_user[user]):
            next_prompt = self.next_states_for_user[user].pop(0)
            self.issued_prompt_for_user[user] = next_prompt
            return next_prompt
        return None

    # maybe this could take PromptedUser?
    def use_prompt_response(self, user: User, resp: str) -> bool:
        if user in self.issued_prompt_for_user:
            prompt = self.issued_prompt_for_user.pop(user)
            self.user_data[user][prompt] = resp
            return True
        return False

    async def default(self, message: Message) -> Response:
        logging.info(message)
        if not message.text or message.group:
            return None
        user = User(message.source)
        if user not in self.next_states_for_user:
            self.next_states_for_user[user] = list(self.spec)
        # validate input somehow
        prompt_used = self.use_prompt_response(user, message.text)
        if prompt_used:
            ack = f"recorded: {message.text}"
        else:
            ack = f"{message.text} yourself"
        maybe_prompt = self.issue_prompt(user)
        if maybe_prompt:
            return f"{ack}. {maybe_prompt}"
        return [
            "thanks for filling out this form. you said:",
            self.user_data[user],
        ]


if __name__ == "__main__":
    run_bot(FormBot)
