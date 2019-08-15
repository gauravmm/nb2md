#!/usr/bin/env python

import argparse
import json
from collections import OrderedDict
from pathlib import Path


class ExternalImage(object):
    def __init__(self, flavour="gfm"):
        self.images = []

    def.process(self, mimetype, imagedata):
        if mimetype == "image/svg+xml":
            file = f"output_{len(self.images)}.svg"
            # Prepare the svg file for writing:
            self.images.append((file, imagedata.encode()))
            return f'{{% include image.html img="{file}" %}}'

        elif mimetype == "image/png":
            # Inline
            return f'<div><img src="data:image/png;base64, {}"></div>\n'.format(imagedata))


def main(args):
    data = json.loads(args.nb_file.read_text())
    external_image = ExternalImage(flavour=args.flavour)

    output_file = parser.output if parser.output else args.nb_file.with_suffix(".md")
    if output_file.suffix != ".md":
        output_file = output_file / args.nb_file.with_suffix(".md")
    output_file.mkdir(parents=True, exist_ok=True)

    output = []

    for cell in data["cells"]:
        if cell["cell_type"] == "markdown":
            output.append(cell_markdown(cell))

        elif cell["cell_type"] == "code":
            if len(cell["source"]) == 0:
                continue
            elif cell["source"][0].startswith("### PREAMBLE"):
                cell_preamble(cell, output_file.with_suffix(".tar.gz"))
            else:
                output.append(cell_source(cell))

                if "outputs" in cell:
                    # Find the output types we want and select the first matching type.
                    output_types_index = [t, output_types_index[t]
                        for t in ["display_data", "execute_result", "stream"]
                        if t in { out["output_type"]:i for i, out in enumerate(cell["outputs"]) }]

                    try:
                        output_cell_type, output_cell_index = output_types_index
                    except IndexError:
                        continue

                    output.append(cell_output_markdown(cell["outputs"][output_cell_index]["data"], external_image))

    output_file.write_text("\n".join((o for o in output if o is not None)))
    external_image.write()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--svg_scale", type=float, default=0.75)
    parser.add_argument("nb_file", type=Path, help="jupyter notebook file")
    parser.add_argument(["--output", "-o"], default=Path("output/"), type=Path, help="output path, will be clobbered")

    flavor = parser.add_mutually_exclusive_group(required=False)
    flavor.add_argument("--gfm", metavar="flavor", type="store_const", const="gfm", help="GitHub flavored markdown")
    flavor.add_argument("--diderot", metavar="flavor", type="store_const", const="diderot", help="Diderot-compatible markdown")

    main(parser.parse_args())
