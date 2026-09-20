r"""Dual extraction (Camelot + Docling) of a bank's statements and key notes.

For each report:
  1. Find statement/note regions on each page from the text layer (headings and
     their position; two-page spreads are split into left and right halves).
  2. Method A, Camelot (stream), reads the table inside each region.
  3. Method B, Docling, reads the page; its tables are assigned to regions by
     their bounding box.
  4. Rows are matched to canonical items (the bank's profile) and the two
     methods are compared cell by cell. Disagreements are returned as
     conflicts; nothing is averaged or picked silently.

Usage:
    .venv\Scripts\python -m pipelines.banks.extract --bank=crdb            # all years
    .venv\Scripts\python -m pipelines.banks.extract --bank=crdb 2025 2024  # some years
Writes data/processed/<bank>/extraction_<year>.json
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from dataclasses import asdict, dataclass, field
from decimal import Decimal
from pathlib import Path

os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS", "1")  # Windows without symlink privilege
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

import pdfplumber  # noqa: E402

from pipelines.banks.items import ItemSpec, Section, normalise_label, parse_number  # noqa: E402
from pipelines.banks.profiles import BankProfile, profile_for  # noqa: E402

STOP_RE = re.compile(r"^(consolidated |bank.?s |bank |the bank.?s )?statements? of |^notes to (the )?(consolidated )?financial statements", re.I)


@dataclass
class Region:
    section: str
    page: int
    x0: float
    top: float
    x1: float
    bottom: float
    heading: str


@dataclass
class Row:
    method: str
    section: str
    page: int
    label: str
    numbers: list[Decimal]
    raw: str
    alt_label: str = ""


@dataclass
class Candidate:
    item: str
    section: str
    method: str
    page: int
    label: str
    current: Decimal | None
    comparative: Decimal | None
    raw: str
    numbers: list[Decimal] = field(default_factory=list)


# ---------------------------------------------------------------- regions

def _lines_by_half(page) -> list[tuple[str, float, float, float, float]]:
    """Return text lines as (text, x0, top, x1, bottom), grouped within each half
    of a two-page spread so side-by-side columns are not merged."""
    words = page.extract_words(keep_blank_chars=False, use_text_flow=False, x_tolerance=1.5)
    spread = page.width > page.height
    halves: dict[int, list] = {}
    for w in words:
        half = int((w["x0"] + w["x1"]) / 2 > page.width / 2) if spread else 0
        halves.setdefault(half, []).append(w)
    lines = []
    for half_words in halves.values():
        half_words.sort(key=lambda w: (round(w["top"]), w["x0"]))
        current: list = []
        for w in half_words:
            if current and abs(w["top"] - current[-1]["top"]) > 2.5:
                lines.append(current)
                current = []
            current.append(w)
        if current:
            lines.append(current)
    out = []
    for ws in lines:
        ws.sort(key=lambda w: w["x0"])
        out.append((" ".join(w["text"] for w in ws), min(w["x0"] for w in ws), min(w["top"] for w in ws),
                    max(w["x1"] for w in ws), max(w["bottom"] for w in ws)))
    return out


NUMERIC_RE = re.compile(r"\d{1,3}(,\d{3})+")


def candidate_pages(pdf_path: Path, sections: list[Section]) -> set[int]:
    """Fast pre-filter with the PDFium text layer: pages with many formatted
    numbers and at least one section heading. Skips narrative and contents pages."""
    import pypdfium2 as pdfium

    doc = pdfium.PdfDocument(str(pdf_path))
    heads = [re.compile(s.heading.lstrip("^"), re.I) for s in sections]
    pages = set()
    for i in range(len(doc)):
        text = doc[i].get_textpage().get_text_range()
        if len(NUMERIC_RE.findall(text)) < 15:
            continue
        flat = re.sub(r"\s+", " ", text.replace("’", "'")).lower()
        if any(h.search(flat) for h in heads):
            pages.add(i + 1)
    return pages


def find_regions(pdf, sections: list[Section], page_filter=None) -> list[Region]:
    regions: list[Region] = []
    for pno, page in enumerate(pdf.pages, start=1):
        if page_filter is not None and pno not in page_filter:
            continue
        spread = page.width > page.height
        lines = _lines_by_half(page)
        for half in ((0, 1) if spread else (0,)):
            hx0, hx1 = ((0, page.width / 2) if half == 0 else (page.width / 2, page.width)) if spread else (0, page.width)
            half_lines = sorted([ln for ln in lines if hx0 <= (ln[1] + ln[3]) / 2 < hx1], key=lambda ln: ln[2])
            for i, (txt, _x0, top, _x1, _bottom) in enumerate(half_lines):
                norm = normalise_label(txt)
                for s in sections:
                    if re.search(s.heading, norm, re.I):
                        end = page.height
                        for later in half_lines[i + 1:]:
                            ln = normalise_label(later[0])
                            # A heading never carries figures; "...reclassified to statement of profit or loss 1,595"
                            # is an OCI line, not the start of the next statement.
                            if (later[2] > top + 5 and STOP_RE.search(ln) and not re.search(s.heading, ln, re.I)
                                    and not NUMERIC_RE.search(later[0])):
                                end = later[2] - 1
                                break
                        regions.append(Region(s.code, pno, hx0, max(0.0, top - 2), hx1, end, txt))
    return _dedupe(regions)


def _dedupe(regions: list[Region]) -> list[Region]:
    """A wrapped heading can match twice in the same place; keep the first."""
    out: list[Region] = []
    for r in regions:
        if any(o.section == r.section and o.page == r.page and o.x0 == r.x0 and abs(o.top - r.top) < 30 for o in out):
            continue
        out.append(r)
    return out


# ---------------------------------------------------------------- rows

def _rows_from_cells(method: str, section: str, page: int, table_rows: list[list[str]]) -> list[Row]:
    rows: list[Row] = []
    for cells in table_rows:
        cells = [str(c or "").strip() for c in cells]
        if not any(cells):
            continue
        label_parts, label_cells, numbers, seen_number = [], [], [], False
        for c in cells:
            if not c:
                continue
            cell_text = []
            for part in c.split("\n") if "\n" in c else [c]:
                v = parse_number(part)
                if v is None:
                    if not seen_number:
                        label_parts.append(part)
                        cell_text.append(part)
                else:
                    if not label_parts and not seen_number and v == 0:
                        continue
                    seen_number = True
                    numbers.append(v)
            if cell_text and not NOTE_REF_RE.match(" ".join(cell_text)):
                label_cells.append(" ".join(cell_text))
        label = _clean_label(" ".join(label_parts))
        # Fallback label: the text cell nearest the numbers. Needed when a table
        # detector merges neighbouring page text into the first column of a row.
        alt = _clean_label(label_cells[-1]) if len(label_cells) > 1 else ""
        rows.append(Row(method, section, page, label, numbers, " | ".join(c for c in cells if c), alt))
    return rows


NOTE_REF_RE = re.compile(r"^\d{1,2}[a-z]?(\.\d+)*\s*(\([a-z0-9ivx\-,]+\))*$", re.I)


def _clean_label(text: str) -> str:
    label = normalise_label(text)
    # Drop a trailing note reference such as "10", "11(a)", "24(a-c)", "39 (iii)", "24a".
    label = re.sub(r"\s+\d{1,2}[a-z]?(\s*\([a-z0-9ivx\-]+\))*$", "", label)
    return re.sub(r"\s+\d{1,2}\s*\([a-z0-9ivx\-]+\)$", "", label).strip()


def camelot_rows(pdf_path: Path, regions: list[Region], page_heights: dict[int, float]) -> list[Row]:
    import camelot

    rows: list[Row] = []
    for r in regions:
        h = page_heights[r.page]
        area = f"{r.x0},{h - r.top},{r.x1},{h - r.bottom}"
        try:
            tables = camelot.read_pdf(str(pdf_path), pages=str(r.page), flavor="stream", table_areas=[area])
        except Exception as exc:  # camelot raises on empty areas
            rows.append(Row("camelot", r.section, r.page, "", [], f"ERROR {exc}"))
            continue
        for t in tables:
            rows.extend(_rows_from_cells("camelot", r.section, r.page, t.df.values.tolist()))
    return rows


def text_rows(pdf_path: Path, regions: list[Region], page_heights: dict[int, float]) -> list[Row]:
    """Third reader: the PDF's own text lines inside each region (pdfplumber words grouped by
    line). Trailing number tokens are the values; everything before them is the label. It is
    independent of Camelot's column detection and Docling's layout model."""
    rows: list[Row] = []
    with pdfplumber.open(pdf_path) as pdf:
        for r in regions:
            page = pdf.pages[r.page - 1]
            crop = page.within_bbox((r.x0, max(0.0, r.top), r.x1, min(page.height, r.bottom)))
            words = crop.extract_words(keep_blank_chars=False, use_text_flow=False, x_tolerance=1.5)
            words.sort(key=lambda w: (round(w["top"]), w["x0"]))
            lines: list[list[dict]] = []
            for w in words:
                if lines and abs(w["top"] - lines[-1][-1]["top"]) <= 2.5:
                    lines[-1].append(w)
                else:
                    lines.append([w])
            for ws in lines:
                ws.sort(key=lambda w: w["x0"])
                tokens = [w["text"] for w in ws]
                i = len(tokens)
                while i > 0 and parse_number(tokens[i - 1]) is not None:
                    i -= 1
                numbers = [parse_number(x) for x in tokens[i:]]
                rows.append(Row("text", r.section, r.page, _clean_label(" ".join(tokens[:i])), numbers,
                                " | ".join(tokens)[:2000]))
    return rows


_DOCLING = None


def _docling_converter():
    global _DOCLING
    if _DOCLING is None:
        from docling.datamodel.base_models import InputFormat
        from docling.datamodel.pipeline_options import PdfPipelineOptions
        from docling.document_converter import DocumentConverter, PdfFormatOption

        opts = PdfPipelineOptions(do_ocr=False, do_table_structure=True)
        _DOCLING = DocumentConverter(format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=opts)})
    return _DOCLING


def docling_rows(pdf_path: Path, regions: list[Region], page_heights: dict[int, float]) -> list[Row]:
    conv = _docling_converter()
    rows: list[Row] = []
    pages = sorted({r.page for r in regions})
    for p in pages:
        res = conv.convert(str(pdf_path), page_range=(p, p))
        doc = res.document
        page_regions = [r for r in regions if r.page == p]
        for tb in doc.tables:
            if not tb.prov:
                continue
            prov = tb.prov[0]
            bbox = prov.bbox.to_top_left_origin(page_height=page_heights[p])
            cx, cy = (bbox.l + bbox.r) / 2, (bbox.t + bbox.b) / 2
            owners = [r for r in page_regions if r.x0 <= cx <= r.x1 and r.top - 5 <= cy <= r.bottom + 5]
            if not owners:
                # A table can start above the heading line Docling assigned; fall back to horizontal overlap.
                owners = [r for r in page_regions if r.x0 <= cx <= r.x1 and bbox.b >= r.top]
            df = tb.export_to_dataframe(doc=doc)
            table_rows = [list(map(str, df.columns))] + df.astype(str).values.tolist()
            for owner in owners[:1]:
                rows.extend(_rows_from_cells("docling", owner.section, p, table_rows))
    return rows


# ---------------------------------------------------------------- matching

def _profile_label(profile: BankProfile, label: str) -> str:
    """Undo a report's known text-layer problems before matching (see the profile)."""
    for wrong, right in profile.label_fixes:
        label = label.replace(wrong, right)
    for noise in profile.label_noise:
        label = re.sub(noise, "", label)
    return label


