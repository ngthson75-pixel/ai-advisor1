#!/usr/bin/env python3
"""
Chạy script này 1 lần trên máy local để lấy refresh token.
Sau đó copy 3 values vào Render env vars.

Cài thư viện trước:
  pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client

Cách dùng:
  1. Download OAuth credentials JSON từ Google Cloud Console
  2. Đặt tên file là credentials.json cùng thư mục với script này
  3. Chạy: python get_gmail_token.py
  4. Browser sẽ mở → đăng nhập bằng aiadvisorhotline@gmail.com → Allow
  5. Copy 3 values xuất hiện vào Render env vars
"""

import json
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def main():
    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
    creds = flow.run_local_server(port=0)
    
    print("\n" + "="*60)
    print("✅ THÀNH CÔNG! Copy 3 values này vào Render env vars:")
    print("="*60)
    print(f"\nGMAIL_CLIENT_ID     = {creds.client_id}")
    print(f"GMAIL_CLIENT_SECRET = {creds.client_secret}")
    print(f"GMAIL_REFRESH_TOKEN = {creds.refresh_token}")
    print("\n" + "="*60)

if __name__ == '__main__':
    main()
