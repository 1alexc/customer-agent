#!/usr/bin/env python3
"""Deploy Customer Support Agent to Vertex AI Agent Runtime with Agent Identity.

Supports both in-place updates of existing runtimes (revisions) and new deployments.
Usage:
    python3 deploy.py           # Updates existing AGENT_RESOURCE_NAME from .env (in-place)
    python3 deploy.py --new     # Forces creating a brand-new Reasoning Engine instance
    python3 deploy.py --resource projects/.../reasoningEngines/...  # Updates a specific instance
"""

import argparse
import logging
import os
from pathlib import Path
from dotenv import load_dotenv

# 1. Environment & Logging Setup
CURRENT_DIR = Path(__file__).resolve().parent
os.chdir(CURRENT_DIR)
for env_candidate in [CURRENT_DIR / ".env", CURRENT_DIR / "customer_support" / ".env"]:
    if env_candidate.exists():
        load_dotenv(env_candidate, override=True)
        break

import agentplatform
from agentplatform import types
from agentplatform.frameworks import AdkApp
import google.adk

from customer_support.agent import root_agent

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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Deploy or update Customer Support Agent on Vertex AI Agent Runtime."
    )
    parser.add_argument(
        "--new",
        action="store_true",
        help="Force creation of a new Agent Runtime instance instead of updating the existing one.",
    )
    parser.add_argument(
        "--resource",
        default=os.getenv("AGENT_RESOURCE_NAME"),
        help="Target Agent Runtime resource name to update (defaults to AGENT_RESOURCE_NAME in .env).",
    )
    return parser.parse_args()


args = parse_args()

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

# 4. Prepare Deployment Config
deployment_config = {
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
        "MODEL_ARMOR_INPUT_TEMPLATE": os.getenv("MODEL_ARMOR_INPUT_TEMPLATE", ""),
        "MODEL_ARMOR_OUTPUT_TEMPLATE": os.getenv("MODEL_ARMOR_OUTPUT_TEMPLATE", ""),
    },
}

app = AdkApp(agent=root_agent)

# 5. Execute In-Place Update or New Deployment
is_update = bool(args.resource and not args.new)

if is_update:
    print(f"\n[IN-PLACE UPDATE] Deploying new revision to existing Agent Runtime:")
    print(f"Target Resource: {args.resource}")
    print(f"Agent:           {root_agent.name} (ADK {ADK_VERSION})\n")
    remote_app = client.runtimes.update(
        name=args.resource,
        agent=app,
        config=deployment_config,
    )
else:
    print(f"\n[NEW DEPLOYMENT] Creating new Agent Runtime instance:")
    print(f"Location:        {LOCATION}")
    print(f"Agent:           {root_agent.name} (ADK {ADK_VERSION})\n")
    remote_app = client.runtimes.create(
        agent=app,
        config=deployment_config,
    )

# 6. Output Resource Info & Auto-update .env
resource_name = getattr(
    getattr(remote_app, "api_resource", None), "name", args.resource if is_update else "N/A"
)
effective_identity = getattr(
    getattr(remote_app, "api_resource", None), "spec", None
)
effective_identity = getattr(effective_identity, "effective_identity", "N/A")

print("\n" + "=" * 65)
if is_update:
    print("IN-PLACE UPDATE SUCCESSFUL! (New revision active)")
else:
    print("DEPLOYMENT SUCCESSFUL!")
print("=" * 65)
print(f"Remote Resource Name: {resource_name}")
if effective_identity != "N/A":
    print(f"Agent Identity:       {effective_identity}")
print("=" * 65)

if resource_name != "N/A":
    for env_path in [CURRENT_DIR / ".env", CURRENT_DIR / "customer_support" / ".env"]:
        if env_path.exists():
            lines = env_path.read_text().splitlines()
            updated = False
            for i, line in enumerate(lines):
                if line.startswith("AGENT_RESOURCE_NAME="):
                    lines[i] = f"AGENT_RESOURCE_NAME={resource_name}"
                    updated = True
                    break
            if not updated:
                lines.append(f"AGENT_RESOURCE_NAME={resource_name}")
            env_path.write_text("\n".join(lines) + "\n")
            print(f"Synced {env_path.relative_to(CURRENT_DIR)} with AGENT_RESOURCE_NAME.")

print("\nTest with:")
print('  python3 test_agent.py "Where is ORD-1004?"\n')