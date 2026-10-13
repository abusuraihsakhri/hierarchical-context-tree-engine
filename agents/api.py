"""
FastAPI REST API Server for Hierarchical Context Tree Engine.
"""
import hmac
import os
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from .base import AuditLogger, PHIGuard, SecurityException
from .models import SystemTaskPayload, ConsensusDossier
from .supervisor import SystemSupervisor

supervisor = SystemSupervisor(model_provider="mock")

app = FastAPI(
    title="Hierarchical Context Tree Engine API",
    description="Enterprise Distributed Component Platform (Long-Horizon Agent Context & State Architecture)",
    version="3.0.0-ENTERPRISE",
)


class ChatRequest(BaseModel):
    query: str


@app.get("/health")
def health():
    return {"status": "HEALTHY", "service": "hierarchical-context-tree-engine", "domain": "Long-Horizon Agent Context & State Architecture", "standard": "Autonomous Agent State Machine & Token Economy RFC", "version": "3.0.0-ENTERPRISE"}


@app.get("/metrics")
def metrics():
    return {
        "dossiers_processed_total": len(supervisor.dossier_registry),
        "audit_blocks_total": len(AuditLogger.get_trail()),
        "system_status": "NOMINAL_OPTIMAL"
    }


@app.post("/api/audit")
def api_audit(payload: SystemTaskPayload):
    try:
        dossier = supervisor.process_task(payload)
    except SecurityException:
        raise HTTPException(status_code=422, detail="Sensitive identifiers are not accepted")
    return dossier.to_dict()


@app.post("/api/chat")
def api_chat(req: ChatRequest):
    try:
        ans = supervisor.query_supervisory_chat(req.query)
        return {"response": ans}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/audit/logs")
def api_audit_logs(x_audit_read_key: Optional[str] = Header(default=None)):
    """Audit metadata is restricted; identifier-bearing logs are not public."""
    expected = os.getenv("AUDIT_LOG_READ_KEY")
    if not expected or not x_audit_read_key or not hmac.compare_digest(
        x_audit_read_key, expected
    ):
        raise HTTPException(status_code=403, detail="Audit access denied")
    return {"audit_trail": AuditLogger.get_trail(), "verified": AuditLogger.verify_integrity()}
