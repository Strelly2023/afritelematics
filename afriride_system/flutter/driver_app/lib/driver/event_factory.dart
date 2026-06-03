Map<String, dynamic> createEvent({
  required String eventType,
  required String deviceId,
  required String entityId,
  required int logicalClock,
  required Map<String, dynamic> payload,
}) {
  return {
    'event_id': '${deviceId}_$logicalClock',
    'event_type': eventType,
    'device_id': deviceId,
    'entity_id': entityId,
    'timestamp': DateTime.now().millisecondsSinceEpoch,
    'logical_clock': logicalClock,
    'payload': payload,
  };
}
