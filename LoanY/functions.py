import json
import requests
import os
import openai
import toml
from openai import OpenAI
from prompts import assistant_instructions
import streamlit as st

# Load configuration from config.toml
config = toml.load('/Users/cameronhightower/Documents/LoanY/.streamlit/config.toml')

# Set the OpenAI and GMAIL API keys from the config file
openai.api_key = config['openai']['api_key']
OPENAI_API_KEY = openai.api_key
# GMAIL_API_KEY = config['']['']




# Init OpenAI Client
if 'client' not in st.session_state:
    st.session_state.client = OpenAI(api_key = OPENAI_API_KEY)


# def send_email_to_loan_officer():
#   url = ""  # GMAIL API URL
#   headers = {
#       "Authorization": GMAIL_API_KEY,
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

        fha_file = client.files.create(file=open("/Users/cameronhightower/Documents/LoanY/docs/FHA_11_7_23.pdf", "rb"),
                               purpose='assistants')
        
        va_file = client.files.create(file=open("/Users/cameronhightower/Documents/LoanY/docs/va_pamphlet.pdf", "rb"),
                               purpose='assistants')

        assistant = client.beta.assistants.create(
        # Getting assistant prompt from "prompts.py" file, edit on left panel if you want to change the prompt
        instructions=assistant_instructions,
        model="gpt-4-1106-preview",
        tools=[
            {
                "type": "retrieval"  # This adds the knowledge base as a tool
            },
        #     {
        #         "type": "function",  # This adds sending an email as a tool
        #         "function": {
        #             "name": "send_email_to_loan_officer",
        #             "description":
        #             "Sends an email to a human loan officer containing a summary of the conversation with the prospective buyer",
        #             "parameters": {
        #                 "type": "object",
        #                 "properties": {
        #                     "address": {
        #                         "type":
        #                         "string",
        #                         "description":
        #                         "Address for calculating solar potential."
        #                     },
        #                     "monthly_bill": {
        #                         "type":
        #                         "integer",
        #                         "description":
        #                         "Monthly electricity bill in USD for savings estimation."
        #                     }
        #                 },
        #                 "required": ["address", "monthly_bill"]
        #             }
        #         }
        #     },
        #     {
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










