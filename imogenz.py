#!/usr/bin/python3.9
import asyncio
import logging
from typing import Optional
from aiohttp import web
from forest.core import Bot, Message, Response, app



class Echo(Bot):

    async def do_echo(self, msg: Message) -> str:
        logging.info(msg.full_text)
        logging.info(msg.text)
        return f"you said {msg.text}"

if __name__ == "__main__":

    @app.on_startup.append
    async def start_wrapper(out_app: web.Application) -> None:
        out_app["bot"] = Echo()

    web.run_app(app, port=8080, host="0.0.0.0")
