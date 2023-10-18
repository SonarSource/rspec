# Validate the asciidoc environment directives in the given file.
# Errors are printed to the standard error stream.
#
# "ifdef" commands has to start the line without any leading spaces,
# as per asciidoc format.
#
# Only one form is allowed:
# ifdef::env-github,rspecator-view[]
#
# The closing command is:
# endif::env-github,rspecator-view[]
#
# It must be in the same file.
# Only one such environment is allowed per file.

from pathlib import Path
import sys


VALID_IFDEF = "ifdef::env-github,rspecator-view[]"
VALID_ENDIF = "endif::env-github,rspecator-view[]"


class Checker:
    def __init__(self, file: Path):
        assert file.exists()
        assert file.is_file()

        self.file = file
        self.is_env_open = False
        self.has_env = False

    def process(self):
        content = self.file.read_text(encoding="utf-8")
        lines = content.splitlines(keepends=False)
        for line_index, line in enumerate(lines):
            if line.startswith("ifdef::"):
                self._process_open(line_index + 1, line)
            if line.startswith("endif::"):
                self._process_close(line_index + 1, line)
        if self.is_env_open:
            self._on_error(len(line), "The ifdef command is not closed.")

    def _process_open(self, line_number: int, line: str):
        if self.has_env:
            self._on_error(line_number, "Only one ifdef command is allowed per file.")

        self.has_env = True
        self.is_env_open = True

        # IDEs should be configured to properly display the description,
        # not the other way around.
        # "env-vscode" was used in the passed. Instead, user should be able to
        # toggle the rspecator view based on their needs. Help these users migrate.
        if "vscode" in line:
            self._on_error(
                line_number,
                "Configure VS Code to display rspecator-view by setting the asciidoctor attribute.",
            )

        if line != VALID_IFDEF:
            self._on_error(
                line_number,
                f'Incorrect asciidoc environment. "{VALID_IFDEF}" should be used instead.',
            )

    def _process_close(self, line_number: int, line: str):
        if not self.is_env_open:
            self._on_error(line_number, "Unexpected endif command.")

        self.is_env_open = False

        if line != VALID_ENDIF:
            self._on_error(
                line_number,
                f'Incorrect endif command. "{VALID_ENDIF}" should be used instead.',
            )

    def _on_error(self, line_number: int, message: str):
        sys.exit(f"{self.file}:{line_number} {message}")


def main():
    assert len(sys.argv) == 2
    file = Path(sys.argv[1])
    Checker(file).process()


if __name__ == "__main__":
    main()
