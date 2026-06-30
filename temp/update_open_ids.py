import os
os.chdir(r"C:\Users\11489\.openclaw\workspace-market")
LF = chr(10)
CRLF = chr(13) + chr(10)

# open_id 映射（从 system 11:18 提示）
id_map = {
    "ou_a4b3294e4facf8d2245f93670a1eb2e0": "ou_99585f227f3320a8f959ef0104955934",  # 战略分析专家
    "ou_9ddee84f9fcf21d93ed458a570cc23c6": "ou_bf2eed5b88b75419c1ecb0c3585bfbac",  # 报告执行专家
    "ou_cff96255f27cd4de8f4a4b7d287558d1": "ou_1f836bd9f17531c6d4306fcc94b23529",  # 编排专家
    "ou_de94d66a3b8676adb827399f88eb0fc9": "ou_aea6c01c9df9dface7740b00c6174053",  # 数据分析专家
}

files = ["SOUL.md", "MEMORY.md", ".learnings/LEARNINGS.md", "memory/2026-06-29.md"]
for f in files:
    if not os.path.exists(f):
        print(f"SKIP {f} (not exists)")
        continue
    with open(f, "rb") as fh:
        data = fh.read()
    text = data.decode("utf-8")
    old_text = text
    for old, new in id_map.items():
        if old in text:
            text = text.replace(old, new)
            print(f"  {f}: 替换 {old} -> {new}")
    if text != old_text:
        # 标准化换行
        text = text.replace(CRLF, LF).replace(LF, CRLF)
        with open(f, "wb") as fh:
            fh.write(text.encode("utf-8"))
        print(f"  {f}: 已写入")
