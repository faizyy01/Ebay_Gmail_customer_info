from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import base64
import email
from apiclient import errors
import re
import csv
# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
import time
from progress.bar import Bar

label = ''

def getemail(msg_str,reg):
    #regex =  [r"(mailto:).*\"\>",r"[/>][$]\d*.\d*[/<]"]
    #reg = r"(mailto:).*\"\>"
    matches = re.finditer(reg, msg_str, re.MULTILINE)
    #print(str(mime))
    for matchNum, match in enumerate(matches, start=1):
        emailfr = str(match.group().replace('"',''))
        #emailfr = str(match.group().replace("mailto:",""))
        emailfr = emailfr.replace("mailto:","")
        emailfr = emailfr.replace(" ","")
        emailfr = emailfr.replace("<","")
        emailfr = emailfr.replace(">","")
        emailfr = emailfr.replace("(","")
        emailfr = emailfr.replace(")","")
        emailfr = emailfr.replace("$","")
        #print ("{match}".format(match = match.group()))
        return(emailfr)


def data_encoder(text):
    if len(text)>0:
        message = base64.urlsafe_b64decode(text)
        message = str(message, 'utf-8')
        message = email.message_from_string(message)
    return message

def readMessage(content)->str:
    message = None
    if "data" in content['payload']['body']:
        message = content['payload']['body']['data']
        message = data_encoder(message)
    elif "data" in content['payload']['parts'][0]['body']:
        message = content['payload']['parts'][0]['body']['data']
        message = data_encoder(message)
    else:
        print("body has no data.")
    return message

def main():
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
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
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('gmail', 'v1', credentials=creds)


    # Call the Gmail API
    results = service.users().labels().list(userId='me').execute()
    labels = results.get('labels', [])
    bigboys = []
    smallboys = []
    smallboys.append(['email','amount'])


    resultsemail = service.users().messages().list(userId='me',labelIds = [label]).execute()
    messages = resultsemail.get('messages', [])

    while 'nextPageToken' in resultsemail:
        page_token = resultsemail['nextPageToken']
        resultsemail = service.users().messages().list(userId='me',labelIds = [label], pageToken=page_token).execute()
        messages.extend(resultsemail['messages'])

    totalcount = len(messages)
    bar = Bar('Processing', max = totalcount)
    for message in messages:
            bar.next()
            time.sleep(1)
            messagebody = service.users().messages().get(userId='me', id=message['id'], format='full').execute()
            msg_str = str(readMessage(messagebody))
            regex =  [r"[/(](mailto:)( ).*[/)]",r"[$]\d*.\d*"]
            smallboys.append([getemail(msg_str, regex[0]),getemail(msg_str, regex[1])])
    bar.finish()

    with open('customers', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(smallboys)

if __name__ == '__main__':
    main()
