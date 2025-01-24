# update_final_response_tool.py

import os
from llama_index.core.tools import FunctionTool
from llama_index.llms.ollama import Ollama
from prompts import general_context, final_response_update_prompt_template
from tools.log_utils import write_llm_log

VERBOSE = True
ollama_for_update = Ollama(model="llama3.1", request_timeout=180.0)

def update_final_response_tool_func(params: dict) -> dict:
    user_objective = params.get("user_objective", "")
    steps_list = params.get("steps_list", "")
    step_description = params.get("step_description", "")
    question_text = params.get("question_text", "")
    answer_text = params.get("answer_text", "")
    step_idx = params.get("step_idx", 0)
    question_idx = params.get("question_idx", 0)

    if VERBOSE:
        print("[update_final_response_tool] user_objective:", user_objective)
        print("[update_final_response_tool] steps_list:", steps_list)
        print("[update_final_response_tool] step_description:", step_description)
        print("[update_final_response_tool] question:", question_text)
        print("[update_final_response_tool] answer:", answer_text)
        print("[update_final_response_tool] step_idx:", step_idx, "question_idx:", question_idx)

    os.makedirs("data", exist_ok=True)
    
    final_response_path = os.path.join("data", "final_response.txt")
    if not os.path.exists(final_response_path):
        with open(final_response_path, "w", encoding="utf-8") as f:
            f.write("")

    with open(final_response_path, "r", encoding="utf-8") as f:
        current_final_response = f.read()

    if VERBOSE:
        print("[update_final_response_tool] old final_response:")
        print(current_final_response)
        print("--------------------------------------------------")

    prompt = (
        f"{general_context}\n"
        + final_response_update_prompt_template.format(
            user_objective=user_objective,
            steps_list=steps_list,
            step_description=step_description,
            question_text=question_text,
            answer_text=answer_text
        )
        + f"\n\n[當前最終回覆 (old)]:\n{current_final_response}\n"
        + f"\n\n現在開始更新舊的要回覆給用戶的內容，這是一個修正回覆給用戶的內容的過程。\n你需要將先前的最終回覆內容 (可能有程式碼、結論) 與新的資訊整合，不要刪除先前已存在的有效程式碼或結論，\n而是將新的想法或程式碼補充、修正進去。\n讓新的功能也都被整理進去完整程式碼中。\n你可以讓回覆的token盡可能多，來回覆最完整的內容。\n讓用戶看到的回覆是最完整最豐富且正確的。\n絕對不可以移除已經存在的功能程式碼，回答時的程式碼都需要保持舊有的功能，並疊加上新的功能程式，所以程式碼會越來越完善。\n"
    )

    if VERBOSE:
        print("[update_final_response_tool] final prompt to LLM =")
        print(prompt)
        print("--------------------------------------------------")

    try:
        resp = ollama_for_update.complete(prompt)
        updated_final_response = str(resp)
    except Exception as e:
        return {"error": f"Ollama generate failed: {str(e)}"}

    if VERBOSE:
        print("[update_final_response_tool] LLM response (new final_response):")
        print(updated_final_response)
        print("==================================================")

    # 寫log => update_based_on_step{i}_question{j}_LLM.txt
    if step_idx and question_idx:
        filename = f"update_based_on_step{step_idx}_question{question_idx}_LLM.txt"
        write_llm_log(filename, prompt, updated_final_response)

    try:
        with open(final_response_path, "w", encoding="utf-8") as f:
            f.write(updated_final_response)
    except Exception as e:
        return {"error": f"Failed to write final_response.txt: {str(e)}"}

    return {
        "message": "[update_final_response_tool] final_response updated",
        "updated_final_response": updated_final_response
    }

update_final_response_tool = FunctionTool.from_defaults(
    fn=update_final_response_tool_func,
    name="update_final_response_tool",
    description="Update final_response.txt with user_objective, steps_list, step_description, question_text, and answer_text"
)
