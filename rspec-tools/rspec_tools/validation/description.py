import re
from pathlib import Path
from typing import Dict, Final, List, Union

from bs4 import BeautifulSoup

from rspec_tools.errors import RuleValidationError
from rspec_tools.rules import LanguageSpecificRule
from rspec_tools.utils import LANG_TO_SOURCE


def read_file(path):
    section_names_path = Path(__file__).parent.parent.parent.parent.joinpath(path)
    return section_names_path.read_text(encoding="utf-8").split("\n")


def parse_names(path):
    section_names_path = read_file(path)
    return [s.replace("* ", "").strip() for s in section_names_path if s.strip()]


def parse_security_standard_links(descr):
    link_nodes = descr.find_all("a")
    security_standards_links: Dict[str, List] = {}
    for node in link_nodes:
        href = node.attrs["href"]
        for standard_key in SECURITY_STANDARD_URL:
            standard = SECURITY_STANDARD_URL[standard_key]
            url_pattern = standard["url_pattern"]
            result = re.match(url_pattern, href)
            if result is not None:
                convert = standard["convert_id"]
                category = convert(result[1])
                if standard_key not in security_standards_links.keys():
                    security_standards_links[standard_key] = []
                security_standards_links[standard_key].append(category)
    return security_standards_links


HOW_TO_FIX_IT = "How to fix it"
HOW_TO_FIX_IT_REGEX = re.compile(HOW_TO_FIX_IT)
SECURITY_STANDARD_URL = {
    "OWASP": {
        "url_pattern": r"https://(?:www\.)?owasp\.org/www-project-top-ten/2017/A(10|[1-9])_2017-",
        "convert_id": lambda value: f"A{value.lstrip('0')}",
    },
    "OWASP Top 10 2021": {
        "url_pattern": r"https://(?:www\.)?owasp\.org/Top10/A(10|0[1-9])_2021-",
        "convert_id": lambda value: f"A{value.lstrip('0')}",
    },
}

# The list of all the sections currently accepted by the script.
# The list includes multiple variants for each title because they all occur
# in the migrated RSPECs.
# Further work required to shorten the list by renaming the sections in some RSPECS
# to keep only on version for each title.
HOTSPOT_SECTION_NAMES: Final[list[str]] = parse_names(
    "docs/header_names/hotspot_section_names.adoc"
)
# The list of all the framework names currently accepted by the script.
ACCEPTED_FRAMEWORK_NAMES: Final[list[str]] = parse_names(
    "docs/header_names/allowed_framework_names.adoc"
)

# This needs to be kept in sync with the [headers list in docs/descriptions.adoc](https://github.com/SonarSource/rspec/blob/master/docs/description.adoc#2-education-format)
MANDATORY_SECTIONS = ["Why is this an issue?"]
CODE_EXAMPLES = "Code examples"
OPTIONAL_SECTIONS = {
    # Also covers 'How to fix it in {Framework Display Name}'
    HOW_TO_FIX_IT: [],  # Empty list because we now accept anything as sub-section
    "Resources": [
        "Documentation",
        "Articles & blog posts",
        "Conference presentations",
        "Standards",
        "External coding guidelines",
        "Benchmarks",
        "Related rules",
    ],
}
SUBSECTIONS = {CODE_EXAMPLES: ["Noncompliant code example", "Compliant solution"]}


def validate_duplications(h2_titles, rule_language):
    as_set = set(h2_titles)
    if len(as_set) != len(h2_titles):
        duplicates = [x for x in h2_titles if h2_titles.count(x) > 1]
        raise RuleValidationError(
            f"Rule {rule_language.id} has duplicated {set(duplicates)} sections"
        )


def intersection(list1, list2):
    return list(set(list1).intersection(list2))


def difference(list1, list2):
    return list(set(list1) - set(list2))


def validate_titles_are_not_misclassified_as_subtitles(
    rule_language: LanguageSpecificRule,
    subtitles: list[str],
    allowed_h2_sections: list[str],
):
    # TODO This does not validate "How to fix it" section for frameworks as the section names are a bit special.
    misclassified = intersection(subtitles, allowed_h2_sections)
    if misclassified:
        misclassified.sort()
        misclassified_str = ", ".join(misclassified)
        raise RuleValidationError(
            f"Rule {rule_language.id} has some sections misclassified. Ensure there are not too many `=` in the asciidoc file for: {misclassified_str}"
        )


