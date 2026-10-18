#!/usr/bin/env python3
"""Deploy Customer Support Agent to Vertex AI Agent Runtime with Agent Identity."""

import logging
import os
from pathlib import Path
from dotenv import load_dotenv

import agentplatform
from agentplatform import types
from agentplatform.frameworks import AdkApp
import google.adk

from customer_support.agent import root_agent

# 1. Environment & Logging Setup
CURRENT_DIR = Path(__file__).resolve().parent
os.chdir(CURRENT_DIR)
load_dotenv(CURRENT_DIR / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)

PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT")
if not PROJECT_ID:
    raise SystemExit("Error: GOOGLE_CLOUD_PROJECT is required in .env")

LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
BUCKET = os.getenv("STAGING_BUCKET", f"gs://{PROJECT_ID}-agent-runtime-staging")
ADK_VERSION = getattr(google.adk, "__version__", "1.33.0")

# 2. Compatibility Patch (fixes 'LlmAgent' object has no attribute 'mode')
for ag in [root_agent] + getattr(root_agent, "sub_agents", []):
    if not hasattr(ag, "mode") or ag.mode is None:
        try:
            object.__setattr__(ag, "mode", "chat")
        except Exception:
            pass

# 3. Initialize Agent Platform Client (v1beta1 for Agent Identity)
client = agentplatform.Client(
    project=PROJECT_ID,
    location=LOCATION,
    http_options={"api_version": "v1beta1"},
)

# 4. Deploy AdkApp with Agent Identity
print(f"Deploying {root_agent.name} (ADK {ADK_VERSION}) to Agent Runtime ({LOCATION})...")
app = AdkApp(agent=root_agent)

remote_app = client.runtimes.create(
    agent=app,
    config={
        "display_name": "customer-support-agent",
        "identity_type": types.IdentityType.AGENT_IDENTITY,
        "staging_bucket": BUCKET,
        "requirements": [
            "google-cloud-agentplatform[agent-engines,adk]>=2.5.0",
            "google-cloud-aiplatform[agent_engines,adk]>=1.152.0",
            "cloudpickle>=3.0.0",
            f"google-adk=={ADK_VERSION}",
            "google-genai>=1.75.0",
            "python-dotenv>=1.0.0",
            "pydantic>=2.0.0",
        ],
        "extra_packages": ["customer_support"],
        "env_vars": {
            "GOOGLE_GENAI_USE_VERTEXAI": "true",
            "GOOGLE_CLOUD_LOCATION": LOCATION,
            "SUPPORT_MODEL": os.getenv("SUPPORT_MODEL", "gemini-2.5-flash"),
        },
    },
)

# 5. Output Resource Info & Auto-update .env
resource_name = getattr(remote_app.api_resource, "name", "N/A")
effective_identity = getattr(
    remote_app.api_resource.spec, "effective_identity", "N/A"
)

print("\n" + "=" * 65)
print("DEPLOYMENT SUCCESSFUL!")
print("=" * 65)
print(f"Remote Resource Name: {resource_name}")
print(f"Agent Identity:       {effective_identity}")
print("=" * 65)

if resource_name != "N/A":
    env_path = CURRENT_DIR / ".env"
    lines = env_path.read_text().splitlines() if env_path.exists() else []
    updated = False
    for i, line in enumerate(lines):
        if line.startswith("AGENT_RESOURCE_NAME="):
            lines[i] = f"AGENT_RESOURCE_NAME={resource_name}"
            updated = True
            break
    if not updated:
        lines.append(f"AGENT_RESOURCE_NAME={resource_name}")
    env_path.write_text("\n".join(lines) + "\n")
    print(f"Updated {env_path.name} with AGENT_RESOURCE_NAME.")

print("\nTest with:")
print('  python3 test_agent.py "Where is ORD-1004?"\n')