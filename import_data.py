import os
import io
import json
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# 環境変数からサービスアカウントJSONを文字列として読み込み（一行JSONでもOK）
SERVICE_ACCOUNT_JSON = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
FILE_ID = os.getenv('GOOGLE_DRIVE_FILE_ID')

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def authenticate_google_drive():
    # JSON文字列を辞書に変換
    service_account_info = json.loads(SERVICE_ACCOUNT_JSON)
    creds = service_account.Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
    return creds

def read_uploaded_csv_from_drive(file_id):
    creds = authenticate_google_drive()
    service = build('drive', 'v3', credentials=creds)

    try:
        request = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        fh.seek(0)
        df = pd.read_csv(fh)
        return df

    except Exception as e:
        print(f"読み込み中にエラーが発生しました: {e}")
        return None
