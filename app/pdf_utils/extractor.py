import io
import re
import fitz
import pdfplumber
import camelot
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from PIL import Image, ImageFilter
import numpy as np
import cv2
from pdf2image import convert_from_bytes


@dataclass
class TextFragment:
    text: str
    page: int
    x0: float
    y0: float
    x1: float
    y1: float
    font_name: str = ""
    font_size: float = 0.0
    is_bold: bool = False
    is_italic: bool = False
    column: Optional[int] = None
    is_span_column: bool = False
    line_id: Optional[int] = None


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
    is_scanned: bool


class Line:
    def __init__(self, fragments: List[TextFragment]):
        self.fragments = sorted(fragments, key=lambda f: f.x0)
        self.y0 = min(f.y0 for f in fragments)
        self.y1 = max(f.y1 for f in fragments)
        self.x0 = min(f.x0 for f in fragments)
        self.x1 = max(f.x1 for f in fragments)
        self.width = self.x1 - self.x0
        self.height = self.y1 - self.y0
        self.font_size = max(f.font_size for f in fragments) if fragments else 0

    @property
    def text(self) -> str:
        return " ".join(f.text for f in self.fragments)

    @property
    def center_x(self) -> float:
        return (self.x0 + self.x1) / 2


class PDFExtractor:
    def __init__(self, pdf_bytes: bytes):
        self.pdf_bytes = pdf_bytes
        self._fitz_doc = fitz.open("pdf", pdf_bytes)
        self._plumber_doc = pdfplumber.open(io.BytesIO(pdf_bytes))
        self.page_count = len(self._fitz_doc)
        self._scanned_pages_cache: Dict[int, bool] = {}

    def close(self):
        self._fitz_doc.close()
        self._plumber_doc.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _is_scanned_page(self, page_num: int) -> bool:
        if page_num in self._scanned_pages_cache:
            return self._scanned_pages_cache[page_num]
        
        fitz_page = self._fitz_doc[page_num]
        text = fitz_page.get_text().strip()
        
        if len(text) < 10:
            text_dict = fitz_page.get_text("dict")
            has_text = False
            for block in text_dict.get("blocks", []):
                if block.get("type") == 0:
                    for line in block.get("lines", []):
                        for span in line.get("spans", []):
                            if span.get("text", "").strip():
                                has_text = True
                                break
            if not has_text:
                self._scanned_pages_cache[page_num] = True
                return True
        
        self._scanned_pages_cache[page_num] = False
        return False

    def _extract_ocr(self, page_num: int) -> List[TextFragment]:
        try:
            images = convert_from_bytes(
                self.pdf_bytes,
                first_page=page_num + 1,
                last_page=page_num + 1,
                dpi=300
            )
            
            if not images:
                return []
            
            img = images[0]
            img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)
            
            _, img_binary = cv2.threshold(img_cv, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            kernel = np.ones((1, 1), np.uint8)
            img_binary = cv2.morphologyEx(img_binary, cv2.MORPH_OPEN, kernel)
            img_binary = cv2.dilate(img_binary, kernel, iterations=1)
            
            try:
                import pytesseract
                ocr_data = pytesseract.image_to_data(
                    Image.fromarray(img_binary),
                    lang='chi_sim+eng',
                    output_type=pytesseract.Output.DICT
                )
                
                fragments = []
                h, w = img_cv.shape
                pdf_page = self._fitz_doc[page_num]
                pdf_w, pdf_h = pdf_page.rect.width, pdf_page.rect.height
                scale_x = pdf_w / w
                scale_y = pdf_h / h
                
                n_boxes = len(ocr_data['text'])
                for i in range(n_boxes):
                    text = ocr_data['text'][i].strip()
                    if not text:
                        continue
                    
                    conf = int(ocr_data['conf'][i])
                    if conf < 60:
                        continue
                    
                    x0 = ocr_data['left'][i] * scale_x
                    y0 = ocr_data['top'][i] * scale_y
                    x1 = (ocr_data['left'][i] + ocr_data['width'][i]) * scale_x
                    y1 = (ocr_data['top'][i] + ocr_data['height'][i]) * scale_y
                    font_size = ocr_data['height'][i] * scale_y
                    
                    fragments.append(TextFragment(
                        text=text,
                        page=page_num,
                        x0=float(x0),
                        y0=float(y0),
                        x1=float(x1),
                        y1=float(y1),
                        font_name="OCR",
                        font_size=float(font_size),
                        is_bold=False,
                        is_italic=False
                    ))
                
                return fragments
                
            except ImportError:
                print("提示: 未安装 pytesseract，将使用 PyMuPDF OCR 作为备选")
                print("  如需更好的中英文OCR效果，请安装:")
                print("  1. pip install pytesseract")
                print("  2. 安装 Tesseract OCR 引擎 (https://github.com/UB-Mannheim/tesseract/wiki)")
                print("  3. 安装中文语言包 (chi_sim)")
                
                try:
                    doc = fitz.open("pdf", self.pdf_bytes)
                    page = doc[page_num]
                    try:
                        textpage = page.get_textpage_ocr(flags=0, dpi=300, full=True)
                    except Exception as e:
                        print(f"PyMuPDF OCR 不可用: {e}")
                        print("提示: PyMuPDF OCR 需要完整版本的 PyMuPDF")
                        doc.close()
                        return []
                    
                    text_dict = textpage.extractDICT()
                    doc.close()
                    
                    fragments = []
                    for block in text_dict.get("blocks", []):
                        if block.get("type") == 0:
                            for line in block.get("lines", []):
                                for span in line.get("spans", []):
                                    bbox = span.get("bbox", [0, 0, 0, 0])
                                    text = span.get("text", "").strip()
                                    if text:
                                        fragments.append(TextFragment(
                                            text=text,
                                            page=page_num,
                                            x0=float(bbox[0]),
                                            y0=float(bbox[1]),
                                            x1=float(bbox[2]),
                                            y1=float(bbox[3]),
                                            font_name="OCR",
                                            font_size=float(span.get("size", 12)),
                                            is_bold=False,
                                            is_italic=False
                                        ))
                    
                    return fragments
                except Exception as e:
                    print(f"PyMuPDF OCR 处理失败: {e}")
                    return []
                
        except Exception as e:
            print(f"OCR 处理错误: {e}")
            print("提示: 请确保已安装:")
            print("  - pdf2image 依赖 poppler: https://github.com/oschwartz10612/poppler-windows/releases")
            print("  - opencv-python: 已在 requirements.txt 中")
            return []

    def get_metadata(self) -> PDFMetadata:
        doc = self._fitz_doc
        meta = doc.metadata
        first_page = doc[0]
        rect = first_page.rect
        
        is_scanned = any(self._is_scanned_page(p) for p in range(self.page_count))
        
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
            page_size=(rect.width, rect.height),
            is_scanned=is_scanned
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
                
                if len(text) > 100 or frag.is_span_column:
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

    def _detect_lines(self, fragments: List[TextFragment], page_height: float) -> List[Line]:
        if not fragments:
            return []
        
        has_line_ids = all(f.line_id is not None for f in fragments)
        
        if has_line_ids:
            line_groups: Dict[int, List[TextFragment]] = {}
            for frag in fragments:
                lid = frag.line_id
                if lid not in line_groups:
                    line_groups[lid] = []
                line_groups[lid].append(frag)
            
            lines = []
            for lid in sorted(line_groups.keys()):
                lines.append(Line(line_groups[lid]))
            
            lines.sort(key=lambda l: l.y0)
            return lines
        
        line_height = self._estimate_line_height(fragments)
        tolerance = line_height * 0.4
        
        sorted_frags = sorted(fragments, key=lambda f: (f.y0, f.x0))
        
        lines = []
        current_line_frags = []
        current_y_center = None
        
        for frag in sorted_frags:
            frag_y_center = (frag.y0 + frag.y1) / 2
            
            if current_y_center is None:
                current_y_center = frag_y_center
                current_line_frags = [frag]
            else:
                if abs(frag_y_center - current_y_center) <= tolerance:
                    current_line_frags.append(frag)
                    current_y_center = (current_y_center + frag_y_center) / 2
                else:
                    if current_line_frags:
                        lines.append(Line(current_line_frags))
                    current_y_center = frag_y_center
                    current_line_frags = [frag]
        
        if current_line_frags:
            lines.append(Line(current_line_frags))
        
        return lines

    def _detect_columns(self, page_num: int, fragments: List[TextFragment]) -> List[TextFragment]:
        if len(fragments) < 10:
            for f in fragments:
                f.column = 0
                f.is_span_column = True
            return fragments
        
        doc = self._fitz_doc
        page = doc[page_num]
        page_width = page.rect.width
        page_height = page.rect.height
        
        lines = self._detect_lines(fragments, page_height)
        
        if not lines:
            for f in fragments:
                f.column = 0
                f.is_span_column = True
            return fragments
        
        font_sizes = [f.font_size for f in fragments if f.font_size > 0]
        max_font_size = max(font_sizes) if font_sizes else 12
        large_font_threshold = max(max_font_size * 0.5, 12)
        
        body_lines = []
        span_lines = []
        
        for line in lines:
            line_width_ratio = line.width / page_width
            is_large_font = line.font_size >= large_font_threshold
            has_large_fragment = any(f.font_size >= large_font_threshold for f in line.fragments)
            
            if line_width_ratio > 0.75 or is_large_font or has_large_fragment:
                span_lines.append(line)
                for f in line.fragments:
                    f.is_span_column = True
                    f.column = 0
            else:
                body_lines.append(line)
        
        for f in fragments:
            if f.font_size >= large_font_threshold and not f.is_span_column:
                f.is_span_column = True
                f.column = 0
        
        if len(body_lines) < 10:
            for f in fragments:
                if f.column is None:
                    f.column = 0
                    f.is_span_column = False
            return fragments
        
        all_x0 = []
        for line in body_lines:
            for f in line.fragments:
                all_x0.append(f.x0)
        
        hist, bin_edges = np.histogram(all_x0, bins=30, range=(0, page_width))
        
        peaks = []
        peak_threshold = len(body_lines) * 0.15
        for i in range(1, len(hist) - 1):
            if hist[i] > hist[i-1] and hist[i] > hist[i+1] and hist[i] > peak_threshold:
                peaks.append((bin_edges[i] + bin_edges[i+1]) / 2)
        
        peaks.sort()
        
        if len(peaks) >= 2:
            column_centers = []
            last_peak = peaks[0]
            column_centers.append(last_peak)
            
            min_col_gap = page_width * 0.18
            for peak in peaks[1:]:
                if peak - last_peak > min_col_gap:
                    column_centers.append(peak)
                    last_peak = peak
            
            max_columns = 3
            if len(column_centers) > max_columns:
                column_centers = column_centers[:max_columns]
            
            if len(column_centers) >= 2:
                gaps = []
                for i in range(1, len(column_centers)):
                    gaps.append((column_centers[i-1] + column_centers[i]) / 2)
                
                for line in body_lines:
                    for f in line.fragments:
                        if f.is_span_column:
                            continue
                        
                        center_x = (f.x0 + f.x1) / 2
                        assigned = False
                        
                        for col_idx, gap in enumerate(gaps):
                            if center_x < gap:
                                f.column = col_idx
                                assigned = True
                                break
                        
                        if not assigned:
                            f.column = len(gaps)
                
                for line in span_lines:
                    for f in line.fragments:
                        if f.column is None:
                            f.column = 0
                            f.is_span_column = True
                
                return fragments
        
        x_coords = sorted(all_x0)
        gaps = []
        for i in range(1, len(x_coords)):
            gap = x_coords[i] - x_coords[i-1]
            if gap > page_width * 0.1:
                gaps.append((x_coords[i-1] + gap / 2, gap))
        
        if not gaps:
            for f in fragments:
                if f.column is None:
                    f.column = 0
                    f.is_span_column = False
            return fragments
        
        gaps.sort(key=lambda x: x[1], reverse=True)
        column_divider = gaps[0][0]
        
        for line in body_lines:
            for f in line.fragments:
                if f.is_span_column or f.column is not None:
                    continue
                
                center_x = (f.x0 + f.x1) / 2
                if center_x < column_divider:
                    f.column = 0
                else:
                    f.column = 1
        
        for f in fragments:
            if f.column is None:
                f.column = 0
                f.is_span_column = True
        
        return fragments

    def _estimate_line_height(self, fragments: List[TextFragment]) -> float:
        if len(fragments) < 2:
            return 12.0
        
        y_coords = sorted(list(set([round((f.y0 + f.y1) / 2, 1) for f in fragments])))
        if len(y_coords) < 2:
            return 12.0
        
        gaps = [y_coords[i+1] - y_coords[i] for i in range(len(y_coords)-1)]
        gaps = [g for g in gaps if g > 0 and g < 50]
        
        if not gaps:
            return 12.0
        
        return sum(gaps) / len(gaps)

    def extract_text(self, page_num: Optional[int] = None) -> Dict[str, Any]:
        if page_num is not None:
            fragments = self._extract_page_layout(page_num)
            fragments = self._detect_columns(page_num, fragments)
            fragments = self._sort_by_reading_order(fragments)
            
            lines = []
            current_line = []
            current_y = None
            line_height = self._estimate_line_height(fragments)
            
            for f in fragments:
                frag_y = (f.y0 + f.y1) / 2
                if current_y is None or abs(frag_y - current_y) > line_height * 0.5:
                    if current_line:
                        lines.append(" ".join([x.text for x in current_line]))
                    current_line = [f]
                    current_y = frag_y
                else:
                    current_line.append(f)
            
            if current_line:
                lines.append(" ".join([x.text for x in current_line]))
            
            text = "\n".join(lines)
            
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
            line_groups: Dict[int, List[TextFragment]] = {}
            
            for f in fragments:
                key = f.line_id if f.line_id is not None else int(round(f.y0 / 2))
                if key not in line_groups:
                    line_groups[key] = []
                line_groups[key].append(f)
            
            sorted_line_keys = sorted(line_groups.keys())
            
            result = []
            for key in sorted_line_keys:
                line_frags = line_groups[key]
                
                span_in_line = [f for f in line_frags if f.is_span_column]
                col_in_line = [f for f in line_frags if not f.is_span_column]
                
                span_in_line.sort(key=lambda f: f.x0)
                col_in_line.sort(key=lambda f: (f.column if f.column is not None else 0, f.x0))
                
                result.extend(span_in_line)
                result.extend(col_in_line)
            
            return result
        else:
            line_groups: Dict[int, List[TextFragment]] = {}
            line_height = self._estimate_line_height(fragments)
            
            for f in fragments:
                key = f.line_id if f.line_id is not None else int(round(f.y0 / line_height * 2))
                if key not in line_groups:
                    line_groups[key] = []
                line_groups[key].append(f)
            
            sorted_line_keys = sorted(line_groups.keys())
            
            result = []
            for key in sorted_line_keys:
                line_frags = line_groups[key]
                line_frags.sort(key=lambda f: f.x0)
                result.extend(line_frags)
            
            return result

    def extract_layout(self, page_num: Optional[int] = None) -> Dict[str, Any]:
        if page_num is not None:
            fragments = self._extract_page_layout(page_num)
            fragments = self._detect_columns(page_num, fragments)
            fragments = self._sort_by_reading_order(fragments)
            
            columns_detected = max((f.column for f in fragments if f.column is not None), default=0) + 1
            span_count = sum(1 for f in fragments if f.is_span_column)
            
            return {
                "page": page_num + 1,
                "columns_detected": columns_detected,
                "span_elements_count": span_count,
                "fragments": [asdict(f) for f in fragments]
            }
        else:
            result = {"pages": []}
            for p in range(self.page_count):
                page_result = self.extract_layout(p)
                result["pages"].append(page_result)
            return result

    def _extract_page_layout(self, page_num: int) -> List[TextFragment]:
        if self._is_scanned_page(page_num):
            return self._extract_ocr(page_num)
        
        fragments = self._extract_native_text(page_num)
        
        if not fragments:
            return self._extract_ocr(page_num)
        
        return fragments

    def _extract_native_text(self, page_num: int) -> List[TextFragment]:
        fragments = []
        
        try:
            fitz_page = self._fitz_doc[page_num]
            text_dict = fitz_page.get_text("dict")
            line_counter = 0
            for block in text_dict.get("blocks", []):
                if block.get("type") == 0:
                    for line in block.get("lines", []):
                        for span in line.get("spans", []):
                            bbox = span.get("bbox", [0, 0, 0, 0])
                            font_name = span.get("font", "")
                            text = span.get("text", "").strip()
                            if not text:
                                continue
                                
                            fragments.append(TextFragment(
                                text=text,
                                page=page_num,
                                x0=float(bbox[0]),
                                y0=float(bbox[1]),
                                x1=float(bbox[2]),
                                y1=float(bbox[3]),
                                font_name=font_name,
                                font_size=float(span.get("size", 0)),
                                is_bold=bool(span.get("flags", 0) & 1 << 5 or "Bold" in font_name or "bold" in font_name or "Hei" in font_name),
                                is_italic=bool(span.get("flags", 0) & 1 << 6 or "Italic" in font_name or "italic" in font_name),
                                line_id=line_counter
                            ))
                        line_counter += 1
        except Exception as e:
            pass
        
        if not fragments:
            try:
                plumber_page = self._plumber_doc.pages[page_num]
                words = plumber_page.extract_words(
                    keep_blank_chars=False,
                    use_text_flow=True,
                    extra_attrs=["fontname", "size"]
                )
                
                for word in words:
                    font_name = word.get("fontname", "")
                    text = word.get("text", "").strip()
                    if not text:
                        continue
                        
                    fragments.append(TextFragment(
                        text=text,
                        page=page_num,
                        x0=float(word.get("x0", 0)),
                        y0=float(word.get("top", 0)),
                        x1=float(word.get("x1", 0)),
                        y1=float(word.get("bottom", 0)),
                        font_name=font_name,
                        font_size=float(word.get("size", 0)),
                        is_bold=bool("Bold" in font_name or "bold" in font_name or "BD" in font_name or "Hei" in font_name),
                        is_italic=bool("Italic" in font_name or "italic" in font_name or "IT" in font_name or "Oblique" in font_name)
                    ))
            except Exception as e:
                pass
        
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
        
        for flavor in ["lattice", "stream"]:
            try:
                pdf_io.seek(0)
                camelot_tables = camelot.read_pdf(
                    pdf_io,
                    pages=str(page_num + 1),
                    flavor=flavor,
                    suppress_stdout=True
                )
                
                for idx, ct in enumerate(camelot_tables):
                    if ct.df.empty:
                        continue
                    
                    data = ct.df.values.tolist()
                    rows, cols = len(data), len(data[0]) if data else 0
                    
                    if flavor == "lattice":
                        if ct.accuracy < 40:
                            continue
                        if rows < 2 or cols < 2:
                            continue
                        non_empty_ratio = 0.2
                    else:
                        if ct.accuracy < 90:
                            continue
                        if rows < 4 or cols < 3:
                            continue
                        non_empty_ratio = 0.6
                    
                    non_empty_cells = sum(1 for row in data for cell in row if str(cell).strip())
                    total_cells = rows * cols
                    if total_cells > 0 and non_empty_cells / total_cells < non_empty_ratio:
                        continue
                    
                    has_header_markers = False
                    if data and data[0]:
                        first_row_text = " ".join(str(x) for x in data[0] if str(x).strip())
                        if any(marker in first_row_text for marker in ["序号", "编号", "名称", "日期", "金额", "数量", "备注", "No.", "Date", "Amount", "Qty"]):
                            has_header_markers = True
                    
                    if flavor == "stream" and not has_header_markers:
                        try:
                            col_widths = []
                            for col in ct.df.columns:
                                col_texts = ct.df[col].astype(str).str.len().values
                                col_widths.append(float(col_texts.mean()))
                            
                            if len(col_widths) >= 2:
                                avg_width = sum(col_widths) / len(col_widths)
                                width_variance = sum((w - avg_width)**2 for w in col_widths) / len(col_widths)
                                if width_variance < 30:
                                    continue
                        except:
                            continue
                    
                    has_vertical_separators = False
                    is_likely_toc = False
                    
                    if rows > 1 and cols > 1:
                        all_col_widths = []
                        for col in range(cols):
                            col_texts = [len(str(data[r][col])) for r in range(rows) if str(data[r][col]).strip()]
                            if col_texts:
                                all_col_widths.append(sum(col_texts) / len(col_texts))
                        
                        if len(all_col_widths) >= 2:
                            max_width = max(all_col_widths)
                            min_width = min(all_col_widths)
                            if max_width > 0 and max_width / min_width > 1.5:
                                has_vertical_separators = True
                    
                    if flavor == "stream":
                        first_col_texts = [str(data[r][0]).strip() for r in range(rows) if r < len(data)]
                        last_col_texts = [str(data[r][-1]).strip() for r in range(rows) if r < len(data)]
                        
                        toc_number_pattern = 0
                        for t in first_col_texts:
                            if re.match(r'^[\d\.]+$', t):
                                toc_number_pattern += 1
                            elif re.match(r'^第[一二三四五六七八九十百千\d]+[章节篇部分]', t):
                                toc_number_pattern += 1
                            elif re.match(r'^[\d\.]+[\s、．]+', t):
                                toc_number_pattern += 1
                        
                        numeric_last_col = sum(1 for t in last_col_texts if t.isdigit() and 1 <= int(t) <= 500)
                        
                        if toc_number_pattern >= rows * 0.4 or numeric_last_col >= rows * 0.4:
                            is_likely_toc = True
                        
                        if not is_likely_toc:
                            has_dots = 0
                            for row in data:
                                row_text = " ".join(str(c) for c in row if str(c).strip())
                                if re.search(r'[.．·]{2,}', row_text):
                                    has_dots += 1
                            
                            if has_dots >= rows * 0.3:
                                is_likely_toc = True
                        
                        if not is_likely_toc:
                            avg_cell_length = 0
                            total_cells = 0
                            for row in data:
                                for cell in row:
                                    cell_text = str(cell).strip()
                                    if cell_text:
                                        avg_cell_length += len(cell_text)
                                        total_cells += 1
                            if total_cells > 0:
                                avg_cell_length /= total_cells
                            
                            short_cell_ratio = 0
                            for row in data:
                                for cell in row:
                                    cell_text = str(cell).strip()
                                    if cell_text and len(cell_text) <= 4:
                                        short_cell_ratio += 1
                            if total_cells > 0:
                                short_cell_ratio /= total_cells
                            
                            if short_cell_ratio > 0.6 and avg_cell_length < 8:
                                is_likely_toc = True
                    
                    if flavor == "stream" and ((not has_header_markers and not has_vertical_separators) or is_likely_toc):
                        continue
                    
                    cells = []
                    for r in range(rows):
                        row_cells = []
                        for c in range(cols):
                            cell_text = str(data[r][c]).strip() if data[r][c] is not None else ""
                            col_width = (ct.bbox[2] - ct.bbox[0]) / cols
                            row_height = (ct.bbox[3] - ct.bbox[1]) / rows
                            row_cells.append(TableCell(
                                text=cell_text,
                                row=r,
                                col=c,
                                x0=ct.bbox[0] + c * col_width,
                                y0=ct.bbox[1] + r * row_height,
                                x1=ct.bbox[0] + (c + 1) * col_width,
                                y1=ct.bbox[1] + (r + 1) * row_height
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
                continue
        
        if tables:
            tables = self._deduplicate_tables(tables)
            tables = self._split_merged_tables(tables)
            tables = self._merge_overlapping_tables(tables)
            return tables
        
        return self._fallback_table_detection(page_num)
    
    def _split_merged_tables(self, tables: List[Table]) -> List[Table]:
        if not tables:
            return tables
        
        split_tables = []
        
        for table in tables:
            if table.rows < 4:
                split_tables.append(table)
                continue
            
            row_heights = []
            for r in range(table.rows - 1):
                y0_curr = min(cell.y0 for row in table.cells[r:r+1] for cell in row if cell)
                y1_next = max(cell.y1 for row in table.cells[r+1:r+2] for cell in row if cell)
                if y0_curr and y1_next:
                    row_heights.append(y1_next - y0_curr)
            
            if not row_heights:
                split_tables.append(table)
                continue
            
            avg_height = sum(row_heights) / len(row_heights)
            
            split_points = []
            for r in range(len(row_heights)):
                if row_heights[r] > avg_height * 1.8 and row_heights[r] > 10:
                    split_points.append(r + 1)
            
            if not split_points:
                split_tables.append(table)
                continue
            
            prev_split = 0
            for split_point in split_points:
                if split_point - prev_split >= 2:
                    new_rows = split_point - prev_split
                    new_data = table.data[prev_split:split_point]
                    new_cells = table.cells[prev_split:split_point]
                    
                    new_y0 = min(cell.y0 for row in new_cells for cell in row if cell)
                    new_y1 = max(cell.y1 for row in new_cells for cell in row if cell)
                    
                    split_tables.append(Table(
                        page=table.page,
                        rows=new_rows,
                        cols=table.cols,
                        data=new_data,
                        cells=new_cells,
                        x0=table.x0,
                        y0=new_y0,
                        x1=table.x1,
                        y1=new_y1
                    ))
                prev_split = split_point
            
            if table.rows - prev_split >= 2:
                new_rows = table.rows - prev_split
                new_data = table.data[prev_split:]
                new_cells = table.cells[prev_split:]
                
                new_y0 = min(cell.y0 for row in new_cells for cell in row if cell)
                new_y1 = max(cell.y1 for row in new_cells for cell in row if cell)
                
                split_tables.append(Table(
                    page=table.page,
                    rows=new_rows,
                    cols=table.cols,
                    data=new_data,
                    cells=new_cells,
                    x0=table.x0,
                    y0=new_y0,
                    x1=table.x1,
                    y1=new_y1
                ))
        
        return split_tables
    
    def _deduplicate_tables(self, tables: List[Table]) -> List[Table]:
        if len(tables) < 2:
            return tables
        
        tables.sort(key=lambda t: (t.y0, t.x0))
        
        unique = []
        seen_areas = []
        
        for table in tables:
            area = (table.x1 - table.x0) * (table.y1 - table.y0)
            
            is_dup = False
            for i, (u_area, u_table) in enumerate(seen_areas):
                overlap_x = min(table.x1, u_table.x1) - max(table.x0, u_table.x0)
                overlap_y = min(table.y1, u_table.y1) - max(table.y0, u_table.y0)
                
                if overlap_x > 0 and overlap_y > 0:
                    overlap_area = overlap_x * overlap_y
                    table_area = (table.x1 - table.x0) * (table.y1 - table.y0)
                    u_area_calc = (u_table.x1 - u_table.x0) * (u_table.y1 - u_table.y0)
                    
                    if overlap_area / min(table_area, u_area_calc) > 0.8:
                        is_dup = True
                        if table.rows * table.cols > u_table.rows * u_table.cols:
                            unique[i] = table
                            seen_areas[i] = (area, table)
                        break
            
            if not is_dup:
                unique.append(table)
                seen_areas.append((area, table))
        
        return unique

    def _merge_overlapping_tables(self, tables: List[Table]) -> List[Table]:
        if len(tables) < 2:
            return tables
        
        tables.sort(key=lambda t: t.y0)
        
        merged = []
        current = tables[0]
        
        for next_table in tables[1:]:
            vertical_gap = next_table.y0 - current.y1
            horizontal_overlap = min(current.x1, next_table.x1) - max(current.x0, next_table.x0)
            min_width = min(current.x1 - current.x0, next_table.x1 - next_table.x0)
            
            if vertical_gap < 15 and horizontal_overlap > min_width * 0.6:
                new_rows = current.rows + next_table.rows
                new_cols = max(current.cols, next_table.cols)
                new_data = current.data + next_table.data
                
                new_cells = current.cells.copy()
                for row in next_table.cells:
                    new_row = []
                    for cell in row:
                        new_row.append(TableCell(
                            text=cell.text,
                            row=cell.row + current.rows,
                            col=cell.col,
                            x0=cell.x0,
                            y0=cell.y0,
                            x1=cell.x1,
                            y1=cell.y1
                        ))
                    new_cells.append(new_row)
                
                current = Table(
                    page=current.page,
                    rows=new_rows,
                    cols=new_cols,
                    data=new_data,
                    cells=new_cells,
                    x0=min(current.x0, next_table.x0),
                    y0=min(current.y0, next_table.y0),
                    x1=max(current.x1, next_table.x1),
                    y1=max(current.y1, next_table.y1)
                )
            else:
                merged.append(current)
                current = next_table
        
        merged.append(current)
        return merged

    def _fallback_table_detection(self, page_num: int) -> List[Table]:
        fragments = self._extract_page_layout(page_num)
        if len(fragments) < 10:
            return []
        
        page_height = self._fitz_doc[page_num].rect.height
        page_width = self._fitz_doc[page_num].rect.width
        
        line_groups: Dict[int, List[TextFragment]] = {}
        for f in fragments:
            key = f.line_id if f.line_id is not None else int(round(f.y0 / 2))
            if key not in line_groups:
                line_groups[key] = []
            line_groups[key].append(f)
        
        line_height = self._estimate_line_height(fragments)
        
        potential_rows = []
        for line_id in sorted(line_groups.keys()):
            row_frags = line_groups[line_id]
            if len(row_frags) >= 2:
                x_centers = sorted([(f.x0 + f.x1) / 2 for f in row_frags])
                gaps = [x_centers[i+1] - x_centers[i] for i in range(len(x_centers)-1)]
                
                if len(gaps) >= 1 and all(g > 10 for g in gaps):
                    avg_gap = sum(gaps) / len(gaps)
                    gap_variance = sum((g - avg_gap) ** 2 for g in gaps) / len(gaps)
                    
                    if gap_variance < avg_gap * avg_gap * 0.8:
                        x0 = min(f.x0 for f in row_frags)
                        x1 = max(f.x1 for f in row_frags)
                        y0 = min(f.y0 for f in row_frags)
                        y1 = max(f.y1 for f in row_frags)
                        potential_rows.append((y0, y1, row_frags, x0, x1))
        
        if len(potential_rows) < 2:
            return []
        
        table_groups = []
        current_group = [potential_rows[0]]
        
        for i in range(1, len(potential_rows)):
            prev_y0, prev_y1, _, prev_x0, prev_x1 = potential_rows[i-1]
            curr_y0, curr_y1, _, curr_x0, curr_x1 = potential_rows[i]
            gap = curr_y0 - prev_y1
            
            prev_width = prev_x1 - prev_x0
            curr_width = curr_x1 - curr_x0
            width_ratio = min(prev_width, curr_width) / max(prev_width, curr_width)
            horizontal_overlap = min(prev_x1, curr_x1) - max(prev_x0, curr_x0)
            
            avg_width = (prev_width + curr_width) / 2
            table_like_width = avg_width > page_width * 0.25
            
            if (gap < line_height * 3 and gap > -line_height * 0.5 and 
                width_ratio > 0.5 and 
                horizontal_overlap > avg_width * 0.4 and
                table_like_width):
                current_group.append(potential_rows[i])
            else:
                if len(current_group) >= 2:
                    table_groups.append(current_group)
                current_group = [potential_rows[i]]
        
        if len(current_group) >= 2:
            table_groups.append(current_group)
        
        if not table_groups:
            return []
        
        tables = []
        
        for group in table_groups:
            cols_count = max(len(r[2]) for r in group)
            
            if cols_count < 2:
                continue
            
            col_alignments = []
            for r_idx, (y0, y1, row_frags, x0, x1) in enumerate(group):
                sorted_frags = sorted(row_frags, key=lambda f: f.x0)
                for c_idx, frag in enumerate(sorted_frags):
                    if c_idx >= len(col_alignments):
                        col_alignments.append([])
                    col_alignments[c_idx].append((frag.x0 + frag.x1) / 2)
            
            valid_cols = 0
            for col_xs in col_alignments:
                if len(col_xs) >= 2:
                    variance = sum((x - sum(col_xs)/len(col_xs))**2 for x in col_xs) / len(col_xs)
                    if variance < 500:
                        valid_cols += 1
            
            if valid_cols < 2:
                continue
            
            rows_data = []
            for y0, y1, row_frags, x0, x1 in group:
                sorted_frags = sorted(row_frags, key=lambda f: f.x0)
                row_data = [""] * cols_count
                for c_idx, frag in enumerate(sorted_frags[:cols_count]):
                    row_data[c_idx] = frag.text
                rows_data.append((y0, y1, row_data, sorted_frags))
            
            if len(rows_data) < 2:
                continue
            
            rows = len(rows_data)
            cols = cols_count
            data = [[row_data for _, _, row_data, _ in rows_data][r] for r in range(rows)]
            cells = [[None for _ in range(cols)] for _ in range(rows)]
            
            for r_idx, (y0, y1, row_data, frags) in enumerate(rows_data):
                for c_idx, frag in enumerate(frags[:cols]):
                    cells[r_idx][c_idx] = TableCell(
                        text=frag.text,
                        row=r_idx,
                        col=c_idx,
                        x0=frag.x0,
                        y0=frag.y0,
                        x1=frag.x1,
                        y1=frag.y1
                    )
            
            valid_cells = [c for row in cells for c in row if c is not None]
            if not valid_cells:
                continue
            
            x0 = min(c.x0 for c in valid_cells)
            y0 = min(c.y0 for c in valid_cells)
            x1 = max(c.x1 for c in valid_cells)
            y1 = max(c.y1 for c in valid_cells)
            
            tables.append(Table(
                page=page_num,
                rows=rows,
                cols=cols,
                data=data,
                cells=cells,
                x0=x0,
                y0=y0,
                x1=x1,
                y1=y1
            ))
        
        return tables

    def _table_to_dict(self, table: Table) -> Dict[str, Any]:
        return {
            "rows": table.rows,
            "cols": table.cols,
            "data": table.data,
            "cells": [[asdict(c) if c else None for c in row] for row in table.cells],
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
