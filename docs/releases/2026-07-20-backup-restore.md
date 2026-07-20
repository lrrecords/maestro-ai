# Backup Restore Evidence - 2026-07-20

## Purpose

This record captures a restore test using a real repository data artifact copied into a scratch workspace.

## Verification Environment

- Workspace: `c:\Users\brett\Documents\maestro-ai`
- Source artifact: `data/maestro_build_progress.md`
- Test area: `tmp_restore_test`
- Date: 2026-07-20

## Restore Test Procedure

1. Copy `data/maestro_build_progress.md` into a scratch working file.
2. Record the SHA-256 hash of the scratch file.
3. Copy the scratch file into a backup location.
4. Delete the scratch file.
5. Restore the scratch file from the backup copy.
6. Recompute the SHA-256 hash and compare it to the original.

## Result

```text
Source       : C:\Users\brett\Documents\maestro-ai\data\maestro_build_progress.md
Scratch      : C:\Users\brett\Documents\maestro-ai\tmp_restore_test\maestro_build_progress.md
Backup       : C:\Users\brett\Documents\maestro-ai\tmp_restore_test\backup\maestro_build_progress.md
OriginalHash : BB9E957723FFE529941F424CC890FC039F612B587AD031408D1D2AFF5A60215C
RestoredHash : BB9E957723FFE529941F424CC890FC039F612B587AD031408D1D2AFF5A60215C
Match        : True
```

## Interpretation

- The restored file matched the original file byte-for-byte by SHA-256 hash.
- This demonstrates a successful backup and restore cycle for a representative operational data artifact.

## Remaining Evidence Gaps

- Incident drill output
- Supplier review/sign-off record

## Notes

- This test used a scratch copy so it did not alter the tracked repository artifact.
- The `tmp_restore_test` directory can be discarded after the release archive is finalized.