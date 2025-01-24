# tools/question_tool.py

import os
from llama_index.core.tools import FunctionTool
from llama_index.llms.ollama import Ollama
from prompts import general_context, question_prompt_template
from tools.parse_utils import parse_multilevel_list
from tools.log_utils import write_llm_log

VERBOSE = True
ollama_for_questions = Ollama(model="llama3.1", request_timeout=180.0)

def question_tool_func(params: dict) -> dict:
    user_objective = params.get("user_objective", "")

    steps_path = os.path.join("data", "steps.txt")
    if not os.path.exists(steps_path):
        return {"error": "steps.txt not found."}

    with open(steps_path, "r", encoding="utf-8") as f:
        steps_lines = [l.strip() for l in f if l.strip()]

    conversation_path = os.path.join("data", "conversation_context.txt")
    if not os.path.exists(conversation_path):
        return {"error": "conversation_context.txt not found."}

    step_index = 1
    for step_desc in steps_lines:

        # 重新讀取 conversation_context (確保取得最新追加內容)
        with open(conversation_path, "r", encoding="utf-8") as cf:
            conversation_context = cf.read()

        if VERBOSE:
            print(f"[question_tool] Generating questions for step {step_index} => {step_desc}")

        prompt = (
            f"{general_context}\n"
            + question_prompt_template.format(
                conversation_context=conversation_context,
                user_objective=user_objective,
                step_description=step_desc
            )
        )

        if VERBOSE:
            print("[question_tool] prompt to LLM:")
            print(prompt)
            print("------------------------------------")

        try:
            resp = ollama_for_questions.complete(prompt)
            questions_text = str(resp)
        except Exception as e:
            return {"error": f"Failed to generate questions for step {step_index}: {e}"}

        if VERBOSE:
            print("[question_tool] LLM response:")
            print(questions_text)
            print("====================================")

        # 檔名: step{step_index}_to_question_LLM.txt
        filename = f"step{step_index}_to_question_LLM.txt"
        write_llm_log(filename, prompt, questions_text)

        parsed_questions = parse_multilevel_list(questions_text)

        question_file = os.path.join("data", f"step{step_index}_questions.txt")
        with open(question_file, "w", encoding="utf-8") as qf:
            for line in parsed_questions:
                qf.write(line + "\n")

        # 追加到 conversation_context.txt
        with open(conversation_path, "a", encoding="utf-8") as cf:
            cf.write(f"[Step {step_index} Socratic Questions]\n")
            for line in parsed_questions:
                cf.write(line + "\n")
            cf.write("\n")

        step_index += 1

    msg = f"[question_tool] Generated questions for {step_index-1} steps."
    if VERBOSE:
        print(msg)
    return {"message": msg}

question_tool = FunctionTool.from_defaults(
    fn=question_tool_func,
    name="question_tool",
    description="Generate Socratic questions for each step, update conversation_context"
)
