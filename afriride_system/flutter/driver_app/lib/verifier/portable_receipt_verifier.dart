import 'dart:collection';
import 'dart:convert';
import 'dart:math';

import 'package:archive/archive.dart';
import 'package:crypto/crypto.dart';

class PortableVerificationResult {
  final bool valid;
  final String reason;
  final String trustLevel;
  final Map<String, dynamic>? payload;
  final Map<String, dynamic>? zkReceipt;
  final Map<String, dynamic>? bridge;
  final Map<String, dynamic>? verification;

  const PortableVerificationResult({
    required this.valid,
    required this.reason,
    required this.trustLevel,
    required this.payload,
    required this.zkReceipt,
    required this.bridge,
    required this.verification,
  });

  factory PortableVerificationResult.invalid(
    String reason, {
    String trustLevel = 'UNTRUSTED',
    Map<String, dynamic>? payload,
    Map<String, dynamic>? zkReceipt,
    Map<String, dynamic>? bridge,
    Map<String, dynamic>? verification,
  }) {
    return PortableVerificationResult(
      valid: false,
      reason: reason,
      trustLevel: trustLevel,
      payload: payload,
      zkReceipt: zkReceipt,
      bridge: bridge,
      verification: verification ??
          {
            'valid': false,
            'reason': reason,
          },
    );
  }

  factory PortableVerificationResult.valid({
    required String reason,
    required String trustLevel,
    required Map<String, dynamic> payload,
    required Map<String, dynamic> zkReceipt,
    required Map<String, dynamic>? bridge,
    required Map<String, dynamic> verification,
  }) {
    return PortableVerificationResult(
      valid: true,
      reason: reason,
      trustLevel: trustLevel,
      payload: payload,
      zkReceipt: zkReceipt,
      bridge: bridge,
      verification: verification,
    );
  }
}

String _stableJson(Object? value) {
  return jsonEncode(_canonicalize(value));
}

Object? _canonicalize(Object? value) {
  if (value is Map) {
    final keys = value.keys.map((key) => key.toString()).toList()
      ..sort((a, b) => a.compareTo(b));
    final canonical = LinkedHashMap<String, dynamic>();
    for (final key in keys) {
      canonical[key] = _canonicalize(value[key]);
    }
    return canonical;
  }
  if (value is List) {
    return value.map(_canonicalize).toList(growable: false);
  }
  return value;
}

String _hash(Object? payload, {required String domain}) {
  final canonical = _stableJson({
    'domain': domain,
    'payload': payload,
  });
  return sha256.convert(utf8.encode(canonical)).toString();
}

Map<String, dynamic> _canonicalMap(Map<String, dynamic> input) {
  return Map<String, dynamic>.from(_canonicalize(input) as Map);
}

String _repeat(String value, int times) {
  return List.filled(times, value).join();
}

Map<String, dynamic> _buildZkReceipt(
  Map<String, dynamic> receipt, {
  List<String> hiddenFields = const [],
  String? chainId,
  int? epoch,
}) {
  final normalizedHiddenFields = hiddenFields
      .map((field) => field.trim())
      .where((field) => field.isNotEmpty)
      .toSet()
      .toList(growable: false)
    ..sort();

  final redacted = <String, dynamic>{};
  for (final entry in receipt.entries) {
    if (!normalizedHiddenFields.contains(entry.key)) {
      redacted[entry.key] = entry.value;
    }
  }

  final canonicalRedacted = _canonicalMap(redacted);
  final publicInputs = <String, dynamic>{
    'receipt_hash': _hash(canonicalRedacted, domain: 'zk_receipt_public'),
    'hidden_commitment': _hash(
      {
        for (final field in normalizedHiddenFields) field: receipt[field],
      },
      domain: 'zk_receipt_hidden',
    ),
    'issued_at': (receipt['issued_at'] ?? '').toString().trim(),
    'chain_id': (chainId ?? receipt['chain_id'] ?? '').toString().trim(),
    'epoch': epoch ?? int.tryParse((receipt['epoch'] ?? '0').toString()) ?? 0,
  };

  final commitment = _hash(
    {
      'public_inputs': publicInputs,
      'redacted_receipt': canonicalRedacted,
      'hidden_fields': normalizedHiddenFields,
    },
    domain: 'zk_receipt_commitment',
  );
  final proof = _hash(
    {
      'scheme': 'mock-zk-receipt-v1',
      'commitment': commitment,
      'public_inputs': publicInputs,
    },
    domain: 'zk_receipt_proof',
  );
  final proofHash = _hash(
    {
      'scheme': 'mock-zk-receipt-v1',
      'commitment': commitment,
      'proof': proof,
      'public_inputs': publicInputs,
    },
    domain: 'zk_receipt_artifact',
  );

  return _canonicalMap({
    'type': 'zk_receipt',
    'version': '1.0',
    'scheme': 'mock-zk-receipt-v1',
    'hidden_fields': normalizedHiddenFields,
    'public_inputs': publicInputs,
    'redacted_receipt': canonicalRedacted,
    'commitment': commitment,
    'proof': proof,
    'proof_hash': proofHash,
  });
}

