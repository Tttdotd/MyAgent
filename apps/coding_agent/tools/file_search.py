from pathlib import Path
from typing import List
from hello_agents import Tool, ToolParameter
class FileSearchTool(Tool):
    """文件搜索工具, 在当前目录下搜索目标文件"""

    def __init__(self, root_dir = "."):
        name = "file_search"
        description = "文件搜索工具. 当你只知道想要操作的文件或文件夹的名称或名称中的关键词时, 可以调用此工具在当前目录进行搜索, 以获取要操作文件或文件夹的完整路径."
        super().__init__(name, description)
        self.root_dir = Path(root_dir).resolve()
        self.ignore_dirs = {
            ".git",
            "__pycache__",
            ".pytest_cache",
            ".mypy_cache",
            ".venv",
            "venv",
            "node_modules",
            "dist",
            "build"
        }

    def run(self, parameters):
        path = parameters.get("path", str(self.root_dir))
        query = parameters.get("query")

        if not query:
            return f"FileSearch失败: file_search 的 query参数不能为空"

        # 构建目标路径
        target = (self.root_dir / path).resolve()
        
        matches = []
        query = str(query).strip().lower()
        try:
            # 构造目标搜索路径
            for path in target.rglob("*"):
                # 如果是需要忽略的文件, 直接跳过
                if self._should_ignore(path):
                    continue

                relative_path = path.relative_to(self.root_dir)
                relative_text = str(relative_path).replace("\\", "/")

                # 如果为文件夹, 补一个"/"
                if not path.is_file():
                    relative_text += "/"

                filename = path.name.lower()
                if query in filename:
                    matches.append(relative_text)

            if not matches:
                return f"FileSearch失败: 未在本目录下找到匹配文件: {query}"
            
            result = [f"找到 {len(matches)} 个匹配文件:"]
            result.extend(matches)
            return "\n".join(result)
        except Exception as e:
            return f"FileSearch失败: 文件搜索失败, 原因: {e}"

    def get_parameters(self) -> List[ToolParameter]:
        """获取工具参数定义"""
        return [
            ToolParameter(
                name="path",
                type="string",
                description="搜索路径. 表示在哪一路径下进行文件搜索, 请使用相对于当前工作目录的相对路径.",
                required=False,
                default='.'
            ),
            ToolParameter(
                name="query",
                type="string",
                description="进行文件搜索时使用的文件或文件夹的名称或名称中的关键字",
                required=True,
            )
        ]
    
    def _should_ignore(self, path: Path) -> bool:
        return any(part in self.ignore_dirs for part in path.parts)