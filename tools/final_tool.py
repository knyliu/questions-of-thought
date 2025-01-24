# tools/final_tool.py

import os
from llama_index.core.tools import FunctionTool
from llama_index.llms.ollama import Ollama
from prompts import general_context, final_prompt_template

ollama_for_final = Ollama(model="llama3.1", request_timeout=180.0)

def final_tool_func(params: dict) -> dict:
    user_objective = params.get("user_objective", "")

    conversation_path = os.path.join("data", "conversation_context.txt")
    if not os.path.exists(conversation_path):
        return {"error": "conversation_context.txt not found."}

    with open(conversation_path, "r", encoding="utf-8") as cf:
        conversation_context = cf.read()

    prompt = (
        f"{general_context}\n"
        + final_prompt_template.format(
            conversation_context=conversation_context,
            user_objective=user_objective
        )
    )
    try:
        resp = ollama_for_final.complete(prompt)
        final_text = str(resp)
    except Exception as e:
        return {"error": f"Failed to generate final answer: {e}"}

    os.makedirs("data", exist_ok=True)
    final_path = os.path.join("data", "final_answer.txt")
    try:
        with open(final_path, "w", encoding="utf-8") as f:
            f.write(final_text)
    except Exception as e:
        return {"error": f"Failed to write final_answer.txt: {e}"}

    return {
        "message": "[final_tool] Final answer generated.",
        "final_answer": final_text
    }

final_tool = FunctionTool.from_defaults(
    fn=final_tool_func,
    name="final_tool",
    description="Aggregate conversation_context, produce final_answer.txt with a complete integrated solution"
)
