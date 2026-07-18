# NCP-007 Code Generation Security Model

The Development Studio enforces:

- tenant and workspace scoping
- permission checks for repository, generation, validation, review, approval, commit, push, and command execution
- protected-path controls
- command allowlisting
- patch application safety checks
- evidence generation for governed actions

Sensitive operations remain approval-gated where policy requires them. The implementation uses deterministic local behavior for automated tests and does not claim live provider verification without external credentials.
