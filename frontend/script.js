document.addEventListener('DOMContentLoaded', () => {
    const API_URL = 'YOUR_BACKEND_URL'; // Replace with your deployed backend URL
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
    }

    function handleError(error) {
        hideLoading();
        alert(`Ein Fehler ist aufgetreten: ${error.message}`);
    }

    codeForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const code = document.getElementById('code-input').value;
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
