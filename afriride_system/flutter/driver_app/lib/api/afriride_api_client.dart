import 'dart:convert';

import 'package:http/http.dart' as http;

import '../contracts/earnings_contract.dart';
import '../contracts/ledger_receipt_contract.dart';
import '../contracts/receipt_contract.dart';
import '../contracts/replay_contract.dart';
import '../contracts/ride_contract.dart';

/// AfriRide Driver API Client
///
/// Purpose:
/// Provides contract-bound access to server-authorized driver actions.
///
/// Constitutional Properties:
/// - API-bound
/// - authority-neutral
/// - replay-read-only
/// - receipt-read-only
/// - earnings-read-only
///
/// This client does NOT:
/// - compute pricing
/// - assign drivers
/// - rank drivers
/// - mutate replay
/// - generate receipts
/// - authorize payouts
///
/// Driver App requests actions.
/// Server decides authority.
class AfriRideApiClient {
  final String baseUrl;
  final http.Client _client;

  AfriRideApiClient({
    required this.baseUrl,
    http.Client? client,
  }) : _client = client ?? _UnsupportedClient();

  Future<List<RideContract>> getAssignedRideRequests({
    required String driverId,
  }) async {
    _requireNonEmpty(driverId, "missing_driver_id");

    final response = await _get(
      "/driver/$driverId/rides/assigned",
    );

    final body = _decodeJson(response);
    final rides = body["rides"];

    if (rides is! List) {
      throw const ApiContractException(
        "invalid_assigned_rides_payload",
      );
    }

    return rides
        .map((item) {
          if (item is! Map<String, dynamic>) {
            throw const ApiContractException(
              "invalid_assigned_ride_item",
            );
          }

          return RideContract.fromJson(item);
        })
        .toList(growable: false);
  }

  Future<void> acceptRide({
    required String rideId,
    required String driverId,
  }) async {
    await _driverRideAction(
      rideId: rideId,
      driverId: driverId,
      action: "accept",
    );
  }

  Future<void> rejectRide({
    required String rideId,
    required String driverId,
  }) async {
    await _driverRideAction(
      rideId: rideId,
      driverId: driverId,
      action: "reject",
    );
  }

  Future<void> startRide({
    required String rideId,
    required String driverId,
  }) async {
    await _driverRideAction(
      rideId: rideId,
      driverId: driverId,
      action: "start",
    );
  }

  Future<void> completeRide({
    required String rideId,
    required String driverId,
  }) async {
    await _driverRideAction(
      rideId: rideId,
      driverId: driverId,
      action: "complete",
    );
  }

  Future<ReceiptContract> getReceipt({
    required String rideId,
  }) async {
    _requireNonEmpty(rideId, "missing_ride_id");

    final response = await _get(
      "/ride/$rideId/receipt",
    );

    return ReceiptContract.fromJson(
      _decodeJson(response),
    );
  }

  Future<LedgerReceiptContract> getLedgerReceipt({
    required String rideId,
  }) async {
    _requireNonEmpty(rideId, "missing_ride_id");

    final response = await _get(
      "/ride/$rideId/ledger-receipt",
    );

    return LedgerReceiptContract.fromJson(
      _decodeJson(response),
    );
  }

  Future<ReplayContract> getReplay({
    required String rideId,
  }) async {
    _requireNonEmpty(rideId, "missing_ride_id");

    final response = await _get(
      "/ride/$rideId/replay",
    );

    return ReplayContract.fromJson(
      _decodeJson(response),
    );
  }

  Future<EarningsContract> getEarnings({
    required String driverId,
  }) async {
    _requireNonEmpty(driverId, "missing_driver_id");

    final response = await _get(
      "/driver/$driverId/earnings",
    );

    return EarningsContract.fromJson(
      _decodeJson(response),
    );
  }

  Future<void> _driverRideAction({
    required String rideId,
    required String driverId,
    required String action,
  }) async {
    _requireNonEmpty(rideId, "missing_ride_id");
    _requireNonEmpty(driverId, "missing_driver_id");
    _requireAllowedAction(action);

    await _post(
      "/ride/$rideId/$action",
      {
        "driver_id": driverId,
      },
    );
  }

  Future<http.Response> _get(
    String path,
  ) async {
    final response = await _client.get(
      _uri(path),
      headers: {
        "accept": "application/json",
      },
    );

    _ensureSuccess(response);

    return response;
  }

  Future<http.Response> _post(
    String path,
    Map<String, dynamic> body,
  ) async {
    final response = await _client.post(
      _uri(path),
      headers: {
        "accept": "application/json",
        "content-type": "application/json",
      },
      body: jsonEncode(body),
    );

    _ensureSuccess(response);

    return response;
  }

  Uri _uri(
    String path,
  ) {
    final trimmedBaseUrl = baseUrl.trim();

    if (trimmedBaseUrl.isEmpty) {
      throw const ApiContractException(
        "missing_base_url",
      );
    }

    if (!path.startsWith("/")) {
      throw const ApiContractException(
        "invalid_api_path",
      );
    }

    return Uri.parse(trimmedBaseUrl).resolve(path);
  }

  Map<String, dynamic> _decodeJson(
    http.Response response,
  ) {
    try {
      final decoded = jsonDecode(response.body);

      if (decoded is! Map<String, dynamic>) {
        throw const ApiContractException(
          "invalid_json_object",
        );
      }

      return decoded;
    } on FormatException {
      throw const ApiContractException(
        "invalid_json",
      );
    }
  }

  void _ensureSuccess(
    http.Response response,
  ) {
    if (response.statusCode < 200 ||
        response.statusCode >= 300) {
      throw ApiContractException(
        "api_request_failed_${response.statusCode}",
      );
    }
  }

  void _requireNonEmpty(
    String value,
    String reason,
  ) {
    if (value.trim().isEmpty) {
      throw ApiContractException(reason);
    }
  }

  void _requireAllowedAction(
    String action,
  ) {
    const allowed = {
      "accept",
      "reject",
      "start",
      "complete",
    };

    if (!allowed.contains(action)) {
      throw const ApiContractException(
        "invalid_driver_action",
      );
    }
  }
}

/// Stable API boundary exception.
///
/// The Driver App may display this as an error state.
/// It must not reinterpret it as system authority.
class ApiContractException implements Exception {
  final String reason;

  const ApiContractException(this.reason);

  @override
  String toString() => reason;
}

/// Prevents accidental network use when no client is supplied.
///
/// In production, inject a real http.Client.
/// In tests, inject a mock client.
///
/// This fails closed instead of silently performing undefined behavior.
class _UnsupportedClient extends http.BaseClient {
  _UnsupportedClient();

  @override
  Future<http.StreamedResponse> send(
    http.BaseRequest request,
  ) {
    throw const ApiContractException(
      "missing_http_client",
    );
  }
}
