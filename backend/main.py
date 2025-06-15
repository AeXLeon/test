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
        # Open image
        image = Image.open(io.BytesIO(image_bytes))
        
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Resize image if too small
        if image.size[0] < 1000:
            ratio = 1000.0 / image.size[0]
            new_size = (1000, int(image.size[1] * ratio))
            image = image.resize(new_size, Image.Resampling.LANCZOS)
        
        # Enhance image for better OCR
        from PIL import ImageEnhance
        
        # Erhöhe Kontrast
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)
        
        # Erhöhe Schärfe
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(2.0)
        
        # OCR mit spezifischen Einstellungen für Codes
        custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        code = pytesseract.image_to_string(image, config=custom_config).strip()
        
        # Bereinige den erkannten Code
        code = ''.join(c for c in code if c.isalnum())
        
        if not code:
            raise ValueError("Kein Code im Bild gefunden")
            
        return code
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process image: {str(e)}")

async def fill_survey(code: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
        )
        page = await context.new_page()
        
        try:
            # Navigate to survey page
            await page.goto('https://mcdonalds.fast-insight.com/voc/de/de')
            await page.wait_for_load_state('networkidle')
            
            # Fill in the code
            code_input = await page.wait_for_selector('input[id="receiptCode"]')
            await code_input.fill(code)
            
            # Handle reCAPTCHA
            site_key = await page.evaluate('document.querySelector("[data-sitekey]").getAttribute("data-sitekey")')
            recaptcha_response = await solve_recaptcha(site_key, page.url)
            
            # Insert reCAPTCHA response and trigger verification
            await page.evaluate(f'''
                document.getElementById("g-recaptcha-response").innerHTML = "{recaptcha_response}";
                ___grecaptcha_cfg.clients[0].K.K.callback("{recaptcha_response}");
            ''')
            
            # Wait for reCAPTCHA verification and submit form
            await page.wait_for_timeout(2000)  # Wait for reCAPTCHA verification
            submit_button = await page.wait_for_selector('button[type="submit"]')
            await submit_button.click()
            
            # Wait for navigation and fill survey
            await page.wait_for_load_state('networkidle')
            
            # Automatisch alle Radio-Buttons mit der höchsten Bewertung auswählen
            radio_selectors = [
                'input[type="radio"][value="7"]',  # Sehr zufrieden
                'input[type="radio"][value="5"]',  # Sehr wahrscheinlich
                'input[type="radio"][value="1"]'   # Ja
            ]
            
            for selector in radio_selectors:
                elements = await page.query_selector_all(selector)
                for element in elements:
                    await element.evaluate('el => el.click()')
                await page.wait_for_timeout(500)
            
            # Weiter-Button klicken, wenn vorhanden
            next_buttons = ['button:has-text("Weiter")', 'button:has-text("Absenden")']
            for button in next_buttons:
                try:
                    await page.click(button)
                    await page.wait_for_load_state('networkidle')
                    await page.wait_for_timeout(1000)
                except:
                    continue
            
            # Warte auf die Bestätigungsseite
            await page.wait_for_selector('div:has-text("Vielen Dank")', timeout=10000)
            
            # Take screenshot of the confirmation page
            screenshot = await page.screenshot(full_page=True)
            
            await browser.close()
            return base64.b64encode(screenshot).decode()
            
        except Exception as e:
            await browser.close()
            raise HTTPException(status_code=500, detail=f"Survey automation failed: {str(e)}")

@app.post("/process-code")
async def process_code(code: str = Form(...)):
    try:
        # Validate code format
        code = code.strip().upper()
        if not code.isalnum() or len(code) < 8:
            raise HTTPException(status_code=400, detail="Ungültiges Code-Format. Der Code sollte mindestens 8 alphanumerische Zeichen enthalten.")
        
        screenshot = await fill_survey(code)
        return JSONResponse(content={
            "success": True,
            "screenshot": screenshot,
            "message": "Umfrage erfolgreich ausgefüllt!"
        })
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Fehler beim Ausfüllen der Umfrage: {str(e)}"
        )

@app.post("/process-image")
async def process_image_upload(file: UploadFile = File(...)):
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400,
                detail="Ungültiges Dateiformat. Bitte laden Sie ein Bild hoch (JPG, PNG, etc.)."
            )
        
        contents = await file.read()
        if len(contents) > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(
                status_code=400,
                detail="Bild ist zu groß. Maximale Größe ist 10MB."
            )
        
        code = await process_image(contents)
        screenshot = await fill_survey(code)
        return JSONResponse(content={
            "success": True,
            "screenshot": screenshot,
            "message": f"Code '{code}' wurde erkannt und die Umfrage wurde erfolgreich ausgefüllt!"
        })
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Fehler bei der Verarbeitung: {str(e)}"
        )
