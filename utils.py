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

    file_size = os.path.getsize(file_path)
    if file_size < 84:  # Minimum size for a valid STL file
        return {'valid': False, 'message': "File too small to be a valid STL"}

    try:
        with open(file_path, 'rb') as f:
            if is_binary_stl(file_path):
                # Binary STL validation
                f.seek(80)
                face_count = struct.unpack('<I', f.read(4))[0]
                expected_size = 84 + face_count * 50
                if file_size != expected_size:
                    return {'valid': False, 'message': f"Invalid binary STL file size. Expected {expected_size} bytes, got {file_size} bytes"}
                
                # Check for valid normals and vertices
                for _ in range(face_count):
                    normal = struct.unpack('<3f', f.read(12))
                    for _ in range(3):  # 3 vertices per face
                        vertex = struct.unpack('<3f', f.read(12))
                    attr_byte_count = struct.unpack('<H', f.read(2))[0]
                    if any(not -1 <= x <= 1 for x in normal) or any(not -1e6 <= x <= 1e6 for x in vertex):
                        return {'valid': False, 'message': "Invalid normal or vertex values in binary STL"}
            else:
                # ASCII STL validation
                f.seek(0)
                first_line = f.readline().strip().lower()
                if not first_line.startswith(b'solid'):
                    return {'valid': False, 'message': "Invalid ASCII STL file: doesn't start with 'solid'"}
                
                # Check for 'endsolid' at the end
                f.seek(-80, 2)  # Go to last 80 bytes
                last_80_bytes = f.read().lower()
                if b'endsolid' not in last_80_bytes:
                    return {'valid': False, 'message': "Invalid ASCII STL file: missing 'endsolid'"}
                
                # Check for valid facets
                f.seek(0)
                content = f.read().decode('utf-8', errors='ignore').lower()
                if content.count('facet normal') != content.count('endfacet'):
                    return {'valid': False, 'message': "Invalid ASCII STL file: mismatched facet count"}

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

def repair_stl_file(file_path):
    try:
        # Load the STL file
        original_mesh = mesh.Mesh.from_file(file_path)

        # Remove duplicate vertices
        vertices, indices = np.unique(original_mesh.vectors.reshape([-1, 3]), axis=0, return_inverse=True)
        faces = indices.reshape([-1, 3])

        # Create a new mesh with cleaned data
        repaired_mesh = mesh.Mesh(np.zeros(faces.shape[0], dtype=mesh.Mesh.dtype))
        for i, f in enumerate(faces):
            repaired_mesh.vectors[i] = vertices[f]

        # Save the repaired mesh
        repaired_file_path = file_path.replace('.stl', '_repaired.stl')
        repaired_mesh.save(repaired_file_path)

        return {'success': True, 'message': "STL file repaired successfully", 'repaired_file': repaired_file_path}
    except Exception as e:
        return {'success': False, 'message': f"Failed to repair STL file: {str(e)}"}
