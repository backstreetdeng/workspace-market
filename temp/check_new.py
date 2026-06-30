import sys
sys.stdout.reconfigure(encoding='utf-8')
raw = open('memory/2026-06-29.md', 'rb').read()
text = raw.decode('utf-8')
marker = '## 22:18-22:59'
idx = text.find(marker)
if idx < 0:
    print('!! 找不到新内容 marker')
else:
    new_text = text[idx:]
    new_lines = new_text.split('\n')
    print(f'新内容开始于字符 {idx}')
    print(f'新内容行数: {len(new_lines)}')
    print(f'新内容字符数: {len(new_text)}')
    print()
    print('--- 22:18-22:59 段全部内容（前 1500 字符）---')
    print(new_text[:1500])
    print()
    print('--- 22:18-22:59 段全部内容（后 1500 字符）---')
    print(new_text[-1500:])