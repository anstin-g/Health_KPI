import pyodbc
import json
import re
import logging
import ast

server = ""
database = ""
username = ""
password = ""

conn = pyodbc.connect(
    f"DRIVER={{ODBC Driver 18 for SQL Server}};"
    f"SERVER={server};"
    f"DATABASE={database};"
    f"UID={username};"
    f"PWD={password};"
    "Encrypt=yes;"
    "TrustServerCertificate=no;"
    "Timeout=30;"
)

cursor = conn.cursor()

# Setup logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# UPLOAD - Store Document Data as String
def upload_document(user_id, document_name, document_data, document_details):
    """Uploads a document's data as a string."""
    try:
        query = '''
        INSERT INTO UserDocuments (UserID, DocumentName, DocumentData, Details)
        VALUES (?, ?, ?, ?)
        '''
        cursor.execute(query, (user_id, document_name, document_data, document_details))
        conn.commit()
        logger.info(f"Document '{document_name}' uploaded successfully.")
    except Exception as e:
        logger.error(f"Error uploading document: {e}")

# READ - Fetch Document Data by Name
def fetch_document(user_id, document_name):
    """Fetches the document data as a string."""
    try:
        query = '''
        SELECT DocumentData FROM UserDocuments 
        WHERE UserID = ? AND DocumentName = ?
        '''
        cursor.execute(query, (user_id, document_name))
        document = cursor.fetchone()

        if document:
            logger.info(f"Document '{document_name}' fetched successfully.")
            return document[0]  # Returning document content
        else:
            logger.warning(f"Document '{document_name}' not found for user ID {user_id}.")
            return None
    except Exception as e:
        logger.error(f"Error fetching document: {e}")
        return None

def fetch_document_details(user_id, document_name):
    """Fetches the document details as a string."""
    try:
        query = '''
        SELECT Details FROM UserDocuments 
        WHERE UserID = ? AND DocumentName = ?
        '''
        cursor.execute(query, (user_id, document_name))
        document = cursor.fetchone()

        if document:
            return document[0]  # Returning document details
        else:
            logger.warning(f"Details for document '{document_name}' not found for user ID {user_id}.")
            return None
    except Exception as e:
        logger.error(f"Error fetching document details: {e}")
        return None

def fetch_document_names(user_id):
    """Fetches all document names for a user and returns as list."""
    try:
        query = '''
        SELECT DocumentName 
        FROM UserDocuments 
        WHERE UserID = ?
        '''

        cursor.execute(query, (user_id,))   # <-- FIXED tuple
        rows = cursor.fetchall()

        if rows:
            return [row[0] for row in rows]
        else:
            logger.warning(f"Documents not found for user ID {user_id}.")
            return []   # <-- ALWAYS return list

    except Exception as e:
        logger.error(f"Error fetching document names: {e}")
        return []       # <-- NEVER return None
    
def fetch_all_documents(user_id):
    try:
        query = '''
        SELECT DocumentData FROM UserDocuments
        WHERE UserID = ?
        '''
        cursor.execute(query, (user_id,))
        documents = cursor.fetchall()

        document_list = []

        for row in documents:
            raw_data = row[0]
            parsed = string_to_dict(raw_data)

            if parsed is not None:
                document_list.append(parsed)

        logger.info(f"{len(document_list)} document(s) fetched for user ID {user_id}.")
        return document_list

    except Exception as e:
        logger.error(f"Error fetching documents: {e}")
        return []

def string_to_dict(string_data):
    try:
        # Remove markdown backticks if any
        cleaned = string_data.replace("```", "").strip()

        # Try JSON first (for future clean data)
        try:
            return json.loads(cleaned)
        except:
            pass

        # Fallback: parse Python dict string safely
        return ast.literal_eval(cleaned)

    except Exception as e:
        logger.error(f"Parsing failed: {e}")
        logger.error(f"Raw data was: {string_data}")
        return None
# print(fetch_all_documents("32"))
# print(fetch_document_names("32"))