console.log('main.js is being executed', new Date().toISOString());

import * as THREE from 'https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.module.js';
import { OrbitControls } from 'https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/examples/jsm/controls/OrbitControls.js';

console.log('Imports completed');
console.log('Three.js version:', THREE ? THREE.REVISION : 'not loaded');
console.log('OrbitControls imported:', typeof OrbitControls !== 'undefined' ? 'yes' : 'no');

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOMContentLoaded event fired');

    const fileInput = document.getElementById('technical_drawing');
    const uploadForm = document.querySelector('form');
    const uploadButton = document.querySelector('button[type="submit"]');
    const feedbackDiv = document.createElement('div');
    feedbackDiv.className = 'mt-3';
    
    if (uploadForm) {
        uploadForm.appendChild(feedbackDiv);
    }

    if (fileInput) {
        fileInput.addEventListener('change', function(e) {
            if (e.target.files.length > 0) {
                let fileName = e.target.files[0].name;
                fileInput.nextElementSibling.textContent = fileName;
            } else {
                fileInput.nextElementSibling.textContent = 'Choose file';
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

    if (document.getElementById('3d-preview')) {
        console.log('3D preview canvas found, initializing visualization');
        initializeVisualization();
    } else {
        console.log('3D preview canvas not found, skipping visualization initialization');
    }

    const deleteButtons = document.querySelectorAll('.delete-file');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const orderId = this.getAttribute('data-order-id');
            const filename = this.getAttribute('data-filename');
            if (confirm('Are you sure you want to delete this file?')) {
                deleteFile(orderId, filename);
            }
        });
    });
});

