import os

from google.adk.models.llm_response import LlmResponse
from google.genai import types

BLOCKED_MESSAGE = (
    "This prompt was blocked by Model Armor and was not sent to the model."
)


def model_armor_config() -> types.GenerateContentConfig:
    return types.GenerateContentConfig(
        model_armor_config=types.ModelArmorConfig(
            prompt_template_name=os.environ["MODEL_ARMOR_INPUT_TEMPLATE"],
            response_template_name=os.environ["MODEL_ARMOR_OUTPUT_TEMPLATE"],
        )
    )


def explain_model_armor_block(callback_context, llm_response) -> LlmResponse | None:
    """Replace a Model Armor error with text the Playground can display."""
    del callback_context
    if getattr(llm_response, "error_code", None) != "MODEL_ARMOR":
        return None

    detail = (getattr(llm_response, "error_message", None) or "").strip()
    text = f"{BLOCKED_MESSAGE} {detail}" if detail else BLOCKED_MESSAGE
    return LlmResponse(
        content=types.Content(
            role="model",
            parts=[types.Part(text=text)],
        )
    )
