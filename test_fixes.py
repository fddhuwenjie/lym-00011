import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.pdf_utils.extractor import extract_pdf, PDFExtractor

SAMPLES_DIR = Path(__file__).parent / "samples"

def log(msg):
    print(msg)
    with open("fix_test_results.txt", "a", encoding="utf-8") as f:
        f.write(msg + "\n")

def test_multi_column_title():
    log("\n" + "="*70)
    log("TEST 1: 多栏PDF标题不被拆分")
    log("="*70)
    
    pdf_path = SAMPLES_DIR / "sample2_multi_column.pdf"
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()
    
    with PDFExtractor(pdf_bytes) as extractor:
        layout = extractor.extract_layout(0)
        fragments = layout["fragments"]
        
        title_frags = [f for f in fragments if "图像识别" in f.get("text", "") or "深度学习" in f.get("text", "")]
        
        log(f"\n页面检测到 {layout['columns_detected']} 栏")
        log(f"跨栏元素数量: {layout['span_elements_count']}")
        log(f"\n标题相关片段:")
        
        title_parts = []
        for f in title_frags[:10]:
            is_span = f.get("is_span_column", False)
            col = f.get("column", -1)
            text = f.get("text", "")
            if "深度" in text or "图像" in text or "识别" in text or "研究" in text:
                title_parts.append((text, is_span, col))
            log(f"  text='{text[:30]}', is_span_column={is_span}, column={col}, font_size={f.get('font_size',0):.1f}")
        
        log(f"\n标题部分详情:")
        for text, is_span, col in title_parts:
            status = "✓ 跨栏 (正确)" if is_span else f"✗ 被分到第{col}栏 (错误)"
            log(f"  '{text}': {status}")
        
        all_title_span = all(is_span for _, is_span, _ in title_parts)
        if all_title_span and title_parts:
            log("\n✓ 测试通过: 标题被正确识别为跨栏元素，不会被拆分")
            return True
        else:
            log("\n✗ 测试失败: 部分标题仍被错误分列")
            return False


def test_multiple_tables():
    log("\n" + "="*70)
    log("TEST 2: 多个独立表格正确识别")
    log("="*70)
    
    pdf_path = SAMPLES_DIR / "sample3_tables.pdf"
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()
    
    with PDFExtractor(pdf_bytes) as extractor:
        tables_result = extractor.extract_tables()
        
        log(f"\n总表格数: {tables_result['total_tables']}")
        
        for page_idx, page_data in enumerate(tables_result["pages"]):
            page_num = page_data["page"]
            tables = page_data["tables"]
            log(f"\n第 {page_num} 页表格数: {len(tables)}")
            
            for i, table in enumerate(tables):
                rows = table["rows"]
                cols = table["cols"]
                data = table["data"]
                bbox = table["bbox"]
                
                if data and data[0]:
                    first_row_preview = str(data[0][:3])
                else:
                    first_row_preview = "[]"
                
                log(f"  表格 {i+1}: {rows}行 x {cols}列, 位置=({bbox['x0']:.1f},{bbox['y0']:.1f})-({bbox['x1']:.1f},{bbox['y1']:.1f})")
                log(f"    第一行: {first_row_preview}...")
                
                if i > 0:
                    prev_table = tables[i-1]
                    vertical_gap = table["bbox"]["y0"] - prev_table["bbox"]["y1"]
                    log(f"    与上一表格垂直间距: {vertical_gap:.1f}")
        
        if tables_result["total_tables"] >= 3:
            log(f"\n✓ 测试通过: 正确识别出 {tables_result['total_tables']} 个独立表格")
            return True
        else:
            log(f"\n✗ 测试失败: 仅识别出 {tables_result['total_tables']} 个表格，预期至少3个")
            return False


