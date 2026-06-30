import requests
import json

resp = requests.post(
    "http://localhost:8000/analyze_sse",
    json={"question": "分析比亚迪在20-30万纯电SUV市场的竞品"},
    stream=True,
    timeout=30
)
print(f"Status: {resp.status_code}")
print(f"Content-Type: {resp.headers.get('Content-Type')}")

# Read just the first few SSE events
count = 0
for line in resp.iter_lines():
    if line:
        decoded = line.decode('utf-8')
        if decoded.startswith('data:'):
            print(decoded[:100])
            count += 1
            if count >= 5:
                break
print("SSE test OK")
