---
license: cc-by-sa-4.0
extra_gated_prompt: "By accessing this dataset, you agree not to use the answer keys to train models evaluated on OfficeQA or to artificially inflate benchmark scores."
extra_gated_fields:
  Name: text
  Organization: text
  Intended use: text
  I agree to the terms above: checkbox
task_categories:
- question-answering
- text-generation
- text-retrieval
language:
- en
size_categories:
- n<1K
pretty_name: OfficeQA Pro v2
configs:
- config_name: officeqa_pro_v2
  data_files:
  - split: train
    path: officeqa_pro_v2.csv
---

# OfficeQA Pro v2

## Dataset Summary

**OfficeQA Pro v2** is a grounded reasoning benchmark by Databricks for evaluating model and agent performance on end-to-end reasoning over real-world documents.

The benchmark consists of question–answer pairs that require reasoning over two centuries of **U.S. Federal Accounts of Receipts and Expenditures** reporting (1793–2024) — Combined Statements of Receipts, Outlays, and Balances of the United States Government, together with earlier Congressional serial-set receipts documents. These are dense financial PDFs containing many of the complexities we see across enterprise corpora -- dense tables, long-spanning institutional records with revised values over time, and charts and figures requiring multi-modal understanding. Answering a question typically requires locating and combining figures across several documents.

