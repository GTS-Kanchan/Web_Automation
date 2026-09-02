import re
import base64

with open('reports/test_report.html', 'r', encoding='utf-8') as f:
    html = f.read()

matches = re.findall(r'data:image/png;base64,([^"]+)', html)
for i, b64 in enumerate(matches):
    with open(f'fail_{i}.png', 'wb') as img:
        img.write(base64.b64decode(b64))
        print(f"Saved fail_{i}.png")
