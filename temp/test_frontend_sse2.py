import urllib.request
import json

url = "http://localhost:8000/analyze_sse"
data = json.dumps({"question": "分析比亚迪市场战略"}).encode("utf-8")
req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
resp = urllib.request.urlopen(req, timeout=20)

buffer = ""
events = []
for chunk in iter(lambda: resp.read(2048), b""):
    buffer += chunk.decode("utf-8", errors="replace")
    while "\n" in buffer:
        line, buffer = buffer.split("\n", 1)
        line = line.strip()
        if line.startswith("event:"):
            event_type = line[6:].strip()
            print(f"EVENT_TYPE: {event_type}")
        elif line.startswith("data:"):
            payload = line[5:].strip()
            try:
                obj = json.loads(payload)
                events.append(obj)
                print(f"  data keys: {list(obj.keys())}")
                if "stage" in obj:
                    print(f"  stage={obj.get('stage')}, status={obj.get('status')}, summary={obj.get('summary','')[:60]}")
                else:
                    print(f"  complete event keys: {list(obj.keys())}")
                    print(f"  report length: {len(obj.get('report',''))}")
            except Exception as e:
                print(f"  parse error: {e}, raw: {payload[:80]}")

print(f"\nTotal events received: {len(events)}")
