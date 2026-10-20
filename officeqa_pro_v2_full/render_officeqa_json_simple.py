"""Render one page of an officeqa PDF with stage-1 bboxes overlaid.

The parsed JSONs in this repo (`parsed_corpus/jsons/`) carry bboxes in pixel
coordinates at 300 dpi, so a page rendered at DPI=300 lines up 1:1 with them.
The source PDFs ship alongside them in `pdfs/` (git-lfs), one per JSON.

Usage:
    python render_officeqa_json_simple.py <doc-slug> <page> [-o out.png]

    # 0-indexed page_id, matching the JSON
    python render_officeqa_json_simple.py combined_statement__historical__cs-1872 12
"""
import argparse
import json
import os

import fitz  # PyMuPDF
import matplotlib.patches as patches
import matplotlib.pyplot as plt
from PIL import Image

# --- config -----------------------------------------------------------------
DPI = 300  # must match the dpi the JSON bboxes were computed at

REPO_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_DIR = os.path.join(REPO_DIR, 'parsed_corpus', 'jsons')
PDF_DIR = os.environ.get('OFFICEQA_PDF_DIR', os.path.join(REPO_DIR, 'pdfs'))

TYPE_COLORS = {
    'text': 'blue',
    'figure': 'orange',
    'table': 'green',
    'title': 'red',
    'caption': 'brown',
    'section_header': 'purple',
    'page_footer': 'cyan',
    'page_header': 'magenta',
    'page_number': 'goldenrod',
    'footnote': 'pink',
}


def plot_page_with_bboxes(pix, page_elements, out_path=None, figsize=(15, 20)):
    img = Image.frombytes('RGB', [pix.width, pix.height], pix.samples)
    fig, ax = plt.subplots(1, figsize=figsize)
    ax.imshow(img)

    for idx, element in enumerate(page_elements):
        x1, y1, x2, y2 = element['bbox'][0]['coord']
        element_type = element['type']
        color = TYPE_COLORS.get(element_type, 'gray')
        rect = patches.Rectangle(
            (x1, y1), x2 - x1, y2 - y1,
            linewidth=2, edgecolor=color, facecolor='none', alpha=0.8,
        )
        ax.add_patch(rect)
        ax.text(
            x1, y1 - 5, f'{idx}: {element_type}',
            color=color, fontsize=10,
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7),
            verticalalignment='bottom',
        )

    ax.axis('off')
    plt.tight_layout()
    if out_path:
        plt.savefig(out_path, dpi=100, bbox_inches='tight')
        print(f'Wrote {out_path}')
    else:
        plt.show()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        'slug',
        help='document basename, e.g. combined_statement__historical__cs-1872',
    )
    parser.add_argument('page', type=int, help='0-indexed page_id (matches the JSON)')
    parser.add_argument('-o', '--out', help='save to this PNG instead of showing a window')
    parser.add_argument('--pdf-dir', default=PDF_DIR, help=f'default: {PDF_DIR}')
    args = parser.parse_args()

    # Tolerate the `a/b/c` form as well as the `a__b__c` basename used on disk.
    slug = args.slug.replace('/', '__').removesuffix('.pdf').removesuffix('.json')
    pdf_path = os.path.join(args.pdf_dir, f'{slug}.pdf')
    json_path = os.path.join(JSON_DIR, f'{slug}.json')

    # Render PDF page
    pdf_document = fitz.open(pdf_path)
    page = pdf_document[args.page]
    zoom = DPI / 72
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)

    # Get elements for the page
    with open(json_path) as f:
        json_data = json.load(f)
    page_elements = [
        e for e in json_data['document']['elements']
        if any(b['page_id'] == args.page for b in e['bbox'])
    ]
    print(f'Found {len(page_elements)} elements on page {args.page}')
    print(f'PDF page is {pix.width}x{pix.height}px at {DPI} dpi')

    plot_page_with_bboxes(pix, page_elements, out_path=args.out)


if __name__ == '__main__':
    main()
