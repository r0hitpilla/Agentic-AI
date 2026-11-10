"""Reference classifier for the agent inventory.

Deterministic implementation of knowledge/classification-rules.yaml and
knowledge/risk-model.yaml. Every decision returns the rule ID that fired, so
results are explainable to stewards and auditors. No LLM is involved
(docs/21, threat T2).

Evidence is a plain dict of facts gathered by the reconciliation engine.
Missing keys take the defaults in DEFAULTS. See docs/25-engine-contracts.md.
"""
from __future__ import annotations

import pathlib
from dataclasses import dataclass
from typing import Any, Optional

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent

DEFAULTS: dict[str, Any] = {
    "operator": "bank",
    "personal_consumer_ai_usage": False,
    "acts_on_bank_systems": False,
    "runs_on_user_device": False,
    "model_selects_tools": False,
    "writes_without_human_review": False,
    "kind": "agent_app",
    "calls_llm": False,
    "retired_confirmed": False,
    "standby": False,
    "collector_health_ok": True,
    "platform_api_found": False,
    "registered": False,
    "approved": False,
    "active_owner": False,
    "code_found": False,
    "days_since_runtime": None,      # None = never seen at runtime
    "schedule_period_days": None,
    "credentials_live": False,
    "runtime_identity_matches": False,
    "via_gateway": False,
    "minimum_profile_complete": False,
    "previous_status": None,
}

TIER_ORDER = ["low", "medium", "high", "critical"]
EXTERNAL_OPERATORS = {"customer", "partner", "merchant", "network"}
INFRA_KINDS = {"model_server", "mcp_server", "gateway"}


@dataclass(frozen=True)
class Decision:
    value: Any
    rule: str
    subtype: Optional[str] = None


def load_knowledge(root: pathlib.Path = ROOT) -> dict:
    k = root / "knowledge"
    return {
        "rules": yaml.safe_load((k / "classification-rules.yaml").read_text()),
        "risk": yaml.safe_load((k / "risk-model.yaml").read_text()),
    }


