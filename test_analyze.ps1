$body = @{
    question = "分析2026年中国新能源乘用车市场竞争格局"
    analysis_type = "comprehensive"
    time_range = "最近12个月"
    max_cycles = 3
} | ConvertTo-Json

$headers = @{
    "Content-Type" = "application/json"
}

$response = Invoke-WebRequest -Uri "http://localhost:8003/analyze_sse" -Method POST -Headers $headers -Body $body -TimeoutSec 120 -UseBasicParsing -ContentType "application/json"
$response.StatusCode
$response.Content | Select-Object -First 100
