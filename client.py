import logging

from asyncio import gather
from dataclasses import dataclass
from typing import Callable, Optional

from aiohttp.web_middlewares import middleware
from alerts_in_ua.async_client import AsyncClient
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from utils.test_alert import TestAlert
from map import MAPPING


@dataclass
class NotificationHanlder:
    func: Callable
    kwargs: Optional[dict]
    filter: Optional[Callable]

    @staticmethod
    def collect(func: Callable, kwargs: Optional[dict] = None, custom_filter: Optional[Callable] = None) -> "NotificationHanlder":
        return NotificationHanlder(
            func=func,
            kwargs={} if not kwargs else kwargs,
            filter=custom_filter
        )


@dataclass
class NotificationAlert:
    location_id: int
    title: str
    alert: bool

    @staticmethod
    def from_dict(location_id: int, other_data: dict) -> "NotificationAlert":
        other_data["location_id"] = location_id
        return NotificationAlert(**other_data)


class AIUNClient:
    def __init__(self, alert_in_ua_client: AsyncClient,
                 sheduler: AsyncIOScheduler,
                 funcs: list[NotificationHanlder],
                 sheduler_interval: int = 10,
                 sheduler_max_instances: int = 1000,
                 drop_padding_update: bool = True,
                 test_alert: Optional[TestAlert] = None,
                 global_filter: Optional[Callable] = None):
        self.client = alert_in_ua_client
        self.sheduler = sheduler
        self.funcs = funcs
        self.sheduler_interval = sheduler_interval
        self.sheduler_max_instances = sheduler_max_instances
        self.drop_padding_update = drop_padding_update
        self.wake_up_iteration = False
        self.test_alert = test_alert
        self.global_filter = global_filter

    def add_job(self):
        logging.info(msg=f"Successfully connected {len(self.funcs)} functions")
        self.sheduler.add_job(
            func=self._start_client,
            trigger=IntervalTrigger(seconds=self.sheduler_interval),
            max_instances=self.sheduler_max_instances,
        )

    @staticmethod
    def to_alert_obj(update_alerts: dict) -> list[NotificationAlert]:
        update_data_obj = []
        for location_id, other_data in update_alerts.items():
            update_data_obj.append(NotificationAlert.from_dict(location_id, other_data))

        return update_data_obj

    async def send_notification(self, update_alerts: list[NotificationAlert]):
        logging.info(msg=f"Map update, {len(update_alerts)} updates recorded")
        handlers = await self._use_filters(update_alerts)
        if not handlers:
            return
        callable_task = [
             notif_handler.func(update_alerts, **notif_handler.kwargs) for notif_handler in handlers
        ]
        await gather(*callable_task)

    async def _start_client(self):
        if self.test_alert:
            active_alerts = self.test_alert
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
        if self.global_filter:
            update_alerts = await self.global_filter(update_alerts)
            if not update_alerts: return
        await self.send_notification(self.to_alert_obj(update_alerts))

    async def _use_filters(self, update_alerts: list[NotificationAlert]) -> list[NotificationHanlder]:
        handlers = []
        for handler in self.funcs:
            if handler.filter is not None:
                use_filter = await handler.filter(update_alerts)
                if use_filter:
                    handlers.append(handler)
                else:
                    continue
            else:
                handlers.append(handler)
        return handlers


