class TaskResultStore:

    def __init__(self):
        self.results = {}

    def save(self, task):
        self.results[task.id] = task

    def get(self, task_id):
        return self.results.get(task_id)