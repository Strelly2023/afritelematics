class EventStore {
  final List<Map<String, dynamic>> _pending = [];

  void add(Map<String, dynamic> event) {
    _pending.add(Map<String, dynamic>.from(event));
  }

  List<Map<String, dynamic>> pending() {
    final events = _pending.map((event) => Map<String, dynamic>.from(event)).toList();
    events.sort((left, right) {
      final clockCompare = (left['logical_clock'] as int).compareTo(right['logical_clock'] as int);
      if (clockCompare != 0) {
        return clockCompare;
      }
      return (left['event_id'] as String).compareTo(right['event_id'] as String);
    });
    return events;
  }

  void markSent(Iterable<String> eventIds) {
    final sent = eventIds.toSet();
    _pending.removeWhere((event) => sent.contains(event['event_id']));
  }
}
