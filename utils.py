import os
import numpy as np
from stl import mesh
import logging
import struct
import cadquery as cq
from OCP.STEPControl import STEPControl_Reader
from OCP.IGESControl import IGESControl_Reader
from OCP.IFSelect import IFSelect_RetDone
from OCP.gp import gp_Pnt

logging.basicConfig(level=logging.DEBUG)

ALLOWED_EXTENSIONS = {'stl', 'obj', 'step', 'stp', 'iges', 'igs', 'jpg', 'jpeg', 'png', 'gif'}

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
        logging.error(f"File not found: {file_path}")
        return {'valid': False, 'message': "File not found"}

    if not file_path.lower().endswith('.stl'):
        logging.error(f"Not an STL file: {file_path}")
        return {'valid': False, 'message': "Not an STL file"}

    file_size = os.path.getsize(file_path)
    if file_size < 84:  # Minimum size for a valid STL file
        logging.error(f"File too small to be a valid STL: {file_path}")
        return {'valid': False, 'message': "File too small to be a valid STL"}

    try:
        with open(file_path, 'rb') as f:
            if is_binary_stl(file_path):
                # Binary STL validation
                f.seek(80)
                face_count = struct.unpack('<I', f.read(4))[0]
                expected_size = 84 + face_count * 50
                if file_size != expected_size:
                    logging.error(f"Invalid binary STL file size: {file_path}. Expected {expected_size} bytes, got {file_size} bytes")
                    return {'valid': False, 'message': f"Invalid binary STL file size. Expected {expected_size} bytes, got {file_size} bytes"}
                
                # Check for valid normals and vertices
                for _ in range(face_count):
                    normal = struct.unpack('<3f', f.read(12))
                    vertices = [struct.unpack('<3f', f.read(12)) for _ in range(3)]
                    attr_byte_count = struct.unpack('<H', f.read(2))[0]
                    if any(not -1 <= x <= 1 for x in normal) or any(not -1e6 <= x <= 1e6 for v in vertices for x in v):
                        logging.error(f"Invalid normal or vertex values in binary STL: {file_path}")
                        return {'valid': False, 'message': "Invalid normal or vertex values in binary STL"}
            else:
                # ASCII STL validation
                f.seek(0)
                first_line = f.readline().strip().lower()
                if not first_line.startswith(b'solid'):
                    logging.error(f"Invalid ASCII STL file: {file_path}. Doesn't start with 'solid'")
                    return {'valid': False, 'message': "Invalid ASCII STL file: doesn't start with 'solid'"}
                
                # Check for 'endsolid' at the end
                f.seek(-80, 2)  # Go to last 80 bytes
                last_80_bytes = f.read().lower()
                if b'endsolid' not in last_80_bytes:
                    logging.error(f"Invalid ASCII STL file: {file_path}. Missing 'endsolid'")
                    return {'valid': False, 'message': "Invalid ASCII STL file: missing 'endsolid'"}
                
                # Check for valid facets
                f.seek(0)
                content = f.read().decode('utf-8', errors='ignore').lower()
                if content.count('facet normal') != content.count('endfacet'):
                    logging.error(f"Invalid ASCII STL file: {file_path}. Mismatched facet count")
                    return {'valid': False, 'message': "Invalid ASCII STL file: mismatched facet count"}

    except Exception as e:
        logging.error(f"Error validating STL file: {file_path}. Error: {str(e)}")
        return {'valid': False, 'message': f"Error validating STL file: {str(e)}"}

    logging.info(f"STL file validated successfully: {file_path}")
    return {'valid': True, 'message': "STL file is valid"}

def process_cad_file(filename):
    try:
        file_path = os.path.join('static', 'uploads', filename)
        if filename.lower().endswith('.stl'):
            logging.info(f"Processing STL file: {filename}")
            return process_stl_file(file_path)
        elif filename.lower().endswith(('.step', '.stp')):
            logging.info(f"Processing STEP file: {filename}")
            return process_step_file(file_path)
        elif filename.lower().endswith(('.iges', '.igs')):
            logging.info(f"Processing IGES file: {filename}")
            return process_iges_file(file_path)
        elif filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
            logging.info(f"2D image file detected: {filename}")
            return {
                'type': 'image',
                'filename': filename
            }
        else:
            logging.error(f"Unsupported file type: {filename}")
            return {'error': 'Unsupported file type'}
    except Exception as e:
        logging.error(f"Error processing CAD file: {str(e)}", exc_info=True)
        return {'error': f'An unexpected error occurred: {str(e)}'}

def process_stl_file(file_path):
    try:
        stl_mesh = mesh.Mesh.from_file(file_path)
        vertices = stl_mesh.vectors.reshape([-1, 3]).tolist()
        faces = np.arange(len(vertices)).reshape([-1, 3]).tolist()
        center = np.mean(stl_mesh.vectors.reshape([-1, 3]), axis=0)
        size = np.max(stl_mesh.vectors.reshape([-1, 3]), axis=0) - np.min(stl_mesh.vectors.reshape([-1, 3]), axis=0)
        
        return {
            'vertices': vertices,
            'faces': faces,
            'center': center.tolist(),
            'size': size.tolist()
        }
    except Exception as e:
        logging.error(f"Error processing STL file: {str(e)}")
        return {'error': f'Error processing STL file: {str(e)}'}

def process_step_file(file_path):
    try:
        reader = STEPControl_Reader()
        status = reader.ReadFile(file_path)
        
        if status == IFSelect_RetDone:
            reader.TransferRoots()
            shape = reader.Shape()
            return process_shape(shape)
        else:
            logging.error(f"Failed to read STEP file: {file_path}")
            return {'error': 'Failed to read STEP file'}
    except Exception as e:
        logging.error(f"Error processing STEP file: {str(e)}")
        return {'error': f'Error processing STEP file: {str(e)}'}

def process_iges_file(file_path):
    try:
        reader = IGESControl_Reader()
        status = reader.ReadFile(file_path)
        
        if status == IFSelect_RetDone:
            reader.TransferRoots()
            shape = reader.Shape()
            return process_shape(shape)
        else:
            logging.error(f"Failed to read IGES file: {file_path}")
            return {'error': 'Failed to read IGES file'}
    except Exception as e:
        logging.error(f"Error processing IGES file: {str(e)}")
        return {'error': f'Error processing IGES file: {str(e)}'}

def process_shape(shape):
    try:
        mesh = cq.Mesh.fromShape(shape)
        vertices = [(v.X, v.Y, v.Z) for v in mesh.vertices]
        faces = [tuple(f) for f in mesh.triangles]
        
        # Calculate center and size
        bbox = shape.BoundingBox()
        center = ((bbox.xmin + bbox.xmax) / 2, (bbox.ymin + bbox.ymax) / 2, (bbox.zmin + bbox.zmax) / 2)
        size = (bbox.xmax - bbox.xmin, bbox.ymax - bbox.ymin, bbox.zmax - bbox.zmin)
        
        return {
            'vertices': vertices,
            'faces': faces,
            'center': center,
            'size': size
        }
    except Exception as e:
        logging.error(f"Error processing shape: {str(e)}")
        return {'error': f'Error processing shape: {str(e)}'}

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

        logging.info(f"STL file repaired successfully: {file_path}")
        return {'success': True, 'message': "STL file repaired successfully", 'repaired_file': repaired_file_path}
    except Exception as e:
        logging.error(f"Failed to repair STL file: {file_path}. Error: {str(e)}")
        return {'success': False, 'message': f"Failed to repair STL file: {str(e)}"}
