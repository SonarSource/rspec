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
import re


VALID_IFDEF = "ifdef::env-github,rspecator-view[]"
VALID_ENDIF = "endif::env-github,rspecator-view[]"

VARIABLE_DECL = re.compile(r':\w+: ')

INCLUDE = re.compile(r'include::')

FORMATTING_CHARS = ['_', r'\*', r'\#']
WORD_FORMATTING_CHARS = [r'\~', r'\^']

# If the formatting char is repeated twice, it can go anywhere
UNCONSTRAINED_FORMATTING = '|'.join(x + x for x in FORMATTING_CHARS)
# Single formatting char are dangerous at the beginning of a word
FORMATTING_OPENING = '|'.join(r'(\W|^)' + x + r'\w' for x in FORMATTING_CHARS)
# Single formatting char are dangerous at the end of a word
FORMATTING_CLOSING = '|'.join(r'\w' + x + r'(\W|$)' for x in FORMATTING_CHARS)
# Word formatting is broken by spaces so we look for things like `#word#`
WORD_FORMATTING = "|".join(x + r'\S+' + x for x in WORD_FORMATTING_CHARS)

# We combine all the matchers
NEED_PROTECTION = re.compile('[^+]*('
                             f'{UNCONSTRAINED_FORMATTING}|'
                             f'{FORMATTING_OPENING}|'
                             f'{FORMATTING_CLOSING}|'
                             f'{WORD_FORMATTING}'
                             ')[^+]*')

CLOSE_CONSTRAINED_PASSTHROUGH = re.compile(r'\w\+\b')

BACKQUOTE = re.compile(r'((\`\`+)|(?<![\\\w])(\`)(?!\s))')


def close_passthrough(count, pos, line):
    while count > 0:
        # `+++a++` will display '+a' in case of inbalance, we try to find the biggest closing block
        if count == 1 and line[pos + count].isalnum() and not line[pos - 1].isalnum():
            #constrained '+'. It is a passthrough only if it is directly around text and surrounded by spaces: \b+\w.*\w+\b
            close_pattern = CLOSE_CONSTRAINED_PASSTHROUGH
        else:
            close_pattern = re.compile(r'\+' * count)
        end = close_pattern.search(line, pos + count)
        if end:
            return end.end()
        count -= 1
    return pos


def close_inline_block(line: str, pos: int, pattern: str):
    max_pos = len(line)
    while pos < max_pos:
        if line[pos] == '+':
            count = 1
            while pos + count < max_pos and line[pos + count] == '+':
                count += 1
            pos = close_passthrough(count, pos, line)
        if line[pos] == '`' and ((len(pattern) == 1 and (pos == max_pos -1 or not line[pos + 1].isalnum())) or (pos < max_pos - 1 and line[pos + 1] == '`')):
            return pos
        pos += 1
    return -1


class Sanitizer:
    def __init__(self, file: Path):
        assert file.exists()
        assert file.is_file()

        self._file = file
        self._is_env_open = False
        self._has_env = False
        self._error_count = 0
        self._code = False
        self._empty_line = True
        self._was_include = False

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
                self._process_open_ifdef(line_number, line)
            elif line.startswith("endif::"):
                self._process_close_ifdef(line_number, line)
            elif not line.strip():
                self._empty_line = True
            else:
                self._process_description(line_number, line)
                self._empty_line = False

        if self._is_env_open:
            self._on_error(len(lines), "An ifdef command is opened but never closed.")

        return self._error_count

    def _process_open_ifdef(self, line_number: int, line: str):
        if self._has_env:
            message = "Only one ifdef command is allowed per file."
            if self._is_env_open:
                message += "\nThe previous ifdef command was not closed."
            self._on_error(line_number, message)

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

    def _process_close_ifdef(self, line_number: int, line: str):
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
        if INCLUDE.match(line) or (self._was_include and not self._empty_line):
            self._was_include = True
            if not self._empty_line:
                self._on_error(line_number, '''An include is stuck to other content.
This may result in broken tags and other display issues.
Make sure there is an empty line before and after each include''')
            return
        else:
            self._was_include = False
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

        content_end = close_inline_block(line, pos, pattern)
        if content_end < 0:
            message='Unbalanced code inlining tags.'
            if len(pattern) == 1:
                message += '''
If you are trying to write inline code that is glued to text without a space,
you need to use double backquotes:
> Replace all `reference`s.
Will not display correctly. You need to write:
> Replace all ``reference``s.
'''
            self._on_error(line_number, message)
            return len(line)
        content = line[pos: content_end]
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
        self._error_count += 1


def sanitize_asciidoc(file_path: Path):
    return Sanitizer(file_path).process()
