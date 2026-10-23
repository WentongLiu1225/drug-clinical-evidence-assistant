# Drug Clinical Evidence Assistant

An evidence-grounded question-answering prototype for clinical research documents, built with Python, an LLM, and Streamlit.

The application focuses on the NATALEE trial of ribociclib in early breast cancer. Users can explore study design, patient populations, endpoints, and reported findings, with paragraph-level citations and source text for verification.

[中文说明](README_CHN.md) · [Project Report](docs/project_report.md)

## Features

- Ask free-text questions in English across the collection or within a selected document.
- Generate answers from retrieved passages with traceable citations.
- Inspect the source text supporting each response.
- Receive an explicit insufficient-evidence response when the retrieved passages cannot support an answer.
- Save answers, retrieved evidence, and model usage for review.

The collection contains four public documents covering one study, with selected text from an FDA announcement, the study design paper, a four-year outcomes report, and an HRQOL report. Tables, figures, and supplementary materials are excluded.

## Approach and Evaluation

**Document preparation → passage retrieval → LLM answer generation → evidence display**

Each passage retains its document ID, study ID, section, and paragraph ID. The current application uses keyword retrieval and supplies up to three passages to the answer model.

Development experiments compared keyword overlap, embedding-based semantic search, reciprocal rank fusion, and IDF-weighted retrieval. Keyword overlap was retained as the application default based on the small-scale evaluations; these results do not establish general superiority.

Retrieval and answer quality were evaluated separately. An eight-question regression check included AI-assisted evidence review, with author confirmation pending. Known retrieval failures are retained in the evaluation records.

See the [project report](docs/project_report.md) for methods, results, and failure analysis.

## Quick Start

Developed on macOS with Python 3.10.9.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Create a `.env` file in the project root:

```text
OPENAI_API_KEY=your_api_key_here
```

Keep `.env` out of version control. Answer generation requires access to the model configured in `scripts/ask_evidence.py` and incurs API charges.

Launch the application:

```bash
python -m streamlit run app.py --server.address 127.0.0.1
```

The application uses prepared passages and metadata; embeddings are not required for the default retrieval pipeline. Installation in a fresh environment has not yet been verified.

## Example Questions

Select the relevant document, then try:

- Was the NATALEE trial blinded?
- How long was ribociclib treatment planned to last?
- What was the median age of participants?
- What was the prespecified primary HRQOL endpoint?

## Scope and Limitations

This is a portfolio prototype, not a clinical decision tool. It does not search the web, recommend treatments, or rank drugs.

Coverage is limited to the selected passages. Retrieval can miss available evidence, and citations require verification. An insufficient-evidence response does not establish that the original publication lacks an answer.

Evaluation sets are small and include previously used development questions. Real-world utility and time savings have not been validated.