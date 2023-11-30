import toml
import openai
import streamlit as st

import json
import os
import time
from flask import Flask, request, jsonify
from openai import OpenAI
import functions

# Check OpenAI version compatibility
from packaging import version

required_version = version.parse("1.1.1")
current_version = version.parse(openai.__version__)
if current_version < required_version:
  raise ValueError(
      f"Error: OpenAI version {openai.__version__} is less than the required version 1.1.1"
  )
else:
  print("OpenAI version is compatible.")

# Load configuration from config.toml
config = toml.load('/Users/cameronhightower/Documents/LoanY/.streamlit/config.toml')

# Set the OpenAI API key from the config file
openai.api_key = config['openai']['api_key']
OPENAI_API_KEY = openai.api_key

# llm_model = "gpt-3.5-turbo-0301"
llm_model = "gpt-4-1106-preview"

# from dotenv import load_dotenv, find_dotenv
# _ = load_dotenv(find_dotenv()) # read local .env file
# openai.api_key = os.environ["OPENAI_API_KEY"]



def get_completion(prompt, model=llm_model):
    messages = [{"role": "user", "content": prompt}]
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=0.7, # this is the degree of randomness of the model's output
    )
    return response.choices[0].message["content"]

def get_completion_from_messages(messages, model=llm_model, temperature=0.7):
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=temperature, # this is the degree of randomness of the model's output
    )
    return response.choices[0].message["content"]


# context = [ {'role':'system', 'content':f"""

# """} ]

st.title("LoanY: A loan officer aide streamlining the loan search process")
description = "Your information will not be shared with external parties."
st.write(f":green[{description}]")

# if 'context' not in st.session_state:
#     st.session_state.context = context

# Initialize OpenAI client
if 'client' not in st.session_state:
    st.session_state.client = OpenAI(api_key = OPENAI_API_KEY)

if 'history' not in st.session_state:
    st.session_state.history = ""


if 'thread' not in st.session_state:
    st.session_state.thread = st.session_state.client.beta.threads.create()
    st.session_state.thread_id = st.session_state.thread.id
    print(f"New thread created with ID: {st.session_state.thread.id}")


# Create or load assistant
if 'assistant' not in st.session_state:
    st.session_state.assistant_id = functions.create_assistant(
    st.session_state.client)  # this function comes from "functions.py"



prompt = st.chat_input("Interact with LoanY here.  You can start by saying hello.")


if prompt:
    st.session_state.history += prompt
    st.session_state.history += "\n\n" 
    # st.session_state.context.append({'role':'user', 'content':f"{prompt}"}) 
      
    # Add the user's message to the thread
    st.session_state.client.beta.threads.messages.create(thread_id=st.session_state.thread_id,
                                      role="user",
                                      content=prompt)   
    # Run the Assistant
    run = st.session_state.client.beta.threads.runs.create(thread_id=st.session_state.thread_id,
                                        assistant_id=st.session_state.assistant_id)
    # Check if the Run requires action (function call)
    while True:
        run_status = st.session_state.client.beta.threads.runs.retrieve(thread_id=st.session_state.thread_id,
                                                    run_id=run.id)
        # print(f"Run status: {run_status.status}")
        if run_status.status == 'completed':
            break
        elif run_status.status == 'requires_action':
        # Handle the function call
         for tool_call in run_status.required_action.submit_tool_outputs.tool_calls:
            if tool_call.function.name == "gmail_send_message":
            # Process solar panel calculations
                arguments = json.loads(tool_call.function.arguments)
                output = functions.gmail_send_message(
                    arguments["client_name"], arguments["summary"])
                st.session_state.client.beta.threads.runs.submit_tool_outputs(thread_id=st.session_state.thread_id,
                                                            run_id=run.id,
                                                            tool_outputs=[{
                                                                "tool_call_id":
                                                                tool_call.id,
                                                                "output":
                                                                json.dumps(output)
                                                            }])
            # elif tool_call.function.name == "create_lead":
            # # Process lead creation
            #     arguments = json.loads(tool_call.function.arguments)
            #     output = functions.create_lead(arguments["name"], arguments["phone"],
            #                                     arguments["address"])
            #     st.session_state.client.beta.threads.runs.submit_tool_outputs(thread_id=st.session_state.thread_id,
            #                                                 run_id=run.id,
            #                                                 tool_outputs=[{
            #                                                     "tool_call_id":
            #                                                     tool_call.id,
            #                                                     "output":
            #                                                     json.dumps(output)
            #                                                 }])
        # time.sleep(1)  # Wait for a second before checking again
    
    
    messages = st.session_state.client.beta.threads.messages.list(thread_id=st.session_state.thread_id)
    response = messages.data[0].content[0].text.value

    # response = get_completion_from_messages(st.session_state.context)
    # response = get_completion_from_messages(st.session_state.thread)  
    # st.session_state.context.append({'role':'assistant', 'content':f"{response}"})
  
    # st.session_state.history += f":green[{response}]"
    st.session_state.history += response

    st.session_state.history += "\n\n" 


st.write(st.session_state.history)

# streamlit run streamlit_app.py







