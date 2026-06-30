import urllib.request
import json

url = "http://localhost:8000/analyze_sse"
data = json.dumps({"question": "分析比亚迪市场战略"}).encode("utf-8")

req = urllib.request.Request(url, data=data, headers={
    "Content-Type": "application/json",
    "Accept": "text/event-stream"
})

try:
    resp = urllib.request.urlopen(req, timeout=20)
    print(f"Status: {resp.status}")
    print(f"Headers: {dict(resp.headers)}")
    
    import time
    start = time.time()
    buffer = ""
    count = 0
    
    while True:
        chunk = resp.read(1024)
        if not chunk:
            break
        buffer += chunk.decode("utf-8", errors="replace")
        lines = buffer.split("\n")
        buffer = lines.pop()
        
        for line in lines:
            line = line.strip()
            if line.startswith("data:"):
                payload = line[5:].strip()
                try:
                    obj = json.loads(payload)
                    elapsed = time.time() - start
                    stage = obj.get("stage", "?")
                    stype = obj.get("stage_name", "?")
                    status = obj.get("status", "?")
                    summary = obj.get("summary", "?")
                    print(f"[{elapsed:.1f}s] stage={stage} type={stype} status={status} summary={summary[:50]}")
                    count += 1
                    if count >= 15:
                        break
                except:
                    print(f"  raw: {payload[:80]}")
        if count >= 15:
            break
    
except Exception as e:
    print(f"Error: {e}")
