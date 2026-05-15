"""
afritech.proof.witness
======================

Canonical deterministic witness topology package.

This package governs:
- replay witnesses
- execution witnesses
- mutation witnesses
- transcript witnesses
- witness aggregation

Canonical identity:

    afritech.proof.witness
"""

from afritech.proof.witness.execution_witness import *
from afritech.proof.witness.mutation_witness import *
from afritech.proof.witness.replay_witness import *
from afritech.proof.witness.transcript_witness import *
from afritech.proof.witness.witness_bundle import *

__all__ = [

    "CANONICAL_IDENTITY",

]