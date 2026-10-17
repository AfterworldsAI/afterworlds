"""Scripted provider HTTP transport -- tests and E2E only (CRD Issue 21).

Replaces only the external provider transport: the real ``anthropic`` and
``openai`` SDK clients that ``AnthropicDirectAdapter``, ``OpenRouterAdapter``
and the BYOK credential check construct are given an ``httpx.MockTransport``
that answers in each provider's wire format. Everything above the wire --
``ProviderResolver``, readiness, binding, refusal fallback, the adapters'
request building, response parsing and refusal detection, and every pass
service's own parser -- runs unchanged. Never imported by ``create_app``.

Each request is identified by its forced tool (or, for text passes, by the
classifier prompt / OOC instruction) and answered by a deterministic default
responder unless a scripted reply was queued for that pass with
:meth:`ScriptedProvider.push`. Every request body is recorded so tests can
assert what a pass actually received.
"""

from __future__ import annotations

import json
import re
import threading
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import httpx2 as httpx  # the transport both provider SDKs use

#: Synthetic hosted key for launchers and tests; never a real credential.
SYNTHETIC_HOSTED_KEY = "sk-ant-SYNTHETIC-hosted-0000000000"  # pragma: allowlist secret

_TOOL_PASS = {
    "produce_plan": "planner",
    "propose_canon_updates": "extractor",
    "report_contradictions": "contradiction",
    "report_safety_assessment": "safety",
    "produce_adjudication_proposals": "rpg_adjudication",
    "produce_branch_output": "branching_writer",
    "extract_branching_config_update": "branching_ooc_config_extractor",
    "record_rolling_summary": "rolling_summary",
    "produce_rpg_setup_turn": "rpg_setup_writer",
}
_RANGES = {"1-2": 1, "2-3": 2, "3-4": 3, "2-4": 2, "2-5": 2}
_CLASSIFY_MARKER = "## Player Input to Classify"
_REFUSAL_TEXT = "I can't assist with that request."


@dataclass
class Reply:
    """One scripted answer. Exactly one of the fields is meaningful:
    ``text`` (text content), ``tool_input`` (forced-tool arguments),
    ``refusal`` (a content-policy refusal) or ``status`` (an HTTP error)."""

    text: str | None = None
    tool_input: dict[str, Any] | None = None
    refusal: bool = False
    status: int | None = None


@dataclass
class Call:
    api: str  # "anthropic" | "openrouter"
    pass_name: str
    body: dict[str, Any]
    texts: list[str]
    api_key: str


@dataclass
class ScriptedProvider:
    calls: list[Call] = field(default_factory=list)
    _queues: dict[str, deque[Reply]] = field(default_factory=lambda: defaultdict(deque))
    _lock: threading.Lock = field(default_factory=threading.Lock)
    _undo: list[Callable[[], None]] = field(default_factory=list)

    # -- scripting ---------------------------------------------------------

    def push(self, pass_name: str, *replies: Reply) -> None:
        """Queue replies for the next calls of *pass_name* (FIFO)."""
        with self._lock:
            self._queues[pass_name].extend(replies)

    def reset(self) -> None:
        with self._lock:
            self._queues.clear()
            self.calls.clear()

    def calls_for(self, pass_name: str) -> list[Call]:
        with self._lock:
            return [c for c in self.calls if c.pass_name == pass_name]

    # -- installation ------------------------------------------------------

    def install(self) -> ScriptedProvider:
        """Route every new ``anthropic.Anthropic`` / ``openai.OpenAI`` client
        through this transport. Undo with :meth:`uninstall`."""
        import anthropic
        import openai

        transport = httpx.MockTransport(self._handle)
        for module, name in ((anthropic, "Anthropic"), (openai, "OpenAI")):
            real = getattr(module, name)

            def factory(*args: Any, _real: Any = real, **kwargs: Any) -> Any:
                kwargs["http_client"] = httpx.Client(transport=transport)
                return _real(*args, **kwargs)

            setattr(module, name, factory)
            self._undo.append(
                lambda module=module, name=name, real=real: setattr(module, name, real)
            )
        return self

    def uninstall(self) -> None:
        while self._undo:
            self._undo.pop()()

    # -- transport ---------------------------------------------------------

    def _handle(self, request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content or b"{}")
        api = "openrouter" if "chat/completions" in request.url.path else "anthropic"
        key = request.headers.get("x-api-key") or request.headers.get(
            "authorization", ""
        ).removeprefix("Bearer ")
        if "invalid" in key:
            return httpx.Response(401, json=_error_body(api, "invalid api key"))
        texts = _texts(body, api)
        pass_name = _identify(body, texts, api)
        with self._lock:
            self.calls.append(Call(api, pass_name, body, texts, key))
            queue = self._queues.get(pass_name)
            reply = queue.popleft() if queue else None
        if reply is None:
            reply = _default(pass_name, texts)
        if reply.status is not None:
            return httpx.Response(reply.status, json=_error_body(api, "scripted"))
        tool = _forced_tool(body, api)
        return httpx.Response(200, json=_reply_body(api, body, reply, tool, texts))


