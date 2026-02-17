import pyodbc
import json
import re
import logging

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
def upload_document_pending(user_id, first_name, extrcated_name, document_name, document_data, document_details):
    """Uploads a document's data as a string."""
    try:
        query = '''
        INSERT INTO UserDocumentsPending (UserID, FirstName, ExtractedName, DocumentName, DocumentData, Details)
        VALUES (?, ?, ?, ?, ?, ?)
        '''
        cursor.execute(query, (user_id, first_name, extrcated_name, document_name, document_data, document_details))
        conn.commit()
        logger.info(f"Document '{document_name}' uploaded successfully.")
    except Exception as e:
        logger.error(f"Error uploading document: {e}")

def fetch_pending_documents(user_id):
    """Fetches rows from UserDocumentsPending for a specific user and returns as list of dicts."""
    try:
        query = '''
        SELECT 
            DocumentID,
            UserID,
            FirstName,
            ExtractedName,
            DocumentName,
            DocumentData,
            CreatedAt,
            UpdatedAt,
            Details
        FROM UserDocumentsPending
        WHERE UserID = ?
        '''

        # Execute with parameter
        cursor.execute(query, (user_id,))

        # Get column names
        columns = [column[0] for column in cursor.description]

        rows = cursor.fetchall()

        # Convert rows to list of dictionaries
        result = []
        for row in rows:
            row_dict = dict(zip(columns, row))
            result.append(row_dict)

        logger.info(f"Fetched {len(result)} pending documents for UserID {user_id}.")

        return result

    except Exception as e:
        logger.error(f"Error fetching pending documents for UserID {user_id}: {e}")
        return []
        
def remove_pending_document(document_id):
    """Removes a row from UserDocumentsPending for a specific DocumentID."""
    try:
        query = '''
        DELETE FROM UserDocumentsPending
        WHERE DocumentID = ?
        '''

        # Execute with parameter
        cursor.execute(query, (document_id,))

        # Commit the transaction
        conn.commit()

        # Check if any row was deleted
        if cursor.rowcount > 0:
            logger.info(f"Successfully removed pending document with DocumentID {document_id}.")
            return True
        else:
            logger.warning(f"No pending document found with DocumentID {document_id}.")
            return False

    except Exception as e:
        logger.error(f"Error removing pending document with DocumentID {document_id}: {e}")
        return False
    
def fetch_pending_document_details(user_id, document_name):
    """Fetches the document details as a string."""
    try:
        query = '''
        SELECT Details FROM UserDocumentsPending 
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

# print(fetch_pending_documents())