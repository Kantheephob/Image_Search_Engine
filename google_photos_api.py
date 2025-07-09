import os
import pickle
import requests
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/photoslibrary.readonly']

def get_google_photos_service():
    """Authenticate and return the Google Photos service."""
    creds = None
    
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
            
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'config/credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
            
    return build('photoslibrary', 'v1', credentials=creds, static_discovery=False)

def get_media_items(service, page_size=100):
    """Fetch media items from Google Photos."""
    media_items = []
    response = service.mediaItems().list(pageSize=page_size).execute()
    items = response.get('mediaItems', [])
    media_items.extend(items)
    
    # Handle pagination
    while 'nextPageToken' in response:
        next_page_token = response['nextPageToken']
        response = service.mediaItems().list(
            pageSize=page_size, pageToken=next_page_token
        ).execute()
        items = response.get('mediaItems', [])
        media_items.extend(items)
        if not items: # Break if no more items are returned
            break
    return media_items

def download_image(base_url, filename, output_dir="img_dataset"):
    """Download an image from a given base URL."""
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, filename)
    # Append a size parameter to the base URL for better efficiency
    # For example, download with a max width of 2048px
    download_url = f"{base_url}=w2048-h2048"
    try:
        response = requests.get(download_url, stream=True)
        response.raise_for_status()  # Raise an error for bad responses
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Downloaded: {filename}")
        return file_path
    except requests.exceptions.RequestsDependencyWarning as e:
        print(f"Error downloading {filename}: {e}")
        return None