from execution.queue.redis_queue import RedisTaskQueue
from execution.queue.redis_worker import RedisWorker
from execution.queue.redis_result_store import RedisResultStore

from runtime.activation.constitutional_boot import ConstitutionalRuntime


def execution_fn(request):
    return {
        "status": "success",
        "echo": request["payload"]
    }


def start_worker(base_path):

    runtime = ConstitutionalRuntime(base_path)
    runtime.boot()

    queue = RedisTaskQueue()
    store = RedisResultStore()

    worker = RedisWorker(queue, store, runtime, execution_fn)

    worker.run()


if __name__ == "__main__":
    start_worker("/app")