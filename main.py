import os
import io
import shutil
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
import fitz # PyMuPDF


def pdf_to_txt(pdf_path, txt_path):
    with fitz.open(pdf_path) as pdf:
        text = ""
        for page in pdf:
            text += page.get_text()
    with open(txt_path, "w", encoding="utf-8") as txt:
        txt.write(text)
    return txt_path

def pdf_exists_as_txt(pdf_name, txt_files):

    for txt_file in txt_files:
        txt_file_name_without_ext = os.path.splitext(os.path.basename(txt_file['name']))[0]
        if pdf_name == os.path.splitext(os.path.basename(txt_file['name']))[0]:
            return True

    return False

def upload_file_to_drive_folder(folder_id, service, file_path, actual_file_name):

    try:
        # Define file metadata
        file_name = os.path.basename(file_path)
        file_metadata = {'name': actual_file_name + ".txt", 'parents': [folder_id]}

        # Upload file to the folder
        media = MediaFileUpload(file_path, resumable=True)
        file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        print(f'File ID: {file["id"]} uploaded to folder ID: {folder_id}')
    except HttpError as error:
        print(f'An error occurred: {error}')

def download_file_from_drive(service, file_id, file_path):
    # Download the PDF file contents
    request = service.files().get_media(fileId=file_id)
    file_contents = io.BytesIO(request.execute())

    # Write the PDF file contents to a file
    with open('pdf_files/{}'.format("../" + file_path), 'wb') as f:
        shutil.copyfileobj(file_contents, f)

def get_files_from_drive_folder(folder_id, service):


    # Define the query to search for files in the folder
    query = "'{}' in parents".format(folder_id)

    # Execute the query
    results = service.files().list(q=query, fields="nextPageToken, files(id, name, mimeType)").execute()
    return results.get('files', [])


def update_txt_folder():
    # Service account credentials
    creds = service_account.Credentials.from_service_account_file('credentials.json')

    # ID of folder containing pdf's
    pdf_folder_id = '1rBMK7jStTpsJDNLIJaznlJH3cMB218h-'

    # ID of folder for txt's
    txt_folder_id = '1rNZrv06u_kg9zdoa6D-i82zFfk1QE1tB'

    # Connect to the Google Drive API
    service = build('drive', 'v3', credentials=creds)

    # Get all files within the pdf folder
    pdf_files = get_files_from_drive_folder(pdf_folder_id, service)

    # Get all files within the txt folder
    txt_files = get_files_from_drive_folder(txt_folder_id, service)

    if not pdf_files:
        print('No files found in the specified folder.')
    else:
        # # Create a directory to store the downloaded PDF files
        # if not os.path.exists('pdf_files'):
        #     os.makedirs('pdf_files')

        # Download each PDF file to the directory
        for pdf_file in pdf_files:
            try:
                file_id = pdf_file['id']
                file_name = pdf_file['name']
                file_name_without_ext = os.path.splitext(os.path.basename(file_name))[0]
                file_mime_type = pdf_file.get('mimeType', '')



                # Check if the file is a PDF and doesnt already exitst as a txt
                if file_mime_type == 'application/pdf' and not pdf_exists_as_txt(file_name_without_ext, txt_files):

                    download_file_from_drive(service, file_id, "temp.pdf")

                    pdf_to_txt("temp.pdf", "temp.txt")

                    upload_file_to_drive_folder(txt_folder_id, service, "temp.txt", file_name_without_ext)

                    print('Downloaded file: {}'.format(file_name))

            except HttpError as error:
                print('An error occurred: {}'.format(error))



# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    update_txt_folder()


