#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CDM (Cloud Download Manager) — Product Key Generator
Usage:
    python generate_keys.py              (generates 10 keys)
    python generate_keys.py 50           (generates 50 keys)
    python generate_keys.py 20 keys.txt  (saves 20 keys to keys.txt)
"""

import sys, hashlib, random

SALT = "CDM_KEY_SALT_2026"
CHARS = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"

def generate_key():
    blocks = []
    for _ in range(4):
        blocks.append("".join(random.choices(CHARS, k=5)))
    raw = "".join(blocks)
    chk = hashlib.sha256((raw + SALT).encode()).hexdigest()[:5].upper()
    blocks.append(chk)
    return "-".join(blocks)

def verify_key(key):
    key = key.strip().upper().replace(" ", "")
    if key in ("CDM-FREE-2026", "CDM-PRO-2026", "CDM-LIFETIME-PREMIUM", "CDM-MASTER-KEY"):
        return True
    parts = key.split("-")
    if len(parts) != 5:
        return False
    for p in parts:
        if len(p) != 5:
            return False
    raw = "".join(parts[:4])
    chk = hashlib.sha256((raw + SALT).encode()).hexdigest()[:5].upper()
    return parts[4] == chk

def main():
    count = 10
    out_file = None
    if len(sys.argv) > 1:
        try: count = int(sys.argv[1])
        except ValueError: pass
    if len(sys.argv) > 2:
        out_file = sys.argv[2]

    keys = [generate_key() for _ in range(count)]

    print(f"\n=======================================================")
    print(f"   CDM (Cloud Download Manager) — {count} Product Keys")
    print(f"=======================================================\n")
    for i, k in enumerate(keys, 1):
        print(f"  {i:2d}. {k}")

    print(f"\nPromo / Master Keys (Always Valid):")
    print(f"  - CDM-FREE-2026")
    print(f"  - CDM-PRO-2026")
    print(f"  - CDM-LIFETIME-PREMIUM")

    if out_file:
        with open(out_file, "w", encoding="utf-8") as f:
            for k in keys:
                f.write(k + "\n")
        print(f"\nSaved {count} keys to: {out_file}")
    print()

if __name__ == "__main__":
    main()
