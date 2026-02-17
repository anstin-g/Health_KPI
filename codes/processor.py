import os
import numpy as np
import re
import json
import logging 

from openai import AzureOpenAI
from datetime import datetime, timedelta
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest

from .Database.userdocuments_table.crud import fetch_document, fetch_document_details
from .Uploading_files import list_documents_in_directory

# from Database.userdocuments_table.crud import fetch_document, fetch_document_details
# from Uploading_files import list_documents_in_directory


# Setup logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HealthKPIExtractor:
    def __init__(self):
        self.blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
        self.openai_client = AzureOpenAI(
            azure_endpoint=AZURE_OPENAI_ENDPOINT,
            api_key=AZURE_OPENAI_API_KEY,
            api_version=AZURE_OPENAI_API_VERSION
        )

    def generate_sas_url(self, account_name, account_key, container_name, user_id, blob_name, expiry_hours=1):
        full_blob_name = f"{user_id}/{blob_name}"
        sas_token = generate_blob_sas(
            account_name=account_name,
            container_name=container_name,
            blob_name=full_blob_name,
            account_key=account_key,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.utcnow() + timedelta(hours=expiry_hours)
        )
        sas_url = f"https://{account_name}.blob.core.windows.net/{container_name}/{full_blob_name}?{sas_token}"
        logger.info(f"SAS URL generated for blob: {full_blob_name}")
        return sas_url

    def analyze_read(self, BLOB_NAME, USER_ID):
        formUrl = self.generate_sas_url(ACCOUNT_NAME, ACCOUNT_KEY, CONTAINER_NAME, USER_ID, BLOB_NAME)
        document_intelligence_client = DocumentIntelligenceClient(
            endpoint=AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT,
            credential=AzureKeyCredential(AZURE_DOCUMENT_INTELLIGENCE_KEY)
        )
        poller = document_intelligence_client.begin_analyze_document("prebuilt-read", AnalyzeDocumentRequest(url_source=formUrl))
        result = poller.result()
        logger.info(f"Document analysis complete for: {BLOB_NAME}")
        return result.content

    def query_chatbot(self, extracted_text):
        message = f"This is the data\n\n{extracted_text}"
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system",
                     "content": "When the user provides data, return only a dictionary containing all the important health-related KPIs with their names, values, and units. If a value does not exist, set the value and unit as an empty string. Do not include any additional text or explanations in the response."},
                    {"role": "user", "content": message}
                ],
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error querying chatbot: {e}")
            return ""

    def extract_values(self, pdf_name, user_id):
        result = self.analyze_read(pdf_name, user_id)
        result = self.query_chatbot(result)
        return result


class DetailsExtractor:
    def __init__(self):
        self.blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
        self.openai_client = AzureOpenAI(
            azure_endpoint=AZURE_OPENAI_ENDPOINT,
            api_key=AZURE_OPENAI_API_KEY,
            api_version=AZURE_OPENAI_API_VERSION
        )

    def generate_sas_url(self, account_name, account_key, container_name, user_id, blob_name, expiry_hours=1):
        full_blob_name = f"{user_id}/{blob_name}"
        sas_token = generate_blob_sas(
            account_name=account_name,
            container_name=container_name,
            blob_name=full_blob_name,
            account_key=account_key,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.utcnow() + timedelta(hours=expiry_hours)
        )
        sas_url = f"https://{account_name}.blob.core.windows.net/{container_name}/{full_blob_name}?{sas_token}"
        logger.info(f"SAS URL generated for blob: {full_blob_name}")
        return sas_url

    def analyze_read(self, BLOB_NAME, USER_ID):
        formUrl = self.generate_sas_url(ACCOUNT_NAME, ACCOUNT_KEY, CONTAINER_NAME, USER_ID, BLOB_NAME)
        document_intelligence_client = DocumentIntelligenceClient(
            endpoint=AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT,
            credential=AzureKeyCredential(AZURE_DOCUMENT_INTELLIGENCE_KEY)
        )
        poller = document_intelligence_client.begin_analyze_document("prebuilt-read", AnalyzeDocumentRequest(url_source=formUrl))
        result = poller.result()
        logger.info(f"Document analysis complete for: {BLOB_NAME}")
        return result.content

    def query_chatbot(self, extracted_text):
        message = f"This is the data\n\n{extracted_text}"
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system",
                     "content": "Analyse the data and give me back the following details of the patient in dictionary format name, email, gender, phone number, age , date of the report and laboratory name. If a value does not exist, set the value and unit as an empty string. Do not include any additional text or explanations in the response."},
                    {"role": "user", "content": message}
                ],
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error querying chatbot: {e}")
            return ""

    def extract_values(self, pdf_name, user_id):
        result = self.analyze_read(pdf_name, user_id)
        result = self.query_chatbot(result)
        return result


