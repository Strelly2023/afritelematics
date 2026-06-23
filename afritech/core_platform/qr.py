"""Small PNG QR-style renderer for NovaTrust verification URLs."""

from __future__ import annotations

import hashlib
import struct
import zlib


def render_qr_png(value: str, *, scale: int = 6, modules: int = 25) -> bytes:
    """Render a deterministic QR-like PNG without external dependencies.

    This is intentionally dependency-free. It is not a standards-compliant QR
    encoder, but it gives auditors a scannable-looking visual binding while the
    URL remains printed in the PDF and exposed through the API.
    """

    matrix = _matrix(value, modules=modules)
    size = modules * scale
    rows = []
    for y in range(size):
        module_y = y // scale
        row = bytearray([0])
        for x in range(size):
            module_x = x // scale
            row.extend(b"\x11\x20\x33" if matrix[module_y][module_x] else b"\xff\xff\xff")
        rows.append(bytes(row))
    raw = b"".join(rows)
    return (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0))
        + _chunk(b"IDAT", zlib.compress(raw, 9))
        + _chunk(b"IEND", b"")
    )


def _matrix(value: str, *, modules: int) -> list[list[bool]]:
    digest = hashlib.sha256(value.encode("utf-8")).digest()
    bits = "".join(f"{byte:08b}" for byte in digest)
    matrix = [[False for _ in range(modules)] for _ in range(modules)]
    _finder(matrix, 0, 0)
    _finder(matrix, modules - 7, 0)
    _finder(matrix, 0, modules - 7)
    cursor = 0
    for y in range(modules):
        for x in range(modules):
            if matrix[y][x]:
                continue
            if _in_finder(x, y, modules):
                continue
            matrix[y][x] = bits[cursor % len(bits)] == "1"
            cursor += 1
    return matrix


def _finder(matrix: list[list[bool]], x0: int, y0: int) -> None:
    for y in range(y0, y0 + 7):
        for x in range(x0, x0 + 7):
            edge = x in {x0, x0 + 6} or y in {y0, y0 + 6}
            center = x0 + 2 <= x <= x0 + 4 and y0 + 2 <= y <= y0 + 4
            matrix[y][x] = edge or center


def _in_finder(x: int, y: int, modules: int) -> bool:
    return (
        (x < 7 and y < 7)
        or (x >= modules - 7 and y < 7)
        or (x < 7 and y >= modules - 7)
    )


def _chunk(kind: bytes, data: bytes) -> bytes:
    crc = zlib.crc32(kind + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", crc)
