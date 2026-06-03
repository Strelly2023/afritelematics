import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;

import 'package:afriride_driver_pilot/api/afriride_api_client.dart';
import 'package:afriride_driver_pilot/contracts/receipt_contract.dart';
import 'package:afriride_driver_pilot/guards/driver_evidence_guard.dart';

class FakeReceiptVisibilityHttpClient extends http.BaseClient {
  int receiptCalls = 0;

  final Map<String, dynamic> responseBody;
  final int statusCode;

  FakeReceiptVisibilityHttpClient({
    required this.responseBody,
    this.statusCode = 200,
  });

  @override
  Future<http.StreamedResponse> send(
    http.BaseRequest request,
  ) async {
    if (request.method == "GET" &&
        request.url.path == "/ride/ride-1/receipt") {
      receiptCalls += 1;

      return _jsonResponse(
        responseBody,
        statusCode: statusCode,
      );
    }

    return _jsonResponse(
      {
        "error": "not_found",
      },
      statusCode: 404,
    );
  }

  http.StreamedResponse _jsonResponse(
    Map<String, dynamic> body, {
    required int statusCode,
  }) {
    return http.StreamedResponse(
      Stream<List<int>>.fromIterable(
        [
          utf8.encode(
            jsonEncode(body),
          ),
        ],
      ),
      statusCode,
      headers: {
        "content-type": "application/json",
      },
    );
  }
}

void main() {
  testWidgets(
    "driver can load completed ride receipt evidence through API contract",
    (tester) async {
      final fakeClient = FakeReceiptVisibilityHttpClient(
        responseBody: {
          "ride_id": "ride-1",
          "receipt_id": "receipt-1",
          "status": "completed",
          "replay_id": "replay-1",
          "receipt_hash": "receipt-hash-1",
          "issued_at": "2026-05-31T00:00:00Z",
        },
      );

      final apiClient = AfriRideApiClient(
        baseUrl: "https://example.invalid",
        client: fakeClient,
      );

      final receipt = await apiClient.getReceipt(
        rideId: "ride-1",
      );

      DriverEvidenceGuard.validateCompletedReceipt(
        receipt,
      );

      expect(fakeClient.receiptCalls, 1);
      expect(receipt.rideId, "ride-1");
      expect(receipt.receiptId, "receipt-1");
      expect(receipt.status, "completed");
      expect(receipt.replayId, "replay-1");
      expect(receipt.receiptHash, "receipt-hash-1");
      expect(receipt.issuedAt, "2026-05-31T00:00:00Z");
    },
  );

  testWidgets(
    "receipt visibility rejects non-completed receipt evidence",
    (tester) async {
      final receipt = ReceiptContract(
        rideId: "ride-1",
        receiptId: "receipt-1",
        status: "pending",
      );

      expect(
        () => DriverEvidenceGuard.validateCompletedReceipt(
          receipt,
        ),
        throwsA(
          isA<DriverEvidenceException>(),
        ),
      );
    },
  );

  testWidgets(
    "receipt visibility rejects missing receipt id",
    (tester) async {
      final receipt = ReceiptContract(
        rideId: "ride-1",
        receiptId: "",
        status: "completed",
      );

      expect(
        () => DriverEvidenceGuard.validateCompletedReceipt(
          receipt,
        ),
        throwsA(
          isA<DriverEvidenceException>(),
        ),
      );
    },
  );

  testWidgets(
    "receipt API failure remains fail-closed",
    (tester) async {
      final fakeClient = FakeReceiptVisibilityHttpClient(
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
        () => apiClient.getReceipt(
          rideId: "ride-1",
        ),
        throwsA(
          isA<ApiContractException>(),
        ),
      );
    },
  );
}