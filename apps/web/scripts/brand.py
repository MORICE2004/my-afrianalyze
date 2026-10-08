"""Writes the static AfriEdge brand files from the master geometry in src/components/brand/mark.ts.

    python scripts/brand.py            # SVGs in public/brand and src/app/icon.svg
    node scripts/brand-png.cjs         # PNG renders of those SVGs (favicon, app icon, report logo)

The SVGs are the master assets. The wordmark in afriedge-logo.svg is set as text in IBM Plex Sans with system
fallbacks; inside the web app the wordmark is live text in the same face.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
src = (ROOT / "src/components/brand/mark.ts").read_text(encoding="utf-8")
paths = re.findall(r'(?:leftLeg|rightLeg|edge): "([^"]+)"', src)
bars = re.findall(r"\{ x: ([\d.]+), y: ([\d.]+), w: ([\d.]+), h: ([\d.]+) \}", src)
shapes = "".join(f'<path d="{d}"/>' for d in paths) + "".join(
    f'<rect x="{x}" y="{y}" width="{w}" height="{h}"/>' for x, y, w, h in bars)


def mark(fill: str) -> str:
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" fill="{fill}">{shapes}</svg>\n'


def logo(fill: str) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 206 48" fill="{fill}">'
            f'<g>{shapes}</g><text x="60" y="36" font-family="IBM Plex Sans, Inter, Helvetica Neue, Arial, sans-serif" '
            f'font-size="32" font-weight="600" letter-spacing="-0.6">AfriEdge</text></svg>\n')


out = ROOT / "public/brand"
out.mkdir(parents=True, exist_ok=True)
(out / "afriedge-mark.svg").write_text(mark("#141414"), encoding="utf-8")
(out / "afriedge-mark-white.svg").write_text(mark("#ffffff"), encoding="utf-8")
(out / "afriedge-logo.svg").write_text(logo("#141414"), encoding="utf-8")
(out / "afriedge-logo-white.svg").write_text(logo("#ffffff"), encoding="utf-8")
# Favicon: the mark on a white tile so it reads on light and dark browser tabs alike.
(ROOT / "src/app/icon.svg").write_text(
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="12" fill="#ffffff"/>'
    f'<g transform="translate(8 8)" fill="#141414">{shapes}</g></svg>\n', encoding="utf-8")
print("brand SVGs written")
