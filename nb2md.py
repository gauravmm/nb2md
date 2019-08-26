#!/usr/bin/env python3

import argparse
import base64
import json
from collections import OrderedDict
from pathlib import Path

from formatting import Formatters


class ExternalImage(object):
    def __init__(self, basedir=Path("."), flavor="gfm"):
        self.flavor = flavor
        self.basedir = basedir
        self.images = []

    def process(self, mimetype, imagedata):
        if mimetype == "image/svg+xml":
            filename = f"output_{len(self.images)}.svg"
            # Prepare the svg file for writing:
            assert isinstance(imagedata, list)
            self.images.append((filename, "\n".join(imagedata).encode()))
            if self.flavor == "gfm":
                return f'{{% include image.html img="{filename}" %}}'
            else:
                return f'![]({filename})'

        elif mimetype == "image/png":
            # Inline
            if self.flavor == "gfm":
                return f'<div><img src="data:image/png;base64, {imagedata}"></div>'
            else:
                filename = f"output_{len(self.images)}.png"
                self.images.append((filename, base64.b64decode(imagedata )))
                return f'![]({filename})'

    def write(self):
        for fn, data in self.images:
            (self.basedir / fn).write_bytes(data)

def main(args):
    data = json.loads(args.nb_file.read_text())

    output_file = args.output if args.output else args.nb_file.with_suffix(".md")
    if output_file.suffix != ".md":
        output_file = output_file / args.nb_file.with_suffix(".md").name
    # Ensure parent exists
    output_file.parent.mkdir(parents=True, exist_ok=True)

    formatter = Formatters[args.flavor](ExternalImage(basedir=output_file.parent, flavor=args.flavor))

    output = []

    for cell in data["cells"]:
        if cell["cell_type"] == "markdown":
            output.append(formatter.markdown(cell))

        elif cell["cell_type"] == "code":
            if len(cell["source"]) == 0:
                continue
            elif cell["source"][0].startswith("### PREAMBLE"):
                formatter.preamble(cell, output_file.with_suffix(".tar.gz"))
            else:
                output.append(formatter.source(cell))

                if "outputs" in cell:
                    # Find the output types we want and select the first matching type.
                    output_types_lookup = { out["output_type"]:i for i, out in enumerate(cell["outputs"]) }
                    output_types_index = [(t, output_types_lookup[t]) for t in ["display_data", "execute_result", "stream"] if t in output_types_lookup]

                    try:
                        output_cell_type, output_cell_index = output_types_index[0]
                    except IndexError:
                        continue

                output.append(formatter.output(cell["outputs"][output_cell_index]["text" if output_cell_type == "stream" else "data"]))

    output_file.write_text("\n\n".join(filter(lambda o: o is not None, output)) + "\n")
    formatter.finalize()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("nb_file", type=Path, help="jupyter notebook file")
    parser.add_argument("--output", "-o", default=Path("output/"), type=Path, help="output path, will be clobbered")
    parser.add_argument("--flavor", choices=["gfm", "diderot"], default="gfm", help="output flavor, select between gfm (GitHub flavored markdown) and diderot")

    main(parser.parse_args())
