import sys, subprocess
sys.stdout.reconfigure(encoding='utf-8')
# 读 raw commit message
result = subprocess.check_output(['git', 'log', '-1', '--format=%B'])
print('=== commit message raw ===')
print(result.decode('utf-8'))