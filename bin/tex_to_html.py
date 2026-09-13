#!/usr/bin/env python3

import argparse
import html
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BLOG_DIR = ROOT / "blog"
TEMPLATE_PATH = BLOG_DIR / "_template.html"

METADATA = (
    "blogtitle",
    "blogsubtitle",
    "written",
    "updated",
)

HEADINGS = {
    "section": ("h2", "blog-section"),
    "subsection": ("h3", "blog-subsection"),
}

INLINE = {
    "textit": ("<em>", "</em>"),
    "emph": ("<em>", "</em>"),
    "textbf": ("<strong>", "</strong>"),
}


def extract_document(tex: str) -> str:
    match = re.search(
        r"\\begin\{document\}(.*?)\\end\{document\}",
        tex,
        re.DOTALL,
    )

    if not match:
        raise ValueError(
            r"Could not find \begin{document}...\end{document}"
        )

    return match.group(1).strip()


def read_braced(source: str, start: int):
    """
    Read a {...} group starting at source[start].
    """

    if start >= len(source) or source[start] != "{":
        raise ValueError("Expected '{'")

    depth = 0

    for i in range(start, len(source)):
        if source[i] == "{":
            depth += 1

        elif source[i] == "}":
            depth -= 1

            if depth == 0:
                return source[start + 1:i], i + 1

    raise ValueError("Unmatched '{'")


def read_args(
    source: str,
    start: int,
    count: int,
):
    """
    Read count braced arguments, allowing whitespace between them.
    """

    args = []
    i = start

    for _ in range(count):
        while (
            i < len(source)
            and source[i].isspace()
        ):
            i += 1

        if (
            i >= len(source)
            or source[i] != "{"
        ):
            return None

        arg, i = read_braced(
            source,
            i,
        )

        args.append(arg)

    return args, i


def replace_command(
    source: str,
    command: str,
    nargs: int,
    render,
) -> str:
    """
    Replace every occurrence of a LaTeX command.

    Example:

        replace_command(
            source,
            "emph",
            1,
            lambda text: f"<em>{text}</em>",
        )
    """

    token = "\\" + command
    output = []
    i = 0

    while True:
        pos = source.find(
            token,
            i,
        )

        if pos == -1:
            output.append(
                source[i:]
            )
            break

        output.append(
            source[i:pos]
        )

        parsed = read_args(
            source,
            pos + len(token),
            nargs,
        )

        if parsed is None:
            output.append(token)
            i = pos + len(token)
            continue

        args, i = parsed

        output.append(
            render(*args)
        )

    return "".join(output)


def extract_metadata(source: str):
    """ 
    Extract:
        blogtitle{...}
        blogsubtitle{...}
        written{YYYY-MM-DD}
        updated{YYYY-MM-DD}
    and remove them from the article body.
    """

    metadata = {}
    body = source

    for command in METADATA:
        token = "\\" + command
        pos = body.find(token)

        if pos == -1:
            raise ValueError(
                f"Missing required metadata command: "
                f"\\{command}{{...}}"
            )

        parsed = read_args(
            body,
            pos + len(token),
            1,
        )

        if parsed is None:
            raise ValueError(
                f"Expected '{{' after \\{command}"
            )

        (value,), end = parsed

        metadata[command] = (
            value.strip()
        )

        body = (
            body[:pos]
            + body[end:]
        )

    for command in (
        "written",
        "updated",
    ):
        if not re.fullmatch(
            r"\d{4}-\d{2}-\d{2}",
            metadata[command],
        ):
            raise ValueError(
                f"\\{command} must use YYYY-MM-DD"
            )

    return metadata, body.strip()


