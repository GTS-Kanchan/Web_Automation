from bs4 import BeautifulSoup
import json

with open('tc043_fail.html', 'r', encoding='utf-8') as f:
    soup = BeautifulSoup(f.read(), 'html.parser')

radios = soup.find_all('input', type='radio')
for r in radios:
    print(f"id={r.get('id')} name={r.get('name')} value={r.get('value')} checked={r.has_attr('checked')} wire:model.live={r.get('wire:model.live')}")
