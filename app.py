# app.py
import os
import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from config import Config
from routes.auth import auth_bp, login_required, role_required
from routes.traffic import traffic_bp
from routes.pollution import pollution_bp
from routes.services import services_bp
from routes.reports import reports_bp
from database import supabase_client
from ai import explainable_ai, groq_service

app = Flask(__name__)
app.config.from_object(Config)

# Set permanent session lifetime
app.permanent_session_lifetime = datetime.timedelta(days=7)

# Register Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(traffic_bp)
app.register_blueprint(pollution_bp)
app.register_blueprint(services_bp)
app.register_blueprint(reports_bp)

# Context processor to expose session details to all templates
@app.context_processor
def inject_user():
    return dict(current_user=session.get('user'))

# ==========================================
# 1. GENERAL PAGES & DASHBOARD
# ==========================================
@app.route('/')
def index():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('auth.login'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Fetch data to populate KPIs
    traffic_logs = supabase_client.get_all_traffic_data()
    pollution_logs = supabase_client.get_all_pollution_data()
    service_logs = supabase_client.get_all_service_data()
    citizen_logs = supabase_client.get_all_citizen_reports()
    
    # 1. Calculate KPI Values
    total_traffic_density = sum(x.get('vehicle_count', 0) for x in traffic_logs[:5]) if traffic_logs else 0
    
    avg_aqi = int(sum(x.get('aqi', 0) for x in pollution_logs) / len(pollution_logs)) if pollution_logs else 0
    
    # Water Quality Score (derived from Water Supply service log)
    water_logs = [x for x in service_logs if x.get('service_name') == 'Water Supply']
    water_score = 92 # default good score
    if water_logs:
        outages = sum(1 for w in water_logs if w.get('status') in ['Maintenance', 'Outage', 'Under Repair'])
        water_score = max(50, 95 - (outages * 15))
        
    citizen_reports_count = len(citizen_logs)
    pending_services_issues = sum(1 for x in citizen_logs if x.get('status') in ['Pending', 'In Progress'])
    
    kpis = {
        "traffic_density": total_traffic_density,
        "aqi": avg_aqi,
        "water_score": water_score,
        "citizen_reports_count": citizen_reports_count,
        "pending_issues": pending_services_issues
    }
    
    # 2. Renders Dashboard with aggregated logs for Chart.js and Map JS
    return render_template(
        'dashboard.html',
        kpis=kpis,
        traffic_records=traffic_logs[:10],
        pollution_records=pollution_logs[:10],
        service_records=service_logs,
        citizen_reports=citizen_logs[:10]
    )

# ==========================================
# 2. CITIZEN REPORTING SYSTEM ROUTES
# ==========================================
@app.route('/citizen-reports', methods=['GET'])
@login_required
def citizen_reports():
    user = session['user']
    if user.get('role') == 'citizen':
        # Citizens only see their own reports
        reports = supabase_client.get_citizen_reports_by_user(user.get('id'))
    else:
        # Officers/Admins see all reports
        reports = supabase_client.get_all_citizen_reports()
        
    return render_template('citizen_reports.html', reports=reports)

@app.route('/citizen-reports/add', methods=['POST'])
@login_required
def add_citizen_report():
    user = session['user']
    issue_type = request.form.get('issue_type')
    description = request.form.get('description')
    location = request.form.get('location') # Coordinates like "lat,lng,readable_name"
    image_file = request.files.get('image')
    
    if not issue_type or not location:
        flash("Issue type and location coordinates are required.", "danger")
        return redirect(url_for('citizen_reports'))
        
    image_url = None
    if image_file and image_file.filename != '':
        # Call upload script
        image_url = supabase_client.upload_image_to_supabase_or_local(image_file, "citizen_report")
        
    result = supabase_client.add_citizen_report(
        user_id=user.get('id') if user.get('role') == 'citizen' else None,
        issue_type=issue_type,
        description=description,
        location=location,
        image_url=image_url
    )
    
    if result:
        flash("Your report has been submitted successfully.", "success")
    else:
        flash("Failed to submit citizen report. Please try again.", "danger")
        
    return redirect(url_for('citizen_reports'))

@app.route('/citizen-reports/update-status/<report_id>', methods=['POST'])
@login_required
@role_required(['admin', 'officer'])
def update_report_status(report_id):
    status = request.form.get('status')
    if not status:
        return jsonify({"success": False, "error": "Status is required"}), 400
        
    result = supabase_client.update_citizen_report_status(report_id, status)
    if result:
        flash(f"Report status updated to '{status}'.", "success")
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "Database update failed"}), 500

