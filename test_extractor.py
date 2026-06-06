import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.pdf_utils.extractor import extract_pdf

SAMPLES_DIR = Path(__file__).parent / "samples"

def test_sample(sample_name, test_name, extract_type="all"):
    print(f"\n{'='*60}")
    print(f"测试: {test_name}")
    print(f"样本: {sample_name}")
    print(f"抽取类型: {extract_type}")
    print('='*60)
    
    pdf_path = SAMPLES_DIR / sample_name
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()
    
    try:
        result = extract_pdf(pdf_bytes, extract_type)
        
        if extract_type == "text" or (extract_type == "all" and "text" in result):
            text_data = result.get("text", result) if extract_type == "all" else result
            pages = text_data.get("pages", [])
            print(f"\n文本抽取:")
            print(f"  总页数: {len(pages)}")
            if pages:
                first_page_text = pages[0].get("text", "")[:200]
                print(f"  第1页内容预览: {first_page_text}...")
        
        if extract_type == "layout" or (extract_type == "all" and "layout" in result):
            layout_data = result.get("layout", result) if extract_type == "all" else result
            pages = layout_data.get("pages", [])
            print(f"\n布局抽取:")
            print(f"  总页数: {len(pages)}")
            if pages:
                fragments = pages[0].get("fragments", [])
                columns = pages[0].get("columns_detected", 1)
                print(f"  第1页检测到 {columns} 栏")
                print(f"  第1页片段数: {len(fragments)}")
                if fragments:
                    frag = fragments[0]
                    print(f"  第一个片段: 文本='{frag.get('text','')[:30]}', 字体={frag.get('font_name','')}, 字号={frag.get('font_size',0):.1f}, 位置=({frag.get('x0',0):.1f},{frag.get('y0',0):.1f})")
        
        if extract_type == "tables" or (extract_type == "all" and "tables" in result):
            tables_data = result.get("tables", result) if extract_type == "all" else result
            total_tables = tables_data.get("total_tables", 0)
            print(f"\n表格识别:")
            print(f"  总表格数: {total_tables}")
            pages = tables_data.get("pages", [])
            for page in pages:
                page_tables = page.get("tables", [])
                if page_tables:
                    print(f"  第{page['page']}页表格数: {len(page_tables)}")
                    for i, table in enumerate(page_tables):
                        print(f"    表格{i+1}: {table.get('rows',0)}行 x {table.get('cols',0)}列")
                        if table.get("data"):
                            print(f"    第一行: {table['data'][0][:3]}...")
        
        if extract_type == "toc" or (extract_type == "all" and "toc" in result):
            toc_data = result.get("toc", []) if extract_type == "all" else result.get("toc", [])
            print(f"\n目录抽取:")
            print(f"  顶级目录项数: {len(toc_data)}")
            for entry in toc_data[:5]:
                print(f"    L{entry.get('level',0)}: {entry.get('title','')[:40]} -> 第{entry.get('page',0)}页")
                for child in entry.get("children", [])[:3]:
                    print(f"      L{child.get('level',0)}: {child.get('title','')[:35]} -> 第{child.get('page',0)}页")
        
        if extract_type == "metadata" or (extract_type == "all" and "metadata" in result):
            meta_data = result.get("metadata", {})
            print(f"\n元信息:")
            print(f"  标题: {meta_data.get('title','N/A')}")
            print(f"  作者: {meta_data.get('author','N/A')}")
            print(f"  页数: {meta_data.get('pages','N/A')}")
            print(f"  加密: {meta_data.get('encrypted','N/A')}")
            print(f"  页面大小: {meta_data.get('page_size','N/A')}")
            print(f"  创建日期: {meta_data.get('creation_date','N/A')}")
        
        print(f"\n[OK] 测试通过!")
        return True
        
    except Exception as e:
        print(f"\n[FAILED] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("开始测试PDF抽取功能...")
    
    tests = [
        ("sample1_single_column.pdf", "单栏文本 - 全部抽取", "all"),
        ("sample1_single_column.pdf", "单栏文本 - 仅文本", "text"),
        ("sample2_multi_column.pdf", "双栏排版 - 布局还原", "layout"),
        ("sample3_tables.pdf", "表格识别", "tables"),
        ("sample4_toc.pdf", "目录与书签", "toc"),
        ("sample1_single_column.pdf", "元信息", "metadata"),
        ("sample5_scanned.pdf", "扫描PDF - 元信息", "metadata"),
    ]
    
    passed = 0
    failed = 0
    
    for sample_name, test_name, extract_type in tests:
        if test_sample(sample_name, test_name, extract_type):
            passed += 1
        else:
            failed += 1
    
    print(f"\n{'='*60}")
    print(f"测试结果: 通过 {passed}/{passed+failed}, 失败 {failed}/{passed+failed}")
    print('='*60)
    
    sys.exit(0 if failed == 0 else 1)
