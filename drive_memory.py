import os, json, io
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload

# drive.file scope: LEO can only see/edit files IT creates, not your whole Drive
SCOPES = ['https://www.googleapis.com/auth/drive.file']
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_PATH = os.path.join(BASE_DIR, 'credentials.json')
TOKEN_PATH = os.path.join(BASE_DIR, 'token.json')
MEMORY_FILENAME = 'leo_memory.json'

def _get_credentials():
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, 'w') as f:
            f.write(creds.to_json())
    return creds

def _get_service():
    return build('drive', 'v3', credentials=_get_credentials())

def _find_memory_file_id(service):
    results = service.files().list(
        q=f"name='{MEMORY_FILENAME}' and trashed=false",
        spaces='drive',
        fields='files(id, name)'
    ).execute()
    files = results.get('files', [])
    return files[0]['id'] if files else None

def load_memory():
    service = _get_service()
    file_id = _find_memory_file_id(service)
    if not file_id:
        return {}
    request = service.files().get_media(fileId=file_id)
    buf = io.BytesIO()
    downloader = MediaIoBaseDownload(buf, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    buf.seek(0)
    try:
        return json.loads(buf.read().decode('utf-8'))
    except json.JSONDecodeError:
        return {}

def save_memory(data):
    service = _get_service()
    file_id = _find_memory_file_id(service)
    content = json.dumps(data, indent=2).encode('utf-8')
    media = MediaIoBaseUpload(io.BytesIO(content), mimetype='application/json', resumable=False)
    if file_id:
        service.files().update(fileId=file_id, media_body=media).execute()
    else:
        service.files().create(body={'name': MEMORY_FILENAME}, media_body=media, fields='id').execute()

def remember(key, value):
    data = load_memory()
    data[key] = value
    save_memory(data)
    return f"Remembered: {key} = {value}"

def recall(key=None):
    data = load_memory()
    if key is None:
        return data
    return data.get(key, "I don't have that stored.")