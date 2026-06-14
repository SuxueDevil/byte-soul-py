"""ReAct 输出解析器"""
import re


def parse_action(text: str) -> tuple[str, str] | None:
    """
    从 LLM 输出中解析 Action 和 Action Input。
    @param text: LLM 输出文本
    @return: (action, action_input) 或 None
    """
    # 一、匹配 Action
    action_match = re.search(r"Action:\s*(.+?)(?:\n|$)", text)
    input_match = re.search(r"Action Input:\s*(.+?)(?:\n|$)", text)

    if action_match and input_match:
        action = action_match.group(1).strip()
        action_input = input_match.group(1).strip()
        return action, action_input
    return None


def parse_final_answer(text: str) -> str | None:
    """
    从 LLM 输出中解析 Final Answer。
    @param text: LLM 输出文本
    @return: 最终答案或 None
    """
    # 一、匹配 Final Answer
    match = re.search(r"Final Answer:\s*(.+)", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None
