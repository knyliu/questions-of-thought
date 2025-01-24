# tools/steps_tool.py

import os
from llama_index.core.tools import FunctionTool
from llama_index.llms.ollama import Ollama
from prompts import general_context, steps_prompt_template
from tools.parse_utils import parse_multilevel_list
from tools.log_utils import write_llm_log

VERBOSE = True
ollama_for_steps = Ollama(model="llama3.1", request_timeout=180.0)

def steps_tool_func(user_objective: str) -> dict:
    if VERBOSE:
        print("========== 剖析步驟成任務 ==========")
        print("[steps_tool] user_objective =", user_objective)

    os.makedirs("data", exist_ok=True)

    conversation_path = os.path.join("data", "conversation_context.txt")
    with open(conversation_path, "w", encoding="utf-8") as f:
        f.write(f"[User Objective]\n{user_objective}\n\n")

    prompt = f"{general_context}\n" + steps_prompt_template.format(user_objective=user_objective)

    if VERBOSE:
        print("[steps_tool] Prompt to LLM:")
        print(prompt)
        print("------------------------------------")

    try:
        response = ollama_for_steps.complete(prompt)
        steps_text = str(response)
    except Exception as e:
        return {"error": f"Failed to get steps: {e}"}

    if VERBOSE:
        print("[steps_tool] LLM response:")
        print(steps_text)
        print("====================================")

    # 寫log -> steps_LLM.txt
    write_llm_log("steps_LLM.txt", prompt, steps_text)

    parsed_steps = parse_multilevel_list(steps_text)

    steps_path = os.path.join("data", "steps.txt")
    try:
        with open(steps_path, "w", encoding="utf-8") as f:
            for s in parsed_steps:
                f.write(s + "\n")
    except Exception as e:
        return {"error": f"Failed to write steps: {e}"}

    with open(conversation_path, "a", encoding="utf-8") as f:
        f.write("[Generated Steps]\n")
        f.write(steps_text + "\n\n")

    msg = f"[steps_tool] Wrote {len(parsed_steps)} steps to steps.txt."
    if VERBOSE:
        print(msg)

    return {
        "steps_count": len(parsed_steps),
        "message": msg
    }

steps_tool = FunctionTool.from_defaults(
    fn=steps_tool_func,
    name="steps_tool",
    description="Parse user objective into multiple steps, update conversation_context, and save steps.txt"
)
