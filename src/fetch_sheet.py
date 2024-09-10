import os.path
import sys
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

SAMPLE_SPREADSHEET_ID = "1gNMdlnevrfawztpJdujWn54WxohZB9pLD5KG5EapImM"
SAMPLE_RANGE_NAME = 'Sheet1!A1:D10' 
CREDENTIALS_PATH = "../credentials.json"
TOKEN_PATH = "../token.json"

def fetch_sheet():
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
        values = result.get("values", [])
        
        # Check if there's data in the sheet
        if not values:
            print("No data found.")
            return

        # Function to print the claims table with properly formatted columns
        def print_claims_table(claims):
            col_widths = [max(len(str(item)) for item in col) for col in zip(*claims)]
            for row in claims:
                print(" | ".join(str(item).ljust(width) for item, width in zip(row, col_widths)))

        # Print the fetched data
        print_claims_table(values)

    except HttpError as err:
        print(err)
    
    
    
if __name__ == "__main__":
    while True:
        answer = input("re query?: ")
        if answer == "y" or answer=="yes":
            fetch_sheet()
        else:
            sys.exit()