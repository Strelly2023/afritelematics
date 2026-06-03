"""Display serializers for reference-only traceability metadata."""

from rest_framework import serializers


class GovernanceReferenceSerializer(serializers.Serializer):
    type = serializers.CharField()
    id = serializers.CharField()


class TraceabilityBridgeSerializer(serializers.Serializer):
    status = serializers.CharField()
    reference_only = serializers.BooleanField()
    runtime_authority = serializers.BooleanField()
    enforcement_authority = serializers.BooleanField()
    projection_dependency = serializers.BooleanField()


class TraceabilitySerializer(serializers.Serializer):
    governance_traceability = GovernanceReferenceSerializer(many=True)
    traceability_bridge = TraceabilityBridgeSerializer()
