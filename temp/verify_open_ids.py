import os
os.chdir(r"C:\Users\11489\.openclaw\workspace-market")
files = ["SOUL.md", "MEMORY.md", ".learnings/LEARNINGS.md", "memory/2026-06-29.md"]
old_ids = [
    "ou_a4b3294e4facf8d2245f93670a1eb2e0",
    "ou_9ddee84f9fcf21d93ed458a570cc23c6",
    "ou_cff96255f27cd4de8f4a4b7d287558d1",
    "ou_de94d66a3b8676adb827399f88eb0fc9",
]
for f in files:
    with open(f, "rb") as fh:
        data = fh.read()
    text = data.decode("utf-8")
    for oid in old_ids:
        if oid in text:
            # 找位置
            idx = text.find(oid)
            print(f"{f} 仍有旧 {oid} 在位置 {idx}: ...{text[max(0,idx-30):idx+50]}...")
    print(f"  {f}: OK (无旧 open_id)")
