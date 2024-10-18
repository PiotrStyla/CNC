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
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_FACE
from OCP.BRep import BRep_Tool
from OCP.GeomAdaptor import GeomAdaptor_Surface
from OCP.GeomAbs import GeomAbs_SurfaceType

logging.basicConfig(level=logging.DEBUG)

ALLOWED_EXTENSIONS = {'stl', 'obj', 'step', 'stp', 'iges', 'igs', 'jpg', 'jpeg', 'png', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_cad_file(filename):
    try:
        file_path = os.path.join('static', 'uploads', filename)
        file_extension = os.path.splitext(filename)[1].lower()
        logging.info(f"Processing file: {filename} with extension: {file_extension}")

        if file_extension in ['.stl']:
            logging.info(f"Processing STL file: {filename}")
            return process_stl_file(file_path)
        elif file_extension in ['.step', '.stp']:
            logging.info(f"Processing STEP file: {filename}")
            return process_step_file(file_path)
        elif file_extension in ['.iges', '.igs']:
            logging.info(f"Processing IGES file: {filename}")
            return process_iges_file(file_path)
        elif file_extension in ['.jpg', '.jpeg', '.png', '.gif']:
            logging.info(f"2D image file detected: {filename}")
            return {
                'type': 'image',
                'filename': filename
            }
        else:
            logging.error(f"Unsupported file type: {filename}")
            return {'error': 'Unsupported file type'}
    except Exception as e:
        logging.exception(f"Error processing CAD file: {filename}")
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
            'size': size.tolist(),
            'surface_types': ['planar'] * len(faces)  # Assuming all faces are planar in STL
        }
    except Exception as e:
        logging.exception(f"Error processing STL file: {file_path}")
        return {'error': f'Error processing STL file: {str(e)}'}

def process_step_file(file_path):
    try:
        # Import the STEP file using cadquery
        model = cq.importers.importStep(file_path)
        
        # Get the vertices and faces
        shape = model.val()
        mesh = BRepMesh_IncrementalMesh(shape, 0.1)
        mesh.Perform()
        
        builder = cq.Workplane("XY").newObject([shape])
        topo = builder.objects[0].toTopology()
        
        vertices = []
        faces = []
        
        for v in topo.Vertices():
            vertices.append([v.X, v.Y, v.Z])
        
        for f in topo.Faces():
            face = []
            for v in f.Vertices():
                face.append(vertices.index([v.X, v.Y, v.Z]))
            faces.append(face)
        
        # Calculate bounding box
        bbox = shape.BoundingBox()
        center = [(bbox.xmin + bbox.xmax) / 2, (bbox.ymin + bbox.ymax) / 2, (bbox.zmin + bbox.zmax) / 2]
        size = [bbox.xmax - bbox.xmin, bbox.ymax - bbox.ymin, bbox.zmax - bbox.zmin]
        
        # Extract surface types
        surface_types = []
        explorer = TopExp_Explorer(shape, TopAbs_FACE)
        while explorer.More():
            face = explorer.Current()
            surface = BRep_Tool.Surface(face)
            adaptor = GeomAdaptor_Surface(surface)
            surface_type = adaptor.GetType()
            surface_types.append(str(GeomAbs_SurfaceType(surface_type)))
            explorer.Next()
        
        return {
            'vertices': vertices,
            'faces': faces,
            'center': center,
            'size': size,
            'surface_types': surface_types
        }
    except Exception as e:
        logging.exception(f"Error processing STEP file: {file_path}")
        return {'error': f'Error processing STEP file: {str(e)}'}

def process_iges_file(file_path):
    try:
        # Import the IGES file using cadquery
        model = cq.importers.importIges(file_path)
        
        # The rest of the processing is similar to STEP files
        shape = model.val()
        mesh = BRepMesh_IncrementalMesh(shape, 0.1)
        mesh.Perform()
        
        builder = cq.Workplane("XY").newObject([shape])
        topo = builder.objects[0].toTopology()
        
        vertices = []
        faces = []
        
        for v in topo.Vertices():
            vertices.append([v.X, v.Y, v.Z])
        
        for f in topo.Faces():
            face = []
            for v in f.Vertices():
                face.append(vertices.index([v.X, v.Y, v.Z]))
            faces.append(face)
        
        # Calculate bounding box
        bbox = shape.BoundingBox()
        center = [(bbox.xmin + bbox.xmax) / 2, (bbox.ymin + bbox.ymax) / 2, (bbox.zmin + bbox.zmax) / 2]
        size = [bbox.xmax - bbox.xmin, bbox.ymax - bbox.ymin, bbox.zmax - bbox.zmax]
        
        # Extract surface types
        surface_types = []
        explorer = TopExp_Explorer(shape, TopAbs_FACE)
        while explorer.More():
            face = explorer.Current()
            surface = BRep_Tool.Surface(face)
            adaptor = GeomAdaptor_Surface(surface)
            surface_type = adaptor.GetType()
            surface_types.append(str(GeomAbs_SurfaceType(surface_type)))
            explorer.Next()
        
        return {
            'vertices': vertices,
            'faces': faces,
            'center': center,
            'size': size,
            'surface_types': surface_types
        }
    except Exception as e:
        logging.exception(f"Error processing IGES file: {file_path}")
        return {'error': f'Error processing IGES file: {str(e)}'}
