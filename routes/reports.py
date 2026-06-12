# routes/reports.py
import csv
import io
import datetime
from flask import Blueprint, render_template, request, Response, send_file, flash, redirect, url_for
from routes.auth import login_required, role_required
from database import supabase_client
from fpdf import FPDF

reports_bp = Blueprint('reports', __name__)

class SmartCityPDF(FPDF):
    def header(self):
        # Draw background decoration banner
        self.set_fill_color(30, 41, 59) # Dark slate header
        self.rect(0, 0, 210, 35, 'F')
        
        # Smart City Title
        self.set_font('helvetica', 'B', 16)
        self.set_text_color(255, 255, 255)
        self.cell(0, 5, 'METROVILLE SMART CITY ADMINISTRATION', ln=True, align='L')
        self.set_font('helvetica', 'I', 10)
        self.cell(0, 8, 'AI-POWERED INFRASTRUCTURE & UTILITIES AUDIT REPORT', ln=True, align='L')
        self.ln(12)

    def footer(self):
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}} - Generated on {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', align='C')

@reports_bp.route('/reports', methods=['GET'])
@login_required
@role_required(['admin', 'officer'])
def view_reports():
    return render_template('reports.html')

@reports_bp.route('/reports/export/csv', methods=['GET'])
@login_required
@role_required(['admin', 'officer'])
def export_csv():
    dataset = request.args.get('dataset', 'traffic')
    report_type = request.args.get('type', 'daily') # daily, weekly, monthly
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    filename = f"smartcity_{dataset}_{report_type}_{datetime.datetime.now().strftime('%Y%m%d')}.csv"
    
    if dataset == 'traffic':
        records = supabase_client.get_all_traffic_data()
        writer.writerow(['ID', 'Location', 'Vehicle Count', 'Avg Speed (km/h)', 'Congestion Level', 'Timestamp'])
        for r in records:
            writer.writerow([r.get('id'), r.get('location'), r.get('vehicle_count'), r.get('avg_speed'), r.get('congestion_level'), r.get('timestamp')])
            
    elif dataset == 'pollution':
        records = supabase_client.get_all_pollution_data()
        writer.writerow(['ID', 'Location', 'AQI', 'PM2.5', 'PM10', 'CO2', 'Noise Level (dB)', 'Timestamp'])
        for r in records:
            writer.writerow([r.get('id'), r.get('location'), r.get('aqi'), r.get('pm25'), r.get('pm10'), r.get('co2'), r.get('noise_level'), r.get('timestamp')])
            
    elif dataset == 'services':
        records = supabase_client.get_all_service_data()
        writer.writerow(['ID', 'Service Name', 'Location', 'Status', 'Response Time (hrs)', 'Issue Count', 'Timestamp'])
        for r in records:
            writer.writerow([r.get('id'), r.get('service_name'), r.get('location'), r.get('status'), r.get('response_time'), r.get('issue_count'), r.get('timestamp')])
            
    elif dataset == 'citizen_reports':
        records = supabase_client.get_all_citizen_reports()
        writer.writerow(['ID', 'Reporter ID', 'Issue Type', 'Description', 'Location Coordinates', 'Status', 'Timestamp'])
        for r in records:
            writer.writerow([r.get('id'), r.get('user_id'), r.get('issue_type'), r.get('description'), r.get('location'), r.get('status'), r.get('timestamp')])
            
    else:
        flash("Invalid dataset requested for CSV export.", "danger")
        return redirect(url_for('reports.view_reports'))
        
    csv_data = output.getvalue()
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename={filename}"}
    )

