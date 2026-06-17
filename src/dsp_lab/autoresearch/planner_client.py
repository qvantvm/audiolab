"""Planner client factory and OpenAI-compatible HTTP client."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any, Protocol

from dsp_lab.autoresearch.mock_planner import MockPlanner
from dsp_lab.autoresearch.planner_config import PlannerPolicy
from dsp_lab.autoresearch.proposal_schema import extract_json_from_text
from dsp_lab.autoresearch.template_planner import propose_from_template


class PlannerClient(Protocol):
    def propose(self, context: dict[str, Any], prompt: str) -> dict[str, Any]: ...


class TemplatePlanner:
    def __init__(self, policy: PlannerPolicy):
        self.policy = policy

    def propose(self, context: dict[str, Any], prompt: str) -> dict[str, Any]:
        return propose_from_template(context, max_proposals=self.policy.max_proposals)


class OpenAICompatiblePlanner:
    def __init__(self, policy: PlannerPolicy):
        self.policy = policy
        self.base_url = policy.resolved_base_url().rstrip("/")
        self.model = policy.resolved_model()
        self.api_key = os.environ.get("AURALIS_LLM_API_KEY", "")

    def propose(self, context: dict[str, Any], prompt: str) -> dict[str, Any]:
        if not self.base_url or not self.model:
            raise RuntimeError(
                "openai_compatible planner requires AURALIS_LLM_BASE_URL and AURALIS_LLM_MODEL "
                "(or config base_url/model). Use template or mock mode instead."
            )

        url = f"{self.base_url}/chat/completions"
        body = {
            "model": self.model,
            "temperature": self.policy.temperature,
            "messages": [
                {"role": "system", "content": "Return JSON only. No markdown."},
                {"role": "user", "content": prompt},
            ],
        }
        data = json.dumps(body).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise RuntimeError(f"LLM request failed: {exc}") from exc

        content = ""
        choices = payload.get("choices", [])
        if choices:
            content = str(choices[0].get("message", {}).get("content", ""))
        if not content:
            raise RuntimeError("Empty LLM response")

        parsed = extract_json_from_text(content)
        parsed["_meta"] = {
            "model": self.model,
            "base_url": self.base_url,
            "temperature": self.policy.temperature,
            "request_id": payload.get("id"),
        }
        return parsed


def make_planner(policy: PlannerPolicy) -> PlannerClient:
    mode = policy.mode.lower()
    if mode == "mock":
        fixture = policy.mock_fixture_path or None
        return MockPlanner(fixture_path=fixture)
    if mode == "openai_compatible":
        return OpenAICompatiblePlanner(policy)
    return TemplatePlanner(policy)