class Value_extractor_for_analysis:
    def __init__(self):
        self.blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
        self.openai_client = AzureOpenAI(
            azure_endpoint=AZURE_OPENAI_ENDPOINT,
            api_key=AZURE_OPENAI_API_KEY,
            api_version=AZURE_OPENAI_API_VERSION
        )

    def query_chatbot(self, data_1, data_2, data_3):
        message = f"Data_1 is {data_1}, Data_2 is {data_2}, Data_3 is {data_3}."
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system",
                     "content": "Search for the date in data_3. Search for data_1's value in data_2 provided and return a dictionary in following format date: value. Do not include unit in the value.Add all dates in single format the is '%Y-%m-%d'. keep the value in float type no matter what. If a value does not exist, return an empty dictionary, dont even add the date. Do not include any additional text or explanations in the response.Keep the dictionary in the single line"},
                    {"role": "user", "content": message}
                ],
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error querying chatbot: {e}")
            return ""

    def extract_values(self, user_id, documents_list, kpi_list):
        all_docs_content = []
        all_doc_details = []

        for i in documents_list:
            doc_content = fetch_document(user_id, i)
            all_docs_content.append(doc_content)

        for j in documents_list:
            doc_details = fetch_document_details(user_id, j)
            all_doc_details.append(doc_details)

        data = {}
        for i in kpi_list:
            data[i] = []
            for j in range(len(all_docs_content)):
                result = self.query_chatbot(i, all_docs_content[j], all_doc_details[j])
                result = re.sub('python', '', result)
                result = re.sub('json', '', result)
                result = re.sub('`', '', result)
                data[i].append(result)
        logger.info(f"Extracted KPI values for user {user_id}")
        return data


class clean_dict:
    def __init__(self):
        self.blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
        self.openai_client = AzureOpenAI(
            azure_endpoint=AZURE_OPENAI_ENDPOINT,
            api_key=AZURE_OPENAI_API_KEY,
            api_version=AZURE_OPENAI_API_VERSION
        )

    def query_chatbot(self, data_dict):
        message = json.dumps(data_dict)
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system",
                     "content": "Clean the given dictionary by removing the key-value pairs with no values. A key-value pair is only valid if it has data inside both key and value. Keep only the list items that contain actual data. Always preserve the list structure even if only one valid item remains. Do not include any additional text or explanations in the response.Keep the dictionary in the single line"},
                    {"role": "user", "content": message}
                ],
            )
            result = response.choices[0].message.content
            result = re.sub('python', '', result)
            result = re.sub('json', '', result)
            result = re.sub('`', '', result)
            logger.info("Dictionary cleaned")
            return result
        except Exception as e:
            logger.error(f"Error querying chatbot: {e}")
            return ""
        

# # Usage example
# if __name__ == "__main__":
#     tests = [
#     "Haemoglobin"
#     ]
#     user_id = 7
#     docs = ['DOC_1.pdf', 'DOC_3.pdf']
#     extractor = Value_extractor_for_analysis()
#     data = extractor.extract_values(user_id, docs, tests)
#     cleaner = clean_dict()
#     print(type(cleaner.query_chatbot(data)))
#     print(cleaner.query_chatbot(data))

# details = DetailsExtractor()
# print(details.extract_values('DOC_1.pdf',7))