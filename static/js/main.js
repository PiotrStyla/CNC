// ... [keep existing imports and initial setup] ...

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
            canvas.style.display = 'none';
            imagePreview.style.display = 'block';
            imagePreview.src = `/static/uploads/${filename}`;
            imagePreview.onload = function() {
                const container = document.getElementById('visualization-container');
                const containerAspectRatio = container.clientWidth / container.clientHeight;
                const imageAspectRatio = this.naturalWidth / this.naturalHeight;

                if (imageAspectRatio > containerAspectRatio) {
                    // Image is wider than the container
                    this.style.width = '100%';
                    this.style.height = 'auto';
                } else {
                    // Image is taller than the container
                    this.style.width = 'auto';
                    this.style.height = '100%';
                }
            };
        }

        function display3DModel(data) {
            // ... [keep the existing display3DModel function] ...
        }

        // ... [keep other existing functions] ...

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