# ---------------------------------------------------------------------------
# Request inspection
# ---------------------------------------------------------------------------


def _texts(body: dict[str, Any], api: str) -> list[str]:
    out: list[str] = []
    if api == "anthropic":
        system = body.get("system")
        if isinstance(system, str):
            out.append(system)
        for block in system or []:
            if isinstance(block, dict):
                out.append(block.get("text", ""))
    for message in body.get("messages", []):
        content = message.get("content")
        if isinstance(content, str):
            out.append(content)
        else:
            out.extend(b.get("text", "") for b in content or [] if isinstance(b, dict))
    return out


def _forced_tool(body: dict[str, Any], api: str) -> str | None:
    choice = body.get("tool_choice")
    if not isinstance(choice, dict):
        return None
    if api == "anthropic":
        return choice.get("name")
    return (choice.get("function") or {}).get("name")


def _identify(body: dict[str, Any], texts: list[str], api: str) -> str:
    tool = _forced_tool(body, api)
    if tool is not None:
        return _TOOL_PASS.get(tool, tool)
    joined = "\n".join(texts)
    if _CLASSIFY_MARKER in joined:
        return "intent_classifier"
    if joined.strip() == "ping":
        return "credential_check"
    if "out-of-character" in joined.lower() and "OOC" in joined:
        return "ooc_writer"
    return "writer"


def classified_input(texts: list[str]) -> str:
    joined = "\n".join(texts)
    return joined.split(_CLASSIFY_MARKER, 1)[-1].strip()


def current_input(texts: list[str]) -> str:
    """The last ``Player:`` line a pass rendered (its current input)."""
    found = ""
    for text in texts:
        for line in text.splitlines():
            if line.startswith("Player: "):
                found = line.removeprefix("Player: ")
    return found


# ---------------------------------------------------------------------------
# Deterministic defaults
# ---------------------------------------------------------------------------


def _narrate(player_input: str) -> str:
    if player_input.startswith("[Begin story]"):
        return "The story opens on a rain-dark harbor at dusk."
    return f"The narrator answers: {player_input}."


