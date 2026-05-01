from afritech_v1.governance.rules import evaluate
from afritech_v1.proof.proof_engine import generate_proof
from afritech_v1.security.security_engine import enforce
from afritech_v1.vm.vm_engine import execute
from afritech_v1.epoch.epoch_engine import apply

def run(action: str):
    decision = evaluate(action)
    proof = generate_proof(decision)
    enforce(proof)
    result = execute(action)
    apply(result)
    return result