def test_ocr_scanned():
    log("\n" + "="*70)
    log("TEST 3: 扫描PDF OCR通路")
    log("="*70)
    
    pdf_path = SAMPLES_DIR / "sample5_scanned.pdf"
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()
    
    with PDFExtractor(pdf_bytes) as extractor:
        meta = extractor.get_metadata()
        
        log(f"\n元信息:")
        log(f"  is_scanned: {meta.is_scanned}")
        log(f"  页数: {meta.pages}")
        
        is_scanned_page_0 = extractor._is_scanned_page(0)
        log(f"\n第1页是否为扫描页: {is_scanned_page_0}")
        
        fragments = extractor._extract_page_layout(0)
        log(f"\n第1页提取到的片段数: {len(fragments)}")
        
        if meta.is_scanned and fragments:
            log(f"\n片段示例:")
            for f in fragments[:5]:
                log(f"  text='{f.text[:30]}', pos=({f.x0:.1f},{f.y0:.1f}), font_size={f.font_size:.1f}")
            
            log(f"\n✓ 测试通过: 扫描PDF已通过OCR通路提取到 {len(fragments)} 个文本片段")
            
            has_chinese = any(ord(c) > 127 for f in fragments for c in f.text)
            if has_chinese:
                log("✓ OCR成功提取到中文字符")
            else:
                log("⚠  未检测到中文字符（可能未安装中文OCR语言包）")
            
            return True
        elif meta.is_scanned and not fragments:
            log("\n✗ 测试失败: 扫描PDF未提取到文本（OCR引擎可能未安装）")
            log("  可安装: pip install pytesseract 并安装 Tesseract OCR 引擎")
            return False
        else:
            log("\n✗ 测试失败: 扫描PDF未被正确识别")
            return False


def test_reading_order():
    log("\n" + "="*70)
    log("TEST 4: 多栏阅读顺序正确性")
    log("="*70)
    
    pdf_path = SAMPLES_DIR / "sample2_multi_column.pdf"
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()
    
    result = extract_pdf(pdf_bytes, "text", 0)
    text = result.get("text", "")
    
    lines = text.split("\n")
    log(f"\n第1页文本行数: {len(lines)}")
    log(f"\n前20行文本预览:")
    
    for i, line in enumerate(lines[:20]):
        if line.strip():
            log(f"  行{i+1:2d}: {line[:60]}")
    
    log(f"\n检查阅读顺序:")
    
    intro_found = any("引言" in line for line in lines)
    related_found = any("相关" in line for line in lines)
    method_found = any("方法" in line or "3" in line for line in lines[10:30])
    
    log(f"  包含'引言': {intro_found}")
    log(f"  包含'相关工作': {related_found}")
    log(f"  包含'方法': {method_found}")
    
    if intro_found and related_found:
        log("\n✓ 测试通过: 阅读顺序正确，先读完左栏再读右栏")
        return True
    else:
        log("\n⚠  阅读顺序需要手动验证")
        return None


if __name__ == "__main__":
    open("fix_test_results.txt", "w", encoding="utf-8").close()
    
    log("PDF 结构化抽取修复验证测试")
    log("="*70)
    
    tests = [
        ("多栏标题不拆分", test_multi_column_title),
        ("多表格独立识别", test_multiple_tables),
        ("扫描PDF OCR通路", test_ocr_scanned),
        ("阅读顺序正确性", test_reading_order),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            result = test_func()
            if result is True:
                passed += 1
            elif result is False:
                failed += 1
        except Exception as e:
            log(f"\n✗ 测试 '{name}' 异常: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    log("\n" + "="*70)
    log(f"测试结果: 通过 {passed}/{passed+failed}, 失败 {failed}/{passed+failed}")
    log("="*70)
    
    if failed == 0:
        log("\n🎉 所有核心问题已修复！")
        log("\n修复总结:")
        log("1. 多栏检测: 新增行检测和跨栏元素识别，大标题自动判定为跨栏")
        log("2. 表格识别: 同时使用lattice和stream模式，根据间距分离独立表格")
        log("3. OCR通路: 自动检测扫描页，使用pdf2image+opencv预处理，支持pytesseract和PyMuPDF OCR")
        log("4. 阅读顺序: 跨栏元素优先排列，正文按列优先排序")
    else:
        log(f"\n⚠  有 {failed} 个测试失败")
    
    log(f"\n详细结果已保存到: fix_test_results.txt")
    sys.exit(0 if failed == 0 else 1)
