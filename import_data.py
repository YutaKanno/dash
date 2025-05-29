import os
import io
import pandas as pd
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

from dotenv import load_dotenv
load_dotenv()

CLIENT_SECRET_FILE = os.getenv('GOOGLE_CLIENT_SECRET_JSON_PATH')
FILE_ID = os.getenv('GOOGLE_DRIVE_FILE_ID')

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def authenticate_google_drive():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
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