def _default(pass_name: str, texts: list[str]) -> Reply:
    joined = "\n".join(texts)
    if pass_name == "intent_classifier":
        raw = classified_input(texts)
        intent = "in_character_action"
        if raw.lower().startswith(("[ooc]", "ooc:")):
            intent = "ooc"
        elif re.search(r"\bopt_\d+\b|\bI choose\b|\boption \d+\b", raw, re.I):
            intent = "branch_choice"
        return Reply(
            text=json.dumps(
                {
                    "intent_type": intent,
                    "confidence": 0.95,
                    "ambiguous": False,
                    "secondary_intent": None,
                }
            )
        )
    if pass_name == "credential_check":
        return Reply(text="pong")
    if pass_name == "planner":
        return Reply(
            tool_input={
                "scene_goal": "Advance the scene from the Sojourner's input.",
                "next_beat": "The world responds.",
                "facts_needed": [],
            }
        )
    if pass_name == "writer":
        # The prose Writer renders its current input as the last block
        # before its intent block.
        inputs = [x for x in texts if not x.startswith("[INTENT CLASSIFICATION]")]
        return Reply(text=_narrate(inputs[-1] if inputs else ""))
    if pass_name == "ooc_writer":
        return Reply(text="Out of character: understood.")
    if pass_name == "extractor":
        return Reply(tool_input={"proposals": []})
    if pass_name == "contradiction":
        return Reply(tool_input={"violations": []})
    if pass_name == "safety":
        return Reply(tool_input={"concerns": []})
    if pass_name == "rpg_adjudication":
        return Reply(tool_input={"rolls": []})
    if pass_name == "branching_writer":
        match = re.search(r"branch_count_range: (\S+)", joined)
        count = _RANGES.get(match.group(1), 2) if match else 2
        return Reply(
            tool_input={
                "narrative_text": _narrate(current_input(texts)),
                "branch_options_text": [f"Path {i + 1}" for i in range(count)],
                "branch_presentation_state": "shown",
            }
        )
    if pass_name == "branching_ooc_config_extractor":
        ooc = " ".join(
            line for line in joined.splitlines() if line.startswith("Player (OOC): ")
        ).lower()
        style = next(
            (
                v
                for k, v in (
                    ("true cyoa", "true_cyoa"),
                    ("hybrid", "hybrid"),
                    ("freeform", "freeform_only"),
                )
                if k in ooc
            ),
            None,
        )
        return Reply(
            tool_input={
                "interaction_style": style,
                "branching_cadence": None,
                "branch_count_range": None,
                "length_preference": None,
            }
        )
    if pass_name == "rpg_setup_writer":
        # World: state an understanding; configuration: summarize; character
        # creation: clarify (tests script the character proposal explicitly).
        player = current_input(texts)
        if "phase: world_setup" in joined:
            result: dict[str, Any] = {
                "kind": "world_confirmation",
                "understanding": f"I understand the world as: {player}",
            }
        elif "phase: play_configuration" in joined:
            result = {"kind": "configuration_summary"}
            # Summarize the configuration actually rendered for this turn.
            settings = re.findall(
                r"^((?:session_type|tone|dice_handling|gm_cheating|house_rules"
                r"|acceptable_content): .*)$",
                joined,
                re.MULTILINE,
            )
            player = f"{player} Your settings: {'; '.join(settings)}."
        else:
            result = {"kind": "clarification", "questions": ["Tell me more."]}
        return Reply(
            tool_input={
                "schema_version": 1,
                "gm_text": f"The GM responds: {player}",
                "result": result,
            }
        )
    if pass_name == "rolling_summary":
        block = next(
            (t for t in texts if t.startswith("[Rolling Summary Compression]")), ""
        )
        prior = block.split("prior_summary:\n", 1)[-1].split("\n\nwindow:", 1)[0]
        narration = re.findall(r"Narration: (.+)", block)
        summary = " ".join(
            ([] if prior == "none" else [prior]) + [f"[{n[:60]}]" for n in narration]
        )
        return Reply(tool_input={"summary": summary})
    raise AssertionError(f"no scripted default for pass {pass_name!r}")


# ---------------------------------------------------------------------------
# Wire formats
# ---------------------------------------------------------------------------


def _usage(body: dict[str, Any]) -> tuple[int, int]:
    return max(1, len(json.dumps(body)) // 4), 40


def _reply_body(
    api: str, body: dict[str, Any], reply: Reply, tool: str | None, texts: list[str]
) -> dict[str, Any]:
    in_tokens, out_tokens = _usage(body)
    model = body.get("model", "scripted")
    if api == "anthropic":
        if reply.refusal:
            content: list[dict[str, Any]] = [{"type": "text", "text": _REFUSAL_TEXT}]
            stop = "refusal"
        elif reply.tool_input is not None:
            content = [
                {
                    "type": "tool_use",
                    "id": "toolu_scripted",
                    "name": tool or "unknown_tool",
                    "input": reply.tool_input,
                }
            ]
            stop = "tool_use"
        else:
            content = [{"type": "text", "text": reply.text or ""}]
            stop = "end_turn"
        return {
            "id": "msg_scripted",
            "type": "message",
            "role": "assistant",
            "model": model,
            "content": content,
            "stop_reason": stop,
            "stop_sequence": None,
            "usage": {
                "input_tokens": in_tokens,
                "output_tokens": out_tokens,
                "cache_read_input_tokens": 0,
                "cache_creation_input_tokens": 0,
            },
        }
    message: dict[str, Any] = {"role": "assistant", "content": None}
    finish = "stop"
    if reply.refusal:
        # OpenRouterAdapter detects a start-anchored refusal phrase in text.
        message["content"] = _REFUSAL_TEXT
    elif reply.tool_input is not None:
        message["tool_calls"] = [
            {
                "id": "call_scripted",
                "type": "function",
                "function": {
                    "name": tool or "unknown_tool",
                    "arguments": json.dumps(reply.tool_input),
                },
            }
        ]
        finish = "tool_calls"
    else:
        message["content"] = reply.text or ""
    return {
        "id": "chatcmpl-scripted",
        "object": "chat.completion",
        "created": 0,
        "model": model,
        "choices": [{"index": 0, "message": message, "finish_reason": finish}],
        "usage": {
            "prompt_tokens": in_tokens,
            "completion_tokens": out_tokens,
            "total_tokens": in_tokens + out_tokens,
        },
    }


def _error_body(api: str, message: str) -> dict[str, Any]:
    if api == "anthropic":
        return {"type": "error", "error": {"type": "api_error", "message": message}}
    return {"error": {"message": message, "code": 500}}
