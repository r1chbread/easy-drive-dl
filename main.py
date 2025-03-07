import os
import sys
import json
import time
import io
import logging
from tqdm import tqdm
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler("download.log", encoding="utf-8"),  # Log to a file
        logging.StreamHandler()  # Log to console
    ],
)

def exception_handler(exc_type, exc_value, exc_traceback):
    logging.error(exc_value)
    input("Press Enter to exit.")
    sys.exit(1)

sys.excepthook = exception_handler

# Paths to config files
SERVICE_ACCOUNT_FILE: str = "./service-account.json"
CONFIG_FILE: str = "./config.json"

for fp in [SERVICE_ACCOUNT_FILE, CONFIG_FILE]:
    if not os.path.exists(fp):
        raise FileNotFoundError(f"File not found: {fp}")

# Load config JSON
with open(CONFIG_FILE, encoding="utf-8") as f:
    config: dict = json.load(f)

FOLDER_IDS: list[str] = config["folder_ids"]
ALLOWED_EXTENSIONS: list[str] = config["allowed_extensions"]
LOOP_INTERVAL: int = config.get("loop_interval", 60)  # Default to 60 seconds if not set

# Download directory
DOWNLOAD_PATH: str = "./downloads"
os.makedirs(DOWNLOAD_PATH, exist_ok=True)

# Authenticate with service account credentials
def authenticate() -> object:
    scopes: list[str] = ["https://www.googleapis.com/auth/drive"]
    credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scopes)
    service = build("drive", "v3", credentials=credentials)
    return service

# Check if the folder ID is valid
def is_valid_folder(service, folder_id: str) -> bool:
    try:
        # Try to fetch folder metadata by ID
        folder = service.files().get(fileId=folder_id).execute()
        if folder.get('mimeType') == 'application/vnd.google-apps.folder':
            return True
        else:
            return False
    except HttpError as error:
        return False

# Get list of files in a Google Drive folder
def list_files(service, folder_id: str):
    if not is_valid_folder(service, folder_id):
        raise RuntimeError(f"Invalid folder ID: {folder_id}.")

    query = f"'{folder_id}' in parents and trashed=false"
    try:
        results = service.files().list(q=query, fields="files(id, name, mimeType, size)").execute()
        files = results.get("files", [])

        # Filter files based on allowed extensions
        filtered_files = [
            file for file in files if any(file['name'].endswith(ext) for ext in ALLOWED_EXTENSIONS)
        ]
        
        # Log the filtering results
        if len(filtered_files) < len(files):
            skipped_files = [file['name'] for file in files if not any(file['name'].endswith(ext) for ext in ALLOWED_EXTENSIONS)]
            logging.info(f"Skipping files with unsupported extensions: {', '.join(skipped_files)}")

        return filtered_files
    except HttpError as error:
        logging.error(f"An error occurred while listing files: {error}")
        return []

# Download a file from Google Drive with progress bar
def download_file(service: object, file_id: str, file_name: str) -> None:
    file_path: str = os.path.join(DOWNLOAD_PATH, file_name)

    if os.path.exists(file_path):
        logging.info(f"Skipping {file_name} (already downloaded).")
        return

    request = service.files().get_media(fileId=file_id)
    fh = io.FileIO(file_path, "wb")
    downloader = MediaIoBaseDownload(fh, request)
    
    logging.info(f"Downloading: {file_name}")

    with tqdm(total=100, unit="%", ncols=80, desc=file_name, ascii=True) as pbar:
        done = False
        while not done:
            status, done = downloader.next_chunk()
            pbar.update(int(status.progress() * 100) - pbar.n)  # Update progress bar

    logging.info(f"Download complete: {file_name}")

# Main function to check and download files in a loop
def main() -> None:
    service = authenticate()

    while True:
        for folder_id in FOLDER_IDS:
            files = list_files(service, folder_id)
            if not files:
                logging.info("No new files found.")

            for file in files:
                download_file(service, file["id"], file["name"])

        logging.info(f"Waiting for {LOOP_INTERVAL} seconds before next check...")
        time.sleep(LOOP_INTERVAL)

if __name__ == "__main__":
    main()
