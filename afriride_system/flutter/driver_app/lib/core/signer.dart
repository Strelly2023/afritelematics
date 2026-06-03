import 'dart:convert';

import 'package:crypto/crypto.dart';

class EventSigner {
  final String secret;

  EventSigner(this.secret);

  String sign(Map<String, dynamic> event) {
    final payload = {
      'device_id': event['device_id'],
      'entity_id': event['entity_id'],
      'event_id': event['event_id'],
      'event_type': event['event_type'],
      'logical_clock': event['logical_clock'],
      'payload': event['payload'],
      'timestamp': event['timestamp'],
    };
    final encoded = jsonEncode(_canonicalValue(payload));
    return Hmac(sha256, utf8.encode(secret)).convert(utf8.encode(encoded)).toString();
  }

  dynamic _canonicalValue(dynamic value) {
    if (value is Map<String, dynamic>) {
      return _canonical(value);
    }
    if (value is List) {
      return value.map(_canonicalValue).toList();
    }
    return value;
  }

  Map<String, dynamic> _canonical(Map<String, dynamic> value) {
    final keys = value.keys.toList()..sort();
    return {for (final key in keys) key: _canonicalValue(value[key])};
  }
}
