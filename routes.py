import os
from flask import render_template, request, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename
from app import app, db
from models import User, Order
from utils import allowed_file, process_cad_file, validate_stl_file, repair_stl_file
import logging

logging.basicConfig(level=logging.DEBUG)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        if 'technical_drawing' not in request.files:
            flash('No file part', 'error')
            logging.error("File upload failed: No file part in request")
            return redirect(request.url)
        file = request.files['technical_drawing']
        if file.filename == '':
            flash('No selected file', 'error')
            logging.error("File upload failed: No selected file")
            return redirect(request.url)
        if file and allowed_file(file.filename):
            try:
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                file.save(file_path)
                logging.info(f"File saved successfully: {file_path}")
                
                # Validate STL file
                validation_result = validate_stl_file(file_path)
                if not validation_result['valid']:
                    logging.warning(f"STL file validation failed: {validation_result['message']}")
                    
                    # Attempt to repair the file
                    repair_result = repair_stl_file(file_path)
                    if repair_result['success']:
                        file_path = repair_result['repaired_file']
                        flash(f"File was repaired: {repair_result['message']}", 'warning')
                        logging.info(f"STL file repaired: {file_path}")
                    else:
                        os.remove(file_path)
                        flash(f"Invalid or corrupted STL file: {validation_result['message']}", 'error')
                        logging.error(f"STL file validation failed and repair unsuccessful: {validation_result['message']}")
                        return redirect(request.url)
                
                # Process CAD file and generate 3D model
                model_data = process_cad_file(os.path.basename(file_path))
                if model_data is None or 'error' in model_data:
                    error_message = model_data.get('error', 'Error processing the uploaded file')
                    logging.error(f"Error processing the uploaded file: {filename}. Error: {error_message}")
                    flash(error_message, 'error')
                    return redirect(request.url)
                
                # Create a new order without specifying user_id
                order = Order(technical_drawing=os.path.basename(file_path))
                db.session.add(order)
                db.session.commit()
                logging.info(f"New order created with ID: {order.id}")
                
                flash('File uploaded and processed successfully', 'success')
                return redirect(url_for('visualization', order_id=order.id))
            except Exception as e:
                logging.error(f"Error uploading file: {str(e)}", exc_info=True)
                flash(f'Error uploading file: {str(e)}', 'error')
                return redirect(request.url)
        else:
            logging.warning(f"Invalid file type: {file.filename}")
            flash('Invalid file type. Please upload a supported file format (STL, OBJ, STEP, STP).', 'error')
    return render_template('upload.html')

@app.route('/visualization/<int:order_id>')
def visualization(order_id):
    order = Order.query.get_or_404(order_id)
    return render_template('visualization.html', order=order)

@app.route('/get_model_data')
def get_model_data():
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
    if 'additional_file' not in request.files:
        flash('No file part', 'error')
        logging.error("Additional file upload failed: No file part in request")
        return redirect(url_for('visualization', order_id=order.id))
    file = request.files['additional_file']
    if file.filename == '':
        flash('No selected file', 'error')
        logging.error("Additional file upload failed: No selected file")
        return redirect(url_for('visualization', order_id=order.id))
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
            logging.info(f"Additional file uploaded successfully: {file_path}")
        except Exception as e:
            flash(f'Error uploading additional file: {str(e)}', 'error')
            logging.error(f"Error uploading additional file: {str(e)}", exc_info=True)
    else:
        flash('Invalid file type', 'error')
        logging.warning(f"Invalid additional file type: {file.filename}")
    return redirect(url_for('visualization', order_id=order.id))