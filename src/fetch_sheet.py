import os.path

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

  if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)

  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          CREDENTIALS_PATH, SCOPES
      )
      creds = flow.run_local_server(port=0)

    with open(TOKEN_PATH, "w") as token:
      token.write(creds.to_json())

  try:
    service = build("sheets", "v4", credentials=creds)

    sheet = service.spreadsheets()
    result = (
        sheet.values()
        .get(spreadsheetId=SAMPLE_SPREADSHEET_ID, range=SAMPLE_RANGE_NAME)
        .execute()
    )
    values = result.get("values", [])
            
    if not values:
      print("No data found.")
      return
  
    def print_claims_table(claims):
        col_widths = [max(len(str(item)) for item in col) for col in zip(*claims)]
        
        for row in claims:
            print(" | ".join(str(item).ljust(width) for item, width in zip(row, col_widths)))
            
    print_claims_table(values)
    
  except HttpError as err:
    print(err)
    
    
    
if __name__ == "__main__":
    fetch_sheet()