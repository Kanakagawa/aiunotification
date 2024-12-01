import asyncio

from client import AIUNClient
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from alerts_in_ua.async_client import AsyncClient


async def alerts(data):
    print(data)


async def main():
    sheduler = AsyncIOScheduler()
    client_aiu = AsyncClient(token="Your token alerts.in.ua")
    client_aiun = AIUNClient(alert_in_ua_client=client_aiu,
                             sheduler=sheduler,
                             funcs=[alerts],
                             drop_padding_update=False)
    await client_aiun.start()
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
    asyncio.run(main=main())
