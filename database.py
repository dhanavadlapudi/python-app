import sqlite3

from app import get_db_connection

with sqlite3.Connection("data.db") as conn:
    cursor = conn.cursor()
    query = "SELECT * FROM eic_details;"
    data = cursor.execute(query).fetchall()
    one_record = cursor.execute(query).fetchone()
    five_records = cursor.execute(query).fetchmany(5)

keys = ["pbno","name","area","section"]

pbno_list = [dict(zip(keys,row)) for row in data]

# working with contracts table

with sqlite3.Connection("data.db") as conn:
    cursor = conn.cursor()
    query = "SELECT * FROM contracts;"
    data = cursor.execute(query).fetchall()
    one_record = cursor.execute(query).fetchone()
    five_records = cursor.execute(query).fetchmany(5)

print(one_record)
print(five_records)
 




#working with manpower table
with sqlite3.Connection("data.db") as conn:
    cursor = conn.cursor()
    query = "SELECT * FROM manpower;"
    data = cursor.execute(query).fetchall()
    one_record = cursor.execute(query).fetchone()
    five_records = cursor.execute(query).fetchmany(5)

keys = ["punch_id","employee_id","name","contract_no","contractor_name","category","pf_no","esi_no","aadhaar_no","bank_account_no","date_of_joining"]

punch_id_list = [dict(zip(keys,row)) for row in data]

conn = get_db_connection()

contract_exists = conn.execute("SELECT * FROM contracts WHERE contract_no = ?",(10525,)).fetchone()
print(contract_exists)





