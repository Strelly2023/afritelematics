import 'package:flutter/foundation.dart';

import 'core/api_client.dart';
import 'core/signer.dart';
import 'rider/rider_controller.dart';
import 'rider/ws_client.dart';

void main() {
  const apiBaseUrl = String.fromEnvironment(
    'AFRIRIDE_API_BASE_URL',
    defaultValue: 'http://localhost:8000',
  );
  const deviceRole = String.fromEnvironment(
    'AFRIRIDE_DEVICE_ROLE',
    defaultValue: 'rider',
  );
  const pilotRunId = String.fromEnvironment(
    'AFRIRIDE_PILOT_RUN_ID',
    defaultValue: 'local_pilot',
  );
  const eventSecret = String.fromEnvironment(
    'AFRIRIDE_EVENT_SECRET',
    defaultValue: '',
  );

  const rideId = 'ride_123';
  final controller = RiderController(
    deviceId: '${deviceRole}_1',
    pilotRunId: pilotRunId,
    signer: EventSigner(
      eventSecret.isEmpty ? 'local-dev-only-event-secret' : eventSecret,
    ),
    api: ApiClient(baseUrl: apiBaseUrl),
  );
  controller.requestRide(
    rideId: rideId,
    pickup: 'A',
    dropoff: 'B',
  );

  final tracking = RideTrackingClient(
    rideId,
    baseUrl: _webSocketBaseUrl(apiBaseUrl),
  );
  tracking.listen().listen((message) {
    debugPrint('Live update: $message');
  });
}

String _webSocketBaseUrl(String apiBaseUrl) {
  final uri = Uri.parse(apiBaseUrl);
  final scheme = uri.scheme == 'https' ? 'wss' : 'ws';
  return uri.replace(scheme: scheme).toString();
}
