# Answer questions using keyword retrieval and cited evidence.

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from load_documents import load_documents
from search_keyword import search_paragraphs


PROJECT_DIR = Path(__file__).resolve().parent.parent

PROMPT_PATH = PROJECT_DIR / "prompts" / "answer_v1.txt"
RUNS_DIR = PROJECT_DIR / "runs"

ANSWER_MODEL = "gpt-6.1-sol"
TOP_K = 3
RUN_VERSION = "answer_keyword_v2"
RETRIEVAL_METHOD = "keyword_overlap"


def answer_question(question, document_id=None):
    question = question.strip()

    if not question:
        raise ValueError("Please enter a question.")

    paragraphs, metadata_by_id = load_documents()

    if not paragraphs:
        raise ValueError("No paragraphs loaded.")

    # None means search all collected documents.
    if document_id is not None:
        if document_id not in metadata_by_id:
            raise ValueError(f"Unknown document ID: {document_id}")

        selected_paragraphs = []

        for paragraph in paragraphs:
            if paragraph["document_id"] == document_id:
                selected_paragraphs.append(paragraph)

        paragraphs = selected_paragraphs

        metadata_by_id = {
            document_id: metadata_by_id[document_id]
        }

        if not paragraphs:
            raise ValueError(
                f"No paragraphs found for document: {document_id}"
            )

    instructions = PROMPT_PATH.read_text(encoding="utf-8")

    if not instructions.strip():
        raise ValueError("The prompt file is empty.")

    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()

    # Search the selected collection locally.
    results = search_paragraphs(
        question,
        paragraphs,
        top_k=TOP_K,
    )

    evidence = []
    retrieval_log = []

    for result in results:
        paragraph = result["paragraph"]
        metadata = metadata_by_id[paragraph["document_id"]]

        passage = {
            "paragraph_id": paragraph["paragraph_id"],
            "document_id": paragraph["document_id"],
            "study_id": paragraph["study_id"],
            "section": paragraph["section"],
            "source_title": metadata["title"],
            "source_url": metadata["source_url"],
            "text": paragraph["text"],
        }
        evidence.append(passage)

        retrieval_log.append({
            "paragraph_id": paragraph["paragraph_id"],
            "document_id": paragraph["document_id"],
            "keyword_score": result["score"],
            "matched_words": result["matched_words"],
        })

    # Only the question and retrieved evidence go to the answer model.
    model_input = json.dumps(
        {
            "question": question,
            "evidence_passages": evidence,
        },
        ensure_ascii=False,
        indent=2,
    )

    answer_response = None
    usage = None

    if evidence:
        env_path = PROJECT_DIR / ".env"

        if not env_path.exists():
            raise FileNotFoundError("Missing project .env file.")

        load_dotenv(env_path, override=True)
        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key or not api_key.strip():
            raise ValueError("OPENAI_API_KEY is missing or empty.")

        client = OpenAI(
            api_key=api_key,
            timeout=60.0,
            max_retries=0,
        )

        answer_response = client.responses.create(
            model=ANSWER_MODEL,
            instructions=instructions,
            input=model_input,
            reasoning={"effort": "low"},
            max_output_tokens=2000,
            store=False,
        )

        answer = answer_response.output_text
        usage = answer_response.usage

    else:
        # Do not call the answer model when retrieval returns nothing.
        answer = (
            "No keyword-matched passages were retrieved. "
            "The current retrieval does not provide enough evidence "
            "to answer this question. This does not prove that the "
            "answer is absent from the selected documents."
        )

    elapsed = time.perf_counter() - started

    paragraph_files = []
    document_metadata = []

    for current_document_id, metadata in metadata_by_id.items():
        paragraph_path = (
            PROJECT_DIR / "data" / "processed"
            / f"{current_document_id}_paragraphs.json"
        )

        paragraph_files.append(
            paragraph_path.relative_to(PROJECT_DIR).as_posix()
        )
        document_metadata.append(metadata)

    timestamp = datetime.now(timezone.utc)
    run_name = timestamp.strftime("%Y%m%dT%H%M%S_%fZ")
    log_path = RUNS_DIR / f"{RUN_VERSION}_{run_name}.json"

    answer_model_called = answer_response is not None
    answer_model_returned = None
    raw_answer_response = None
    response_status = "not_called_no_evidence"

    if answer_model_called:
        answer_model_returned = answer_response.model
        raw_answer_response = answer_response.model_dump(mode="json")
        response_status = answer_response.status

    run_log = {
        "run_version": RUN_VERSION,
        "created_at": timestamp.isoformat(),
        "question": question,
        "retrieval_method": RETRIEVAL_METHOD,
        "selected_document_id": document_id,
        "document_ids": list(metadata_by_id),
        "document_metadata": document_metadata,
        "paragraph_count": len(paragraphs),
        "paragraph_files": paragraph_files,
        "answer_model_configured": ANSWER_MODEL,
        "answer_model_called": answer_model_called,
        "answer_model_returned": answer_model_returned,
        "response_status": response_status,
        "prompt_version": PROMPT_PATH.name,
        "instructions": instructions,
        "model_input": model_input,
        "top_k": TOP_K,
        "retrieval": retrieval_log,
        "answer": answer,
        "elapsed_seconds": elapsed,
        "raw_answer_response": raw_answer_response,
    }

    log_path.write_text(
        json.dumps(run_log, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # Save incomplete responses, but do not display them as answers.
    if answer_model_called:
        if answer_response.status != "completed" or not answer.strip():
            raise RuntimeError(
                "No complete answer returned. "
                f"Response status: {answer_response.status}. "
                f"Inspect the saved log: {log_path}"
            )

    return {
        "question": question,
        "answer": answer,
        "evidence": evidence,
        "retrieval": retrieval_log,
        "retrieval_method": RETRIEVAL_METHOD,
        "selected_document_id": document_id,
        "elapsed_seconds": elapsed,
        "usage": usage,
        "log_path": str(log_path),
        "document_count": len(metadata_by_id),
        "paragraph_count": len(paragraphs),
    }


def main():
    question = input("Enter a question in English: ").strip()

    if not question:
        print("Please enter a question.")
        return

    document_id = input(
        "Document ID (press Enter to search all documents): "
    ).strip()

    if not document_id:
        document_id = None

    print("Loading evidence and generating an answer...")

    result = answer_question(
        question,
        document_id=document_id,
    )

    print(
        f"\nUsed {result['paragraph_count']} paragraphs "
        f"from {result['document_count']} documents for retrieval."
    )
    print("Retrieval method:", result["retrieval_method"])

    if result["selected_document_id"] is None:
        print("Search scope: all collected documents")
    else:
        print("Search scope:", result["selected_document_id"])

    print("\nANSWER")
    print(result["answer"])

    print("\nRETRIEVED EVIDENCE — not all passages are necessarily cited")

    for passage, retrieval in zip(
        result["evidence"], result["retrieval"]
    ):
        print(f"\n[{passage['paragraph_id']}]")
        print("Keyword score:", retrieval["keyword_score"])
        print("Matched words:", ", ".join(retrieval["matched_words"]))
        print("Section:", passage["section"])
        print("Study:", passage["study_id"])
        print("Source:", passage["source_title"])
        print("URL:", passage["source_url"])
        print("Text:", passage["text"])

    usage = result["usage"]

    if usage is not None:
        print("\nAnswer input tokens:", usage.input_tokens)
        print("Answer output tokens:", usage.output_tokens)
    else:
        print("\nNo answer-model API request was sent.")

    print(f"Elapsed seconds: {result['elapsed_seconds']:.2f}")
    print("Saved run:", result["log_path"])


if __name__ == "__main__":
    main()
