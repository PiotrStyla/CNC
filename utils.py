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

# ... [keep existing functions] ...

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
        logging.error(f"Error processing STEP file: {str(e)}")
        return {'error': f'Error processing STEP file: {str(e)}'}

# ... [keep other existing functions] ...
