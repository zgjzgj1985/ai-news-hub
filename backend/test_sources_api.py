"""测试订阅源API"""
import requests
import json

# 测试获取订阅源列表
try:
    resp = requests.get('http://localhost:8000/api/sources', timeout=5)
    print('=== GET /api/sources ===')
    print(f'Status: {resp.status_code}')
    data = resp.json()
    print(f'订阅源数量: {len(data)}')
    for s in data:
        print(f'  [{s["id"]}] {s["name"]}')
        print(f'       URL: {s["url"]}')
        print(f'       category={s["category"]}, enabled={s["enabled"]}, priority={s["priority"]}')
        print()
except Exception as e:
    print(f'连接错误: {e}')
    print('后端服务可能未启动，请先运行: cd backend && python -m uvicorn main:app --reload')