def is_stage_row(numbers: list[Decimal]) -> bool:
    """Stage 1 + stage 2 + stage 3 = total: a stage breakdown, not a GROUP/BANK column row."""
    return len(numbers) >= 4 and numbers[-4] + numbers[-3] + numbers[-2] == numbers[-1] and numbers[-1] != 0


def match(rows: list[Row], profile: BankProfile, year: int) -> list[Candidate]:
    sections = profile.all_sections
    by_section = {s.code: s for s in sections}
    out: list[Candidate] = []
    seen: dict[tuple[str, str, str], int] = {}  # (method, section, item) -> rows matched so far
    for i, row in enumerate(rows):
        sec = by_section.get(row.section)
        if sec is None or not row.label:
            continue
        labels = [_profile_label(profile, row.label)] + ([_profile_label(profile, row.alt_label)] if row.alt_label else [])
        for spec in sec.items:
            role, label = None, None
            for candidate_label in labels:
                if spec.mode == "stage3_of_4":
                    if re.search(spec.pattern.replace("{year}", str(year)), candidate_label):
                        role, label = "current", candidate_label
                    elif re.search(spec.pattern.replace("{year}", str(year - 1)), candidate_label):
                        role, label = "comparative", candidate_label
                elif re.search(spec.pattern.replace("{year}", str(year)), candidate_label):
                    role, label = "pair", candidate_label
                if role:
                    break
            if role is None:
                continue
            numbers = row.numbers
            # Label wrapped onto the next row: take that row's numbers.
            # Join a label wrapped onto the next row. In a GROUP/BANK layout only when this row has no
            # figures except a note number; otherwise a split row would borrow the next line's values.
            wrapped = len(numbers) < 2 if profile.columns != "group_first" else (
                len(numbers) == 0 or (len(numbers) == 1 and numbers[0] == numbers[0].to_integral_value()
                                      and 0 < numbers[0] < 100))
            if wrapped and i + 1 < len(rows) and rows[i + 1].section == row.section:
                nxt = rows[i + 1]
                if len(nxt.numbers) >= 2 and len(nxt.label) < profile.wrap_label_max:
                    numbers, label = nxt.numbers, f"{label} {nxt.label}".strip()
            if spec.mode in ("stage3_by_total", "total_by_order") and not is_stage_row(numbers):
                continue
            if spec.mode == "columns" and profile.columns == "group_first":
                if is_stage_row(numbers):
                    continue  # a stage breakdown row that shares the label (e.g. gross loans by stage)
                if len(numbers) < 4:
                    continue  # a split row; guessing which two columns survived could pick BANK figures
            cur, comp = _pick(spec, numbers, profile.columns)
            if role == "current":
                comp = None
            elif role == "comparative":
                cur, comp = None, cur
            if spec.mode == "total_by_order":
                key = (row.method, sec.code, spec.code)
                n = seen.get(key, 0)
                seen[key] = n + 1
                if n > 1:
                    continue  # GROUP current, GROUP prior come first; later blocks are BANK
                cur, comp = (numbers[-1], None) if n == 0 else (None, numbers[-1])
            out.append(Candidate(spec.code, sec.code, row.method, row.page, label, cur, comp, row.raw, numbers))
    return out


