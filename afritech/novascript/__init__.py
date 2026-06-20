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
from afritech.novascript.v2 import NovaScriptV2Engine, get_novascript_v2_engine

__all__ = [
    "NovaScriptArchitectureRequest",
    "NovaScriptDebugRequest",
    "NovaScriptDocsRequest",
    "NovaScriptGenerateRequest",
    "NovaScriptExplainRequest",
    "NovaScriptService",
    "NovaScriptV2Engine",
    "NovaScriptTestRequest",
    "get_novascript_service",
    "get_novascript_v2_engine",
]