def validate_section_names(rule_language: LanguageSpecificRule):
    """Validates all h2-level section names"""

    def get_titles(level: Union[str, list[str]]) -> list[str]:
        return list(
            map(lambda x: x.text.strip(), rule_language.description.find_all(level))
        )

    h2_titles = get_titles("h2")
    subtitles = get_titles(["h3", "h4", "h5", "h6"])
    allowed_h2_sections = list(MANDATORY_SECTIONS) + list(OPTIONAL_SECTIONS.keys())
    validate_titles_are_not_misclassified_as_subtitles(
        rule_language, subtitles, allowed_h2_sections
    )
    validate_duplications(h2_titles, rule_language)

    education_titles = intersection(h2_titles, allowed_h2_sections)
    if education_titles:
        # Using the education format.
        validate_how_to_fix_it_sections_names(rule_language, h2_titles)
        missing_titles = difference(list(MANDATORY_SECTIONS), education_titles)
        if missing_titles:
            # All mandatory titles have to be present in the rule description.
            raise RuleValidationError(
                f'Rule {rule_language.id} is missing the "{missing_titles[0]}" section'
            )
    else:
        # Using the hotspot format.
        for title in h2_titles:
            if title not in HOTSPOT_SECTION_NAMES:
                raise RuleValidationError(
                    f'Rule {rule_language.id} has an unconventional header "{title}"'
                )


def validate_how_to_fix_it_sections_names(
    rule_language: LanguageSpecificRule, h2_titles: list[str]
):
    how_to_fix_it_sections = [s for s in h2_titles if HOW_TO_FIX_IT_REGEX.match(s)]
    if not how_to_fix_it_sections:
        # No 'How to fix it' section for the rule.
        return
    if len(how_to_fix_it_sections) > 6:
        raise RuleValidationError(
            f'Rule {rule_language.id} has more than 6 "{HOW_TO_FIX_IT}" sections. Please ensure this limit can be increased with PM/UX teams'
        )

    if HOW_TO_FIX_IT in how_to_fix_it_sections and len(how_to_fix_it_sections) > 1:
        raise RuleValidationError(
            f'Rule {rule_language.id} is mixing "{HOW_TO_FIX_IT}" with "How to fix it in FRAMEWORK NAME" sections. Either use a single "{HOW_TO_FIX_IT}" or one or more "How to fix it in FRAMEWORK"'
        )
    for section_name in how_to_fix_it_sections:
        validate_how_to_fix_it_framework(section_name, rule_language)


def validate_how_to_fix_it_framework(section_name, rule_language):
    result = re.search("How to fix it in (?:(?:an|a|the)\\s)?(.*)", section_name)
    if result is not None:
        current_framework = result.group(1)
        if current_framework not in ACCEPTED_FRAMEWORK_NAMES:
            raise RuleValidationError(
                f'Rule {rule_language.id} has a "{HOW_TO_FIX_IT}" section for an unsupported framework: "{result.group(1)}"'
            )
    elif section_name != HOW_TO_FIX_IT:
        raise RuleValidationError(
            f'Rule {rule_language.id} has a "{HOW_TO_FIX_IT}" section with an unsupported format: "{section_name}". Either use "{HOW_TO_FIX_IT}" or "How to fix it in FRAMEWORK NAME"'
        )


def collect_titles(node, level):
    """Collects all the titles of a given level starting from the provided node

    The goal of this function is to extract titles from the extra HTML tags
    that are produced when the HTML file is produced from the ASCIIdoc.
    The titles are collected in the order in which they appear.

    Args:
        node (BeautifulSoup): BeautifulSoup object
        level (int): the level of title we are looking for

    Returns:
        list[BeautifulSoup]: List of nodes that were found.
    """

    current = node.next_sibling
    nodes = []
    while current is not None:
        if hasattr(current, "find_all"):
            nodes = nodes + current.find_all(f"h{level}")
        current = current.next_sibling
    return nodes


def validate_section_levels(rule_language: LanguageSpecificRule):
    h1 = rule_language.description.find("h1")
    if h1 is not None:
        name = h1.text.strip()
        raise RuleValidationError(
            f'Rule {rule_language.id} has level-0 header "{name}"'
        )


def validate_one_parameter(child, id):
    if child.name != "div" or child["class"][0] != "sidebarblock":
        raise RuleValidationError(
            f"Rule {id} should use `****` blocks for each parameter"
        )
    for div_child in child.children:
        if div_child.name is not None:
            if div_child["class"][0] != "content":
                raise RuleValidationError(
                    f"Rule {id} should use `****` blocks for each parameter"
                )
            if div_child.p is None:
                raise RuleValidationError(
                    f"Rule {id} should have a description for each parameter"
                )
            if div_child.find("div", "title") is None:
                raise RuleValidationError(
                    f"Rule {id} should have a parameter name declared with `.name` before the bock, for each parameter"
                )


def validate_parameters(rule_language: LanguageSpecificRule):
    for h3 in rule_language.description.find_all("h3"):
        name = h3.text.strip()
        if name == "Parameters":
            for child in h3.parent.children:
                if child.name is None or child == h3 or child.name == "hr":
                    continue
                validate_one_parameter(child, rule_language.id)


