import os
import sys
import io
import httplib2
import warnings

# Suppress metadata warnings
warnings.filterwarnings('ignore')

try:
    from googleapiclient import discovery
    from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
    from oauth2client import client, tools
    from oauth2client.file import Storage
except ImportError as e:
    print(f"Warning: Google API import issue: {e}")


class GoogleOCR:
    """Google Drive OCR Engine using Google Drive API."""

    def __init__(self):
        """Initialize Google OCR with credentials."""
        self.SCOPES = 'https://www.googleapis.com/auth/drive'
        self.CLIENT_SECRET_FILE = 'client_secret_395744274280-ot1ar85i1306dvbo7ql1a7rqblc3j1bn.apps.googleusercontent.com.json'
        self.APPLICATION_NAME = 'Google OCR Tool'
        self.credentials = None
        self.service = None
        self._initialize_credentials()

    def _initialize_credentials(self):
        """Initialize credentials from storage."""
        try:
            credential_path = os.path.join("./", 'drive-python-quickstart.json')
            store = Storage(credential_path)
            credentials = store.get()
            
            if not credentials or credentials.invalid:
                if os.path.exists(self.CLIENT_SECRET_FILE):
                    flow = client.flow_from_clientsecrets(self.CLIENT_SECRET_FILE, self.SCOPES)
                    flow.user_agent = self.APPLICATION_NAME
                    credentials = tools.run(flow, store)
                else:
                    raise FileNotFoundError(f"Client secret file not found: {self.CLIENT_SECRET_FILE}")
            
            self.credentials = credentials
        except Exception as e:
            print(f"Warning: Could not initialize credentials: {e}")
            self.credentials = None

    def run(self, file):
        """Process image file through Google Drive OCR.
        
        Args:
            file (str): Base filename (without extension)
        """
        if not self.credentials:
            raise RuntimeError("Credentials not initialized. Cannot process image.")
        
        try:
            http = self.credentials.authorize(httplib2.Http())
            service = discovery.build('drive', 'v3', http=http)
            img_file = file + '.png'
            txt_file = file + '.txt'

            mime = 'application/vnd.google-apps.document'
            res = service.files().create(
                body={
                    'name': img_file,
                    'mimeType': mime
                },
                media_body=MediaFileUpload(img_file, mimetype=mime, resumable=True)
            ).execute()
            
            downloader = MediaIoBaseDownload(
                io.FileIO(txt_file, 'wb'),
                service.files().export_media(
                    fileId=res['id'], mimeType="text/plain")
            )
            done = False
            while done is False:
                _, done = downloader.next_chunk()

            service.files().delete(fileId=res['id']).execute()
            service.close()
        except Exception as e:
            raise Exception(f"OCR processing error: {str(e)}")
