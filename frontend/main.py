"""Minimal FastAPI proxy for a deployed A2A agent (Agent Runtime, agents-cli 1.1.0+).

The browser talks ONLY to this proxy (same origin, no CORS, no GCP creds in the
browser). The proxy authenticates with Application Default Credentials and
forwards chat to the deployed agent over the A2A protocol, returning replies as
structured parts the chat UI knows how to show:

  * {"kind": "text", "text": ...}  -> a normal chat bubble
  * {"kind": "a2ui", "data": ...}  -> one A2UI message (beginRendering /
    surfaceUpdate); static/index.html renders these as a card.
"""

import json
import os
import re
import uuid

import google.auth
import google.auth.transport.requests
import httpx
from a2a.client import ClientConfig, ClientFactory
from a2a.types import (
    AgentCard,
    Message,
    Part,
    Role,
    TaskArtifactUpdateEvent,
)
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

try:
    from a2a.types import SendMessageRequest
except ImportError:
    SendMessageRequest = None

try:
    from a2a.types import FilePart, TextPart
except ImportError:
    FilePart = None
    TextPart = None

try:
    from a2a.types import TransportProtocol
except ImportError:
    TransportProtocol = None

RESOURCE = os.environ.get(
    "AGENT_ENGINE_RESOURCE_NAME",
    "projects/976987337939/locations/us-east1/reasoningEngines/4697036708045127680",
)
# The agent's app directory (matches agent_directory in agents-cli-manifest.yaml).
AGENT_DIRECTORY = os.environ.get("AGENT_DIRECTORY", "app")
# Location is embedded in the resource name: projects/<p>/locations/<loc>/reasoningEngines/<id>.
LOCATION = RESOURCE.split("/locations/")[1].split("/")[0]

# A2A endpoint for an Agent Runtime deployment, via the Agent Engine HTTP
# passthrough. The card lives at the well-known path under this base.
A2A_BASE = (
    f"https://{LOCATION}-aiplatform.googleapis.com/reasoningEngines/v1/"
    f"{RESOURCE}/api/a2a/{AGENT_DIRECTORY}"
)
A2A_CARD_URL = f"{A2A_BASE}/.well-known/agent-card.json"

# The agent tags its A2UI data parts with this mime type.
_A2UI_MIME = "application/json+a2ui"

# One set of ADC credentials, refreshed per request (access tokens expire ~1h).
_creds, _ = google.auth.default(
    scopes=["https://www.googleapis.com/auth/cloud-platform"]
)


def _auth_headers() -> dict[str, str]:
    _creds.refresh(google.auth.transport.requests.Request())
    return {
        "Authorization": f"Bearer {_creds.token}",
        "Content-Type": "application/json",
    }


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def _json_errors(request: Request, exc: Exception):
    # Always return JSON so the browser never receives a plain-text 500 page
    return JSONResponse(
        status_code=200,
        content={
            "parts": [{"kind": "text", "text": f"Error: {type(exc).__name__}: {exc}"}]
        },
    )


# Reuse ONE A2A context per user so the agent remembers the conversation.
_contexts: dict[str, str] = {}
# Cache the agent card after the first fetch.
_card: AgentCard | None = None


async def _get_card(client: httpx.AsyncClient) -> AgentCard:
    global _card
    if _card is None:
        resp = await client.get(A2A_CARD_URL)
        resp.raise_for_status()
        data = resp.json()
        try:
            card = AgentCard(**data)
            if hasattr(card, "url"):
                setattr(card, "url", A2A_BASE)
        except Exception:
            from google.protobuf.json_format import ParseDict

            card = AgentCard()
            ParseDict(data, card, ignore_unknown_fields=True)
            for iface in getattr(card, "supported_interfaces", []):
                iface.url = A2A_BASE
        _card = card
    return _card


