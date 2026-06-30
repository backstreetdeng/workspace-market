$r = Invoke-WebRequest -Uri 'http://localhost:8003/health' -TimeoutSec 5 -UseBasicParsing
$r.StatusCode
$r.Content
