import os
import numpy as np
from stl import mesh
import logging
import struct

logging.basicConfig(level=logging.DEBUG)

ALLOWED_EXTENSIONS = {'stl', 'obj', 'step', 'stp', 'jpg', 'jpeg', 'png', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def is_binary_stl(file_path):
    with open(file_path, 'rb') as f:
        f.seek(80)  # Skip header
        try:
            face_count = struct.unpack('<I', f.read(4))[0]
            return (os.path.getsize(file_path) - 84) % 50 == 0
        except struct.error:
            return False

def validate_stl_file(file_path):
    if not os.path.exists(file_path):
        return {'valid': False, 'message': "File not found"}

    if not file_path.lower().endswith('.stl'):
        return {'valid': False, 'message': "Not an STL file"}

    if os.path.getsize(file_path) < 84:  # Minimum size for a valid STL file
        return {'valid': False, 'message': "File too small to be a valid STL"}

    try:
        with open(file_path, 'rb') as f:
            if is_binary_stl(file_path):
                # Binary STL validation
                f.seek(80)
                face_count = struct.unpack('<I', f.read(4))[0]
                expected_size = 84 + face_count * 50
                if os.path.getsize(file_path) != expected_size:
                    return {'valid': False, 'message': "Invalid binary STL file size"}
            else:
                # ASCII STL validation
                first_line = f.readline().strip().lower()
                if not first_line.startswith(b'solid'):
                    return {'valid': False, 'message': "Invalid ASCII STL file"}
    except Exception as e:
        return {'valid': False, 'message': f"Error validating STL file: {str(e)}"}

    return {'valid': True, 'message': "STL file is valid"}

def process_cad_file(filename):
    try:
        file_path = os.path.join('static', 'uploads', filename)
        if filename.lower().endswith('.stl'):
            logging.info(f"Processing STL file: {filename}")

            validation_result = validate_stl_file(file_path)
            if not validation_result['valid']:
                return {'error': validation_result['message']}

            try:
                # Load the STL file
                stl_mesh = mesh.Mesh.from_file(file_path)

                # Calculate the center of the mesh
                center = np.mean(stl_mesh.vectors.reshape([-1, 3]), axis=0)
                
                # Calculate the size of the mesh
                size = np.max(stl_mesh.vectors.reshape([-1, 3]), axis=0) - np.min(stl_mesh.vectors.reshape([-1, 3]), axis=0)
                
                # Prepare data for Three.js
                vertices = stl_mesh.vectors.reshape([-1, 3]).tolist()
                faces = np.arange(len(vertices)).reshape([-1, 3]).tolist()
                
                logging.info(f"STL file processed successfully: {filename}")
                return {
                    'vertices': vertices,
                    'faces': faces,
                    'center': center.tolist(),
                    'size': size.tolist()
                }
            except ValueError as ve:
                logging.error(f"Error loading STL file: {str(ve)}")
                return {'error': 'Invalid STL file format'}
            except IOError as ioe:
                logging.error(f"Error reading STL file: {str(ioe)}")
                return {'error': 'Unable to read the STL file'}
        else:
            logging.info(f"Non-STL file detected: {filename}")
            # For other file types, we'll just return basic information for now
            return {
                'filename': filename,
                'type': filename.rsplit('.', 1)[1].lower()
            }
    except Exception as e:
        logging.error(f"Error processing CAD file: {str(e)}", exc_info=True)
        return {'error': f'An unexpected error occurred: {str(e)}'}
