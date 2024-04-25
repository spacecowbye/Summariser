import os
import urllib.parse
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from io import BytesIO
import streamlit as st
from list import available_docs
from google.oauth2 import service_account
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline

# Function to authenticate with Google Drive API
def create_google_doc(summary, service, folder_id):
    # Create a new Google Doc
    title = "Testing"
    file_metadata = {
        'name': title,
        'parents': [folder_id],
        'mimeType': 'application/vnd.google-apps.document'
    }
    file = service.files().create(body=file_metadata).execute()
    doc_id = file['id']

    # Insert the summary into the Google Doc
    media = MediaIoBaseUpload(BytesIO(summary.encode()), mimetype='text/plain')
    service.files().update(fileId=doc_id, media_body=media).execute()

    st.write('Google Doc created and summary inserted.')
def append_to_google_doc(summary, service, doc_id):
    # Retrieve the existing Google Doc
    doc = service.files().get(fileId=doc_id, fields='name').execute()
    title = doc['name']

    # Insert the summary into the Google Doc
    media = MediaIoBaseUpload(BytesIO(summary.encode()), mimetype='text/plain')
    service.files().update(fileId=doc_id, media_body=media).execute()

    st.write(f'Summary appended to Google Doc: {title}')


# Function to authenticate with Google Drive API

def authenticate():
    # Path to your service account key JSON file
    key_path = 'credentials.json'

    # Create credentials using service account key file
    credentials = service_account.Credentials.from_service_account_file(key_path, scopes=['https://www.googleapis.com/auth/drive'])

    return credentials
    

# LLM pipeline

def llm_pipeline(text):
    tokenizer = AutoTokenizer.from_pretrained("MBZUAI/LaMini-Flan-T5-248M")
    model = AutoModelForSeq2SeqLM.from_pretrained("MBZUAI/LaMini-Flan-T5-248M")
    max_input_length = tokenizer.model_max_length

    # Split the input text into batches based on the maximum input length
    batches = []
    current_batch = ""
    for line in text.strip().split('\n'):
        if len(current_batch) + len(line) + 1 <= max_input_length:
            current_batch += line + "\n"
        else:
            batches.append(current_batch.strip())
            current_batch = line + "\n"
    if current_batch:
        batches.append(current_batch.strip())

    # Process each batch and concatenate the summaries
    summaries = []
    for batch in batches:
        pipe_sum = pipeline(
            'summarization',
            model=model,
            tokenizer=tokenizer,
            max_length=300,  # Set a maximum length for the generated summary
            min_length=50)
        result = pipe_sum(batch)
        summaries.append(result[0]['summary_text'])

    # Join the summaries of all batches
    return "\n".join(summaries)

# Streamlit app
st.title('Google Drive Summary Uploader')

# Input text for summarization
text_to_summarize = st.text_area('Enter the text to summarize:')

# Get the selected folder from the user
selected_doc = st.selectbox('Select the folder where the summary will be written:', [doc['name'] for doc in available_docs])
selected_folder_id = [doc['id'] for doc in available_docs if doc['name'] == selected_doc][0]

# Summarize the text
if st.button('Summarize'):
    # Authenticate with Google Drive API
    credentials = authenticate()
    service = build('drive', 'v3', credentials=credentials)
    # Message to instruct the user to click the button
    st.markdown('Please wait while we summarize and upload the document...')

    with st.spinner('Summarizing text...'):
        summary = llm_pipeline(text_to_summarize)

    # Create a Google Doc with the summary and insert it into the selected folder
    append_to_google_doc(summary, service, selected_folder_id)
