"""
FastAPI REST API Server for Who Icd11 Multilingual Auto Coder.
"""
from fastapi import FastAPI, HTTPException, Header, Depends
from pydantic import Field
from typing import Optional
import os
from .base import SecurityException
from pydantic import BaseModel
from .base import AuditLogger
from .models import SystemTaskPayload, ConsensusDossier
from .supervisor import SystemSupervisor

supervisor = SystemSupervisor(model_provider="mock")


def require_api_key(x_api_key: Optional[str] = Header(default=None)):
    configured = os.getenv("AUDIT_API_KEY")
    if configured:
        import hmac
        if not x_api_key or not hmac.compare_digest(x_api_key, configured):
            raise HTTPException(status_code=401, detail="Unauthorized")


app = FastAPI(
    title="Who Icd11 Multilingual Auto Coder API",
    description="Enterprise Distributed Component Platform (Clinical & Biomedical AI)",
    version="3.0.0-ENTERPRISE",
)


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)


@app.get("/health")
def health():
    return {"status": "HEALTHY", "service": "who-icd11-multilingual-auto-coder", "domain": "Clinical & Biomedical AI", "standard": "CAP / CLSI / ISO Standards", "version": "3.0.0-ENTERPRISE"}


@app.get("/metrics")
def metrics():
    return {
        "dossiers_processed_total": len(supervisor.dossier_registry),
        "audit_blocks_total": len(AuditLogger.get_trail()),
        "system_status": "NOMINAL_OPTIMAL"
    }


@app.post("/api/audit", dependencies=[Depends(require_api_key)])
def api_audit(payload: SystemTaskPayload):
    try:
        dossier = supervisor.process_task(payload)
    except SecurityException:
        raise HTTPException(status_code=422, detail="Potential personal identifier in submitted data") from None
    return dossier.to_dict()


@app.post("/api/chat", dependencies=[Depends(require_api_key)])
def api_chat(req: ChatRequest):
    try:
        ans = supervisor.query_supervisory_chat(req.query)
    except SecurityException:
        raise HTTPException(status_code=422, detail="Potential personal identifier in submitted data") from None
    return {"response": ans}


@app.get("/api/audit/logs", dependencies=[Depends(require_api_key)])
def api_audit_logs():
    return {"audit_trail": AuditLogger.get_trail(), "verified": AuditLogger.verify_integrity()}
