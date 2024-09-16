import os
import io
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
import yaml
from telegram.ext import CallbackContext

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseUpload
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

load_dotenv()
SAMPLE_SPREADSHEET_ID = os.environ["SAMPLE_SPREADSHEET_ID"]
CLAIM_RECEIPT_FOLDER_ID = os.environ["CLAIM_RECEIPT_FOLDER_ID"]
PAYMENT_PROOF_FOLDER_ID = os.environ["PAYMENT_PROOF_FOLDER_ID"]


# Load in config file
def load_config(config_path):
    with open(config_path, "r") as file:
        config = yaml.safe_load(file)
    return config


# Load the config
config = load_config(config_path="config.yaml")

SHEETS_SCOPES = config["sheets"]["scopes"]
G_DRIVE_SCOPES = config["drive"]["scopes"]
SAMPLE_RANGE_NAME = config["sheets"]["range_name"]
CREDENTIALS_PATH = config["credentials"]["path"]
SHEET_TOKEN_PATH = config["sheets"]["token_path"]
DRIVE_TOKEN_PATH = config["drive"]["token_path"]


def fetch_sheet():
    """
    Fetches data from the excel sheet and stores returns it as a pandas dataframe
    """

    creds = None

    # Check if token.json exists and load it if it does
    # Need better error handling for this
    if os.path.exists(SHEET_TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(SHEET_TOKEN_PATH, SHEETS_SCOPES)

    # If no valid credentials are available, log in again
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())  # refresh the token if it’s expired
        else:
            # log in and get new credentials
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_PATH, SHEETS_SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Save the credentials for future runs
        with open(SHEET_TOKEN_PATH, "w") as token:
            token.write(creds.to_json())

    try:
        # Call the Sheets API
        service = build("sheets", "v4", credentials=creds)
        sheet = service.spreadsheets()
        result = (
            sheet.values()
            .get(spreadsheetId=SAMPLE_SPREADSHEET_ID, range=SAMPLE_RANGE_NAME)
            .execute()
        )
        # retrieve the sheet data
        sheet = result.get("values", [])
        # check if there's data in the sheet
        if not sheet:
            return "No data found in the Google Sheet."

        # Here the sheet is a pandas dataframe
        df = pd.DataFrame(sheet[1:], columns=sheet[0])
        return df

    except HttpError as err:
        return f"An error occurred: {err}"


def get_claim_status(df, id):
    id = id.strip()
    try:
        status_msg = df[df["Claim ID"] == id]["Approval Status"].values[0]
    except IndexError:
        return {"error": True, "status_msg": id}

    return {"error": False, "status_msg": status_msg}


def send_claim_receipt_to_cloud(receipt_path: str, photo_file) -> str:
    """Uploads the receipt to a pre-defined folder in Google Drive and returns the file ID."""

    creds = None

    if os.path.exists(DRIVE_TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(DRIVE_TOKEN_PATH, G_DRIVE_SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())  # refresh the token if it’s expired
        else:
            # Log in and get new credentials
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_PATH, G_DRIVE_SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open(DRIVE_TOKEN_PATH, "w") as token:
            token.write(creds.to_json())

    # calling the google drive API
    service = build("drive", "v3", credentials=creds)

    # Validate the MIME type to ensure it's a JPG
    if photo_file.file_path.endswith(".jpg") or photo_file.file_path.endswith(".jpeg"):
        # Use a unique file name for the receipt using the UUID
        image_uuid = receipt_path
        file_metadata = {
            "name": f"{image_uuid}.jpg",
            "parents": [CLAIM_RECEIPT_FOLDER_ID],
        }

        # store media bytes
        receipt_stream = io.BytesIO(photo_file.download_as_bytearray())
        media = MediaIoBaseUpload(receipt_stream, mimetype="image/jpeg")

        # Upload the file to Google Drive inside the folder with FOLDER_ID
        file = (
            service.files()
            .create(body=file_metadata, media_body=media, fields="id")
            .execute()
        )
        return

    else:
        raise ValueError("File type is not JPG")


def send_payment_proof_to_cloud(receipt_path: str, photo_file) -> str:
    """Uploads the receipt to a pre-defined folder in Google Drive and returns the file ID."""

    creds = None

    if os.path.exists(DRIVE_TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(DRIVE_TOKEN_PATH, G_DRIVE_SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())  # refresh the token if it’s expired
        else:
            # Log in and get new credentials
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_PATH, G_DRIVE_SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open(DRIVE_TOKEN_PATH, "w") as token:
            token.write(creds.to_json())

    # calling the google drive API
    service = build("drive", "v3", credentials=creds)

    # Validate the MIME type to ensure it's a JPG
    if photo_file.file_path.endswith(".jpg") or photo_file.file_path.endswith(".jpeg"):
        # Use a unique file name for the receipt using the UUID
        image_uuid = receipt_path
        file_metadata = {
            "name": f"{image_uuid}.jpg",
            "parents": [PAYMENT_PROOF_FOLDER_ID],
        }

        # store media bytes
        receipt_stream = io.BytesIO(photo_file.download_as_bytearray())
        media = MediaIoBaseUpload(receipt_stream, mimetype="image/jpeg")

        # Upload the file to Google Drive inside the folder with FOLDER_ID
        file = (
            service.files()
            .create(body=file_metadata, media_body=media, fields="id")
            .execute()
        )
        return

    else:
        raise ValueError("File type is not JPG")


def current_datetime():
    return datetime.now().strftime("%Y-%m-%d")


def export_claim_details(context: CallbackContext):
    """
    Appends a new claim to the Google Sheet.
    """
    new_row = [
        context.user_data.get("receipt_uuid", "").capitalize(),
        context.user_data.get("department", "").capitalize(),
        context.user_data.get("name", "").capitalize(),
        current_datetime(),
        context.user_data.get("category", "").capitalize(),
        context.user_data.get("amount", "").capitalize(),
        context.user_data.get("description", "").capitalize(),
        "Pending",
        "Yes",
    ]

    creds = None

    if os.path.exists(SHEET_TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(SHEET_TOKEN_PATH, SHEETS_SCOPES)

    # If no valid credentials are available, log in again
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())  # refresh the token if it’s expired
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_PATH, SHEETS_SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open(SHEET_TOKEN_PATH, "w") as token:
            token.write(creds.to_json())

    try:
        # Call the oogle sheets API
        service = build("sheets", "v4", credentials=creds)
        sheet = service.spreadsheets()

        # appending the new row
        request = sheet.values().append(
            spreadsheetId=SAMPLE_SPREADSHEET_ID,
            range=SAMPLE_RANGE_NAME,
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body={"values": [new_row]},
        )
        response = request.execute()

        print(f"Claim successfully appended to Sheet ID {response['spreadsheetId']}")

    except HttpError as err:
        print(f"An error occurred: {err}")
        return


if __name__ == "__main__":
    fetch_sheet()
