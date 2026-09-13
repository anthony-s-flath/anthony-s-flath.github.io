#!/usr/bin/env python3

"""
Simple LaTeX-to-HTML converter for blog posts.

This script handles only the small subset of LaTeX used by the blog:
- blog metadata such as title and dates
- section/subsection headings
- basic inline formatting such as \\textit, \\emph, and \\textbf
- links with \\href
- blog figures
- simple itemize/enumerate lists
- lightweight bibliography entries
"""

import argparse
import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "blog" / "_template.html"

METADATA = ("blogtitle", "blogsubtitle", "written", "updated")

HEADINGS = {
    "section": ("h2", "blog-section"),
    "subsection": ("h3", "blog-subsection"),
}

INLINE = {
    "textit": ("<em>", "</em>"),
    "emph": ("<em>", "</em>"),
    "textbf": ("<strong>", "</strong>"),
}

LISTS = {
    "enumerate": "ol",
    "itemize": "ul",
}


def read_braced(s, i):
    """Read {...}, including nested braces."""
    if i >= len(s) or s[i] != "{":
        raise ValueError("Expected '{'")

    depth = 0

    for j in range(i, len(s)):
        if s[j] == "{":
            depth += 1
        elif s[j] == "}":
            depth -= 1

        if depth == 0:
            return s[i + 1 : j], j + 1

    raise ValueError("Unmatched '{'")


def read_args(s, i, n):
    args = []

    for _ in range(n):
        while i < len(s) and s[i].isspace():
            i += 1

        if i >= len(s) or s[i] != "{":
            return None

        arg, i = read_braced(s, i)
        args.append(arg)

    return args, i


def replace_command(s, command, nargs, render):
    token = "\\" + command
    out = []
    i = 0

    while True:
        pos = s.find(token, i)

        if pos < 0:
            out.append(s[i:])
            break

        out.append(s[i:pos])

        parsed = read_args(
            s,
            pos + len(token),
            nargs,
        )

        if not parsed:
            out.append(token)
            i = pos + len(token)
            continue

        args, i = parsed
        out.append(render(*args))

    return "".join(out)


def extract_document(tex):
    match = re.search(
        r"\\begin\{document\}(.*?)\\end\{document\}",
        tex,
        re.DOTALL,
    )

    if not match:
        raise ValueError(r"Could not find \begin{document}...\end{document}")

    return match.group(1).strip()


def extract_commands(body, commands):
    """
    Extract one-argument commands and remove them from body.

    Returns:
        ({command: value}, cleaned_body)
    """
    values = {}

    for command in commands:
        token = "\\" + command
        pos = body.find(token)

        if pos < 0:
            raise ValueError(f"Missing \\{command}{{...}}")

        parsed = read_args(
            body,
            pos + len(token),
            1,
        )

        if not parsed:
            raise ValueError(f"Invalid \\{command}{{...}}")

        (value,), end = parsed
        values[command] = value.strip()

        body = body[:pos] + body[end:]

    return values, body.strip()


def extract_bibliography(body):
    """Remove all \\bib{...} commands and return their contents."""
    entries = []
    token = r"\bib"
    out = []
    i = 0

    while True:
        pos = body.find(token, i)

        if pos < 0:
            out.append(body[i:])
            break

        out.append(body[i:pos])

        parsed = read_args(
            body,
            pos + len(token),
            1,
        )

        if not parsed:
            raise ValueError(r"Invalid \bib{...}")

        (entry,), i = parsed
        entries.append(entry.strip())

    return entries, "".join(out).strip()


def split_fields(s):
    """
    Split BibTeX fields on top-level commas.

    Commas inside {...} or "..." are ignored.
    """
    fields = []
    start = 0
    depth = 0
    quoted = False

    for i, char in enumerate(s):
        if char == '"':
            quoted = not quoted
        elif not quoted:
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
            elif char == "," and depth == 0:
                fields.append(s[start:i])
                start = i + 1

    fields.append(s[start:])
    return fields


def clean_bib_value(value):
    value = value.strip()

    if len(value) >= 2 and (
        (value[0] == "{" and value[-1] == "}") or (value[0] == '"' and value[-1] == '"')
    ):
        value = value[1:-1]

    # Good enough for ordinary copied BibTeX.
    value = value.replace("{", "").replace("}", "")
    value = value.replace(r"\&", "&")
    value = value.replace("~", " ")
    value = value.replace("--", "–")

    return value.strip()


def parse_bib(raw):
    """
    Best-effort parser for normal BibTeX entries.
    """
    match = re.match(
        r"@(\w+)\s*\{\s*([^,]+)\s*,(.*)\}\s*$",
        raw.strip(),
        re.DOTALL,
    )

    if not match:
        return {"raw": raw}

    entry = {
        "type": match.group(1).lower(),
        "key": match.group(2).strip(),
    }

    for field in split_fields(match.group(3)):
        if "=" not in field:
            continue

        name, value = field.split("=", 1)

        entry[name.strip().lower()] = clean_bib_value(value)

    return entry


