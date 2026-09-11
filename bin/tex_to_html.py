#!/usr/bin/env python3

import argparse
import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LATEX_DIR = ROOT / "latex"


# (LaTeX heading command, HTML tag, CSS class)
HEADING_RULES = [
    ("section", "h2", "blog-section"),
    ("subsection", "h3", "blog-subsection"),
]


# (LaTeX one-argument command, opening HTML, closing HTML)
ONE_ARG_RULES = [
    ("textit", "<em>", "</em>"),
    ("emph", "<em>", "</em>"),
    ("textbf", "<strong>", "</strong>"),
]


# (LaTeX two-argument command, conversion type)
# I could probably remove redundancy, but what if I need it!!!!!
TWO_ARG_RULES = [
    ("href", "href"),
    ("blogfigure", "blogfigure"),
]


def extract_document(tex: str) -> str:
    match = re.search(
        r"\\begin\{document\}(.*?)\\end\{document\}",
        tex,
        flags=re.DOTALL,
    )

    if not match:
        raise ValueError(
            r"Could not find \begin{document}...\end{document}"
        )

    return match.group(1).strip()


def read_braced(source: str, start: int):
    """
    Read a {...} group starting at source[start].

    Returns:
        (contents, index_after_closing_brace)
    """

    if start >= len(source) or source[start] != "{":
        raise ValueError("Expected '{'")

    depth = 0

    for i in range(start, len(source)):
        char = source[i]

        if char == "{":
            depth += 1

        elif char == "}":
            depth -= 1

            if depth == 0:
                return source[start + 1 : i], i + 1

    raise ValueError("Unmatched '{'")


def replace_one_arg_command(
    source: str,
    command: str,
    open_tag: str,
    close_tag: str,
) -> str:
    """
    Convert a one-argument LaTeX command such as:

        \\emph{hello}

    into:

        <em>hello</em>
    """

    token = "\\" + command
    output = []
    i = 0

    while i < len(source):
        pos = source.find(token, i)

        if pos == -1:
            output.append(source[i:])
            break

        output.append(source[i:pos])

        brace = pos + len(token)

        if brace >= len(source) or source[brace] != "{":
            output.append(token)
            i = brace
            continue

        content, end = read_braced(
            source,
            brace,
        )

        output.append(
            open_tag
            + content
            + close_tag
        )

        i = end

    return "".join(output)


def replace_two_arg_command(
    source: str,
    command: str,
    rule_type: str,
) -> str:
    """
    Convert a two-argument LaTeX command such as:

        \\href{https://example.com}{example}

    or:

        \\blogfigure{/assets/svg/figure.svg}
        {\\textbf{Figure 1.} A lattice.}

    into HTML.
    """

    token = "\\" + command
    output = []
    i = 0

    while i < len(source):
        pos = source.find(token, i)

        if pos == -1:
            output.append(source[i:])
            break

        output.append(source[i:pos])

        first_brace = pos + len(token)

        # Allow whitespace/newlines before the first argument.
        while (
            first_brace < len(source)
            and source[first_brace].isspace()
        ):
            first_brace += 1

        if (
            first_brace >= len(source)
            or source[first_brace] != "{"
        ):
            output.append(token)
            i = pos + len(token)
            continue

        first, after_first = read_braced(
            source,
            first_brace,
        )

        second_brace = after_first

        # Allow whitespace/newlines between the two arguments.
        while (
            second_brace < len(source)
            and source[second_brace].isspace()
        ):
            second_brace += 1

        if (
            second_brace >= len(source)
            or source[second_brace] != "{"
        ):
            output.append(source[pos:after_first])
            i = after_first
            continue

        second, end = read_braced(
            source,
            second_brace,
        )

        if rule_type == "href":
            output.append(
                f'<a href="{html.escape(first, quote=True)}">'
                f"{second}"
                "</a>"
            )

        elif rule_type == "blogfigure":
            output.append(
                "\n\n"
                '<figure class="blog-figure">\n'
                f'    <img src="{html.escape(first, quote=True)}" alt="">\n'
                "    <figcaption>\n"
                f"        {second}\n"
                "    </figcaption>\n"
                "</figure>"
                "\n\n"
            )

        else:
            raise ValueError(
                f"Unknown two-argument rule type: {rule_type}"
            )

        i = end

    return "".join(output)

def replace_heading(
    source: str,
    command: str,
    tag: str,
    css_class: str,
) -> str:
    """
    Convert a LaTeX heading such as:

        \\section{Lattices}

    into:

        <h2 class="blog-section">Lattices</h2>
    """

    token = "\\" + command
    output = []
    i = 0

    while i < len(source):
        pos = source.find(token, i)

        if pos == -1:
            output.append(source[i:])
            break

        output.append(source[i:pos])

        brace = pos + len(token)

        if brace >= len(source) or source[brace] != "{":
            output.append(token)
            i = brace
            continue

        content, end = read_braced(
            source,
            brace,
        )

        output.append(
            f'\n\n<{tag} class="{css_class}">'
            f"{content}"
            f"</{tag}>\n\n"
        )

        i = end

    return "".join(output)


def latex_to_html(tex: str) -> str:
    body = extract_document(tex)

    # Block-level heading commands.
    for command, tag, css_class in HEADING_RULES:
        body = replace_heading(
            body,
            command,
            tag,
            css_class,
        )

    # Inline one-argument commands.
    for command, open_tag, close_tag in ONE_ARG_RULES:
        body = replace_one_arg_command(
            body,
            command,
            open_tag,
            close_tag,
        )

    # Two-argument commands.
    #
    # Most are inline, such as \href.
    # \blogfigure deliberately emits a block-level <figure>.
    for command, rule_type in TWO_ARG_RULES:
        body = replace_two_arg_command(
            body,
            command,
            rule_type,
        )

    # Blank lines separate paragraphs / blocks.
    blocks = re.split(
        r"\n\s*\n",
        body,
    )

    output = []

    block_prefixes = (
        *(
            f'<{tag} class="{css_class}">'
            for _, tag, css_class in HEADING_RULES
        ),
        '<figure class="blog-figure">',
    )

    for block in blocks:
        block = block.strip()

        if not block:
            continue

        if block.startswith(block_prefixes):
            output.append(block)

        else:
            output.append(
                '<p class="blog-paragraph">'
                f"{block}"
                "</p>"
            )

    return "\n\n".join(output)


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Convert temporary LaTeX into "
            "a blog HTML fragment."
        )
    )

    parser.add_argument(
        "input",
        type=Path,
        help=(
            "LaTeX file, e.g. "
            "latex/lattices_1.tex"
        ),
    )

    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help=(
            "Optional output path. "
            "Defaults to latex/<name>.html"
        ),
    )

    args = parser.parse_args()

    input_path = args.input

    if not input_path.is_absolute():
        input_path = ROOT / input_path

    if args.output:
        output_path = args.output

        if not output_path.is_absolute():
            output_path = ROOT / output_path

    else:
        output_path = (
            LATEX_DIR
            / f"{input_path.stem}.html"
        )

    tex = input_path.read_text()
    converted = latex_to_html(tex)

    output_path.write_text(
        converted + "\n"
    )

    print(
        f"{input_path.relative_to(ROOT)} "
        f"-> "
        f"{output_path.relative_to(ROOT)}"
    )


if __name__ == "__main__":
    main()
