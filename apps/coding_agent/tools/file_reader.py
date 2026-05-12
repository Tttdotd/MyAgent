from pathlib import Path
from typing import Any, Dict, List

from hello_agents import Tool, ToolParameter


class FileReaderTool(Tool):
    """读文件工具"""

    def __init__(
        self,
        name: str = "file_reader",
        description: str = "字符串文件读取工具. 当你需要读取文件内容并加以理解的时候, 请调用此工具.",
        root_dir: str = ".",
    ):
        super().__init__(name, description)
        self.root_dir = Path(root_dir).resolve()

    def run(self, parameters: Dict[str, Any]) -> str:
        path = parameters.get("path")
        if not path:
            return "错误：文件读取路径为空"

        target = (self.root_dir / path).resolve()
        if target != self.root_dir and self.root_dir not in target.parents:
            return f"错误：不允许读取工作目录以外的文件: {path}"
        if not target.exists():
            return f"错误：文件不存在: {path}"
        if not target.is_file():
            return f"错误：目标不是文件: {path}"

        try:
            return target.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return f"错误：文件不是有效的UTF-8文本文件: {path}"
        except Exception as e:
            return f"错误：文件读取失败: {path}，原因: {e}"

    def get_parameters(self) -> List[ToolParameter]:
        """获取参数定义"""
        return [
            # 需要读取的文件路径
            ToolParameter(
                name="path",
                type="string",
                description="要读取的文件路径",
                required=True,
            )
        ]
