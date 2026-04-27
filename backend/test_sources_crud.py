"""测试订阅源CRUD API"""
import requests
import json

BASE_URL = 'http://localhost:8000/api/sources'

def test_create_source():
    """测试创建订阅源"""
    print('=== 测试创建订阅源 ===')
    new_source = {
        'name': 'Test Source',
        'url': 'https://example.com/test-feed.xml',
        'category': 'blog',
        'priority': 5
    }
    try:
        resp = requests.post(BASE_URL, json=new_source, timeout=5)
        print(f'Status: {resp.status_code}')
        if resp.status_code == 201:
            data = resp.json()
            print(f'创建成功! ID: {data["id"]}, Name: {data["name"]}')
            return data['id']
        else:
            print(f'创建失败: {resp.text}')
    except Exception as e:
        print(f'连接错误: {e}')
    return None

def test_update_source(source_id):
    """测试更新订阅源"""
    print('\n=== 测试更新订阅源 ===')
    update_data = {'priority': 8, 'enabled': False}
    try:
        resp = requests.patch(f'{BASE_URL}/{source_id}', json=update_data, timeout=5)
        print(f'Status: {resp.status_code}')
        if resp.status_code == 200:
            data = resp.json()
            print(f'更新成功! priority={data["priority"]}, enabled={data["enabled"]}')
    except Exception as e:
        print(f'连接错误: {e}')

def test_delete_source(source_id):
    """测试删除订阅源"""
    print('\n=== 测试删除订阅源 ===')
    try:
        resp = requests.delete(f'{BASE_URL}/{source_id}', timeout=5)
        print(f'Status: {resp.status_code}')
        if resp.status_code == 204:
            print('删除成功!')
        else:
            print(f'删除失败: {resp.text}')
    except Exception as e:
        print(f'连接错误: {e}')

def test_get_source(source_id):
    """测试获取单个订阅源"""
    print('\n=== 测试获取单个订阅源 ===')
    try:
        resp = requests.get(f'{BASE_URL}/{source_id}', timeout=5)
        print(f'Status: {resp.status_code}')
        if resp.status_code == 200:
            data = resp.json()
            print(f'获取成功! {data["name"]} - {data["url"]}')
    except Exception as e:
        print(f'连接错误: {e}')

def test_get_nonexistent():
    """测试获取不存在的订阅源"""
    print('\n=== 测试获取不存在的订阅源 ===')
    try:
        resp = requests.get(f'{BASE_URL}/99999', timeout=5)
        print(f'Status: {resp.status_code}')
        if resp.status_code == 404:
            print('正确返回404')
    except Exception as e:
        print(f'连接错误: {e}')

if __name__ == '__main__':
    # 1. 创建测试订阅源
    new_id = test_create_source()

    # 2. 获取单个订阅源
    if new_id:
        test_get_source(new_id)

    # 3. 更新订阅源
    if new_id:
        test_update_source(new_id)

    # 4. 测试获取不存在的订阅源
    test_get_nonexistent()

    # 5. 删除测试订阅源
    if new_id:
        test_delete_source(new_id)

    print('\n=== 所有测试完成 ===')
