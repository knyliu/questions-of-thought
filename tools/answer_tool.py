# tools/answer_tool.py

import os
from llama_index.core.tools import FunctionTool
from llama_index.llms.ollama import Ollama

from prompts import general_context, answer_prompt_template
from tools.update_final_response_tool import update_final_response_tool_func
from tools.log_utils import write_llm_log  # 用於記錄 LLM
from tools.parse_utils import parse_multilevel_list  # 如果回答也需要解析, 可視需求

VERBOSE = True
ollama_for_answers = Ollama(model="llama3.1", request_timeout=120.0)

def extract_step_number(filename: str) -> int:
    """
    從檔名中取出stepN的數字,
    比如 "step10_questions.txt" => 10
         "step2_questions.txt"  => 2
    """
    # "step10_questions.txt" -> "10_questions.txt" -> split('_')[0] -> "10"
    base = filename.replace("step", "").replace("_questions.txt", "")
    try:
        return int(base)
    except:
        return 0  # 若失敗就回傳0

def answer_tool_func(params: dict) -> dict:
    """
    1. 按照數字順序處理 stepN_questions.txt
    2. 讀取 conversation_context.txt, 將其帶入 Prompt
    3. 回答完之後, 將回答寫回 conversation_context.txt
    4. 把 prompt/response 寫到 llm_log/<檔名>.txt
    """
    user_objective = params.get("user_objective", "")

    # 讀 steps.txt => steps_list
    steps_list_str = ""
    steps_lines = []
    steps_path = os.path.join("data", "steps.txt")
    if os.path.exists(steps_path):
        with open(steps_path, "r", encoding="utf-8") as sf:
            steps_lines = [l.strip() for l in sf if l.strip()]
        steps_list_str = "\n".join(steps_lines)

    # 尋找 stepN_questions.txt
    all_files = os.listdir("data")
    qfiles = [f for f in all_files if f.startswith("step") and f.endswith("_questions.txt")]

    # 2. 修正排序(數字順序)
    qfiles.sort(key=extract_step_number)

    if not qfiles:
        return {"error": "No step*_questions.txt found in data/"}

    total_answers = 0

    # conversation_context.txt
    conversation_path = os.path.join("data", "conversation_context.txt")

    for qfile in qfiles:
        step_idx = extract_step_number(qfile)
        # 取得 step_description
        step_description = ""
        if 1 <= step_idx <= len(steps_lines):
            step_description = steps_lines[step_idx - 1]

        questions_path = os.path.join("data", qfile)
        answers_path = os.path.join("data", f"step{step_idx}_answers.txt")

        # 讀 question lines
        with open(questions_path, "r", encoding="utf-8") as f:
            questions_lines = [line.strip() for line in f if line.strip()]

        answers_collected = []

        # 針對每個問題回答
        for j, question_text in enumerate(questions_lines, start=1):
            if VERBOSE:
                print(f"[answer_tool] step {step_idx}, question #{j}: {question_text}")

            # 重新讀取 conversation_context
            if os.path.exists(conversation_path):
                with open(conversation_path, "r", encoding="utf-8") as cf:
                    conversation_context = cf.read()
            else:
                conversation_context = ""

            # 組合 Prompt
            prompt = (
                f"{general_context}\n"
                + answer_prompt_template.format(
                    conversation_context=conversation_context,
                    user_objective=user_objective,
                    question=question_text
                )
            )

            if VERBOSE:
                print("===== Prompt to LLM =====")
                print(prompt)
                print("-------------------------")

            try:
                resp = ollama_for_answers.complete(prompt)
                answer_text = str(resp)

                if VERBOSE:
                    print("===== LLM response =====")
                    print(answer_text)
                    print("==================================================")

                answers_collected.append((question_text, answer_text))
                total_answers += 1

                # 紀錄 LLM呼叫 => step{i}_question{j}_LLM.txt
                filename = f"step{step_idx}_question{j}_LLM.txt"
                write_llm_log(filename, prompt, answer_text)

                # 3. 回答後, 將回答寫入 conversation_context.txt
                with open(conversation_path, "a", encoding="utf-8") as cf:
                    cf.write(f"[step {step_idx} question {j} Q&A]\n")
                    cf.write(f"Q: {question_text}\nA: {answer_text}\n\n")

                # 4. 更新 final_response
                update_result = update_final_response_tool_func({
                    "user_objective": user_objective,
                    "steps_list": steps_list_str,
                    "step_description": step_description,
                    "question_text": question_text,
                    "answer_text": answer_text,
                    "step_idx": step_idx,
                    "question_idx": j
                })
                if "error" in update_result:
                    print("[answer_tool] Error in update_final_response_tool:", update_result["error"])
                else:
                    if VERBOSE:
                        print("[answer_tool] final_response updated after Q&A.")
                        print("========== Updated final_response ==========")
                        print(update_result["updated_final_response"])
                        print("============================================\n")

            except Exception as e:
                error_msg = f"Error answering question '{question_text}': {e}"
                answers_collected.append((question_text, error_msg))
                if VERBOSE:
                    print("[answer_tool] ", error_msg)

        # 寫入 stepN_answers.txt
        with open(answers_path, "w", encoding="utf-8") as af:
            for (q, a) in answers_collected:
                af.write(f"Q: {q}\nA: {a}\n\n")

    msg = f"[answer_tool] Done. Processed {len(qfiles)} question files, total {total_answers} answers."
    if VERBOSE:
        print(msg)

    return {"message": msg}

answer_tool = FunctionTool.from_defaults(
    fn=answer_tool_func,
    name="answer_tool",
    description="Read stepN_questions.txt, answer each question in numeric order, store to conversation_context, log LLM calls, update final_response"
)
