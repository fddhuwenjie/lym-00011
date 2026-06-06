# API 修复验证脚本
$baseUrl = "http://localhost:8011/api/v1"
$outputFile = "api_test_results.txt"

# 清空输出文件
Clear-Content -Path $outputFile -ErrorAction SilentlyContinue

function Log($msg) {
    Write-Host $msg
    Add-Content -Path $outputFile -Value $msg
}

Log "=============================================="
Log "PDF 结构化抽取 API - 修复验证测试"
Log "=============================================="
Log ""

# 测试1: 多栏PDF标题不被拆分
Log "=============================================="
Log "测试1: 多栏PDF标题不被拆分 (sample2)"
Log "=============================================="

try {
    $response = Invoke-WebRequest -Uri "$baseUrl/samples/sample2_multi_column.pdf/extract/layout?page=1" -UseBasicParsing
    $json = $response.Content | ConvertFrom-Json
    $data = $json.data

    Log "检测到栏数: $($data.columns_detected)"
    Log "跨栏元素数: $($data.span_elements_count)"
    Log "总片段数: $($data.fragments.Count)"
    Log ""

    Log "标题相关片段:"
    $titleFound = $false
    $allTitleSpan = $true

    foreach ($frag in $data.fragments) {
        if ($frag.text -match "深度|图像|识别|研究|技术") {
            $titleFound = $true
            Log "  text='$($frag.text)', is_span_column=$($frag.is_span_column), column=$($frag.column), font_size=$($frag.font_size)"
            if (-not $frag.is_span_column) {
                $allTitleSpan = $false
            }
        }
    }

    Log ""
    if ($titleFound -and $allTitleSpan) {
        Log "+ 测试通过: 标题被正确识别为跨栏元素，不会被拆分"
    } elseif ($titleFound) {
        Log "- 测试失败: 部分标题未被标记为跨栏"
    } else {
        Log "? 未找到标题相关片段"
    }
} catch {
    Log "- 测试异常: $($_.Exception.Message)"
}

Log ""

# 测试2: 多个独立表格识别
Log "=============================================="
Log "测试2: 多个独立表格识别 (sample3)"
Log "=============================================="

try {
    $response = Invoke-WebRequest -Uri "$baseUrl/samples/sample3_tables.pdf/extract/tables" -UseBasicParsing
    $json = $response.Content | ConvertFrom-Json
    $data = $json.data

    Log "总表格数: $($data.total_tables)"
    Log ""

    foreach ($page in $data.pages) {
        Log "第 $($page.page) 页表格数: $($page.tables.Count)"
        foreach ($idx in 0..($page.tables.Count - 1)) {
            $table = $page.tables[$idx]
            Log "  表格 $($idx + 1): $($table.rows)行 x $($table.cols)列"
            Log "    位置: ($($table.bbox.x0), $($table.bbox.y0)) - ($($table.bbox.x1), $($table.bbox.y1))"
            if ($table.data.Count -gt 0 -and $table.data[0].Count -gt 0) {
                Log "    第一行: $($table.data[0][0..2] -join ', ')"
            }
            if ($idx -gt 0) {
                $prev = $page.tables[$idx - 1]
                $gap = $table.bbox.y0 - $prev.bbox.y1
                Log "    与上一表格间距: $gap"
            }
        }
    }

    Log ""
    if ($data.total_tables -ge 2) {
        Log "+ 测试通过: 正确识别出 $($data.total_tables) 个独立表格"
    } else {
        Log "- 测试失败: 仅识别出 $($data.total_tables) 个表格，预期至少2个"
    }
} catch {
    Log "- 测试异常: $($_.Exception.Message)"
}

Log ""

# 测试3: 扫描PDF OCR通路
Log "=============================================="
Log "测试3: 扫描PDF OCR通路 (sample5)"
Log "=============================================="

try {
    $response = Invoke-WebRequest -Uri "$baseUrl/samples/sample5_scanned.pdf/extract/metadata" -UseBasicParsing
    $json = $response.Content | ConvertFrom-Json
    $meta = $json.data.metadata

    Log "是否扫描文档: $($meta.is_scanned)"
    Log "页数: $($meta.pages)"
    Log ""

    if ($meta.is_scanned) {
        Log "检测为扫描文档，测试OCR提取..."
        $response2 = Invoke-WebRequest -Uri "$baseUrl/samples/sample5_scanned.pdf/extract/text?page=1" -UseBasicParsing
        $json2 = $response2.Content | ConvertFrom-Json
        $text = $json2.data.text

        Log "第1页文本长度: $($text.Length)"
        if ($text.Length -gt 0) {
            Log "文本预览: $($text.Substring(0, [Math]::Min(100, $text.Length)))"
            Log "+ 测试通过: 扫描PDF已通过OCR提取到文本"
        } else {
            Log "- 测试失败: 扫描PDF未提取到文本（OCR引擎可能未安装）"
        }
    } else {
        Log "- 测试失败: 扫描PDF未被正确识别"
    }
} catch {
    Log "- 测试异常: $($_.Exception.Message)"
}

Log ""
Log "=============================================="
Log "测试完成，详细结果已保存到: $outputFile"
Log "=============================================="
