#!/usr/bin/env python3
"""
通过飞书发送文件
"""

import os
import json
import requests
from pathlib import Path

# 配置
FEISHU_APP_ID = "cli_a91bd999acb8dbce"
FEISHU_APP_SECRET = "wnD3iSdOtDU15F5mWoY7rv83IShUXuhW"
FILE_PATH = "/Users/admin/.openclaw/workspace/reports/cntin_730_initiatives_report_v5.html"
RECEIVER_ID = "ou_2cee1fc61ad3be5fa26e9a1ebcd69db3"  # Roberto 的 open_id

def get_tenant_access_token():
    """获取 tenant access token"""
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    headers = {"Content-Type": "application/json"}
    data = {
        "app_id": FEISHU_APP_ID,
        "app_secret": FEISHU_APP_SECRET
    }
    
    response = requests.post(url, headers=headers, json=data)
    result = response.json()
    
    if result.get("code") == 0:
        return result.get("tenant_access_token")
    else:
        raise Exception(f"获取 token 失败: {result}")

def upload_file(token, file_path):
    """上传文件到飞书"""
    url = "https://open.feishu.cn/open-apis/im/v1/files"
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    file_name = Path(file_path).name
    
    with open(file_path, 'rb') as f:
        files = {
            'file': (file_name, f, 'text/html')
        }
        data = {
            'file_type': 'stream',
            'file_name': file_name
        }
        
        response = requests.post(url, headers=headers, files=files, data=data)
        result = response.json()
        
        if result.get("code") == 0:
            return result.get("data", {}).get("file_key")
        else:
            raise Exception(f"上传文件失败: {result}")

def send_file_message(token, file_key, receiver_id):
    """发送文件消息"""
    url = "https://open.feishu.cn/open-apis/im/v1/messages"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    params = {
        "receive_id_type": "open_id"
    }
    
    content = json.dumps({
        "file_key": file_key
    })
    
    data = {
        "receive_id": receiver_id,
        "msg_type": "file",
        "content": content
    }
    
    response = requests.post(url, headers=headers, params=params, json=data)
    result = response.json()
    
    if result.get("code") == 0:
        return True
    else:
        raise Exception(f"发送消息失败: {result}")

def main():
    print("📤 正在通过飞书发送文件...")
    
    # 1. 获取 token
    print("1. 获取 tenant access token...")
    token = get_tenant_access_token()
    print("✅ Token 获取成功")
    
    # 2. 上传文件
    print("2. 上传文件...")
    file_key = upload_file(token, FILE_PATH)
    print(f"✅ 文件上传成功, file_key: {file_key}")
    
    # 3. 发送消息
    print("3. 发送文件消息...")
    send_file_message(token, file_key, RECEIVER_ID)
    print("✅ 文件发送成功!")

if __name__ == '__main__':
    main()
