import urllib.request, json, socket, time
socket.setdefaulttimeout(15)
payload = {
    'model': 'openclaw/market_strategy',
    'messages': [{'role':'user','content':'ping'}],
    'user': 'market-web:e2e_test_suv_001',
    'stream': False,
    'temperature': 0.2
}
req = urllib.request.Request(
    'http://127.0.0.1:18789/v1/chat/completions',
    data=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
    headers={
        'Authorization': 'Bearer 2ec777c61f588861712e0d7d9da2cf909fb2b4f45c954be9',
        'Content-Type': 'application/json',
        'x-openclaw-session-key': 'agent:market_strategy:web:chat:e2e_test_suv_001',
    },
    method='POST'
)
t0 = time.time()
try:
    r = urllib.request.urlopen(req)
    body = r.read().decode('utf-8')
    print(f'HTTP {r.status} in {time.time()-t0:.1f}s')
    print(body[:800])
except urllib.error.HTTPError as e:
    print(f'HTTP {e.code} in {time.time()-t0:.1f}s')
    err_body = e.read().decode('utf-8', errors='ignore')
    print(f'Body: {err_body[:800]}')
except Exception as e:
    print(f'EXCEPTION ({type(e).__name__}) in {time.time()-t0:.1f}s: {e}')