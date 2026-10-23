# Load our collected documents and their source information.

import json
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent.parent

DOCUMENT_IDS = [
    "fda_ribociclib_2024",
    "natalee_design_2023",
    "natalee_4year_2025",
    "natalee_qol_2025",
]


def load_documents():
    all_paragraphs = []
    metadata_by_id = {}
    seen_paragraph_ids = set()

    for document_id in DOCUMENT_IDS:
        metadata_path = (
            PROJECT_DIR / "data/raw" / f"{document_id}_metadata.json"
        )
        paragraphs_path = (
            PROJECT_DIR / "data/processed"
            / f"{document_id}_paragraphs.json"
        )

        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        paragraphs = json.loads(paragraphs_path.read_text(encoding="utf-8"))

        if metadata["document_id"] != document_id:
            raise ValueError(f"Metadata document ID mismatch: {document_id}")

        if not paragraphs:
            raise ValueError(f"No paragraphs found: {document_id}")

        metadata_by_id[document_id] = metadata

        for paragraph in paragraphs:
            paragraph_id = paragraph["paragraph_id"]

            if paragraph["document_id"] != document_id:
                raise ValueError(f"Wrong document ID: {paragraph_id}")

            if paragraph["study_id"] != metadata["study_id"]:
                raise ValueError(f"Study ID mismatch: {paragraph_id}")

            if paragraph_id in seen_paragraph_ids:
                raise ValueError(f"Duplicate paragraph ID: {paragraph_id}")

            if not paragraph["text"].strip():
                raise ValueError(f"Empty paragraph: {paragraph_id}")

            seen_paragraph_ids.add(paragraph_id)
            all_paragraphs.append(paragraph)

    return all_paragraphs, metadata_by_id


def main():
    paragraphs, metadata_by_id = load_documents()

    print(f"Documents loaded: {len(metadata_by_id)}")
    print(f"Paragraphs loaded: {len(paragraphs)}")

    study_ids = set()

    for document_id, metadata in metadata_by_id.items():
        study_ids.add(metadata["study_id"])
        paragraph_count = 0

        for paragraph in paragraphs:
            if paragraph["document_id"] == document_id:
                paragraph_count += 1

        print(f"\nDocument: {document_id}")
        print(f"Study: {metadata['study_id']}")
        print(f"Paragraphs: {paragraph_count}")
        print(f"Title: {metadata['title']}")

    print(f"\nUnique studies: {len(study_ids)}")


if __name__ == "__main__":
    main()