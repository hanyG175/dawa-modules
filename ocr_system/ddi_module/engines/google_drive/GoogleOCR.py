from googleapiclient import discovery
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
from oauth2client import client, tools
from oauth2client.file import Storage
import os
import httplib2
import io
from pathlib import Path


class GoogleOCR:
    def __init__(self):
        SCOPES = 'https://www.googleapis.com/auth/drive'
        CLIENT_SECRET_FILE = 'client_secret_791442723837-7ch74jh2dpavoios3ko118ennk03o51i.apps.googleusercontent.com.json'
        APPLICATION_NAME = 'Drive API Python Quickstart'

        self.scopes = SCOPES
        self.application_name = APPLICATION_NAME
        self.client_secret_file = str(Path(__file__).resolve().parents[2] / 'credentials' / CLIENT_SECRET_FILE)
        self.credential_path = str(Path(__file__).resolve().parents[2] / 'credentials' / 'drive-python-quickstart.json')

        # Optional mock mode for UI/testing when Drive credentials are not available.
        mock_flag = os.environ.get('GOOGLE_OCR_MOCK', '').lower()
        self.mock = mock_flag in ('1', 'true', 'yes')
        if self.mock:
            print('GoogleOCR: running in MOCK mode (GOOGLE_OCR_MOCK enabled). No Drive credentials required.')
            self.credentials = None
            return

        # Ensure client secret file exists and provide a helpful error if missing.
        if not os.path.exists(self.client_secret_file):
            raise FileNotFoundError(
                "Google OCR credentials not found. Expected client secret at: {}\n"
                "Place the OAuth client JSON in the 'credentials' folder or set 'GOOGLE_OCR_MOCK=1' to run without Drive auth."
                .format(self.client_secret_file)
            )

        store = Storage(self.credential_path)
        credentials = store.get()
        if not credentials or credentials.invalid:
            flow = client.flow_from_clientsecrets(self.client_secret_file, self.scopes)
            flow.user_agent = self.application_name
            credentials = tools.run_flow(flow, store)

        self.credentials = credentials

    def _reauthenticate(self):
        print('Stored token is invalid/outdated. Re-authenticating...')
        store = Storage(self.credential_path)
        flow = client.flow_from_clientsecrets(self.client_secret_file, self.scopes)
        flow.user_agent = self.application_name
        credentials = tools.run_flow(flow, store)
        self.credentials = credentials
        return credentials

    def run(self, file):
        if os.path.exists(file):
            img_file = file
            txt_file = str(Path(file).with_suffix('.txt'))
        else:
            img_file = file + '.png'
            txt_file = file + '.txt'

        def _execute_ocr_once():
            if self.mock:
                # Create a placeholder text file so callers can continue.
                placeholder = 'MOCK OCR: credentials missing or mock mode enabled.'
                with open(txt_file, 'w', encoding='utf-8') as fh:
                    fh.write(placeholder)
                return

            http = self.credentials.authorize(httplib2.Http())
            service = discovery.build('drive', 'v3', http=http)

            mime = 'application/vnd.google-apps.document'
            res = service.files().create(
                body={
                    'name': Path(img_file).name,
                    'mimeType': mime
                },
                media_body=MediaFileUpload(img_file, resumable=True)
            ).execute()
            
            with io.FileIO(txt_file, 'wb') as fh:
                downloader = MediaIoBaseDownload(
                    fh,
                    service.files().export_media(
                        fileId=res['id'], mimeType="text/plain")
                )
                done = False
                while done is False:
                    _, done = downloader.next_chunk()

            service.files().delete(fileId=res['id']).execute()
            service.close()

        try:
            _execute_ocr_once()
        except Exception as e:
            if 'invalid_grant' in str(e).lower():
                self._reauthenticate()
                _execute_ocr_once()
            else:
                raise
        
        return txt_file
