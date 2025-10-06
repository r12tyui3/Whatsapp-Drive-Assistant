from fastapi import FastAPI, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import os, uuid, base64, asyncio
from scrapers.hc_services import HCServicesScraper
from scrapers.district_services import DistrictServicesScraper
from db.database import init_db, get_session
from db.models import QueryLog, RawResponse, CaseDetail, OrderDocument
from sqlalchemy.orm import Session
from datetime import datetime
import json
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # run startup
    await init_db()
    try:
        yield
    finally:
        # run shutdown: ensure any live scraper browser/context is torn down
        # iterate over a list copy because teardown may modify the dict
        for sid, scraper in list(SEARCH_SESSIONS.items()):
            try:
                # scraper.teardown() is async; await it if present
                teardown = getattr(scraper, 'teardown', None)
                if teardown:
                    await teardown()
            except Exception:
                # swallow exceptions on shutdown to avoid noisy failures
                pass
        SEARCH_SESSIONS.clear()

# In-memory session store for Playwright pages (TTL per session)
SEARCH_SESSIONS = {}

# create app with lifespan handler
app = FastAPI(title="Court Data Fetcher", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

class StartSearchPayload(BaseModel):
    portal: str  # "HIGH_COURT" or "DISTRICT_COURT"
    high_court: str | None = None
    state: str | None = None
    district: str | None = None
    establishment: str | None = None
    case_type: str
    case_number: str
    case_year: str

@app.post("/start-search", response_class=JSONResponse)
async def start_search(payload: StartSearchPayload):
    session_id = str(uuid.uuid4())
    try:
        if payload.portal == "HIGH_COURT":
            scraper = HCServicesScraper()
        elif payload.portal == "DISTRICT_COURT":
            scraper = DistrictServicesScraper()
        else:
            raise HTTPException(400, "Invalid portal")

        # use Pydantic v2 API to get a dict representation
        captcha_png_b64 = await scraper.prepare_search(payload.model_dump())
        SEARCH_SESSIONS[session_id] = scraper
        return {"sessionId": session_id, "captchaImageBase64": captcha_png_b64}
    except Exception as e:
        return JSONResponse({"error": f"Failed to initialize search: {e}"}, status_code=500)

@app.post("/solve-captcha", response_class=JSONResponse)
async def solve_captcha(sessionId: str = Form(...), captchaText: str = Form(...), db: Session = Depends(get_session)):
    scraper = SEARCH_SESSIONS.get(sessionId)
    if not scraper:
        raise HTTPException(410, "Session expired. Please start again.")
    try:
        result = await scraper.submit_and_fetch(captchaText)
        # Persist query and raw response
        # `court` can be a dict for district scraper; serialize to JSON for DB storage
        court_val = result.get("court")
        if isinstance(court_val, (dict, list)):
            court_val = json.dumps(court_val)

        q = QueryLog(
            id=str(uuid.uuid4()),
            portal=result["portal"],
            court=court_val,
            case_type=result["input"]["case_type"],
            case_number=result["input"]["case_number"],
            case_year=result["input"]["case_year"],
            created_at=datetime.utcnow(),
            status=result.get("status", "OK")
        )
        db.add(q)
        db.flush()
        # Raw HTML
        raw = RawResponse(id=str(uuid.uuid4()), query_id=q.id, html=result["raw_html"])
        db.add(raw)
        # Case detail
        cd = CaseDetail(
            id=str(uuid.uuid4()),
            query_id=q.id,
            parties=result["parsed"].get("parties"),
            filing_date=result["parsed"].get("filing_date"),
            next_hearing_date=result["parsed"].get("next_hearing_date"),
            case_status=result["parsed"].get("case_status")
        )
        db.add(cd)
        # Orders
        for od in result["orders"]:
            doc = OrderDocument(
                id=od["id"],
                query_id=q.id,
                title=od["title"],
                order_date=od.get("date"),
                file_path=od.get("file_path"),
                source_url=od.get("source_url")
            )
            db.add(doc)
        db.commit()
        # Free browser resources
        await scraper.teardown()
        SEARCH_SESSIONS.pop(sessionId, None)
        # Return data for UI
        return {"queryId": q.id, "parsed": result["parsed"], "orders": [
            {"id": o["id"], "title": o["title"], "date": o.get("date"), "downloadUrl": f"/download/{o['id']}"} for o in result["orders"]
        ]}
    except (HCServicesScraper.InvalidCaptcha, DistrictServicesScraper.InvalidCaptcha) as ic:
        # Both scrapers raise their own InvalidCaptcha; handle both and return a fresh captcha
        return JSONResponse({"captchaError": True, "message": "Invalid CAPTCHA. Please try again.", "captchaImageBase64": getattr(ic, 'new_captcha_b64', None)}, status_code=400)
    except Exception as e:
        await scraper.teardown()
        SEARCH_SESSIONS.pop(sessionId, None)
        return JSONResponse({"error": f"Search failed: {e}"}, status_code=500)

@app.get("/download/{doc_id}", response_class=FileResponse)
def download_order(doc_id: str, db: Session = Depends(get_session)):
    doc = db.query(OrderDocument).filter(OrderDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(404, "Document not found")
    if not doc.file_path or not os.path.exists(doc.file_path):
        raise HTTPException(404, "File not available")
    filename = os.path.basename(doc.file_path)
    return FileResponse(doc.file_path, media_type="application/pdf", filename=filename)

@app.get("/cause-list", response_class=HTMLResponse)
async def cause_list(request: Request, portal: str = "HIGH_COURT", court: str | None = None, state: str | None = None, district: str | None = None, date: str | None = None):
    try:
        if portal == "HIGH_COURT":
            scraper = HCServicesScraper()
            items = await scraper.fetch_cause_list(court=court, date=date)
        else:
            scraper = DistrictServicesScraper()
            items = await scraper.fetch_cause_list(state=state, district=district, date=date)
        await scraper.teardown()
        return templates.TemplateResponse("cause_list.html", {"request": request, "portal": portal, "items": items, "court": court, "state": state, "district": district, "date": date})
    except Exception as e:
        return templates.TemplateResponse("cause_list.html", {"request": request, "portal": portal, "items": [], "error": str(e)})


@app.get('/health', response_class=JSONResponse)
async def health():
    """Lightweight health check for liveness/readiness."""
    return JSONResponse({"status": "ok"})
