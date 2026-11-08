#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""
Add or refresh the 64-byte firmware header used by the NETGEAR GS110EMX
stock firmware (checked by its web UI before flashing):

  0x00..0x20  zero padding
  0x20..0x30  board name, NUL padded
  0x30..0x34  CRC32 (big endian), see below
  0x34..0x38  total image length including header (big endian)
  0x38..0x40  version string, NUL padded
  0x40..      payload (U-Boot FIT image, optionally followed by rootfs)

The CRC is a standard reflected CRC32 computed over the whole image with
the header bytes 0x20..0x40 zeroed, but without the final XOR.
"""

import argparse
import struct
import sys
import zlib

HDR_LEN = 0x40


def build_header(board, version, payload):
    total = HDR_LEN + len(payload)
    crc = zlib.crc32(bytes(HDR_LEN) + payload) ^ 0xFFFFFFFF
    return (
        bytes(0x20)
        + board.encode().ljust(16, b"\0")[:16]
        + struct.pack(">II", crc, total)
        + version.encode().ljust(8, b"\0")[:8]
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--board", default="GS110EMX")
    parser.add_argument("--version", default="9.9.9.9",
                        help="max 7 chars; a high value avoids stock downgrade warnings")
    parser.add_argument("--update", action="store_true",
                        help="input already has a header: replace it instead of prepending")
    parser.add_argument("input")
    parser.add_argument("output")
    args = parser.parse_args()

    if len(args.version.encode()) > 7 or len(args.board.encode()) > 15:
        sys.exit("board name or version string too long")

    with open(args.input, "rb") as f:
        data = f.read()

    if args.update:
        if len(data) < HDR_LEN or data[0x20:0x30].rstrip(b"\0") != args.board.encode():
            sys.exit("--update: input does not start with a %s header" % args.board)
        data = data[HDR_LEN:]

    with open(args.output, "wb") as f:
        f.write(build_header(args.board, args.version, data))
        f.write(data)


if __name__ == "__main__":
    main()
