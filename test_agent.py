#!/usr/bin/env python3
"""Query the deployed Customer Support Agent on Vertex AI Agent Runtime.

Usage:
    python3 test_agent.py "Where is ORD-1004?"
    python3 test_agent.py "I want a refund for ORD-1002"
    python3 test_agent.py --verbose "Where is ORD-1004?"
"""

import argparse
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load configuration from .env file (keeps project & resource IDs out of Git)
CURRENT_DIR = Path(__file__).resolve().parent
for env_candidate in [CURRENT_DIR / ".env", CURRENT_DIR / "customer_support" / ".env"]:
    if env_candidate.exists():
        load_dotenv(env_candidate)
        break

DEFAULT_RESOURCE = os.getenv("AGENT_RESOURCE_NAME")
DEFAULT_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
DEFAULT_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Query the deployed Agent Runtime instance."
    )
    parser.add_argument(
        "message",
        nargs="?",
        default="Where is ORD-1004?",
        help="Message/question to send to the agent (default: 'Where is ORD-1004?').",
    )
    parser.add_argument(
        "--resource",
        default=DEFAULT_RESOURCE,
        help="Full resource name of the deployed Reasoning Engine (defaults to AGENT_RESOURCE_NAME in .env).",
    )
    parser.add_argument(
        "--project",
        default=DEFAULT_PROJECT,
        help="Google Cloud project ID (defaults to GOOGLE_CLOUD_PROJECT in .env).",
    )
    parser.add_argument(
        "--location",
        default=DEFAULT_LOCATION,
        help="Google Cloud location (defaults to GOOGLE_CLOUD_LOCATION in .env or 'us-central1').",
    )
    parser.add_argument(
        "--user-id",
        default="test_user",
        help="User ID for the session (default: 'test_user').",
    )
    parser.add_argument(
        "--session-id",
        default=None,
        help="Session ID to continue an existing conversation (default: creates new session).",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print raw event payloads returned by the runtime.",
    )
    return parser.parse_args()


def print_event_content(event, verbose: bool = False) -> tuple[bool, bool]:
    """Extract and print text chunks from an ADK event structure.

    Returns:
        tuple[bool, bool]: (has_text, has_error)
    """
    if verbose:
        print(f"\n[EVENT] {event}")

    has_text = False
    has_error = False

    if isinstance(event, dict):
        # 1. Check for remote runtime errors
        if "errorMessage" in event or "errorCode" in event or (
            event.get("code") and event.get("code") != 200
        ):
            code = event.get("errorCode") or event.get("code")
            msg = event.get("errorMessage") or event.get("message", "Unknown error")
            print(f"\n[REMOTE ERROR {code}]: {msg}", file=sys.stderr)
            return False, True

        # 2. Extract content parts
        content = event.get("content")
        if isinstance(content, dict):
            parts = content.get("parts", [])
            for part in parts:
                if isinstance(part, dict) and "text" in part and part["text"]:
                    print(part["text"], end="", flush=True)
                    has_text = True
        elif "text" in event and event["text"]:
            print(event["text"], end="", flush=True)
            has_text = True

    elif hasattr(event, "content"):
        content = getattr(event, "content", None)
        if content and hasattr(content, "parts"):
            for part in content.parts:
                if hasattr(part, "text") and part.text:
                    print(part.text, end="", flush=True)
                    has_text = True
        elif hasattr(event, "text") and event.text:
            print(event.text, end="", flush=True)
            has_text = True

    elif isinstance(event, str):
        print(event, end="", flush=True)
        has_text = True

    return has_text, has_error



def main():
    args = parse_args()

    # Validate that sensitive cloud identifiers are provided via .env or CLI flags
    if not args.resource:
        print(
            "[ERROR] No Agent Runtime resource specified.\n"
            "Please set AGENT_RESOURCE_NAME in your .env file or pass --resource.",
            file=sys.stderr,
        )
        sys.exit(1)

    if not args.project:
        print(
            "[ERROR] No Google Cloud project specified.\n"
            "Please set GOOGLE_CLOUD_PROJECT in your .env file or pass --project.",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        import agentplatform
    except ImportError:
        print(
            "[ERROR] Missing agentplatform SDK.\n"
            "Run: pip install 'google-cloud-agentplatform[adk,runtimes]'",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"Connecting to deployed Agent Runtime: {args.resource}...")
    client = agentplatform.Client(project=args.project, location=args.location)

    # Note: client.runtimes.get requires keyword argument name=
    try:
        agent = client.runtimes.get(name=args.resource)
    except Exception as exc:
        print(f"\n[ERROR] Failed to fetch agent runtime: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"\nUser: {args.message}")
    print("-" * 50)
    print("Agent: ", end="", flush=True)

    try:
        # AdkApp on Agent Runtime registers stream_query
        if hasattr(agent, "stream_query"):
            kwargs = {"message": args.message, "user_id": args.user_id}
            if args.session_id:
                kwargs["session_id"] = args.session_id

            received_any = False
            encountered_error = False
            for event in agent.stream_query(**kwargs):
                has_text, has_error = print_event_content(event, verbose=args.verbose)
                if has_text:
                    received_any = True
                if has_error:
                    encountered_error = True

            if not received_any and not encountered_error and not args.verbose:
                print("(No response content received)")
            print("\n")

        elif hasattr(agent, "query"):
            response = agent.query(message=args.message)
            print(f"\n{response}\n")
        else:
            methods = [m for m in dir(agent) if not m.startswith("_")]
            print(
                f"\n[ERROR] Neither 'stream_query' nor 'query' method found on remote agent.\n"
                f"Available methods: {methods}",
                file=sys.stderr,
            )
            sys.exit(1)

    except Exception as exc:
        print(f"\n[ERROR] Query failed: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
