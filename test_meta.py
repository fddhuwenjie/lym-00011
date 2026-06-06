import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import fitz

SAMPLES_DIR = Path(__file__).parent / "samples"

pdf_path = SAMPLES_DIR / "sample1_single_column.pdf"
doc = fitz.open(str(pdf_path))
meta = doc.metadata
print("Fitz metadata:")
print(meta)
print()
print("doc.is_encrypted:", doc.is_encrypted)
print("doc.page_count:", len(doc))
page = doc[0]
print("page rect:", page.rect)
print("page size:", (page.rect.width, page.rect.height))
doc.close()
