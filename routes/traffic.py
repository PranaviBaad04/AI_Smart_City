# routes/traffic.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from routes.auth import login_required, role_required
from database import supabase_client
from ai import groq_service

traffic_bp = Blueprint('traffic', __name__)

@traffic_bp.route('/traffic', methods=['GET'])
@login_required
def list_traffic():
    records = supabase_client.get_all_traffic_data()
    return render_template('traffic.html', traffic_records=records)

@traffic_bp.route('/traffic/add', methods=['POST'])
@login_required
@role_required(['admin', 'officer'])
def add_traffic():
    location = request.form.get('location')
    vehicle_count = request.form.get('vehicle_count')
    avg_speed = request.form.get('avg_speed')
    congestion_level = request.form.get('congestion_level')
    timestamp = request.form.get('timestamp') or None
    
    if not location or not vehicle_count or not avg_speed or not congestion_level:
        flash("All traffic fields are required.", "danger")
        return redirect(url_for('traffic.list_traffic'))
        
    result = supabase_client.add_traffic_data(
        location=location,
        vehicle_count=vehicle_count,
        avg_speed=avg_speed,
        congestion_level=congestion_level,
        timestamp=timestamp
    )
    
    if result:
        flash("Traffic record added successfully.", "success")
    else:
        flash("Failed to add traffic record.", "danger")
        
    return redirect(url_for('traffic.list_traffic'))

@traffic_bp.route('/traffic/update/<record_id>', methods=['POST'])
@login_required
@role_required(['admin', 'officer'])
def update_traffic(record_id):
    location = request.form.get('location')
    vehicle_count = request.form.get('vehicle_count')
    avg_speed = request.form.get('avg_speed')
    congestion_level = request.form.get('congestion_level')
    
    if not location or not vehicle_count or not avg_speed or not congestion_level:
        flash("All fields are required for update.", "danger")
        return redirect(url_for('traffic.list_traffic'))
        
    result = supabase_client.update_traffic_data(
        record_id=record_id,
        location=location,
        vehicle_count=vehicle_count,
        avg_speed=avg_speed,
        congestion_level=congestion_level
    )
    
    if result:
        flash("Traffic record updated successfully.", "success")
    else:
        flash("Failed to update traffic record.", "danger")
        
    return redirect(url_for('traffic.list_traffic'))

@traffic_bp.route('/traffic/delete/<record_id>', methods=['POST', 'GET'])
@login_required
@role_required(['admin', 'officer'])
def delete_traffic(record_id):
    result = supabase_client.delete_traffic_data(record_id)
    if result:
        flash("Traffic record deleted successfully.", "success")
    else:
        flash("Failed to delete traffic record.", "danger")
    return redirect(url_for('traffic.list_traffic'))

@traffic_bp.route('/traffic/ai-analysis', methods=['GET', 'POST'])
@login_required
def traffic_ai_analysis():
    records = supabase_client.get_all_traffic_data()
    
    if not records:
        return jsonify({
            "risk_level": "Low",
            "issues": "No traffic logs found in the database.",
            "recommendations": "Add some traffic logs to run the AI recommendation engine."
        })
        
    # Aggregate data for Groq analysis
    summary = []
    total_vehicles = 0
    total_speed = 0
    high_congestion_count = 0
    
    for r in records[:10]: # Analyze top 10 recent records
        total_vehicles += r.get('vehicle_count', 0)
        total_speed += float(r.get('avg_speed', 0))
        if r.get('congestion_level') == 'High':
            high_congestion_count += 1
        summary.append({
            "location": r.get('location'),
            "vehicle_count": r.get('vehicle_count'),
            "avg_speed": float(r.get('avg_speed')),
            "congestion": r.get('congestion_level')
        })
        
    avg_speed = total_speed / len(records[:10]) if records else 0
    
    data_summary = {
        "recent_logs": summary,
        "metrics_summary": {
            "total_monitored_zones": len(records),
            "average_vehicle_density": total_vehicles / len(records[:10]) if records else 0,
            "overall_average_speed": avg_speed,
            "high_congestion_zones_ratio": f"{high_congestion_count}/{len(records[:10])}"
        }
    }
    
    recommendation = groq_service.get_smart_city_recommendations("traffic", data_summary)
    return jsonify(recommendation)
