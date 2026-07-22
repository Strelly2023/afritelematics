# RC build and reproducibility assessment

Classification: `FAILED`

Source commit: `82fabb8000bd5c4d512b307f0f61db09197af6a2`

The aggregate API build ran from a clean detached worktree at
`v2026.1.5-rc.1`. Dependency installation and the application wheel build
completed inside an intermediate Docker layer. Docker did not complete image
export or create either requested immutable tag. Repeated image inspection
returned no matching image, and subsequent daemon queries did not complete
successfully.

No digest, SBOM, registry push, second isolated build, or reproducibility claim
is available. Remaining images were not built after the first critical artifact
failed because partial artifacts cannot satisfy the release gate.
