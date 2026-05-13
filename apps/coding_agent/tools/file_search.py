from pathlib import Path
from typing import List
from hello_agents import Tool, ToolParameter
class FileSearchTool(Tool):
    """文件搜索工具, 在当前目录下搜索目标文件"""

    def __init__(self, root_dir = "."):
        name = "file_search"
        description = "文件搜索工具. 当你只知道想要操作的文件名称或名称中的关键词时, 可以调用此工具在当前目录进行搜索, 以获取要操作文件的完整路径."
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
        query = parameters.get("query")

        if not query:
            return f"file_search 的 query参数不能为空"
        
        matches = []
        query = str(query).strip().lower()
        try:
            for path in self.root_dir.rglob("*"):
                # 如果是需要忽略的文件, 直接跳过
                if self._should_ignore(path):
                    continue

                # # 跳过文件夹
                # if not path.is_file():
                #     continue

                relative_path = path.relative_to(self.root_dir)
                relative_text = str(relative_path).replace("\\", "/")

                filename = path.name.lower()
                if query in filename:
                    matches.append(relative_text)

            if not matches:
                return f"未在本目录下找到匹配文件: {query}"
            
            result = [f"找到 {len(matches)} 个匹配文件:"]
            result.extend(matches)
            return "\n".join(result)
        except Exception as e:
            return f"错误: 文件搜索失败, 原因: {e}"

    def get_parameters(self) -> List[ToolParameter]:
        """获取工具参数定义"""
        return [
            ToolParameter(
                name="query",
                type="string",
                description="进行文件搜索时使用的文件名称或名称中的关键字",
                required=True,
            )
        ]
    
    def _should_ignore(self, path: Path) -> bool:
        return any(part in self.ignore_dirs for part in path.parts)