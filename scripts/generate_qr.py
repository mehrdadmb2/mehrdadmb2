#!/usr/bin/env python3
"""Generate repository-local SVG QR codes for donation addresses."""
from pathlib import Path
import qrcode

OUT = Path(__file__).resolve().parents[1] / "assets" / "qr"
OUT.mkdir(parents=True, exist_ok=True)

ITEMS = {
    "ton.svg": "UQBQU9KnjwIsdSGwG08b3L43Vy_wPlCg_3FaK9m4N2Toj84k",
    "trc20-usdt.svg": "TYbqxzEWrvYPnLvGtk6JY6Sbh8DMqfjcYq",
    "ethereum.svg": "0x968C2fD883a2004276f5e627Fe38654137601c51",
    "bitcoin.svg": "bc1q6knq0g4w9axt7t204y3e4hk4kz4zkh8vxj2e3a",
    "solana.svg": "7otC7qwCWqmrzbVA3XykjsZHbuKgrqaP2hE25NnByRDP",
    "bnb.svg": "0x968C2fD883a2004276f5e627Fe38654137601c51",
    "polygon.svg": "0x968C2fD883a2004276f5e627Fe38654137601c51",
    "tron.svg": "TGYN1zzeGUjuXipVPvS4gTUivQyAu7GNUm",
}


def make_svg(data: str, size: int = 9, border: int = 2) -> str:
    qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=size, border=border)
    qr.add_data(data)
    qr.make(fit=True)
    matrix = qr.get_matrix()
    rows = len(matrix)
    cols = len(matrix[0])
    dim = rows * size
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {dim} {dim}" role="img" aria-label="QR code">',
        f'<rect width="{dim}" height="{dim}" fill="#ffffff"/>',
        '<g fill="#111111">',
    ]
    for y, row in enumerate(matrix):
        for x, dark in enumerate(row):
            if dark:
                parts.append(f'<rect x="{x*size}" y="{y*size}" width="{size}" height="{size}"/>')
    parts.append('</g></svg>')
    return ''.join(parts)

for filename, value in ITEMS.items():
    (OUT / filename).write_text(make_svg(value), encoding="utf-8")

print(f"generated {len(ITEMS)} QR SVG files in {OUT}")