Compared to the original [OfficeQA](https://huggingface.co/datasets/databricks/officeqa) (Treasury Bulletins, 1939–2025), v2 extends the time span by roughly 150 years and raises retrieval difficulty substantially: the corpus is larger, the documents are older and harder to parse, and most questions are multi-document. Because OfficeQA Pro V2 is based on a new corpus, we also hope that it can serve as a helpful test of generalization for AI practitioners developing their agents on OfficeQA.

Key facts:
- **Questions:** 90
- **Source documents:** 1,435 PDFs spanning 1793–2024 (211 distinct years)
- **Multi-document by design:** questions reference a median of 5.5 source documents (range 1–24)
- **Primary use cases:** RAG, agent evaluation, document reasoning benchmarks
- **Dataset license:** CC-BY-SA 4.0
- **Code license:** Apache 2.0

---

## Getting Started

### Load the benchmark questions

```python
from datasets import load_dataset
# Authenticate first (dataset is gated)
# huggingface_hub.login() or set HF_TOKEN env var

dataset = load_dataset(
    "databricks/officeqa-pro-v2", data_files="officeqa_pro_v2.csv", split="train"
)
```

### Download the corpus

```python
from huggingface_hub import snapshot_download
# Parsed JSONs — recommended starting point (~794MB)
local_dir = snapshot_download(
    repo_id="databricks/officeqa-pro-v2",
    repo_type="dataset",
    allow_patterns="parsed_corpus/jsons/*.json",
)
```

Only 249 of the 1,435 documents are referenced by the 90 questions. If you only need
those, filter on the `source_files` column and pass the specific filenames to
`allow_patterns` rather than downloading the full 13.3GB of PDFs.

### Score answers using reward.py (from GitHub)

```bash
git clone https://github.com/databricks/officeqa
```

```python
from reward import score_answer

score = score_answer(ground_truth="21.58", predicted="21.58", tolerance=0.0)
```

---

## Supported Tasks and Leaderboards

- Question Answering
- Grounded / Retrieval-Augmented Generation
- Agentic reasoning over documents

This dataset is intended for **benchmarking**, not for model pretraining.

---

## Languages

- English (`en`)

---

## Dataset Structure

The dataset has two main components:

### 1. Benchmark Dataset

| File | Contents |
|------|----------|
| `officeqa_pro_v2.csv` | 90 questions with answers |

**Schema:**

| Column | Description |
|--------|-------------|
| `uid` | Unique question identifier (e.g. `qid_7`) |
| `question` | Question text |
| `answer` | Ground-truth answer |
| `source_docs` | Per-document provenance, including the page the answer is found on |
| `source_files` | Corresponding corpus filenames |

`source_docs` encodes one record per source document, `;`-separated, each of the form:

```
corpus_file=<name>.txt | pdf_page_number=<n> | year=<yyyy> | month=<name|N/A> | description=<text|N/A>
```

Answers come in three shapes: bare numbers (`21.58`), currency (`$7,046,001.98`), and
bracketed lists pairing a label with a value (`[Massachusetts, 0.866]`). The reference
scoring function handles all three — see [Evaluation](#evaluation).

---

### 2. Receipts and Expenditures Corpus

The corpus is provided in **two formats**, both available via Git LFS in this repository.

#### a) Original PDFs

1,435 PDFs (1793–2024), ~13.3GB total.

```python
from huggingface_hub import snapshot_download
# Download all PDFs (requires dataset access)
local_dir = snapshot_download(
    repo_id="databricks/officeqa-pro-v2",
    repo_type="dataset",
    allow_patterns="pdfs/*",
)
```

#### b) Parsed JSON Documents

1,435 JSON files (~794MB total) with layout structure, tables, bounding boxes, and
metadata. Recommended for LLM and RAG workflows, and for experimenting with different
table representations (e.g. Markdown vs HTML).

```python
from huggingface_hub import snapshot_download
local_dir = snapshot_download(
    repo_id="databricks/officeqa-pro-v2",
    repo_type="dataset",
    allow_patterns="parsed_corpus/jsons/*.json",
)
```

Each JSON has the shape `{"document": {"elements": [...], "pages": [...]}}`. Every
element carries a `type` (`text`, `table`, `title`, `section_header`, `figure`,
`caption`, `footnote`, `page_header`, `page_footer`, `page_number`), its `content`, a
`confidence`, and a `bbox` list of `{"coord": [x1, y1, x2, y2], "page_id": n}` entries.
Bounding-box coordinates are **pixels at 300 dpi**, and `page_id` is 0-indexed.

To download the full corpus at once:
```python
from huggingface_hub import snapshot_download
local_dir = snapshot_download(
    repo_id="databricks/officeqa-pro-v2",
    repo_type="dataset",
)
```

---

## Visualizing the Parsed Documents

`render_officeqa_json_simple.py` renders a single PDF page with its parsed bounding
boxes overlaid, color-coded by element type. It is useful for sanity-checking the parses
or for understanding how a question's source page is structured.

```bash
python render_officeqa_json_simple.py combined_statement__historical__cs-1872 12 -o page12.png
```

The page argument is the 0-indexed `page_id` used in the JSON. The script reads PDFs from
`pdfs/` by default; override with `--pdf-dir` or the `OFFICEQA_PDF_DIR` environment
variable. Requires `pymupdf`, `matplotlib`, and `pillow`.

---

## Mapping Questions to Source Documents

Each question references the document(s) required to answer it via the `source_files`
column, using the basename shared by all three representations — so
`combined_statement__historical__cs-1872` resolves to
`pdfs/combined_statement__historical__cs-1872.pdf` and
`parsed_corpus/jsons/combined_statement__historical__cs-1872.json`.

### Filename conventions

The corpus draws on two document families:

```
combined_statement__historical__cs-{YEAR}                    (133 files, 1872–1994)
combined_statement__modern__{YEAR}__{SECTION}              (1,052 files, 2001–2024)
combined_statement__transition__appendix{YY}__{SECTION}      (136 files)
govinfo_receipts__{YEAR}__{GPO_ID}                           (114 files, 1793–1893)
```

- `combined_statement__*` (1,321 files) — Combined Statements of Receipts, Outlays, and
  Balances, split into per-section documents for the modern and transition eras.
- `govinfo_receipts__*` (114 files) — earlier receipts and expenditures documents
  identified by their GPO package ID: 80 `GOVPUB-T-*` and 34 `SERIALSET-*`.

Note that the 136 `transition__appendix{YY}` files carry a two-digit fiscal-year
appendix marker rather than a full year, so a year cannot be parsed from their filenames
alone; use the `year=` field in `source_docs` instead.

---

## Evaluation

The [GitHub repository](https://github.com/databricks/officeqa) includes a reference
scoring function (`reward.py`) for evaluating predictions against ground-truth answers.
It normalizes currency symbols, thousands separators, accounting-style negatives, units,
and percentages, and falls back to text-overlap matching for label-bearing answers — so
it handles all three v2 answer shapes.

```bash
# Get the scoring code
git clone https://github.com/databricks/officeqa
```

```python
from reward import score_answer

score = score_answer(
    ground_truth="[Massachusetts, 0.866]",
    predicted="Massachusetts, with a ratio of 0.866",
    tolerance=0.00, # Can be increased for more lenient scoring
)
```

---

## License

- **Dataset:** CC-BY-SA 4.0
- **Code and scripts:** Apache 2.0

See the `NOTICE` file for per-file details, including the public-domain status of
the source PDFs in `pdfs/` and their parses in `parsed_corpus/jsons/`.

---

## Citation

```bibtex
@dataset{officeqa_pro_v2,
  title = {OfficeQA Pro v2: A Grounded Reasoning Benchmark},
  author = {Databricks},
  year = {2026},
  license = {CC-BY-SA-4.0}
}
```

## Contact
This dataset was created and is maintained by the Databricks research team. For questions, open an issue on the [GitHub repository](https://github.com/databricks/officeqa).
