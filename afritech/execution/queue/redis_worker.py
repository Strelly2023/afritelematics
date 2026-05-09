import time
from execution.queue.task_models import ExecutionTask, TaskStatus


class RedisWorker:

    def __init__(self, queue, store, runtime, execution_fn, event_bus=None):
        self.queue = queue
        self.store = store
        self.runtime = runtime
        self.execution_fn = execution_fn
        self.event_bus = event_bus

    def run(self):

        print("✅ Worker started")

        while True:

            data = self.queue.pop()

            task = ExecutionTask(data["payload"])
            task.id = data["id"]

            try:
                task.status = TaskStatus.RUNNING

                result = self.runtime.execute(
                    task.payload,
                    self.execution_fn
                )

                task.result = result
                task.status = TaskStatus.COMPLETED

                self._emit({
                    "type": "TASK_COMPLETED",
                    "task_id": task.id
                })

            except Exception as e:
                task.status = TaskStatus.FAILED
                task.error = str(e)

                self._emit({
                    "type": "TASK_FAILED",
                    "task_id": task.id
                })

            self.store.save(task.to_dict())
            time.sleep(0.01)

    def _emit(self, event):
        if self.event_bus:
            import asyncio
            asyncio.run(self.event_bus.publish(event))
