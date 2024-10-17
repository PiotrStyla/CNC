import os
from flask import render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from app import app, db
from models import User, Order
from utils import allowed_file, process_cad_file, validate_stl_file, repair_stl_file
import logging
from flask_login import login_user, login_required, logout_user, current_user

logging.basicConfig(level=logging.DEBUG)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user:
            flash('Username already exists', 'error')
            return redirect(url_for('register'))
        
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exists', 'error')
            return redirect(url_for('register'))
        
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully.', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Invalid username or password', 'error')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))

@app.route('/upload', methods=['GET', 'POST'])
@login_required
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
                
                if filename.lower().endswith('.stl'):
                    validation_result = validate_stl_file(file_path)
                    if not validation_result['valid']:
                        logging.warning(f"STL file validation failed: {validation_result['message']}")
                        
                        repair_result = repair_stl_file(file_path)
                        if repair_result['success']:
                            file_path = repair_result['repaired_file']
                            filename = os.path.basename(file_path)
                            flash(f"File was repaired: {repair_result['message']}", 'warning')
                            logging.info(f"STL file repaired: {file_path}")
                        else:
                            os.remove(file_path)
                            flash(f"Invalid or corrupted STL file: {validation_result['message']}", 'error')
                            logging.error(f"STL file validation failed and repair unsuccessful: {validation_result['message']}")
                            return redirect(request.url)
                
                order = Order(technical_drawing=filename, user_id=current_user.id)
                db.session.add(order)
                db.session.commit()
                logging.info(f"New order created with ID: {order.id} and filename: {filename}")
                
                flash('File uploaded and processed successfully', 'success')
                return redirect(url_for('visualization', order_id=order.id))
            except Exception as e:
                logging.error(f"Error uploading file: {str(e)}", exc_info=True)
                flash(f'Error uploading file: {str(e)}', 'error')
                return redirect(request.url)
        else:
            logging.warning(f"Invalid file type: {file.filename}")
            flash('Invalid file type. Please upload a supported file format (STL, OBJ, STEP, STP, JPG, JPEG, PNG, GIF).', 'error')
    return render_template('upload.html')

@app.route('/visualization/<int:order_id>')
@login_required
def visualization(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        flash('You do not have permission to view this order.', 'error')
        return redirect(url_for('index'))
    return render_template('visualization.html', order=order)

@app.route('/get_model_data/<int:order_id>')
@login_required
def get_model_data(order_id):
    logging.info(f"get_model_data called for order_id: {order_id}")
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized access'}), 403
    if order:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], order.technical_drawing)
        file_extension = os.path.splitext(order.technical_drawing)[1].lower()
        logging.info(f"File path: {file_path}, File extension: {file_extension}")

        if file_extension in ['.stl', '.obj', '.step', '.stp']:
            logging.info(f"Processing 3D file: {order.technical_drawing}")
            model_data = process_cad_file(order.technical_drawing)
            if model_data:
                logging.info(f"3D model data processed for order_id: {order_id}")
                logging.debug(f"Model data: {model_data}")
                return jsonify(model_data)
            else:
                logging.error(f"Error processing 3D model data for order_id: {order_id}")
                return jsonify({'error': 'Error processing 3D model data'}), 500
        elif file_extension in ['.jpg', '.jpeg', '.png', '.gif']:
            logging.info(f"2D image file detected for order_id: {order_id}")
            return jsonify({
                'type': 'image',
                'filename': order.technical_drawing
            })
        else:
            logging.error(f"Unsupported file type for order_id: {order_id}")
            return jsonify({'error': 'Unsupported file type'}), 400
    logging.error(f"Order not found for order_id: {order_id}")
    return jsonify({'error': 'Order not found'}), 404

@app.route('/order_management')
@login_required
def order_management():
    orders = Order.query.filter_by(user_id=current_user.id).all()
    return render_template('order_management.html', orders=orders)

@app.route('/add_comment/<int:order_id>', methods=['POST'])
@login_required
def add_comment(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        flash('You do not have permission to add comments to this order.', 'error')
        return redirect(url_for('index'))
    comment = request.form.get('comment')
    if comment:
        order.comments = order.comments + '\n' + comment if order.comments else comment
        db.session.commit()
        flash('Comment added successfully', 'success')
    return redirect(url_for('visualization', order_id=order.id))

@app.route('/upload_additional_file/<int:order_id>', methods=['POST'])
@login_required
def upload_additional_file(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        flash('You do not have permission to upload files to this order.', 'error')
        return redirect(url_for('index'))
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

@app.route('/delete_file/<int:order_id>/<filename>', methods=['POST'])
@login_required
def delete_file(order_id, filename):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized access'}), 403
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    logging.info(f"Attempting to delete file: {file_path}")
    
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            logging.info(f"File deleted from file system: {file_path}")
            
            if filename == order.technical_drawing:
                db.session.delete(order)
                logging.info(f"Deleted order {order_id} as its technical drawing was deleted")
                db.session.commit()
                flash('File and order deleted successfully', 'success')
                return jsonify({'success': True, 'message': 'File and order deleted successfully', 'redirect': url_for('order_management')})
            elif order.additional_files:
                files = order.additional_files.split(',')
                if filename in files:
                    files.remove(filename)
                    order.additional_files = ','.join(files)
                    logging.info(f"Removed {filename} from additional files for order {order_id}")
                    db.session.commit()
                    flash('File deleted successfully', 'success')
                    return jsonify({'success': True, 'message': 'File deleted successfully'})
            
            logging.info(f"Database updated successfully for order {order_id}")
        except Exception as e:
            db.session.rollback()
            error_message = f'Error deleting file: {str(e)}'
            flash(error_message, 'error')
            logging.error(error_message, exc_info=True)
            return jsonify({'success': False, 'message': error_message}), 500
    else:
        error_message = f'File not found: {file_path}'
        flash(error_message, 'error')
        logging.warning(error_message)
        return jsonify({'success': False, 'message': error_message}), 404

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)