Map<String, dynamic> _buildMerkleProof(List<String> leaves, int index) {
  if (index < 0 || index >= leaves.length) {
    throw RangeError.index(index, leaves, 'index');
  }

  final leafHashes = leaves
      .map((leaf) => _hash({'leaf': leaf}, domain: 'cross_chain_merkle_leaf'))
      .toList(growable: false);
  var currentIndex = index;
  final path = <Map<String, dynamic>>[];
  var level = List<String>.from(leafHashes);

  while (level.length > 1) {
    var siblingIndex = currentIndex.isEven ? currentIndex + 1 : currentIndex - 1;
    if (siblingIndex >= level.length) {
      siblingIndex = currentIndex;
    }
    path.add({
      'position': currentIndex.isEven ? 'right' : 'left',
      'hash': level[siblingIndex],
    });

    final nextLevel = <String>[];
    for (var i = 0; i < level.length; i += 2) {
      final left = level[i];
      final right = i + 1 < level.length ? level[i + 1] : level[i];
      nextLevel.add(
        _hash({'left': left, 'right': right}, domain: 'cross_chain_merkle_parent'),
      );
    }
    level = nextLevel;
    currentIndex ~/= 2;
  }

  return _canonicalMap({
    'index': index,
    'leaf': leaves[index],
    'leaf_hash': leafHashes[index],
    'leaf_count': leaves.length,
    'path': path,
    'root': level.first,
  });
}

List<String> _normaliseLeaves(Iterable<String> values) {
  final unique = <String>{};
  for (final value in values) {
    final trimmed = value.trim();
    if (trimmed.isNotEmpty) {
      unique.add(trimmed);
    }
  }
  final leaves = unique.toList(growable: false);
  leaves.sort((a, b) => a.compareTo(b));
  return leaves;
}

Map<String, dynamic> _buildCrossChainBridge(
  Map<String, dynamic> zkReceipt,
  Map<String, dynamic> lightClientState, {
  List<Map<String, dynamic>> receiptBatch = const [],
}) {
  final receiptCommitment = (zkReceipt['commitment'] ?? '').toString().trim();
  if (receiptCommitment.isEmpty) {
    throw StateError('zk_commitment_required');
  }

  final canonicalState = _canonicalMap({
    'chain_id': (lightClientState['chain_id'] ?? '').toString().trim(),
    'block_height': int.tryParse(
          (lightClientState['block_height'] ?? 0).toString(),
        ) ??
        0,
    'state_root': (lightClientState['state_root'] ?? '').toString().trim(),
    'validator_set_hash':
        (lightClientState['validator_set_hash'] ?? '').toString().trim(),
    if (lightClientState['block_hash'] != null)
      'block_hash': lightClientState['block_hash'].toString().trim(),
    if (lightClientState['trusted_height'] != null)
      'trusted_height':
          int.tryParse(lightClientState['trusted_height'].toString()) ?? 0,
    if (lightClientState['timestamp'] != null)
      'timestamp': lightClientState['timestamp'].toString().trim(),
  });

  final leaves = _normaliseLeaves([
    receiptCommitment,
    ...receiptBatch.map((item) => (item['commitment'] ?? '').toString()),
  ]);
  final proof = _buildMerkleProof(leaves, leaves.indexOf(receiptCommitment));
  final receiptRoot = _merkleRoot(leaves);
  final stateHash = _hash(
    canonicalState,
    domain: 'cross_chain_light_client_state',
  );

  final bridge = <String, dynamic>{
    'type': 'cross_chain_bridge',
    'version': '1.0',
    'scheme': 'novatrust-light-client-v1',
    'zk_commitment': receiptCommitment,
    'receipt_root': receiptRoot,
    'receipt_proof': proof,
    'light_client_state': canonicalState,
    'light_client_state_hash': stateHash,
    'receipt_batch_size': leaves.length,
  };
  final bridgeHash = _hash(bridge, domain: 'cross_chain_bridge');
  bridge['bridge_hash'] = bridgeHash;
  bridge['bridge_id'] = 'bridge-${bridgeHash.substring(0, min(16, bridgeHash.length))}';
  return _canonicalMap(bridge);
}

