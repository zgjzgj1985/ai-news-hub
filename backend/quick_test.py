import requests
r = requests.get('http://localhost:8000/api/sources')
print('Status:', r.status_code)
print('Sources:', len(r.json()))
for s in r.json():
    print(f'  {s["id"]}. {s["name"]} enabled={s["enabled"]}')
