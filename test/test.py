import asyncio
import logging
import sys
from os import getenv
from contextlib import suppress

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from alerts_in_ua.async_client import AsyncClient

from client import AIUNClient, NotificationHanlder, NotificationAlert
from utils.test_alert import create_test_alert_map

TOKEN_ALERTS_IN_UA = getenv("TOKEN")


async def handler_filter(n_data: list[NotificationAlert]) -> bool:
    """
    Use an internal filter for the handler, your filter should return True or False
    """
    return True

async def global_filter(n_data: dict[int:dict]) -> dict:
    """

    Use a global filter to run code before the client sends notifications to handlers.

    The global filter should return the received date back. Internal data can be changed, but new ones cannot be added.

    """
    return n_data


async def alerts_handler(n_data: list[NotificationAlert], my_arg: bool):
    logging.info(msg=f"{n_data=}\n{my_arg=}")


async def main():
    sheduler = AsyncIOScheduler()
    client_aiu = AsyncClient(token=TOKEN_ALERTS_IN_UA)
    client_aiun = AIUNClient(alert_in_ua_client=client_aiu,
                             sheduler=sheduler,
                             sheduler_interval=5,
                             funcs=[
                                 NotificationHanlder.collect(
                                     func=alerts_handler,
                                     kwargs={
                                         "my_arg": True
                                     },
                                     custom_filter=handler_filter
                                 )
                             ],
                             global_filter=global_filter,
                             drop_padding_update=False,
                             test_alert=create_test_alert_map(alert_ids=[
                                 31, 14, 15, 20
                             ]))
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
    with suppress(KeyboardInterrupt, RuntimeError):
        logging.basicConfig(level=logging.INFO, stream=sys.stdout)
        asyncio.run(main=main())