def _extract_parts(parts: list) -> list[dict]:
    """Turn A2A response parts into structured parts for the chat UI.

    Text parts pass through as {"kind": "text"}. A2UI data parts (tagged
    application/json+a2ui) become {"kind": "a2ui", "data": <message>} so the UI
    renders the card; each data part is one A2UI message (beginRendering or
    surfaceUpdate).
    """
    out: list[dict] = []
    for p in parts:
        root = getattr(p, "root", p)
        # Check text content
        text = getattr(root, "text", None)
        if text:
            # Check for <a2ui-json> or <a2a_datapart_json> tags
            a2ui_match = re.search(
                r"<(?:a2ui-json|a2a_datapart_json[^>]*)>(.*?)</(?:a2ui-json|a2a_datapart_json)>",
                text,
                re.DOTALL,
            )
            if a2ui_match:
                json_str = a2ui_match.group(1).strip()
                try:
                    data = json.loads(json_str)
                    items = data if isinstance(data, list) else [data]
                    for item in items:
                        if (
                            isinstance(item, dict)
                            and "components" in item
                            and "surfaceUpdate" not in item
                        ):
                            norm_item = {
                                "surfaceUpdate": {"components": item["components"]}
                            }
                            if "surfaceId" in item:
                                norm_item["surfaceId"] = item["surfaceId"]
                            out.append({"kind": "a2ui", "data": norm_item})
                        else:
                            out.append({"kind": "a2ui", "data": item})
                except Exception:
                    out.append({"kind": "text", "text": text})

                remaining_text = re.sub(
                    r"<(?:a2ui-json|a2a_datapart_json[^>]*)>.*?</(?:a2ui-json|a2a_datapart_json)>",
                    "",
                    text,
                    flags=re.DOTALL,
                ).strip()
                if remaining_text:
                    out.append({"kind": "text", "text": remaining_text})
                continue
            else:
                out.append({"kind": "text", "text": text})
                continue

        # Check A2UI / structured data content
        data = getattr(root, "data", None)
        if data is not None:
            meta = getattr(root, "metadata", None) or {}
            mime = (
                meta.get("mimeType")
                if isinstance(meta, dict)
                else getattr(meta, "mime_type", None)
            )
            if mime == _A2UI_MIME:
                out.append({"kind": "a2ui", "data": data})
                continue

        # Check URL / file content
        url = getattr(root, "url", None) or getattr(
            getattr(root, "file", None), "uri", None
        )
        if url:
            out.append({"kind": "text", "text": url})

    return out


@app.post("/chat")
async def chat(req: Request):
    body = await req.json()
    message = body.get("message", "")
    user_id = body.get("user_id") or "web-user"
    parts: list[dict] = []

    async with httpx.AsyncClient(headers=_auth_headers(), timeout=120) as client:
        card = await _get_card(client)
        if TransportProtocol is not None:
            cfg = ClientConfig(
                supported_transports=[
                    TransportProtocol.jsonrpc,
                    TransportProtocol.http_json,
                ],
                httpx_client=client,
            )
        else:
            cfg = ClientConfig(httpx_client=client)

        factory = ClientFactory(cfg)
        a2a_client = factory.create(card)

        if TextPart is not None:
            part_obj = Part(root=TextPart(text=message))
        else:
            part_obj = Part(text=message)

        if hasattr(Role, "user"):
            user_role = Role.user
        elif hasattr(Role, "ROLE_USER"):
            user_role = Role.ROLE_USER
        else:
            user_role = "user"

        msg = Message(
            message_id=str(uuid.uuid4()),
            role=user_role,
            parts=[part_obj],
            context_id=_contexts.get(user_id),
        )

        last_task = None
        got_artifact_update = False

        # Support both a2a-sdk 0.3.x (pass Message directly) and 1.x (SendMessageRequest)
        try:
            stream = a2a_client.send_message(msg)
        except Exception:
            if SendMessageRequest is not None:
                stream = a2a_client.send_message(SendMessageRequest(message=msg))
            else:
                raise

        async for event in stream:
            if isinstance(event, tuple):
                task, update = event
                if task is not None:
                    last_task = task
                    if getattr(task, "context_id", None):
                        _contexts[user_id] = task.context_id
                if isinstance(update, TaskArtifactUpdateEvent):
                    got_artifact_update = True
                    parts.extend(_extract_parts(update.artifact.parts))
            else:
                if hasattr(event, "HasField"):
                    if event.HasField("task"):
                        last_task = event.task
                        if getattr(event.task, "context_id", None):
                            _contexts[user_id] = event.task.context_id
                    if event.HasField("artifact_update"):
                        got_artifact_update = True
                        parts.extend(_extract_parts(event.artifact_update.artifact.parts))
                    elif event.HasField("message"):
                        parts.extend(_extract_parts(event.message.parts))
                else:
                    task = getattr(event, "task", None)
                    if task:
                        last_task = task
                        if getattr(task, "context_id", None):
                            _contexts[user_id] = task.context_id
                    art_update = getattr(event, "artifact_update", None)
                    if art_update:
                        got_artifact_update = True
                        art = getattr(art_update, "artifact", None)
                        if art:
                            parts.extend(_extract_parts(art.parts))
                    msg_obj = getattr(event, "message", None)
                    if msg_obj:
                        parts.extend(_extract_parts(msg_obj.parts))

        # Non-streaming fallback: pull parts from the final task's artifacts.
        if not got_artifact_update and last_task is not None:
            for artifact in getattr(last_task, "artifacts", None) or []:
                parts.extend(_extract_parts(artifact.parts))

    if not parts:
        parts = [{"kind": "text", "text": "(The agent didn't return a reply.)"}]
    return JSONResponse({"parts": parts})


# Serve the chat UI (keep this mount last so /chat wins).
app.mount("/", StaticFiles(directory="static", html=True), name="static")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
