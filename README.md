# AIUNClient - Асинхронный клиент для получения уведомлений про тревоги в вашем приложении.
**AIUNClient** — Это просто Python класс, который принимает на вход Планировщик задач и Асинхронный класс библиотеки alerts_in_ua (AsyncClient)

## Особенности

- **Асинхронная работа** с API для получения актуальных оповещений.
- **Планировщик задач** для регулярного выполнения проверки уведомлений (каждые 20 секунд по умолчанию).
- **Гибкость**: возможность передавать собственные функции для обработки оповещений и отправки уведомлений.
- **Механизм обновлений**: проверка изменений в оповещениях и обновление данных с учётом заданных условий.
  
## Установка
Для установки вам потребуется установить зависимости из файла requirements.txt после того как вы склонируете данный репозиторий.
К примеру вы можете склонировать данный репозиторий в папку вашего проекта например modules/aiunotification не забудьте создать __init__.py


## Использование

```python
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


```

