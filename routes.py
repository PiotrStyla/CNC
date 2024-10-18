import os
from flask import render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from app import app, db, socketio
from models import User, Order
from utils import allowed_file, process_cad_file
import logging
from flask_login import login_user, login_required, logout_user, current_user
from flask_socketio import emit, join_room, leave_room

logging.basicConfig(level=logging.DEBUG)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully.', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password.', 'error')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user:
            flash('Username already exists.', 'error')
        else:
            new_user = User(username=username, email=email)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            flash('Registered successfully. Please log in.', 'success')
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/upload', methods=['GET', 'POST'])
@login_required
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
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            new_order = Order(technical_drawing=filename, user_id=current_user.id)
            db.session.add(new_order)
            db.session.commit()
            flash('File uploaded successfully', 'success')
            return redirect(url_for('visualization', order_id=new_order.id))
    return render_template('upload.html')

@app.route('/order_management')
@login_required
def order_management():
    orders = Order.query.filter_by(user_id=current_user.id).all()
    return render_template('order_management.html', orders=orders)

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
        model_data = process_cad_file(order.technical_drawing)
        if 'error' not in model_data:
            logging.info(f"Model data processed successfully for order_id: {order_id}")
            return jsonify(model_data)
        else:
            logging.error(f"Error processing model data for order_id: {order_id}: {model_data['error']}")
            return jsonify({'error': model_data['error']}), 500
    except Exception as e:
        logging.exception(f"Unexpected error processing model data for order_id: {order_id}")
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500

@app.route('/chat')
@login_required
def chat():
    return render_template('chat.html')

@socketio.on('join')
def on_join(data):
    username = current_user.username
    room = data['room']
    join_room(room)
    emit('status', {'msg': username + ' has entered the room.'}, room=room)

@socketio.on('leave')
def on_leave(data):
    username = current_user.username
    room = data['room']
    leave_room(room)
    emit('status', {'msg': username + ' has left the room.'}, room=room)

@socketio.on('message')
def handle_message(data):
    username = current_user.username
    room = data['room']
    emit('message', {'msg': data['msg'], 'username': username}, room=room)
