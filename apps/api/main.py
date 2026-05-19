from __future__ import annotations

import os
from dataclasses import asdict

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from packages.research_engine.models import ResearchBrief
from packages.research_engine.providers import ModelProviderError, get_model_provider
from packages.research_engine.workflow import build_research_plan, generate_personas, run_research


APP_DISPLAY_NAME = os.getenv("APP_DISPLAY_NAME", "App-Q")
APP_MODEL_PROVIDER = os.getenv("APP_MODEL_PROVIDER", "mock")

app = FastAPI(title=APP_DISPLAY_NAME)


class BriefPayload(BaseModel):
    title: str = Field(..., min_length=3)
    market: str = "Türkiye"
    category: str = ""
    idea: str = Field(..., min_length=10)
    target_users: list[str] = Field(default_factory=list)
    questions: list[str] = Field(default_factory=list)
    competitors: list[str] = Field(default_factory=list)
    expected_price: str | None = None
    sales_channel: str | None = None
    success_metric: str | None = None

    def to_brief(self) -> ResearchBrief:
        return ResearchBrief(
            title=self.title,
            market=self.market,
            category=self.category,
            idea=self.idea,
            target_users=self.target_users,
            questions=self.questions,
            competitors=self.competitors,
            expected_price=self.expected_price,
            sales_channel=self.sales_channel,
            success_metric=self.success_metric,
        )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "app": APP_DISPLAY_NAME, "provider": APP_MODEL_PROVIDER}


@app.post("/brief/questions")
def brief_questions(payload: BriefPayload) -> dict[str, list[dict]]:
    plan = build_research_plan(payload.to_brief())
    return {"questions": [asdict(question) for question in plan.clarifying_questions]}


@app.post("/research/plan")
def research_plan(payload: BriefPayload) -> dict:
    return asdict(build_research_plan(payload.to_brief()))


@app.post("/personas/generate")
def personas_generate(payload: BriefPayload) -> dict[str, list[dict]]:
    return {"personas": [asdict(persona) for persona in generate_personas(payload.to_brief())]}


@app.post("/research/run")
def research_run(payload: BriefPayload) -> dict:
    model = get_model_provider(APP_MODEL_PROVIDER)
    try:
        report = run_research(payload.to_brief(), model)
    except ModelProviderError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return asdict(report)
