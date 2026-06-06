import sys
import requests
import json
from pathlib import Path

BASE_URL = "http://localhost:8011"
SAMPLES_DIR = Path(__file__).parent / "samples"

def print_result(name, response, show_data=True, max_len=500):
    print(f"\n{'='*70}")
    print(f"测试: {name}")
    print(f"URL: {response.url}")
    print(f"状态码: {response.status_code}")
    print('='*70)
    
    if response.status_code == 200:
        try:
            data = response.json()
            if show_data:
                if isinstance(data, dict) and "data" in data:
                    data_str = json.dumps(data["data"], ensure_ascii=False, indent=2)
                    if len(data_str) > max_len:
                        print(data_str[:max_len] + "\n... (内容已截断)")
                    else:
                        print(data_str)
                elif isinstance(data, dict) and "samples" in data:
                    print(f"样本数量: {data.get('count', 0)}")
                    for sample in data.get("samples", []):
                        print(f"  - {sample.get('name')}: {sample.get('description')} ({sample.get('size_kb', 0):.1f} KB)")
                else:
                    data_str = json.dumps(data, ensure_ascii=False, indent=2)
                    if len(data_str) > max_len:
                        print(data_str[:max_len] + "\n... (内容已截断)")
                    else:
                        print(data_str)
            print("\n[SUCCESS]")
            return True
        except Exception as e:
            print(f"响应解析失败: {e}")
            print(f"响应内容: {response.text[:200]}")
    else:
        print(f"错误信息: {response.text[:200]}")
    
    print("\n[FAILED]")
    return False


def test_root():
    resp = requests.get(f"{BASE_URL}/")
    return print_result("API根路径 - 健康检查", resp, show_data=True)


def test_list_samples():
    resp = requests.get(f"{BASE_URL}/api/v1/samples")
    return print_result("获取测试样本列表", resp, show_data=True)


def test_extract_metadata_by_url():
    resp = requests.get(f"{BASE_URL}/api/v1/samples/sample1_single_column.pdf/extract/metadata")
    return print_result("通过URL获取样本1元信息", resp, show_data=True)


def test_extract_text_by_url():
    resp = requests.get(f"{BASE_URL}/api/v1/samples/sample1_single_column.pdf/extract/text?page=1")
    return print_result("通过URL获取样本1第1页文本", resp, show_data=True, max_len=800)


def test_extract_layout_by_url():
    resp = requests.get(f"{BASE_URL}/api/v1/samples/sample2_multi_column.pdf/extract/layout?page=1")
    return print_result("通过URL获取样本2布局信息（双栏）", resp, show_data=True, max_len=1000)


def test_extract_tables_by_url():
    resp = requests.get(f"{BASE_URL}/api/v1/samples/sample3_tables.pdf/extract/tables?page=1")
    return print_result("通过URL获取样本3表格", resp, show_data=True, max_len=1500)


def test_extract_toc_by_url():
    resp = requests.get(f"{BASE_URL}/api/v1/samples/sample4_toc.pdf/extract/toc")
    return print_result("通过URL获取样本4目录", resp, show_data=True, max_len=2000)


def test_upload_extract_metadata():
    pdf_path = SAMPLES_DIR / "sample1_single_column.pdf"
    with open(pdf_path, "rb") as f:
        files = {"file": ("sample1.pdf", f, "application/pdf")}
        resp = requests.post(f"{BASE_URL}/api/v1/extract/metadata", files=files)
    return print_result("上传文件获取元信息", resp, show_data=True)


def test_upload_extract_all():
    pdf_path = SAMPLES_DIR / "sample2_multi_column.pdf"
    with open(pdf_path, "rb") as f:
        files = {"file": ("sample2.pdf", f, "application/pdf")}
        resp = requests.post(f"{BASE_URL}/api/v1/extract/all", files=files)
    return print_result("上传文件获取全部信息（样本2双栏）", resp, show_data=True, max_len=1200)


def test_upload_extract_tables():
    pdf_path = SAMPLES_DIR / "sample3_tables.pdf"
    with open(pdf_path, "rb") as f:
        files = {"file": ("sample3.pdf", f, "application/pdf")}
        resp = requests.post(f"{BASE_URL}/api/v1/extract/tables?page=1", files=files)
    return print_result("上传文件获取表格（样本3）", resp, show_data=True, max_len=2000)


if __name__ == "__main__":
    print("开始测试PDF抽取API服务...")
    print(f"服务地址: {BASE_URL}")
    
    tests = [
        ("API健康检查", test_root),
        ("获取样本列表", test_list_samples),
        ("URL方式 - 元信息", test_extract_metadata_by_url),
        ("URL方式 - 文本抽取", test_extract_text_by_url),
        ("URL方式 - 布局还原（双栏）", test_extract_layout_by_url),
        ("URL方式 - 表格识别", test_extract_tables_by_url),
        ("URL方式 - 目录抽取", test_extract_toc_by_url),
        ("上传文件 - 元信息", test_upload_extract_metadata),
        ("上传文件 - 全部信息（双栏）", test_upload_extract_all),
        ("上传文件 - 表格识别", test_upload_extract_tables),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"\n{'='*70}")
            print(f"测试: {name}")
            print(f"异常: {e}")
            print("\n[FAILED]")
            failed += 1
    
    print(f"\n{'='*70}")
    print(f"测试总结: 通过 {passed}/{passed+failed}, 失败 {failed}/{passed+failed}")
    print('='*70)
    
    if failed == 0:
        print("\n🎉 所有API测试通过！服务运行正常。")
        print(f"\nAPI文档地址: {BASE_URL}/docs")
        print(f"\n可用的测试样本:")
        for pdf_file in sorted(SAMPLES_DIR.glob("*.pdf")):
            size_kb = pdf_file.stat().st_size / 1024
            print(f"  - {pdf_file.name} ({size_kb:.1f} KB)")
    else:
        print(f"\n❌ 有 {failed} 个测试失败，请检查服务状态。")
    
    sys.exit(0 if failed == 0 else 1)
