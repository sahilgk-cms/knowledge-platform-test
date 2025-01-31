from googleapiclient.discovery import build
from google.oauth2 import service_account

SCOPES = ["https://www.googleapis.com/auth/drive"]
SERVICE_ACCOUNT_FILE = "knowledge-test-449405-c95ab587a67e.json"

credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes = SCOPES)
drive_service = build("drive", "v3", credentials = credentials)

DOCUMENTS_FOLDER = "1IWTJYPenJ-JSrjnxTaA-p8-6pkrkjifU"
IMAGES_FOLDER = "1KZedpRQVC9oZNdv_8ZNyAn_ZrUvveZFM"


def get_file_id_from_parent_folder(parent_folder: str, file_name: str):
    query = f"'{parent_folder}' in parents and name = '{file_name}' and trashed = False"
    results = drive_service.files().list(q = query, fields = "files(id, name)").execute()
    files = results.get("files", [])

    if not files:
        return None
    
    file_id = files[0]["id"]
    return file_id


def display_image_from_file_id(file_id):
    return f"https://lh3.googleusercontent.com/d/{file_id}=s500"

def download_file_from_file_id(file_id):
    return f"https://drive.google.com/uc?export=download&id={file_id}"