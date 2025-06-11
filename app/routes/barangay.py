from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
import mysql.connector
from config import Config

barangay_bp = Blueprint('barangay', __name__)

@barangay_bp.route('/barangays')
@login_required
def list_barangays():
    conn = mysql.connector.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DB
    )
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM barangay ORDER BY barangay_district, barangay_name')
    barangays = cursor.fetchall()
    
    # Format data for frontend
    barangays_by_district = {}
    for barangay in barangays:
        district = barangay['barangay_district']
        if district not in barangays_by_district:
            barangays_by_district[district] = []
        barangays_by_district[district].append({
            'id': barangay['barangay_id'],
            'name': barangay['barangay_name'],
            'population': barangay['barangay_population']
        })
    
    cursor.close()
    conn.close()
    return render_template('barangays.html', barangays_by_district=barangays_by_district)

@barangay_bp.route('/barangay/add', methods=['GET', 'POST'])
@login_required
def add_barangay():
    if request.method == 'POST':
        name = request.form['barangay_name']
        population = request.form['barangay_population']
        district = request.form['barangay_district']
        conn = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DB
        )
        cursor = conn.cursor()
        cursor.execute('INSERT INTO barangay (barangay_name, barangay_population, barangay_district) VALUES (%s, %s, %s)', (name, population, district))
        conn.commit()
        cursor.close()
        conn.close()
        flash('Barangay added!', 'success')
        return redirect(url_for('barangay.list_barangays'))
    return render_template('add_barangay.html')

@barangay_bp.route('/barangay/update_population', methods=['POST'])
@login_required
def update_population():
    try:
        barangay_id = request.form.get('barangay_id')
        population = request.form.get('population')
        
        if not barangay_id or not population:
            flash('Missing required fields', 'danger')
            return redirect(url_for('barangay.list_barangays'))
        
        conn = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DB
        )
        cursor = conn.cursor()
        
        # Update the population
        cursor.execute('UPDATE barangay SET barangay_population = %s WHERE barangay_id = %s',
                      (population, barangay_id))
        conn.commit()
        
        # Log the update in audit_logs
        cursor.execute('''
            INSERT INTO audit_logs (user_id, action, details, timestamp)
            VALUES (%s, %s, %s, NOW())
        ''', (current_user.id, 'UPDATE_POPULATION', f'Updated population for barangay ID {barangay_id} to {population}'))
        conn.commit()
        
        cursor.close()
        conn.close()
        
        flash('Population updated successfully!', 'success')
        return redirect(url_for('barangay.list_barangays'))
        
    except Exception as e:
        flash(f'Error updating population: {str(e)}', 'danger')
        return redirect(url_for('barangay.list_barangays')) 