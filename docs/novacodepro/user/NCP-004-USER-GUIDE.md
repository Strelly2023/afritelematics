# NCP-004 User Guide

Open NovaAI at `/novacodepro/ai`.

Typical flow:

1. create an AI execution from a request
2. analyse the request
3. answer any clarification prompts
4. generate requirements
5. generate and validate a plan
6. request approval
7. approve from an authorized role
8. execute the governed steps
9. verify the result
10. review evidence and replay

What to expect:

- the system fails closed when tenant, workspace, or approval context is missing
- the execution timeline and evidence are stored server-side
- execution can be cancelled or rolled back if required

Known limitation:

- browser-driven E2E automation is not yet committed in this repository
