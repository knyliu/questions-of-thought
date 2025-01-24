# tools/log_utils.py

import os

def write_llm_log(filename: str, prompt: str, response: str):
    """
    將 prompt 與 response 寫入 llm_log/<filename>.
    檔名例: steps_LLM.txt, step1_to_question_LLM.txt, step1_question2_LLM.txt, ...
    """
    os.makedirs("llm_log", exist_ok=True)
    filepath = os.path.join("llm_log", filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("===== PROMPT =====\n")
        f.write(prompt)
        f.write("\n\n===== RESPONSE =====\n")
        f.write(response)
