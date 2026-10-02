#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright 2026 Bapplington
# SPDX-License-Identifier: GPL-2.0-or-later
"""Read-only EB v3 payload probe. No automatic emulator mounting or extraction.

Block size is explicit: older EB scripts assume 16/64 bytes, while inspected
NBA Live 19 archives use 4096. This tool supports only chunkzip version 2.
"""
import argparse
import pathlib
import struct
import zlib


def decode_chunkzip(data, limit=64 * 1024 * 1024):
    if len(data) < 40 or data[:8] != b"chunkzip":
        raise ValueError("Expected chunkzip header")
    version, size, chunk_size, chunks = struct.unpack_from(">IIII", data, 8)
    if version != 2 or not 0 < size <= limit or not chunk_size or chunks != (size + chunk_size - 1) // chunk_size:
        raise ValueError("Unsupported or invalid chunkzip dimensions")
    pos, output = 40, bytearray()
    for _ in range(chunks):
        pos = ((pos + 7) // 8) * 8
        if pos % 16 != 8:
            pos += 8
        if pos + 8 > len(data):
            raise ValueError("Truncated chunk descriptor")
        stored, method = struct.unpack_from(">II", data, pos)
        pos += 8
        if stored > len(data) - pos:
            raise ValueError("Truncated chunk payload")
        expected = min(chunk_size, size - len(output))
        payload = data[pos:pos + stored]
        if method == 4:
            decoded = payload
        elif method == 1:
            inflater = zlib.decompressobj(-15)
            decoded = inflater.decompress(payload, expected + 1)
            if not inflater.eof or inflater.unused_data or inflater.unconsumed_tail:
                raise ValueError("Invalid or oversized deflate stream")
        else:
            raise ValueError(f"Unsupported chunkzip method {method}")
        if len(decoded) != expected:
            raise ValueError("Decoded chunk size mismatch")
        output.extend(decoded)
        pos += stored
    return bytes(output)


def probe(path, guest_path, block_size):
    if block_size not in (16, 64, 4096):
        raise ValueError("Unsupported block size")
    with pathlib.Path(path).open("rb") as source:
        source.seek(0, 2)
        actual_size = source.tell()
        source.seek(0)
        header = source.read(32)
        if len(header) != 32:
            raise ValueError("Truncated EB header")
        magic, version, count, flags, names, name_bytes, width, folder_width, folders, declared = struct.unpack(">2sHIIIIBBHQ", header)
        if magic != b"EB" or version != 3 or actual_size != declared or count > 200000 or width < 3:
            raise ValueError("Invalid EB header")
        folder_start = (names + count * width + 15) // 16 * 16
        stride = 20 if flags & 0x10000 else 16
        if names < 48 + count * stride or not folder_width or not folders or name_bytes > 8 * 1024 * 1024 or folder_start + folders * folder_width > names + name_bytes or names + name_bytes > actual_size:
            raise ValueError("Invalid name region")
        source.seek(folder_start)
        folder_data = source.read(folders * folder_width)
        folder_names = [folder_data[i * folder_width:(i + 1) * folder_width].split(b"\0", 1)[0].decode() for i in range(folders)]
        source.seek(names)
        records = source.read(count * width)
        for index in range(count):
            record = records[index * width:(index + 1) * width]
            folder = struct.unpack_from(">H", record)[0]
            if folder >= folders:
                raise ValueError("Invalid folder index")
            name = record[2:].split(b"\0", 1)[0].decode()
            full = "/".join(filter(None, (folder_names[folder], name))).replace("\\", "/")
            if full.casefold() != guest_path.replace("\\", "/").casefold():
                continue
            if 48 + (index + 1) * stride > names:
                raise ValueError("Entry table overlaps names")
            source.seek(48 + index * stride)
            offset, compressed, size = struct.unpack(">III", source.read(12))
            offset *= block_size
            if offset < names + name_bytes or offset >= actual_size:
                raise ValueError("Payload outside archive")
            source.seek(offset)
            # Bounded private read; compressed record lengths differ from chunk
            # header lengths in this variant, so never treat them as proof.
            data = source.read(min(actual_size - offset, 64 * 1024 * 1024))
            return decode_chunkzip(data)
        raise ValueError("Path absent from name table")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive")
    parser.add_argument("path")
    parser.add_argument("--block-size", type=int, required=True)
    args = parser.parse_args()
    payload = probe(args.archive, args.path, args.block_size)
    print(f"Decoded {len(payload)} bytes; signature {payload[:16].hex()}")
