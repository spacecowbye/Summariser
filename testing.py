def append_to_google_doc(summary, service, doc_id):
    # Retrieve the existing Google Doc
    doc = service.files().get(fileId=doc_id, fields='name').execute()
    title = doc['name']

    # Insert the summary into the Google Doc
    media = MediaIoBaseUpload(BytesIO(summary.encode()), mimetype='text/plain')
    service.files().update(fileId=doc_id, media_body=media).execute()

    st.write(f'Summary appended to Google Doc: {title}')