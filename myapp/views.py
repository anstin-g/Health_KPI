from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.http import HttpResponse, Http404
from django.conf import settings
from urllib.parse import urlencode
import secrets
import requests
import logging
import json
import re
import os
import ast

from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from codes.Database.users_table.crud import login_user, get_user_id, create_user, get_first_name, get_user
from codes.Uploading_files import delete_file_in_directory, upload_document_to_blob, create_directory_if_not_exists, list_documents_in_directory
from codes.processor import HealthKPIExtractor, DetailsExtractor, Value_extractor_for_analysis, clean_dict
from codes.Database.userdocuments_table.crud import upload_document, fetch_document, fetch_document_details, fetch_all_documents, fetch_document_names, string_to_dict
from codes.graph_generator import plot_and_save_graphs, parse_input_data
from codes.downloading_files import fetch_pdf_view
from codes.Database.userdocumentspending_table.crud import remove_pending_document, fetch_pending_documents

user_id = None
selected = []

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Your existing functions like login_user, create_user, etc. are assumed to be imported

user_id = None
firstname = None

@csrf_exempt
def user_login(request):
    global user_id
    if request.method == "POST":
        data = json.loads(request.body)
        userid = data.get("userid")
        password = data.get("password")

        data = login_user(userid, password)
        firstname = get_first_name(userid)
        user_id = str(get_user_id(userid))
        if "successful" in data:
            return JsonResponse({"redirect": "/home/"}, status=200)
        else:
            return JsonResponse({"message": data}, status=401)
    return render(request, 'user_login.html')

def home(request):
    return render(request, 'home.html')

@csrf_exempt  
def register_user(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)  
        except json.JSONDecodeError:
            data = request.POST  

        password = data.get("password")
        dob = data.get("dob")
        gender = data.get("gender")
        phonenumber = data.get("phonenumber")
        useremail = data.get("useremail")
        lastname = data.get("lastname")
        firstname = data.get("firstname")

        create_user(firstname, lastname, useremail, password, phonenumber)

        return JsonResponse({"message": "User registered successfully", "redirect_url": ""}, status=201)

    return render(request, 'user_register.html')


def google_login_start(request):
    """Redirect user to Google OAuth consent screen."""
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        logger.warning("Google OAuth not configured: missing GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET")
        return redirect('user_login')
    state = secrets.token_urlsafe(32)
    request.session['google_oauth_state'] = state
    params = {
        'client_id': settings.GOOGLE_CLIENT_ID,
        'redirect_uri': settings.GOOGLE_REDIRECT_URI,
        'response_type': 'code',
        'scope': 'openid email profile',
        'state': state,
        'access_type': 'offline',
        'prompt': 'consent',
    }
    url = 'https://accounts.google.com/o/oauth2/v2/auth?' + urlencode(params)
    return redirect(url)


def google_login_callback(request):
    """Handle Google OAuth callback: verify state, exchange code, create/lookup user, redirect."""
    global user_id, firstname
    state = request.GET.get('state')
    code = request.GET.get('code')
    stored_state = request.session.get('google_oauth_state')

    if not state or state != stored_state:
        logger.warning("Google OAuth state mismatch - possible CSRF")
        return redirect('user_login')
    del request.session['google_oauth_state']

    if not code:
        logger.warning("Google OAuth callback missing code")
        return redirect('user_login')

    token_url = 'https://oauth2.googleapis.com/token'
    token_data = {
        'client_id': settings.GOOGLE_CLIENT_ID,
        'client_secret': settings.GOOGLE_CLIENT_SECRET,
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': settings.GOOGLE_REDIRECT_URI,
    }
    resp = requests.post(token_url, data=token_data, headers={'Content-Type': 'application/x-www-form-urlencoded'})
    if resp.status_code != 200:
        logger.error(f"Google token exchange failed: {resp.status_code} {resp.text}")
        return redirect('user_login')

    token_json = resp.json()
    id_token_str = token_json.get('id_token')
    if not id_token_str:
        logger.error("Google token response missing id_token")
        return redirect('user_login')

    try:
        idinfo = id_token.verify_oauth2_token(
            id_token_str,
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID
        )
        if idinfo['aud'] != settings.GOOGLE_CLIENT_ID:
            logger.warning("Google ID token audience mismatch")
            return redirect('user_login')
        email = idinfo.get('email')
        given_name = idinfo.get('given_name') or ''
        family_name = idinfo.get('family_name') or ''
    except ValueError as e:
        logger.error(f"Google ID token verification failed: {e}")
        return redirect('user_login')

    if not email:
        logger.warning("Google userinfo missing email")
        return redirect('user_login')

    existing = get_user(email)
    if existing:
        user_id = str(existing[0])
        firstname = existing[1] or given_name
        logger.info(f"Google OAuth login for existing user: {email}")
    else:
        oauth_password = secrets.token_urlsafe(32)
        create_user(given_name, family_name, email, oauth_password, phone=None)
        user_id = str(get_user_id(email))
        firstname = given_name
        logger.info(f"Google OAuth created new user: {email}")

    return redirect(settings.LOGIN_REDIRECT_URL)


