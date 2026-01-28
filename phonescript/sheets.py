import os
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import json
import csv 
import io

# --- SCOPES ---
SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/spreadsheets.readonly"
]

# --- File paths ---
TOKEN_FILE = "token.json"
CREDENTIALS_FILE = "credentials.json"
SHEETS_FILE = "files.json"

def add_local_sheet(file_id, sheet_name):

    """Add a sheet to the local sheets file."""
    sheets = {}
    if os.path.exists(SHEETS_FILE):
        with open(SHEETS_FILE, "r") as f:
            sheets = json.load(f)
    else:
        print(f"No sheets file found at {SHEETS_FILE}")
        return False

    sheets[sheet_name] = file_id

    with open(SHEETS_FILE, "w") as f:
        json.dump(sheets, f, indent=4)

    print(f"Added sheet '{sheet_name}' with ID {file_id} to {SHEETS_FILE}")
    return True

def delete_local_sheet(sheet_name):
    """Delete a sheet from the local sheets file."""
    if os.path.exists(SHEETS_FILE):
        with open(SHEETS_FILE, "r") as f:
            sheets = json.load(f)
    else:
        print(f"No sheets file found at {SHEETS_FILE}")
        return False

    if sheet_name in sheets:
        del sheets[sheet_name]
        with open(SHEETS_FILE, "w") as f:
            json.dump(sheets, f, indent=4)
        print(f"Deleted sheet '{sheet_name}' from {SHEETS_FILE}")
        return True
    else:
        print(f"Sheet '{sheet_name}' not found in {SHEETS_FILE}")
        return False

def get_local_sheets():
    """Retrieve the local sheets file."""

    if os.path.exists(SHEETS_FILE):
        with open(SHEETS_FILE, "r") as f:
            sheets = json.load(f)
        return sheets["files"]
    else:
        print(f"No sheets file found at {SHEETS_FILE}")
        return []

# --- Authenticate user ---
def authenticate():
    """Authenticate the user and return credentials. Reuse existing token if valid."""

    creds = None

    # Try to load existing token
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        if creds and creds.valid:
            return creds  # Use existing valid token

    # If no token or invalid, run OAuth flow
    flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
    creds = flow.run_local_server(port=0)

    # Save token for future runs
    with open(TOKEN_FILE, "w") as token_file:
        token_file.write(creds.to_json())

    print("Authentication successful. Token saved. Credentials:", creds)
    return creds

# --- List all spreadsheets ---
def list_spreadsheets(creds):
    drive = build("drive", "v3", credentials=creds)
    results = drive.files().list(
        q="mimeType='application/vnd.google-apps.spreadsheet'",
        fields="files(id, name)",
        pageSize=100
    ).execute()

    files = results.get("files", [])
    if not files:
        print("No spreadsheets found.")
        return []
    
    files_dict = {}

    for file in files:
        files_dict[file["name"]] = file["id"]

    print("\nSpreadsheets:\n")
    for i, f in enumerate(files, 1):
        print(f"{i}. {f['name']}  ({f['id']})")

    return files_dict

# --- Download a spreadsheet as CSV ---

# --- Download a spreadsheet as CSV and return string ---
def download_sheet_as_csv(creds, file_id, output_file="sheet.csv"):
    drive = build("drive", "v3", credentials=creds)
    request = drive.files().export(
        fileId=file_id,
        mimeType="text/csv"
    )
    csv_bytes = request.execute()          # bytes
    csv_text = csv_bytes.decode("utf-8")  # convert to string

    # save to file (optional)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(csv_text)

    print(f"\nDownloaded spreadsheet as {output_file}")

    return csv_text


def filter_csv(input_csv, filters):
    """
    Filter CSV rows based on multiple columns with comma-separated values.

    Args:
        input_csv (str): CSV content as a string.
        filters (dict): Dictionary of {column_name: allowed_values}.
                        allowed_values can be a list or set.
                        Each column is checked for at least one match in its CSV cell.

    Returns:
        str: Filtered CSV as a string.
    """
    
    input_io = io.StringIO(input_csv)
    output_io = io.StringIO()
    
    reader = csv.DictReader(input_io)
    writer = csv.DictWriter(output_io, fieldnames=reader.fieldnames)
    writer.writeheader()
    
    print(f"Applying filters: {filters}")

    for row in reader:
        keep = False
        print(f"Evaluating row: {row}")
        for col, allowed_values in filters.items():
            # Ensure allowed_values is iterable
            print(f"Filtering on column '{col}' with allowed values: {allowed_values}")
            allowed_values = set(allowed_values)  # convert list or set to set for fast lookup
            
            # Split by commas, strip whitespace
            values = [v.strip().lower() for v in row[col].split(',') if v.strip()]
            print(f"Row values for column '{col}': {values}")
            print(f"Allowed values for column '{col}': {allowed_values}")
            
            for v in values:
                if v in allowed_values:
                    print(f"Match found: '{v}' is in allowed values for column '{col}'")
                    keep = True
                    break
        if keep:
            writer.writerow(row)
    
    return output_io.getvalue()


# --- Main program ---
if __name__ == "__main__":
    creds = authenticate()
    files = list_spreadsheets(creds)
    if not files:
        exit()

    # Ask user which sheet to download
    choice = input("\nEnter the number of the spreadsheet to download as CSV: ")
    try:
        choice = int(choice)
        if 1 <= choice <= len(files):
            file_id = files[choice - 1]["id"]
            download_sheet_as_csv(creds, file_id)
        else:
            print("Invalid number.")
    except ValueError:
        print("Invalid input. Must be a number.")
