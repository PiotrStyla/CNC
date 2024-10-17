from build123d import *
import os

def create_sample_model():
    with BuildPart() as model:
        # Base cube
        Box(10, 10, 10)
        
        # Cylinder on top
        with Locations((0, 0, 10)):
            Cylinder(radius=3, height=5)
        
        # Sphere on one side
        with Locations((5, 0, 5)):
            Sphere(radius=2)
        
        # Cone on another side
        with Locations((-5, 0, 5)):
            Cone(bottom_radius=2, top_radius=0, height=4)
        
        # Torus on front
        with Locations((0, 5, 5)):
            Torus(major_radius=2, minor_radius=0.5)
    
    return model.part

if __name__ == "__main__":
    sample_model = create_sample_model()
    
    # Try to use export_step if available
    try:
        from build123d.exporters import export_step
        export_step(sample_model, "sample_cad_model.step")
        print("Sample STEP file 'sample_cad_model.step' has been generated using build123d.")
    except ImportError:
        print("export_step not available in build123d. Falling back to cadquery.")
        
        # Fallback to cadquery
        import cadquery as cq
        
        # Convert build123d model to cadquery workplane
        cq_model = cq.Workplane("XY").add(sample_model)
        
        # Export to STEP format
        cq.exporters.export(cq_model, 'sample_cad_model.step')
        print("Sample STEP file 'sample_cad_model.step' has been generated using cadquery.")

    # Verify the file was created
    if os.path.exists("sample_cad_model.step"):
        print("STEP file created successfully.")
    else:
        print("Failed to create STEP file.")
