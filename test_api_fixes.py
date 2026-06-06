import sys
import json
import urllib.request
import urllib.parse

BASE_URL = "http://localhost:8011/api/v1"
OUTPUT_FILE = "api_test_results.txt"

def log(msg):
    print(msg)
    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")

def api_get(endpoint):
    url = f"{BASE_URL}/{endpoint}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as response:
        data = response.read().decode("utf-8")
        return json.loads(data)

def main():
    open(OUTPUT_FILE, "w", encoding="utf-8").close()
    
    log("=" * 50)
    log("PDF 结构化抽取 API - 修复验证测试")
    log("=" * 50)
    log("")

    # 测试1: 多栏PDF标题不被拆分
    log("=" * 50)
    log("测试1: 多栏PDF标题不被拆分 (sample2)")
    log("=" * 50)

    try:
        result = api_get("samples/sample2_multi_column.pdf/extract/layout?page=1")
        data = result["data"]

        log(f"检测到栏数: {data['columns_detected']}")
        log(f"跨栏元素数: {data['span_elements_count']}")
        log(f"总片段数: {len(data['fragments'])}")
        log("")

        log("标题相关片段:")
        title_found = False
        all_title_span = True
        title_texts = []

        for frag in data["fragments"]:
            text = frag.get("text", "")
            if any(key in text for key in ["深度", "图像", "识别", "研究", "技术"]):
                title_found = True
                is_span = frag.get("is_span_column", False)
                col = frag.get("column", -1)
                font_size = frag.get("font_size", 0)
                log(f"  text='{text}', is_span_column={is_span}, column={col}, font_size={font_size:.1f}")
                if not is_span:
                    all_title_span = False
                title_texts.append(text)

        log("")
        if title_found and all_title_span:
            log("+ 测试通过: 标题被正确识别为跨栏元素，不会被拆分")
            log(f"  标题文字: {' '.join(title_texts)}")
        elif title_found:
            log("- 测试失败: 部分标题未被标记为跨栏")
        else:
            log("? 未找到标题相关片段")
    except Exception as e:
        log(f"- 测试异常: {e}")
        import traceback
        traceback.print_exc()

    log("")

    # 测试2: 多个独立表格识别
    log("=" * 50)
    log("测试2: 多个独立表格识别 (sample3)")
    log("=" * 50)

    try:
        result = api_get("samples/sample3_tables.pdf/extract/tables")
        data = result["data"]

        log(f"总表格数: {data['total_tables']}")
        log("")

        for page in data["pages"]:
            page_num = page["page"]
            tables = page["tables"]
            log(f"第 {page_num} 页表格数: {len(tables)}")
            for idx, table in enumerate(tables):
                rows = table["rows"]
                cols = table["cols"]
                bbox = table["bbox"]
                log(f"  表格 {idx + 1}: {rows}行 x {cols}列")
                log(f"    位置: ({bbox['x0']:.1f}, {bbox['y0']:.1f}) - ({bbox['x1']:.1f}, {bbox['y1']:.1f})")
                if table["data"] and table["data"][0]:
                    first_row = table["data"][0][:3]
                    log(f"    第一行: {', '.join(str(x) for x in first_row)}")
                if idx > 0:
                    prev = tables[idx - 1]
                    gap = table["bbox"]["y0"] - prev["bbox"]["y1"]
                    log(f"    与上一表格间距: {gap:.1f}")

        log("")
        if data["total_tables"] >= 2:
            log(f"+ 测试通过: 正确识别出 {data['total_tables']} 个独立表格")
        else:
            log(f"- 测试失败: 仅识别出 {data['total_tables']} 个表格，预期至少2个")
    except Exception as e:
        log(f"- 测试异常: {e}")
        import traceback
        traceback.print_exc()

    log("")

    # 测试3: 扫描PDF OCR通路
    log("=" * 50)
    log("测试3: 扫描PDF OCR通路 (sample5)")
    log("=" * 50)

    try:
        result = api_get("samples/sample5_scanned.pdf/extract/metadata")
        meta = result["data"]["metadata"]

        log(f"是否扫描文档: {meta['is_scanned']}")
        log(f"页数: {meta['pages']}")
        log("")

        if meta["is_scanned"]:
            log("检测为扫描文档，测试OCR提取...")
            result2 = api_get("samples/sample5_scanned.pdf/extract/text?page=1")
            text = result2["data"]["text"]

            log(f"第1页文本长度: {len(text)}")
            if len(text) > 0:
                preview = text[:100].replace("\n", " ")
                log(f"文本预览: {preview}...")
                log("+ 测试通过: 扫描PDF已通过OCR提取到文本")
                has_chinese = any(ord(c) > 127 for c in text)
                if has_chinese:
                    log("  OCR成功提取到中文字符")
                else:
                    log("  警告: 未检测到中文字符（可能未安装中文OCR语言包）")
            else:
                log("- 测试失败: 扫描PDF未提取到文本（OCR引擎可能未安装）")
                log("  可安装: pip install pytesseract 并安装 Tesseract OCR 引擎")
        else:
            log("- 测试失败: 扫描PDF未被正确识别")
    except Exception as e:
        log(f"- 测试异常: {e}")
        import traceback
        traceback.print_exc()

    log("")
    log("=" * 50)
    log("测试完成，详细结果已保存到: " + OUTPUT_FILE)
    log("=" * 50)

if __name__ == "__main__":
    main()
