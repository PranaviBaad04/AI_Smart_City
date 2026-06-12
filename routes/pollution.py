# routes/pollution.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from routes.auth import login_required, role_required
from database import supabase_client
from ai import groq_service

pollution_bp = Blueprint('pollution', __name__)

@pollution_bp.route('/pollution', methods=['GET'])
@login_required
def list_pollution():
    records = supabase_client.get_all_pollution_data()
    return render_template('pollution.html', pollution_records=records)

@pollution_bp.route('/pollution/add', methods=['POST'])
@login_required
@role_required(['admin', 'officer'])
def add_pollution():
    location = request.form.get('location')
    aqi = request.form.get('aqi')
    pm25 = request.form.get('pm25')
    pm10 = request.form.get('pm10')
    co2 = request.form.get('co2')
    noise_level = request.form.get('noise_level')
    timestamp = request.form.get('timestamp') or None
    
    if not location or not aqi or not pm25 or not pm10 or not co2 or not noise_level:
        flash("All pollution metrics are required.", "danger")
        return redirect(url_for('pollution.list_pollution'))
        
    result = supabase_client.add_pollution_data(
        location=location,
        aqi=aqi,
        pm25=pm25,
        pm10=pm10,
        co2=co2,
        noise_level=noise_level,
        timestamp=timestamp
    )
    
    if result:
        flash("Pollution analytics record added successfully.", "success")
    else:
        flash("Failed to add pollution record.", "danger")
        
    return redirect(url_for('pollution.list_pollution'))

@pollution_bp.route('/pollution/update/<record_id>', methods=['POST'])
@login_required
@role_required(['admin', 'officer'])
def update_pollution(record_id):
    location = request.form.get('location')
    aqi = request.form.get('aqi')
    pm25 = request.form.get('pm25')
    pm10 = request.form.get('pm10')
    co2 = request.form.get('co2')
    noise_level = request.form.get('noise_level')
    
    if not location or not aqi or not pm25 or not pm10 or not co2 or not noise_level:
        flash("All fields are required for update.", "danger")
        return redirect(url_for('pollution.list_pollution'))
        
    result = supabase_client.update_pollution_data(
        record_id=record_id,
        location=location,
        aqi=aqi,
        pm25=pm25,
        pm10=pm10,
        co2=co2,
        noise_level=noise_level
    )
    
    if result:
        flash("Pollution record updated successfully.", "success")
    else:
        flash("Failed to update pollution record.", "danger")
        
    return redirect(url_for('pollution.list_pollution'))

@pollution_bp.route('/pollution/delete/<record_id>', methods=['POST', 'GET'])
@login_required
@role_required(['admin', 'officer'])
def delete_pollution(record_id):
    result = supabase_client.delete_pollution_data(record_id)
    if result:
        flash("Pollution record deleted successfully.", "success")
    else:
        flash("Failed to delete pollution record.", "danger")
    return redirect(url_for('pollution.list_pollution'))

@pollution_bp.route('/pollution/ai-analysis', methods=['GET', 'POST'])
@login_required
def pollution_ai_analysis():
    records = supabase_client.get_all_pollution_data()
    
    if not records:
        return jsonify({
            "risk_level": "Low",
            "issues": "No pollution records found.",
            "recommendations": "Add some pollution monitoring records to check environmental alerts."
        })
        
    summary = []
    total_aqi = 0
    high_aqi_count = 0
    
    for r in records[:10]: # Analyze top 10 recent records
        aqi_val = int(r.get('aqi', 0))
        total_aqi += aqi_val
        if aqi_val > 100:
            high_aqi_count += 1
        summary.append({
            "location": r.get('location'),
            "aqi": aqi_val,
            "pm25": float(r.get('pm25', 0)),
            "pm10": float(r.get('pm10', 0)),
            "co2": float(r.get('co2', 0)),
            "noise": float(r.get('noise_level', 0))
        })
        
    avg_aqi = total_aqi / len(records[:10])
    
    data_summary = {
        "recent_pollution_logs": summary,
        "metrics_summary": {
            "monitored_stations": len(records),
            "average_aqi": avg_aqi,
            "unhealthy_stations_ratio": f"{high_aqi_count}/{len(records[:10])}"
        }
    }
    
    recommendation = groq_service.get_smart_city_recommendations("pollution", data_summary)
    return jsonify(recommendation)
