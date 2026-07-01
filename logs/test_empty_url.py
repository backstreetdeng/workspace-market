import os
# 模拟 18003 的 gateway_client.py 行为
os.environ["OPENCLAW_GATEWAY_BASE_URL"] = ""  # 系统 env 是空
url = os.environ.get("OPENCLAW_GATEWAY_BASE_URL", "http://127.0.0.1:18789").rstrip("/")
print(f"URL resolved to: '{url}'")

import urllib.request, json, socket
socket.setdefaulttimeout(8)
payload = {
    'model': 'openclaw/market_strategy',
    'messages': [{'role':'user','content':'ping'}],
    'user': 'market-web:test',
    'stream': False,
    'temperature': 0.2
}
# 完全模拟 gateway_client.py
req = urllib.request.Request(
    f'{url}/v1/chat/completions',
    data=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
    headers={
        'Authorization': 'Bearer 2ec777c61f588861712e0d7d9da2cf909fb2b4f45c954be9',
        'Content-Type': 'application/json',
        'x-openclaw-session-key': 'agent:market_strategy:web:chat:test',
    },
    method='POST'
)
try:
    r = urllib.request.urlopen(req)
    print(f'HTTP {r.status}: {r.read().decode("utf-8")[:300]}')
except urllib.error.HTTPError as e:
    print(f'HTTP {e.code}: {e.read().decode("utf-8", errors="ignore")[:300]}')
except urllib.error.URLError as e:
    print(f'URLError: {e.reason} ({type(e.reason).__name__})')
except Exception as e:
    print(f'EXC ({type(e).__name__}): {e}')