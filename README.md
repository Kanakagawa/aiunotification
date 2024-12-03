# AIUNClient - Асинхронный клиент для получения уведомлений про тревоги в вашем приложении.
**AIUNClient** — Это просто Python класс, который принимает на вход Планировщик задач и Асинхронный класс библиотеки alerts_in_ua (AsyncClient)

## Особенности

- **Асинхронная работа** с API для получения актуальных оповещений.
- **Планировщик задач** для регулярного выполнения проверки уведомлений (каждые 20 секунд по умолчанию).
- **Гибкость**: возможность передавать собственные функции для обработки оповещений и отправки уведомлений.
- **Механизм обновлений**: проверка изменений в оповещениях и обновление данных с учётом заданных условий.
  
## Установка
Для установки вам потребуется установить зависимости из файла requirements.txt после того как вы склонируете данный репозиторий.
К примеру вы можете склонировать данный репозиторий в папку вашего проекта например models/aiunotification не забудьте создать __init__.py


## Использование

```python
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
                                 NotificationHanlder.collect(
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
```

## Мой телеграм - t.me/iceown
## Мой блог - t.me/ic3xblog