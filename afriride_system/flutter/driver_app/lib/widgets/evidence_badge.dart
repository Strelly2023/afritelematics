import 'package:flutter/material.dart';

/// Evidence Badge
///
/// Purpose:
/// Displays evidence state in the Driver App UI.
///
/// Constitutional Properties:
/// - display-only
/// - read-only
/// - authority-neutral
/// - no replay mutation
/// - no receipt generation
/// - no pricing computation
///
/// This widget does NOT:
/// - validate evidence
/// - create evidence
/// - approve evidence
/// - override evidence
/// - mutate replay
///
/// Evidence validation must happen before rendering.
class EvidenceBadge extends StatelessWidget {
  final String label;
  final bool verified;

  const EvidenceBadge({
    super.key,
    required this.label,
    required this.verified,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Semantics(
      label: "$label evidence ${verified ? "verified" : "unverified"}",
      child: Container(
        padding: const EdgeInsets.symmetric(
          horizontal: 10,
          vertical: 6,
        ),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(999),
          border: Border.all(
            color: verified
                ? theme.colorScheme.primary
                : theme.colorScheme.error,
          ),
        ),
        child: Text(
          verified ? "$label: Verified" : "$label: Not verified",
          style: theme.textTheme.labelMedium?.copyWith(
            color: verified
                ? theme.colorScheme.primary
                : theme.colorScheme.error,
            fontWeight: FontWeight.w600,
          ),
        ),
      ),
    );
  }
}