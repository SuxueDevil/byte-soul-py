"""工具基类"""
from abc import ABC, abstractmethod


class BaseTool(ABC):
    """工具基类：定义工具接口"""

    name: str = ""
    description: str = ""

    @abstractmethod
    def execute(self, **kwargs) -> str:
        """
        执行工具。
        @param kwargs: 工具参数
        @return: 执行结果
        """
        pass

    def to_prompt(self) -> str:
        """
        生成工具描述，用于 Prompt。
        @return: 工具描述字符串
        """
        return f"- {self.name}: {self.description}"
