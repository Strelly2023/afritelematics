import 'package:geolocator/geolocator.dart';

class GpsService {
  Stream<Position> getStream() {
    return Geolocator.getPositionStream();
  }
}
