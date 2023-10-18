# Validate the asciidoc environment directives in the given file.
# Errors are printed to the standard output stream.
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

        self._file = file
        self._is_env_open = False
        self._has_env = False
        self._is_valid = True

    def process(self) -> bool:
        content = self._file.read_text(encoding="utf-8")
        lines = content.splitlines(keepends=False)
        for line_index, line in enumerate(lines):
            line_number = line_index + 1
            if line.startswith("ifdef::"):
                self._process_open(line_number, line)
            if line.startswith("endif::"):
                self._process_close(line_number, line)

        if self._is_env_open:
            self._on_error(len(line), "The ifdef command is not closed.")

        return self._is_valid

    def _process_open(self, line_number: int, line: str):
        if self._has_env:
            self._on_error(line_number, "Only one ifdef command is allowed per file.")

        if self._is_env_open:
            self._on_error(line_number, "The previous ifdef command was not closed.")

        self._has_env = True
        self._is_env_open = True

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
        if not self._is_env_open:
            self._on_error(line_number, "Unexpected endif command.")

        self._is_env_open = False

        if line != VALID_ENDIF:
            self._on_error(
                line_number,
                f'Incorrect endif command. "{VALID_ENDIF}" should be used instead.',
            )

    def _on_error(self, line_number: int, message: str):
        print(f"{self._file}:{line_number} {message}")
        self._is_valid = False


def main():
    assert len(sys.argv) == 2
    file = Path(sys.argv[1])
    valid = Checker(file).process()
    if not valid:
        sys.exit(1)

if __name__ == "__main__":
    main()
