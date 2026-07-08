# Internal QA Release Checklist

## Required Checks
- Internal QA config present
- Live payments disabled
- Real charging disabled
- External payouts disabled
- Production credentials forbidden
- Public launch forbidden
- Controlled pilot forbidden unless separately approved
- APKs exist with checksums
- Release manifests exist
- App icons exist
- Button registry exists
- API contract routes exist or are mocked
- No debug-only labels in release metadata
- No production-ready claims in release artifacts

## Evidence
- Pytest output
- APK checksum output
- Server validation output
- Screenshots or recordings from device QA runs
- Internal QA test report
