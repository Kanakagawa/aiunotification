# AIUNClient - Асинхронный клиент для получения уведомлений про тревоги в вашем приложении.
**AIUNClient** — Это просто Python класс, который принимает на вход Планировщик задач и Асинхронный класс библиотеки alerts_in_ua (AsyncClient)

## Особенности

- **Асинхронная работа** с API для получения актуальных оповещений.
- **Планировщик задач** для регулярного выполнения проверки уведомлений (каждые 10 секунд по умолчанию).
- **Гибкость**: возможность передавать собственные функции для обработки оповещений и отправки уведомлений.
- **Механизм обновлений**: проверка изменений в оповещениях и обновление данных с учётом заданных условий.
- **Фильтры**: выполнение ваших кастомных фильтров перед вызовом обработчиков.
  
## Установка
Для установки вам потребуется установить зависимости из файла requirements.txt после того как вы склонируете данный репозиторий.
К примеру вы можете склонировать данный репозиторий в папку вашего проекта например utils/aiunotification не забудьте создать __init__.py


## Используйте тесты

```python
import asyncio
import logging
import sys
from os import getenv
from contextlib import suppress

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from alerts_in_ua.async_client import AsyncClient

from client import AIUNClient, NotificationHandler, NotificationAlert
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
    scheduler  = AsyncIOScheduler()
    client_aiu = AsyncClient(token=TOKEN_ALERTS_IN_UA)
    client_aiun = AIUNClient(alert_in_ua_client=client_aiu,
                             scheduler =scheduler,
                             scheduler_interval=5,
                             funcs=[
                                 NotificationHandler.collect(
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
    scheduler .start()
    # Instead of the below code, use aiogram polling or any other event loop.
    # BELOW, THE CODE IS MADE FOR THE TEST.
    print("The program has started. Press Ctrl+C to stop.")
    stop_event = asyncio.Event()
    try:
        await stop_event.wait()
    except KeyboardInterrupt:
        print("Stopping the program...")
        scheduler .shutdown(wait=False)


if __name__ == "__main__":
    with suppress(KeyboardInterrupt, RuntimeError):
        logging.basicConfig(level=logging.INFO, stream=sys.stdout)
        asyncio.run(main=main())



```

В данном коде мы используем тестовые тревоги, для того чтоб не использовать Токены alert.in.ua и просмотреть какие будут входные данные.


## Мой телеграм - https://t.me/iceown
## Мой блог - https://t.me/ic3xblog
