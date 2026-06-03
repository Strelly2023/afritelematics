"""
Read-only serializers for the Explainability Graph.

These serializers expose graph nodes and edges for display/API use only.

Constitutional Law
------------------
Serializers display graph data.
Serializers do not validate runtime truth.
Serializers do not enforce governance.
Serializers do not mutate receipts.
Serializers do not create authority.
"""

from __future__ import annotations

try:
    from rest_framework import serializers
except Exception:  # pragma: no cover
    serializers = None  # type: ignore[assignment]


if serializers is not None:

    class GraphNodeSerializer(serializers.Serializer):
        """Read-only graph node serializer."""

        type = serializers.CharField(read_only=True)
        id = serializers.CharField(read_only=True)
        label = serializers.CharField(read_only=True)

        graph_status = serializers.CharField(read_only=True)
        data_classification = serializers.CharField(read_only=True)
        output_classification = serializers.CharField(read_only=True)

        read_only = serializers.BooleanField(read_only=True)
        display_only = serializers.BooleanField(read_only=True)
        non_authoritative = serializers.BooleanField(read_only=True)
        runtime_authority = serializers.BooleanField(read_only=True)
        validation_authority = serializers.BooleanField(read_only=True)


    class GraphEdgeSerializer(serializers.Serializer):
        """Read-only graph edge serializer."""

        source_id = serializers.CharField(read_only=True)
        target_id = serializers.CharField(read_only=True)
        relation = serializers.CharField(read_only=True)

        graph_status = serializers.CharField(read_only=True)
        relationship_classification = serializers.CharField(read_only=True)
        data_classification = serializers.CharField(read_only=True)
        output_classification = serializers.CharField(read_only=True)

        read_only = serializers.BooleanField(read_only=True)
        display_only = serializers.BooleanField(read_only=True)
        non_authoritative = serializers.BooleanField(read_only=True)
        runtime_authority = serializers.BooleanField(read_only=True)
        validation_authority = serializers.BooleanField(read_only=True)

        influences_runtime = serializers.BooleanField(read_only=True)
        influences_replay = serializers.BooleanField(read_only=True)
        influences_proof = serializers.BooleanField(read_only=True)


    class ExplainabilityGraphSerializer(serializers.Serializer):
        """Read-only explainability graph serializer."""

        graph_status = serializers.CharField(read_only=True)
        data_classification = serializers.CharField(read_only=True)
        output_classification = serializers.CharField(read_only=True)
        relationship_classification = serializers.CharField(read_only=True)

        read_only = serializers.BooleanField(read_only=True)
        display_only = serializers.BooleanField(read_only=True)
        non_authoritative = serializers.BooleanField(read_only=True)

        runtime_authority = serializers.BooleanField(read_only=True)
        validation_authority = serializers.BooleanField(read_only=True)

        influences_runtime = serializers.BooleanField(read_only=True)
        influences_replay = serializers.BooleanField(read_only=True)
        influences_proof = serializers.BooleanField(read_only=True)

        nodes = GraphNodeSerializer(many=True, read_only=True)
        edges = GraphEdgeSerializer(many=True, read_only=True)


else:

    class GraphNodeSerializer:  # type: ignore[no-redef]
        """Fallback placeholder when DRF is unavailable."""


    class GraphEdgeSerializer:  # type: ignore[no-redef]
        """Fallback placeholder when DRF is unavailable."""


    class ExplainabilityGraphSerializer:  # type: ignore[no-redef]
        """Fallback placeholder when DRF is unavailable."""