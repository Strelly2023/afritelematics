import 'dart:convert';

import 'package:afriride_rider_pilot/core/api_client.dart';
import 'package:afriride_rider_pilot/core/signer.dart';
import 'package:afriride_rider_pilot/rider/rider_controller.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;

void main() {
  test('requestRide includes pilot run id in outbound event payload', () async {
    late Map<String, dynamic> requestBody;
    final api = ApiClient(
      baseUrl: 'https://afriride-api.onrender.com',
      client: _FakeClient((request) async {
        requestBody = jsonDecode(await request.finalize().bytesToString())
            as Map<String, dynamic>;
        return http.StreamedResponse(
          Stream.value(utf8.encode('{"accepted":["rider_1_1"]}')),
          200,
        );
      }),
    );

    final controller = RiderController(
      signer: EventSigner('pilot-secret'),
      api: api,
    );

    final result = await controller.requestRide(
      rideId: 'ride_123',
      pickup: 'A',
      dropoff: 'B',
      pilotRunId: 'live_pilot_001',
    );

    final events = requestBody['events'] as List<dynamic>;
    final event = events.single as Map<String, dynamic>;
    final payload = event['payload'] as Map<String, dynamic>;
    expect(payload['pilot_run_id'], 'live_pilot_001');
    expect(result['accepted'], ['rider_1_1']);
  });
}

class _FakeClient extends http.BaseClient {
  final Future<http.StreamedResponse> Function(http.BaseRequest request)
      _handler;

  _FakeClient(this._handler);

  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) {
    return _handler(request);
  }
}
