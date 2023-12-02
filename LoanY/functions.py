import json
import requests
import os
import openai
import toml
from openai import OpenAI
from prompts import assistant_instructions
import streamlit as st

# GMAIL API
import base64
from email.message import EmailMessage
import google.auth
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
import os
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


# Load configuration from config.toml
config = toml.load('/Users/cameronhightower/Documents/LoanY/.streamlit/config.toml')

# Set the OpenAI and GMAIL API keys from the config file
openai.api_key = config['openai']['api_key']
OPENAI_API_KEY = openai.api_key
GMAIL_API_KEY = config['gmail']['api_key']



# Init OpenAI Client
if 'client' not in st.session_state:
    st.session_state.client = OpenAI(api_key = OPENAI_API_KEY)


SCOPES = ["https://www.googleapis.com/auth/gmail.compose"]

# Send a summary email to the human loan officer
def gmail_send_message(client_name, summary):
  """Create and send an email message
  Print the returned  message id
  Returns: Message object, including message id
  """
  creds = None
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.

  if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          "credentials.json", SCOPES
      )
      creds = flow.run_local_server(port=0)
    with open("token.json", "w") as token:
      token.write(creds.to_json())

  try:
    service = build("gmail", "v1", credentials=creds)
    message = EmailMessage()

    message.set_content(summary)

    message["To"] = "cameron.hightower@simbabuilds.com"
    message["From"] = "cameron.hightower@simbabuilds.com"
    message["Subject"] = f"Summary of conversation with {client_name}"

    # encoded message
    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

    create_message = {"raw": encoded_message}
    # pylint: disable=E1101
    send_message = (
        service.users()
        .messages()
        .send(userId="me", body=create_message)
        .execute()
    )
    print(f'Message Id: {send_message["id"]}')
  except HttpError as error:
    print(f"An error occurred: {error}")
    send_message = None
  return send_message






# # Add lead to Airtable
# def create_lead(name, phone, address):
#   url = "https://api.airtable.com/v0/appM1yx0NobvowCAg/Leads"  # Change this to your Airtable API URL
#   headers = {
#       "Authorization": AIRTABLE_API_KEY,
#       "Content-Type": "application/json"
#   }
#   data = {
#       "records": [{
#           "fields": {
#               "Name": name,
#               "Phone": phone,
#               "Address": address
#           }
#       }]
#   }
#   response = requests.post(url, headers=headers, json=data)
#   if response.status_code == 200:
#     print("Lead created successfully.")
#     return response.json()
#   else:
#     print(f"Failed to create lead: {response.text}")




# Create or load assistant
def create_assistant(client):
    assistant_file_path = 'assistant.json'

    # If there is an assistant.json file already, then load that assistant
    if os.path.exists(assistant_file_path):
        with open(assistant_file_path, 'r') as file:
            assistant_data = json.load(file)
            assistant_id = assistant_data['assistant_id']
            print("Loaded existing assistant ID.")
    else:
    # If no assistant.json is present, create a new assistant using the below specifications

        fha_file = client.files.create(file=open("/Users/cameronhightower/Documents/LoanY/docs/FHA_pamphlet.pdf", "rb"),
                               purpose='assistants')
        
        va_file = client.files.create(file=open("/Users/cameronhightower/Documents/LoanY/docs/VA_pamphlet.pdf", "rb"),
                               purpose='assistants')

        assistant = client.beta.assistants.create(
        # Getting assistant prompt from "prompts.py" file, edit on left panel if you want to change the prompt
        instructions=assistant_instructions,
        model= "gpt-4-1106-preview",
        tools=[
            {
                "type": "retrieval"  # This adds the knowledge base as a tool
            },
            {
                "type": "function",  # This adds sending an email as a tool
                "function": {
                    "name": "gmail_send_message",
                    "description":
                    "Sends an email to a human loan officer containing a summary of the conversation with the prospective buyer",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "summary": {
                                "type":
                                "string",
                                "description":
                                "Summary of conversation with client"
                            },
                            "client_name": {
                                "type":
                                "string",
                                "description":
                                "The name of the client"
                            }
                        },
                        "required": ["summary", "client_name"]
                    }
                }
            }
        #     ,{
        #         "type": "function",  # This adds the lead capture as a tool
        #         "function": {
        #             "name": "create_lead",
        #             "description":
        #             "Capture lead details and save to Airtable.",
        #             "parameters": {
        #                 "type": "object",
        #                 "properties": {
        #                     "name": {
        #                         "type": "string",
        #                         "description": "Name of the lead."
        #                     },
        #                     "phone": {
        #                         "type": "string",
        #                         "description": "Phone number of the lead."
        #                     },
        #                     "address": {
        #                         "type": "string",
        #                         "description": "Address of the lead."
        #                     }
        #                 },
        #                 "required": ["name", "phone", "address"]
        #             }
        #         }
        #     }
        ],
        file_ids=[fha_file.id, va_file.id])

        # Create a new assistant.json file to load on future runs
        with open(assistant_file_path, 'w') as file:
            json.dump({'assistant_id': assistant.id}, file)
            print("Created a new assistant and saved the ID.")

        assistant_id = assistant.id

    return assistant_id










