from flask import Flask, render_template, request, session, redirect, url_for, flash
import sqlite3
import hashlib
import json
import pandas as pd
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Path to Excel file
EXCEL_FILE = 'plswork.xlsx'

def get_db_connection():
    conn = sqlite3.connect('app.db')
    conn.row_factory = sqlite3.Row
    return conn

def read_excel_sheet(sheet_name):
    """Read data from Excel sheet"""
    try:
        df = pd.read_excel(EXCEL_FILE, sheet_name=sheet_name)
        return df
    except Exception as e:
        print(f"Error reading {sheet_name}: {e}")
        return None

def clean_data_for_json(data):
    """Convert any datetime objects to strings for JSON serialization"""
    if isinstance(data, list):
        return [clean_data_for_json(item) for item in data]
    elif isinstance(data, dict):
        return {key: clean_data_for_json(value) for key, value in data.items()}
    elif isinstance(data, (datetime, pd.Timestamp)):
        return data.strftime('%Y-%m-%d')
    elif pd.isna(data):  # Handle NaN values
        return None
    elif isinstance(data, (int, float)):
        return float(data) if isinstance(data, float) else int(data)
    else:
        return data

@app.route('/')
def login_page():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    # Hash the password
    password_hash = hashlib.sha256(password.encode()).hexdigest()

    # Try database first
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ? AND password_hash = ?',
                       (username, password_hash)).fetchone()
    conn.close()
    
    if user:
        session['username'] = username
        return redirect(url_for('dashboard'))

    # Fallback to Excel
    try:
        df = read_excel_sheet('users')
        if df is not None:
            # Find user in Excel
            user_row = df[(df['username'] == username) & (df['password'] == password)]
            if not user_row.empty:
                session['username'] = username
                return redirect(url_for('dashboard'))
    except Exception as e:
        print(f"Excel login error: {e}")

    flash('Invalid username or password')
    return redirect(url_for('login_page'))

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login_page'))

    username = session['username']
    
    # Initialize variables
    kpi_labels = []
    kpi_values = []
    sales_products = []
    sales_units = []
    employee_names = []
    employee_efficiency = []
    task_labels = []
    task_counts = []
    
    try:
        # 1. KPI Data from 'data' sheet
        kpi_df = read_excel_sheet('data')
        if kpi_df is not None and not kpi_df.empty:
            kpi_df['date'] = pd.to_datetime(kpi_df['date']).dt.strftime('%Y-%m-%d')
            kpi_labels = kpi_df['date'].tolist()
            kpi_values = kpi_df['kpi_rate'].astype(float).tolist()
        
        # 2. Sales Data from 'sales' sheet
        sales_df = read_excel_sheet('sales')
        if sales_df is not None and not sales_df.empty:
            sales_products = sales_df['product'].unique().tolist()
            sales_units = []
            for product in sales_products:
                total = sales_df[sales_df['product'] == product]['units_sold'].sum()
                sales_units.append(int(total))
        
        # 3. Employee Data from 'employee' sheet
        employee_df = read_excel_sheet('employee')
        if employee_df is not None and not employee_df.empty:
            # Sort by efficiency (handle column name with %)
            efficiency_col = [col for col in employee_df.columns if 'efficiency' in col.lower()][0]
            employee_df_sorted = employee_df.sort_values(by=efficiency_col, ascending=False).head(5)
            employee_names = employee_df_sorted['name'].tolist()
            
            # Convert efficiency to float, handling any non-numeric values
            efficiency_values = []
            for val in employee_df_sorted[efficiency_col].tolist():
                try:
                    if isinstance(val, str):
                        val = val.replace('%', '')
                    efficiency_values.append(float(val))
                except:
                    efficiency_values.append(0.0)
            employee_efficiency = efficiency_values
        
        # 4. Tasks Data from 'tasks' sheet
        tasks_df = read_excel_sheet('tasks')
        if tasks_df is not None and not tasks_df.empty:
            # Find status column
            status_col = [col for col in tasks_df.columns if 'status' in col.lower()][0]
            status_counts = tasks_df[status_col].value_counts()
            task_labels = status_counts.index.tolist()
            task_counts = status_counts.values.astype(int).tolist()
        
    except Exception as e:
        print(f"Error reading Excel data: {e}")
        # Fallback to database
        conn = get_db_connection()
        
        kpi_data = conn.execute('SELECT date, kpi_rate FROM data ORDER BY date').fetchall()
        kpi_labels = [row['date'].split(' ')[0] for row in kpi_data]
        kpi_values = [float(row['kpi_rate']) for row in kpi_data]
        
        sales_data = conn.execute('SELECT product, SUM(units_sold) as total_units FROM sales GROUP BY product').fetchall()
        sales_products = [row['product'] for row in sales_data]
        sales_units = [int(row['total_units']) for row in sales_data]
        
        employee_data = conn.execute('SELECT name, efficiency FROM employee ORDER BY efficiency DESC LIMIT 5').fetchall()
        employee_names = [row['name'] for row in employee_data]
        employee_efficiency = [float(row['efficiency']) for row in employee_data]
        
        tasks_data = conn.execute('SELECT status, COUNT(*) as count FROM tasks GROUP BY status').fetchall()
        task_labels = [row['status'] for row in tasks_data]
        task_counts = [int(row['count']) for row in tasks_data]
        
        conn.close()

    # Calculate change (last 2 values)
    if len(kpi_values) >= 2:
        change = kpi_values[-1] - kpi_values[-2]
    else:
        change = 0

    # Clean data for JSON serialization
    kpi_labels = clean_data_for_json(kpi_labels)
    kpi_values = clean_data_for_json(kpi_values)
    sales_products = clean_data_for_json(sales_products)
    sales_units = clean_data_for_json(sales_units)
    employee_names = clean_data_for_json(employee_names)
    employee_efficiency = clean_data_for_json(employee_efficiency)
    task_labels = clean_data_for_json(task_labels)
    task_counts = clean_data_for_json(task_counts)

    return render_template('index.html',
                         username=username,
                         kpi_labels=json.dumps(kpi_labels),
                         kpi_values=json.dumps(kpi_values),
                         change=change,
                         sales_products=json.dumps(sales_products),
                         sales_units=json.dumps(sales_units),
                         employee_names=json.dumps(employee_names),
                         employee_efficiency=json.dumps(employee_efficiency),
                         task_labels=json.dumps(task_labels),
                         task_counts=json.dumps(task_counts))

