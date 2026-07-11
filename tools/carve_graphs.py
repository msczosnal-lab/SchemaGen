"""Wyciaga grafy (schematic_graph.payload_json) wprost z surowych stron
uszkodzonej bazy SQLite — omija zniszczone wskazniki b-tree (jak .recover).

  python tools/carve_graphs.py <uszkodzony.db> [wyjscie.db]

Domyslne wyjscie: data/schemagen.carved.db  (swiezy schemat + odzyskane grafy).
Read-only na zrodle. Nic nie nadpisuje.
"""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _varint(buf, off):
    v = 0
    for i in range(9):
        b = buf[off + i]
        if i == 8:
            return (v << 8) | b, off + 9
        v = (v << 7) | (b & 0x7F)
        if not (b & 0x80):
            return v, off + i + 1
    return v, off + 9


def _serial_len(st):
    if st in (0, 8, 9):
        return 0
    if st in (1, 2, 3, 4):
        return st
    if st == 5:
        return 6
    if st in (6, 7):
        return 8
    if st >= 12:
        return (st - 12) // 2 if st % 2 == 0 else (st - 13) // 2
    return 0


def iter_json_texts(src_path):
    """Yielduje wszystkie wartosci kolumn TEXT bedace JSON-em (dict) — z surowych
    leaf/overflow pages, omijajac zniszczony b-tree. Zwraca (dict, raw_str)."""
    data = Path(src_path).read_bytes()
    if len(data) < 100 or data[:16] != b"SQLite format 3\x00":
        return {}
    ps = int.from_bytes(data[16:18], "big")
    if ps == 1:
        ps = 65536
    if ps < 512:
        return {}
    reserved = data[20]
    U = ps - reserved
    npages = len(data) // ps
    found = {}

    def overflow(pg, need):
        out = b""
        while pg and len(out) < need:
            base = (pg - 1) * ps
            nxt = int.from_bytes(data[base:base + 4], "big")
            out += data[base + 4: base + U]
            pg = nxt
        return out[:need]

    for p in range(1, npages + 1):
        base = (p - 1) * ps
        hdr = 100 if p == 1 else 0
        if base + hdr + 8 > len(data):
            continue
        if data[base + hdr] != 0x0D:  # tylko table b-tree leaf
            continue
        ncell = int.from_bytes(data[base + hdr + 3: base + hdr + 5], "big")
        cpa = base + hdr + 8
        for i in range(ncell):
            try:
                cpoff = int.from_bytes(data[cpa + i * 2: cpa + i * 2 + 2], "big")
                o = base + cpoff
                payload_size, o = _varint(data, o)
                _rowid, o = _varint(data, o)
                X = U - 35
                if payload_size <= X:
                    local = payload_size
                    ovpg = 0
                else:
                    M = ((U - 12) * 32 // 255) - 23
                    K = M + ((payload_size - M) % (U - 4))
                    local = K if K <= X else M
                    ovpg = int.from_bytes(data[o + local: o + local + 4], "big")
                body = data[o: o + local]
                if ovpg:
                    body += overflow(ovpg, payload_size - local)
                body = body[:payload_size]

                hs, ho = _varint(body, 0)
                serials = []
                pos = ho
                while pos < hs:
                    st, pos = _varint(body, pos)
                    serials.append(st)
                dpos = hs
                for st in serials:
                    ln = _serial_len(st)
                    val = body[dpos: dpos + ln]
                    dpos += ln
                    if st >= 13 and st % 2 == 1 and val[:1] == b'{':
                        try:
                            txt = val.decode("utf-8", "strict")
                            obj = json.loads(txt)
                        except Exception:
                            continue
                        if isinstance(obj, dict):
                            yield obj, txt
            except Exception:
                continue


def carve(src_path):
    found = {}
    for obj, txt in iter_json_texts(src_path):
        if obj.get("version") == 2 and "symbols" in obj:
            pid = obj.get("page_id")
            nsym = len(obj.get("symbols", []))
            if pid and (pid not in found or nsym > found[pid][1]):
                found[pid] = (txt, nsym, len(obj.get("lines", [])))
    return found


def main():
    if len(sys.argv) < 2:
        print("Uzycie: python tools/carve_graphs.py <uszkodzony.db> [wyjscie.db]")
        return 1
    src = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else str(ROOT / "data" / "schemagen.carved.db")

    found = carve(src)
    if not found:
        print("[!] Nie znaleziono zadnych grafow w %s" % src)
        return 2
    for pid, (_p, nsym, nlin) in sorted(found.items()):
        print("  %s : symboli=%d linii=%d" % (pid, nsym, nlin))

    sys.path.insert(0, str(ROOT))
    import backend.db as dbm
    import backend.paths as pm
    outp = Path(out)
    dbm.DB_PATH = outp
    pm.DB_PATH = outp
    if outp.exists():
        outp.unlink()
    dbm.init_db()
    import datetime
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    c = sqlite3.connect(outp)
    for pid, (payload, _s, _l) in found.items():
        c.execute("INSERT OR REPLACE INTO schematic_graph (page_id, payload_json, updated_at) VALUES (?,?,?)",
                  (pid, payload, now))
    c.commit()
    c.close()
    print("[OK] Zapisano %d grafow do %s" % (len(found), out))
    print("    Sprawdz: python tools/inspect_graph.py %s" % out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
