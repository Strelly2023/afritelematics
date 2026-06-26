function uid(prefix = "queue") {
  return `${prefix}-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

const DEFAULT_QUEUES = ["decision", "projection", "notification", "synchronization", "analytics", "ai", "audit"];

function normalizeTask(task = {}, queue) {
  return {
    id: task.id || uid(queue),
    queue,
    type: task.type || "runtime.task",
    priority: Number.isFinite(Number(task.priority)) ? Number(task.priority) : 0,
    deadline: task.deadline || null,
    retries: Number.isFinite(Number(task.retries)) ? Number(task.retries) : 0,
    backoffMs: Number.isFinite(Number(task.backoffMs)) ? Number(task.backoffMs) : 0,
    circuit: task.circuit || "closed",
    payload: task.payload || {},
    source: task.source || "runtime",
    createdAt: task.createdAt || new Date().toISOString(),
    updatedAt: task.updatedAt || new Date().toISOString(),
  };
}

export function createRuntimeScheduler(seedQueues = {}) {
  const queues = Object.fromEntries(DEFAULT_QUEUES.map((name) => [name, []]));
  const deadLetters = [];
  const metrics = Object.fromEntries(DEFAULT_QUEUES.map((name) => [name, { enqueued: 0, processed: 0, failed: 0 }]));
  const listeners = new Set();

  Object.entries(seedQueues || {}).forEach(([name, tasks]) => {
    if (queues[name]) {
      queues[name] = Array.isArray(tasks) ? tasks.map((task) => normalizeTask(task, name)) : [];
    }
  });

  const notify = (snapshot) => {
    listeners.forEach((listener) => {
      try {
        listener(snapshot);
      } catch {
        // ignore listener failures
      }
    });
  };

  const enqueue = (queueName, task = {}) => {
    const name = queues[queueName] ? queueName : "projection";
    const entry = normalizeTask(task, name);
    queues[name].push(entry);
    queues[name].sort((left, right) => right.priority - left.priority || left.createdAt.localeCompare(right.createdAt));
    metrics[name].enqueued += 1;
    notify({ type: "enqueued", queue: name, task: entry, metrics: getSnapshot().metrics });
    return entry;
  };

  const drain = (queueName = "projection", limit = 1) => {
    const name = queues[queueName] ? queueName : "projection";
    const batch = queues[name].splice(0, Math.max(0, limit));
    metrics[name].processed += batch.length;
    notify({ type: "drained", queue: name, tasks: batch, metrics: getSnapshot().metrics });
    return batch;
  };

  const fail = (queueName = "projection", taskId = null, reason = "unknown") => {
    const name = queues[queueName] ? queueName : "projection";
    metrics[name].failed += 1;
    const task = queues[name].find((item) => item.id === taskId);
    if (task) {
      task.circuit = "open";
      task.retries += 1;
      task.updatedAt = new Date().toISOString();
      task.failureReason = reason;
    }
    if (task && task.retries >= 3) {
      deadLetters.push({
        ...task,
        queue: name,
        deadLetterReason: reason,
        deadLetterAt: new Date().toISOString(),
      });
      queues[name] = queues[name].filter((item) => item.id !== taskId);
    }
    notify({ type: "failed", queue: name, taskId, reason, metrics: getSnapshot().metrics, deadLetters: [...deadLetters] });
    return task || null;
  };

  const complete = (queueName = "projection", taskId = null) => {
    const name = queues[queueName] ? queueName : "projection";
    const task = queues[name].find((item) => item.id === taskId);
    if (!task) {
      return null;
    }
    queues[name] = queues[name].filter((item) => item.id !== taskId);
    metrics[name].processed += 1;
    notify({ type: "completed", queue: name, taskId, metrics: getSnapshot().metrics });
    return task;
  };

  const retry = (queueName = "projection", taskId = null) => {
    const name = queues[queueName] ? queueName : "projection";
    const task = queues[name].find((item) => item.id === taskId);
    if (!task) {
      return null;
    }
    task.retries += 1;
    task.circuit = "half-open";
    task.backoffMs = Math.max(1000, (task.backoffMs || 1000) * 2);
    task.updatedAt = new Date().toISOString();
    notify({ type: "retried", queue: name, taskId, metrics: getSnapshot().metrics });
    return task;
  };

  const cancel = (queueName = "projection", taskId = null, reason = "cancelled") => {
    const name = queues[queueName] ? queueName : "projection";
    const task = queues[name].find((item) => item.id === taskId);
    if (!task) {
      return null;
    }
    queues[name] = queues[name].filter((item) => item.id !== taskId);
    deadLetters.push({
      ...task,
      queue: name,
      deadLetterReason: reason,
      deadLetterAt: new Date().toISOString(),
      cancelled: true,
    });
    notify({ type: "cancelled", queue: name, taskId, reason, metrics: getSnapshot().metrics, deadLetters: [...deadLetters] });
    return task;
  };

  const getSnapshot = () => ({
    queues: Object.fromEntries(Object.entries(queues).map(([name, tasks]) => [name, tasks.map((task) => ({ ...task }))])),
    metrics: Object.fromEntries(Object.entries(metrics).map(([name, value]) => [name, { ...value }])),
    depth: Object.values(queues).reduce((sum, tasks) => sum + tasks.length, 0),
    deadLetters: [...deadLetters],
  });

  return {
    enqueue,
    drain,
    fail,
    complete,
    retry,
    cancel,
    restore(snapshotData = {}) {
      DEFAULT_QUEUES.forEach((name) => {
        queues[name] = Array.isArray(snapshotData?.queues?.[name])
          ? snapshotData.queues[name].map((task) => normalizeTask(task, name))
          : [];
        metrics[name] = snapshotData?.metrics?.[name]
          ? { ...snapshotData.metrics[name] }
          : { enqueued: 0, processed: 0, failed: 0 };
      });
      deadLetters.length = 0;
      if (Array.isArray(snapshotData.deadLetters)) {
        deadLetters.push(...snapshotData.deadLetters.map((entry) => ({ ...entry })));
      }
      notify({ type: "restored", metrics: getSnapshot().metrics, depth: getSnapshot().depth });
      return getSnapshot();
    },
    snapshot: getSnapshot,
    subscribe(listener) {
      if (typeof listener !== "function") {
        return () => {};
      }
      listeners.add(listener);
      return () => listeners.delete(listener);
    },
    get queues() {
      return queues;
    },
    get metrics() {
      return getSnapshot().metrics;
    },
  };
}
