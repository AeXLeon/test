document.addEventListener('DOMContentLoaded', () => {
    const API_URL = window.location.hostname === 'localhost'
        ? 'http://localhost:8000'
        : 'https://your-backend-url.com'; // Replace with your deployed backend URL
    const codeForm = document.getElementById('code-form');
    const imageForm = document.getElementById('image-form');
    const loading = document.getElementById('loading');
    const result = document.getElementById('result');
    const resultImage = document.getElementById('result-image');
    const downloadBtn = document.getElementById('download-btn');

    function showLoading() {
        loading.classList.remove('hidden');
        result.classList.add('hidden');
    }

    function hideLoading() {
        loading.classList.add('hidden');
    }

    function showResult(imageData) {
        resultImage.src = `data:image/png;base64,${imageData}`;
        result.classList.remove('hidden');
    }    function showMessage(message, isError = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isError ? 'error' : 'success'}`;
        messageDiv.textContent = message;
        document.querySelector('.container').insertBefore(messageDiv, result);
        
        // Remove message after 5 seconds
        setTimeout(() => messageDiv.remove(), 5000);
    }

    function handleError(error) {
        hideLoading();
        showMessage(error.message, true);
    }

    codeForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const code = document.getElementById('code-input').value.trim();
        
        if (!code) {
            showMessage('Bitte geben Sie einen Code ein.', true);
            return;
        }
        
        showLoading();

        try {
            const formData = new FormData();
            formData.append('code', code);

            const response = await fetch(`${API_URL}/process-code`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            hideLoading();
            showResult(data.screenshot);
        } catch (error) {
            handleError(error);
        }
    });

    imageForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const file = document.getElementById('image-input').files[0];
        if (!file) {
            alert('Bitte wählen Sie ein Bild aus.');
            return;
        }

        showLoading();

        try {
            const formData = new FormData();
            formData.append('file', file);

            const response = await fetch(`${API_URL}/process-image`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            hideLoading();
            showResult(data.screenshot);
        } catch (error) {
            handleError(error);
        }
    });

    downloadBtn.addEventListener('click', () => {
        const link = document.createElement('a');
        link.download = 'survey-result.png';
        link.href = resultImage.src;
        link.click();
    });
});
