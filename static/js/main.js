document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.getElementById('technical_drawing');
    const fileLabel = document.querySelector('.custom-file-label');

    if (fileInput) {
        fileInput.addEventListener('change', function(e) {
            let fileName = e.target.files[0].name;
            fileLabel.textContent = fileName;
        });
    }

    // 3D Visualization
    const canvas = document.getElementById('3d-preview');
    if (canvas) {
        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(75, canvas.clientWidth / canvas.clientHeight, 0.1, 1000);
        const renderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: true });

        renderer.setSize(canvas.clientWidth, canvas.clientHeight);

        // Add lights
        const ambientLight = new THREE.AmbientLight(0x404040);
        scene.add(ambientLight);
        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.5);
        directionalLight.position.set(1, 1, 1);
        scene.add(directionalLight);

        // Load the 3D model
        const loader = new THREE.BufferGeometryLoader();
        fetch('/get_model_data')
            .then(response => response.json())
            .then(data => {
                if (data.vertices && data.faces) {
                    const geometry = new THREE.BufferGeometry();
                    geometry.setAttribute('position', new THREE.Float32BufferAttribute(data.vertices.flat(), 3));
                    geometry.setIndex(data.faces.flat());
                    geometry.computeVertexNormals();

                    const material = new THREE.MeshPhongMaterial({ color: 0x00ff00, wireframe: false });
                    const mesh = new THREE.Mesh(geometry, material);

                    // Center and scale the model
                    mesh.position.set(-data.center[0], -data.center[1], -data.center[2]);
                    const scale = 5 / Math.max(...data.size);
                    mesh.scale.set(scale, scale, scale);

                    scene.add(mesh);

                    // Adjust camera position
                    camera.position.z = 10;

                    function animate() {
                        requestAnimationFrame(animate);
                        mesh.rotation.x += 0.01;
                        mesh.rotation.y += 0.01;
                        renderer.render(scene, camera);
                    }

                    animate();
                } else {
                    console.error('Invalid model data received');
                }
            })
            .catch(error => console.error('Error loading 3D model:', error));

        // Handle window resize
        window.addEventListener('resize', function() {
            camera.aspect = canvas.clientWidth / canvas.clientHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(canvas.clientWidth, canvas.clientHeight);
        });
    }
});
