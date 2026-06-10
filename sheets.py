import os
import json
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from dotenv import load_dotenv
import io

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

class GoogleSheetsClient:
    def __init__(self):
        load_dotenv()

        credentials_path = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
        sheet_id = os.getenv("GOOGLE_SHEET_ID")

        creds = Credentials.from_service_account_file(credentials_path, scopes=SCOPES)

        # Connexion Google Sheets
        client = gspread.authorize(creds)
        self.sheet = client.open_by_key(sheet_id).worksheet("note_de_frais")

        # Connexion Google Drive
        self.drive = build("drive", "v3", credentials=creds)

    def upload_image(self, image_bytes: bytes, filename: str, media_type: str) -> str:
        file_metadata = {"name": filename}
        media = MediaIoBaseUpload(io.BytesIO(image_bytes), mimetype=media_type)

        file = self.drive.files().create(
            body=file_metadata,
            media_body=media,
            fields="id"
        ).execute()

        file_id = file.get("id")

        # Rendre le fichier public en lecture
        self.drive.permissions().create(
            fileId=file_id,
            body={"type": "anyone", "role": "reader"}
        ).execute()

        return f"https://drive.google.com/uc?id={file_id}"

    def append_expense(self, data: dict, image_url: str = None) -> None:
        row = [
            data.get("Horodatage"),
            data.get("Type"),
            data.get("Fournisseur"),
            data.get("Date"),
            data.get("Montant TTC ($)"),
            data.get("TVA ($)"),
            data.get("Devise"),
            data.get("Description"),
            data.get("Confiance"),
            f'=IMAGE("{image_url}")' if image_url else None
        ]

        self.sheet.append_row(row)

if __name__ == "__main__":
    client = GoogleSheetsClient()

    fake_data = {
        "Horodatage": "2024-01-15T12:30:00",
        "Type": "restaurant",
        "Fournisseur": "Bistrouille, le bistrot des ratatouilles",
        "Date": "2024-01-15",
        "Montant TTC ($)": 24.50,
        "TVA ($)": 2.45,
        "Devise": "USD",
        "Description": "Déjeuner test",
        "Confiance": "haute",
        "Image": None
    }

    client.append_expense(fake_data, image_url=None)
    print("Ligne ok")