# main.py

import os
from tools.steps_tool import steps_tool_func
from tools.question_tool import question_tool_func
from tools.answer_tool import answer_tool_func
# from tools.final_tool import final_tool_func

from tools.update_final_response_tool import update_final_response_tool_func

def main():
    user_objective = input("請輸入您的任務描述: ")

    # 1. 產生 steps
    steps_result = steps_tool_func(user_objective)
    if "error" in steps_result:
        print("Error in steps_tool:", steps_result["error"])
        return
    print(steps_result["message"])

    # 2. question
    q_result = question_tool_func({"user_objective": user_objective})
    if "error" in q_result:
        print("Error in question_tool:", q_result["error"])
        return
    print(q_result["message"])

    # 3. answer
    a_result = answer_tool_func({"user_objective": user_objective})
    if "error" in a_result:
        print("Error in answer_tool:", a_result["error"])
        return
    print(a_result["message"])

    # (可選) 再做一次更新 or final_tool
    # ...

if __name__ == "__main__":
    main()
