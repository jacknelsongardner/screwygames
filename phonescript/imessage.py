
import time
import csv
import subprocess
import time
import io

def personalize(col, message):
    for key in col.keys():
        placeholder = f"${key.upper().replace(' ', '_')}"
        if placeholder in message:
            message = message.replace(placeholder, col[key])
    safe_message = message.replace('"', '\\"')
    return safe_message


def send_messages(message, contacts_file=None):
    print(contacts_file)
    print(message)
    
    if contacts_file is None:
        print("No contacts file provided.")
        return False

    try:
        # Wrap string in StringIO if it's a raw string
        if isinstance(contacts_file, str):
            contacts_file = io.StringIO(contacts_file)

        # Read CSV
        contacts_dict = list(csv.DictReader(contacts_file))
        print(f"Message to send: {message}")
        print(f"Total contacts: {len(contacts_dict)}")

        for c in contacts_dict:
            print(f"Contact: {c}")

            # Make sure the phone column exists
            phone_field = 'phone' if 'phone' in c else 'phone number'

            # Assuming personalize is defined elsewhere
            personalized = personalize(c, message)

            applescript = f'''
            tell application "Messages"
                set targetService to 1st service whose service type = iMessage
                set theBuddy to buddy "{c[phone_field]}" of targetService
                send "{personalized}" to theBuddy
            end tell
            '''

            print(f"Sending to {c['name']} at {c[phone_field]}: {personalized}")
            subprocess.run(["osascript", "-e", applescript])
            time.sleep(2)  # anti-spam delay

        return True

    except Exception as e:
        print(f"Error sending messages: {e}")
        return False
