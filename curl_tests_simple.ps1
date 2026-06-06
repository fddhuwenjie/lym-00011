$BASE_URL = "http://localhost:8011"
$SAMPLES_DIR = "$PSScriptRoot\samples"

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "PDF Structured Extraction API - CURL Validation Tests" -ForegroundColor Cyan
Write-Host "Server: $BASE_URL" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan

$Passed = 0
$Failed = 0

function Run-Test {
    param(
        [string]$TestName,
        [string]$Method,
        [string]$Url,
        [string]$SampleFile = $null
    )
    
    Write-Host ""
    Write-Host "[TEST] $TestName" -ForegroundColor Yellow
    Write-Host "  URL: $Url" -ForegroundColor DarkGray
    
    try {
        if ($SampleFile) {
            $FileBytes = [System.IO.File]::ReadAllBytes($SampleFile)
            $FileName = Split-Path $SampleFile -Leaf
            $MultipartContent = New-Object System.Net.Http.MultipartFormDataContent
            $ByteArrayContent = New-Object System.Net.Http.ByteArrayContent($FileBytes)
            $ByteArrayContent.Headers.ContentType = "application/pdf"
            $MultipartContent.Add($ByteArrayContent, "file", $FileName)
            
            $Response = Invoke-WebRequest -Method $Method -Uri $Url -Body $MultipartContent -ContentType "multipart/form-data" -ErrorAction Stop
        } else {
            $Response = Invoke-WebRequest -Method $Method -Uri $Url -ErrorAction Stop
        }
        
        $StatusCode = $Response.StatusCode
        $Json = $Response.Content | ConvertFrom-Json -ErrorAction SilentlyContinue
        
        Write-Host "  Status: $StatusCode" -ForegroundColor Green
        
        if ($Json -and $Json.success -eq $true) {
            Write-Host "  Result: PASS" -ForegroundColor Green
            return $true
        } else {
            Write-Host "  Result: FAIL" -ForegroundColor Red
            if ($Json) {
                Write-Host "  Error: $($Json.data)" -ForegroundColor Red
            }
            return $false
        }
    } catch {
        $ErrCode = $_.Exception.Response.StatusCode.value__
        Write-Host "  Status: $ErrCode" -ForegroundColor Red
        Write-Host "  Result: FAIL" -ForegroundColor Red
        Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

Write-Host ""
Write-Host "--- Basic Tests ---" -ForegroundColor Magenta

if (Run-Test -TestName "Health Check" -Method "GET" -Url "$BASE_URL/") { $Passed++ } else { $Failed++ }
if (Run-Test -TestName "List Samples" -Method "GET" -Url "$BASE_URL/api/v1/samples") { $Passed++ } else { $Failed++ }

Write-Host ""
Write-Host "--- URL-based Extraction Tests ---" -ForegroundColor Magenta

if (Run-Test -TestName "Metadata - Sample1 (single column)" -Method "GET" -Url "$BASE_URL/api/v1/samples/sample1_single_column.pdf/extract/metadata") { $Passed++ } else { $Failed++ }
if (Run-Test -TestName "Text Extraction - Sample1 Page 1" -Method "GET" -Url "$BASE_URL/api/v1/samples/sample1_single_column.pdf/extract/text?page=1") { $Passed++ } else { $Failed++ }
if (Run-Test -TestName "Layout Extraction - Sample2 (multi-column)" -Method "GET" -Url "$BASE_URL/api/v1/samples/sample2_multi_column.pdf/extract/layout?page=1") { $Passed++ } else { $Failed++ }
if (Run-Test -TestName "Table Extraction - Sample3" -Method "GET" -Url "$BASE_URL/api/v1/samples/sample3_tables.pdf/extract/tables?page=1") { $Passed++ } else { $Failed++ }
if (Run-Test -TestName "TOC Extraction - Sample4" -Method "GET" -Url "$BASE_URL/api/v1/samples/sample4_toc.pdf/extract/toc") { $Passed++ } else { $Failed++ }
if (Run-Test -TestName "Metadata - Sample5 (scanned)" -Method "GET" -Url "$BASE_URL/api/v1/samples/sample5_scanned.pdf/extract/metadata") { $Passed++ } else { $Failed++ }

Write-Host ""
Write-Host "--- File Upload Extraction Tests ---" -ForegroundColor Magenta

$S1 = "$SAMPLES_DIR\sample1_single_column.pdf"
$S2 = "$SAMPLES_DIR\sample2_multi_column.pdf"
$S3 = "$SAMPLES_DIR\sample3_tables.pdf"
$S4 = "$SAMPLES_DIR\sample4_toc.pdf"

if (Run-Test -TestName "Upload Metadata - Sample1" -Method "POST" -Url "$BASE_URL/api/v1/extract/metadata" -SampleFile $S1) { $Passed++ } else { $Failed++ }
if (Run-Test -TestName "Upload Text - Sample2 Page 1" -Method "POST" -Url "$BASE_URL/api/v1/extract/text?page=1" -SampleFile $S2) { $Passed++ } else { $Failed++ }
if (Run-Test -TestName "Upload Layout - Sample2" -Method "POST" -Url "$BASE_URL/api/v1/extract/layout?page=1" -SampleFile $S2) { $Passed++ } else { $Failed++ }
if (Run-Test -TestName "Upload Tables - Sample3" -Method "POST" -Url "$BASE_URL/api/v1/extract/tables?page=1" -SampleFile $S3) { $Passed++ } else { $Failed++ }
if (Run-Test -TestName "Upload TOC - Sample4" -Method "POST" -Url "$BASE_URL/api/v1/extract/toc" -SampleFile $S4) { $Passed++ } else { $Failed++ }
if (Run-Test -TestName "Upload All - Sample2 (multi-column)" -Method "POST" -Url "$BASE_URL/api/v1/extract/all" -SampleFile $S2) { $Passed++ } else { $Failed++ }

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "Test Complete: Passed $Passed/$($Passed + $Failed), Failed $Failed/$($Passed + $Failed)" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan

if ($Failed -eq 0) {
    Write-Host ""
    Write-Host "All tests passed! PDF extraction API is working correctly." -ForegroundColor Green
    Write-Host ""
    Write-Host "API Docs: $BASE_URL/docs" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Available Samples:" -ForegroundColor Cyan
    Get-ChildItem $SAMPLES_DIR -Filter *.pdf | ForEach-Object {
        $SizeKB = [math]::Round($_.Length / 1KB, 1)
        Write-Host "  - $($_.Name) ($SizeKB KB)"
    }
} else {
    Write-Host ""
    Write-Host "Some tests failed. Please check the server status." -ForegroundColor Yellow
}

exit $Failed
