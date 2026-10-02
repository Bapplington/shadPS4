<!-- SPDX-FileCopyrightText: Copyright 2026 Bapplington -->
<!-- SPDX-License-Identifier: GPL-2.0-or-later -->
# NBA Live 19 investigation

This branch contains AI-assisted diagnostic tooling, reviewed against synthetic fixtures and locally owned game data. It is not a gameplay fix or a supported EB filesystem backend. No game payload, firmware, keys, save data or raw user logs are included.

## Confirmed on 2026-10-02

- A local CUSA11355 test copy reaches menus. Match entry and smooth gameplay remain unconfirmed.
- Inspected EB v3 entries in graphics_fix.big (flags 0x00510c00) require 4096-byte offset blocks. The older 16-byte interpretation returned invalid payloads, including name-table bytes.
- With explicit 4096-byte offsets and bounded chunkzip v2 decoding, renderbins.xml parses as XML (17999 bytes) and player_shadow.rnafx starts with RSF (23344 bytes). A separate private extractor agrees byte for byte.
- Prior crashes using invalid extracted files do not establish a renderer defect. Missing loose-file opens may be ordinary archive fallback probes.

## Diagnostic reader

Run `python -m unittest discover -s scripts -p test_eb_probe.py -v` for synthetic tests. They cover multiple aligned chunks, stored/deflate methods, malformed sizes, truncated inputs, unsupported methods, oversized deflate output and wrong EB block sizes.

Run `python scripts/eb_probe.py YOUR_PRIVATE_ARCHIVE data/common/config/renderbins.xml --block-size 4096` to inspect a privately owned archive. The command reports size and signature only; it never extracts or modifies files. The block size must be explicit. Only chunkzip version 2 and methods 1/4 are accepted. Other archive variants remain unsupported.

## Next evidence needed

Use validated payloads in a disposable overlay and isolated profile, retain a baseline and compare actual loading. Trace guest archive-loader behavior and unresolved calls before implementing emulator APIs. Name-table presence alone does not establish missing content, a filesystem bug or the cause of a graphics stall. No gameplay fix has been validated, and no protocol evidence supports a community server implementation yet.

The user repeated the loading route with 56 structurally validated graphics files and reported the same black/loading screen. This experiment did not resolve the stall.

## First emulator implementation

The fallback libc did not register vsnprintf (NID Q2V+iqvjgC0), which the local game imports. Its existing formatting helper also ignored the caller's size and formatted into a size-n temporary with unlimited writes before strcpy. This branch now registers guest va_list-based vsnprintf and bounds all formatter output, preserving the required-length return value even when truncated or called with zero capacity. Synthetic sanitizer tests check canaries, zero/one-byte capacities, long strings, register arguments and overflow-area arguments. These are concrete API and memory-safety fixes; whether the game executes this import on the stalled route and whether it affects gameplay remain unknown.

Preserved original game and patch directories must remain untouched. Keep all copyrighted payloads and private runtime files outside Git.
