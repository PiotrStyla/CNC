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
        const renderer = new THREE.WebGLRenderer({ canvas: canvas });

        renderer.setSize(canvas.clientWidth, canvas.clientHeight);

        // Add a simple cube as a placeholder
        const geometry = new THREE.BoxGeometry();
        const material = new THREE.MeshBasicMaterial({ color: 0x00ff00, wireframe: true });
        const cube = new THREE.Mesh(geometry, material);
        scene.add(cube);

        camera.position.z = 5;

        function animate() {
            requestAnimationFrame(animate);
            cube.rotation.x += 0.01;
            cube.rotation.y += 0.01;
            renderer.render(scene, camera);
        }

        animate();
    }
});
