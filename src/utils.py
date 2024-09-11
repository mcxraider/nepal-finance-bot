import os.path
import pandas as pd
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

SAMPLE_SPREADSHEET_ID = "1gNMdlnevrfawztpJdujWn54WxohZB9pLD5KG5EapImM"
SAMPLE_RANGE_NAME = 'Sheet1!A1:M10' 
CREDENTIALS_PATH = "../credentials.json"
TOKEN_PATH = "../token.json"


def fetch_sheet():
    '''
    Fetches data from the excel sheet and stores returns it as a pandas dataframe
    '''
    
    creds = None

    # Check if token.json exists and load it if it does
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    # If no valid credentials are available, log in again
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())  # Refresh the token if it’s expired
        else:
            # Log in and get new credentials
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for future runs
        with open(TOKEN_PATH, "w") as token:
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
        
        # Check if there's data in the sheet
        if not sheet:
            return "No data found in the Google Sheet."

        # Here the sheet is a pandas dataframe
        df = pd.DataFrame(sheet[1:], columns=sheet[0])
        
        return df

    except HttpError as err:
        return f"An error occurred: {err}"


def get_claim_status(df, id):
    try:
        status_msg = df[df["Claim ID"] == id]["Approval Status"].values[0]
    except IndexError:
        return {"error": True, "status_msg": id}
    
    return {"error": False, "status_msg": status_msg}


def send_to_sheet(department, name, category, amount)


if __name__ == "__main__":
    fetch_sheet()