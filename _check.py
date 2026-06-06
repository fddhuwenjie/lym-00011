import sys, os
sys.path.insert(0, '.')

samples = [
    'samples/sample1_single_column.pdf',
    'samples/sample2_multi_column.pdf',
    'samples/sample3_tables.pdf',
    'samples/sample4_toc.pdf',
    'samples/sample5_scanned.pdf',
]

print('--- file sizes ---')
for s in samples:
    if os.path.exists(s):
        print(s, os.path.getsize(s), 'bytes')
    else:
        print(s, 'MISSING')

try:
    from app.pdf_utils.extractor import PDFExtractor
except Exception as e:
    print('IMPORT ERROR:', e)
    sys.exit(1)

for s in samples[:4]:
    if not os.path.exists(s):
        continue
    print(f'\n=== {s} ===')
    try:
        with open(s, 'rb') as f:
            data = f.read()
        with PDFExtractor(data) as ex:
            md = ex.get_metadata()
            print('  pages=', md.pages, 'encrypted=', md.encrypted, 'title=', md.title)
            toc = ex.extract_toc()
            print('  toc_top_entries=', len(toc), '(first 3 titles):',
                  [t.title for t in toc[:3]])
            tx = ex.extract_text(0)
            tlen = len(tx.get('text', ''))
            print('  page0 text length=', tlen, 'first 80 chars:', tx.get('text', '')[:80].replace('\n', ' / '))
            tbl = ex.extract_tables(0)
            print('  page0 table_count=', tbl.get('table_count', 0))
            lay = ex.extract_layout(0)
            print('  page0 columns_detected=', lay.get('columns_detected', 0), 'fragments=', len(lay.get('fragments', [])))
    except Exception as e:
        print('  ERROR:', repr(e))
