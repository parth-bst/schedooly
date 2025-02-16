# Filename: google_docs_reader.py
from google.oauth2 import service_account
from googleapiclient.discovery import build
from google.oauth2 import service_account
from config import AppConfig
import openai
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GoogleDocManager:
    def __init__(self):
        # Initialize config and OpenAI settings
        self.config = AppConfig()
        logger.info(f"Initializing GoogleDocManager {self.config.config}")
        
        openai.api_key = self.config.config['openai']['api-key'] #openai.api-key
        #openai.organization = self.config.config.openai.organization
        
        self._init_credentials()
        
    def _init_credentials(self):
        # Get credentials directly from config
        
        SCOPES = ['https://www.googleapis.com/auth/spreadsheets',
                  'https://www.googleapis.com/auth/documents']
        google_credentials = service_account.Credentials.from_service_account_file(
            self.config.config['google']['credentials-path'],
            scopes=SCOPES
        )
        self.sheets_service = build('sheets', 'v4', credentials=google_credentials)
        self.docs_service = build('docs', 'v1', credentials=google_credentials)


    def get_base_cv_data(self, document_id=None):
        # Use configured doc ID if none provided
        doc_id = document_id or self.config.config['google']['schedule_doc_id']
        logger.info(f"Getting base CV data from document ID: {doc_id}")
        document = self.docs_service.documents().get(documentId=doc_id).execute()
        content = document.get('body').get('content')
        logger.info(f"RAW Content of base CV file are: {content}")

        base_cv_data = extract_content_doc(content)
        return base_cv_data

    def write_to_sheet(self, spreadsheet_id, range_name, values):
        """Write data to Google Sheets
        
        Args:
            spreadsheet_id (str): The ID of the spreadsheet
            range_name (str): The A1 notation of the range e.g. 'Sheet1!A1:B2'
            values (list): 2D array of values to write
        """
        body = {
            'values': values
        }
        result = self.sheets_service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption='RAW',
            body=body
        ).execute()
        return result

    def append_to_sheet(self, spreadsheet_id, range_name, values):
        """Append data to Google Sheets
        
        Args:
            spreadsheet_id (str): The ID of the spreadsheet
            range_name (str): The A1 notation of the range e.g. 'Sheet1!A:B'
            values (list): 2D array of values to append
        """
        body = {
            'values': values
        }
        result = self.sheets_service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption='RAW',
            insertDataOption='INSERT_ROWS',
            body=body
        ).execute()
        return result

    def read_sheet(self, spreadsheet_id, range_name):
        """Read data from Google Sheets
        
        Args:
            spreadsheet_id (str): The ID of the spreadsheet
            range_name (str): The A1 notation of the range to read
        """
        result = self.sheets_service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=range_name
        ).execute()
        return result.get('values', [])

def extract_content_doc(content):
    text_content = []
    for element in content:
        if 'paragraph' in element:
            paragraph_text = ''
            # Get all text runs in the paragraph
            for text_element in element['paragraph'].get('elements', []):
                if 'textRun' in text_element:
                    paragraph_text += text_element['textRun']['content']
            text_content.append(paragraph_text)
    return text_content
