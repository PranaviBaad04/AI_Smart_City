# routes/services.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from routes.auth import login_required, role_required
from database import supabase_client
from ai import groq_service

services_bp = Blueprint('services', __name__)

@services_bp.route('/services', methods=['GET'])
@login_required
def list_services():
    records = supabase_client.get_all_service_data()
    return render_template('services.html', service_records=records)

@services_bp.route('/services/add', methods=['POST'])
@login_required
@role_required(['admin', 'officer'])
def add_service():
    service_name = request.form.get('service_name')
    location = request.form.get('location')
    status = request.form.get('status')
    response_time = request.form.get('response_time')
    issue_count = request.form.get('issue_count')
    
    if not service_name or not location or not status or not response_time or not issue_count:
        flash("All utility status fields are required.", "danger")
        return redirect(url_for('services.list_services'))
        
    result = supabase_client.add_service_data(
        service_name=service_name,
        location=location,
        status=status,
        response_time=response_time,
        issue_count=issue_count
    )
    
    if result:
        flash("Utility status log added successfully.", "success")
    else:
        flash("Failed to add utility status log.", "danger")
        
    return redirect(url_for('services.list_services'))

@services_bp.route('/services/update/<record_id>', methods=['POST'])
@login_required
@role_required(['admin', 'officer'])
def update_service(record_id):
    service_name = request.form.get('service_name')
    location = request.form.get('location')
    status = request.form.get('status')
    response_time = request.form.get('response_time')
    issue_count = request.form.get('issue_count')
    
    if not service_name or not location or not status or not response_time or not issue_count:
        flash("All fields are required for update.", "danger")
        return redirect(url_for('services.list_services'))
        
    result = supabase_client.update_service_data(
        record_id=record_id,
        service_name=service_name,
        location=location,
        status=status,
        response_time=response_time,
        issue_count=issue_count
    )
    
    if result:
        flash("Utility status record updated successfully.", "success")
    else:
        flash("Failed to update utility record.", "danger")
        
    return redirect(url_for('services.list_services'))

@services_bp.route('/services/delete/<record_id>', methods=['POST', 'GET'])
@login_required
@role_required(['admin', 'officer'])
def delete_service(record_id):
    result = supabase_client.delete_service_data(record_id)
    if result:
        flash("Utility status record deleted successfully.", "success")
    else:
        flash("Failed to delete utility record.", "danger")
    return redirect(url_for('services.list_services'))

@services_bp.route('/services/ai-analysis', methods=['GET', 'POST'])
@login_required
def services_ai_analysis():
    records = supabase_client.get_all_service_data()
    
    if not records:
        return jsonify({
            "risk_level": "Low",
            "issues": "No municipal utility logs found.",
            "recommendations": "Add some public utility status logs to check performance metrics."
        })
        
    summary = []
    total_time = 0
    total_issues = 0
    outages = 0
    
    for r in records:
        resp_time = float(r.get('response_time', 0))
        issues = int(r.get('issue_count', 0))
        total_time += resp_time
        total_issues += issues
        if r.get('status') in ['Outage', 'Under Repair']:
            outages += 1
        summary.append({
            "service": r.get('service_name'),
            "location": r.get('location'),
            "status": r.get('status'),
            "response_time_hr": resp_time,
            "issues": issues
        })
        
    avg_resp = total_time / len(records) if records else 0
    
    data_summary = {
        "services_overview": summary,
        "metrics_summary": {
            "total_monitored_sectors": len(records),
            "average_response_time_hours": avg_resp,
            "total_pending_issues": total_issues,
            "active_outages_or_repairs": outages
        }
    }
    
    recommendation = groq_service.get_smart_city_recommendations("services", data_summary)
    return jsonify(recommendation)