String _merkleRoot(List<String> leaves) {
  final leafHashes = leaves
      .map((leaf) => _hash({'leaf': leaf}, domain: 'cross_chain_merkle_leaf'))
      .toList(growable: false);
  if (leafHashes.isEmpty) {
    return _hash({'leaves': []}, domain: 'cross_chain_merkle_root');
  }

  var level = leafHashes;
  while (level.length > 1) {
    final nextLevel = <String>[];
    for (var i = 0; i < level.length; i += 2) {
      final left = level[i];
      final right = i + 1 < level.length ? level[i + 1] : level[i];
      nextLevel.add(
        _hash({'left': left, 'right': right}, domain: 'cross_chain_merkle_parent'),
      );
    }
    level = nextLevel;
  }
  return level.first;
}

bool _verifyMerkleProof({
  required String leaf,
  required Map<String, dynamic> proof,
  required String root,
}) {
  final proofLeafHash = (proof['leaf_hash'] ?? '').toString().trim();
  var current = _hash({'leaf': leaf}, domain: 'cross_chain_merkle_leaf');
  if (proofLeafHash.isNotEmpty && proofLeafHash != current) {
    return false;
  }

  final path = proof['path'];
  if (path is! List) {
    return false;
  }
  for (final step in path) {
    if (step is! Map) {
      return false;
    }
    final position = (step['position'] ?? '').toString().trim().toLowerCase();
    final siblingHash = (step['hash'] ?? '').toString().trim();
    if (siblingHash.isEmpty || (position != 'left' && position != 'right')) {
      return false;
    }
    current = position == 'left'
        ? _hash({'left': siblingHash, 'right': current}, domain: 'cross_chain_merkle_parent')
        : _hash({'left': current, 'right': siblingHash}, domain: 'cross_chain_merkle_parent');
  }
  return current == root;
}

PortableVerificationResult _verifyZkReceipt(Map<String, dynamic> zkReceipt) {
  final scheme = (zkReceipt['scheme'] ?? '').toString().trim();
  final publicInputs = zkReceipt['public_inputs'];
  final redactedReceipt = zkReceipt['redacted_receipt'];
  final commitment = (zkReceipt['commitment'] ?? '').toString().trim();
  final proof = (zkReceipt['proof'] ?? '').toString().trim();
  final proofHash = (zkReceipt['proof_hash'] ?? '').toString().trim();
  final hiddenFields = zkReceipt['hidden_fields'] is List
      ? ((zkReceipt['hidden_fields'] as List)
          .map((field) => field.toString().trim())
          .where((field) => field.isNotEmpty)
          .toList(growable: false)
        ..sort((a, b) => a.compareTo(b)))
      : <String>[];

  if (scheme.isEmpty) {
    return PortableVerificationResult.invalid('zk_scheme_missing');
  }
  if (publicInputs is! Map || redactedReceipt is! Map) {
    return PortableVerificationResult.invalid('zk_artifact_incomplete');
  }
  if (commitment.isEmpty || proof.isEmpty || proofHash.isEmpty) {
    return PortableVerificationResult.invalid('zk_artifact_incomplete');
  }

  final expectedCommitment = _hash(
    {
      'public_inputs': _canonicalMap(Map<String, dynamic>.from(publicInputs)),
      'redacted_receipt': _canonicalMap(Map<String, dynamic>.from(redactedReceipt)),
      'hidden_fields': hiddenFields,
    },
    domain: 'zk_receipt_commitment',
  );
  if (commitment != expectedCommitment) {
    return PortableVerificationResult.invalid('zk_commitment_mismatch');
  }

  final expectedProof = _hash(
    {
      'scheme': scheme,
      'commitment': commitment,
      'public_inputs': _canonicalMap(Map<String, dynamic>.from(publicInputs)),
    },
    domain: 'zk_receipt_proof',
  );
  if (proof != expectedProof) {
    return PortableVerificationResult.invalid('zk_proof_mismatch');
  }

  final expectedProofHash = _hash(
    {
      'scheme': scheme,
      'commitment': commitment,
      'proof': proof,
      'public_inputs': _canonicalMap(Map<String, dynamic>.from(publicInputs)),
    },
    domain: 'zk_receipt_artifact',
  );
  if (proofHash != expectedProofHash) {
    return PortableVerificationResult.invalid('zk_proof_hash_mismatch');
  }

  return PortableVerificationResult.valid(
    reason: 'zk_receipt_verified',
    trustLevel: 'HIGH',
      payload: Map<String, dynamic>.from(zkReceipt),
    zkReceipt: Map<String, dynamic>.from(zkReceipt),
    bridge: null,
    verification: {
      'valid': true,
      'reason': 'zk_receipt_verified',
      'commitment': commitment,
      'proof_hash': proofHash,
    },
  );
}