@reports_bp.route('/reports/export/pdf', methods=['GET'])
@login_required
@role_required(['admin', 'officer'])
def export_pdf():
    report_type = request.args.get('type', 'daily').capitalize()
    
    # Load all data for report compile
    traffic_logs = supabase_client.get_all_traffic_data()
    pollution_logs = supabase_client.get_all_pollution_data()
    service_logs = supabase_client.get_all_service_data()
    citizen_logs = supabase_client.get_all_citizen_reports()
    
    # Initialize PDF document
    pdf = SmartCityPDF(orientation='P', unit='mm', format='A4')
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Title Spacer
    pdf.ln(5)
    
    # Report Sub-Header Card
    pdf.set_fill_color(240, 245, 250)
    pdf.rect(10, 36, 190, 15, 'F')
    pdf.set_font('helvetica', 'B', 11)
    pdf.set_text_color(30, 41, 59)
    pdf.text(15, 45, f"Report Profile: {report_type} Urban Summary")
    pdf.set_font('helvetica', '', 9)
    pdf.text(130, 45, f"Period Ending: {datetime.datetime.now().strftime('%B %d, %Y')}")
    pdf.ln(15)
    
    # Section 1: Executive KPI Metrics
    pdf.set_font('helvetica', 'B', 12)
    pdf.set_text_color(29, 78, 216) # Accent Blue
    pdf.cell(0, 10, '1. Executive KPI Summary', ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('helvetica', '', 9)
    
    # Calculate stats
    avg_speed = sum(float(x.get('avg_speed', 0)) for x in traffic_logs) / len(traffic_logs) if traffic_logs else 0
    avg_aqi = sum(int(x.get('aqi', 0)) for x in pollution_logs) / len(pollution_logs) if pollution_logs else 0
    pending_complaints = sum(1 for x in citizen_logs if x.get('status') == 'Pending')
    total_issues = sum(int(x.get('issue_count', 0)) for x in service_logs)
    
    # KPI Grid
    col_width = 45
    pdf.set_draw_color(220, 225, 230)
    pdf.set_fill_color(248, 250, 252)
    
    # Box 1
    pdf.cell(col_width, 18, '', border=1, fill=True)
    pdf.set_xy(10, pdf.get_y() - 18)
    pdf.set_font('helvetica', 'B', 7)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(col_width, 6, 'AVG SPEED', ln=True, align='C')
    pdf.set_font('helvetica', 'B', 12)
    pdf.set_text_color(29, 78, 216)
    pdf.cell(col_width, 10, f"{avg_speed:.1f} km/h", align='C')
    pdf.set_xy(10 + col_width, pdf.get_y() - 6)
    
    # Box 2
    pdf.cell(col_width, 18, '', border=1, fill=True)
    pdf.set_xy(10 + col_width, pdf.get_y() - 18)
    pdf.set_font('helvetica', 'B', 7)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(col_width, 6, 'MEAN AQI SCORE', ln=True, align='C')
    pdf.set_font('helvetica', 'B', 12)
    pdf.set_text_color(180, 83, 9) # Gold/Brown
    pdf.cell(col_width, 10, f"{avg_aqi:.1f}", align='C')
    pdf.set_xy(10 + (col_width * 2), pdf.get_y() - 6)
    
    # Box 3
    pdf.cell(col_width, 18, '', border=1, fill=True)
    pdf.set_xy(10 + (col_width * 2), pdf.get_y() - 18)
    pdf.set_font('helvetica', 'B', 7)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(col_width, 6, 'PENDING COMPLAINTS', ln=True, align='C')
    pdf.set_font('helvetica', 'B', 12)
    pdf.set_text_color(220, 38, 38) # Red
    pdf.cell(col_width, 10, f"{pending_complaints}", align='C')
    pdf.set_xy(10 + (col_width * 3), pdf.get_y() - 6)
    
    # Box 4
    pdf.cell(col_width + 10, 18, '', border=1, fill=True)
    pdf.set_xy(10 + (col_width * 3), pdf.get_y() - 18)
    pdf.set_font('helvetica', 'B', 7)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(col_width + 10, 6, 'SERVICE FAULTS PENDING', ln=True, align='C')
    pdf.set_font('helvetica', 'B', 12)
    pdf.set_text_color(31, 41, 55)
    pdf.cell(col_width + 10, 10, f"{total_issues}", align='C')
    
    pdf.ln(18)
    pdf.ln(5)
    
    # Section 2: Traffic Monitoring Reports
    pdf.set_font('helvetica', 'B', 11)
    pdf.set_text_color(29, 78, 216)
    pdf.cell(0, 8, '2. Traffic Congestion Log (Top 5 Active Entries)', ln=True)
    pdf.set_text_color(0, 0, 0)
    
    # Traffic table header
    pdf.set_font('helvetica', 'B', 8)
    pdf.set_fill_color(219, 234, 254)
    pdf.cell(70, 7, 'Location', border=1, fill=True)
    pdf.cell(30, 7, 'Vehicles Count', border=1, fill=True, align='C')
    pdf.cell(30, 7, 'Avg Speed (km/h)', border=1, fill=True, align='C')
    pdf.cell(30, 7, 'Congestion Level', border=1, fill=True, align='C')
    pdf.cell(30, 7, 'Timestamp', border=1, fill=True, align='C')
    pdf.ln(7)
    
    pdf.set_font('helvetica', '', 8)
    for t in traffic_logs[:5]:
        # Clean coordinates out of location if any
        loc = t.get('location', '')
        pdf.cell(70, 6, loc[:38], border=1)
        pdf.cell(30, 6, str(t.get('vehicle_count')), border=1, align='C')
        pdf.cell(30, 6, f"{float(t.get('avg_speed')):.1f}", border=1, align='C')
        pdf.cell(30, 6, t.get('congestion_level'), border=1, align='C')
        ts = t.get('timestamp', '')[:16].replace('T', ' ')
        pdf.cell(30, 6, ts, border=1, align='C')
        pdf.ln(6)
        
    pdf.ln(6)
    
    # Section 3: Pollution Analytics
    pdf.set_font('helvetica', 'B', 11)
    pdf.set_text_color(29, 78, 216)
    pdf.cell(0, 8, '3. Pollution Analytics Log (Top 5 Active Entries)', ln=True)
    pdf.set_text_color(0, 0, 0)
    
    # Pollution table header
    pdf.set_font('helvetica', 'B', 8)
    pdf.set_fill_color(254, 243, 199) # Warm yellow header
    pdf.cell(70, 7, 'Location', border=1, fill=True)
    pdf.cell(20, 7, 'AQI Score', border=1, fill=True, align='C')
    pdf.cell(25, 7, 'PM2.5 (ug/m3)', border=1, fill=True, align='C')
    pdf.cell(25, 7, 'CO2 (ppm)', border=1, fill=True, align='C')
    pdf.cell(25, 7, 'Noise (dB)', border=1, fill=True, align='C')
    pdf.cell(25, 7, 'Timestamp', border=1, fill=True, align='C')
    pdf.ln(7)
    
    pdf.set_font('helvetica', '', 8)
    for p in pollution_logs[:5]:
        loc = p.get('location', '')
        pdf.cell(70, 6, loc[:38], border=1)
        pdf.cell(20, 6, str(p.get('aqi')), border=1, align='C')
        pdf.cell(25, 6, f"{float(p.get('pm25')):.1f}", border=1, align='C')
        pdf.cell(25, 6, f"{float(p.get('co2')):.1f}", border=1, align='C')
        pdf.cell(25, 6, f"{float(p.get('noise_level')):.1f}", border=1, align='C')
        ts = p.get('timestamp', '')[:16].replace('T', ' ')
        pdf.cell(25, 6, ts, border=1, align='C')
        pdf.ln(6)
        
    pdf.ln(6)
    
    # Section 4: Public Services Status
    pdf.set_font('helvetica', 'B', 11)
    pdf.set_text_color(29, 78, 216)
    pdf.cell(0, 8, '4. Public Utility Status (All Monitored Sectors)', ln=True)
    pdf.set_text_color(0, 0, 0)
    
    # Services table header
    pdf.set_font('helvetica', 'B', 8)
    pdf.set_fill_color(241, 245, 249)
    pdf.cell(50, 7, 'Service Name', border=1, fill=True)
    pdf.cell(60, 7, 'Assigned Sector Location', border=1, fill=True)
    pdf.cell(30, 7, 'Operating Status', border=1, fill=True, align='C')
    pdf.cell(25, 7, 'Resp Time (hrs)', border=1, fill=True, align='C')
    pdf.cell(25, 7, 'Active Faults', border=1, fill=True, align='C')
    pdf.ln(7)
    
    pdf.set_font('helvetica', '', 8)
    for s in service_logs:
        pdf.cell(50, 6, s.get('service_name'), border=1)
        pdf.cell(60, 6, s.get('location')[:32], border=1)
        pdf.cell(30, 6, s.get('status'), border=1, align='C')
        pdf.cell(25, 6, f"{float(s.get('response_time')):.1f}", border=1, align='C')
        pdf.cell(25, 6, str(s.get('issue_count')), border=1, align='C')
        pdf.ln(6)
        
    pdf.ln(6)
    
    # Section 5: Citizen Reports Action Ledger
    pdf.set_font('helvetica', 'B', 11)
    pdf.set_text_color(29, 78, 216)
    pdf.cell(0, 8, '5. Citizen Service Complaint Ledger (Recent Active)', ln=True)
    pdf.set_text_color(0, 0, 0)
    
    # Citizen complaints table
    pdf.set_font('helvetica', 'B', 8)
    pdf.set_fill_color(254, 226, 226) # Warm red header
    pdf.cell(40, 7, 'Issue Type', border=1, fill=True)
    pdf.cell(60, 7, 'Description', border=1, fill=True)
    pdf.cell(50, 7, 'Reported Location', border=1, fill=True)
    pdf.cell(20, 7, 'Status', border=1, fill=True, align='C')
    pdf.cell(20, 7, 'Posted', border=1, fill=True, align='C')
    pdf.ln(7)
    
    pdf.set_font('helvetica', '', 8)
    for c in citizen_logs[:6]:
        pdf.cell(40, 6, c.get('issue_type'), border=1)
        desc = c.get('description', '')
        pdf.cell(60, 6, desc[:32] + ('...' if len(desc) > 32 else ''), border=1)
        # Parse coordinates out if stored as "lat,lng,text"
        loc_parts = c.get('location', '').split(',', 2)
        loc_text = loc_parts[-1] if len(loc_parts) == 3 else c.get('location', '')
        pdf.cell(50, 6, loc_text[:28], border=1)
        pdf.cell(20, 6, c.get('status'), border=1, align='C')
        ts = c.get('timestamp', '')[:10]
        pdf.cell(20, 6, ts, border=1, align='C')
        pdf.ln(6)
        
    pdf.ln(10)
    
    # Add a closing signoff box
    pdf.set_draw_color(150, 150, 150)
    pdf.set_fill_color(245, 245, 245)
    pdf.cell(0, 15, 'Authorized by Metroville AI Smart City Auditor Console. Valid without manual signature.', border=1, fill=True, align='C')
    
    # Save PDF contents to buffer and return
    pdf_buffer = pdf.output(dest='S')
    
    # Create file response
    return Response(
        pdf_buffer,
        mimetype="application/pdf",
        headers={"Content-disposition": f"attachment; filename=SmartCity_{report_type}_AuditReport_{datetime.datetime.now().strftime('%Y%m%d')}.pdf"}
    )
