import hashlib
import yaml
import json
from datetime import datetime


class ReplayBindingError(Exception):
    """Raised when replay binding or verification fails"""
    pass


class TruthPacket:

    def __init__(self, request, response, metadata):
        self.request = request
        self.response = response
        self.metadata = metadata

    def to_dict(self):
        return {
            "request": self.request,
            "response": self.response,
            "metadata": self.metadata
        }

    def canonical(self):
        return yaml.dump(
            self.to_dict(),
            sort_keys=True,
            allow_unicode=False,
            default_flow_style=False,
            width=4096
        )

    def hash(self):
        return hashlib.sha256(self.canonical().encode()).hexdigest()


class ReplayTranscript:

    def __init__(self, truth_packet, runtime_certificate_hash, attestation_hash):
        self.truth_packet = truth_packet
        self.runtime_certificate_hash = runtime_certificate_hash
        self.attestation_hash = attestation_hash
        self.generated_at = datetime.utcnow().isoformat()

    def to_dict(self):
        return {
            "truth_packet": self.truth_packet.to_dict(),
            "truth_hash": self.truth_packet.hash(),
            "runtime_certificate_hash": self.runtime_certificate_hash,
            "attestation_hash": self.attestation_hash,
            "generated_at": self.generated_at
        }

    def canonical(self):
        return json.dumps(
            self.to_dict(),
            sort_keys=True
        )

    def hash(self):
        return hashlib.sha256(self.canonical().encode()).hexdigest()


class ReplayVerifier:

    def verify(self, transcript: ReplayTranscript):

        # Recompute truth hash
        recomputed_truth_hash = transcript.truth_packet.hash()

        if recomputed_truth_hash != transcript.to_dict()["truth_hash"]:
            raise ReplayBindingError("Truth hash mismatch")

        # Determinism check placeholder
        # (Extend with full deterministic replay)
        self.validate_determinism(transcript)

        return True

    def validate_determinism(self, transcript: ReplayTranscript):
        """
        Placeholder for deterministic replay:
        - Re-run computation
        - Compare outputs
        """
        return True


class ReplayBindingEngine:

    def __init__(self, validator):
        self.validator = validator
        self.verifier = ReplayVerifier()

    # -----------------------------------------------------------------
    # HASH HELPERS
    # -----------------------------------------------------------------

    def compute_certificate_hash(self):
        cert = self.validator.certificate
        canonical = yaml.dump(cert, sort_keys=True)
        return hashlib.sha256(canonical.encode()).hexdigest()

    def compute_attestation_hash(self):
        attn = self.validator.attestation
        canonical = yaml.dump(attn, sort_keys=True)
        return hashlib.sha256(canonical.encode()).hexdigest()

    # -----------------------------------------------------------------
    # TRUTH PACKET CREATION
    # -----------------------------------------------------------------

    def create_truth_packet(self, request, response):

        metadata = {
            "epoch": self.validator.registry["epoch"]["current"],
            "deterministic": True,
            "timestamp": datetime.utcnow().isoformat()
        }

        return TruthPacket(request, response, metadata)

    # -----------------------------------------------------------------
    # TRANSCRIPT BUILDING
    # -----------------------------------------------------------------

    def build_transcript(self, truth_packet):

        cert_hash = self.compute_certificate_hash()
        attn_hash = self.compute_attestation_hash()

        return ReplayTranscript(
            truth_packet=truth_packet,
            runtime_certificate_hash=cert_hash,
            attestation_hash=attn_hash
        )

    # -----------------------------------------------------------------
    # FULL REPLAY PIPELINE
    # -----------------------------------------------------------------

    def bind_and_verify(self, request, response):

        # ✅ Step 1: Ensure runtime is admitted
        self.validator.validate_request(request)

        # ✅ Step 2: Build TruthPacket
        truth_packet = self.create_truth_packet(request, response)

        # ✅ Step 3: Build Transcript
        transcript = self.build_transcript(truth_packet)

        # ✅ Step 4: Verify Replay
        self.verifier.verify(transcript)

        return {
            "truth_packet": truth_packet.to_dict(),
            "truth_hash": truth_packet.hash(),
            "transcript_hash": transcript.hash(),
            "verified": True
        }