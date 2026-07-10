# NovaRide Mobile v2026.1.1 Rollback

1. Preserve all `v2026.1.1` immutable files, manifests, checksums, and provenance.
2. Record rollback reason, approver, timestamp, affected app, and evidence reference.
3. Repoint only the convenience alias:
   - `/novaride/rider-latest-public-pilot.apk`
   - `/novaride/driver-latest-public-pilot.apk`
4. Verify alias URL status, content type, APK ZIP bytes, and checksum.
5. Do not delete audit evidence or immutable versioned files.
6. Notify pilot participants with affected version, rollback version, and required reinstall guidance.

Rollback target: `2026.1.0`.

