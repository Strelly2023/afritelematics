# Replay Admissibility Proof Target

Assumptions:
- AX-DET-001
- AX-RPL-001
- AX-RPL-002
- AX-RPL-003
- AX-ADM-003

Inference steps:
1. Replay reconstructs state from recorded history.
2. Valid replay state equals original execution state.
3. Admissible execution implies replay validity and determinism.

Theorem:
Replay of valid history is unique and admissible.

Sketch:
Divergent replay is not admissible.
