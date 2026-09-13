import re
from typing import Dict, List


def clean_text(text: str) -> str:
    """
    Clean unnecessary whitespace while preserving
    meaningful paragraph structure.
    """

    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Remove extra spaces/tabs
    text = re.sub(r"[ \t]+", " ", text)

    # Reduce excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def add_metadata(document_name: str) -> Dict[str, str]:
    """
    Add metadata based on the policy document name.
    """

    metadata = {
        "source": document_name,
        "policy_type": "general",
        "country": "All"
    }

    name = document_name.lower()

    if "travel_policy_india" in name:
        metadata.update({
            "policy_type": "travel",
            "country": "India"
        })

    elif "travel_policy_us" in name:
        metadata.update({
            "policy_type": "travel",
            "country": "United States"
        })

    elif "airport" in name:
        metadata.update({
            "policy_type": "airport",
            "country": "India/United States"
        })

    elif "employee_eligibility" in name:
        metadata.update({
            "policy_type": "eligibility",
            "country": "India/United States"
        })

    elif "expense" in name:
        metadata.update({
            "policy_type": "expense",
            "country": "India/United States"
        })

    elif "cancellation" in name:
        metadata.update({
            "policy_type": "cancellation",
            "country": "All"
        })

    elif "approval" in name:
        metadata.update({
            "policy_type": "approval",
            "country": "India/United States"
        })

    return metadata


def chunk_text(
    text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 75
) -> List[str]:
    """
    Split text into chunks while trying to preserve
    paragraph and sentence boundaries.
    """

    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0")

    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError(
            "chunk_overlap must be >= 0 and smaller than chunk_size"
        )

    text = clean_text(text)

    # Split into paragraphs
    paragraphs = text.split("\n\n")

    chunks = []
    current_chunk = ""

    for paragraph in paragraphs:

        paragraph = paragraph.strip()

        if not paragraph:
            continue

        # If adding the paragraph stays within the limit
        if len(current_chunk) + len(paragraph) + 2 <= chunk_size:
            if current_chunk:
                current_chunk += "\n\n" + paragraph
            else:
                current_chunk = paragraph

        else:
            # Save current chunk
            if current_chunk:
                chunks.append(current_chunk.strip())

            # Start a new chunk
            current_chunk = paragraph

    # Add final chunk
    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks

if __name__ == "__main__":

    from ingestion import load_documents

    documents = load_documents()

    print("\nPreprocessing Test")
    print("=" * 60)

    total_chunks = 0

    for document in documents:

        cleaned_text = clean_text(document["content"])

        metadata = add_metadata(document["document_name"])

        chunks = chunk_text(cleaned_text)

        total_chunks += len(chunks)

        print(f"\nDocument: {document['document_name']}")
        print(f"Policy Type: {metadata['policy_type']}")
        print(f"Country: {metadata['country']}")
        print(f"Chunks: {len(chunks)}")

        if chunks:
            print("\nFirst chunk:")
            print("-" * 40)
            print(chunks[0])
            print("-" * 40)

    print(f"\nTotal chunks created: {total_chunks}")