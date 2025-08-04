# # app/main.py

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List
import logging
import os
import httpx

from . import models, schemas, database
from .models import SevaEntry
from .database import get_db
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from .database import engine

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ENV Vars
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_API_KEY = os.getenv("SUPABASE_API_KEY")
SUPABASE_TABLE = os.getenv("SUPABASE_TABLE")

HEADERS = {
    "apikey": SUPABASE_API_KEY,
    "Authorization": f"Bearer {SUPABASE_API_KEY}",
    "Content-Type": "application/json"
}

@asynccontextmanager

async def lifespan(app: FastAPI):
    logger.info("🚀 FastAPI application started")
    logger.info(f"🔐 SUPABASE_URL: {SUPABASE_URL}")
    logger.info(f"🔐 POSTGRES_URL: {os.getenv('POSTGRES_URL')}")
    logging.info("🛠️ Creating tables if they don't exist...")
    models.Base.metadata.create_all(bind=engine)
    yield
    logger.info("🛑 FastAPI shutting down")

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/debug/tables")
def list_tables():
    from sqlalchemy import inspect
    inspector = inspect(engine)
    return inspector.get_table_names()


@app.get("/search")
def search_entries(field: str = Query(...), query: str = Query(...), db: Session = Depends(get_db)):
    logger.info(f"🔍 GET /search with field={field} and query={query}")
    allowed_fields = ["paath_name", "person_name", "gotra_name", "start_date"]
    if field not in allowed_fields:
        raise HTTPException(status_code=400, detail="Invalid field")

    search_query = f"%{query.lower()}%"
    column = getattr(models.SevaEntry, field)

    try:
        if field == "start_date":
            results = db.query(models.SevaEntry).filter(column == query).all()
        else:
            results = db.query(models.SevaEntry).filter(column.ilike(search_query)).all()
        logger.info(f"✅ Found {len(results)} entries")
        return results
    except Exception as e:
        logger.error(f"❌ Error in search: {e}")
        raise HTTPException(status_code=500, detail="Search failed")

@app.get("/search-by-date")
def search_by_date(date: str = Query(...), db: Session = Depends(get_db)):
    logger.info(f"📅 GET /search-by-date with date={date}")
    try:
        target_date = datetime.strptime(date, "%Y-%m-%d").date()
        entries = db.query(SevaEntry).filter(
            SevaEntry.start_date <= target_date,
            SevaEntry.end_date >= target_date
        ).all()
        logger.info(f"✅ Found {len(entries)} entries for date {target_date}")
        return entries
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")
    except Exception as e:
        logger.error(f"❌ Error searching by date: {e}")
        raise HTTPException(status_code=500, detail="Failed to search by date")

@app.get("/trash")
async def get_trashed_entries():
    logger.info("🗑️ GET /trash called")
    try:
        url = f"{SUPABASE_URL}/rest/v1/{SUPABASE_TABLE}?check=eq.false&select=*"
        response = httpx.get(url, headers=HEADERS)
        response.raise_for_status()
        logger.info(f"✅ Trash fetch success with {len(response.json())} entries")
        return response.json()
    except Exception as e:
        logger.error(f"❌ Error fetching trash: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch trash entries")

@app.patch("/trash/{entry_id}/restore")
async def restore_entry(entry_id: int, db: Session = Depends(get_db)):
    logger.info(f"♻️ PATCH /trash/{entry_id}/restore called")
    try:
        url = f"{SUPABASE_URL}/rest/v1/{SUPABASE_TABLE}?id=eq.{entry_id}"
        patch_res = httpx.patch(url, headers=HEADERS, json={"check": True})
        patch_res.raise_for_status()

        fetch_res = httpx.get(url, headers=HEADERS)
        fetch_res.raise_for_status()
        data = fetch_res.json()

        if not data:
            raise HTTPException(status_code=404, detail="Entry not found in Supabase")

        entry_data = data[0]
        new_entry = SevaEntry(**entry_data)
        db.merge(new_entry)
        db.commit()
        logger.info("✅ Entry restored and committed to DB")
        return {"detail": "Restored and saved to Postgres"}
    except Exception as e:
        logger.error(f"❌ Error restoring entry: {e}")
        raise HTTPException(status_code=500, detail="Failed to restore entry")

@app.delete("/trash/{entry_id}")
async def delete_entry_permanently(entry_id: int):
    logger.info(f"🚮 DELETE /trash/{entry_id} called")
    try:
        url = f"{SUPABASE_URL}/rest/v1/{SUPABASE_TABLE}?id=eq.{entry_id}"
        response = httpx.delete(url, headers=HEADERS)
        response.raise_for_status()
        logger.info("✅ Entry permanently deleted")
        return {"detail": "Permanently deleted"}
    except Exception as e:
        logger.error(f"❌ Error deleting permanently: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete permanently")

