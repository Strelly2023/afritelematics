import 'core/signer.dart';
import 'rider/rider_controller.dart';
import 'rider/ws_client.dart';

void main() {
  final controller = RiderController(signer: EventSigner('pilot-secret'));
  controller.requestRide(rideId: 'ride_123', pickup: 'A', dropoff: 'B');

  final tracking = RideTrackingClient('ride_123');
  tracking.listen().listen((message) {
    print('Live update: $message');
  });
}
