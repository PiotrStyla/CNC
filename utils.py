import os
import numpy as np
from stl import mesh

ALLOWED_EXTENSIONS = {'stl', 'obj', 'step', 'stp', 'jpg', 'jpeg', 'png', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_cad_file(filename):
    try:
        file_path = os.path.join('static', 'uploads', filename)
        if filename.lower().endswith('.stl'):
            # Load the STL file
            stl_mesh = mesh.Mesh.from_file(file_path)
            
            # Calculate the center of the mesh
            center = np.mean(stl_mesh.vectors.reshape([-1, 3]), axis=0)
            
            # Calculate the size of the mesh
            size = np.max(stl_mesh.vectors.reshape([-1, 3]), axis=0) - np.min(stl_mesh.vectors.reshape([-1, 3]), axis=0)
            
            # Prepare data for Three.js
            vertices = stl_mesh.vectors.reshape([-1, 3]).tolist()
            faces = np.arange(len(vertices)).reshape([-1, 3]).tolist()
            
            return {
                'vertices': vertices,
                'faces': faces,
                'center': center.tolist(),
                'size': size.tolist()
            }
        else:
            # For other file types, we'll just return basic information for now
            return {
                'filename': filename,
                'type': filename.rsplit('.', 1)[1].lower()
            }
    except Exception as e:
        print(f"Error processing CAD file: {str(e)}")
        return None
