"""Ensure the asciidoc code for a rule description follows best practices

Checks are:
* "ifdef"/"endif" blocks should be well-formed for RSPEC
* Inline code with backquotes is correctly escaped and balanced
* Include commands are not appended to other code
* "C++" is referred to using the {cpp} attribute
* rules.sonarsource.com is not linked directly
"""

import re
from pathlib import Path

VALID_IFDEF = "ifdef::env-github,rspecator-view[]"
VALID_ENDIF = "endif::env-github,rspecator-view[]"

VARIABLE_DECL = re.compile(r":\w+: ")

INCLUDE = re.compile(r"include::")

FORMATTING_CHARS = ["_", r"\*", r"\#"]
WORD_FORMATTING_CHARS = [r"\~", r"\^"]

# If the formatting char is repeated twice, it can go anywhere
UNCONSTRAINED_FORMATTING = "|".join(x + x for x in FORMATTING_CHARS)
# Single formatting char are dangerous at the beginning of a word
FORMATTING_OPENING = "|".join(r"(\W|^)" + x + r"\w" for x in FORMATTING_CHARS)
# Single formatting char are dangerous at the end of a word
FORMATTING_CLOSING = "|".join(r"\w" + x + r"(\W|$)" for x in FORMATTING_CHARS)
# Word formatting is broken by spaces so we look for things like `#word#`
WORD_FORMATTING = "|".join(x + r"\S+" + x for x in WORD_FORMATTING_CHARS)

# We combine all the matchers
NEED_PROTECTION = re.compile(
    "("
    f"{UNCONSTRAINED_FORMATTING}|"
    f"{FORMATTING_OPENING}|"
    f"{FORMATTING_CLOSING}|"
    f"{WORD_FORMATTING}"
    ")"
)

# There is a regex trick here:
# We want to stop the search if there is a backquote
# We do that by matching backquote OR the closing passthrough
# Then we'll ignore any match of backquote
CLOSE_CONSTRAINED_PASSTHROUGH = re.compile(r"`|((?<!\s)\+(?=`))")

CLOSE_CONSTRAINED_BACKQUOTE = re.compile(r"`(?!\w)")
CLOSE_UNCONSTRAINED_BACKQUOTE = re.compile("``")

PASSTHROUGH_MACRO_TEXT = r"pass:\w*\[(\\\]|[^\]])*\]"

PASSTHROUGH_MACRO = re.compile(PASSTHROUGH_MACRO_TEXT)

CPP = re.compile(r"\b[Cc]\+\+")

RULES_SONARSOURCE = re.compile(r"https?:\/\/rules\.sonarsource\.com\/(.*)\/RSPEC-\d+")

# There is a regex trick here:
# We want to skip passthrough macros, to not find pass:[``whatever``]
# We do that by matching
# * EITHER passthrough macros including their ignored backquotes
# * OR backquotes
# Then we'll ignore any match of PASSTHROUGH_MACRO
BACKQUOTE = re.compile(
    PASSTHROUGH_MACRO_TEXT + r"|(?P<backquote>(``+)|(?<![\\\w])(`)(?!\s))"
)


def close_passthrough(count, pos, line):
    """Find the end of a passthrough block marked by *count* plus signs"""
    while count > 0:
        # `+++a++` will display '+a' in case of inbalance, we try to find the biggest closing block
        if count == 1:
            if not line[pos + count].isspace() and line[pos - 1] == "`":
                # constrained '+'. It is a passthrough only if it is directly around text and surrounded by backquotes: `+Some Content+`
                close_pattern = CLOSE_CONSTRAINED_PASSTHROUGH
            else:
                return pos
        else:
            close_pattern = re.compile("(" + r"\+" * count + ")")
        end = close_pattern.search(line, pos + count)
        if end and end.group(1):
            return end.end()
        count -= 1
    return pos


def skip_passthrough_macro(line, pos):
    """If this is a passthrough macro, skip to the end"""
    if line[pos] == "p":
        pm = PASSTHROUGH_MACRO.match(line, pos)
        if pm:
            return pm.end()
    return pos


def skip_passthrough_plus(line, pos):
    """If this is a passthrough +, skip to the end"""
    if line[pos] == "+":
        count = 1
        while pos + count < len(line) and line[pos + count] == "+":
            count += 1
        return close_passthrough(count, pos, line)
    return pos


