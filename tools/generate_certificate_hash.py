import yaml
import json
import hashlib
from pathlib import Path


CERT_PATH = Path("afritech/proof/runtime_certificate.yaml")


def compute_hash(payload):
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


doc = yaml.safe_load(CERT_PATH.read_text())

cert = doc["runtime_certificate"]

payload = dict(cert)
payload.pop("signature", None)

hash_value = compute_hash(payload)

print("\n✅ NEW PAYLOAD HASH:\n")
print(hash_value)