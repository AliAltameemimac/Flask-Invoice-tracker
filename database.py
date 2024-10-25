import sqlite3
from decimal import Decimal

def init_db():
    conn = sqlite3.connect('invoice_tracker.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS subcontractors
                 (id INTEGER PRIMARY KEY,
                  name TEXT,
                  job_title TEXT,
                  package TEXT,
                  contact_no TEXT,
                  email TEXT,
                  address TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS invoices
                 (id INTEGER PRIMARY KEY,
                  ref_no TEXT,
                  subcontractor TEXT,
                  description TEXT,
                  date TEXT,
                  amount_due REAL,
                  amount_received REAL,
                  balance_amount REAL)''')
    conn.commit()
    conn.close()

def add_subcontractor(name, job_title, package, contact_no, email, address):
    conn = sqlite3.connect('invoice_tracker.db')
    c = conn.cursor()
    c.execute("INSERT INTO subcontractors (name, job_title, package, contact_no, email, address) VALUES (?, ?, ?, ?, ?, ?)",
              (name, job_title, package, contact_no, email, address))
    conn.commit()
    conn.close()

def add_invoice(ref_no, subcontractor, description, date, amount_due, amount_received, balance_amount):
    conn = sqlite3.connect('invoice_tracker.db')
    c = conn.cursor()
    c.execute("INSERT INTO invoices (ref_no, subcontractor, description, date, amount_due, amount_received, balance_amount) VALUES (?, ?, ?, ?, ?, ?, ?)",
              (ref_no, subcontractor, description, date, amount_due, amount_received, balance_amount))
    conn.commit()
    conn.close()

def get_all_invoices():
    conn = sqlite3.connect('invoice_tracker.db')
    c = conn.cursor()
    c.execute("SELECT * FROM invoices")
    invoices = []
    for row in c.fetchall():
        invoice = {
            'id': row[0],
            'ref_no': row[1],
            'subcontractor': row[2],
            'description': row[3],
            'date': row[4],
            'amount_due': f"{Decimal(row[5]):,.2f}",
            'amount_received': f"{Decimal(row[6]):,.2f}",
            'balance_amount': f"{Decimal(row[7]):,.2f}"
        }
        invoices.append(invoice)
    conn.close()
    return invoices

def get_all_subcontractors():
    conn = sqlite3.connect('invoice_tracker.db')
    c = conn.cursor()
    c.execute("SELECT name FROM subcontractors")
    subcontractors = [row[0] for row in c.fetchall()]
    conn.close()
    return subcontractors