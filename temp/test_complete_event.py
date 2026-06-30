import urllib.request
import json

url = "http://localhost:8000/analyze_sse"
data = json.dumps({"question": "分析比亚迪市场战略"}).encode("utf-8")
req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
resp = urllib.request.urlopen(req, timeout=20)

buffer = ""
for chunk in iter(lambda: resp.read(512), b""):
    buffer += chunk.decode("utf-8", errors="replace")
    lines = buffer.split("\n")
    buffer = lines.pop()
    for line in lines:
        line = line.strip()
        if line.startswith("data:"):
            payload = line[5:].strip()
            try:
                obj = json.loads(payload)
                print("=== EVENT ===")
                print(json.dumps(obj, ensure_ascii=False, indent=2)[:500])
            except:
                print("raw:", payload[:100])
