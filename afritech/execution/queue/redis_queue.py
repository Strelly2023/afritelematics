import json
import redis


class RedisTaskQueue:

    def __init__(self, url="redis://redis:6379/0"):
        self.client = redis.Redis.from_url(url)

    def push(self, task):
        self.client.rpush("afritech:tasks", json.dumps(task))

    def pop(self):
        _, data = self.client.blpop("afritech:tasks")
        return json.loads(data)