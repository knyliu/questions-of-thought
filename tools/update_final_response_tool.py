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
        + f"\n\n先前預計以以下內容回覆給用戶:\n{current_final_response}\n，以上是先前預計以以下內容回覆給用戶。"
        + f"\n\n現在開始修改以上內容。現在這個討論及修改內容是中間過程，接下來你生成的回覆即是用戶第一次看到基於他提出的目標的回覆。\n你需要將先前預計的回覆內容與新的討論資訊整合，不要刪除先前已存在的有效程式碼和功能特徵或結論，\n而是將新的功能特和程式碼補充、加入進去。\n讓新的功能特徵都被加入至完整程式碼中。\n你可以讓回覆的字數盡可能多，來回覆最完整的程式碼內容。\n讓用戶看到的回覆是最完整最豐富且正確的。\n絕對不可以移除已經存在的功能特徵程式碼，回答時的程式碼都需要保持舊有的功能，並疊加上新的功能程式，所以程式碼會越來越完善。\n生成的程式碼絕對不能使用註解省略，不能略過任何程式碼，使用者只會收到這一次的程式碼，要讓使用者看得到所有程式碼，並可以直接使用，所以不能省略或略過任何程式碼，請確保程式碼正確且連貫。\n\n現在，開始回覆給用戶，用戶是第一次看到基於他提出的目標的回覆。"
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
