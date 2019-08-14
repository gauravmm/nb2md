#!/usr/bin/env python

import os
import re
import argparse
import json
import glob
import shutil

# Eric: PIL images for PNG cell outputs
from PIL import Image
from io import BytesIO
import base64

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

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--svg_scale", type=float, default=0.75)
    parser.add_argument("nb_file", type=str, help="jupyter notebook file")
    args = parser.parse_args()

    base, ext = os.path.splitext(args.nb_file)

    with open(args.nb_file) as f:
        raw_data = f.read()
        f.seek(0)
        data = json.load(f)

    output = open(base + ".md", "w")

    output_idx = 0

    for cell in data["cells"]:
        if cell["cell_type"] == "markdown":
            cell_text = "".join(cell["source"]) + "\n"
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


            output.write(cell_text + "\n")

        elif cell["cell_type"] == "code":
            print(len(cell["source"]))
            if len(cell["source"]) > 0 and cell["source"][0].startswith("### PREAMBLE"):
                output.write("---\nlayout: post\ntitle: {}subtitle: {}author: {}img: {}---\n\n[Download post as jupyter notebook]({})\n\n"\
                    .format(cell["source"][1][2:], cell["source"][2][2:], 
                            cell["source"][3][2:], cell["source"][4][2:], base + ".tar.gz"))
            else:
                cell_text = "".join(cell["source"]) + "\n"
                output.write("\n```python\n" + cell_text + "```\n\n")

                if "outputs" in cell:
                    output_types = {out["output_type"]:i 
                                    for i,out in enumerate(cell["outputs"])}
                    if "display_data" in output_types:
                        # write svg to file and link to the svg
                        print("here")
                        cell_output = cell["outputs"][output_types["display_data"]]
                        if "image/svg+xml" in cell_output["data"]:
                            with open("output_{}.svg".format(output_idx), "w") as f_svg:
                                f_svg.writelines(cell_output["data"]["image/svg+xml"])
                        output.write('\n{{% include image.html img="output_{}.svg" %}}\n\n'.format(output_idx))
                        output_idx += 1

                    elif "execute_result" in output_types:
                        # print execution results (mainly tables)
                       
                        cell_output = cell["outputs"][output_types["execute_result"]]
                        if "text/html" in cell_output["data"]:
                            cell_output_text = "".join(cell_output["data"]["text/html"])
                            output.write("\n<div><small>" + cell_output_text + "</small></div>\n")
                        elif "image/svg+xml" in cell_output["data"]:
                            with open("output_{}.svg".format(output_idx), "w") as f_svg:
                                f_svg.writelines(cell_output["data"]["image/svg+xml"])
                            output.write('\n{{% include image.html img="output_{}.svg" %}}\n\n'.format(output_idx))
                            output_idx += 1
                        elif "image/png" in cell_output["data"]: 
                            cell_data = cell_output["data"]["image/png"]
                            output.write('\n<div><img src="data:image/png;base64, {}"></div>\n'.format(cell_data))
                        elif "text/plain" in cell_output["data"]:
                            cell_output_text = "".join(cell_output["data"]["text/plain"])
                            output.write("<pre>\n" + cell_output_text + "\n</pre>\n\n")

                    elif "stream" in output_types:
                        cell_output = cell["outputs"][output_types["stream"]]
                        cell_output_text = "".join(cell_output["text"])
                        output.write("<pre>\n" + cell_output_text + "</pre>\n\n")

    output.close()

    ## create the notebook directory and 
    all_files = glob.glob("**/*", recursive=True)
    occuring_files = [f for f in all_files if raw_data.find(f) >= 0 and os.path.isfile(f) and os.stat(f).st_size < 20*1024*1024]
    if os.path.exists(base):
        shutil.rmtree(base)
    os.makedirs(base)
    for f in occuring_files + [base + ".ipynb"]:
        shutil.copy(f, base)
    os.system("tar -czf {0}.tar.gz {0}".format(base))

    base_post = os.path.split(os.getcwd())[1]
    shutil.move(base + ".md", "../_posts/" + base_post + ".md")


