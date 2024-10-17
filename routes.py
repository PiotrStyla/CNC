# ... [keep existing imports] ...

@app.route('/visualization/<int:order_id>')
@login_required
def visualization(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        flash('You do not have permission to view this order.', 'error')
        return redirect(url_for('index'))
    
    file_extension = os.path.splitext(order.technical_drawing)[1].lower()
    return render_template('visualization.html', order=order, file_extension=file_extension)

# ... [keep other existing routes] ...

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

        model_data = process_cad_file(order.technical_drawing)
        if 'error' not in model_data:
            logging.info(f"Model data processed for order_id: {order_id}")
            return jsonify(model_data)
        else:
            logging.error(f"Error processing model data for order_id: {order_id}: {model_data['error']}")
            return jsonify({'error': model_data['error']}), 500
    logging.error(f"Order not found for order_id: {order_id}")
    return jsonify({'error': 'Order not found'}), 404

# ... [keep other existing routes] ...