def latex_body_to_html(body: str) -> str:
    # Headings.
    for command, (
        tag,
        css_class,
    ) in HEADINGS.items():

        body = replace_command(
            body,
            command,
            1,
            lambda text,
            tag=tag,
            css=css_class:
                (
                    f'\n\n'
                    f'<{tag} class="{css}">'
                    f'{text}'
                    f'</{tag}>'
                    f'\n\n'
                ),
        )

    # Inline formatting.
    for command, (
        open_tag,
        close_tag,
    ) in INLINE.items():

        body = replace_command(
            body,
            command,
            1,
            lambda text,
            opening=open_tag,
            closing=close_tag:
                opening
                + text
                + closing,
        )

    # Links.
    body = replace_command(
        body,
        "href",
        2,
        lambda url, text:
            (
                f'<a href="'
                f'{html.escape(url, quote=True)}'
                f'">{text}</a>'
            ),
    )

    # Figures.
    body = replace_command(
        body,
        "blogfigure",
        2,
        lambda src, caption:
            (
                "\n\n"
                '<figure class="blog-figure">\n'
                f'    <img src="'
                f'{html.escape(src, quote=True)}'
                f'" alt="">\n'
                "    <figcaption>\n"
                f"        {caption}\n"
                "    </figcaption>\n"
                "</figure>"
                "\n\n"
            ),
    )

    block_prefixes = tuple(
        f'<{tag} class="{css}">'
        for tag, css
        in HEADINGS.values()
    ) + (
        '<figure class="blog-figure">',
    )

    output = []

    for block in re.split(
        r"\n\s*\n",
        body,
    ):
        block = block.strip()

        if not block:
            continue

        if block.startswith(
            block_prefixes
        ):
            output.append(block)

        else:
            output.append(
                f'<p class="blog-paragraph">'
                f'{block}'
                f'</p>'
            )

    return "\n\n".join(output)


def render_template(
    template: str,
    metadata: dict,
    content: str,
) -> str:
    values = {
        **{
            key: html.escape(value)
            for key, value
            in metadata.items()
        },
        "content": content,
    }

    for name, value in values.items():
        template = re.sub(
            rf"\{{\{{\s*"
            rf"{re.escape(name)}"
            rf"\s*\}}\}}",
            lambda _: value,
            template,
        )

    remaining = re.findall(
        r"\{\{\s*"
        r"[A-Za-z_][A-Za-z0-9_]*"
        r"\s*\}\}",
        template,
    )

    if remaining:
        raise ValueError(
            "Unfilled template placeholder(s): "
            + ", ".join(remaining)
        )

    return template


def latex_to_html(
    tex: str,
    template: str,
) -> str:
    metadata, body = extract_metadata(
        extract_document(tex)
    )

    content = latex_body_to_html(
        body
    )

    return render_template(
        template,
        metadata,
        content,
    )


def rooted(path: Path) -> Path:
    if path.is_absolute():
        return path

    return ROOT / path


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Convert a LaTeX blog post "
            "into HTML."
        )
    )

    parser.add_argument(
        "input",
        type=Path,
        help=(
            "Blog source, e.g. "
            "blog/lattices/1/main.tex"
        ),
    )

    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help=(
            "Output path. Defaults to "
            "index.html beside the input."
        ),
    )

    parser.add_argument(
        "--template",
        type=Path,
        default=TEMPLATE_PATH,
        help=(
            "HTML template. Defaults to "
            "blog/_template.html."
        ),
    )

    args = parser.parse_args()

    input_path = rooted(
        args.input
    )

    template_path = rooted(
        args.template
    )

    if args.output:
        output_path = rooted(
            args.output
        )
    else:
        output_path = (
            input_path.parent
            / "index.html"
        )

    tex = input_path.read_text(
        encoding="utf-8"
    )

    template = template_path.read_text(
        encoding="utf-8"
    )

    converted = latex_to_html(
        tex,
        template,
    )

    output_path.write_text(
        converted.rstrip() + "\n",
        encoding="utf-8",
    )

    print(
        f"{input_path.relative_to(ROOT)} "
        f"-> "
        f"{output_path.relative_to(ROOT)}"
    )


if __name__ == "__main__":
    main()
