from queue import Queue


class TaskQueue:

    def __init__(self):
        self.queue = Queue()

    def push(self, task):
        self.queue.put(task)

    def pop(self):
        return self.queue.get()

    def is_empty(self):
        return self.queue.empty()