Map<String, dynamic>? _verifyBridge(
  Map<String, dynamic>? bridge,
  String commitment, {
  Map<String, dynamic>? expectedLightClientState,
}) {
  if (bridge == null) {
    return null;
  }
  if (bridge['scheme']?.toString().trim() != 'novatrust-light-client-v1') {
    return {
      'valid': false,
      'reason': 'cross_chain_bridge_scheme_invalid',
    };
  }
  final zkCommitment = bridge['zk_commitment']?.toString().trim() ?? '';
  final receiptRoot = bridge['receipt_root']?.toString().trim() ?? '';
  final bridgeHash = bridge['bridge_hash']?.toString().trim() ?? '';
  final receiptProof = bridge['receipt_proof'];
  final statePayload = bridge['light_client_state'];
  final stateHash = bridge['light_client_state_hash']?.toString().trim() ?? '';

  if (zkCommitment.isEmpty || receiptRoot.isEmpty || bridgeHash.isEmpty) {
    return {
      'valid': false,
      'reason': 'cross_chain_bridge_incomplete',
    };
  }
  if (receiptProof is! Map || statePayload is! Map) {
    return {
      'valid': false,
      'reason': 'cross_chain_bridge_incomplete',
    };
  }

  final canonicalState = _canonicalMap(Map<String, dynamic>.from(statePayload));
  final expectedStateHash = _hash(
    canonicalState,
    domain: 'cross_chain_light_client_state',
  );
  if (stateHash != expectedStateHash) {
    return {
      'valid': false,
      'reason': 'cross_chain_light_client_state_hash_mismatch',
    };
  }
  if (expectedLightClientState != null &&
      _canonicalMap(Map<String, dynamic>.from(expectedLightClientState)) !=
          canonicalState) {
    return {
      'valid': false,
      'reason': 'cross_chain_light_client_state_mismatch',
    };
  }

  final expectedBridgeHash = _hash(
    {
      for (final entry in bridge.entries)
        if (entry.key != 'bridge_hash' && entry.key != 'bridge_id')
          entry.key: entry.value,
    },
    domain: 'cross_chain_bridge',
  );
  if (bridgeHash != expectedBridgeHash) {
    return {
      'valid': false,
      'reason': 'cross_chain_bridge_hash_mismatch',
    };
  }
  if (commitment.isNotEmpty && zkCommitment != commitment) {
    return {
      'valid': false,
      'reason': 'cross_chain_commitment_mismatch',
    };
  }
  if (!_verifyMerkleProof(
    leaf: zkCommitment,
    proof: Map<String, dynamic>.from(receiptProof),
    root: receiptRoot,
  )) {
    return {
      'valid': false,
      'reason': 'cross_chain_merkle_proof_invalid',
    };
  }
  return {
    'valid': true,
    'reason': 'cross_chain_bridge_verified',
    'bridge_hash': bridgeHash,
    'zk_commitment': zkCommitment,
    'light_client_state_hash': expectedStateHash,
  };
}

String _normalizeBase64Url(String input) {
  final remainder = input.length % 4;
  if (remainder == 0) {
    return input;
  }
  return input + List.filled(4 - remainder, '=').join();
}

