import os
import base64
from fastapi import FastAPI, File, UploadFile, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from backend import ExpenseAgent
from sheets import GoogleSheetsClient

app = FastAPI()
agent = ExpenseAgent()
sheets = GoogleSheetsClient()

ALLOWED_TYPES = ["image/jpeg", "image/png", "image/webp"]
MAX_SIZE = 10 * 1024 * 1024  # 10 MB

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def index():
    with open(os.path.join(os.path.dirname(__file__), "static/index.html")) as f:
        return f.read()


@app.post("/api/analyze", response_class=HTMLResponse)
async def analyze(file: UploadFile = File(...)):
    # Validation type MIME
    if file.content_type not in ALLOWED_TYPES:
        return HTMLResponse(content=_error("Type de fichier non supporté. Utilisez JPEG, PNG ou WEBP."), status_code=400)

    image_bytes = await file.read()

    # Validation taille
    if len(image_bytes) > MAX_SIZE:
        return HTMLResponse(content=_error("Image trop lourde (max 10 MB)."), status_code=400)

    data = agent.extract_from_bytes(image_bytes, file.content_type)
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")
    image_data = f"data:{file.content_type};base64,{image_b64}"

    return HTMLResponse(content=_form(data, image_data))


@app.post("/api/submit", response_class=HTMLResponse)
async def submit(
    Horodatage: str = Form(None),
    Type: str = Form(None),
    Fournisseur: str = Form(None),
    Date: str = Form(None),
    montant_ttc: str = Form(None),
    tva: str = Form(None),
    Devise: str = Form(None),
    Description: str = Form(None),
    Confiance: str = Form(None),
    image_data: str = Form(None)
):
    data = {
        "Horodatage": Horodatage,
        "Type": Type,
        "Fournisseur": Fournisseur,
        "Date": Date,
        "Montant TTC ($)": montant_ttc,
        "TVA ($)": tva,
        "Devise": Devise,
        "Description": Description,
        "Confiance": Confiance,
    }

    image_url = None
    if image_data:
        # Décoder le base64
        header, encoded = image_data.split(",", 1)
        media_type = header.split(":")[1].split(";")[0]
        image_bytes = base64.b64decode(encoded)
        filename = f"receipt_{Horodatage or 'unknown'}.jpg"
        image_url = sheets.upload_image(image_bytes, filename, media_type)

    sheets.append_expense(data, image_url=image_url)

    return HTMLResponse(content=_success(data, image_url))


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return HTMLResponse(content=_error(str(exc)), status_code=500)


def _error(message: str) -> str:
    return f"""
    <div class="error">
        <p>❌ {message}</p>
    </div>
    """

def _success(data: dict, image_url: str) -> str:
    return f"""
    <div class="success">
        <p>Note de frais enregistré my lord</p>
        <p><strong>{data.get('Fournisseur')}</strong> — {data.get('Montant TTC ($)')} {data.get('Devise')}</p>
        {f'<img src="{image_url}" width="200"/>' if image_url else ''}
    </div>
    """

def _form(data: dict, image_data: str) -> str:
    return f"""
    <form hx-post="/api/submit" hx-target="#result" hx-encoding="multipart/form-data">
        <input type="hidden" name="image_data" value="{image_data}"/>

        <label>Horodatage</label>
        <input type="text" name="Horodatage" value="{data.get('Horodatage') or ''}"/>

        <label>Type</label>
        <select name="Type">
            {''.join(f'<option value="{t}" {"selected" if data.get("Type") == t else ""}>{t}</option>' for t in ["restaurant", "transport", "hôtel", "autre"])}
        </select>

        <label>Fournisseur</label>
        <input type="text" name="Fournisseur" value="{data.get('Fournisseur') or ''}"/>

        <label>Date</label>
        <input type="text" name="Date" value="{data.get('Date') or ''}"/>

        <label>Montant TTC ($)</label>
        <input type="number" step="0.01" name="montant_ttc" value="{data.get('Montant TTC ($)') or ''}"/>

        <label>TVA ($)</label>
        <input type="number" step="0.01" name="tva" value="{data.get('TVA ($)') or ''}"/>

        <label>Devise</label>
        <input type="text" name="Devise" value="{data.get('Devise') or 'USD'}"/>

        <label>Description</label>
        <input type="text" name="Description" value="{data.get('Description') or ''}"/>

        <label>Confiance</label>
        <select name="Confiance">
            {''.join(f'<option value="{c}" {"selected" if data.get("Confiance") == c else ""}>{c}</option>' for c in ["haute", "moyen", "basse"])}
        </select>

        <button type="submit">Enregistrer</button>
    </form>
    """