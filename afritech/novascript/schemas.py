from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class NovaScriptGenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=3)
    project_id: str = Field(default="project-employee-rbac")
    language: str = Field(default="python", min_length=1)
    mode: str = Field(default="code", min_length=1)


class NovaScriptExplainRequest(BaseModel):
    code: str = Field(..., min_length=1)
    context: str = ""


class NovaScriptDebugRequest(BaseModel):
    code: str = Field(default="", min_length=0)
    error: str = Field(default="", min_length=0)
    context: str = ""


class NovaScriptArchitectureRequest(BaseModel):
    description: str = Field(..., min_length=3)
    stack: str = Field(default="FastAPI + PostgreSQL", min_length=1)


class NovaScriptTestRequest(BaseModel):
    target: str = Field(..., min_length=1)
    framework: str = Field(default="pytest", min_length=1)


class NovaScriptDocsRequest(BaseModel):
    topic: str = Field(..., min_length=1)
    audience: str = Field(default="developer", min_length=1)
    format: str = Field(default="README", min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
