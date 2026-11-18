"""Conservative HTML-to-text parser retaining headings, tables and footnote markers.

The output is for manual research review, not validated clinical interpretation.
"""
from html.parser import HTMLParser
import re

SPACE = re.compile(r"[ \t\r\f\v]+")
SKIP = {"script", "style", "nav", "footer", "header", "noscript", "svg"}
BLOCK = {"p", "div", "section", "article", "ul", "ol", "li", "blockquote"}
HEADINGS = {"h1", "h2", "h3", "h4", "h5", "h6"}

class StructuredHTMLExtractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.skip_stack: list[str] = []
        self.table_depth = 0
        self.cell_depth = 0
        self.row_depth = 0

    def _newline(self, count: int = 1):
        self.parts.append("\n" * count)

    def handle_starttag(self, tag, attrs):
        if self.skip_stack:
            if tag in SKIP:
                self.skip_stack.append(tag)
            return
        if tag in SKIP:
            self.skip_stack.append(tag)
            return
        if tag in HEADINGS:
            self._newline(2)
            self.parts.append("#" * int(tag[1]) + " ")
        elif tag == "table":
            self.table_depth += 1
            self._newline(2)
            self.parts.append("[TABLE]\n")
        elif tag == "tr" and self.table_depth:
            self.row_depth += 1
            self._newline()
        elif tag in {"td", "th"} and self.table_depth:
            if self.cell_depth == 0:
                self.parts.append(" | ")
            self.cell_depth += 1
        elif tag == "br":
            self._newline()
        elif tag == "li":
            self._newline()
            self.parts.append("- ")
        elif tag in BLOCK:
            self._newline()

    def handle_endtag(self, tag):
        if self.skip_stack:
            if tag == self.skip_stack[-1]:
                self.skip_stack.pop()
            return
        if tag in HEADINGS or tag in {"p", "li"}:
            self._newline(2)
        elif tag == "table" and self.table_depth:
            self.parts.append("\n[/TABLE]")
            self._newline(2)
            self.table_depth -= 1
        elif tag == "tr" and self.row_depth:
            self._newline()
            self.row_depth -= 1
        elif tag in {"td", "th"} and self.cell_depth:
            self.cell_depth -= 1
        elif tag in BLOCK:
            self._newline()

    def handle_data(self, data):
        if not self.skip_stack:
            self.parts.append(data)

    def get_text(self):
        raw = "".join(self.parts)
        lines = [SPACE.sub(" ", line).strip() for line in raw.splitlines()]
        return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()

def extract_structured_text(html: str) -> str:
    parser = StructuredHTMLExtractor()
    parser.feed(html)
    parser.close()
    return parser.get_text()
