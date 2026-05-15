import random
import uuid

from locust import HttpUser, between, task


class DeviceApiUser(HttpUser):
    wait_time = between(0.05, 0.3)
    device_count = 5

    def on_start(self) -> None:
        response = self.client.post(
            "/users",
            json={"name": f"load-user-{uuid.uuid4()}"},
            name="POST /users",
        )
        response.raise_for_status()
        self.user_id = response.json()["id"]
        self.device_ids = [str(uuid.uuid4()) for _ in range(self.device_count)]

        for device_id in self.device_ids:
            self.client.post(
                f"/users/{self.user_id}/devices/{device_id}",
                name="POST /users/{user_id}/devices/{device_id}",
            )

    @task(20)
    def collect_device_data(self) -> None:
        device_id = random.choice(self.device_ids)
        self.client.post(
            f"/devices/{device_id}",
            json={
                "x": random.uniform(-100.0, 100.0),
                "y": random.uniform(-100.0, 100.0),
                "z": random.uniform(-100.0, 100.0),
            },
            name="POST /devices/{device_id}",
        )

    @task(4)
    def get_device_analytics(self) -> None:
        device_id = random.choice(self.device_ids)
        self.client.get(
            f"/devices/{device_id}/analytics",
            name="GET /devices/{device_id}/analytics",
        )

    @task(1)
    def get_user_analytics(self) -> None:
        self.client.get(
            f"/users/{self.user_id}/analytics",
            name="GET /users/{user_id}/analytics",
        )
