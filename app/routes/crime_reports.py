from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
import mysql.connector
import pandas as pd
import random
import datetime
from config import Config

crime_reports_bp = Blueprint('crime_reports', __name__)

@crime_reports_bp.route('/upload_crime_report', methods=['GET', 'POST'])
@login_required
def upload_crime_report():
    if request.method == 'POST':
        file = request.files['file']
        if file and file.filename.endswith('.xlsx'):
            df = pd.read_excel(file)
            batch_id = int(datetime.datetime.now().timestamp())
            conn = mysql.connector.connect(
                host=Config.MYSQL_HOST,
                user=Config.MYSQL_USER,
                password=Config.MYSQL_PASSWORD,
                database=Config.MYSQL_DB
            )
            cursor = conn.cursor()
            for _, row in df.iterrows():
                cursor.execute('''INSERT INTO crime_report (barangay_name, type_of_place, date_reported, time_reported, date_committed, time_committed, offense, type_of_crime, classification_of_crime, victim, suspect, narrative, status, batch_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                    (row['barangay_name'], row['type_of_place'], row['date_reported'], row['time_reported'], row['date_committed'], row['time_committed'], row['offense'], row['type_of_crime'], row['classification_of_crime'], row['victim'], row['suspect'], row['narrative'], row['status'], batch_id))
            conn.commit()
            cursor.close()
            conn.close()
            flash('Crime reports uploaded successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Please upload a valid Excel (.xlsx) file.', 'danger')
    return render_template('upload_crime_report.html') 