import sys
import requests
import json
from pathlib import Path

BASE_URL = "http://localhost:8011"
SAMPLES_DIR = Path(__file__).parent / "samples"

def run_test(name, method, url, files=None, params=None, show=False, max_len=1000):
    print(f"\n{'='*70}")
    print(f"[TEST] {name}")
    print(f"  URL: {url}")
    print(f"  Method: {method}")
    
    try:
        if method == "GET":
            resp = requests.get(url, params=params, timeout=30)
        else:
            resp = requests.post(url, files=files, params=params, timeout=60)
        
        print(f"  Status: {resp.status_code}")
        
        if resp.status_code == 200:
            data = resp.json()
            if data.get("success"):
                print(f"  Result: PASS")
                
                if show:
                    print(f"  Response:")
                    if "data" in data:
                        resp_data = data["data"]
                    else:
                        resp_data = data
                    
                    data_str = json.dumps(resp_data, ensure_ascii=False, indent=2)
                    if len(data_str) > max_len:
                        print(data_str[:max_len])
                        print(f"... (truncated, total {len(data_str)} chars)")
                    else:
                        print(data_str)
                
                return True
            else:
                print(f"  Result: FAIL - {data}")
                return False
        else:
            print(f"  Result: FAIL - {resp.text[:200]}")
            return False
            
    except Exception as e:
        print(f"  Result: FAIL - Exception: {e}")
        return False

def main():
    print("=" * 70)
    print("PDF Structured Extraction API - CURL Validation Tests")
    print(f"Server: {BASE_URL}")
    print("=" * 70)
    
    passed = 0
    failed = 0
    results = []
    
    tests = [
        ("1. Health Check", "GET", f"{BASE_URL}/", None, None, True, 500),
        ("2. List Samples", "GET", f"{BASE_URL}/api/v1/samples", None, None, True, 1000),
    ]
    
    url_tests = [
        ("3. URL - Metadata (Sample1 single column)", "GET", 
         f"{BASE_URL}/api/v1/samples/sample1_single_column.pdf/extract/metadata", None, None, True, 500),
        ("4. URL - Text Extraction (Sample1 Page 1)", "GET",
         f"{BASE_URL}/api/v1/samples/sample1_single_column.pdf/extract/text", None, {"page": 1}, True, 800),
        ("5. URL - Layout Extraction (Sample2 multi-column)", "GET",
         f"{BASE_URL}/api/v1/samples/sample2_multi_column.pdf/extract/layout", None, {"page": 1}, True, 1200),
        ("6. URL - Table Extraction (Sample3)", "GET",
         f"{BASE_URL}/api/v1/samples/sample3_tables.pdf/extract/tables", None, {"page": 1}, True, 1500),
        ("7. URL - TOC Extraction (Sample4)", "GET",
         f"{BASE_URL}/api/v1/samples/sample4_toc.pdf/extract/toc", None, None, True, 2000),
        ("8. URL - Metadata (Sample5 scanned)", "GET",
         f"{BASE_URL}/api/v1/samples/sample5_scanned.pdf/extract/metadata", None, None, True, 500),
    ]
    
    upload_tests = []
    for sample_name, test_name, endpoint, params in [
        ("sample1_single_column.pdf", "Metadata", "metadata", None),
        ("sample2_multi_column.pdf", "Text (Page 1)", "text", {"page": 1}),
        ("sample2_multi_column.pdf", "Layout (Page 1)", "layout", {"page": 1}),
        ("sample3_tables.pdf", "Tables (Page 1)", "tables", {"page": 1}),
        ("sample4_toc.pdf", "TOC", "toc", None),
        ("sample2_multi_column.pdf", "All (multi-column)", "all", None),
    ]:
        pdf_path = SAMPLES_DIR / sample_name
        files = {"file": (sample_name, open(pdf_path, "rb"), "application/pdf")}
        idx = len(tests) + len(url_tests) + len(upload_tests) + 1
        upload_tests.append((
            f"{idx}. Upload - {test_name} ({sample_name})",
            "POST",
            f"{BASE_URL}/api/v1/extract/{endpoint}",
            files,
            params,
            True,
            1200
        ))
    
    all_tests = tests + url_tests + upload_tests
    
    for name, method, url, files, params, show, max_len in all_tests:
        result = run_test(name, method, url, files, params, show, max_len)
        if result:
            passed += 1
        else:
            failed += 1
        results.append((name, result))
        
        if files:
            for f in files.values():
                if hasattr(f[1], 'close'):
                    f[1].close()
    
    print(f"\n{'='*70}")
    print(f"Test Summary: Passed {passed}/{passed+failed}, Failed {failed}/{passed+failed}")
    print("=" * 70)
    
    if failed == 0:
        print("\nAll tests passed! PDF Structured Extraction API is working correctly.")
        print(f"\nAPI Documentation: {BASE_URL}/docs")
        print("\nAvailable Test Samples:")
        for pdf_file in sorted(SAMPLES_DIR.glob("*.pdf")):
            size_kb = pdf_file.stat().st_size / 1024
            print(f"  - {pdf_file.name} ({size_kb:.1f} KB)")
        
        print("\n" + "=" * 70)
        print("Example CURL Commands:")
        print("=" * 70)
        print(f"\n# List all samples")
        print(f"curl {BASE_URL}/api/v1/samples")
        print(f"\n# Upload PDF and extract metadata")
        print(f"curl -X POST -F \"file=@sample.pdf\" {BASE_URL}/api/v1/extract/metadata")
        print(f"\n# Upload PDF and extract all info")
        print(f"curl -X POST -F \"file=@sample.pdf\" {BASE_URL}/api/v1/extract/all")
        print(f"\n# Use preloaded sample for table extraction")
        print(f"curl {BASE_URL}/api/v1/samples/sample3_tables.pdf/extract/tables")
        print(f"\n# Use preloaded sample for text extraction (page 1)")
        print(f"curl {BASE_URL}/api/v1/samples/sample1_single_column.pdf/extract/text?page=1")
        print()
    else:
        print(f"\n{failed} tests failed. Please check the server logs.")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
