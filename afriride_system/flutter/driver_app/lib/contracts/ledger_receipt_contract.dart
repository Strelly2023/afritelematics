// Portable Ledger Receipt Contract
//
// Purpose:
// Represents a server-derived proof export for a completed ride ledger.
//
// Constitutional Properties:
// - read-only
// - derived evidence only
// - authority-neutral
// - display-safe
//
// This contract does NOT:
// - generate receipts
// - mutate the event chain
// - verify replay locally
// - create proof authority

class LedgerReceiptContract {
  final String receiptId;
  final String verdict;
  final String receiptHash;
  final int eventCount;
  final String rootHash;
  final String hashMode;
  final String signatureMode;
  final bool allSignaturesValid;
  final bool allIdentitiesVerified;
  final bool replayValid;
  final double totalFare;

  const LedgerReceiptContract({
    required this.receiptId,
    required this.verdict,
    required this.receiptHash,
    required this.eventCount,
    required this.rootHash,
    required this.hashMode,
    required this.signatureMode,
    required this.allSignaturesValid,
    required this.allIdentitiesVerified,
    required this.replayValid,
    required this.totalFare,
  });

  factory LedgerReceiptContract.fromJson(
    Map<String, dynamic> json,
  ) {
    final ledgerProof =
        _object(json, 'ledger_proof');

    final signatureValidation =
        _object(
          json,
          'signature_validation',
        );

    final identityValidation =
        _object(
          json,
          'identity_validation',
        );

    final replayProof =
        _object(
          json,
          'replay_proof',
        );

    final financialSummary =
        _object(
          json,
          'financial_summary',
        );

    return LedgerReceiptContract(
      receiptId:
          _string(json, 'receipt_id'),
      verdict:
          _string(json, 'verdict'),
      receiptHash:
          _string(json, 'receipt_hash'),
      eventCount:
          _int(
            ledgerProof,
            'event_count',
          ),
      rootHash:
          _string(
            ledgerProof,
            'root_hash',
          ),
      hashMode:
          _string(
            ledgerProof,
            'hash_mode',
          ),
      signatureMode:
          _string(
            signatureValidation,
            'signature_mode',
          ),
      allSignaturesValid:
          _bool(
            signatureValidation,
            'all_signatures_valid',
          ),
      allIdentitiesVerified:
          _bool(
            identityValidation,
            'all_verified',
          ),
      replayValid:
          _bool(
            replayProof,
            'replay_valid',
          ),
      totalFare:
          _num(
            financialSummary,
            'total_fare',
          ).toDouble(),
    );
  }

  bool get isValid =>
      verdict == 'VALID';

  bool get isCryptographic =>
      hashMode ==
      'sha256_canonical_chain';

  bool get isSigned =>
      signatureMode ==
      'rsa_pss_sha256';

  bool get isEvidenceComplete =>
      receiptId.isNotEmpty &&
      receiptHash.isNotEmpty &&
      rootHash.isNotEmpty;

  bool get isProofValid =>
      isValid &&
      allSignaturesValid &&
      allIdentitiesVerified &&
      replayValid;

  Map<String, dynamic> toJson() {
    return {
      'receipt_id': receiptId,
      'verdict': verdict,
      'receipt_hash': receiptHash,
      'ledger_proof': {
        'event_count': eventCount,
        'root_hash': rootHash,
        'hash_mode': hashMode,
      },
      'signature_validation': {
        'signature_mode':
            signatureMode,
        'all_signatures_valid':
            allSignaturesValid,
      },
      'identity_validation': {
        'all_verified':
            allIdentitiesVerified,
      },
      'replay_proof': {
        'replay_valid':
            replayValid,
      },
      'financial_summary': {
        'total_fare': totalFare,
      },
    };
  }

  @override
  String toString() {
    return
        'LedgerReceiptContract('
        'receiptId=$receiptId, '
        'verdict=$verdict, '
        'eventCount=$eventCount'
        ')';
  }

  @override
  bool operator ==(
    Object other,
  ) {
    return other
            is LedgerReceiptContract &&
        other.receiptId ==
            receiptId &&
        other.receiptHash ==
            receiptHash;
  }

  @override
  int get hashCode =>
      Object.hash(
        receiptId,
        receiptHash,
      );
}

Map<String, dynamic> _object(
  Map<String, dynamic> json,
  String key,
) {
  final value = json[key];

  if (value is! Map<String, dynamic>) {
    throw ArgumentError(
      'invalid_$key',
    );
  }

  return value;
}

String _string(
  Map<String, dynamic> json,
  String key,
) {
  final value =
      (json[key] as String?)?.trim();

  if (value == null ||
      value.isEmpty) {
    throw ArgumentError(
      'missing_$key',
    );
  }

  return value;
}

int _int(
  Map<String, dynamic> json,
  String key,
) {
  final value = json[key];

  if (value is! int) {
    throw ArgumentError(
      'invalid_$key',
    );
  }

  return value;
}

bool _bool(
  Map<String, dynamic> json,
  String key,
) {
  final value = json[key];

  if (value is! bool) {
    throw ArgumentError(
      'invalid_$key',
    );
  }

  return value;
}

num _num(
  Map<String, dynamic> json,
  String key,
) {
  final value = json[key];

  if (value is! num) {
    throw ArgumentError(
      'invalid_$key',
    );
  }

  return value;
}