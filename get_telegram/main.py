import configparser
import os
import asyncio
import functools
import aiofiles
import json

from pyrogram import Client

config = configparser.ConfigParser()
config.read("config.ini")

api_id = config["Telegram"]["api_id"]
api_hash = config["Telegram"]["api_hash"]
session_file = config["Telegram"]["session_file"]
channels = list(map(int, filter(None, config["Telegram"]["channels"].split(','))))


@functools.lru_cache(maxsize=None)
async def read_json(json_file="posts.json"):
    if not os.path.exists(json_file):
        async with aiofiles.open(json_file, 'w') as f:
            await f.write(json.dumps({"retries": 0}))

    async with aiofiles.open(json_file, "r") as f:
        json_data = json.loads(await f.read())

        return json_data


@functools.lru_cache(maxsize=None)
async def write_json(key, data, json_file="posts.json"):
    async with aiofiles.open(json_file, "r") as f:
        rj = json.loads(await f.read())

    rj[key] = data

    async with aiofiles.open(json_file, "w") as f:
        json_data = json.dumps(rj)
        await f.write(json_data)


async def get_last_message(channel_ids, limit=1):
    async with Client(session_file) as app:
        rj = await read_json()
        retries = rj["retries"]

        channel_id = channel_ids[retries]
        if channel_id == len(channels):
            await write_json(
                key="retries",
                data=0
            )

        async for message in app.get_chat_history(channel_id, limit=limit, offset_id=-limit):
            if channel_id < len(channels):
                new_v = rj["retries"] + 1
                await write_json(
                    key="retries",
                    data=new_v
                )

            return channel_id, message.date, message.text


async def get_new_messages():
    messages = list()

    for i in range(len(channels)):
        channel_id, date, message = await get_last_message(channels)
        rj = await read_json()
        if rj[channel_id][0] != date:
            messages.append(message)

        await write_json(key=channel_id, data=(str(date), message))

    return messages


asyncio.run(get_new_messages())
