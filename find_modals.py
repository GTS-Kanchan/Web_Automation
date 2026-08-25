from bs4 import BeautifulSoup

html = open('popup_fail_dump.html', encoding='utf-8').read()
soup = BeautifulSoup(html, 'html.parser')

elements = soup.select("[x-data*='LivewireUIModal'], [x-data*='modal' i], [role='dialog'], .modal")

for i, tag in enumerate(elements):
    print(f"Match {i}:")
    print(f"  Tag: {tag.name}")
    print(f"  Class: {tag.get('class')}")
    print(f"  ID: {tag.get('id')}")
    print(f"  x-data: {tag.get('x-data')}")
    print(f"  role: {tag.get('role')}")
    print()
