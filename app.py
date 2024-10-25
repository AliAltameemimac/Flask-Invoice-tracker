# Aggregates invoices by subcontractor
def aggregate_invoice_data():
    invoices = get_all_invoices()  # Retrieve all invoices from the database
    summary = defaultdict(lambda: {
        'total_amount_due': 0.0,
        'total_amount_received': 0.0,
        'total_balance_amount': 0.0,
        'ref_no': ''
    })

    # Process each invoice to aggregate amounts per subcontractor
    for invoice in invoices:
        subcontractor = invoice['subcontractor']
        amount_due = invoice.get('amount_due', 0.0)
        amount_received = invoice.get('amount_received', 0.0)
        balance_amount = invoice.get('balance_amount', 0.0)

        summary[subcontractor]['total_amount_due'] += amount_due
        summary[subcontractor]['total_amount_received'] += amount_received
        summary[subcontractor]['total_balance_amount'] += balance_amount
        summary[subcontractor]['ref_no'] = invoice['ref_no']  # Record the most recent ref_no for each subcontractor

    return summary

# Rest of app.py code
from flask import Flask, render_template, request, redirect, url_for, send_file
from fpdf import FPDF
import sqlite3
import tempfile
from collections import defaultdict
import pandas as pd
import datetime
import random
import string
import os

app = Flask(__name__)

# Initialize the database (assuming init_db and other helper functions are correctly set up)
from database import init_db, add_subcontractor, add_invoice, get_all_invoices, get_all_subcontractors
init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add_subcontractor', methods=['GET', 'POST'])
def add_subcontractor_route():
    if request.method == 'POST':
        subcontractor_data = {
            'name': request.form['name'],
            'job_title': request.form['job_title'],
            'package': request.form['package'],
            'contact_no': request.form['contact_no'],
            'email': request.form['email'],
            'address': request.form['address']
        }
        add_subcontractor(**subcontractor_data)
        return redirect(url_for('index'))
    return render_template('add_subcontractor.html')

@app.route('/add_invoice', methods=['GET', 'POST'])
def add_invoice_route():
    if request.method == 'POST':
        invoice_data = {
            'ref_no': request.form['ref_no'],
            'subcontractor': request.form['subcontractor'],
            'description': request.form['description'],
            'date': request.form['date'],
            'amount_due': float(request.form.get('amount_due', 0.0)),
            'amount_received': float(request.form.get('amount_received', 0.0)),
            'balance_amount': float(request.form.get('balance_amount', 0.0))
        }
        add_invoice(**invoice_data)
        return redirect(url_for('index'))

    ref_no = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    today_date = datetime.date.today().strftime('%Y-%m-%d')
    subcontractors = get_all_subcontractors()
    return render_template('add_invoice.html', ref_no=ref_no, today_date=today_date, subcontractors=subcontractors)

@app.route('/view_invoices')
def view_invoices():
    invoices = get_all_invoices()
    invoices_sorted = sorted(invoices, key=lambda inv: inv['subcontractor'])

    summary = defaultdict(lambda: {'total_amount_due': 0.0, 'total_amount_received': 0.0, 'total_balance_amount': 0.0})
    for invoice in invoices:
        subcontractor = invoice['subcontractor']
        summary[subcontractor]['total_amount_due'] += invoice.get('amount_due', 0.0)
        summary[subcontractor]['total_amount_received'] += invoice.get('amount_received', 0.0)
        summary[subcontractor]['total_balance_amount'] += invoice.get('balance_amount', 0.0)

    summary_list = [{
        'subcontractor': k,
        'total_amount_due': f"{v['total_amount_due']:,.2f}",
        'total_amount_received': f"{v['total_amount_received']:,.2f}",
        'total_balance_amount': f"{v['total_balance_amount']:,.2f}"
    } for k, v in summary.items()]

    # Format amounts in invoices for display
    invoices_formatted = [{
        **invoice,
        'amount_due': f"{invoice['amount_due']:,.2f}",
        'amount_received': f"{invoice['amount_received']:,.2f}",
        'balance_amount': f"{invoice['balance_amount']:,.2f}"
    } for invoice in invoices_sorted]

    return render_template('view_invoices.html', invoices=invoices_formatted, summary=summary_list)


@app.route('/export_to_excel')
def export_to_excel():
    invoices = get_all_invoices()
    df = pd.DataFrame(invoices)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as temp_file:
        df.to_excel(temp_file.name, index=False)
    return send_file(temp_file.name, as_attachment=True, download_name='invoices_export.xlsx')

def get_all_invoices():
    conn = sqlite3.connect('invoice_tracker.db')  # Replace with your database path
    cursor = conn.cursor()
    cursor.execute('SELECT ref_no, subcontractor, description, date, amount_due, amount_received FROM invoices')
    invoices = cursor.fetchall()
    conn.close()
    return [{'ref_no': inv[0], 'subcontractor': inv[1], 'description': inv[2], 'date': inv[3],
             'amount_due': float(inv[4]), 'amount_received': float(inv[5]),
             'balance_amount': float(inv[4]) - float(inv[5])} for inv in invoices]

@app.route('/export_to_pdf')
def export_to_pdf():
    summary_data = aggregate_invoice_data()
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=8)
    pdf.cell(200, 10, txt="Subcontractor Summary Report", ln=True, align='C')

    pdf.cell(20, 10, 'Ref No', border=1)
    pdf.cell(40, 10, 'Subcontractor', border=1)
    pdf.cell(40, 10, 'Total Amount Due', border=1)
    pdf.cell(40, 10, 'Total Amount Received', border=1)
    pdf.cell(40, 10, 'Balance Amount', border=1)
    pdf.ln()

    for subcontractor, totals in summary_data.items():
        pdf.cell(20, 10, str(totals['ref_no']), border=1)
        pdf.cell(40, 10, subcontractor, border=1)
        pdf.cell(40, 10, f"{totals['total_amount_due']:,.2f}", border=1)
        pdf.cell(40, 10, f"{totals['total_amount_received']:,.2f}", border=1)
        pdf.cell(40, 10, f"{totals['total_balance_amount']:,.2f}", border=1)
        pdf.ln()

    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        pdf.output(tmp_file.name)
    return send_file(tmp_file.name, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port= 5000, debug=True)
