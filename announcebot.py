import asyncio
from typing import Optional, Union
from aiohttp import web
from forest.core import Bot, Message, Response, app
import logging
import phonenumbers as pn
import csv
import os


class AnnounceBot(Bot):
    #def __init__(self):
         ##Init any relevant stuff
        #self.pwd = os.getcwd()
        #pass
         # we need a dir of files of each user's collections, organized somehow
         # 




    # async def do_announce(self, msg: Message):
    #     logging.info(msg.full_text)
    #     logging.info(msg.text)

    #     ##This would be an annouce command
    #     return "What is returned will be the annoucement text"

    # async def do_get_past_announcements(self, message: Message):
    #     # Logic to get past annoucement
    #     return "Annoucements List"

    # async def do_subscribe(self, msg: Message):
    #     try:
    #         receipt = await subscriber_manager(number=message.source)
    #         return "here's a link to the crypto renissance twitch signal channel"
    #     except ConnectionError as e:
    #         return "Subscription error! Please try again"

    async def do_pn(self, msg: Message) -> str:
        logging.info(msg)
        if not msg.attachments:
            return "attach a CSV of phone numbers"
        else:
            relname = msg.attachments[0]['fileName']
            filename = os.getcwd() + "/downloads/" + relname
            with open(filename, 'r') as f:
                output = f.read()

            return relname + '\n' + output
        

    async def do_echo(self, msg: Message) -> str:
        """/imagine <prompt>"""
        logging.info(msg)
        logging.info(msg.full_text)
        logging.info(msg.text)
        logging.info("reached the echo codepath")

        return f"you said {msg.text}"



if __name__ == "__main__":

    @app.on_startup.append
    async def start_wrapper(out_app: web.Application) -> None:
        out_app["bot"] = AnnounceBot()

    web.run_app(app, port=8080, host="0.0.0.0")