@app.post("/data", response_model=schemas.SevaEntryOut)
async def create_entry(entry: schemas.SevaEntryCreate, db: Session = Depends(get_db)):
    logger.info(f"📝 POST /data with entry: {entry}")
    try:
        new_entry = models.SevaEntry(**entry.model_dump())
        db.add(new_entry)
        db.commit()
        db.refresh(new_entry)

        supabase_payload = {
            "id": new_entry.id,
            "paath_name": new_entry.paath_name,
            "person_name": new_entry.person_name,
            "gotra_name": new_entry.gotra_name,
            "start_date": new_entry.start_date.isoformat(),
            "end_date": new_entry.end_date.isoformat(),
            "check": True
        }

        response = httpx.post(
            f"{SUPABASE_URL}/rest/v1/{SUPABASE_TABLE}",
            json=supabase_payload,
            headers={**HEADERS, "Prefer": "return=minimal"},
            timeout=10.0,
        )

        logger.info(f"📡 Supabase POST status: {response.status_code}")
        logger.info(f"📨 Supabase response: {response.text}")
        response.raise_for_status()
    except Exception as e:
        logger.error(f"❌ Supabase insert failed: {e}")
    return new_entry

@app.get("/data", response_model=List[schemas.SevaEntryOut])
def read_entries(db: Session = Depends(get_db)):
    logger.info("📥 GET /data called")
    try:
        entries = db.query(models.SevaEntry).all()
        logger.info(f"✅ Returning {len(entries)} entries")
        return entries
    except Exception as e:
        logger.error(f"❌ Failed to fetch entries: {e}")
        raise HTTPException(status_code=500, detail="Error fetching data")

