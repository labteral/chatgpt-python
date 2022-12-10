from typing import Any
from rich.markdown import Markdown
from rich.markdown import CodeBlock
from rich.console import Console, RenderResult, ConsoleOptions
from rich.syntax import Syntax
from rich.panel import Panel
from rich import box


class CustomCodeBlock(CodeBlock):
    """A code block with syntax highlighting."""

    style_name = "markdown.code_block"

    @classmethod
    def create(cls, markdown: "Markdown", node: Any) -> "CodeBlock":
        node_info = node.info or ""
        lexer_name = node_info.partition(" ")[0]
        return cls(lexer_name or "default", markdown.code_theme)

    def __init__(self, lexer_name: str, theme: str) -> None:
        self.lexer_name = lexer_name
        self.theme = theme

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        code = str(self.text).rstrip()
        syntax = Panel(
            Syntax(code,
                   "python",
                   theme="gruvbox-dark",
                   #    background_color="default",
                   word_wrap=True,
                   padding=2),
            border_style="none",
            box=box.SIMPLE,
            padding=0
        )
        yield syntax