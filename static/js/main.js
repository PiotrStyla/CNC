document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.getElementById('technical_drawing');
    const fileLabel = document.querySelector('.custom-file-label');
    const uploadForm = document.querySelector('form');
    const uploadButton = document.querySelector('button[type="submit"]');
    const feedbackDiv = document.createElement('div');
    feedbackDiv.className = 'mt-3';
    uploadForm.appendChild(feedbackDiv);

    if (fileInput) {
        fileInput.addEventListener('change', function(e) {
            if (e.target.files.length > 0) {
                let fileName = e.target.files[0].name;
                fileLabel.textContent = fileName;
            } else {
                fileLabel.textContent = 'Choose file';
            }
        });
    }

    if (uploadForm) {
        uploadForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            if (!fileInput || !fileInput.files[0]) {
                showFeedback('Please select a file to upload.', 'warning');
                return;
            }

            const formData = new FormData(uploadForm);
            uploadButton.disabled = true;
            showFeedback('Uploading file...', 'info');

            fetch('/upload', {
                method: 'POST',
                body: formData
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.text();
            })
            .then(html => {
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, 'text/html');
                const flashMessages = doc.querySelectorAll('.alert');
                
                if (flashMessages.length > 0) {
                    flashMessages.forEach(message => {
                        const messageText = message.textContent.trim();
                        const messageType = message.classList.contains('alert-success') ? 'success' : 
                                            message.classList.contains('alert-warning') ? 'warning' : 'error';
                        showFeedback(messageText, messageType);
                    });
                } else {
                    // If no flash messages, assume success and redirect
                    window.location.href = '/visualization/' + getOrderIdFromHtml(html);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showFeedback('An error occurred while uploading the file. Please try again.', 'error');
            })
            .finally(() => {
                uploadButton.disabled = false;
            });
        });
    }

    function showFeedback(message, type) {
        feedbackDiv.innerHTML = `<div class="alert alert-${type}" role="alert">${message}</div>`;
    }

    function getOrderIdFromHtml(html) {
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');
        const orderIdElement = doc.querySelector('[data-order-id]');
        return orderIdElement ? orderIdElement.dataset.orderId : null;
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
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
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
                    showFeedback('Error loading 3D model. Please try uploading the file again.', 'error');
                }
            })
            .catch(error => {
                console.error('Error loading 3D model:', error);
                showFeedback('Error loading 3D model. Please try uploading the file again.', 'error');
            });

        // Handle window resize
        window.addEventListener('resize', function() {
            camera.aspect = canvas.clientWidth / canvas.clientHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(canvas.clientWidth, canvas.clientHeight);
        });
    }
});
