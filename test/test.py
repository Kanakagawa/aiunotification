import asyncio
import logging
import sys
from os import getenv
from client import AIUNClient, NotificationHanlder
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from alerts_in_ua.async_client import AsyncClient


TOKEN_ALERTS_IN_UA = getenv("TOKEN")


async def alerts_handler(data, my_arg: bool):
    logging.info(msg=f"{data=}\n{my_arg=}")


async def main():
    sheduler = AsyncIOScheduler()
    client_aiu = AsyncClient(token=TOKEN_ALERTS_IN_UA)
    client_aiun = AIUNClient(alert_in_ua_client=client_aiu,
                             sheduler=sheduler,
                             sheduler_interval=5,
                             funcs=[
                                 NotificationHanlder.compile(
                                     func=alerts_handler,
                                     kwargs={
                                         "my_arg": True
                                     }
                                 )
                             ],
                             drop_padding_update=False,
                             test_alert=True)
    client_aiun.add_job()
    sheduler.start()
    # Instead of the below code, use aiogram polling or any other event loop.
    # BELOW, THE CODE IS MADE FOR THE TEST.
    print("The program has started. Press Ctrl+C to stop.")
    stop_event = asyncio.Event()
    try:
        await stop_event.wait()
    except KeyboardInterrupt:
        print("Stopping the program...")
        sheduler.shutdown(wait=False)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main=main())
