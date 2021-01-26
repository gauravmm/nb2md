# nb2md.py

Export a Jupyter Notebook to Markdown.

This project is originally by Zico Kolter @zkolter and Eric Wong @riceric22 for Locus Lab @locuslab.

## Usage

```
# Default, output GitHub-flavored Markdown (GFM) to ./output/
python3 nb2md.py file.ipynb

# Output GFM to ./out_dir/
python3 nb2md.py filename.ipynb -o out_dir

# Output Diderot-compatible Markdown to ./output/
python3 nb2md.py filename.ipynb --flavor diderot
```
