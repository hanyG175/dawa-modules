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
        self.client_secret_file = str(Path(__file__).parents[3] / 'credentials' / CLIENT_SECRET_FILE)
        self.credential_path = str(Path(__file__).parents[3] / 'credentials' / 'drive-python-quickstart.json')

        store = Storage(self.credential_path)
        credentials = store.get()
        if not credentials or credentials.invalid:
            flow = client.flow_from_clientsecrets(self.client_secret_file, self.scopes)
            flow.user_agent = self.application_name
            credentials = tools.run_flow(flow, store)

        self.credentials = credentials

    def _reauthenticate(self):
        """Force interactive OAuth flow and overwrite old token file."""
        print('Stored token is invalid/outdated. Re-authenticating...')
        store = Storage(self.credential_path)
        flow = client.flow_from_clientsecrets(self.client_secret_file, self.scopes)
        flow.user_agent = self.application_name
        credentials = tools.run_flow(flow, store)
        self.credentials = credentials
        return credentials

    def run(self, file):
        # Accept both base name (old behavior) and full file path.
        if os.path.exists(file):
            img_file = file
            txt_file = str(Path(file).with_suffix('.txt'))
        else:
            img_file = file + '.png'
            txt_file = file + '.txt'

        def _execute_ocr_once():
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


if __name__ == '__main__':
    print('Google OCR - direct run mode')

    selected_file = ''

    # Try file picker first (no command needed)
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        selected_file = filedialog.askopenfilename(
            title='Select an image file',
            filetypes=[
                ('Images', '*.png *.jpg *.jpeg *.bmp *.tiff *.tif'),
                ('All files', '*.*')
            ]
        )
        root.destroy()
    except Exception:
        selected_file = ''

    # Fallback to manual path input
    if not selected_file:
        selected_file = input('Enter image path: ').strip().strip('"')

    if not selected_file:
        print('No file selected. Exit.')
        raise SystemExit(0)

    if not os.path.exists(selected_file):
        print(f'File not found: {selected_file}')
        raise SystemExit(1)

    try:
        ocr = GoogleOCR()
        output_file = ocr.run(selected_file)
        print(f'OCR done. Output: {output_file}')
    except Exception as e:
        print(f'OCR failed: {e}')
        raise SystemExit(1)

