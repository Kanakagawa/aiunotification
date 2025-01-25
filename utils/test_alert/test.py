from dataclasses import dataclass


@dataclass
class TestAlert:
    location_uid: int


def create_test_alert_map(alert_ids: list[int]) -> list[TestAlert]:
    return [TestAlert(location_uid=alert_id)for alert_id in alert_ids]