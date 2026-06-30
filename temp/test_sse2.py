import requests
import json
import time

print("Testing /analyze_sse...")
start = time.time()
try:
    resp = requests.post(
        "http://localhost:8000/analyze_sse",
        json={"question": "分析比亚迪在20-30万纯电SUV市场的竞品"},
        stream=True,
        timeout=15
    )
    print(f"Status: {resp.status_code}")
    count = 0
    for line in resp.iter_lines():
        if line:
            decoded = line.decode('utf-8')
            if decoded.startswith('data:'):
                print(f"[{time.time()-start:.1f}s] {decoded[:150]}")
                count += 1
                if count >= 8:
                    break
except Exception as e:
    print(f"Error: {e}")
