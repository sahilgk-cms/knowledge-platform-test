from googleapiclient.discovery import build
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
from googleapiclient.http import HttpRequest
import os
import json
from dotenv import load_dotenv
import streamlit as st
import httplib2
load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/drive"]


#### Retrieving credentials from local
# credentials_path = os.getenv("GOOGLE_DRIVE_CREDENTIALS_PATH")
# if credentials_path is None or not os.path.exists(credentials_path):
#     raise ValueError("Google Drive credentials file is missing or incorrect")
# with open(credentials_path, "r") as file:
#     credentials_dict = json.load(file)

#### Retrieveing credentials from Github
# SERVICE_ACCOUNT_INFO = os.getenv("GOOGLE_DRIVE_CREDENTIALS")

#### Retrieving credentials from Streamlit Cloud
SERVICE_ACCOUNT_INFO = st.secrets["google"]["GOOGLE_DRIVE_CREDENTIALS"]

if SERVICE_ACCOUNT_INFO is None:
    raise ValueError("Missing GOOGLE_DRIVE_CREDENTIALS environment variable!")
credentials_dict = json.loads(SERVICE_ACCOUNT_INFO)

#########################################################################################################

try:
    credentials = service_account.Credentials.from_service_account_info(credentials_dict, scopes = SCOPES)
    if credentials.expired or not credentials.valid:
        credentials.refresh(Request())
except RefreshError as e:
    st.error(f"Failed to refresh credentials: {e}")    
    



drive_service = build("drive", "v3", credentials = credentials)

DOCUMENTS_FOLDER = "1IWTJYPenJ-JSrjnxTaA-p8-6pkrkjifU"
IMAGES_FOLDER = "1KZedpRQVC9oZNdv_8ZNyAn_ZrUvveZFM"


def get_file_id_from_parent_folder(parent_folder: str, file_name: str) -> str:
    '''
    This function gets the file id of the given file present in the parent folder
    Args:
        parent folder, file name
    Returns:
        file id
    '''
    query = f"'{parent_folder}' in parents and name = '{file_name}' and trashed = False"
    results = drive_service.files().list(q = query, fields = "files(id, name)").execute()
    files = results.get("files", [])

    if not files:
        return None
    
    file_id = files[0]["id"]
    return file_id


def display_image_from_file_id(file_id: str) -> str:
    '''
    This function converts the image_file_id into image for display purpose
    Args:
        image_file_id
    Returns:
        image_url for display purpose
    '''
    return f"https://lh3.googleusercontent.com/d/{file_id}=s500"

def download_file_from_file_id(file_id: str) -> str:
    '''
    This function converts the file_id into image for download purpose
    Args:
        file_id
    Returns:
        file_url for download purpose
    '''
    return f"https://drive.google.com/uc?export=download&id={file_id}"
