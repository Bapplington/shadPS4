# SPDX-FileCopyrightText: Copyright 2026 Bapplington
# SPDX-License-Identifier: GPL-2.0-or-later
import pathlib
import struct
import tempfile
import unittest
import zlib

from eb_probe import decode_chunkzip, probe


def fixture(payload, stored=False):
    compressor = zlib.compressobj(wbits=-15)
    stream = payload if stored else compressor.compress(payload) + compressor.flush()
    header = b"chunkzip" + struct.pack(">IIIIIIII", 2, len(payload), 4096, 1, 16, 0, 0, 0)
    return header + struct.pack(">II", len(stream), 4 if stored else 1) + stream


class ChunkzipTests(unittest.TestCase):
    def test_multiple_chunks_with_alignment(self):
        payloads = [b"abc" * 1365 + b"!", b"tail"]
        blob = bytearray(b"chunkzip" + struct.pack(">IIIIIIII", 2, 4100, 4096, 2, 16, 0, 0, 0))
        for payload in payloads:
            while len(blob) % 16 != 8:
                blob.append(0)
            compressor = zlib.compressobj(wbits=-15)
            stream = compressor.compress(payload) + compressor.flush()
            blob.extend(struct.pack(">II", len(stream), 1) + stream)
        self.assertEqual(decode_chunkzip(blob), b"".join(payloads))

    def test_unknown_method(self):
        data = bytearray(fixture(b"payload"))
        struct.pack_into(">I", data, 44, 99)
        with self.assertRaises(ValueError):
            decode_chunkzip(data)

    def test_deflate_bomb(self):
        data = bytearray(fixture(b"A" * 100000))
        struct.pack_into(">I", data, 12, 7)
        with self.assertRaises(ValueError):
            decode_chunkzip(data)

    def test_deflate(self):
        data = b"synthetic XML and shader content" * 80
        self.assertEqual(decode_chunkzip(fixture(data)), data)

    def test_stored(self):
        data = bytes(range(256))
        self.assertEqual(decode_chunkzip(fixture(data, True)), data)

    def test_truncated(self):
        with self.assertRaises(ValueError):
            decode_chunkzip(fixture(b"payload")[:-1])

    def test_size_limit(self):
        with self.assertRaises(ValueError):
            decode_chunkzip(fixture(b"large" * 100), limit=20)

    def test_wrong_declared_size(self):
        data = bytearray(fixture(b"payload"))
        struct.pack_into(">I", data, 12, 3)
        with self.assertRaises(ValueError):
            decode_chunkzip(bytes(data))


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = pathlib.Path(self.temp.name) / "synthetic.big"
        self.payload = b"synthetic payload"
        data = bytearray(4096)
        struct.pack_into(">2sHIIIIBBHQ", data, 0, b"EB", 3, 1, 0x510c00, 80, 48, 16, 16, 1, 4096 + len(fixture(self.payload)))
        struct.pack_into(">III", data, 48, 1, 0, len(fixture(self.payload)))
        data[80:96] = struct.pack(">H", 0) + b"asset.bin\0".ljust(14, b"\0")
        data[96:112] = b"data\0".ljust(16, b"\0")
        self.path.write_bytes(data + fixture(self.payload))

    def test_explicit_alignment(self):
        self.assertEqual(probe(self.path, "DATA\\asset.bin", 4096), self.payload)

    def test_wrong_alignment_rejected(self):
        for block in (16, 64):
            with self.assertRaises(ValueError):
                probe(self.path, "data/asset.bin", block)

    def test_absent_path(self):
        with self.assertRaises(ValueError):
            probe(self.path, "missing.bin", 4096)

    def test_truncated_header(self):
        self.path.write_bytes(b"EB")
        with self.assertRaises(ValueError):
            probe(self.path, "data/asset.bin", 4096)


if __name__ == "__main__":
    unittest.main()
