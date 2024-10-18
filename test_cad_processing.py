import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import process_cad_file
import json

def test_process_cad_file():
    filename = "sample_cad_model.step"
    result = process_cad_file(filename)
    
    print("CAD Processing Result:")
    print(json.dumps(result, indent=2))
    
    if 'error' in result:
        print(f"Error processing CAD file: {result['error']}")
    else:
        print("CAD file processed successfully!")
        print(f"Number of vertices: {len(result['vertices'])}")
        print(f"Number of faces: {len(result['faces'])}")
        print(f"Center: {result['center']}")
        print(f"Size: {result['size']}")
        print(f"Surface types: {result['surface_types']}")

if __name__ == "__main__":
    test_process_cad_file()