@csrf_exempt
def upload_files(request):
    if request.method == 'POST':

        files = request.FILES.getlist('files')
        uploaded_files = []

        for file in files:
            temp_dir = "temp/"
            os.makedirs(temp_dir, exist_ok=True)
            local_file_path = os.path.join(temp_dir, file.name)

            with open(local_file_path, "wb+") as destination:
                for chunk in file.chunks():
                    destination.write(chunk)

            # Upload to Azure Blob
            upload_document_to_blob(user_id, local_file_path)

            os.remove(local_file_path)

            uploaded_files.append(file.name)

        return JsonResponse({
            "message": "Upload successful. Processing started in background.",
            "files": uploaded_files
        })
    return render(request, 'upload_documents.html')

def _get_dashboard_documents_data():
    """Build documents list and pending list for dashboard. Used by dashboard (HTML) and dashboard_documents (JSON)."""
    documents = fetch_document_names(user_id)
    document_details_list = []
    response_data = []

    if documents:
        try:
            for document in documents:
                document_data = fetch_document_details(user_id, document)
                if document_data is None:
                    document_details_list.append({})
                    continue
                parsed_data = string_to_dict(document_data)
                document_details_list.append(parsed_data)
        except Exception as e:
            logger.error(f"Error processing documents: {e}")

        for document in documents:
            document_data = fetch_document_details(user_id, document)
            if document_data:
                details_dict = string_to_dict(document_data)
                filtered_details = {
                    k: v for k, v in details_dict.items()
                    if 'name' in k or 'date' in k or 'lab' in k
                }
            else:
                filtered_details = {}
            response_data.append({"file": document, "details": filtered_details})

    pending_documents_list = fetch_pending_documents(user_id)
    logger.info(f"Final documents: {response_data}")
    return response_data, pending_documents_list


@csrf_exempt
def dashboard_documents(request):
    """API endpoint for dashboard documents JSON. Separate URL so browser back never shows JSON for /dashboard/."""
    if user_id is None:
        return JsonResponse({"documents": [], "pending_documents": []}, status=401)
    response_data, pending_documents_list = _get_dashboard_documents_data()
    resp = JsonResponse({
        "documents": response_data,
        "pending_documents": pending_documents_list
    })
    resp["Cache-Control"] = "no-store, no-cache, must-revalidate"
    resp["Pragma"] = "no-cache"
    return resp


@csrf_exempt
def dashboard(request):

    if user_id is None:
        return render(request, 'user_login.html')

    if request.method == "POST":

        try:
            raw_body = request.body

            data = json.loads(raw_body)

            selected_documents = data.get("selected_documents", [])

            for index, doc in enumerate(selected_documents):

                upload_document(
                    doc["UserID"],
                    doc["DocumentName"],
                    doc["DocumentData"],
                    doc["Details"]
                )

                remove_pending_document(doc["DocumentID"])

            resp = JsonResponse({"status": "success"})
            resp["Cache-Control"] = "no-store"
            return resp

        except Exception as e:
            logger.error(f"Error processing selected documents: {e}")
            err_resp = JsonResponse(
                {"status": "error", "message": str(e)},
                status=500
            )
            err_resp["Cache-Control"] = "no-store"
            return err_resp

    response_data, pending_documents_list = _get_dashboard_documents_data()

    return render(request, 'dashboard.html', {
        'documents': response_data
    })

def clean_extracted_values(extracted: dict) -> dict:
    """
    Removes empty '{}' entries and keeps only non-empty date:value mappings.
    Returns only keys that have at least one valid value.
    """

    cleaned = {}

    for test_name, values in extracted.items():
        valid_values = []

        for v in values:
            v = v.strip()

            # Skip empty placeholders
            if v == '{}' or v == "":
                continue

            # Try to validate it's a dict-like structure
            try:
                # Normalize single quotes to double quotes for JSON parsing
                json.loads(v.replace("'", '"'))
                valid_values.append(v)
            except json.JSONDecodeError:
                # If not valid JSON, still keep original string
                valid_values.append(v)

        if valid_values:
            cleaned[test_name] = valid_values

    return cleaned

