class LogicalClock {
  int _counter;

  LogicalClock({int initialValue = 0}) : _counter = initialValue;

  int next() {
    _counter += 1;
    return _counter;
  }
}
