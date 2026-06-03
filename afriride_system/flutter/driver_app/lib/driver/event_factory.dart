import 'dart:convert';

import 'package:crypto/crypto.dart';

Map<String, dynamic> createEvent({
  required String eventType,
  required String deviceId,
  required String entityId,
  required int logicalClock,
  required Map<String, dynamic> payload,
  required String pilotRunId,
  String? driverId,
  String? previousEventHash,
  Map<String, dynamic>? locationSnapshot,
}) {
  final eventTimestamp = DateTime.now().millisecondsSinceEpoch;
  final evidencePayload = Map<String, dynamic>.from(payload)
    ..putIfAbsent('pilot_run_id', () => pilotRunId)
    ..putIfAbsent('ride_id', () => entityId)
    ..putIfAbsent('driver_id', () => driverId ?? deviceId)
    ..putIfAbsent('device_id', () => deviceId)
    ..putIfAbsent('event_timestamp', () => eventTimestamp)
    ..putIfAbsent('previous_event_hash', () => previousEventHash ?? 'GENESIS');

  if (locationSnapshot != null) {
    evidencePayload['location_snapshot'] = locationSnapshot;
    evidencePayload['location_hash'] = hashCanonical(locationSnapshot);
  }

  return {
    'event_id': '${deviceId}_$logicalClock',
    'event_type': eventType,
    'device_id': deviceId,
    'entity_id': entityId,
    'timestamp': eventTimestamp,
    'logical_clock': logicalClock,
    'payload': evidencePayload,
  };
}

String hashCanonical(Map<String, dynamic> value) {
  final encoded = jsonEncode(_canonicalValue(value));
  return sha256.convert(utf8.encode(encoded)).toString();
}

dynamic _canonicalValue(dynamic value) {
  if (value is Map<String, dynamic>) {
    final keys = value.keys.toList()..sort();
    return {for (final key in keys) key: _canonicalValue(value[key])};
  }
  if (value is List) {
    return value.map(_canonicalValue).toList();
  }
  return value;
}