def _pick(spec: ItemSpec, numbers: list[Decimal], columns: str = "last2") -> tuple[Decimal | None, Decimal | None]:
    if spec.mode == "stage3_of_4":
        # Row is stage 1, stage 2, stage 3, total. The total is kept in `numbers` for the tie check.
        return (numbers[-2], None) if len(numbers) >= 4 else (None, None)
    if spec.mode == "stage3_by_total":
        # Either year's row can be the right one; the resolver keeps the row whose total ties to gross loans.
        return numbers[-2], numbers[-2]
    if spec.mode == "columns_min2" and len(numbers) < 4:
        return (numbers[-2], numbers[-1]) if len(numbers) >= 2 else (None, None)  # GROUP-only row
    if columns == "group_first" and len(numbers) >= 4:
        return numbers[-4], numbers[-3]  # GROUP current, GROUP prior, BANK current, BANK prior
    if len(numbers) >= 2:
        return numbers[-2], numbers[-1]
    return None, None


# ---------------------------------------------------------------- driver

def extract_year(profile: BankProfile, year: int, methods: tuple[str, ...] = ("camelot", "docling")) -> dict:
    pdf_path = profile.pdf_path(year)
    sections = profile.all_sections
    t0 = time.time()
    with pdfplumber.open(pdf_path) as pdf:
        heights = {i: p.height for i, p in enumerate(pdf.pages, start=1)}
        regions = find_regions(pdf, sections, candidate_pages(pdf_path, sections))
    rows: list[Row] = []
    timings = {}
    for m in methods:
        t = time.time()
        reader = {"camelot": camelot_rows, "docling": docling_rows, "text": text_rows}[m]
        rows += reader(pdf_path, regions, heights)
        timings[m] = round(time.time() - t, 1)
    candidates = match(rows, profile, year)
    result = {
        "fiscal_year": year,
        "file": pdf_path.as_posix(),
        "regions": [asdict(r) for r in regions],
        "candidates": [asdict(c) for c in candidates],
        "row_count": {m: sum(1 for r in rows if r.method == m) for m in methods},
        "seconds": {"total": round(time.time() - t0, 1), **timings},
    }
    out_dir = profile.processed_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    # Decimals are written as strings so no value passes through a float.
    # Only a full dual run may replace the file the resolver reads; single-method
    # runs (for debugging) write alongside it.
    name = f"extraction_{year}.json" if set(methods) == {"camelot", "docling"} else \
        f"extraction_{year}_{'_'.join(methods)}.json"
    (out_dir / name).write_text(json.dumps(result, indent=1, default=str), encoding="utf-8")
    return result


def main(argv: list[str]) -> None:
    bank = next((a.split("=", 1)[1] for a in argv if a.startswith("--bank=")), None)
    profile = profile_for(bank or "")
    if profile is None:
        raise SystemExit("Usage: python -m pipelines.banks.extract --bank=<nmb|crdb> [years] [--method=camelot]")
    years = [int(a) for a in argv if a.isdigit()] or profile.years
    methods = tuple(a.split("=", 1)[1] for a in argv if a.startswith("--method=")) or ("camelot", "docling")
    for y in years:
        res = extract_year(profile, y, methods)
        items = sorted({c["item"] for c in res["candidates"]})
        print(f"{y}: regions={len(res['regions'])} rows={res['row_count']} items={len(items)} time={res['seconds']}")


if __name__ == "__main__":
    main(sys.argv[1:])