def highlight_name(rule_language: LanguageSpecificRule):
    if rule_language.language in LANG_TO_SOURCE:
        return LANG_TO_SOURCE[rule_language.language]
    return rule_language.language


def known_highlight(language):
    return language in LANG_TO_SOURCE.values()


def validate_source_language(rule_language: LanguageSpecificRule):
    descr = rule_language.description
    for h2 in descr.find_all("h2"):
        name = h2.text.strip()
        if name.startswith("Compliant") or name.startswith("Noncompliant"):
            for pre in h2.parent.find_all("pre"):
                if (
                    not pre.has_attr("class")
                    or pre["class"][0] != "highlight"
                    or not pre.code
                    or not pre.code.has_attr("data-lang")
                ):
                    raise RuleValidationError(
                        f"""Rule {rule_language.id} has non highlighted code example in section "{name}".
Use [source,{highlight_name(rule_language)}] or [source,text] before the opening '----'."""
                    )
                elif not known_highlight(pre.code["data-lang"]):
                    raise RuleValidationError(
                        f"""Rule {rule_language.id} has unknown language "{pre.code['data-lang']}" in code example in section "{name}".
Are you looking for "{highlight_name(rule_language)}"?"""
                    )


def validate_subsections(rule_language: LanguageSpecificRule):
    for optional_section in list(OPTIONAL_SECTIONS.keys()):
        if optional_section == HOW_TO_FIX_IT:
            validate_subsections_for_section(
                rule_language,
                optional_section,
                OPTIONAL_SECTIONS[optional_section],
                section_regex=HOW_TO_FIX_IT_REGEX,
            )
        else:
            validate_subsections_for_section(
                rule_language, optional_section, OPTIONAL_SECTIONS[optional_section]
            )
    for subsection_with_sub_subsection in list(SUBSECTIONS.keys()):
        if subsection_with_sub_subsection == CODE_EXAMPLES:
            validate_subsections_for_section(
                rule_language,
                subsection_with_sub_subsection,
                SUBSECTIONS[subsection_with_sub_subsection],
                level=4,
                is_duplicate_allowed=True,
            )
        else:
            validate_subsections_for_section(
                rule_language,
                subsection_with_sub_subsection,
                SUBSECTIONS[subsection_with_sub_subsection],
                level=4,
            )


def validate_subsections_for_section(
    rule_language: LanguageSpecificRule,
    section_name: str,
    allowed_subsections: set[str],
    **options,
):

    # Handle options
    level = options["level"] if "level" in options else 3
    section_regex = (
        options["section_regex"] if "section_regex" in options else section_name
    )
    is_duplicate_allowed = (
        options["is_duplicate_allowed"] if "is_duplicate_allowed" in options else False
    )

    descr = rule_language.description
    top_level_section = descr.find(f"h{level-1}", string=section_regex)
    if top_level_section is not None:
        titles = collect_titles(top_level_section, level)
        subsections_seen = set()
        for title in titles:
            name = title.text.strip()
            if allowed_subsections and name not in allowed_subsections:
                raise RuleValidationError(
                    f'Rule {rule_language.id} has a "{section_name}" subsection with an unallowed name: "{name}"'
                )
            if name in subsections_seen and not is_duplicate_allowed:
                raise RuleValidationError(
                    f'Rule {rule_language.id} has duplicate "{section_name}" subsections. There are 2 occurences of "{name}"'
                )
            subsections_seen.add(name)


def validate_security_standard_links(rule_language: LanguageSpecificRule):
    descr = rule_language.description
    security_standards_links = parse_security_standard_links(descr)
    metadata = rule_language.metadata

    # Avoid raising mismatch issues on deprecated or closed rules
    if metadata.get("status") != "ready":
        return

    security_standards_metadata = metadata.get("securityStandards", {})
    for standard in SECURITY_STANDARD_URL.keys():

        metadata_mapping = (
            security_standards_metadata[standard]
            if standard in security_standards_metadata.keys()
            else []
        )
        links_mapping = (
            security_standards_links[standard]
            if standard in security_standards_links.keys()
            else []
        )

        extra_links = difference(links_mapping, metadata_mapping)
        if len(extra_links) > 0:
            raise RuleValidationError(
                f"Rule {rule_language.id} has a mismatch for the {standard} security standards. Remove links from the Resources/See section ({extra_links}) or fix the rule metadata"
            )

        missing_links = difference(metadata_mapping, links_mapping)
        if len(missing_links) > 0:
            raise RuleValidationError(
                f"Rule {rule_language.id} has a mismatch for the {standard} security standards. Add links to the Resources/See section ({missing_links}) or fix the rule metadata"
            )
