"""NovaScript AI engineering assistant surface."""

from afritech.novascript.schemas import (
    NovaScriptArchitectureRequest,
    NovaScriptDebugRequest,
    NovaScriptDocsRequest,
    NovaScriptGenerateRequest,
    NovaScriptExplainRequest,
    NovaScriptTestRequest,
)
from afritech.novascript.service import NovaScriptService, get_novascript_service

__all__ = [
    "NovaScriptArchitectureRequest",
    "NovaScriptDebugRequest",
    "NovaScriptDocsRequest",
    "NovaScriptGenerateRequest",
    "NovaScriptExplainRequest",
    "NovaScriptService",
    "NovaScriptTestRequest",
    "get_novascript_service",
]
