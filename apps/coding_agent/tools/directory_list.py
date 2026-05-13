from pathlib import Path
from typing import Any, Dict, List

from hello_agents import Tool, ToolParameter


class DirectoryListTool(Tool):
    """查看指定文件夹下的文件列表"""

    def __init__(self, root_dir: str = "."):
        name = "directory_list"
        description = "文件夹列表工具. 当你需要查看某个目录下有哪些文件和文件夹, 以决定下一步读取或修改哪个文件时, 请调用此工具."
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
            "build",
        }

    def run(self, parameters: Dict[str, Any]) -> str:
        path = parameters.get("path", str(self.root_dir))
        if not path:
            return "DirectoryList失败：目标文件夹路径不能为空"

        target = (self.root_dir / path).resolve()
        if not target.exists():
            return f"DirectoryList失败：文件夹不存在: {path}"
        if not target.is_dir():
            return f"DirectoryList失败：目标不是文件夹: {path}"

        try:
            entries = self._collect_entries(target)
            if not entries:
                return f"DirectoryList成功：文件夹为空: {self._format_path(target.relative_to(self.root_dir))}"

            header_path = self._format_path(target.relative_to(self.root_dir))
            result = [f"DirectoryList成功：文件夹列表: {header_path}"]
            for entry in entries:
                relative_path = self._format_path(entry.relative_to(target))
                marker = "[D]" if entry.is_dir() else "[F]"
                if entry.is_dir():
                    relative_path = f"{relative_path}/"
                result.append(f"{marker} {relative_path}")

            return "\n".join(result)
        except Exception as e:
            return f"DirectoryList失败：文件夹列表读取失败: {path}，原因: {e}"

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="path",
                type="string",
                description="要查看的文件夹路径. 请使用相对于工作目录的路径.",
                required=False,
                default=str(self.root_dir),
            )
        ]

    def _collect_entries(self, target: Path) -> List[Path]:
        candidates = target.iterdir()
        entries = [path for path in candidates if not self._should_ignore(path)]
        return sorted(entries, key=lambda item: (not item.is_dir(), str(item).lower()))

    def _should_ignore(self, path: Path) -> bool:
        return any(part in self.ignore_dirs for part in path.parts)

    def _format_path(self, path: Path) -> str:
        text = str(path).replace("\\", "/")
        return "." if text == "." else text
