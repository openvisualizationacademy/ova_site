import re

from django import template
from django.utils.safestring import mark_safe
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name, TextLexer

register = template.Library()


@register.filter
def highlight_code(code, language):
    if not code:
        return ""
    try:
        lexer = get_lexer_by_name(language)
    except Exception:
        lexer = TextLexer()
    formatter = HtmlFormatter(cssclass="codehilite", wrapcode=True)
    return mark_safe(highlight(code, lexer, formatter))


@register.filter
def inline_code(text):
    if not text:
        return ""
    result = re.sub(r"`([^`]+)`", r"<code>\1</code>", str(text))
    return mark_safe(result)
