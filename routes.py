import os
from flask import render_template, request, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename
from app import app, db
from models import User, Order
from utils import allowed_file, process_cad_file

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        if 'technical_drawing' not in request.files:
            flash('No file part', 'error')
            return redirect(request.url)
        file = request.files['technical_drawing']
        if file.filename == '':
            flash('No selected file', 'error')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            try:
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                file.save(file_path)
                # Process CAD file and generate 3D model
                model_data = process_cad_file(filename)
                if model_data is None:
                    flash('Error processing the uploaded file', 'error')
                    return redirect(request.url)
                # Create a new order
                order = Order(technical_drawing=filename, user_id=1)  # Assuming user is logged in
                db.session.add(order)
                db.session.commit()
                flash('File uploaded successfully', 'success')
                return redirect(url_for('visualization', order_id=order.id))
            except Exception as e:
                flash(f'Error uploading file: {str(e)}', 'error')
                return redirect(request.url)
        else:
            flash('Invalid file type', 'error')
    return render_template('upload.html')

@app.route('/visualization/<int:order_id>')
def visualization(order_id):
    order = Order.query.get_or_404(order_id)
    return render_template('visualization.html', order=order)

@app.route('/get_model_data')
def get_model_data():
    # For simplicity, we're getting the latest order
    # In a real application, you'd want to specify which order's data to retrieve
    latest_order = Order.query.order_by(Order.id.desc()).first()
    if latest_order:
        model_data = process_cad_file(latest_order.technical_drawing)
        if model_data:
            return jsonify(model_data)
    return jsonify({'error': 'No model data available'}), 404

@app.route('/order_management')
def order_management():
    orders = Order.query.all()
    return render_template('order_management.html', orders=orders)

@app.route('/add_comment/<int:order_id>', methods=['POST'])
def add_comment(order_id):
    order = Order.query.get_or_404(order_id)
    comment = request.form.get('comment')
    if comment:
        order.comments = order.comments + '\n' + comment if order.comments else comment
        db.session.commit()
        flash('Comment added successfully', 'success')
    return redirect(url_for('visualization', order_id=order.id))

@app.route('/upload_additional_file/<int:order_id>', methods=['POST'])
def upload_additional_file(order_id):
    order = Order.query.get_or_404(order_id)
    if 'additional_file' in request.files:
        file = request.files['additional_file']
        if file and allowed_file(file.filename):
            try:
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                file.save(file_path)
                if order.additional_files:
                    order.additional_files += ',' + filename
                else:
                    order.additional_files = filename
                db.session.commit()
                flash('Additional file uploaded successfully', 'success')
            except Exception as e:
                flash(f'Error uploading additional file: {str(e)}', 'error')
        else:
            flash('Invalid file type', 'error')
    return redirect(url_for('visualization', order_id=order.id))
