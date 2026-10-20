"""
Markdown to HTML rendering for the blog posts.

Uses a CommonMark compliant parser (the same flavor written by the editor) with
the GitHub extensions most used in posts: tables, strikethrough, task lists and
footnotes. Code blocks with a language (```python) are highlighted by Pygments.
Raw HTML is allowed, since only the site's staff can write posts.
"""
from functools import lru_cache

from markdown_it import MarkdownIt
from markdown_it.token import Token
from mdit_py_plugins.anchors import anchors_plugin
from mdit_py_plugins.footnote import footnote_plugin
from mdit_py_plugins.tasklists import tasklists_plugin
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name
from pygments.util import ClassNotFound


def _highlight_code(code, language, _attrs):
    if not language:
        return ''  # Uses markdown-it's default (escaped) rendering

    try:
        lexer = get_lexer_by_name(language)
    except ClassNotFound:
        return ''

    return highlight(code, lexer, HtmlFormatter(nowrap=True))


def _split_paragraph_lines(state):
    """
    The WYSIWYG mode of the editor saves consecutive paragraphs one per line,
    without the blank line between them that Markdown expects, and shows each
    line as its own paragraph. To publish what was seen in the editor, the lines
    of a paragraph are split into separate paragraphs here as well.
    Paragraphs inside tight lists (rendered without <p>) are left as they are.
    """
    tokens = []
    index = 0
    while index < len(state.tokens):
        token = state.tokens[index]
        is_paragraph = (
            token.type == 'paragraph_open'
            and not token.hidden
            and index + 2 < len(state.tokens)
            and state.tokens[index + 1].type == 'inline'
        )
        if not is_paragraph:
            tokens.append(token)
            index += 1
            continue

        inline, paragraph_close = state.tokens[index + 1], state.tokens[index + 2]
        lines = [[]]
        for child in inline.children or []:
            if child.type == 'softbreak':
                lines.append([])
            else:
                lines[-1].append(child)

        for line in lines:
            if not line:
                continue
            line_inline = Token('inline', '', 0, children=line, map=inline.map, level=inline.level)
            tokens.extend([token, line_inline, paragraph_close])
        index += 3

    state.tokens = tokens


def _render_table_open(self, tokens, idx, options, env):
    # Tables scroll horizontally on small screens instead of breaking the layout
    return '<div class="table-responsive"><table class="table">\n'


def _render_table_close(self, tokens, idx, options, env):
    return '</table></div>\n'


def _render_image(self, tokens, idx, options, env):
    tokens[idx].attrSet('loading', 'lazy')
    return self.image(tokens, idx, options, env)


@lru_cache(maxsize=1)
def get_markdown_parser():
    parser = (
        MarkdownIt('commonmark', {'html': True, 'typographer': True, 'highlight': _highlight_code})
        .enable(['table', 'strikethrough', 'replacements', 'smartquotes'])
        .use(footnote_plugin)
        .use(tasklists_plugin)
        .use(anchors_plugin, min_level=2, max_level=4)
    )
    parser.core.ruler.push('split_paragraph_lines', _split_paragraph_lines)
    parser.add_render_rule('table_open', _render_table_open)
    parser.add_render_rule('table_close', _render_table_close)
    parser.add_render_rule('image', _render_image)
    return parser


def render_markdown(text):
    return get_markdown_parser().render(text or '')
