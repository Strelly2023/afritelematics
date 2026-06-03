import '../core/api_client.dart';
import '../core/event_store.dart';
import '../core/logical_clock.dart';
import '../core/signer.dart';
import 'event_factory.dart';

class RiderController {
  final String deviceId;
  final String pilotRunId;
  final LogicalClock clock;
  final EventStore store;
  final ApiClient api;
  final EventSigner signer;
  String? _lastEventHash;

  RiderController({
    this.deviceId = 'rider_1',
    this.pilotRunId = 'local_pilot',
    required this.signer,
    LogicalClock? clock,
    EventStore? store,
    ApiClient? api,
  })  : clock = clock ?? LogicalClock(),
        store = store ?? EventStore(),
        api = api ?? ApiClient();

  Future<Map<String, dynamic>> requestRide({
    required String rideId,
    required String pickup,
    required String dropoff,
  }) {
    return _emit(
      eventType: 'RIDER_REQUESTED_RIDE',
      entityId: rideId,
      payload: {
        'ride_id': rideId,
        'pickup': pickup,
        'dropoff': dropoff,
      },
    );
  }

  Future<Map<String, dynamic>> cancelRide(String rideId) {
    return _emit(
      eventType: 'RIDER_CANCELLED_RIDE',
      entityId: rideId,
      payload: {'ride_id': rideId},
    );
  }

  Future<Map<String, dynamic>> _emit({
    required String eventType,
    required String entityId,
    required Map<String, dynamic> payload,
  }) async {
    final event = createEvent(
      eventType: eventType,
      deviceId: deviceId,
      entityId: entityId,
      logicalClock: clock.next(),
      payload: payload,
      pilotRunId: pilotRunId,
      riderId: deviceId,
      previousEventHash: _lastEventHash,
    );
    event['signature'] = signer.sign(event);
    _lastEventHash = hashCanonical(event);
    store.add(event);

    final result = await api.sendBatch(store.pending());
    final accepted = (result['accepted'] as List<dynamic>).cast<String>();
    store.markSent(accepted);
    return result;
  }
}