PortableVerificationResult verifyPrivacyQrPayload(String qrData) {
  final normalizedInput = qrData.trim();
  if (normalizedInput.isEmpty) {
    return PortableVerificationResult.invalid('qr_payload_required');
  }

  try {
    final payloadBytes = utf8.encode(normalizedInput);
    if (payloadBytes.length > 50000) {
      return PortableVerificationResult.invalid('qr_payload_too_large');
    }

    final compressed = base64Url.decode(_normalizeBase64Url(normalizedInput));
    if (compressed.length > 250000) {
      return PortableVerificationResult.invalid('qr_decompressed_too_large');
    }

    late final List<int> decompressed;
    try {
      decompressed = ZLibDecoder().decodeBytes(compressed);
    } on ArchiveException {
      return PortableVerificationResult.invalid('qr_invalid_compression');
    }
    if (decompressed.length > 250000) {
      return PortableVerificationResult.invalid('qr_decompressed_too_large');
    }

    final raw = utf8.decode(decompressed);
    final decoded = jsonDecode(raw);
    if (decoded is! Map) {
      return PortableVerificationResult.invalid('qr_invalid_payload');
    }

    final payload = Map<String, dynamic>.from(decoded);
    if (payload['type'] != 'novatrust-zk-qr') {
      return PortableVerificationResult.invalid('invalid_qr_type');
    }
    final qrHash = payload['qr_hash']?.toString().trim() ?? '';
    if (qrHash.isEmpty) {
      return PortableVerificationResult.invalid('qr_invalid_hash');
    }

    final expectedHash = _hash(
      {
        for (final entry in payload.entries) if (entry.key != 'qr_hash') entry.key: entry.value,
      },
      domain: 'zk_qr_payload',
    );
    if (qrHash != expectedHash) {
      return PortableVerificationResult.invalid('qr_integrity_failure');
    }

    final issuedAtText = payload['issued_at']?.toString().trim() ?? '';
    if (issuedAtText.isEmpty) {
      return PortableVerificationResult.invalid('qr_missing_issued_at');
    }
    final issuedAt = DateTime.tryParse(issuedAtText);
    if (issuedAt == null) {
      return PortableVerificationResult.invalid('qr_invalid_timestamp');
    }
    final hasTimezone = issuedAtText.endsWith('Z') ||
        RegExp(r'[+-]\d\d:\d\d$').hasMatch(issuedAtText);
    if (!hasTimezone) {
      return PortableVerificationResult.invalid('qr_timestamp_missing_timezone');
    }
    final issuedAtUtc = issuedAt.toUtc();
    final now = DateTime.now().toUtc();
    if (issuedAtUtc.isAfter(now)) {
      return PortableVerificationResult.invalid('qr_invalid_timestamp');
    }
    final ageSeconds = now.difference(issuedAtUtc).inSeconds;
    if (ageSeconds > 24 * 60 * 60) {
      return PortableVerificationResult.invalid('qr_expired');
    }

    final zkReceipt = payload['zk_receipt'];
    if (zkReceipt is! Map) {
      return PortableVerificationResult.invalid('qr_missing_zk_receipt');
    }

    final zkVerification = _verifyZkReceipt(Map<String, dynamic>.from(zkReceipt));
    if (zkVerification.valid != true) {
      return PortableVerificationResult.invalid(
        zkVerification.reason,
        payload: payload,
        zkReceipt: Map<String, dynamic>.from(zkReceipt),
      );
    }

    final bridgeValue = payload['bridge'];
    final bridge = bridgeValue is Map ? Map<String, dynamic>.from(bridgeValue) : null;
    final bridgeVerification = _verifyBridge(
      bridge,
      zkVerification.zkReceipt?['commitment']?.toString().trim() ?? '',
    );
    if (bridgeVerification != null && bridgeVerification['valid'] == false) {
      return PortableVerificationResult.invalid(
        bridgeVerification['reason']?.toString() ?? 'cross_chain_bridge_invalid',
        trustLevel: 'UNTRUSTED',
        payload: payload,
        zkReceipt: zkVerification.zkReceipt,
        bridge: bridge,
        verification: {
          'valid': false,
          'reason': bridgeVerification['reason']?.toString() ?? 'cross_chain_bridge_invalid',
          'zk_verification': zkVerification.verification,
          'bridge_verification': bridgeVerification,
        },
      );
    }

    final trustLevel = bridgeVerification == null ? 'PARTIAL' : 'HIGH';
    final valid = true;
    final reason = 'stateless_verified';

    return PortableVerificationResult(
      valid: valid,
      reason: reason,
      trustLevel: trustLevel,
      payload: payload,
      zkReceipt: zkVerification.zkReceipt,
      bridge: bridge,
      verification: {
        'valid': valid,
        'reason': reason,
        'zk_verification': zkVerification.verification,
        'bridge_verification': bridgeVerification,
      },
    );
  } on FormatException catch (error) {
    final message = error.message.toLowerCase();
    if (message.contains('base64')) {
      return PortableVerificationResult.invalid('qr_invalid_base64');
    }
    if (message.contains('utf')) {
      return PortableVerificationResult.invalid('qr_invalid_encoding');
    }
    return PortableVerificationResult.invalid('qr_invalid_json');
  } on RangeError {
    return PortableVerificationResult.invalid('qr_invalid_payload');
  } on StateError catch (error) {
    return PortableVerificationResult.invalid(error.message);
  }
}

