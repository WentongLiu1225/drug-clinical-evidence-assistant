import re

from load_documents import load_documents

# Common words that add little search information
STOP_WORDS = {
    "a", "an", "the", "is", "are", "was", "were",
    "what", "which", "how", "who",
    "do", "does", "did", "of", "to", "in", "on",
    "for", "and", "or", "with", "by", "at",
}


def tokenize(text):
    words = re.findall(r"[a-z0-9]+", text.lower())

    tokens = set()

    for word in words:
        if word not in STOP_WORDS:
            tokens.add(word)

    return tokens


def get_score(result):
    return result["score"]


def search_paragraphs(question, paragraphs, top_k=3):
    query_tokens = tokenize(question)
    results = []

    for paragraph in paragraphs:
        paragraph_tokens = tokenize(paragraph["text"])
        matched_words = query_tokens.intersection(paragraph_tokens)
        score = len(matched_words)

        if score > 0:
            result = {
                "score": score,
                "matched_words": sorted(matched_words),
                "paragraph": paragraph,
            }
            results.append(result)

    results.sort(key=get_score, reverse=True)

    return results[:top_k]


def main():
    paragraphs, metadata_by_id = load_documents()

    question = input("Enter a question in English: ").strip()

    if not tokenize(question):
        print("Please enter a question with searchable English words.")
        return

    results = search_paragraphs(question, paragraphs)

    if not results:
        print("No keyword matches found. This does not prove the answer is absent.")
        return

    print("\nRetrieved passages — check whether they answer the question.")

    for rank, result in enumerate(results, start=1):
        paragraph = result["paragraph"]
        metadata = metadata_by_id[paragraph["document_id"]]

        print(f"\nResult {rank} | Keyword score: {result['score']}")
        print("Matched words:", ", ".join(result["matched_words"]))
        print("Paragraph:", paragraph["paragraph_id"])
        print("Section:", paragraph["section"])
        print("Study:", paragraph["study_id"])
        print("Source:", metadata["title"])
        print("URL:", metadata["source_url"])
        print("Text:", paragraph["text"])


if __name__ == "__main__":
    main()