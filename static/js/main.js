// ... [keep the existing imports and initial setup] ...

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
            // ... [keep the existing initScene function] ...
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
            // ... [keep the existing displayImage function] ...
        }

        function display3DModel(data) {
            console.log('Displaying 3D model');
            canvas.style.display = 'block';
            imagePreview.style.display = 'none';

            try {
                const geometry = new THREE.BufferGeometry();
                const vertices = new Float32Array(data.vertices.flat());
                geometry.setAttribute('position', new THREE.BufferAttribute(vertices, 3));
                
                const faces = new Uint32Array(data.faces.flat());
                geometry.setIndex(new THREE.BufferAttribute(faces, 1));
                
                geometry.computeVertexNormals();

                const materials = [];
                data.surface_types.forEach((type, index) => {
                    const color = new THREE.Color(Math.random(), Math.random(), Math.random());
                    materials.push(new THREE.MeshPhongMaterial({ color: color, wireframe: false }));
                });

                mesh = new THREE.Mesh(geometry, materials);

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

                // Display surface type information
                displaySurfaceInfo(data.surface_types);
            } catch (error) {
                console.error('Error displaying 3D model:', error);
                showFeedback('Error displaying 3D model. Please try uploading the file again.', 'error');
                if (fallbackMessage) {
                    fallbackMessage.textContent = `Error displaying 3D model: ${error.message}`;
                    fallbackMessage.style.display = 'block';
                }
            }
        }

        function displaySurfaceInfo(surfaceTypes) {
            const surfaceInfoContainer = document.getElementById('surface-info');
            if (surfaceInfoContainer) {
                const surfaceTypeCounts = surfaceTypes.reduce((acc, type) => {
                    acc[type] = (acc[type] || 0) + 1;
                    return acc;
                }, {});

                let infoHtml = '<h3>Surface Types</h3><ul>';
                for (const [type, count] of Object.entries(surfaceTypeCounts)) {
                    infoHtml += `<li>${type}: ${count}</li>`;
                }
                infoHtml += '</ul>';

                surfaceInfoContainer.innerHTML = infoHtml;
            }
        }

        function animate() {
            requestAnimationFrame(animate);
            if (controls) controls.update();
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

// ... [keep the remaining functions] ...
