# Formatting Code for nb2md

import re
from collections import OrderedDict


class GFMFormatter(object):
    def __init__(self, external_image):
        self.external_image = external_image

    def finalize(self):
        self.external_image.write()

    def markdown(self, cell):
        cell_text = "\n".join(l.rstrip() for l in cell["source"])
        cell_text = re.sub(r'!\[(.*)\]\((.*)\)', 
                            r'{% include image.html img="\2" caption="\1"%}', 
                            cell_text)

        cell_text = re.sub(r'<center>(.*?)</center>',
                            r'<div class="center-text" markdown="1">\n\1\n</div>',
                            cell_text)

        cell_text = escape_symbols(cell_text)

        cell_text = re.sub(r'\\begin{equation}(.*?)\\end{equation}',
                            r'\n$$\1$$\n',
                            cell_text, flags=re.DOTALL)

        return cell_text

    def preamble(self, cell, download_link):
        return f"""---
layout: post
title: cell["source"][1][2:]
subtitle: cell["source"][2][2:]
author: cell["source"][3][2:]
img: cell["source"][4][2:]
---

[Download post as jupyter notebook]({download_link})

"""

    def source(self, cell):
        return f"""```python
{"".join(cell["source"])}
```"""

    def output(self, data):
        for mime, handler in cell_output_handlers.items():
            if mime in data:
                return handler(data[mime], self.external_image)


# Similar to GFM, but without a preamble and image substitution:
class DiderotFormatter(GFMFormatter):
    def markdown(self, cell):
        cell_text = "".join(cell["source"])
        cell_text = escape_symbols(cell_text)
        cell_text = re.sub(r'\\begin{equation}(.*?)\\end{equation}',
                            r'\n$$\1$$\n',
                            cell_text, flags=re.DOTALL)
        return cell_text

    def preamble(self, cell, download_link):
        return None


# Utility functions:
def escape_symbols(text):
    """ Replace \{  with \\{ within $'s.
        Replace * with \* within $'s """
    new_text = ""
    regex = r"[^\\]\$(?:[^\$\\]|\\.)*?\$"
    pos = 0
    m = re.search(regex, text[pos:])
    while m:
        new_text += text[pos:pos+m.start()]

        new_text += re.sub(r"(\\[\{\}\|]|[\*\_\|])", r"\\\1",m.group(0))
        pos += m.end()
        m = re.search(regex, text[pos:])
    new_text += text[pos:]
    return new_text

cell_output_handlers = OrderedDict([
    ("text/html",     lambda d, img: f"<div><small>{''.join(d)}</small></div>"),
    ("image/svg+xml", lambda d, img: img.process("image/svg+xml", d)),
    ("image/png",     lambda d, img: img.process("image/png", d)),
    ("text/plain",    lambda d, img: f"```\n{''.join(d)}\n```"),
    ("text",          lambda d, img: f"```\n{''.join(d)}\n```")])

Formatters = {
    "gfm": GFMFormatter,
    "diderot": DiderotFormatter
}
