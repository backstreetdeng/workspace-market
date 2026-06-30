$url = "http://localhost:8003/analyze_sse"
$body = @{
    question = "分析2026年中国新能源乘用车市场竞争格局"
    analysis_type = "comprehensive"
    time_range = "最近12个月"
    max_cycles = 3
} | ConvertTo-Json -Depth 3

$headers = @{
    "Content-Type" = "application/json"
}

try {
    $resp = Invoke-WebRequest -Uri $url -Method POST -Headers $headers -Body ([Text.Encoding]::UTF8.GetBytes($body)) -TimeoutSec 120 -UseBasicParsing
    Write-Host "Status:" $resp.StatusCode
    Write-Host "Content:" $resp.Content
} catch {
    Write-Host "Error:" $_.Exception.Message
    Write-Host "Response:" $_.Exception.Response
}
