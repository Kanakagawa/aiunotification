import logging

from asyncio import gather
from dataclasses import dataclass
from typing import Callable, Optional

from alerts_in_ua.async_client import AsyncClient
from alerts_in_ua.errors import UnauthorizedError
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from utils.test_alert import TestAlert
from map import MAPPING


@dataclass
class NotificationHandler:
    func: Callable
    kwargs: Optional[dict]
    filter: Optional[Callable]

    @staticmethod
    def collect(func: Callable, kwargs: Optional[dict] = None, custom_filter: Optional[Callable] = None) -> "NotificationHandler":
        """
            NotificationHanlder defines a structure for handling notifications, including
            the processing function, optional arguments, and an optional filter.

            Attributes:
                func (Callable): The function to be executed for processing notifications.
                    This function is called with the notification data and any additional
                    arguments specified in `kwargs`.

                kwargs (Optional[dict]): A dictionary of keyword arguments passed to `func`.
                    Default is an empty dictionary if not provided.

                custom_filter (Optional[Callable]): An optional callable (filter function) used to
                    determine whether the handler should process the notification data.
                    The filter receives the notification data and returns a boolean.
        """
        return NotificationHandler(
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
    """
        AIUNClient manages notification handling, including fetching alerts, filtering,
        and executing notification tasks periodically using an asynchronous scheduler.

        Args:
            alert_in_ua_client (AsyncClient): The asynchronous client instance responsible
                for interacting with the alert system's API.

            scheduler (AsyncIOScheduler): The scheduler instance used for periodically
                running tasks, such as fetching and processing alert data.

            funcs (list[NotificationHandler]): A list of notification handler objects. Each
                handler defines a `func` to process notifications and an optional `filter` to
                determine whether the handler should run.

            scheduler_interval (int, optional): Interval in seconds between task executions
                scheduled by the `sheduler`. Default is 10 seconds.

            scheduler_max_instances (int, optional): Maximum number of concurrent task
                instances that the `sheduler` can execute. Default is 1000.

            drop_padding_update (bool, optional): Determines whether to skip updates that
                occur during the initial wake-up iteration. Default is True.

            test_alert (Optional[TestAlert], optional): A mock or pre-defined alert object for
                testing purposes. If provided, it will be used instead of fetching real alerts
                from the `alert_in_ua_client`. Default is None.

            global_filter (Optional[Callable], optional): A global filter function applied
                to all updates. It takes the raw update data and returns the filtered data
                or an empty result if no updates should be processed. Default is None.
        """
    def __init__(self, alert_in_ua_client: AsyncClient,
                 scheduler: AsyncIOScheduler,
                 funcs: list[NotificationHandler],
                 scheduler_interval: int = 10,
                 scheduler_max_instances: int = 1000,
                 drop_padding_update: bool = True,
                 test_alert: Optional[list[TestAlert]] = None,
                 global_filter: Optional[Callable] = None):
        self.client = alert_in_ua_client
        self.scheduler = scheduler
        self.funcs = funcs
        self.scheduler_interval = scheduler_interval
        self.scheduler_max_instances = scheduler_max_instances
        self.drop_padding_update = drop_padding_update
        self.wake_up_iteration = False
        self.test_alert = test_alert
        self.global_filter = global_filter

    def add_job(self):
        logging.info(msg=f"Successfully connected {len(self.funcs)} functions")
        self.scheduler.add_job(
            func=self._start_client,
            trigger=IntervalTrigger(seconds=self.scheduler_interval),
            max_instances=self.scheduler_max_instances,
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
        try:
            if self.test_alert:
                active_alerts = self.test_alert
            else:
                active_alerts = await self.client.get_active_alerts()
                logging.info(msg=f"Active Alerts: {[alert.location_title for alert in active_alerts]}")
            await self._parse_data(active_alerts)

        except UnauthorizedError:
            logging.error(msg="Invalid API token. HTTP Code:401")
            await self.scheduler.shutdown()

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
            if not update_alerts: return
            update_alerts = await self.global_filter(update_alerts)
        await self.send_notification(self.to_alert_obj(update_alerts))

    async def _use_filters(self, update_alerts: list[NotificationAlert]) -> list[NotificationHandler]:
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


