import '../core/api_client.dart';
import '../core/event_store.dart';
import '../core/logical_clock.dart';
import '../core/signer.dart';
import 'event_factory.dart';

class DriverController {
  final String deviceId;
  final String pilotRunId;
  final LogicalClock clock;
  final EventStore store;
  final ApiClient api;
  final EventSigner signer;
  String? _lastEventHash;

  DriverController({
    this.deviceId = 'driver_1',
    this.pilotRunId = 'local_pilot',
    required this.signer,
    LogicalClock? clock,
    EventStore? store,
    ApiClient? api,
  })  : clock = clock ?? LogicalClock(),
        store = store ?? EventStore(),
        api = api ?? ApiClient();

  Future<Map<String, dynamic>> acceptRide(String rideId) {
    return _emit(
      eventType: 'DRIVER_ACCEPTED_RIDE',
      entityId: rideId,
      payload: {'ride_id': rideId},
    );
  }

  Future<Map<String, dynamic>> recordLocation(
    String rideId,
    double lat,
    double lon,
  ) {
    return _emit(
      eventType: 'DRIVER_LOCATION_UPDATE',
      entityId: rideId,
      payload: {'ride_id': rideId},
      locationSnapshot: {
        'lat': lat,
        'lon': lon,
      },
    );
  }

  Future<Map<String, dynamic>> startTrip(String rideId) {
    return _emit(
      eventType: 'TRIP_STARTED',
      entityId: rideId,
      payload: {'ride_id': rideId},
    );
  }

  Future<Map<String, dynamic>> completeTrip(String rideId) {
    return _emit(
      eventType: 'TRIP_COMPLETED',
      entityId: rideId,
      payload: {'ride_id': rideId},
    );
  }

  int pendingCount() {
    return store.pending().length;
  }

  Future<Map<String, dynamic>> syncPending() async {
    final result = await api.sendBatch(store.pending());
    final accepted = (result['accepted'] as List<dynamic>).cast<String>();
    store.markSent(accepted);
    return result;
  }

  Future<Map<String, dynamic>> _emit({
    required String eventType,
    required String entityId,
    required Map<String, dynamic> payload,
    Map<String, dynamic>? locationSnapshot,
  }) async {
    final event = createEvent(
      eventType: eventType,
      deviceId: deviceId,
      entityId: entityId,
      logicalClock: clock.next(),
      payload: payload,
      pilotRunId: pilotRunId,
      driverId: deviceId,
      previousEventHash: _lastEventHash,
      locationSnapshot: locationSnapshot,
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
