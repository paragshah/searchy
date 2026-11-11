from html.parser import HTMLParser


class NetscapeBookmarkParser(HTMLParser):
    """Parse Netscape bookmark HTML format (exported by browsers)."""

    def __init__(self):
        super().__init__()
        self.bookmarks = []
        self._current_href = None
        self._current_text = ""
        self._in_a_tag = False

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "a":
            attrs_dict = dict(attrs)
            href = attrs_dict.get("href", "")
            if href.lower().startswith(("http://", "https://")):
                self._current_href = href
                self._current_text = ""
                self._in_a_tag = True

    def handle_data(self, data):
        if self._in_a_tag:
            self._current_text += data

    def handle_endtag(self, tag):
        if tag.lower() == "a" and self._in_a_tag:
            self.bookmarks.append({
                "url": self._current_href,
                "title": self._current_text.strip(),
            })
            self._current_href = None
            self._current_text = ""
            self._in_a_tag = False


def parse_bookmark_html(html_content):
    """Parse a Netscape bookmark HTML file, return list of {url, title}."""
    parser = NetscapeBookmarkParser()
    parser.feed(html_content)
    return parser.bookmarks
