import pyodbc
from datetime import datetime
import bcrypt
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

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Helper: Hash password
def hash_password(password):
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt)

# Helper: Verify password
def verify_password(input_password, stored_hash):
    return bcrypt.checkpw(input_password.encode('utf-8'), stored_hash.encode('utf-8'))

# CREATE
def create_user(first_name, last_name, email, password, phone=None, profile_pic=None, dob=None, gender=None):
    try:
        password_hash = hash_password(password).decode('utf-8')
        query = '''
        INSERT INTO Users (FirstName, LastName, Email, PasswordHash, PhoneNumber, ProfilePictureUrl, DateOfBirth, Gender)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        '''
        cursor.execute(query, (first_name, last_name, email, password_hash, phone, profile_pic, dob, gender))
        conn.commit()
        logger.info(f"User created successfully with email: {email}")
        return "User created successfully."
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        return "Failed to create user."

# READ - Get User by Email
def get_user(email):
    try:
        query = 'SELECT UserID, FirstName, LastName, Email, PhoneNumber, ProfilePictureUrl, DateOfBirth, Gender FROM Users WHERE Email = ?'
        cursor.execute(query, (email,))
        user = cursor.fetchone()
        if user:
            logger.info(f"User found with email: {email}")
            return user
        else:
            logger.warning(f"User not found with email: {email}")
            return None
    except Exception as e:
        logger.error(f"Error fetching user: {e}")
        return None

# READ + Password Check (Login)
def login_user(email, input_password):
    try:
        query = 'SELECT UserID, FirstName, PasswordHash FROM Users WHERE Email = ?'
        cursor.execute(query, (email,))
        user = cursor.fetchone()
        if user:
            user_id, name, stored_hash = user
            if verify_password(input_password, stored_hash):
                logger.info(f"Login successful for user: {email}")
                return f"Login successful! Welcome, {name}."
            else:
                logger.warning(f"Incorrect password attempt for user: {email}")
                return "Incorrect password."
        else:
            logger.warning(f"Login attempt failed: user not found with email {email}")
            return "User not found."
    except Exception as e:
        logger.error(f"Error during login: {e}")
        return "Login error."

# UPDATE - Update User Info
def update_user(email, first_name=None, last_name=None, phone=None, profile_pic=None, dob=None, gender=None, password=None):
    try:
        fields = []
        values = []

        if first_name:
            fields.append("FirstName = ?")
            values.append(first_name)
        if last_name:
            fields.append("LastName = ?")
            values.append(last_name)
        if phone:
            fields.append("PhoneNumber = ?")
            values.append(phone)
        if profile_pic:
            fields.append("ProfilePictureUrl = ?")
            values.append(profile_pic)
        if dob:
            fields.append("DateOfBirth = ?")
            values.append(dob)
        if gender:
            fields.append("Gender = ?")
            values.append(gender)
        if password:
            password_hash = hash_password(password).decode('utf-8')
            fields.append("PasswordHash = ?")
            values.append(password_hash)

        if not fields:
            logger.info("No fields provided for update.")
            return "No fields to update."

        query = f"UPDATE Users SET {', '.join(fields)} WHERE Email = ?"
        values.append(email)
        cursor.execute(query, values)
        conn.commit()

        if cursor.rowcount:
            logger.info(f"User updated successfully: {email}")
            return "User updated successfully."
        else:
            logger.warning(f"User not found for update: {email}")
            return "User not found."
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        return "Failed to update user."

# DELETE - Remove User
def delete_user(email):
    try:
        query = "DELETE FROM Users WHERE Email = ?"
        cursor.execute(query, (email,))
        conn.commit()
        if cursor.rowcount:
            logger.info(f"User deleted successfully: {email}")
            return "User deleted successfully."
        else:
            logger.warning(f"Delete failed - user not found: {email}")
            return "User not found."
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        return "Failed to delete user."

# Get UserID from Email
def get_user_id(email):
    try:
        query = "SELECT UserID FROM Users WHERE Email = ?"
        cursor.execute(query, (email,))
        user = cursor.fetchone()

        if user:
            logger.info(f"User ID fetched for email: {email}")
            return user[0]
        else:
            logger.warning(f"User ID not found for email: {email}")
            return "User not found."
    except Exception as e:
        logger.error(f"Error fetching user ID: {e}")
        return None
        
# Get FirstName from Email
def get_first_name(email):
    try:
        query = "SELECT FirstName FROM Users WHERE Email = ?"
        cursor.execute(query, (email,))
        user = cursor.fetchone()

        if user:
            logger.info(f"User FirstName fetched for email: {email}")
            return user[0]
        else:
            logger.warning(f"User FirstName not found for email: {email}")
            return "User not found."
    except Exception as e:
        logger.error(f"Error fetching user FirstName: {e}")
        return None


# Example usage:

# create_user("John", "Doe", "john@example.com", "pass123", "1234567890")
# get_user("john@example.com")
# login_user("john@example.com", "pass123")
# update_user("john@example.com", first_name="Johnny", password="newpass456")
# delete_user("alice@example.com")
# print(type(get_user_id("john@example.com")))
# print(get_first_name("haider@gmail.com"))