from pathlib import Path
from typing import Any, Dict, List

from hello_agents import Tool, ToolParameter


class DirectoryCreateTool(Tool):
    """创建文件夹tool"""

    def __init__(self, root_dir: str = "."):
        name = "directory_create"
        description = "文件夹创建工具. 当需要对项目进行结构化组织时, 往往需要使用文件夹创建能力. 需要时请调用此工具来让项目结构更可读, 更易于维护."
        super().__init__(name, description)
        self.root_dir = Path(root_dir).resolve()

    def run(self, parameters: Dict[str, Any]) -> str:
        path = parameters.get("path", str(self.root_dir))
        name = parameters.get("name")

        if not name:
            return f"DirectoryCreate失败：文件夹名称为空, 无法在{path}路径下创建文件夹"

        target = (self.root_dir / path / name).resolve()
        if target != self.root_dir and self.root_dir not in target.parents:
            return f"DirectoryCreate失败：不允许创建工作目录以外的文件夹: {path}"

        if target.is_dir():
            return f"DirectoryCreate失败：文件夹已存在, 无需重复创建: {target}"

        try:
            target.mkdir(parents=True, exist_ok=False)
            return f"DirectoryCreate成功：文件夹创建成功: {target}"
        except Exception as e:
            return f"DirectoryCreate失败：文件夹创建失败: {path}，原因: {e}"

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="path",
                type="string",
                description="文件夹创建位置. 用于表示在哪个路径下创建文件夹. 请使用相对于当前工作目录的相对路径.",
                required=True,
                default=str(self.root_dir) # 默认创建位置为根目录"."
            ),
            ToolParameter(
                name="name",
                type="string",
                description="要创建的文件夹名称.",
                required=True
            )
        ]
