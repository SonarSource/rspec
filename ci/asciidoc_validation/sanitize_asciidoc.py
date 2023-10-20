# Validate the asciidoc environment directives in the given file(s).
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
import re


VALID_IFDEF = "ifdef::env-github,rspecator-view[]"
VALID_ENDIF = "endif::env-github,rspecator-view[]"


FORMATTING_CHARS = ['_', r'\*', r'\~', r'\#']

UNCONSTRAINED_FORMATTING = '|'.join(x + x for x in FORMATTING_CHARS)

# CONSTRAINED_FORMATTING is only a problem is there is text on one side and not the other
CONSTRAINED_FORMATTING = '|'.join(r'\w' + x + r'(\W|$)|(\W|^)' + x + r'\w' for x in FORMATTING_CHARS)

NEED_PROTECTION = re.compile(f'[^+]*({UNCONSTRAINED_FORMATTING}|{CONSTRAINED_FORMATTING})[^+]*')

CLOSE_CONSTRAINED_PASSTHROUGH = re.compile(r'\w\+\b')

BACKQUOTE = re.compile(r'((\`\`)|(?<![\\\w])(\`))')

VARIABLE_DECL = re.compile(r':\w+: ')


def inline_end(line, pos, pattern):
    max_pos = len(line)
    while pos < max_pos:
        if line[pos] == '+':
            count = 1
            while pos + count < max_pos and line[pos + count] == '+':
                count += 1
            while count > 0:
                # `+++a++` will display '+a' in case of inbalance, we try to find the biggest closing block
                if count == 1 and line[pos + count].isalnum() and not line[pos - 1].isalnum():
                    #constrained '+'. It is a passthrough only if of the form \b+\w.*\w+\b
                    close_pattern = CLOSE_CONSTRAINED_PASSTHROUGH
                else:
                    close_pattern = re.compile(r'\+' * count)
                end = close_pattern.search(line, pos + count)
                if end:
                    pos = end.end()
                    break
                count -= 1
            # if we didn't find anything, it's ok, it just means this was not a passthrough
        if line[pos] == '`' and (len(pattern) == 1 or (pos < max_pos - 1 and line[pos + 1] == '`')):
            return pos
        pos += 1
    return -1


class Checker:
    def __init__(self, file: Path):
        assert file.exists()
        assert file.is_file()

        self._file = file
        self._is_env_open = False
        self._has_env = False
        self._is_valid = True
        self._code = False

    def process(self) -> bool:
        content = self._file.read_text(encoding="utf-8")
        lines = content.splitlines(keepends=False)
        for line_index, line in enumerate(lines):
            if self._code:
                if line == '----':
                    self._code = False
                continue
            if line == '----':
                self._code = True
                continue
            line_number = line_index + 1
            if line.startswith("ifdef::"):
                self._process_open(line_number, line)
            elif line.startswith("endif::"):
                self._process_close(line_number, line)
            else:
                self._process_description(line_number, line)

        if self._is_env_open:
            self._on_error(len(lines), "The ifdef command is not closed.")

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

    def _process_description(self, line_number: int, line: str):
        if VARIABLE_DECL.match(line):
            return
        pos = 0
        res = BACKQUOTE.search(line, pos)
        while res:
            pos = self._check_inlined_code(line_number, res.end(), line, res.group(1))
            res = BACKQUOTE.search(line, pos)

    def _check_inlined_code(self, line_number: int, pos: int, line: str, pattern: str):
        if len(pattern) > 2:
            # Part of the backquotes are displayed as backquotes.
            self._on_error(line_number, 'Use "++" to isolate the backquotes you want to display from the ones that should be interpreted by AsciiDoc.')
            return pos

        content_end = inline_end(line, pos, pattern)
        if content_end < 0:
            self._on_error(line_number, 'Unbalanced code inlining tags')
            return len(line)
        content = line[pos: content_end]
        # print(f'{line_index} content is {content} {NEED_PROTECTION.pattern}')
        pos = content_end + len(pattern)
        if NEED_PROTECTION.fullmatch(content):
            self._on_error (line_number, f'''
Using backquotes does not protect against asciidoc interpretation. Starting or
ending a word with '*', '#', '_' or having two of them consecutively will
trigger unintended behavior with the rest of the text.
Use ``++{content}++`` to avoid that.
''')
            return pos
        return pos

    def _on_error(self, line_number: int, message: str):
        print(f"{self._file}:{line_number} {message}")
        self._is_valid = False


def main():
    files = sys.argv[1:]
    if not files:
        sys.exit("Missing input files")

    valid = True
    for file in files:
        if not Checker(Path(file)).process():
            valid = False
    if not valid:
        sys.exit(1)

if __name__ == "__main__":
    main()
