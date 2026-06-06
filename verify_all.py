import sys
import requests
import json
from pathlib import Path

BASE_URL = "http://localhost:8011"
SAMPLES_DIR = Path(__file__).parent / "samples"

def hline(char='='):
    print(char * 70)

def test_endpoint(name, url, method="GET", file=None, params=None, validator=None):
    print(f"\n{hline('-')}")
    print(f"TEST: {name}")
    print(f"  URL: {url}")
    
    try:
        if method == "GET":
            resp = requests.get(url, params=params, timeout=30)
        else:
            if file:
                with open(file, "rb") as f:
                    files = {"file": (Path(file).name, f, "application/pdf")}
                    resp = requests.post(url, files=files, params=params, timeout=60)
            else:
                resp = requests.post(url, data=params, timeout=30)
        
        if resp.status_code != 200:
            print(f"  STATUS: {resp.status_code} - FAIL")
            print(f"  ERROR: {resp.text[:200]}")
            return False
        
        data = resp.json()
        if not data.get("success", False):
            print(f"  STATUS: {resp.status_code} - FAIL (success=false)")
            return False
        
        result = data.get("data", {})
        
        if validator and not validator(result):
            print(f"  STATUS: {resp.status_code} - FAIL (validation)")
            return False
        
        print(f"  STATUS: {resp.status_code} - PASS")
        
        if isinstance(result, dict):
            for key in ["metadata", "toc", "pages", "total_tables", "count", "samples", "columns_detected"]:
                if key in result:
                    val = result[key]
                    if isinstance(val, list):
                        print(f"  {key}: {len(val)} items")
                    elif isinstance(val, dict):
                        print(f"  {key}: {json.dumps(val, ensure_ascii=False)[:100]}")
                    else:
                        print(f"  {key}: {val}")
            
            if "page" in result and "text" in result:
                text = result["text"][:150].replace('\n', ' ')
                print(f"  text preview: '{text}...'")
            
            if "fragments" in result:
                frags = result["fragments"]
                if frags:
                    f = frags[0]
                    print(f"  fragments: {len(frags)} total")
                    print(f"  first fragment: text='{f.get('text','')[:30]}', font={f.get('font_name','')[:20]}, size={f.get('font_size',0):.1f}, col={f.get('column',0)}")
            
            if "tables" in result:
                for t in result["tables"][:1]:
                    print(f"  table: {t.get('rows',0)}x{t.get('cols',0)}, first row: {t.get('data',[[]])[0][:3]}...")
        
        return True
        
    except Exception as e:
        print(f"  STATUS: ERROR - {str(e)[:100]}")
        return False

