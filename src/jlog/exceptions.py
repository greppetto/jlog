class CLIError(Exception):
    def __init__(self, message):
        super().__init__(f"[CLI] {message}")


class InvalidNameError(CLIError):
    def __init__(self):
        super().__init__("InvalidIDError: Invalid day name")