def analyse_kpi(request):
    if user_id is None:
        return render(request, 'user_login.html')
 
    all_documents_kpis = fetch_all_documents(str(user_id))
 
    # -----------------------------
    # Extract KPI names safely
    # -----------------------------
    list_of_all_kpis = []
 
    for doc in all_documents_kpis:
        if not isinstance(doc, dict):
            continue
 
        main_key = next(iter(doc.keys()), None)
        if main_key and isinstance(doc[main_key], list):
            for item in doc[main_key]:
                if isinstance(item, dict) and "name" in item:
                    list_of_all_kpis.append(item["name"])
 
    sorted_list_of_kpis = sorted(set(list_of_all_kpis))
    logger.info(f"Available KPIs: {sorted_list_of_kpis}")
 
    # -----------------------------
    # Files
    # -----------------------------
    documents_list = list_documents_in_directory(str(user_id))
    selected_files_list = [
        i.split('/')[1] for i in documents_list if 'place' not in i
    ]
 
    # -----------------------------
    # POST handling
    # -----------------------------
    if request.method == "POST":
        data = json.loads(request.body)
        selected_values = data.get("selected_values", [])
        logger.info(f"Selected KPIs: {selected_values}")
 
        extractor = Value_extractor_for_analysis()
        raw_data = extractor.extract_values(
            int(user_id),
            selected_files_list,
            selected_values
        )
 
        logger.info(f"Extracted values: {raw_data}")
 
        # cleaner = clean_dict()
        # ready_data = cleaner.query_chatbot(raw_data)
    
        # ---- TEMP / TEST DATA (as you showed) ----
        # selected_values = ["HEMOGLOBIN", "LYMPHOCYTES - ABSOLUTE COUNT", "HEMATOCRIT(PCV)", "VLDL Cholesterol" ]
        # ready_data = {"HEMOGLOBIN": ["{'2024-08-30': 12.6}", "{'2024-04-15': 14.6}", "{'2023-11-10': 12.5}", "{'2024-05-19': 10.8}"], "LYMPHOCYTES - ABSOLUTE COUNT": ["{'2024-08-30': 1.92}", "{'2023-11-10': 1.61}", "{'2024-05-19': 1.77}"], "HEMATOCRIT(PCV)": ["{'2024-08-30': 45.3}", "{'2023-11-10': 37.4}", "{'2024-05-19': 40.2}"], "VLDL Cholesterol": ["{'2024-04-15': 33.4}"]}
 
        ready_data = clean_extracted_values(raw_data)
        logger.info(f"Cleaned data: {ready_data}")


        # Normalize if string
        if isinstance(ready_data, str):
            ready_data = string_to_dict(ready_data)
 
        if not isinstance(ready_data, dict):
            logger.error(f"Invalid cleaned data format: {ready_data}")
            r = JsonResponse({"chart_data": {}})
            r["Cache-Control"] = "no-store"
            return r
 
        chart_data = {}
 
        # -----------------------------
        # BUILD CHART DATA (FIXED)
        # -----------------------------
        for kpi_name, values_list in ready_data.items():
 
            if kpi_name not in selected_values:
                continue
 
            if not isinstance(values_list, list):
                continue
 
            for value_item in values_list:
                try:
                    # Try JSON first
                    try:
                        parsed = json.loads(value_item)
                    except json.JSONDecodeError:
                        # Fallback for single-quoted dicts
                        parsed = ast.literal_eval(value_item)
 
                    if not isinstance(parsed, dict):
                        continue
 
                    for date, value in parsed.items():
                        chart_data.setdefault(kpi_name, []).append({
                            "name": date,
                            kpi_name: float(value)
                        })
 
                except (ValueError, TypeError, SyntaxError):
                    continue
 
        # -----------------------------
        # Sort by date
        # -----------------------------
        for kpi in chart_data:
            chart_data[kpi].sort(key=lambda x: x["name"])
 
        logger.info(f"Final chart data: {chart_data}")

        resp = JsonResponse({"chart_data": chart_data})
        resp["Cache-Control"] = "no-store"
        return resp
 
    # -----------------------------
    # GET fallback
    # -----------------------------
    return render(request, 'analyse_kpi.html', {
        'selected_files': selected_files_list,
        'sorted_list_of_kpis': sorted_list_of_kpis
    })

def log_out(request):
    global user_id
    user_id = None
    if 'google_oauth_state' in request.session:
        del request.session['google_oauth_state']
    return render(request, 'user_login.html')

def showcase_report(request):
    try:
        document_name = request.GET.get("document_name")
        data = fetch_pdf_view(str(user_id), document_name)
        pdf_bytes = data[1]
        content_type = data[0]

        response = HttpResponse(pdf_bytes, content_type=content_type)
        response['Content-Disposition'] = f'inline; filename="{document_name}"'
        return response

    except Exception as e:
        logger.error(f"Error fetching PDF: {e}")
        raise Http404("Document not found")