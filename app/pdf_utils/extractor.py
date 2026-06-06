import io
import re
import fitz
import pdfplumber
import camelot
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from PIL import Image
import numpy as np


@dataclass
class TextFragment:
    text: str
    page: int
    x0: float
    y0: float
    x1: float
    y1: float
    font_name: str
    font_size: float
    is_bold: bool
    is_italic: bool
    column: Optional[int] = None


@dataclass
class TableCell:
    text: str
    row: int
    col: int
    x0: float
    y0: float
    x1: float
    y1: float


@dataclass
class Table:
    page: int
    rows: int
    cols: int
    data: List[List[str]]
    cells: List[List[TableCell]]
    x0: float
    y0: float
    x1: float
    y1: float


@dataclass
class TocEntry:
    level: int
    title: str
    page: int
    children: List["TocEntry"]


@dataclass
class PDFMetadata:
    title: Optional[str]
    author: Optional[str]
    subject: Optional[str]
    keywords: Optional[str]
    creator: Optional[str]
    producer: Optional[str]
    creation_date: Optional[str]
    mod_date: Optional[str]
    pages: int
    encrypted: bool
    page_size: Tuple[float, float]


class PDFExtractor:
    def __init__(self, pdf_bytes: bytes):
        self.pdf_bytes = pdf_bytes
        self._fitz_doc = fitz.open("pdf", pdf_bytes)
        self._plumber_doc = pdfplumber.open(io.BytesIO(pdf_bytes))
        self.page_count = len(self._fitz_doc)

    def close(self):
        self._fitz_doc.close()
        self._plumber_doc.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def get_metadata(self) -> PDFMetadata:
        doc = self._fitz_doc
        meta = doc.metadata
        first_page = doc[0]
        rect = first_page.rect
        return PDFMetadata(
            title=meta.get("title"),
            author=meta.get("author"),
            subject=meta.get("subject"),
            keywords=meta.get("keywords"),
            creator=meta.get("creator"),
            producer=meta.get("producer"),
            creation_date=meta.get("creationDate"),
            mod_date=meta.get("modDate"),
            pages=self.page_count,
            encrypted=doc.is_encrypted,
            page_size=(rect.width, rect.height)
        )

    def extract_toc(self) -> List[TocEntry]:
        doc = self._fitz_doc
        toc = doc.get_toc()
        
        entries = []
        stack = []
        
        for level, title, page in toc:
            entry = TocEntry(level=level, title=title, page=page, children=[])
            
            while stack and stack[-1].level >= level:
                stack.pop()
            
            if stack:
                stack[-1].children.append(entry)
            else:
                entries.append(entry)
            
            stack.append(entry)
        
        if not entries:
            entries = self._generate_toc_from_headings()
        
        return entries

    def _generate_toc_from_headings(self) -> List[TocEntry]:
        all_fragments = []
        for page_num in range(self.page_count):
            fragments = self._extract_page_layout(page_num)
            all_fragments.extend(fragments)
        
        font_sizes = [f.font_size for f in all_fragments if f.font_size > 0]
        if not font_sizes:
            return []
        
        unique_sizes = sorted(list(set(font_sizes)), reverse=True)
        size_to_level = {size: i + 1 for i, size in enumerate(unique_sizes[:5])}
        
        entries = []
        stack = []
        
        for frag in all_fragments:
            if frag.font_size in size_to_level and len(frag.text.strip()) > 0:
                level = size_to_level[frag.font_size]
                text = frag.text.strip()
                
                if len(text) > 100:
                    continue
                
                entry = TocEntry(level=level, title=text, page=frag.page + 1, children=[])
                
                while stack and stack[-1].level >= level:
                    stack.pop()
                
                if stack:
                    stack[-1].children.append(entry)
                else:
                    entries.append(entry)
                
                stack.append(entry)
        
        return entries

    def _detect_columns(self, page_num: int, fragments: List[TextFragment]) -> List[TextFragment]:
        if len(fragments) < 10:
            for f in fragments:
                f.column = 0
            return fragments
        
        doc = self._fitz_doc
        page = doc[page_num]
        page_width = page.rect.width
        
        x_coords = [f.x0 for f in fragments]
        x_coords.sort()
        
        gaps = []
        for i in range(1, len(x_coords)):
            gap = x_coords[i] - x_coords[i-1]
            if gap > page_width * 0.05:
                gaps.append((x_coords[i-1] + gap / 2, gap))
        
        if not gaps:
            for f in fragments:
                f.column = 0
            return fragments
        
        gaps.sort(key=lambda x: x[1], reverse=True)
        largest_gap = gaps[0]
        column_divider = largest_gap[0]
        
        for f in fragments:
            if f.x1 < column_divider:
                f.column = 0
            elif f.x0 > column_divider:
                f.column = 1
            else:
                f.column = 0 if (f.x0 + f.x1) / 2 < column_divider else 1
        
        return fragments

    def extract_text(self, page_num: Optional[int] = None) -> Dict[str, Any]:
        if page_num is not None:
            fragments = self._extract_page_layout(page_num)
            fragments = self._detect_columns(page_num, fragments)
            fragments = self._sort_by_reading_order(fragments)
            text = "\n".join([f.text for f in fragments if f.text.strip()])
            return {
                "page": page_num + 1,
                "text": text
            }
        else:
            result = {"pages": []}
            full_text = []
            for p in range(self.page_count):
                page_result = self.extract_text(p)
                result["pages"].append(page_result)
                full_text.append(page_result["text"])
            result["full_text"] = "\n\n".join(full_text)
            return result

    def _sort_by_reading_order(self, fragments: List[TextFragment]) -> List[TextFragment]:
        if not fragments:
            return []
        
        has_columns = any(f.column is not None and f.column > 0 for f in fragments)
        
        if has_columns:
            max_col = max(f.column for f in fragments if f.column is not None)
            sorted_frags = []
            for col in range(max_col + 1):
                col_frags = [f for f in fragments if f.column == col]
                col_frags.sort(key=lambda f: (f.y0, f.x0))
                sorted_frags.extend(col_frags)
            return sorted_frags
        else:
            line_height = self._estimate_line_height(fragments)
            fragments.sort(key=lambda f: (round(f.y0 / (line_height * 0.5)) * line_height, f.x0))
            return fragments

    def _estimate_line_height(self, fragments: List[TextFragment]) -> float:
        if len(fragments) < 2:
            return 12.0
        
        y_coords = sorted(list(set([round(f.y0, 1) for f in fragments])))
        if len(y_coords) < 2:
            return 12.0
        
        gaps = [y_coords[i+1] - y_coords[i] for i in range(len(y_coords)-1)]
        gaps = [g for g in gaps if g > 0]
        
        if not gaps:
            return 12.0
        
        return sum(gaps) / len(gaps)

    def extract_layout(self, page_num: Optional[int] = None) -> Dict[str, Any]:
        if page_num is not None:
            fragments = self._extract_page_layout(page_num)
            fragments = self._detect_columns(page_num, fragments)
            fragments = self._sort_by_reading_order(fragments)
            
            columns_detected = max((f.column for f in fragments if f.column is not None), default=0) + 1
            
            return {
                "page": page_num + 1,
                "columns_detected": columns_detected,
                "fragments": [asdict(f) for f in fragments]
            }
        else:
            result = {"pages": []}
            for p in range(self.page_count):
                page_result = self.extract_layout(p)
                result["pages"].append(page_result)
            return result

    def _extract_page_layout(self, page_num: int) -> List[TextFragment]:
        plumber_page = self._plumber_doc.pages[page_num]
        words = plumber_page.extract_words(
            keep_blank_chars=False,
            use_text_flow=True,
            extra_attrs=["fontname", "size"]
        )
        
        fragments = []
        for word in words:
            font_name = word.get("fontname", "")
            fragments.append(TextFragment(
                text=word.get("text", ""),
                page=page_num,
                x0=float(word.get("x0", 0)),
                y0=float(word.get("top", 0)),
                x1=float(word.get("x1", 0)),
                y1=float(word.get("bottom", 0)),
                font_name=font_name,
                font_size=float(word.get("size", 0)),
                is_bold=bool("Bold" in font_name or "bold" in font_name or "BD" in font_name),
                is_italic=bool("Italic" in font_name or "italic" in font_name or "IT" in font_name)
            ))
        
        if not fragments:
            fitz_page = self._fitz_doc[page_num]
            text_dict = fitz_page.get_text("dict")
            for block in text_dict.get("blocks", []):
                if block.get("type") == 0:
                    for line in block.get("lines", []):
                        for span in line.get("spans", []):
                            bbox = span.get("bbox", [0, 0, 0, 0])
                            font_name = span.get("font", "")
                            fragments.append(TextFragment(
                                text=span.get("text", ""),
                                page=page_num,
                                x0=float(bbox[0]),
                                y0=float(bbox[1]),
                                x1=float(bbox[2]),
                                y1=float(bbox[3]),
                                font_name=font_name,
                                font_size=float(span.get("size", 0)),
                                is_bold=bool(span.get("flags", 0) & 1 << 5 or "Bold" in font_name),
                                is_italic=bool(span.get("flags", 0) & 1 << 6 or "Italic" in font_name)
                            ))
        
        return fragments

    def extract_tables(self, page_num: Optional[int] = None) -> Dict[str, Any]:
        pdf_io = io.BytesIO(self.pdf_bytes)
        
        if page_num is not None:
            tables = self._extract_page_tables(page_num, pdf_io)
            return {
                "page": page_num + 1,
                "tables": [self._table_to_dict(t) for t in tables],
                "table_count": len(tables)
            }
        else:
            result = {"pages": [], "total_tables": 0}
            for p in range(self.page_count):
                page_result = self.extract_tables(p)
                result["pages"].append(page_result)
                result["total_tables"] += page_result["table_count"]
            return result

    def _extract_page_tables(self, page_num: int, pdf_io: io.BytesIO) -> List[Table]:
        tables = []
        
        try:
            camelot_tables = camelot.read_pdf(
                pdf_io,
                pages=str(page_num + 1),
                flavor="lattice",
                suppress_stdout=True
            )
            
            for idx, ct in enumerate(camelot_tables):
                if ct.df.empty:
                    continue
                
                data = ct.df.values.tolist()
                rows, cols = len(data), len(data[0]) if data else 0
                
                cells = []
                for r in range(rows):
                    row_cells = []
                    for c in range(cols):
                        cell_text = str(data[r][c]).strip() if data[r][c] is not None else ""
                        row_cells.append(TableCell(
                            text=cell_text,
                            row=r,
                            col=c,
                            x0=ct.bbox[0] + c * (ct.bbox[2] - ct.bbox[0]) / cols,
                            y0=ct.bbox[1] + r * (ct.bbox[3] - ct.bbox[1]) / rows,
                            x1=ct.bbox[0] + (c + 1) * (ct.bbox[2] - ct.bbox[0]) / cols,
                            y1=ct.bbox[1] + (r + 1) * (ct.bbox[3] - ct.bbox[1]) / rows
                        ))
                    cells.append(row_cells)
                
                tables.append(Table(
                    page=page_num,
                    rows=rows,
                    cols=cols,
                    data=data,
                    cells=cells,
                    x0=ct.bbox[0],
                    y0=ct.bbox[1],
                    x1=ct.bbox[2],
                    y1=ct.bbox[3]
                ))
        except Exception as e:
            pass
        
        if not tables:
            tables = self._fallback_table_detection(page_num)
        
        return tables

    def _fallback_table_detection(self, page_num: int) -> List[Table]:
        fragments = self._extract_page_layout(page_num)
        if len(fragments) < 4:
            return []
        
        fragments.sort(key=lambda f: (f.y0, f.x0))
        
        y_coords = sorted(list(set([round(f.y0, 1) for f in fragments])))
        potential_rows = []
        
        for y in y_coords:
            row_frags = [f for f in fragments if abs(f.y0 - y) < 5]
            if len(row_frags) >= 2:
                x_centers = sorted([(f.x0 + f.x1) / 2 for f in row_frags])
                gaps = [x_centers[i+1] - x_centers[i] for i in range(len(x_centers)-1)]
                if all(g > 10 for g in gaps):
                    potential_rows.append((y, row_frags))
        
        if len(potential_rows) < 2:
            return []
        
        cols_count = max(len(r[1]) for r in potential_rows)
        aligned_rows = []
        
        for y, row_frags in potential_rows:
            if len(row_frags) == cols_count:
                aligned_rows.append((y, row_frags))
            else:
                pass
        
        if len(aligned_rows) < 2:
            return []
        
        rows = len(aligned_rows)
        cols = cols_count
        data = [["" for _ in range(cols)] for _ in range(rows)]
        cells = [[None for _ in range(cols)] for _ in range(rows)]
        
        page = self._fitz_doc[page_num]
        page_height = page.rect.height
        
        for r_idx, (y, row_frags) in enumerate(aligned_rows):
            sorted_frags = sorted(row_frags, key=lambda f: f.x0)
            for c_idx, frag in enumerate(sorted_frags[:cols]):
                data[r_idx][c_idx] = frag.text
                cells[r_idx][c_idx] = TableCell(
                    text=frag.text,
                    row=r_idx,
                    col=c_idx,
                    x0=frag.x0,
                    y0=page_height - frag.y1,
                    x1=frag.x1,
                    y1=page_height - frag.y0
                )
        
        all_cells_flat = [c for row in cells for c in row if c is not None]
        x0 = min(c.x0 for c in all_cells_flat)
        y0 = min(c.y0 for c in all_cells_flat)
        x1 = max(c.x1 for c in all_cells_flat)
        y1 = max(c.y1 for c in all_cells_flat)
        
        return [Table(
            page=page_num,
            rows=rows,
            cols=cols,
            data=data,
            cells=cells,
            x0=x0,
            y0=y0,
            x1=x1,
            y1=y1
        )]

    def _table_to_dict(self, table: Table) -> Dict[str, Any]:
        return {
            "rows": table.rows,
            "cols": table.cols,
            "data": table.data,
            "cells": [[asdict(c) for c in row] for row in table.cells],
            "bbox": {
                "x0": table.x0,
                "y0": table.y0,
                "x1": table.x1,
                "y1": table.y1
            }
        }

    def extract_all(self) -> Dict[str, Any]:
        metadata = self.get_metadata()
        toc = self.extract_toc()
        text_result = self.extract_text()
        layout_result = self.extract_layout()
        tables_result = self.extract_tables()
        
        return {
            "metadata": asdict(metadata),
            "toc": [self._toc_to_dict(t) for t in toc],
            "text": text_result,
            "layout": layout_result,
            "tables": tables_result
        }

    def _toc_to_dict(self, entry: TocEntry) -> Dict[str, Any]:
        return {
            "level": entry.level,
            "title": entry.title,
            "page": entry.page,
            "children": [self._toc_to_dict(c) for c in entry.children]
        }


def extract_pdf(pdf_bytes: bytes, extract_type: str = "all", page_num: Optional[int] = None) -> Dict[str, Any]:
    with PDFExtractor(pdf_bytes) as extractor:
        if extract_type == "text":
            return extractor.extract_text(page_num)
        elif extract_type == "layout":
            return extractor.extract_layout(page_num)
        elif extract_type == "tables":
            return extractor.extract_tables(page_num)
        elif extract_type == "toc":
            return {"toc": [extractor._toc_to_dict(t) for t in extractor.extract_toc()]}
        elif extract_type == "metadata":
            return {"metadata": asdict(extractor.get_metadata())}
        else:
            return extractor.extract_all()
