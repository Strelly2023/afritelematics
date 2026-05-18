alias_validator.py                      forbid_topology_change.py
ast_call_order_validator.py             identity_validator.py
ast_import_validator.py                 import_topology_enforcement.py
              invariant_validator.py
completeness_guard.py                   semantic_concept_validator.py
           surface_validator.py
cross_concept_validator.py              witness_validator.py
forbid_raw_epoch_access.py
ostrinov@MacBookAir afritelematics % 



ast_witness_validator.py  
constitutional_validation.py 
alias_validator.py      


for f in afritech/ci/*.py; do
  name=$(basename "$f" .py)
  if [[ "$name" != "alias_validator" && "$name"!="ast_witness_validator"&& "$name"!="constitutional_validation" &&"$name" != "__init__" ]]; then
    echo "▶ Running afritech.ci.$name"
    python3 -m afritech.ci.$name || exit 1
  fi
done