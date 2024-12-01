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
        self.funcs = funcs
        self.sheduler_interval = sheduler_interval
        self.sheduler_max_instances = sheduler_max_instances
        self.drop_padding_update = drop_padding_update
        self.wake_up_iteration = False

    async def start(self):
        self.sheduler.add_job(
            func=self._start_client,
            trigger=IntervalTrigger(seconds=self.sheduler_interval),
            max_instances=self.sheduler_max_instances,
        )

    async def _start_client(self):
        active_alerts = await self.client.get_active_alerts()
        await self._parse_data(active_alerts)

    async def _parse_data(self, active_alerts: list):
        update_alerts = {}
        active_alerts_ids = [int(alert.location_uid) for alert in active_alerts]
        for uid, value in MAPPING.items():
            is_alert = self._should_alert(uid, value, active_alerts_ids)
            if is_alert is not None:
                MAPPING[uid]["alert"] = is_alert
                update_alerts[uid] = MAPPING[uid]
        self._handle_kyiv_alerts(update_alerts)
        if not update_alerts or (not self.wake_up_iteration and self.drop_padding_update):
            if not self.wake_up_iteration:
                self.wake_up_iteration = True
            return
        await self.send_notification(update_alerts)

    @staticmethod
    def _should_alert(uid: int, value: dict, active_alerts_ids: list) -> bool:
        if uid in active_alerts_ids and not value["alert"]:
            return True
        elif uid not in active_alerts_ids and value["alert"]:
            return False
        return None

    def _handle_kyiv_alerts(self, update_alerts: dict):
        kyiv_alert = MAPPING.get(34, {}).get("alert", False)
        kyiv_region_alert = MAPPING.get(14, {}).get("alert", False)

        if kyiv_alert or kyiv_region_alert:
            self._update_kyiv_alert(True, update_alerts)
        else:
            self._update_kyiv_alert(False, update_alerts)

    @staticmethod
    def _update_kyiv_alert(is_alert: bool, update_alerts: dict):
        if MAPPING[32]["alert"] != is_alert:
            MAPPING[32]["alert"] = is_alert
            update_alerts[32] = {"id": 32, "alert": is_alert, "name": "м. Київ або область"}

    async def send_notification(self, update_alerts: dict):
        for func in self.funcs:
            await func(update_alerts)
