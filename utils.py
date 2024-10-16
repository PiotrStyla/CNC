import os

ALLOWED_EXTENSIONS = {'stl', 'obj', 'step', 'stp', 'jpg', 'jpeg', 'png', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_cad_file(filename):
    # This function would typically involve more complex processing
    # For this example, we'll just return the filename
    return filename
