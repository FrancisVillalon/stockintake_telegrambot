import asyncio
import telegram
import tomllib
from pprint import pprint

with open("./config.toml", "rb") as f:
    data = tomllib.load(f)
    tele_key = data["telegram_bot"]["api_key"]


async def main():
    bot = telegram.Bot(tele_key)
    async with bot:
        bot_updates = await bot.get_updates()
        if bot_updates:
            for update in bot_updates:
                print(update["message"]["chat"])


if __name__ == "__main__":
    asyncio.run(main())
