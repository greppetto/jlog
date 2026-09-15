class CLIError(Exception):
    def __init__(self, message: str):
        super().__init__(f"[CLI] {message}")


class InvalidNameError(CLIError):
    def __init__(self):
        super().__init__("InvalidIDError: invalid day name")


class FormatterError(ValueError):
    def __init__(self, message: str):
        super().__init__(f"[Formatter] {message}")


class FrontmatterError(FormatterError):
    """
    Raised when a markdown document contains invalid frontmatter structure.
    """


class MarkdownError(FormatterError):
    """
    Raised when a markdown document contains invalid body structure.
    """
