from pathlib import Path


# Get the project root directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Location of policy documents
POLICY_DIR = BASE_DIR / "data" / "company_policy"


def load_documents():
    documents = []

    # Check whether policy directory exists
    if not POLICY_DIR.exists():
        print(f"Policy directory not found: {POLICY_DIR}")
        return documents

    # Get all text files
    files = sorted(POLICY_DIR.glob("*.txt"))

    if not files:
        print("No policy documents found.")
        return documents

    # Read every policy document
    for file_path in files:

        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            print(f"Error reading {file_path.name}: {e}")
            continue

        content = content.strip()

        # Skip empty files
        if not content:
            print(f"Skipping empty document: {file_path.name}")
            continue

        documents.append({
            "document_name": file_path.name,
            "content": content
        })

    return documents


if __name__ == "__main__":

    documents = load_documents()

    print("\nDocuments Loaded")
    print("=" * 60)

    for document in documents:
        print(
            f"{document['document_name']:<35}"
            f"{len(document['content']):>8} characters"
        )

    print("=" * 60)
    print(f"Total documents: {len(documents)}")