@app.route('/citizen-reports/delete/<report_id>', methods=['POST'])
@login_required
@role_required(['admin'])
def delete_report(report_id):
    result = supabase_client.delete_citizen_report(report_id)
    if result:
        flash("Citizen report deleted successfully.", "success")
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "Database delete failed"}), 500

# ==========================================
# 3. AI RECOMENDATION ENGINE & CHATBOT ROUTES
# ==========================================
@app.route('/ai-insights')
@login_required
def ai_insights():
    # Display general AI dashboard page
    return render_template('ai_insights.html')

@app.route('/api/chatbot', methods=['POST'])
@login_required
def chatbot_endpoint():
    data = request.get_json()
    if not data or 'messages' not in data:
        return jsonify({"error": "Missing messages list"}), 400
        
    response_msg = groq_service.chat_assistant(data['messages'])
    return jsonify({"response": response_msg})

# ==========================================
# 4. EXPLAINABLE AI MODULE ROUTES
# ==========================================
@app.route('/xai', methods=['GET', 'POST'])
@login_required
def xai_explorer():
    # Set default values for initial loads
    traffic_inputs = {"vehicle_count": 130, "avg_speed": 22.5, "hour": 17, "is_weekend": 0}
    pollution_inputs = {"pm25": 42.0, "pm10": 60.5, "co2": 450.0, "noise_level": 70.0}
    
    if request.method == 'POST':
        model_type = request.form.get('model_type', 'traffic')
        
        if model_type == 'traffic':
            traffic_inputs["vehicle_count"] = int(request.form.get('vehicle_count', 130))
            traffic_inputs["avg_speed"] = float(request.form.get('avg_speed', 22.5))
            traffic_inputs["hour"] = int(request.form.get('hour', 17))
            traffic_inputs["is_weekend"] = int(request.form.get('is_weekend', 0))
        elif model_type == 'pollution':
            pollution_inputs["pm25"] = float(request.form.get('pm25', 42.0))
            pollution_inputs["pm10"] = float(request.form.get('pm10', 60.5))
            pollution_inputs["co2"] = float(request.form.get('co2', 450.0))
            pollution_inputs["noise_level"] = float(request.form.get('noise_level', 70.0))
            
    # Calculate SHAP Explanations
    traffic_explanation = explainable_ai.get_traffic_explanation(
        traffic_inputs["vehicle_count"],
        traffic_inputs["avg_speed"],
        traffic_inputs["hour"],
        traffic_inputs["is_weekend"]
    )
    
    pollution_explanation = explainable_ai.get_pollution_explanation(
        pollution_inputs["pm25"],
        pollution_inputs["pm10"],
        pollution_inputs["co2"],
        pollution_inputs["noise_level"]
    )
    
    return render_template(
        'xai.html',
        traffic_inputs=traffic_inputs,
        pollution_inputs=pollution_inputs,
        traffic_xai=traffic_explanation,
        pollution_xai=pollution_explanation
    )

# ==========================================
# 5. SYSTEM SETTINGS
# ==========================================
@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        # Update user session or general information (simulation)
        name = request.form.get('name')
        if name:
            session['user']['name'] = name
            flash("Profile settings updated locally (Simulation).", "success")
        return redirect(url_for('settings'))
    return render_template('settings.html')

# Start Server
if __name__ == '__main__':
    # Ensure static uploads dir exists
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    app.run(host='0.0.0.0', port=5000, debug=True)
