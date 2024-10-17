import os
from flask import render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from app import app, db, socketio
from models import User, Order
from utils import allowed_file, process_cad_file, validate_stl_file, repair_stl_file
import logging
from flask_login import login_user, login_required, logout_user, current_user
from flask_socketio import emit, join_room, leave_room

logging.basicConfig(level=logging.DEBUG)

@app.route('/')
def index():
    return render_template('index.html')

# ... [keep other existing routes] ...

@app.route('/visualization/<int:order_id>')
@login_required
def visualization(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        flash('You do not have permission to view this order.', 'error')
        return redirect(url_for('index'))
    
    file_extension = os.path.splitext(order.technical_drawing)[1].lower()
    return render_template('visualization.html', order=order, file_extension=file_extension)

@app.route('/get_model_data/<int:order_id>')
@login_required
def get_model_data(order_id):
    logging.info(f"get_model_data called for order_id: {order_id}")
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        logging.warning(f"Unauthorized access attempt for order_id: {order_id}")
        return jsonify({'error': 'Unauthorized access'}), 403
    
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], order.technical_drawing)
    file_extension = os.path.splitext(order.technical_drawing)[1].lower()
    logging.info(f"File path: {file_path}, File extension: {file_extension}")

    try:
        if file_extension in ['.jpg', '.jpeg', '.png', '.gif']:
            return jsonify({
                'type': 'image',
                'filename': order.technical_drawing
            })
        else:
            model_data = process_cad_file(file_path)
            if 'error' not in model_data:
                logging.info(f"Model data processed successfully for order_id: {order_id}")
                return jsonify(model_data)
            else:
                logging.error(f"Error processing model data for order_id: {order_id}: {model_data['error']}")
                return jsonify({'error': model_data['error']}), 500
    except Exception as e:
        logging.exception(f"Unexpected error processing model data for order_id: {order_id}")
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500

# ... [keep other existing routes] ...
