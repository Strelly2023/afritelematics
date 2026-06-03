import 'dart:convert';

import 'package:http/http.dart' as http;

class ApiClient {
  final Uri endpoint;
  final http.Client _client;

  ApiClient({String baseUrl = 'http://localhost:8000', http.Client? client})
      : endpoint = Uri.parse('$baseUrl/v1/events'),
        _client = client ?? http.Client();

  Future<Map<String, dynamic>> sendBatch(List<Map<String, dynamic>> events) async {
    final response = await _client.post(
      endpoint,
      headers: {'content-type': 'application/json'},
      body: jsonEncode({
        'received_at_ms': DateTime.now().millisecondsSinceEpoch,
        'events': events,
      }),
    );
    return jsonDecode(response.body) as Map<String, dynamic>;
  }
}
