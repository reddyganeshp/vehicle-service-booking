from flask import Flask, render_template, request, redirect, url_for, flash
from models.booking import Booking
from lib.service_cost import estimate_cost
from reportlab.pdfgen import canvas
from io import BytesIO
from flask import send_file
import services.s3_manager as s3m
from os import getenv
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.secret_key = "dev-secret"  # for flash messages (in prod use secure secret)

# ---------- HOME ----------
@app.route('/')
def index():
    return render_template('index.html')

# ---------- CREATE ----------
@app.route('/booking/create', methods=['GET', 'POST'])
def create_booking():
    if request.method == 'POST':
        # gather and validate
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        vehicle = request.form.get('vehicle_number', '').strip()
        service_type = request.form.get('service_type', '').strip()
        date = request.form.get('date', '').strip()

        # Basic server-side validation
        if not (name and phone and vehicle and service_type and date):
            flash("All fields are required.", "error")
            return redirect(url_for('create_booking'))

        booking = Booking(name, phone, vehicle, service_type, date)
        try:
            s3m.add_booking(booking.to_dict())
            flash("Booking created successfully.", "success")
        except Exception as e:
            flash(f"Failed to save booking: {e}", "error")

        return redirect(url_for('list_bookings'))

    return render_template('create.html')

# ---------- LIST ----------
@app.route('/bookings')
def list_bookings():
    try:
        bookings = s3m.get_all_bookings()
    except Exception as e:
        bookings = []
        flash(f"Unable to load bookings: {e}", "error")
    return render_template('list.html', bookings=bookings)

# ---------- UPDATE ----------
@app.route('/booking/update/<id>', methods=['GET', 'POST'])
def update_booking(id):
    if request.method == 'POST':
        # collect updated values
        updates = {
            "name": request.form.get('name', '').strip(),
            "phone": request.form.get('phone', '').strip(),
            "vehicle_number": request.form.get('vehicle_number', '').strip(),
            "service_type": request.form.get('service_type', '').strip(),
            "date": request.form.get('date', '').strip(),
        }
        # remove empty values
        updates = {k: v for k, v in updates.items() if v}
        try:
            updated = s3m.update_booking(id, updates)
            if updated:
                flash("Booking updated.", "success")
            else:
                flash("Booking not found.", "error")
        except Exception as e:
            flash(f"Update failed: {e}", "error")
        return redirect(url_for('list_bookings'))

    # GET: show form pre-filled
    booking = s3m.get_booking(id)
    if not booking:
        flash("Booking not found.", "error")
        return redirect(url_for('list_bookings'))
    return render_template('update.html', booking=booking)

# ---------- DELETE ----------
@app.route('/booking/delete/<id>')
def delete_booking(id):
    try:
        ok = s3m.delete_booking(id)
        if ok:
            flash("Booking deleted.", "success")
        else:
            flash("Booking not found.", "error")
    except Exception as e:
        flash(f"Delete failed: {e}", "error")
    return redirect(url_for('list_bookings'))

# ------- SERVICE COST ESTIMATOR (NON-CRUD) --------------
@app.route('/estimate', methods=['GET', 'POST'])
def estimate_service_cost():
    if request.method == 'POST':
        service_type = request.form.get('service_type')
        vehicle_category = request.form.get('vehicle_category')

        cost = estimate_cost(service_type, vehicle_category)

        return render_template(
            'estimate_result.html',
            service_type=service_type,
            vehicle_category=vehicle_category,
            cost=cost
        )

    return render_template('estimate.html')

# -----PDF GENERATION (NON-CRUD) --------
@app.route('/booking/pdf/<id>')
def download_booking_pdf(id):
    booking = s3m.get_booking(id)
    if not booking:
        flash("Booking not found.", "error")
        return redirect(url_for('list_bookings'))

    # Generate PDF in memory
    pdf_buffer = BytesIO()
    pdf = canvas.Canvas(pdf_buffer)

    pdf.setFont("Helvetica", 14)
    pdf.drawString(100, 800, "Vehicle Service Booking Details")
    pdf.setFont("Helvetica", 12)

    y = 760
    for key, value in booking.items():
        pdf.drawString(100, y, f"{key}: {value}")
        y -= 20

    pdf.save()
    pdf_buffer.seek(0)

    filename = f"booking_{booking['id']}.pdf"
    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=filename,
        mimetype='application/pdf'
    )


# ---------- MAIN ----------
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True)
