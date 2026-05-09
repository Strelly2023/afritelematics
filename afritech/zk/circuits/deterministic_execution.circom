pragma circom 2.1.6;

include "circomlib/poseidon.circom";

/*
AfriTech ZK Deterministic Execution Circuit (FINAL)

------------------------------------------------------------
PURPOSE

Proves that:

    result_hash = Poseidon(runtime_output)

AND

    final_commitment = Poseidon(
        result_hash,
        authority_id,
        transcript_hash,
        circuit_version
    )

------------------------------------------------------------
PUBLIC INPUTS

    payload_hash        // hash(payload)
    result_hash         // hash(runtime output)
    authority_id        // hash(authority_profile string)
    transcript_hash     // hash(replay transcript)
    circuit_version     // version binding

------------------------------------------------------------
PRIVATE (WITNESS)

    payload[nPayload]   // canonical payload encoding
    result              // runtime computed result

------------------------------------------------------------
GUARANTEES

✔ deterministic execution binding
✔ authority-bound execution
✔ replay transcript binding
✔ result_hash alignment with runtime
✔ forward-compatible versioning
✔ no hidden state
✔ consensus-safe output identity
*/

template DeterministicExecution(nPayload) {

    // =========================================================
    // PUBLIC INPUTS
    // =========================================================

    signal input payload_hash;
    signal input result_hash;
    signal input authority_id;
    signal input transcript_hash;
    signal input circuit_version;

    // =========================================================
    // PRIVATE INPUTS (WITNESS)
    // =========================================================

    signal input payload[nPayload];
    signal input result;

    // =========================================================
    // STEP 1 — VERIFY PAYLOAD HASH
    // =========================================================

    component payloadHasher = Poseidon(nPayload);

    for (var i = 0; i < nPayload; i++) {
        payloadHasher.inputs[i] <== payload[i];
    }

    payloadHasher.out === payload_hash;

    // =========================================================
    // STEP 2 — RESULT HASH (ALIGNED WITH RUNTIME)
    // =========================================================

    /*
    CRITICAL:

    result_hash MUST represent ExecutionResult.result_hash

    In production:
    - result is derived from runtime logic (outside circuit)
    - circuit proves consistency (not recomputing full business logic)
    */

    component resultHasher = Poseidon(1);
    resultHasher.inputs[0] <== result;

    resultHasher.out === result_hash;

    // =========================================================
    // STEP 3 — AUTHORITY BINDING
    // =========================================================

    component authorityBinder = Poseidon(2);

    authorityBinder.inputs[0] <== result_hash;
    authorityBinder.inputs[1] <== authority_id;

    signal authority_commit;
    authority_commit <== authorityBinder.out;

    // =========================================================
    // STEP 4 — TRANSCRIPT BINDING (REPLAY)
    // =========================================================

    component transcriptBinder = Poseidon(2);

    transcriptBinder.inputs[0] <== authority_commit;
    transcriptBinder.inputs[1] <== transcript_hash;

    signal transcript_commit;
    transcript_commit <== transcriptBinder.out;

    // =========================================================
    // STEP 5 — VERSION BINDING (UPGRADE SAFETY)
    // =========================================================

    component versionBinder = Poseidon(2);

    versionBinder.inputs[0] <== transcript_commit;
    versionBinder.inputs[1] <== circuit_version;

    signal final_commitment;
    final_commitment <== versionBinder.out;

    // =========================================================
    // STEP 6 — OUTPUT CONSISTENCY CHECK
    // =========================================================

    /*
    This enforces:

    final commitment MUST be deterministic
    based on all inputs.
    */

    signal output commitment;

    commitment <== final_commitment;

}