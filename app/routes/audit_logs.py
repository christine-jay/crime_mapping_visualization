from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required, current_user
from app import mysql
from datetime import datetime, timedelta
import traceback
from functools import wraps
import json
from config import Config

audit_logs = Blueprint('audit_logs', __name__)

def get_db_connection():
    """Helper function to get database connection"""
    return mysql.connector.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DB
    )

def log_activity(action_type, module, description):
    """Helper function to log user activities"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO audit_logs 
            (user_id, action, table_affected, timestamp)
            VALUES (%s, %s, %s, NOW())
        """, (
            current_user.id,
            action_type,
            module
        ))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        current_app.logger.error(f"Error logging activity: {str(e)}\n{traceback.format_exc()}")

def audit_log(action_type, module):
    """Decorator to automatically log function calls"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Get function arguments for logging
                arg_dict = {}
                if args:
                    arg_dict['args'] = [str(arg) for arg in args]
                if kwargs:
                    arg_dict['kwargs'] = {k: str(v) for k, v in kwargs.items()}
                
                description = f"Function {f.__name__} called"
                if arg_dict:
                    description += f" with parameters: {json.dumps(arg_dict)}"
                
                log_activity(action_type, module, description)
                return f(*args, **kwargs)
            except Exception as e:
                current_app.logger.error(f"Error in audit_log decorator: {str(e)}\n{traceback.format_exc()}")
                return f(*args, **kwargs)
        return decorated_function
    return decorator

@audit_logs.route('/audit-logs')
@login_required
def view_audit_logs():
    """View audit logs with filtering and pagination"""
    try:
        # Get filter parameters
        action_type = request.args.get('action_type', '')
        module = request.args.get('module', '')
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')
        page = request.args.get('page', 1, type=int)
        per_page = 20

        # Build query
        query = """
            SELECT 
                al.log_id,
                al.timestamp,
                al.action,
                al.table_affected,
                u.username,
                u.name
            FROM audit_logs al
            LEFT JOIN user u ON al.user_id = u.user_id
            WHERE 1=1
        """
        params = []

        if action_type:
            query += " AND al.action = %s"
            params.append(action_type)
        if module:
            query += " AND al.table_affected = %s"
            params.append(module)
        if start_date:
            query += " AND DATE(al.timestamp) >= %s"
            params.append(start_date)
        if end_date:
            query += " AND DATE(al.timestamp) <= %s"
            params.append(end_date)

        # Get total count
        count_query = f"SELECT COUNT(*) FROM ({query}) as count_query"
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(count_query, params)
        total_records = cur.fetchone()[0]

        # Add pagination
        query += " ORDER BY al.timestamp DESC LIMIT %s OFFSET %s"
        params.extend([per_page, (page - 1) * per_page])

        # Execute main query
        cur.execute(query, params)
        logs = cur.fetchall()

        # Get unique modules and action types for filter dropdowns
        cur.execute("SELECT DISTINCT table_affected FROM audit_logs ORDER BY table_affected")
        modules = [row[0] for row in cur.fetchall()]
        
        cur.execute("SELECT DISTINCT action FROM audit_logs ORDER BY action")
        action_types = [row[0] for row in cur.fetchall()]
        
        cur.close()
        conn.close()

        # Format logs for display
        formatted_logs = []
        for log in logs:
            formatted_logs.append({
                'id': log[0],
                'timestamp': log[1].strftime('%Y-%m-%d %H:%M:%S'),
                'action_type': log[2],
                'module': log[3],
                'username': log[4] or 'System',
                'name': log[5] or 'System'
            })

        # Calculate pagination
        total_pages = (total_records + per_page - 1) // per_page

        return render_template(
            'audit_logs.html',
            logs=formatted_logs,
            current_page=page,
            total_pages=total_pages,
            modules=modules,
            action_types=action_types,
            selected_action_type=action_type,
            selected_module=module,
            start_date=start_date,
            end_date=end_date
        )

    except Exception as e:
        current_app.logger.error(f"Error in view_audit_logs: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'error': 'An error occurred while retrieving audit logs',
            'details': str(e)
        }), 500

@audit_logs.route('/api/audit-logs/stats')
@login_required
def get_audit_stats():
    """Get statistics about audit logs"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get total count
        cur.execute("SELECT COUNT(*) FROM audit_logs")
        total_logs = cur.fetchone()[0]
        
        # Get logs by action type
        cur.execute("""
            SELECT action, COUNT(*) as count 
            FROM audit_logs 
            GROUP BY action 
            ORDER BY count DESC
        """)
        action_stats = {row[0]: row[1] for row in cur.fetchall()}
        
        # Get logs by module (table_affected)
        cur.execute("""
            SELECT table_affected, COUNT(*) as count 
            FROM audit_logs 
            GROUP BY table_affected 
            ORDER BY count DESC
        """)
        module_stats = {row[0]: row[1] for row in cur.fetchall()}
        
        # Get recent activity (last 24 hours)
        cur.execute("""
            SELECT COUNT(*) 
            FROM audit_logs 
            WHERE timestamp >= NOW() - INTERVAL 24 HOUR
        """)
        recent_activity = cur.fetchone()[0]
        
        cur.close()
        conn.close()
        
        return jsonify({
            'total_logs': total_logs,
            'action_stats': action_stats,
            'module_stats': module_stats,
            'recent_activity': recent_activity
        })
        
    except Exception as e:
        current_app.logger.error(f"Error in get_audit_stats: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'error': 'An error occurred while retrieving audit statistics',
            'details': str(e)
        }), 500 