@app.route('/tasks')
def tasks():
    if 'username' not in session:
        return redirect(url_for('login_page'))

    username = session['username']
    
    # Try database first
    conn = get_db_connection()
    tasks_data = conn.execute('SELECT * FROM tasks WHERE assigned_to = ?', (username,)).fetchall()
    conn.close()
    
    if tasks_data:
        tasks_list = [dict(task) for task in tasks_data]
    else:
        # Fallback to Excel
        tasks_list = []
        try:
            tasks_df = read_excel_sheet('tasks')
            if tasks_df is not None and not tasks_df.empty:
                # Find relevant columns
                task_name_col = [col for col in tasks_df.columns if 'task' in col.lower() and 'name' in col.lower()][0]
                assigned_col = [col for col in tasks_df.columns if 'assigned' in col.lower()][0]
                status_col = [col for col in tasks_df.columns if 'status' in col.lower()][0]
                
                # Filter tasks for current user
                user_tasks = tasks_df[tasks_df[assigned_col].str.contains(username, na=False)]
                
                for idx, row in user_tasks.iterrows():
                    tasks_list.append({
                        'id': idx,
                        'task': str(row[task_name_col]),
                        'status': str(row[status_col]) if not pd.isna(row[status_col]) else 'Not Started'
                    })
        except Exception as e:
            print(f"Error reading tasks from Excel: {e}")

    return render_template('tasks.html', username=username, tasks=tasks_list)

@app.route('/add_task', methods=['POST'])
def add_task():
    if 'username' not in session:
        return redirect(url_for('login_page'))

    username = session['username']
    task_title = request.form['task']
    status = request.form.get('status', 'Not Started')

    conn = get_db_connection()
    conn.execute('INSERT INTO tasks (task, status, assigned_to) VALUES (?, ?, ?)',
                (task_title, status, username))
    conn.commit()
    conn.close()

    return redirect(url_for('tasks'))

@app.route('/update_task/<int:task_id>', methods=['POST'])
def update_task(task_id):
    if 'username' not in session:
        return redirect(url_for('login_page'))

    username = session['username']
    status = request.form['status']

    conn = get_db_connection()
    conn.execute('UPDATE tasks SET status = ? WHERE id = ? AND assigned_to = ?',
                (status, task_id, username))
    conn.commit()
    conn.close()

    return redirect(url_for('tasks'))

@app.route('/delete_task/<int:task_id>', methods=['POST'])
def delete_task(task_id):
    if 'username' not in session:
        return redirect(url_for('login_page'))

    username = session['username']

    conn = get_db_connection()
    conn.execute('DELETE FROM tasks WHERE id = ? AND assigned_to = ?',
                (task_id, username))
    conn.commit()
    conn.close()

    return redirect(url_for('tasks'))

@app.route('/settings')
def settings():
    if 'username' not in session:
        return redirect(url_for('login_page'))

    username = session['username']
    return render_template('Settings.html', username=username)

@app.route('/messages')
def messages():
    if 'username' not in session:
        return redirect(url_for('login_page'))

    username = session['username']

    # Get conversations for the user
    conn = get_db_connection()
    conversations = conn.execute('''
        SELECT DISTINCT
            CASE WHEN sender = ? THEN recipient ELSE sender END as other_user,
            MAX(timestamp) as last_message_time,
            (SELECT message FROM messages m2
             WHERE (m2.sender = messages.sender AND m2.recipient = messages.recipient)
                OR (m2.sender = messages.recipient AND m2.recipient = messages.sender)
             ORDER BY m2.timestamp DESC LIMIT 1) as last_message
        FROM messages
        WHERE sender = ? OR recipient = ?
        GROUP BY CASE WHEN sender = ? THEN recipient ELSE sender END
        ORDER BY last_message_time DESC
    ''', (username, username, username, username)).fetchall()

    # Get messages for the first conversation if any exist
    messages_list = []
    if conversations:
        other_user = conversations[0]['other_user']
        messages_data = conn.execute('''
            SELECT * FROM messages
            WHERE (sender = ? AND recipient = ?) OR (sender = ? AND recipient = ?)
            ORDER BY timestamp ASC
        ''', (username, other_user, other_user, username)).fetchall()
        messages_list = [dict(msg) for msg in messages_data]

    conn.close()

    return render_template('Messages.html',
                         username=username,
                         conversations=conversations,
                         messages=messages_list,
                         active_conversation=conversations[0]['other_user'] if conversations else None)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login_page'))

if __name__ == '__main__':
    app.run(debug=True)
