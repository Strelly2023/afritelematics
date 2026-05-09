class EventBus:

    def __init__(self):
        self.subscribers = []

    def subscribe(self, fn):
        self.subscribers.append(fn)

    async def publish(self, event: dict):
        for fn in self.subscribers:
            await fn(event)
