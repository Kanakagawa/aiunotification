from typing import Callable
from alerts_in_ua.async_client import AsyncClient

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from map import MAPPING


class AIUNClient:

    def __init__(self, alert_in_ua_client: AsyncClient,
                 sheduler: AsyncIOScheduler,
                 funcs: list[Callable],
                 sheduler_interval: int = 20,
                 sheduler_max_instances: int = 1000,
                 drop_padding_update: bool = True):
        self.client = alert_in_ua_client
        self.sheduler = sheduler
        self.drop_padding_update = drop_padding_update
        self.funcs = funcs
        self.wake_up_iteration = False
        self.sheduler_interval = sheduler_interval
        self.sheduler_max_instances = sheduler_max_instances

    async def start(self):
        self.sheduler.add_job(
            func=self._start_client,
            trigger=IntervalTrigger(seconds=self.sheduler_interval),
            max_instances=self.sheduler_max_instances,
        )

    async def _start_client(self):
        active_alerts = await self.client.get_active_alerts()
        await self._parse_data(active_alerts=active_alerts)

    async def _parse_data(self, active_alerts: list):
        update_alerts: dict = {}

        kyiv_alert = None
        kyiv_region_alert = None
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
            if uid == 34:
                kyiv_alert = is_alert
            elif uid == 14:
                kyiv_region_alert = is_alert
            else:
                pass

        if kyiv_alert is not None or kyiv_region_alert is not None:
            if kyiv_alert or kyiv_region_alert:
                if MAPPING[32]["alert"] is False:
                    MAPPING[32]["alert"] = True
                    update_alerts[32] = {"id": 32, "alert": True, "name": "м. Київ або область"}
            else:
                if MAPPING[32]["alert"] is True:
                    MAPPING[32]["alert"] = False
                    update_alerts[32] = {"id": 32, "alert": False, "name": "м. Київ або область"}
        if self.wake_up_iteration is False and self.drop_padding_update:
            self.wake_up_iteration = True
            return
        if not update_alerts:
            return
        await self.send_notification(update_alerts=update_alerts)


    async def send_notification(self, update_alerts: dict):
        for foo in self.funcs:
            await foo(update_alerts)
