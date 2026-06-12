# database/supabase_client.py
import os
import datetime
from supabase import create_client, Client
from config import Config
from werkzeug.utils import secure_filename

# Initialize Supabase Client
if not Config.SUPABASE_URL or not Config.SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables.")

supabase: Client = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)

# ==========================================
# 1. USER AUTHENTICATION QUERIES
# ==========================================
def get_user_by_email(email):
    try:
        response = supabase.table("users").select("*").eq("email", email.strip().lower()).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        print(f"[Supabase DB Error] get_user_by_email: {e}")
        return None

def get_user_by_id(user_id):
    try:
        response = supabase.table("users").select("*").eq("id", user_id).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        print(f"[Supabase DB Error] get_user_by_id: {e}")
        return None

def create_user(name, email, password_hash, role="citizen"):
    try:
        data = {
            "name": name.strip(),
            "email": email.strip().lower(),
            "password_hash": password_hash,
            "role": role
        }
        response = supabase.table("users").insert(data).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        print(f"[Supabase DB Error] create_user: {e}")
        return None

# ==========================================
# 2. TRAFFIC MONITORING QUERIES
# ==========================================
def get_all_traffic_data():
    try:
        response = supabase.table("traffic_data").select("*").order("timestamp", desc=True).execute()
        return response.data or []
    except Exception as e:
        print(f"[Supabase DB Error] get_all_traffic_data: {e}")
        return []

def add_traffic_data(location, vehicle_count, avg_speed, congestion_level, timestamp=None):
    try:
        data = {
            "location": location.strip(),
            "vehicle_count": int(vehicle_count),
            "avg_speed": float(avg_speed),
            "congestion_level": congestion_level
        }
        if timestamp:
            data["timestamp"] = timestamp
        response = supabase.table("traffic_data").insert(data).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"[Supabase DB Error] add_traffic_data: {e}")
        return None

def update_traffic_data(record_id, location, vehicle_count, avg_speed, congestion_level, timestamp=None):
    try:
        data = {
            "location": location.strip(),
            "vehicle_count": int(vehicle_count),
            "avg_speed": float(avg_speed),
            "congestion_level": congestion_level
        }
        if timestamp:
            data["timestamp"] = timestamp
        response = supabase.table("traffic_data").update(data).eq("id", record_id).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"[Supabase DB Error] update_traffic_data: {e}")
        return None

def delete_traffic_data(record_id):
    try:
        response = supabase.table("traffic_data").delete().eq("id", record_id).execute()
        return True
    except Exception as e:
        print(f"[Supabase DB Error] delete_traffic_data: {e}")
        return False

# ==========================================
# 3. POLLUTION ANALYTICS QUERIES
# ==========================================
def get_all_pollution_data():
    try:
        response = supabase.table("pollution_data").select("*").order("timestamp", desc=True).execute()
        return response.data or []
    except Exception as e:
        print(f"[Supabase DB Error] get_all_pollution_data: {e}")
        return []

def add_pollution_data(location, aqi, pm25, pm10, co2, noise_level, timestamp=None):
    try:
        data = {
            "location": location.strip(),
            "aqi": int(aqi),
            "pm25": float(pm25),
            "pm10": float(pm10),
            "co2": float(co2),
            "noise_level": float(noise_level)
        }
        if timestamp:
            data["timestamp"] = timestamp
        response = supabase.table("pollution_data").insert(data).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"[Supabase DB Error] add_pollution_data: {e}")
        return None

def update_pollution_data(record_id, location, aqi, pm25, pm10, co2, noise_level, timestamp=None):
    try:
        data = {
            "location": location.strip(),
            "aqi": int(aqi),
            "pm25": float(pm25),
            "pm10": float(pm10),
            "co2": float(co2),
            "noise_level": float(noise_level)
        }
        if timestamp:
            data["timestamp"] = timestamp
        response = supabase.table("pollution_data").update(data).eq("id", record_id).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"[Supabase DB Error] update_pollution_data: {e}")
        return None

def delete_pollution_data(record_id):
    try:
        response = supabase.table("pollution_data").delete().eq("id", record_id).execute()
        return True
    except Exception as e:
        print(f"[Supabase DB Error] delete_pollution_data: {e}")
        return False

# ==========================================
# 4. PUBLIC SERVICES QUERIES
# ==========================================
def get_all_service_data():
    try:
        response = supabase.table("service_data").select("*").order("service_name", desc=False).execute()
        return response.data or []
    except Exception as e:
        print(f"[Supabase DB Error] get_all_service_data: {e}")
        return []

