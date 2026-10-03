# Opt-in archive read diagnostics

This NBARevive fork adds bounded metadata logging around the existing kernel ReadFile helper, shared by read, readv and preadv. It is disabled unless NBAREVIVE_ARCHIVE_TRACE=1 is present when the process starts. Only top-level /app0 and /hostapp .big paths are eligible. Logs contain paired IDs, guest archive path, file position, requested byte count and actual read return value; no buffers, host paths, saves or keys are logged. The budget is 20,000 read pairs per process. Logs must remain local and private. Normal read behavior, return values and asset contents are unchanged.

The synthetic test covers path filtering, disabled tracing, concurrent ID uniqueness and budget exhaustion. A Windows compilation and gameplay trace are still required. This diagnostic does not fix gameplay. Correlate successful/short/failed reads and ranges with independently validated archive metadata; an open-probe miss alone does not show a failed archive load. A successful byte read also does not prove guest decoding or loader completion. Begin without an end may reflect a pending read or abrupt termination rather than a deadlock. No upstream contribution is implied.

Source change prepared with AI assistance. Retain upstream copyrights and GPL license. Do not commit raw game logs or payloads.

The path filter accepts redundant slashes immediately after the mount prefix, matching observed /app0//archive.big opens, but still rejects nested paths and traversal. This normalization affects trace eligibility only; no guest file path or I/O behavior is changed.
