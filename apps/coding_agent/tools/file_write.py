from typing import Dict, Any
from pathlib import Path
from typing import List
from hello_agents import Tool, ToolParameter, ToolException

class FileWriteTool(Tool):
    def __init__(self, root_dir="."):
        super().__init__(
            name="file_writer",
            description="字符串文件写入工具. 当你需要将一段字符串内容写入文件的时候, 请调用此工具."
        )
        self.root_dir = Path(root_dir).resolve()
    
    def run(self, parameters: Dict[str, Any]) -> str:
        path = parameters.get("path")
        content = parameters.get("content")
        overwrite = parameters.get("overwrite", False)

        if not path:
            return "FileWrite失败：文件写入路径为空"
        if content is None:
            return "FileWrite失败：文件写入内容为None"
        # 检验overwrite是否为bool类型
        if not isinstance(overwrite, bool):
            return "FileWrite失败：传入的overwrite参数不是bool类型"
        
        target = (self.root_dir / path).resolve()
        if target != self.root_dir and self.root_dir not in target.parents:
            return f"FileWrite失败：不允许写入工作目录以外的文件: {path}"

        if not overwrite and target.exists():
            return f"FileWrite失败：文件已存在，不允许覆盖: {path}"

        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            return f"FileWrite成功：文件写入成功: {target}"
        except Exception as e:
            return f"FileWrite失败：文件写入失败: {path}，原因: {e}"
    
    def get_parameters(self) -> List[ToolParameter]:
        """获取工具参数定义"""
        return [
            ToolParameter(
                name="path",
                type="string",
                description="要写入的文件路径. 请使用相对于工作目录的路径.",
            ),
            ToolParameter(
                name="content",
                type="string",
                description="要写入文件的字符串内容"
            ),
            ToolParameter(
                name="overwrite",
                type="boolean",
                description="是否允许覆盖已存在的文件, 若为True, 可以覆盖",
                required=False,
                default=True
            ),
        ]