def main():
    hline()
    print("PDF STRUCTURED EXTRACTION API - FINAL VERIFICATION")
    print(f"Server: {BASE_URL}")
    hline()
    
    try:
        r = requests.get(f"{BASE_URL}/", timeout=5)
        if r.status_code != 200:
            print("ERROR: Server is not responding!")
            return False
        print("Server is running ✓")
    except:
        print("ERROR: Cannot connect to server!")
        print("Please start the server first: py -m uvicorn app.main:app --port 8011")
        return False
    
    S1 = str(SAMPLES_DIR / "sample1_single_column.pdf")
    S2 = str(SAMPLES_DIR / "sample2_multi_column.pdf")
    S3 = str(SAMPLES_DIR / "sample3_tables.pdf")
    S4 = str(SAMPLES_DIR / "sample4_toc.pdf")
    S5 = str(SAMPLES_DIR / "sample5_scanned.pdf")
    
    tests = []
    
    tests.append(test_endpoint(
        "List Available Samples",
        f"{BASE_URL}/api/v1/samples",
        validator=lambda d: d.get("count", 0) >= 5
    ))
    
    tests.append(test_endpoint(
        "[URL] Metadata - Sample1 (Single Column)",
        f"{BASE_URL}/api/v1/samples/sample1_single_column.pdf/extract/metadata",
        validator=lambda d: d.get("pages", 0) >= 1 and d.get("title") is not None
    ))
    
    tests.append(test_endpoint(
        "[URL] Text Extraction - Sample1 Page 1",
        f"{BASE_URL}/api/v1/samples/sample1_single_column.pdf/extract/text",
        params={"page": 1},
        validator=lambda d: len(d.get("text", "")) > 100
    ))
    
    tests.append(test_endpoint(
        "[URL] Layout & Multi-column - Sample2",
        f"{BASE_URL}/api/v1/samples/sample2_multi_column.pdf/extract/layout",
        params={"page": 1},
        validator=lambda d: d.get("columns_detected", 0) >= 2 and len(d.get("fragments", [])) > 50
    ))
    
    tests.append(test_endpoint(
        "[URL] Table Extraction - Sample3",
        f"{BASE_URL}/api/v1/samples/sample3_tables.pdf/extract/tables",
        params={"page": 1},
        validator=lambda d: len(d.get("tables", [])) >= 1
    ))
    
    tests.append(test_endpoint(
        "[URL] TOC/Bookmarks - Sample4",
        f"{BASE_URL}/api/v1/samples/sample4_toc.pdf/extract/toc",
        validator=lambda d: len(d.get("toc", [])) >= 3
    ))
    
    tests.append(test_endpoint(
        "[URL] Metadata - Sample5 (Scanned)",
        f"{BASE_URL}/api/v1/samples/sample5_scanned.pdf/extract/metadata",
        validator=lambda d: d.get("pages", 0) >= 3
    ))
    
    print(f"\n{hline('=')}")
    print("UPLOAD TESTS (File Upload)")
    hline('=')
    
    tests.append(test_endpoint(
        "[UPLOAD] Metadata - Sample1",
        f"{BASE_URL}/api/v1/extract/metadata",
        method="POST",
        file=S1,
        validator=lambda d: d.get("pages", 0) >= 1
    ))
    
    tests.append(test_endpoint(
        "[UPLOAD] Full Text - Sample2",
        f"{BASE_URL}/api/v1/extract/text",
        method="POST",
        file=S2,
        validator=lambda d: len(d.get("full_text", "")) > 500
    ))
    
    tests.append(test_endpoint(
        "[UPLOAD] Layout Analysis - Sample2",
        f"{BASE_URL}/api/v1/extract/layout",
        method="POST",
        file=S2,
        params={"page": 1},
        validator=lambda d: d.get("columns_detected", 0) >= 2
    ))
    
    tests.append(test_endpoint(
        "[UPLOAD] Table Recognition - Sample3",
        f"{BASE_URL}/api/v1/extract/tables",
        method="POST",
        file=S3,
        params={"page": 1},
        validator=lambda d: len(d.get("tables", [])) >= 1
    ))
    
    tests.append(test_endpoint(
        "[UPLOAD] TOC Extraction - Sample4",
        f"{BASE_URL}/api/v1/extract/toc",
        method="POST",
        file=S4,
        validator=lambda d: len(d.get("toc", [])) >= 3
    ))
    
    tests.append(test_endpoint(
        "[UPLOAD] Complete Extraction - Sample2 (All)",
        f"{BASE_URL}/api/v1/extract/all",
        method="POST",
        file=S2,
        validator=lambda d: all(k in d for k in ["metadata", "text", "layout", "tables", "toc"])
    ))
    
    print(f"\n{hline('=')}")
    passed = sum(1 for t in tests if t)
    print(f"RESULT: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("STATUS: ALL TESTS PASSED ✓")
        hline('=')
        print()
        print("FEATURE VERIFICATION SUMMARY:")
        print("  ✓ Text Extraction - Extracts text per page in reading order")
        print("  ✓ Layout Restoration - Position, font info, multi-column detection")
        print("  ✓ Table Recognition - Auto-detect tables, output 2D array")
        print("  ✓ TOC & Bookmarks - Extract PDF outline or generate from headings")
        print("  ✓ Metadata - Title, author, dates, pages, encryption status")
        print()
        print("TEST SAMPLES:")
        for pdf in sorted(SAMPLES_DIR.glob("*.pdf")):
            size_kb = pdf.stat().st_size / 1024
            print(f"  - {pdf.name} ({size_kb:.1f} KB)")
        print()
        print("API DOCS:")
        print(f"  - Swagger UI: {BASE_URL}/docs")
        print(f"  - ReDoc: {BASE_URL}/redoc")
        print()
        print("EXAMPLE CURL COMMANDS:")
        print(f"  curl {BASE_URL}/api/v1/samples")
        print(f"  curl -X POST -F \"file=@test.pdf\" {BASE_URL}/api/v1/extract/all")
        print(f"  curl {BASE_URL}/api/v1/samples/sample3_tables.pdf/extract/tables")
        print()
        return True
    else:
        print(f"STATUS: {len(tests) - passed} TESTS FAILED")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
