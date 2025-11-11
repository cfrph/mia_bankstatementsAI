#11112025 1:28pm

from flask import Flask, request, Response, render_template
import io
import csv
import zipfile
import json

import capone_processor
import chase7772_processor
import tcb_processor

app = Flask(__name__)

@app.route('/')
def index():
    # Render your upload form HTML template
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload():
    pdf_file = request.files.get('pdf')
    if not pdf_file:
        return "No file uploaded", 400

    journal_start = request.form.get('journal_start', '1000')
    deposit_start = request.form.get('deposit_start', '2000')
    processor_name = request.form.get('processor')

    pdf_bytes = pdf_file.read()

    # Define helper to check valid JSON response from processor
    def check_response(json_data, proc_name):
        if json_data is None:
            return False, f"Failed to process document with {proc_name} processor."
        return True, None

    if processor_name == 'capone':
        response_json = capone_processor.process_pdf(pdf_bytes)
        valid, error_message = check_response(response_json, 'CapOne')
        if not valid:
            return error_message, 500
        csv_data = capone_processor.convert_to_csv(response_json)
        return Response(csv_data, mimetype='text/csv',
                        headers={"Content-Disposition": "attachment;filename=capone_transactions.csv"})

    elif processor_name == 'chase7772':
        response_json = chase7772_processor.process_pdf(pdf_bytes)
        valid, error_message = check_response(response_json, 'Chase7772')
        if not valid:
            return error_message, 500
        csv_data = chase7772_processor.convert_to_csv(response_json)
        return Response(csv_data, mimetype='text/csv',
                        headers={"Content-Disposition": "attachment;filename=chase7772_transactions.csv"})

    elif processor_name == 'tcb':
        response_json = tcb_processor.process_pdf(pdf_bytes)
        valid, error_message = check_response(response_json, 'TCB')
        if not valid:
            return error_message, 500

        debits, credits, unmapped = tcb_processor.process_tcb_json(response_json, journal_start, deposit_start)

        # Generate zipped MultiLedger CSVs in memory
        output_zip = io.BytesIO()
        with zipfile.ZipFile(output_zip, mode='w') as zf:
            debit_io = io.StringIO()
            debit_writer = csv.writer(debit_io)
            debit_writer.writerow(["Journal#", "Date", "Short Desc", "Full Desc", "Amount", "Account#"])
            debit_writer.writerows(debits)
            zf.writestr("tcb_debits.csv", debit_io.getvalue())

            credit_io = io.StringIO()
            credit_writer = csv.writer(credit_io)
            credit_writer.writerow(["Deposit#", "Date", "Short Desc", "Full Desc", "Amount", "Account#"])
            credit_writer.writerows(credits)
            zf.writestr("tcb_credits.csv", credit_io.getvalue())

            if unmapped:
                unmapped_io = io.StringIO()
                unmapped_writer = csv.writer(unmapped_io)
                unmapped_writer.writerow(["Entry#", "Date", "Short Desc", "Full Desc", "Amount", "Account#"])
                unmapped_writer.writerows(unmapped)
                zf.writestr("tcb_unmapped.csv", unmapped_io.getvalue())

        output_zip.seek(0)
        return Response(output_zip.getvalue(), mimetype='application/zip',
                        headers={"Content-Disposition": "attachment;filename=multiledger_tcb_export.zip"})

    else:
        return f"Processor '{processor_name}' not supported", 400

if __name__ == '__main__':
    app.run(debug=True)
