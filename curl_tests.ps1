$BASE_URL = "http://localhost:8011"
$SAMPLES_DIR = "$PSScriptRoot\samples"

Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "PDF 结构化抽取 API - CURL 验证测试" -ForegroundColor Cyan
Write-Host "服务地址: $BASE_URL" -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Cyan

function Test-API {
    param(
        [string]$Name,
        [string]$Method,
        [string]$Url,
        [hashtable]$Params = @{},
        [string]$FilePath = $null,
        [switch]$ShowResponse,
        [int]$MaxShow = 800
    )
    
    Write-Host ""
    Write-Host "[" -ForegroundColor Gray -NoNewline
    Write-Host "测试" -ForegroundColor Yellow -NoNewline
    Write-Host "] " -ForegroundColor Gray -NoNewline
    Write-Host $Name -ForegroundColor White
    Write-Host "  URL: $Url" -ForegroundColor DarkGray
    
    try {
        if ($FilePath) {
            $FileBytes = [System.IO.File]::ReadAllBytes($FilePath)
            $FileName = Split-Path $FilePath -Leaf
            $MultipartContent = New-Object System.Net.Http.MultipartFormDataContent
            $ByteArrayContent = New-Object System.Net.Http.ByteArrayContent($FileBytes)
            $ByteArrayContent.Headers.ContentType = "application/pdf"
            $MultipartContent.Add($ByteArrayContent, "file", $FileName)
            
            if ($Params.Count -gt 0) {
                $QueryParams = ($Params.GetEnumerator() | ForEach-Object { "$($_.Key)=$($_.Value)" }) -join "&"
                $Url = "$Url`?$QueryParams"
            }
            
            $Response = Invoke-WebRequest -Method $Method -Uri $Url -Body $MultipartContent -ContentType "multipart/form-data" -ErrorAction Stop
        } else {
            $Response = Invoke-WebRequest -Method $Method -Uri $Url -Body $Params -ErrorAction Stop
        }
        
        Write-Host "  状态码: " -ForegroundColor DarkGray -NoNewline
        Write-Host $Response.StatusCode -ForegroundColor Green
        
        $Json = $Response.Content | ConvertFrom-Json -ErrorAction SilentlyContinue
        
        if ($ShowResponse -and $Json) {
            Write-Host "  响应内容:" -ForegroundColor DarkGray
            $JsonStr = $Json | ConvertTo-Json -Depth 10
            if ($JsonStr.Length -gt $MaxShow) {
                Write-Host $JsonStr.Substring(0, $MaxShow) -ForegroundColor Gray
                Write-Host "... (内容已截断，共 $($JsonStr.Length) 字符)" -ForegroundColor DarkGray
            } else {
                Write-Host $JsonStr -ForegroundColor Gray
            }
        }
        
        if ($Json.success -eq $true) {
            Write-Host "  结果: " -ForegroundColor DarkGray -NoNewline
            Write-Host "PASS ✓" -ForegroundColor Green
            return $true
        } else {
            Write-Host "  结果: " -ForegroundColor DarkGray -NoNewline
            Write-Host "FAIL ✗" -ForegroundColor Red
            Write-Host "  错误: $($Json.data)" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "  状态码: " -ForegroundColor DarkGray -NoNewline
        Write-Host $_.Exception.Response.StatusCode.value__ -ForegroundColor Red
        Write-Host "  结果: " -ForegroundColor DarkGray -NoNewline
        Write-Host "FAIL ✗" -ForegroundColor Red
        Write-Host "  错误: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

$Passed = 0
$Failed = 0

Write-Host ""
Write-Host "--- 基础功能测试 ---" -ForegroundColor Magenta

if (Test-API -Name "健康检查" -Method "GET" -Url "$BASE_URL/") { $Passed++ } else { $Failed++ }
if (Test-API -Name "获取样本列表" -Method "GET" -Url "$BASE_URL/api/v1/samples" -ShowResponse) { $Passed++ } else { $Failed++ }

Write-Host ""
Write-Host "--- URL方式抽取测试（使用预置样本）---" -ForegroundColor Magenta

if (Test-API -Name "元信息 - 样本1(单栏)" -Method "GET" -Url "$BASE_URL/api/v1/samples/sample1_single_column.pdf/extract/metadata" -ShowResponse) { $Passed++ } else { $Failed++ }
if (Test-API -Name "文本抽取 - 样本1第1页" -Method "GET" -Url "$BASE_URL/api/v1/samples/sample1_single_column.pdf/extract/text" -Params @{page = 1} -ShowResponse) { $Passed++ } else { $Failed++ }
if (Test-API -Name "布局还原 - 样本2(双栏)" -Method "GET" -Url "$BASE_URL/api/v1/samples/sample2_multi_column.pdf/extract/layout" -Params @{page = 1} -ShowResponse -MaxShow 1200) { $Passed++ } else { $Failed++ }
if (Test-API -Name "表格识别 - 样本3" -Method "GET" -Url "$BASE_URL/api/v1/samples/sample3_tables.pdf/extract/tables" -Params @{page = 1} -ShowResponse -MaxShow 1500) { $Passed++ } else { $Failed++ }
if (Test-API -Name "目录抽取 - 样本4" -Method "GET" -Url "$BASE_URL/api/v1/samples/sample4_toc.pdf/extract/toc" -ShowResponse -MaxShow 2000) { $Passed++ } else { $Failed++ }
if (Test-API -Name "元信息 - 样本5(扫描)" -Method "GET" -Url "$BASE_URL/api/v1/samples/sample5_scanned.pdf/extract/metadata" -ShowResponse) { $Passed++ } else { $Failed++ }

Write-Host ""
Write-Host "--- 文件上传抽取测试 ---" -ForegroundColor Magenta

$Sample1 = "$SAMPLES_DIR\sample1_single_column.pdf"
$Sample2 = "$SAMPLES_DIR\sample2_multi_column.pdf"
$Sample3 = "$SAMPLES_DIR\sample3_tables.pdf"
$Sample4 = "$SAMPLES_DIR\sample4_toc.pdf"

if (Test-API -Name "上传抽取元信息 - 样本1" -Method "POST" -Url "$BASE_URL/api/v1/extract/metadata" -FilePath $Sample1 -ShowResponse) { $Passed++ } else { $Failed++ }
if (Test-API -Name "上传抽取文本 - 样本2第1页" -Method "POST" -Url "$BASE_URL/api/v1/extract/text" -Params @{page = 1} -FilePath $Sample2 -ShowResponse -MaxShow 1000) { $Passed++ } else { $Failed++ }
if (Test-API -Name "上传抽取布局 - 样本2" -Method "POST" -Url "$BASE_URL/api/v1/extract/layout" -Params @{page = 1} -FilePath $Sample2 -ShowResponse -MaxShow 1200) { $Passed++ } else { $Failed++ }
if (Test-API -Name "上传抽取表格 - 样本3" -Method "POST" -Url "$BASE_URL/api/v1/extract/tables" -Params @{page = 1} -FilePath $Sample3 -ShowResponse -MaxShow 1500) { $Passed++ } else { $Failed++ }
if (Test-API -Name "上传抽取目录 - 样本4" -Method "POST" -Url "$BASE_URL/api/v1/extract/toc" -FilePath $Sample4 -ShowResponse -MaxShow 2000) { $Passed++ } else { $Failed++ }
if (Test-API -Name "上传抽取全部 - 样本2(双栏)" -Method "POST" -Url "$BASE_URL/api/v1/extract/all" -FilePath $Sample2 -ShowResponse -MaxShow 1500) { $Passed++ } else { $Failed++ }

Write-Host ""
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "测试完成! " -ForegroundColor Cyan -NoNewline
Write-Host "通过: $Passed/$($Passed + $Failed)" -ForegroundColor Green -NoNewline
Write-Host ", 失败: $Failed/$($Passed + $Failed)" -ForegroundColor Red
Write-Host "=" * 70 -ForegroundColor Cyan

if ($Failed -eq 0) {
    Write-Host ""
    Write-Host "🎉 所有测试通过！PDF结构化抽取API服务运行正常。" -ForegroundColor Green
    Write-Host ""
    Write-Host "API文档: $BASE_URL/docs" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "预置测试样本:" -ForegroundColor Cyan
    Get-ChildItem $SAMPLES_DIR -Filter *.pdf | ForEach-Object {
        $SizeKB = [math]::Round($_.Length / 1KB, 1)
        Write-Host "  - $($_.Name) ($SizeKB KB)" -ForegroundColor White
    }
    Write-Host ""
    Write-Host "示例命令:" -ForegroundColor Cyan
    Write-Host "  # 获取样本列表" -ForegroundColor DarkGray
    Write-Host "  curl $BASE_URL/api/v1/samples" -ForegroundColor White
    Write-Host "  # 上传PDF抽取元信息" -ForegroundColor DarkGray
    Write-Host "  curl -X POST -F 'file=@sample.pdf' $BASE_URL/api/v1/extract/metadata" -ForegroundColor White
    Write-Host "  # 使用预置样本抽取表格" -ForegroundColor DarkGray
    Write-Host "  curl $BASE_URL/api/v1/samples/sample3_tables.pdf/extract/tables" -ForegroundColor White
} else {
    Write-Host ""
    Write-Host "⚠️  有 $Failed 个测试失败，请检查服务状态。" -ForegroundColor Yellow
}
