# McDonald's Survey Automation

This project provides a web-based automation tool for completing McDonald's customer surveys. It includes both a frontend interface for users to submit survey codes and a backend service to process the automation.

## Legal Notice

**Important**: This tool should only be used with explicit written permission from McDonald's. Automated survey submissions without authorization may violate terms of service.

## Project Structure

```
McDonaldsAutoFill/
├── frontend/             # Static files for GitHub Pages
│   ├── index.html
│   ├── styles.css
│   └── script.js
└── backend/             # Python FastAPI backend
    ├── main.py
    └── requirements.txt
```

## Setup Instructions

### Backend Setup

1. Install Python dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. Install Playwright browsers:
   ```bash
   playwright install chromium
   ```

3. Install Tesseract OCR:
   - Windows: Download and install from https://github.com/UB-Mannheim/tesseract/wiki
   - Linux: `sudo apt-get install tesseract-ocr`
   - macOS: `brew install tesseract`

4. Create a `.env` file in the backend directory:
   ```
   CAPTCHA_API_KEY=your_2captcha_api_key
   ```

5. Start the backend server:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

### Frontend Setup

1. Update the `API_URL` in `frontend/script.js` to point to your deployed backend server.

2. Deploy to GitHub Pages:
   - Create a new repository on GitHub
   - Push the contents of the `frontend` directory to the `gh-pages` branch
   - Enable GitHub Pages in the repository settings

## Features

- Code input support
- Image upload with OCR
- reCAPTCHA solving
- Survey automation
- Result screenshot generation

## Security Measures

- Rate limiting implemented
- API key protection
- CORS configuration
- Error logging

## Contributing

Please read CONTRIBUTING.md for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the LICENSE.md file for details.

## Disclaimer

This tool is for educational purposes only. Use responsibly and in accordance with all applicable terms of service and laws.