String buildDemoPrivacyQrPayload() {
  final issuedAt = DateTime.now().toUtc().subtract(const Duration(minutes: 5));
  final receipt = <String, dynamic>{
    'type': 'novatrust-proof-receipt',
    'version': '1.0',
    'issuer': 'wallet-demo',
    'issued_at': issuedAt.toIso8601String(),
    'seal_id': 'seal-demo-001',
    'seal_hash': _repeat('a', 64),
    'trust_id': 'trust-demo-001',
    'packet_hash': _repeat('b', 64),
    'consensus_root': _repeat('c', 64),
    'validator_root': _repeat('d', 64),
    'aggregate_signature': _repeat('e', 128),
    'aggregate_scheme': 'bls-threshold',
    'signature_threshold': 2,
    'accepted_validators': ['validator-a', 'validator-b'],
    'rejected_validators': <String>[],
    'violations_hash': _repeat('f', 64),
    'consensus_reached': true,
    'total_votes_raw': 2,
    'total_votes_effective': 2,
    'node_health_hash': _repeat('1', 64),
    'node_health_status': 'healthy',
    'signer_set': [
      _repeat('0', 96),
      _repeat('1', 96),
    ],
    'signer_pop_proofs': [
      _repeat('2', 96),
      _repeat('3', 96),
    ],
  };

  final zkReceipt = _buildZkReceipt(
    receipt,
    hiddenFields: const ['issuer'],
    chainId: 'ETH',
    epoch: 12,
  );
  final bridge = _buildCrossChainBridge(
    zkReceipt,
    {
      'chain_id': 'ETH',
      'block_height': 12345678,
      'state_root': _hash(
        {'commitment': zkReceipt['commitment']},
        domain: 'demo_state_root',
      ),
      'validator_set_hash': _hash(
        {'signers': receipt['signer_set']},
        domain: 'demo_validator_set',
      ),
      'block_hash': _hash(
        {'seal_hash': receipt['seal_hash']},
        domain: 'demo_block_hash',
      ),
      'trusted_height': 12345600,
      'timestamp': issuedAt.toIso8601String(),
    },
    receiptBatch: [
      zkReceipt,
    ],
  );

  final bundle = <String, dynamic>{
    'type': 'novatrust-zk-qr',
    'version': '1.0',
    'issued_at': issuedAt.toIso8601String(),
    'zk_receipt': zkReceipt,
    'bridge': bridge,
  };
  bundle['qr_hash'] = _hash(
    {
      for (final entry in bundle.entries) entry.key: entry.value,
    },
    domain: 'zk_qr_payload',
  );
  return encodePrivacyQrPayload(bundle);
}

String encodePrivacyQrPayload(Map<String, dynamic> bundle) {
  final wrapper = Map<String, dynamic>.from(bundle);
  wrapper['qr_hash'] = _hash(
    {
      for (final entry in wrapper.entries) if (entry.key != 'qr_hash') entry.key: entry.value,
    },
    domain: 'zk_qr_payload',
  );
  return base64Url.encode(
    ZLibEncoder().encode(
      utf8.encode(_stableJson(_canonicalize(wrapper))),
    ),
  );
}