def add_service_data(service_name, location, status, response_time, issue_count):
    try:
        data = {
            "service_name": service_name,
            "location": location.strip(),
            "status": status,
            "response_time": float(response_time),
            "issue_count": int(issue_count)
        }
        response = supabase.table("service_data").insert(data).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"[Supabase DB Error] add_service_data: {e}")
        return None

def update_service_data(record_id, service_name, location, status, response_time, issue_count):
    try:
        data = {
            "service_name": service_name,
            "location": location.strip(),
            "status": status,
            "response_time": float(response_time),
            "issue_count": int(issue_count)
        }
        response = supabase.table("service_data").update(data).eq("id", record_id).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"[Supabase DB Error] update_service_data: {e}")
        return None

def delete_service_data(record_id):
    try:
        response = supabase.table("service_data").delete().eq("id", record_id).execute()
        return True
    except Exception as e:
        print(f"[Supabase DB Error] delete_service_data: {e}")
        return False

# ==========================================
# 5. CITIZEN REPORTS QUERIES & STORAGE
# ==========================================
def get_all_citizen_reports():
    try:
        response = supabase.table("citizen_reports").select("*, users(name)").order("timestamp", desc=True).execute()
        return response.data or []
    except Exception as e:
        print(f"[Supabase DB Error] get_all_citizen_reports: {e}")
        return []

def get_citizen_reports_by_user(user_id):
    try:
        response = supabase.table("citizen_reports").select("*").eq("user_id", user_id).order("timestamp", desc=True).execute()
        return response.data or []
    except Exception as e:
        print(f"[Supabase DB Error] get_citizen_reports_by_user: {e}")
        return []

def add_citizen_report(user_id, issue_type, description, location, image_url=None, status="Pending"):
    try:
        data = {
            "issue_type": issue_type,
            "description": description.strip() if description else "",
            "location": location.strip(),
            "status": status
        }
        if user_id:
            data["user_id"] = user_id
        if image_url:
            data["image_url"] = image_url
            
        response = supabase.table("citizen_reports").insert(data).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"[Supabase DB Error] add_citizen_report: {e}")
        return None

def update_citizen_report_status(report_id, status):
    try:
        data = {"status": status}
        response = supabase.table("citizen_reports").update(data).eq("id", report_id).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"[Supabase DB Error] update_citizen_report_status: {e}")
        return None

def delete_citizen_report(report_id):
    try:
        response = supabase.table("citizen_reports").delete().eq("id", report_id).execute()
        return True
    except Exception as e:
        print(f"[Supabase DB Error] delete_citizen_report: {e}")
        return False

# Helper for image upload with fallback to local server directory
def upload_image_to_supabase_or_local(file_obj, filename_prefix="report"):
    if not file_obj:
        return None
        
    filename = secure_filename(f"{filename_prefix}_{int(datetime.datetime.now().timestamp())}_{file_obj.filename}")
    
    # Try Supabase Storage Upload
    try:
        # Check if bucket exists, or try to create it
        bucket_name = "citizen-reports"
        try:
            # Check if bucket exists by listing files in it (will error if doesn't exist)
            supabase.storage.from_(bucket_name).list()
        except Exception:
            # Attempt to create bucket
            try:
                supabase.storage.create_bucket(bucket_name, options={"public": True})
            except Exception as bucket_err:
                print(f"[Supabase Storage] Failed to create bucket: {bucket_err}. Using local fallback.")
                raise bucket_err
        
        # Read file binary contents
        file_bytes = file_obj.read()
        file_obj.seek(0) # reset pointer
        
        # Upload
        supabase.storage.from_(bucket_name).upload(
            path=filename,
            file=file_bytes,
            file_options={"content-type": file_obj.content_type}
        )
        
        # Get Public URL
        public_url = supabase.storage.from_(bucket_name).get_public_url(filename)
        print(f"[Supabase Storage] Successfully uploaded to bucket '{bucket_name}': {public_url}")
        return public_url
        
    except Exception as e:
        print(f"[Supabase Storage Error] File upload failed: {e}. Falling back to local upload.")
        # Local upload fallback
        upload_dir = Config.UPLOAD_FOLDER
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir, exist_ok=True)
            
        file_path = os.path.join(upload_dir, filename)
        file_obj.save(file_path)
        
        # Return web-accessible path
        return f"/static/uploads/{filename}"