class Classifier:
    def __init__(self, knowledge: Optional[dict] = None):
        self.k = knowledge or load_knowledge()
        params = self.k["rules"]["parameters"]
        self.dormancy_days = params["dormancy_days"]
        self.grace_days = params["schedule_grace_days"]
        self.weights = self.k["rules"]["evidence_weights"]
        self.source_of_truth_map = self.k["rules"]["source_of_truth"]
        self.risk = self.k["risk"]

    # ------------------------------------------------------------------ helpers
    @staticmethod
    def _ev(evidence: dict) -> dict:
        ev = dict(DEFAULTS)
        ev.update(evidence or {})
        return ev

    def dormancy_threshold(self, ev: dict) -> int:
        period = ev.get("schedule_period_days")
        if period:
            return max(self.dormancy_days, period + self.grace_days)
        return self.dormancy_days

    def runtime_recent(self, ev: dict) -> bool:
        days = ev.get("days_since_runtime")
        return days is not None and days <= self.dormancy_threshold(ev)

    # ------------------------------------------------------------- record type
    def record_type(self, evidence: dict) -> Decision:
        ev = self._ev(evidence)
        if ev["personal_consumer_ai_usage"] and not ev["acts_on_bank_systems"]:
            return Decision("not_agent", "RT-0")
        if ev["operator"] in EXTERNAL_OPERATORS:
            return Decision("external_agent", "RT-1")
        if ev["runs_on_user_device"]:
            return Decision("endpoint_agent", "RT-2")
        if ev["model_selects_tools"] or ev["writes_without_human_review"]:
            return Decision("agent", "RT-3")
        if ev["kind"] in INFRA_KINDS:
            return Decision("infrastructure", "RT-4")
        if ev["calls_llm"]:
            return Decision("ai_system", "RT-5")
        return Decision("not_agent", "RT-6")

    # ---------------------------------------------------------- managed status
    def managed_status(self, evidence: dict) -> Decision:
        ev = self._ev(evidence)
        recent = self.runtime_recent(ev)
        ever_seen = ev["days_since_runtime"] is not None
        if ev["retired_confirmed"]:
            return Decision("retired", "MS-1")
        if ev["standby"]:
            return Decision("standby", "MS-2")
        if not ev["collector_health_ok"]:
            return Decision(ev["previous_status"] or "unknown", "MS-3")
        if ev["platform_api_found"] and not (ev["registered"] and ev["active_owner"]):
            return Decision("unmanaged", "MS-4")
        if not ev["registered"] and recent and not ev["code_found"]:
            return Decision("shadow", "MS-5", "ghost")
        if not ev["registered"] and recent:
            return Decision("shadow", "MS-6")
        if not recent and (ever_seen or ev["code_found"]):
            return Decision("dormant", "MS-7", "zombie" if ev["credentials_live"] else None)
        if not recent:
            return Decision("declared", "MS-8")
        if (ev["approved"] and ev["active_owner"] and ev["runtime_identity_matches"]
                and ev["via_gateway"] and ev["minimum_profile_complete"]):
            return Decision("managed", "MS-9")
        return Decision("unmanaged", "MS-10")

    # ----------------------------------------------------------- identity level
    def identity_level(self, evidence: dict) -> Decision:
        ev = self._ev(evidence)
        idn = {"principal_is_human": False, "shared": False, "has_identity": True,
               "static_secret": False, "idp_record": True,
               "delegation_tokens": False, "access_review_recent": False}
        idn.update(ev.get("identity") or {})
        if idn["principal_is_human"] or idn["shared"] or not idn["has_identity"]:
            return Decision(0, "IL-1")
        if idn["static_secret"] or not idn["idp_record"] or not ev["active_owner"]:
            return Decision(1, "IL-2")
        if idn["delegation_tokens"] and idn["access_review_recent"]:
            return Decision(3, "IL-3")
        return Decision(2, "IL-4")

    # -------------------------------------------------------------- confidence
    def confidence(self, planes: list[str]) -> int:
        return min(100, sum(self.weights.get(p, 0) for p in set(planes)))

    # -------------------------------------------------------------------- risk
    def risk_score(self, risk: dict, managed_status: Optional[str] = None,
                   identity_level: Optional[int] = None) -> dict:
        f = self.risk["factors"]
        cap = max((f["capability"][c] for c in risk.get("capabilities", [])), default=0.2)
        exp = max((f["exposure"][e] for e in risk.get("exposure", [])), default=0.2)
        dat = max((f["data_sensitivity"][d] for d in risk.get("data", [])), default=0.2)
        cc = self.risk["control_coverage"]
        coverage = min(cc["max_coverage"], sum(cc["credits"][c] for c in risk.get("controls", [])))
        score = round(cap * exp * dat * (1 - coverage) * 100)
        tier = next(t["tier"] for t in self.risk["tiers"] if score < t["below"])
        applied = []

        def raise_to(min_tier: str, rule: str):
            nonlocal tier
            if TIER_ORDER.index(min_tier) > TIER_ORDER.index(tier):
                tier = min_tier
            applied.append(rule)

        caps = set(risk.get("capabilities", []))
        controls = set(risk.get("controls", []))
        untrusted = bool(risk.get("untrusted_input")) or bool(
            set(self.risk["untrusted_exposures"]) & set(risk.get("exposure", [])))
        toxic = untrusted and dat >= 0.8 and cap >= 0.8
        if toxic:
            raise_to("critical", "RO-1")
        if caps & {"money_movement", "credit_decision"} and "human_in_the_loop_before_write" not in controls:
            raise_to("critical", "RO-2")
        if risk.get("credit_scoring_of_individuals"):
            raise_to("high", "RO-3")
        if managed_status == "shadow" or identity_level == 0:
            raise_to("high", "RO-4")
        if risk.get("customer_facing") or "customer_facing" in risk.get("exposure", []):
            raise_to("medium", "RO-5")
        return {"score": score, "tier": tier, "toxic_combination": toxic, "overrides_applied": applied}

    # ------------------------------------------------------------ merge / drift
    @staticmethod
    def merge_decision(rank: int, same_environment: bool = True) -> str:
        if rank in (1, 2, 3):
            return "auto_merge"
        if rank == 4:
            return "auto_merge" if same_environment else "no_merge"
        return "steward_review"

    def source_of_truth(self, attribute: str) -> str:
        return self.source_of_truth_map[attribute]

    @staticmethod
    def drift(previous: dict, current: dict) -> list[str]:
        order_cls = ["public", "internal", "pii", "account", "card", "credit"]
        order_share = ["single_team", "tenant_internal", "partner", "customer", "public"]
        out = []
        if previous.get("served_model") != current.get("served_model"):
            out.append("model_served_changed")
        if set(previous.get("tools", [])) != set(current.get("tools", [])):
            out.append("tool_added_or_removed")
        if previous.get("tool_hashes", {}) != current.get("tool_hashes", {}):
            out.append("tool_definition_hash_changed")
        if previous.get("prompt_hash") != current.get("prompt_hash"):
            out.append("system_prompt_hash_changed")
        if set(current.get("data_sources", [])) - set(previous.get("data_sources", [])):
            out.append("data_source_added")
        pc, cc = previous.get("data_classification"), current.get("data_classification")
        if pc and cc and order_cls.index(cc) > order_cls.index(pc):
            out.append("data_classification_raised")
        if previous.get("permissions_hash") != current.get("permissions_hash"):
            out.append("identity_or_permissions_changed")
        ps, cs = previous.get("sharing"), current.get("sharing")
        if ps and cs and order_share.index(cs) > order_share.index(ps):
            out.append("sharing_scope_widened")
        if set(current.get("channels", [])) - set(previous.get("channels", [])):
            out.append("new_channel_or_caller")
        if previous.get("owner_active", True) and not current.get("owner_active", True):
            out.append("owner_left")
        return out

    # -------------------------------------------------------------------- spans
    @staticmethod
    def span_decision(span: dict) -> Decision:
        key_present = span.get("agent_key_present", False)
        if not key_present and span.get("collector_enrichment_found"):
            key_present = True  # SP-0: stamped from CMDB lookup on attested facts
            known = True
        else:
            known = span.get("agent_key_known", False)
        if not key_present and span.get("genai_operation", False):
            return Decision("shadow_candidate", "SP-1")
        if key_present and not known:
            return Decision("shadow_alert", "SP-2")
        if key_present and not span.get("identity_matches", True):
            return Decision("quarantine_and_flag_impersonation", "SP-3")
        return Decision("accept_into_provenance", "SP-4")

    # ---------------------------------------------------------------- one call
    def classify(self, evidence: dict) -> dict:
        """Full classification of one candidate record."""
        rt = self.record_type(evidence)
        out: dict[str, Any] = {"record_type": rt.value, "rules": [rt.rule]}
        if rt.value in ("agent", "endpoint_agent"):
            ms = self.managed_status(evidence)
            il = self.identity_level(evidence)
            out.update(managed_status=ms.value, managed_subtype=ms.subtype, identity_level=il.value)
            out["rules"] += [ms.rule, il.rule]
            if "risk" in evidence:
                r = self.risk_score(evidence["risk"], ms.value, il.value)
                out.update(risk_score=r["score"], risk_tier=r["tier"], toxic_combination=r["toxic_combination"])
                out["rules"] += r["overrides_applied"]
        elif "risk" in evidence:
            r = self.risk_score(evidence["risk"])
            out.update(risk_score=r["score"], risk_tier=r["tier"], toxic_combination=r["toxic_combination"])
            out["rules"] += r["overrides_applied"]
        if "planes" in evidence:
            out["confidence"] = self.confidence(evidence["planes"])
        return out
