import json

with open('notebook.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

TARGET = '# Install dependencies (run once)'
OMP_FIX = 'os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"  # Fix OpenMP conflict on Windows+Conda\n\n'

patched = 0
for cell in nb['cells']:
    if cell['cell_type'] != 'code':
        continue
    src = cell['source']
    # Normalise to string for searching
    src_str = ''.join(src) if isinstance(src, list) else src
    if TARGET in src_str and OMP_FIX not in src_str:
        # Insert OMP fix right before 'import fitz'
        marker = 'import fitz  # PyMuPDF'
        new_str = src_str.replace(marker, OMP_FIX + marker, 1)
        cell['source'] = new_str if isinstance(src, str) else list(new_str)
        patched += 1
        break

with open('notebook.ipynb', 'w', encoding='utf-8') as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print(f'Patched {patched} cell(s). KMP_DUPLICATE_LIB_OK fix injected before torch/transformers imports.')
