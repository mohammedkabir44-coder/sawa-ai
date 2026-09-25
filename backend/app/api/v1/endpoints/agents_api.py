import json, hmac, hashlib, base64, time, os
from fastapi.responses import HTMLResponse, Response
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Float, Text, Boolean, Boolean
from app.core.database import get_db, Base
from app.models.product import Product
import uuid
import urllib.request
router = APIRouter(prefix="/dashboard", tags=["Sodangi Agents"])
SECRET = "sodangi-sawa-secret-2026-do-not-share"
SECRET = "sodangi-sawa-secret-2026-do-not-share"
SODANGI_BUSINESS_ID = 3
from fastapi.responses import Response
from datetime import datetime as _dt 
WA_PHONE_ID =os .getenv ("WHATSAPP_PHONE_ID","1332619033263966")
WA_VERIFY_TOKEN =os .getenv ("WA_VERIFY_TOKEN","sodangi_verify_2026")
_BOOT_TIME =__import__ ("time").time ()

@router.get("/ping")
def ping_test():
    return {"status": "QUARANTINE_SUCCESS", "message": "Server is alive! The crash was in the removed code."}

@router.get("/health")
def health_test():
    return {"status": "ok", "database": "skipped for quarantine"}
