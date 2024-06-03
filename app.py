import sqlite3
import os
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory,jsonify


app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for flash messages

# Ensure the upload folder exists
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# Route to render the homepage form
@app.route('/')
def home():
    return render_template('index.html')

# Database helper function
def get_db_connection():
    conn = sqlite3.connect('data.db')
    conn.row_factory = sqlite3.Row
    return conn


# Route to render the form
@app.route('/eic_details')
def eic_details():

    conn = get_db_connection()
    pbno_list = conn.execute('SELECT pbno, name FROM eic_details').fetchall()
    eic_data = conn.execute('SELECT * FROM eic_details').fetchall()
    conn.close()
    
    # Convert pbno_list to a list of dictionaries for JSON serialization
    pbno_list = [dict(row) for row in pbno_list]
    
    return render_template('eic_details.html', pbno_list=pbno_list, eic_data=eic_data)


# Route to handle form submission
@app.route('/submit', methods=['POST'])
def submit():
    pbno = request.form['pbno']
    area = request.form.getlist('area')
    section = request.form.getlist('section')
    
    # Join the selected options with ';'
    area_str = ';'.join(area)
    section_str = ';'.join(section)
    
    # Update the database
    conn = get_db_connection()
    conn.execute('UPDATE eic_details SET area = ?, section = ? WHERE pbno = ?', (area_str, section_str, pbno))
    conn.commit()
    conn.close()
    
    flash('Form submitted successfully!')
    return redirect(url_for('eic_details'))


# Route to render the form for contracts
@app.route('/contracts')
def contract_form():
    conn = get_db_connection()
    contract_data = conn.execute('SELECT * FROM contracts').fetchall()
    conn.close()
    return render_template('contract_form.html', contract_data=contract_data)

# Route to handle contract form submission
@app.route('/submit_contract', methods=['POST'])
def submit_contract():
    contract_no = request.form['contract_no']
    start_date = request.form['start_date']
    end_date = request.form['end_date']
    contractor_name = request.form['contractor_name']
    contract_description = request.form['contract_description']
    machine_file = request.files['machine_list']
    
    if machine_file and machine_file.filename.endswith('.xlsx'):
        file_name = f"{contract_no}_" + machine_file.filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_name)
        machine_file.save(file_path)
        
        conn = get_db_connection()

        contract_exists = conn.execute("SELECT * FROM contracts WHERE contract_no = ?",(contract_no,)).fetchone()

        if contract_exists:
            conn.execute("UPDATE contracts SET start_date=?,end_date=?,contractor_name=?,machine_list=?,contract_description=? WHERE contract_no=?",
                         (start_date,end_date,contractor_name,file_name,contract_description,contract_no))
        else:
            conn.execute('INSERT INTO contracts (contract_no,contract_description, start_date, end_date, contractor_name , machine_list) VALUES (?, ?, ?, ?, ?,?)',
                     (contract_no, contract_description, start_date, end_date, contractor_name, file_name))
        

        conn.commit()
        conn.close()
        
        flash('Contract submitted successfully!')
    else:
        flash('Invalid file format. Please upload an Excel file.')
    
    return redirect(url_for('contract_form'))

# Route to serve uploaded files
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# Route to render the form for manpower
@app.route('/manpower')
def manpower_form():
    conn = get_db_connection()
    contract_data = conn.execute('SELECT contract_no, contractor_name FROM contracts').fetchall()

    selected_contract_no = request.args.get('contract_filter', type=str)

    if selected_contract_no:
        manpower_data = conn.execute('SELECT * FROM manpower WHERE contract_no = ?', (selected_contract_no,)).fetchall()
    else:
        manpower_data = conn.execute('SELECT * FROM manpower').fetchall()
    
    conn.close()
    return render_template('manpower_form.html', contract_data=contract_data, manpower_data=manpower_data,selected_contract_no=selected_contract_no)


# Route to handle manpower form submission
@app.route('/submit_manpower', methods=['POST'])
def submit_manpower():
    punch_id = request.form['punch_id']
    employee_id = request.form['employee_id']
    name = request.form['name']
    contract_no = request.form['contract_no']
    category = request.form['category']
    pf_no = request.form['pf_no']
    esi_no = request.form['esi_no']
    aadhaar_no = request.form['aadhaar_no']
    contractor_name = request.form["contractor_name"]
    bank_account_no = request.form['bank_account_no']
    date_of_joining = request.form['date_of_joining']
    
    conn = get_db_connection()
    contractor_name = conn.execute('SELECT contractor_name FROM contracts WHERE contract_no = ?', (contract_no,)).fetchone()['contractor_name']
    
    employee_exists = conn.execute("SELECT * FROM manpower WHERE punch_id = ?",(punch_id,)).fetchone()

    try:
        if employee_exists:
            conn.execute("UPDATE manpower SET employee_id=?,name=?,contract_no=?,contractor_name=?,category=?,pf_no=?,esi_no=?,aadhaar_no=?,bank_account_no=?,date_of_joining=? WHERE punch_id=?",
                            ( employee_id, name, contract_no, contractor_name, category, pf_no, esi_no, aadhaar_no, bank_account_no, date_of_joining, punch_id))
        else:
            conn.execute('INSERT INTO manpower (punch_id, employee_id, name, contract_no, contractor_name, category, pf_no, esi_no, aadhaar_no, bank_account_no, date_of_joining) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                        (punch_id, employee_id, name, contract_no, contractor_name, category, pf_no, esi_no, aadhaar_no, bank_account_no, date_of_joining))
        conn.commit()
        flash('Manpower details submitted successfully!')
    
    except sqlite3.IntegrityError as e:
        flash(f'An integrity error occurred: {str(e)}', 'error')
        conn.rollback()  # Rollback in case of an error
    except Exception as e:
        flash(f'An unexpected error occurred: {str(e)}', 'error')
        conn.rollback()  # Rollback in case of an error
    finally:
        conn.close()
    
    
    return redirect(url_for('manpower_form',contract_filter=contract_no))

# Route to fetch contractor name based on contract_no
@app.route('/get_contractor_name/<contract_no>')
def get_contractor_name(contract_no):
    conn = get_db_connection()
    contractor_name = conn.execute('SELECT contractor_name FROM contracts WHERE contract_no = ?', (contract_no,)).fetchone()
    conn.close()
    if contractor_name:
        return jsonify(contractor_name=contractor_name['contractor_name'])
    else:
        return jsonify(contractor_name='')

if __name__ == '__main__':
    app.run()