@app.delete("/data/{entry_id}")
def delete_entry(entry_id: int, db: Session = Depends(get_db)):
    logger.info(f"🗑️ DELETE /data/{entry_id} called")
    entry = db.query(models.SevaEntry).filter(models.SevaEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    try:
        db.delete(entry)
        db.commit()
        response = httpx.patch(
            f"{SUPABASE_URL}/rest/v1/{SUPABASE_TABLE}?id=eq.{entry_id}",
            json={"check": False},
            headers=HEADERS,
            timeout=10.0,
        )
        logger.info(f"🛠️ Supabase PATCH status: {response.status_code}")
        logger.info(f"🛠️ Supabase PATCH response: {response.text}")
        response.raise_for_status()
    except Exception as e:
        logger.error(f"❌ Supabase update failed: {e}")
    return {"detail": "Deleted successfully"}




















# from fastapi import FastAPI, Depends, HTTPException
# from sqlalchemy.orm import Session
# from fastapi.middleware.cors import CORSMiddleware
# from . import models, schemas, database
# import httpx
# import os
# from datetime import date
# from typing import List
# from fastapi import Query
# from dotenv import load_dotenv
# from .database import get_db
# from .models import SevaEntry
# import logging

# load_dotenv()

# app = FastAPI()

# # Allow all origins (frontend from Vercel)
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Dependency
# get_db = database.get_db

# SUPABASE_URL = os.getenv("SUPABASE_URL")
# SUPABASE_API_KEY = os.getenv("SUPABASE_API_KEY")
# SUPABASE_TABLE = os.getenv("SUPABASE_TABLE")

# HEADERS = {
#     "apikey": SUPABASE_API_KEY,
#     "Authorization": f"Bearer {SUPABASE_API_KEY}",
#     "Content-Type": "application/json"
# }

# @app.get("/search")
# def search_entries(field: str = Query(...), query: str = Query(...), db: Session = Depends(get_db)):
#     allowed_fields = ["paath_name", "person_name", "gotra_name", "start_date"]
#     if field not in allowed_fields:
#         raise HTTPException(status_code=400, detail="Invalid field")

#     search_query = f"%{query.lower()}%"
#     column = getattr(models.SevaEntry, field)

#     if field == "start_date":
#         try:
#             # try direct comparison for exact match
#             results = db.query(models.SevaEntry).filter(column == query).all()
#         except:
#             results = []
#     else:
#         results = db.query(models.SevaEntry).filter(
#             column.ilike(search_query)
#         ).all()

#     return results

# @app.get("/search-by-date")
# def search_by_date(date: str = Query(...), db: Session = Depends(get_db)):
#     from datetime import datetime
#     try:
#         target_date = datetime.strptime(date, "%Y-%m-%d").date()
#     except ValueError:
#         raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

#     entries = db.query(SevaEntry).filter(
#         SevaEntry.start_date <= target_date,
#         SevaEntry.end_date >= target_date
#     ).all()

#     return entries


# # trash functionlity route map
# # fetches
# @app.get("/trash")
# async def get_trashed_entries():
#     try:
#         url = f"{SUPABASE_URL}/rest/v1/{SUPABASE_TABLE}?check=eq.false&select=*"
#         response = httpx.get(url, headers=HEADERS)
#         response.raise_for_status()
#         return response.json()
#     except Exception as e:
#         print("❌ Error fetching trash:", str(e))
#         raise HTTPException(status_code=500, detail="Failed to fetch trash entries")

# # restore
# @app.patch("/trash/{entry_id}/restore")
# async def restore_entry(entry_id: int, db: Session = Depends(get_db)):
#     try:
#         # Step 1: Update check = true
#         url = f"{SUPABASE_URL}/rest/v1/{SUPABASE_TABLE}?id=eq.{entry_id}"
#         update_payload = {"check": True}
#         patch_res = httpx.patch(url, headers=HEADERS, json=update_payload)
#         patch_res.raise_for_status()

#         # Step 2: Get the full row from Supabase
#         fetch_res = httpx.get(url, headers=HEADERS)
#         fetch_res.raise_for_status()
#         data = fetch_res.json()
#         if not data:
#             raise HTTPException(status_code=404, detail="Entry not found in Supabase")

#         entry_data = data[0]

#         # Step 3: Insert into Postgres
#         new_entry = SevaEntry(
#             id=entry_data["id"],
#             paath_name=entry_data["paath_name"],
#             person_name=entry_data["person_name"],
#             gotra_name=entry_data["gotra_name"],
#             start_date=entry_data["start_date"],
#             end_date=entry_data["end_date"],
#         )
#         db.merge(new_entry)  # merge handles upsert by ID
#         db.commit()

#         return {"detail": "Restored and saved to Postgres"}
#     except Exception as e:
#         print("❌ Error restoring entry:", str(e))
#         raise HTTPException(status_code=500, detail="Failed to restore entry")



# # permanent delete
# @app.delete("/trash/{entry_id}")
# async def delete_entry_permanently(entry_id: int):
#     try:
#         url = f"{SUPABASE_URL}/rest/v1/{SUPABASE_TABLE}?id=eq.{entry_id}"
#         response = httpx.delete(url, headers=HEADERS)
#         response.raise_for_status()
#         return {"detail": "Permanently deleted"}
#     except Exception as e:
#         print("❌ Error deleting entry permanently:", str(e))
#         raise HTTPException(status_code=500, detail="Failed to delete permanently")



# # POST /data
# @app.post("/data", response_model=schemas.SevaEntryOut)
# async def create_entry(entry: schemas.SevaEntryCreate, db: Session = Depends(get_db)):
#     # Step 1: Save to PostgreSQL
#     new_entry = models.SevaEntry(**entry.model_dump())
#     db.add(new_entry)
#     db.commit()
#     db.refresh(new_entry)

#     # Step 2: Build payload for Supabase
#     supabase_payload = {
#         "id": new_entry.id,
#         "paath_name": new_entry.paath_name,
#         "person_name": new_entry.person_name,
#         "gotra_name": new_entry.gotra_name,
#         "start_date": new_entry.start_date.isoformat(),
#         "end_date": new_entry.end_date.isoformat(),
#         "check": True
#     }

#     # Step 3: POST to Supabase
#     try:
#         headers = {
#             "apikey": SUPABASE_API_KEY,
#             "Authorization": f"Bearer {SUPABASE_API_KEY}",
#             "Content-Type": "application/json",
#             "Prefer": "return=minimal"
#         }

#         response = httpx.post(
#             f"{SUPABASE_URL}/rest/v1/{SUPABASE_TABLE}",
#             json=supabase_payload,
#             headers=headers,
#             timeout=10.0,
#         )

#         print("📦 Supabase Payload:", supabase_payload)
#         print("📡 Supabase Status:", response.status_code)
#         print("📨 Supabase Text:", response.text)

#         response.raise_for_status()
#     except Exception as e:
#         print("❌ Supabase insert failed:", str(e))

#     return new_entry

# # GET /data
# @app.get("/data", response_model=list[schemas.SevaEntryOut])
# def read_entries(db: Session = Depends(get_db)):
#     entries = db.query(models.SevaEntry).all()
#     print("✅ /data returning:", [e.__dict__ for e in entries])
#     return entries


# # DELETE /data/{entry_id}
# @app.delete("/data/{entry_id}")
# def delete_entry(entry_id: int, db: Session = Depends(get_db)):
#     entry = db.query(models.SevaEntry).filter(models.SevaEntry.id == entry_id).first()
#     if not entry:
#         raise HTTPException(status_code=404, detail="Entry not found")

#     # Step 1: Delete from PostgreSQL
#     db.delete(entry)
#     db.commit()

#     # Step 2: Update Supabase row with check = False
#     try:
#         headers = {
#             "apikey": SUPABASE_API_KEY,
#             "Authorization": f"Bearer {SUPABASE_API_KEY}",
#             "Content-Type": "application/json"
#         }

#         response = httpx.patch(
#             f"{SUPABASE_URL}/rest/v1/{SUPABASE_TABLE}?id=eq.{entry_id}",
#             json={"check": False},
#             headers=headers,
#             timeout=10.0,
#         )

#         print("🛠️ Supabase PATCH status:", response.status_code)
#         print("🛠️ Supabase PATCH text:", response.text)

#         response.raise_for_status()
#     except Exception as e:
#         print("❌ Supabase update failed:", str(e))

#     return {"detail": "Deleted successfully"}
