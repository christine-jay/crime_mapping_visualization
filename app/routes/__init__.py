from flask import Blueprint, jsonify, request, send_from_directory, render_template
from flask_login import login_required, current_user
import mysql.connector
from config import Config
import os

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@login_required
def dashboard():
    if hasattr(current_user, 'role') and current_user.role == 'user':
        return render_template('dashboard_user.html')
    return render_template('dashboard.html')

@main_bp.route('/crime-map')
@login_required
def crime_map():
    return render_template('crime_map.html')

@main_bp.route('/analytics')
@login_required
def analytics():
    return render_template('analytics.html')

# API endpoints for React frontend
@main_bp.route('/api/dashboard/stats')
@login_required
def api_dashboard_stats():
    try:
        conn = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DB
        )
        cursor = conn.cursor(dictionary=True)
        
        # Get total crimes
        cursor.execute("SELECT COUNT(*) as total FROM crime_report")
        total_crimes = cursor.fetchone()['total']
        
        # Get total barangays
        cursor.execute("SELECT COUNT(*) as total FROM barangay")
        total_barangays = cursor.fetchone()['total']
        
        # Get this month's crimes
        cursor.execute("""
            SELECT COUNT(*) as total FROM crime_report 
            WHERE MONTH(date_reported) = MONTH(CURRENT_DATE()) 
            AND YEAR(date_reported) = YEAR(CURRENT_DATE())
        """)
        this_month = cursor.fetchone()['total']
        
        # Get last month's crimes
        cursor.execute("""
            SELECT COUNT(*) as total FROM crime_report 
            WHERE MONTH(date_reported) = MONTH(DATE_SUB(CURRENT_DATE(), INTERVAL 1 MONTH)) 
            AND YEAR(date_reported) = YEAR(DATE_SUB(CURRENT_DATE(), INTERVAL 1 MONTH))
        """)
        last_month = cursor.fetchone()['total']
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'totalCrimes': total_crimes,
            'totalBarangays': total_barangays,
            'thisMonth': this_month,
            'lastMonth': last_month
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main_bp.route('/api/crimes')
@login_required
def api_crimes():
    try:
        conn = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DB
        )
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT * FROM crime_report 
            ORDER BY date_reported DESC
        """)
        crimes = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify(crimes)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main_bp.route('/api/crimes', methods=['POST'])
@login_required
def api_create_crime():
    try:
        data = request.get_json()
        
        conn = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DB
        )
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO crime_report (
                barangay_name, type_of_place, date_reported, time_reported,
                date_committed, time_committed, offense, type_of_crime,
                classification_of_crime, victim, suspect, narrative, status, batch_id
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            data.get('barangay_name'),
            data.get('type_of_place'),
            data.get('date_reported'),
            data.get('time_reported'),
            data.get('date_committed'),
            data.get('time_committed'),
            data.get('offense'),
            data.get('type_of_crime'),
            data.get('classification_of_crime'),
            data.get('victim'),
            data.get('suspect'),
            data.get('narrative'),
            data.get('status', 'Pending'),
            data.get('batch_id', 1)
        ))
        
        crime_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'id': crime_id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main_bp.route('/api/barangays')
@login_required
def api_barangays():
    try:
        conn = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DB
        )
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM barangay ORDER BY barangay_name")
        barangays = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify(barangays)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main_bp.route('/api/barangays', methods=['POST'])
@login_required
def api_create_barangay():
    try:
        data = request.get_json()
        
        conn = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DB
        )
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO barangay (barangay_name, barangay_population, barangay_district)
            VALUES (%s, %s, %s)
        """, (
            data.get('barangay_name'),
            data.get('barangay_population'),
            data.get('barangay_district')
        ))
        
        barangay_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'id': barangay_id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main_bp.route('/api/audit-logs')
@login_required
def api_audit_logs():
    try:
        conn = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DB
        )
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT al.*, u.username, u.name 
            FROM audit_logs al 
            JOIN user u ON al.user_id = u.user_id 
            ORDER BY al.created_at DESC
        """)
        logs = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify(logs)
    except Exception as e:
        return jsonify({'error': str(e)}), 500 