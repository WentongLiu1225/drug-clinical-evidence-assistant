# Local interface for our clinical evidence assistant.

import sys
from pathlib import Path

import streamlit as st


PROJECT_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = PROJECT_DIR / "scripts"

# Let Python find our existing scripts.
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from ask_evidence import answer_question
from load_documents import load_documents


st.set_page_config(
    page_title="Drug Clinical Evidence Assistant",
    layout="wide",
)

st.title("Drug Clinical Evidence Assistant")
st.write(
    "Explore the design, population, and endpoints of NATALEE "
    "using evidence from our collected documents."
)
st.caption(
    "Portfolio prototype. Answers are limited to the collected passages. "
    "No treatment recommendations or efficacy rankings."
)

# Load the collection without calling an API.
try:
    paragraphs, metadata_by_id = load_documents()
except Exception as error:
    st.error("The document collection could not be loaded.")
    st.text(f"{type(error).__name__}: {error}")
    st.stop()

study_ids = set()

for paragraph in paragraphs:
    study_ids.add(paragraph["study_id"])

st.caption(
    f"{len(metadata_by_id)} documents · "
    f"{len(study_ids)} studies · "
    f"{len(paragraphs)} passages"
)

with st.expander("View collected documents"):
    for document_id, metadata in metadata_by_id.items():
        st.markdown(f"**{metadata['title']}**")
        st.caption(f"Document ID: {document_id}")
        st.markdown(f"[Open source]({metadata['source_url']})")

    st.info(
        "The 2023 design paper includes selected Methods text. "
        "The 2025 four-year report includes selected Methods and Results "
        "text. The 2025 quality-of-life report includes selected Methods "
        "and Results text plus a Discussion paragraph on limitations. "
        "Figures, tables, and supplementary files from these papers "
        "are not included in the searchable collection."
    )

# None represents the full collection.
document_options = [None]

for document_id in metadata_by_id:
    document_options.append(document_id)


def format_document_option(document_id):
    if document_id is None:
        return "All collected documents"

    return metadata_by_id[document_id]["title"]


# Keep the latest result during this browser session.
if "answer_result" not in st.session_state:
    st.session_state["answer_result"] = None

with st.form("question_form"):
    selected_document_id = st.selectbox(
        "Search scope",
        options=document_options,
        format_func=format_document_option,
        help="Choose one report to limit the evidence search to that source.",
    )

    question = st.text_input(
        "Ask a question in English",
        placeholder="How long was ribociclib treatment planned to last?",
    )

    submitted = st.form_submit_button("Find evidence and answer")

if submitted:
    # Clear the previous result before processing a new submission.
    st.session_state["answer_result"] = None

    if not question.strip():
        st.warning("Please enter a question.")
    else:
        try:
            with st.spinner(
                "Retrieving evidence and preparing an answer..."
            ):
                result = answer_question(
                    question,
                    document_id=selected_document_id,
                )

            st.session_state["answer_result"] = result

        except Exception as error:
            st.error("The request failed. No new answer is displayed.")
            st.text(f"{type(error).__name__}: {error}")

result = st.session_state["answer_result"]

if result is not None:
    st.subheader("Answer")
    st.write("Question:", result["question"])

    # Display the scope saved with the answer, not the current selection.
    if "selected_document_id" not in result:
        st.caption("Search scope: not recorded in this older result.")
    else:
        result_document_id = result["selected_document_id"]

        if result_document_id is None:
            st.caption("Search scope: all collected documents.")
        else:
            source_metadata = metadata_by_id.get(result_document_id)
            source_title = result_document_id

            if source_metadata is not None:
                source_title = source_metadata["title"]

            st.caption(f"Search scope: {source_title}")

    st.markdown(result["answer"])

    st.subheader("Retrieved evidence")

    if result["evidence"]:
        st.caption(
            "These are the passages supplied to the answer model. "
            "Not all passages are necessarily cited. "
            "Check whether each citation supports its associated claim."
        )

        for passage in result["evidence"]:
            with st.expander(passage["paragraph_id"]):
                st.write("Source:", passage["source_title"])
                st.write("Study:", passage["study_id"])
                st.write("Section:", passage["section"])
                st.markdown(
                    f"[Open source]({passage['source_url']})"
                )
                st.write(passage["text"])

    else:
        st.info(
            "No keyword-matched passages were retrieved. "
            "Try rephrasing the question using study terminology. "
            "This does not prove the answer is absent from the "
            "selected documents."
        )

    with st.expander("Run details"):
        retrieval_method = result.get(
            "retrieval_method",
            "Not recorded in this session result",
        )
        st.write("Retrieval method:", retrieval_method)

        st.write(
            "Collection searched:",
            f"{result['document_count']} documents, "
            f"{result['paragraph_count']} passages",
        )
        st.write(
            "Passages retrieved:",
            len(result["evidence"]),
        )

        st.write(
            "Retrieval and answer time:",
            f"{result['elapsed_seconds']:.2f} seconds",
        )
        st.caption(
            "This timing excludes startup and document loading."
        )

        usage = result["usage"]

        if usage is not None:
            st.write("Answer input tokens:", usage.input_tokens)
            st.write("Answer output tokens:", usage.output_tokens)
        else:
            st.write("No answer-model API request was sent.")

        st.write("Saved log:", result["log_path"])