def render_bib(entry):
    if "raw" in entry:
        return f"<code>{html.escape(entry['raw'])}</code>"

    parts = []

    author = entry.get("author")
    title = entry.get("title")
    venue = entry.get("journal") or entry.get("booktitle") or entry.get("publisher")
    year = entry.get("year")
    url = entry.get("url")
    doi = entry.get("doi")

    if author:
        authors = author.replace(
            " and ",
            ", ",
        )
        parts.append(html.escape(authors) + ".")

    if title:
        parts.append(f"<em>{html.escape(title)}</em>.")

    if venue:
        parts.append(html.escape(venue) + ".")

    if year:
        parts.append(html.escape(year) + ".")

    if doi:
        safe = html.escape(doi, quote=True)

        parts.append(f'<a href="https://doi.org/{safe}">' f"{html.escape(doi)}</a>.")

    elif url:
        parts.append(f'<a href="{html.escape(url, quote=True)}">' f"Link</a>.")

    return " ".join(parts)


def render_references(entries):
    if not entries:
        return ""

    items = "\n".join(
        f"        <li>{render_bib(parse_bib(entry))}</li>" for entry in entries
    )

    return (
        '<section class="references">\n'
        "    <h3>References</h3>\n"
        "    <ol>\n"
        f"{items}\n"
        "    </ol>\n"
        "</section>"
    )


def replace_list_environment(source, env, tag):
    pattern = re.compile(
        rf"\\begin\{{{env}\}}(.*?)\\end\{{{env}\}}",
        re.DOTALL,
    )

    def render(match):
        body = match.group(1).strip()

        items = re.split(
            r"\\item\s*",
            body,
        )

        items = [item.strip() for item in items if item.strip()]

        rendered = "\n".join(f"    <li>{item}</li>" for item in items)

        return f"\n\n<{tag}>\n" f"{rendered}\n" f"</{tag}>\n\n"

    return pattern.sub(render, source)


def latex_body_to_html(body):
    # Headings
    for command, (tag, css) in HEADINGS.items():
        body = replace_command(
            body,
            command,
            1,
            lambda text, tag=tag, css=css: f'\n\n<{tag} class="{css}">{text}</{tag}>\n\n',
        )

    # Inline formatting
    for command, (opening, closing) in INLINE.items():
        body = replace_command(
            body,
            command,
            1,
            lambda text, a=opening, b=closing: a + text + b,
        )

    # Links
    body = replace_command(
        body,
        "href",
        2,
        lambda url, text: f'<a href="{html.escape(url, quote=True)}">' f"{text}</a>",
    )

    # Figures
    body = replace_command(
        body,
        "blogfigure",
        2,
        lambda src, caption: (
            '\n\n<figure class="blog-figure">\n'
            f'    <img src="{html.escape(src, quote=True)}" alt="">\n'
            f"    <figcaption>{caption}</figcaption>\n"
            "</figure>\n\n"
        ),
    )

    for env, tag in LISTS.items():
        body = replace_list_environment(
            body,
            env,
            tag,
        )

    block_tags = tuple(f'<{tag} class="{css}">' for tag, css in HEADINGS.values()) + (
        '<figure class="blog-figure">',
        "<ol>",
        "<ul>",
    )

    blocks = []

    for block in re.split(r"\n\s*\n", body):
        block = block.strip()

        if not block:
            continue

        if block.startswith(block_tags):
            blocks.append(block)
        else:
            blocks.append(f'<p class="blog-paragraph">{block}</p>')

    return "\n\n".join(blocks)


def render_template(template, values):
    for name, value in values.items():
        template = re.sub(
            rf"\{{\{{\s*{re.escape(name)}\s*\}}\}}",
            lambda _: value,
            template,
        )

    remaining = re.findall(
        r"\{\{\s*\w+\s*\}\}",
        template,
    )

    if remaining:
        raise ValueError("Unfilled template placeholders: " + ", ".join(remaining))

    return template


def latex_to_html(tex, template):
    body = extract_document(tex)

    metadata, body = extract_commands(
        body,
        METADATA,
    )

    for field in ("written", "updated"):
        if not re.fullmatch(
            r"\d{4}-\d{2}-\d{2}",
            metadata[field],
        ):
            raise ValueError(f"\\{field} must use YYYY-MM-DD")

    bibliography, body = extract_bibliography(body)

    values = {
        **{key: html.escape(value) for key, value in metadata.items()},
        "content": latex_body_to_html(body),
        "references": render_references(bibliography),
    }

    return render_template(
        template,
        values,
    )


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "input",
        type=Path,
    )

    parser.add_argument(
        "-o",
        "--output",
        type=Path,
    )

    parser.add_argument(
        "--template",
        type=Path,
        default=TEMPLATE,
    )

    args = parser.parse_args()

    input_path = args.input if args.input.is_absolute() else ROOT / args.input

    template_path = (
        args.template if args.template.is_absolute() else ROOT / args.template
    )

    output_path = args.output if args.output else input_path.parent / "index.html"

    if not output_path.is_absolute():
        output_path = ROOT / output_path

    result = latex_to_html(
        input_path.read_text(encoding="utf-8"),
        template_path.read_text(encoding="utf-8"),
    )

    output_path.write_text(
        result.rstrip() + "\n",
        encoding="utf-8",
    )

    print(f"{input_path.relative_to(ROOT)} " f"-> {output_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