def close_inline_block(line: str, pos: int, closing_pattern: re.Pattern[str]):
    """Find the end of an inline block started with *pattern*"""
    content = ""
    while pos < len(line):
        pos = skip_passthrough_macro(line, pos)
        pos = skip_passthrough_plus(line, pos)
        if closing_pattern.match(line, pos):
            return pos, content
        content += line[pos]
        pos += 1
    return -1, content


class Sanitizer:
    def __init__(self, file: Path):
        assert file.exists()
        assert file.is_file()

        self._file = file
        self._is_env_open = False
        self._has_env = False
        self._error_count = 0
        self._is_inside_code = False
        self._empty_line = True
        self._previous_line_was_include = False

    def process(self) -> bool:
        content = self._file.read_text(encoding="utf-8")
        lines = content.splitlines(keepends=False)
        for line_index, line in enumerate(lines):
            if self._is_inside_code:
                if line == "----":
                    self._is_inside_code = False
                continue
            if line == "----":
                self._is_inside_code = True
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
        elif line != VALID_IFDEF:
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

    def _advance_to_next_backquote(self, line: str, pos: int, line_number: int):
        next_pos = BACKQUOTE.search(line, pos)
        if next_pos:
            cpp = CPP.search(line, pos, endpos=next_pos.pos)
        else:
            cpp = CPP.search(line, pos)
        if cpp:
            self._on_error(
                line_number,
                'To avoid rendering issues, always use the "{cpp}" attribute to refer to the language C++.',
            )
        return next_pos

    def _process_description(self, line_number: int, line: str):
        if VARIABLE_DECL.match(line):
            return
        if self._previous_line_was_include and not self._empty_line:
            self._on_error(
                line_number - 1,
                """An empty line is missing after the include.
This may result in broken tags and other display issues.
Make sure there are always empty lines before and after each include.""",
            )
        if INCLUDE.match(line):
            self._previous_line_was_include = True
            if not self._empty_line:
                self._on_error(
                    line_number,
                    """An empty line is missing before the include.
This may result in broken tags and other display issues.
Make sure there are always empty lines before and after each include.""",
                )
            return
        else:
            self._previous_line_was_include = False
        if RULES_SONARSOURCE.search(line) and not self._is_env_open:
            self._on_error(
                line_number,
                """Do not put direct links to https://rules.sonarsource.com/.
Just use the rule ID and let cross-reference substitution do its job.""",
            )
        pos = 0
        res = self._advance_to_next_backquote(line, pos, line_number)
        # We filter out matches for passthrough. See comment near the BACKQUOTE declaration
        while res and res.group("backquote"):
            pos = self._check_inlined_code(
                line_number, res.end(), line, res.group("backquote")
            )
            res = self._advance_to_next_backquote(line, pos, line_number)

    def _check_inlined_code(
        self, line_number: int, pos: int, line: str, opening_pattern: str
    ):
        if len(opening_pattern) > 2:
            # Part of the backquotes are displayed as backquotes.
            self._on_error(
                line_number,
                'Use "++" to isolate the backquotes you want to display from the ones that should be interpreted by AsciiDoc.',
            )
            return pos
        elif len(opening_pattern) == 2:
            closing_pattern = CLOSE_UNCONSTRAINED_BACKQUOTE
        else:
            closing_pattern = CLOSE_CONSTRAINED_BACKQUOTE

        content_end, content = close_inline_block(line, pos, closing_pattern)
        if content_end < 0:
            message = "Unbalanced code inlining tags."
            if len(opening_pattern) == 1:
                message += """
If you are trying to write inline code that is glued to text without a space,
you need to use double backquotes:
> Replace all `reference`s.
Will not display correctly. You need to write:
> Replace all ``reference``s.
"""
            self._on_error(line_number, message)
            return len(line)
        pos = content_end + len(opening_pattern)
        if NEED_PROTECTION.search(content):
            self._on_error(
                line_number,
                f"""
Using backquotes does not protect against asciidoc interpretation. Starting or
ending a word with '*', '#', '_' or having two of them consecutively will
trigger unintended behavior with the rest of the text.
Use ``++{content}++`` to avoid that.
If you really want to have formatting inside your code, you can write
``pass:n[{content}]``
""",
            )
            return pos
        return pos

    def _on_error(self, line_number: int, message: str):
        print(f"{self._file}:{line_number} {message}")
        self._error_count += 1


def sanitize_asciidoc(file_path: Path):
    """Called by the CLI"""
    return Sanitizer(file_path).process()