function initializeVisualization() {
    console.log('initializeVisualization function called');
    const canvas = document.getElementById('3d-preview');
    const imagePreview = document.getElementById('image-preview');
    const loadingIndicator = document.getElementById('loading-indicator');
    const fallbackMessage = document.getElementById('fallback-message');
    if (canvas) {
        console.log('Canvas found, dimensions:', canvas.clientWidth, 'x', canvas.clientHeight);
        let scene, camera, renderer, mesh, controls;

        function initScene() {
            console.log('Initializing Three.js scene');
            try {
                scene = new THREE.Scene();
                camera = new THREE.PerspectiveCamera(75, canvas.clientWidth / canvas.clientHeight, 0.1, 1000);
                renderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: true });

                renderer.setSize(canvas.clientWidth, canvas.clientHeight);
                renderer.setClearColor(0x000000, 1);
                console.log('Renderer size:', renderer.getSize(new THREE.Vector2()));

                const ambientLight = new THREE.AmbientLight(0x404040);
                scene.add(ambientLight);
                const directionalLight = new THREE.DirectionalLight(0xffffff, 0.5);
                directionalLight.position.set(1, 1, 1);
                scene.add(directionalLight);

                camera.position.z = 5;

                controls = new OrbitControls(camera, renderer.domElement);
                controls.enableDamping = true;
                controls.dampingFactor = 0.25;
                controls.enableZoom = true;

                console.log('Scene initialized successfully');
            } catch (error) {
                console.error('Error initializing Three.js scene:', error);
                showFeedback('Error initializing 3D scene. Please try refreshing the page.', 'error');
            }
        }

        function loadModel() {
            console.log('loadModel function called');
            const currentUrl = window.location.href;
            const orderId = currentUrl.split('/').pop();
            console.log('Current URL:', currentUrl);
            console.log('Order ID:', orderId);
            
            if (loadingIndicator) loadingIndicator.style.display = 'block';
            if (fallbackMessage) fallbackMessage.style.display = 'none';

            fetch(`/get_model_data/${orderId}`)
                .then(response => { 
                    console.log('Response status:', response.status);
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    return response.json(); 
                })
                .then(data => {
                    console.log('Model data received:', data);
                    if (data.type === 'image') {
                        console.log('Displaying 2D image');
                        displayImage(data.filename);
                    } else if (data.vertices && data.faces) {
                        console.log('Displaying 3D model');
                        display3DModel(data);
                    } else {
                        console.error('Invalid model data received:', data);
                        throw new Error('Invalid model data received');
                    }
                })
                .catch(error => {
                    console.error('Error loading model:', error);
                    showFeedback('Error loading model. Please try uploading the file again.', 'error');
                    if (fallbackMessage) {
                        fallbackMessage.textContent = `Error loading model: ${error.message}. File name: ${orderId}`;
                        fallbackMessage.style.display = 'block';
                    }
                })
                .finally(() => {
                    if (loadingIndicator) loadingIndicator.style.display = 'none';
                });
        }

        function displayImage(filename) {
            console.log('Displaying 2D image:', filename);
            canvas.style.display = 'none';
            imagePreview.style.display = 'block';
            imagePreview.src = `/static/uploads/${filename}`;
            imagePreview.alt = 'Uploaded Image';
            console.log('Image displayed successfully');
        }

        function display3DModel(data) {
            console.log('Displaying 3D model');
            canvas.style.display = 'block';
            imagePreview.style.display = 'none';

            try {
                const geometry = new THREE.BufferGeometry();
                geometry.setAttribute('position', new THREE.Float32BufferAttribute(data.vertices.flat(), 3));
                geometry.setIndex(data.faces.flat());
                geometry.computeVertexNormals();

                const material = new THREE.MeshPhongMaterial({ color: 0x00ff00, wireframe: false });
                mesh = new THREE.Mesh(geometry, material);

                mesh.position.set(-data.center[0], -data.center[1], -data.center[2]);
                const scale = 5 / Math.max(...data.size);
                mesh.scale.set(scale, scale, scale);

                scene.add(mesh);
                console.log('Model added to scene');

                const boundingBox = new THREE.Box3().setFromObject(mesh);
                const center = boundingBox.getCenter(new THREE.Vector3());
                const size = boundingBox.getSize(new THREE.Vector3());
                console.log('Model size:', size);

                const maxDim = Math.max(size.x, size.y, size.z);
                const fov = camera.fov * (Math.PI / 180);
                let cameraZ = Math.abs(maxDim / 2 / Math.tan(fov / 2));

                camera.position.z = cameraZ * 1.5;
                camera.updateProjectionMatrix();

                controls.target.copy(center);
                controls.update();
                console.log('Camera and controls updated');
            } catch (error) {
                console.error('Error displaying 3D model:', error);
                showFeedback('Error displaying 3D model. Please try uploading the file again.', 'error');
                if (fallbackMessage) {
                    fallbackMessage.textContent = `Error displaying 3D model: ${error.message}`;
                    fallbackMessage.style.display = 'block';
                }
            }
        }

        function animate() {
            requestAnimationFrame(animate);
            if (controls) controls.update();
            if (mesh) mesh.rotation.y += 0.01;
            if (renderer && scene && camera) {
                renderer.render(scene, camera);
            } else {
                console.error('Renderer, scene, or camera is not initialized');
            }
        }

        function handleResize() {
            console.log('Window resized');
            if (camera && renderer) {
                camera.aspect = canvas.clientWidth / canvas.clientHeight;
                camera.updateProjectionMatrix();
                renderer.setSize(canvas.clientWidth, canvas.clientHeight);
                console.log('New renderer size:', renderer.getSize(new THREE.Vector2()));
            }
        }

        initScene();
        loadModel();
        animate();

        window.addEventListener('resize', handleResize);
    } else {
        console.error('3D preview canvas not found');
        showFeedback('Error: 3D preview canvas not found', 'error');
    }
}

function showFeedback(message, type) {
    const feedbackDiv = document.querySelector('.feedback');
    if (feedbackDiv) {
        feedbackDiv.innerHTML = `<div class="alert alert-${type}" role="alert">${message}</div>`;
    } else {
        console.error('Feedback div not found');
    }
}

function getOrderIdFromHtml(html) {
    const parser = new DOMParser();
    const doc = parser.parseFromString(html, 'text/html');
    const orderIdElement = doc.querySelector('[data-order-id]');
    return orderIdElement ? orderIdElement.dataset.orderId : null;
}

function deleteFile(orderId, filename) {
    console.log(`Deleting file: ${filename} for order: ${orderId}`);
    fetch(`/delete_file/${orderId}/${filename}`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('File deleted successfully');
            const fileElement = document.querySelector(`[data-filename="${filename}"]`);
            if (fileElement) {
                fileElement.remove();
                console.log('File element removed from DOM');
            } else {
                console.warn('File element not found in DOM');
            }
            showFeedback(data.message, 'success');
            if (data.redirect) {
                console.log('Redirecting to:', data.redirect);
                window.location.href = data.redirect;
            } else {
                console.log('Reloading page to reflect changes');
                window.location.reload();
            }
        } else {
            console.error('Error deleting file:', data.message);
            showFeedback(data.message, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showFeedback('Error deleting file. Please try again.', 'error');
    });
}