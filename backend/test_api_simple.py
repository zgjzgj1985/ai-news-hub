"""直接测试订阅源API"""
import requests

BASE_URL = 'http://localhost:8000/api/sources'

print('=== 1. Test GET all sources ===')
resp = requests.get(BASE_URL)
print(f'Status: {resp.status_code}')
print(f'Count: {len(resp.json())}')
for s in resp.json():
    print(f'  [{s["id"]}] {s["name"]} (enabled={s["enabled"]})')

print('\n=== 2. Test POST create source ===')
new_data = {'name': 'Test API', 'url': 'https://test.com/feed.xml', 'category': 'test', 'priority': 5}
resp = requests.post(BASE_URL, json=new_data)
print(f'Status: {resp.status_code}')
if resp.status_code == 201:
    created = resp.json()
    new_id = created['id']
    print(f'Created: id={new_id}, name={created["name"]}')
else:
    print(f'Failed: {resp.text}')
    new_id = None

print('\n=== 3. Test GET single source ===')
if new_id:
    resp = requests.get(f'{BASE_URL}/{new_id}')
    print(f'Status: {resp.status_code}')
    if resp.status_code == 200:
        s = resp.json()
        print(f'Got: {s["name"]}')

print('\n=== 4. Test PATCH update source ===')
if new_id:
    resp = requests.patch(f'{BASE_URL}/{new_id}', json={'priority': 8, 'enabled': False})
    print(f'Status: {resp.status_code}')
    if resp.status_code == 200:
        s = resp.json()
        print(f'Updated: priority={s["priority"]}, enabled={s["enabled"]}')

print('\n=== 5. Test DELETE source ===')
if new_id:
    resp = requests.delete(f'{BASE_URL}/{new_id}')
    print(f'Status: {resp.status_code}')

print('\n=== 6. Verify deletion ===')
if new_id:
    resp = requests.get(f'{BASE_URL}/{new_id}')
    print(f'Status: {resp.status_code} (expect 404)')

print('\n=== Test complete ===')
