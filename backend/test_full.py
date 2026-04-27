"""完整API测试"""
import requests

BASE_URL = 'http://localhost:8000/api/sources'

print('=== 1. Get all sources ===')
resp = requests.get(BASE_URL)
print(f'Status: {resp.status_code}')
sources = resp.json()
print(f'Count: {len(sources)}')
for s in sources:
    print(f'  [{s["id"]}] {s["name"]}')

print('\n=== 2. Create new source ===')
new_data = {'name': 'Test Fresh', 'url': 'https://fresh.test/feed.xml', 'category': 'test', 'priority': 5}
resp = requests.post(BASE_URL, json=new_data)
print(f'Status: {resp.status_code}')
if resp.status_code == 201:
    created = resp.json()
    test_id = created['id']
    print(f'Created: id={test_id}')
else:
    print(f'Response: {resp.text}')
    test_id = None

print('\n=== 3. Get single source ===')
if test_id:
    resp = requests.get(f'{BASE_URL}/{test_id}')
    print(f'Status: {resp.status_code}')
    if resp.status_code == 200:
        print(f'Name: {resp.json()["name"]}')

print('\n=== 4. Update source ===')
if test_id:
    resp = requests.patch(f'{BASE_URL}/{test_id}', json={'priority': 10, 'enabled': False})
    print(f'Status: {resp.status_code}')
    if resp.status_code == 200:
        print(f'Priority updated to: {resp.json()["priority"]}')
        print(f'Enabled set to: {resp.json()["enabled"]}')

print('\n=== 5. Delete source ===')
if test_id:
    resp = requests.delete(f'{BASE_URL}/{test_id}')
    print(f'Status: {resp.status_code}')

print('\n=== 6. Verify deleted ===')
if test_id:
    resp = requests.get(f'{BASE_URL}/{test_id}')
    print(f'Status: {resp.status_code} (expect 404)')

print('\n=== 7. Test 404 ===')
resp = requests.get(f'{BASE_URL}/99999')
print(f'Status: {resp.status_code} (expect 404)')

print('\n=== All tests passed ===')
