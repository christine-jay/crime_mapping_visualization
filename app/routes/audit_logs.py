from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app import mysql
from datetime import datetime

audit_logs = Blueprint('audit_logs', __name__)

@audit_logs.route('/audit-logs')
@login_required
def view_audit_logs():
    try:
        # Get page number from query parameters, default to 1
        page = request.args.get('page', 1, type=int)
        per_page = 20  # Number of logs per page
        
        # Calculate offset for pagination
        offset = (page - 1) * per_page
        
        # Get total count of logs
        cur = mysql.connection.cursor()
        cur.execute("SELECT COUNT(*) FROM audit_logs")
        total_logs = cur.fetchone()[0]
        
        # Get logs with user information
        cur.execute("""
            SELECT 
                al.log_id,
                al.timestamp,
                al.action,
                al.table_affected,
                u.username,
                u.name
            FROM audit_logs al
            LEFT JOIN user u ON al.user_id = u.user_id
            ORDER BY al.timestamp DESC
            LIMIT %s OFFSET %s
        """, (per_page, offset))
        logs = cur.fetchall()
        
        # Calculate total pages
        total_pages = (total_logs + per_page - 1) // per_page
        
        # Format the logs for display
        formatted_logs = []
        for log in logs:
            formatted_logs.append({
                'log_id': log[0],
                'timestamp': log[1].strftime('%Y-%m-%d %H:%M:%S'),
                'action': log[2],
                'table_affected': log[3],
                'username': log[4] or 'System',
                'name': log[5] or 'System'
            })
        
        cur.close()
        
        return render_template('audit_logs.html',
                             logs=formatted_logs,
                             current_page=page,
                             total_pages=total_pages)
                             
    except Exception as e:
        flash('Error retrieving audit logs', 'error')
        return redirect(url_for('main.dashboard')) 