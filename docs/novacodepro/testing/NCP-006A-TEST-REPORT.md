# NCP-006A Test Report

Executed:

- `python3 -m pytest afritech/tests/api/test_novacodepro_auth_sessions.py afritech/tests/api/test_novacodepro_platform_api.py afritech/tests/api/test_novacodepro_ncp006a_api.py -q`
- `python3 -m pytest afritech/tests/novacodepro/test_ncp006a_architecture_service.py -q`
- `cd novacodepro_portal && npm test`
- `cd novacodepro_portal && npm run build`

Result:

- backend architecture API tests: passed
- backend architecture service tests: passed
- portal unit suite: passed
- portal build: passed

Browser-driven E2E and accessibility certification were not run in this session because no browser automation runtime is exposed here.
