import json
import redis

class RedisResultStore:

    def __init__(self, url="redis://localhost:6379/0"):
        self.client = redis.Redis.from_url(url)

    def save(self, task):
        self.client.set(task["id"], json.dumps(task))

    def get(self, task_id):
        data = self.client.get(task_id)
        return json.loads(data) if data else None
    def get_all_entries(self):
        keys = self.client.keys("*")
        entries = []
        for key in keys:            
            data = self.client.get(key)
            if data:
                entries.append(json.loads(data))
        return entries  