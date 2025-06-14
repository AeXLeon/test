import os
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pytesseract
from PIL import Image
import io
from playwright.async_api import async_playwright
from python2captcha import Client
import aiofiles
from dotenv import load_dotenv
import base64

load_dotenv()

app = FastAPI()

# Configure CORS for GitHub Pages frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://<your-github-username>.github.io"],  # Update this with your GitHub Pages domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

reCaptcha_solver = Client(os.getenv('CAPTCHA_API_KEY'))

async def solve_recaptcha(site_key: str, page_url: str):
    try:
        result = await reCaptcha_solver.solve_recaptcha(
            site_key=site_key,
            page_url=page_url
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to solve reCAPTCHA: {str(e)}")

async def process_image(image_bytes: bytes) -> str:
    try:
        image = Image.open(io.BytesIO(image_bytes))
        code = pytesseract.image_to_string(image).strip()
        return code
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process image: {str(e)}")

async def fill_survey(code: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        try:
            # Navigate to survey page
            await page.goto('https://mcdonalds.fast-insight.com/voc/de/de')
            
            # Fill in the code
            await page.fill('input[name="receiptCode"]', code)
            
            # Handle reCAPTCHA
            site_key = await page.evaluate('document.querySelector("[data-sitekey]").getAttribute("data-sitekey")')
            recaptcha_response = await solve_recaptcha(site_key, page.url)
            
            # Submit the form
            await page.evaluate(f'document.getElementById("g-recaptcha-response").innerHTML = "{recaptcha_response}";')
            await page.click('button[type="submit"]')
            
            # Take screenshot
            screenshot = await page.screenshot()
            
            await browser.close()
            return base64.b64encode(screenshot).decode()
            
        except Exception as e:
            await browser.close()
            raise HTTPException(status_code=500, detail=f"Survey automation failed: {str(e)}")

@app.post("/process-code")
async def process_code(code: str = Form(...)):
    try:
        screenshot = await fill_survey(code)
        return JSONResponse(content={"screenshot": screenshot})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process-image")
async def process_image_upload(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        code = await process_image(contents)
        screenshot = await fill_survey(code)
        return JSONResponse(content={"screenshot": screenshot})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
