import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;

import 'package:afriride_driver_pilot/api/afriride_api_client.dart';
import 'package:afriride_driver_pilot/contracts/replay_contract.dart';
import 'package:afriride_driver_pilot/guards/driver_evidence_guard.dart';

class FakeReplayVisibilityHttpClient extends http.BaseClient {
  int replayCalls = 0;

  final Map<String, dynamic> responseBody;
  final int statusCode;

  FakeReplayVisibilityHttpClient({
    required this.responseBody,
    this.statusCode = 200,
  });

  @override
  Future<http.StreamedResponse> send(
    http.BaseRequest request,
  ) async {
    if (request.method == "GET" &&
        request.url.path == "/ride/ride-1/replay") {
      replayCalls += 1;
      return _jsonResponse(
        responseBody,
        statusCode: statusCode,
      );
    }

    return _jsonResponse(
      {"error": "not_found"},
      statusCode: 404,
    );
  }

  http.StreamedResponse _jsonResponse(
    Map<String, dynamic> body, {
    required int statusCode,
  }) {
    return http.StreamedResponse(
      Stream<List<int>>.fromIterable(
        [utf8.encode(jsonEncode(body))],
      ),
      statusCode,
      headers: {
        "content-type": "application/json",
      },
    );
  }
}

void main() {
  test(
    "driver can load verified replay evidence through API contract",
    () async {
      final fakeClient = FakeReplayVisibilityHttpClient(
        responseBody: {
          "ride_id": "ride-1",
          "replay_id": "replay-1",
          "replay_verified": true,
          "replay_hash": "hash-1",
          "receipt_id": "receipt-1",
          "replay_epoch": 1,
        },
      );

      final apiClient = AfriRideApiClient(
        baseUrl: "https://example.invalid",
        client: fakeClient,
      );

      final replay = await apiClient.getReplay(
        rideId: "ride-1",
      );

      DriverEvidenceGuard.validateReplay(
        replay,
      );

      expect(fakeClient.replayCalls, 1);
      expect(replay.rideId, "ride-1");
      expect(replay.replayId, "replay-1");
      expect(replay.replayVerified, true);
      expect(replay.replayHash, "hash-1");
      expect(replay.receiptId, "receipt-1");
      expect(replay.replayEpoch, 1);
    },
  );

  test(
    "replay visibility rejects unverified replay evidence",
    () async {
      final fakeClient = FakeReplayVisibilityHttpClient(
        responseBody: {
          "ride_id": "ride-1",
          "replay_id": "replay-1",
          "replay_verified": false,
        },
      );

      final apiClient = AfriRideApiClient(
        baseUrl: "https://example.invalid",
        client: fakeClient,
      );

      final replay = await apiClient.getReplay(
        rideId: "ride-1",
      );

      expect(
        () => DriverEvidenceGuard.validateReplay(
          replay,
        ),
        throwsA(
          isA<DriverEvidenceException>(),
        ),
      );
    },
  );

  test(
    "replay visibility rejects missing replay id",
    () {
      expect(
        () => apiReplayWithoutId(),
        throwsArgumentError,
      );
    },
  );

  test(
    "replay API failure remains fail-closed",
    () {
      final fakeClient = FakeReplayVisibilityHttpClient(
        responseBody: {
          "error": "server_error",
        },
        statusCode: 500,
      );

      final apiClient = AfriRideApiClient(
        baseUrl: "https://example.invalid",
        client: fakeClient,
      );

      expect(
        () => apiClient.getReplay(
          rideId: "ride-1",
        ),
        throwsA(
          isA<ApiContractException>(),
        ),
      );
    },
  );
}

void apiReplayWithoutId() {
  final payload = {
    "ride_id": "ride-1",
    "replay_id": "",
    "replay_verified": true,
  };

  throwIfReplayInvalid(payload);
}

void throwIfReplayInvalid(
  Map<String, dynamic> payload,
) {
  final replay =
      AfriRideApiClientReplayParser.parse(payload);

  DriverEvidenceGuard.validateReplay(
    replay,
  );
}

/// Test-only parser wrapper.
///
/// This avoids exposing any replay parsing authority in production code.
class AfriRideApiClientReplayParser {
  static ReplayContract parse(
    Map<String, dynamic> payload,
  ) {
    return _parse(payload);
  }

  static ReplayContract _parse(
    Map<String, dynamic> payload,
  ) {
    return ReplayContract.fromJson(payload);
  }
}