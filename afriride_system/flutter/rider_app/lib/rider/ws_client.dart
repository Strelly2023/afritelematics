import 'dart:convert';

import 'package:web_socket_channel/web_socket_channel.dart';

class RideTrackingClient {
  final WebSocketChannel channel;

  RideTrackingClient(String rideId, {String baseUrl = 'ws://localhost:8000'})
      : channel = WebSocketChannel.connect(Uri.parse('$baseUrl/ws/$rideId'));

  Stream<Map<String, dynamic>> listen() {
    return channel.stream.map((data) => jsonDecode(data as String) as Map<String, dynamic>);
  }
}
