import logging

from asyncio import gather
from typing import Callable
from alerts_in_ua.async_client import AsyncClient
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from map import MAPPING

class TestAlert:
    location_uid: int = 28


class AIUNClient:
    def __init__(self, alert_in_ua_client: AsyncClient,
                 sheduler: AsyncIOScheduler,
                 funcs: list[Callable],
                 sheduler_interval: int = 10,
                 sheduler_max_instances: int = 1000,
                 drop_padding_update: bool = True,
                 test_alert: bool = False):
        self.client = alert_in_ua_client
        self.sheduler = sheduler
        self.funcs = funcs
        self.sheduler_interval = sheduler_interval
        self.sheduler_max_instances = sheduler_max_instances
        self.drop_padding_update = drop_padding_update
        self.wake_up_iteration = False
        self.test_alert = test_alert

    def add_job(self):
        logging.info(msg=f"Successfully connected {len(self.funcs)} functions")
        self.sheduler.add_job(
            func=self._start_client,
            trigger=IntervalTrigger(seconds=self.sheduler_interval),
            max_instances=self.sheduler_max_instances,
        )

    async def _start_client(self):
        if self.test_alert:
            active_alerts = [TestAlert()]
        else:
            active_alerts = await self.client.get_active_alerts()
        await self._parse_data(active_alerts)

    async def _parse_data(self, active_alerts: list):
        update_alerts: dict = {}
        active_alerts_ids = [int(alert.location_uid) for alert in active_alerts]
        for uid, value in MAPPING.items():
            if uid in active_alerts_ids and value["alert"] is False:
                is_alert = True
            else:
                if MAPPING[uid]["alert"] is True and uid not in active_alerts_ids:
                    is_alert = False
                else:
                    continue
            MAPPING[uid]["alert"] = is_alert
            update_alerts[uid] = MAPPING[uid]

        if not update_alerts or (not self.wake_up_iteration and self.drop_padding_update):
            if not self.wake_up_iteration:
                self.wake_up_iteration = True
            return
        await self.send_notification(update_alerts)

    async def send_notification(self, update_alerts: dict):
        logging.info(msg=f"Map update, {len(update_alerts)} updates recorded")
        callable_task = [
            func(update_alerts) for func in self.funcs
        ]
        await gather(*callable_task)
