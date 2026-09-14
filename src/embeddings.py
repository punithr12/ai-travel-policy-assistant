import pickle
from pathlib import Path

import faiss
from sentence_transformers import SentenceTransformer

try:
    from .ingestion import load_documents
    from .preprocessing import clean_text, add_metadata, chunk_text
except ImportError:
    from ingestion import load_documents
    from preprocessing import clean_text, add_metadata, chunk_text
import os

SYSTEM_CA = "/etc/ssl/certs/ca-certificates.crt"

os.environ["REQUESTS_CA_BUNDLE"] = SYSTEM_CA
os.environ["SSL_CERT_FILE"] = SYSTEM_CA
os.environ["CURL_CA_BUNDLE"] = SYSTEM_CA

print("Using certificate bundle:", SYSTEM_CA)


# --------------------------------------------------
# Configuration
# --------------------------------------------------

MODEL_NAME = "all-MiniLM-L6-v2"

BASE_DIR = Path(__file__).resolve().parent.parent

VECTOR_STORE_DIR = BASE_DIR / "data" / "vector_store"

FAISS_INDEX_PATH = VECTOR_STORE_DIR / "policy.index"
CHUNKS_PATH = VECTOR_STORE_DIR / "policy_chunks.pkl"


# --------------------------------------------------
# Load embedding model ONCE
# --------------------------------------------------

print("Loading embedding model...")

model = SentenceTransformer(MODEL_NAME)

print("Embedding model loaded successfully.")


# --------------------------------------------------
# Prepare policy chunks
# --------------------------------------------------

def prepare_chunks():
    """
    Load policy documents, clean them, split them
    into chunks, and attach metadata.
    """

    documents = load_documents()

    all_chunks = []

    for document in documents:

        cleaned_text = clean_text(
            document["content"]
        )

        metadata = add_metadata(
            document["document_name"]
        )

        chunks = chunk_text(
            cleaned_text
        )

        for chunk_id, chunk in enumerate(chunks):

            all_chunks.append({
                "text": chunk,

                "metadata": {
                    **metadata,
                    "chunk_id": chunk_id
                }
            })

    return all_chunks


# --------------------------------------------------
# Create embeddings
# --------------------------------------------------

def create_embeddings(chunks):
    """
    Convert policy chunks into numerical embeddings.
    """

    texts = [
        chunk["text"]
        for chunk in chunks
    ]

    embeddings = model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    return embeddings.astype("float32")


# --------------------------------------------------
# Create FAISS index
# --------------------------------------------------

def create_faiss_index(embeddings):
    """
    Create FAISS index using inner-product similarity.
    """

    dimension = embeddings.shape[1]

    index = faiss.IndexFlatIP(
        dimension
    )

    index.add(embeddings)

    return index


# --------------------------------------------------
# Build and save vector store
# --------------------------------------------------

def build_vector_store():
    """
    Build the FAISS vector store and save it to disk.
    """

    print("\nPreparing policy chunks...")

    chunks = prepare_chunks()

    print(
        f"Total chunks: {len(chunks)}"
    )

    print("\nCreating embeddings...")

    embeddings = create_embeddings(
        chunks
    )

    print(
        f"Embedding shape: {embeddings.shape}"
    )

    print("\nCreating FAISS index...")

    index = create_faiss_index(
        embeddings
    )

    print(
        f"Vectors stored: {index.ntotal}"
    )

    # Create vector store directory
    VECTOR_STORE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # Save FAISS index
    faiss.write_index(
        index,
        str(FAISS_INDEX_PATH)
    )

    # Save chunks and metadata
    with open(
        CHUNKS_PATH,
        "wb"
    ) as file:

        pickle.dump(
            chunks,
            file
        )

    print("\nVector store saved successfully.")

    print(
        f"FAISS index: {FAISS_INDEX_PATH}"
    )

    print(
        f"Chunks: {CHUNKS_PATH}"
    )


# --------------------------------------------------
# Load existing vector store
# --------------------------------------------------

def load_vector_store():
    """
    Load the saved FAISS index and policy chunks.
    """

    if not FAISS_INDEX_PATH.exists():

        raise FileNotFoundError(
            f"FAISS index not found: {FAISS_INDEX_PATH}"
        )

    if not CHUNKS_PATH.exists():

        raise FileNotFoundError(
            f"Chunk metadata not found: {CHUNKS_PATH}"
        )

    # Load FAISS index
    index = faiss.read_index(
        str(FAISS_INDEX_PATH)
    )

    # Load chunks and metadata
    with open(
        CHUNKS_PATH,
        "rb"
    ) as file:

        chunks = pickle.load(file)

    return index, chunks


# --------------------------------------------------
# Semantic search
# --------------------------------------------------
# --------------------------------------------------
# Unsupported topic detection
# --------------------------------------------------

UNSUPPORTED_TRAVEL_TYPES = {
    "hotel": [
        "hotel",
        "hotels",
        "hotel reimbursement",
        "hotel expense"
    ],

    "flight": [
        "flight",
        "flights",
        "flight ticket",
        "air ticket",
        "airfare",
        "flight reimbursement"
    ],

    "rental_car": [
        "rental car",
        "rental cars",
        "car rental",
        "car rentals",
        "rental car reimbursement"
    ]
}


def detect_unsupported_topic(query):
    """
    Detect specific travel/expense types that are not defined
    in the supplied policy documents.
    """

    query_lower = query.lower()

    for topic, keywords in UNSUPPORTED_TRAVEL_TYPES.items():

        for keyword in keywords:

            if keyword in query_lower:

                return topic

    return None

# --------------------------------------------------
# Semantic search
# --------------------------------------------------

def search_policy(
    query,
    top_k=3
):
    """
    Search the policy knowledge base using semantic similarity.

    Returns no results when the query explicitly asks about a
    travel/expense type that is not defined in the supplied
    policy documents.
    """

    # --------------------------------------------------
    # Check for unsupported travel types first
    # --------------------------------------------------

    unsupported_topic = detect_unsupported_topic(query)

    if unsupported_topic:

        print(
            f"[RAG] Unsupported policy topic detected: "
            f"{unsupported_topic}"
        )

        return []


    # --------------------------------------------------
    # Load existing FAISS index
    # --------------------------------------------------

    index, chunks = load_vector_store()


    # --------------------------------------------------
    # Convert query into embedding
    # --------------------------------------------------

    query_embedding = model.encode(
        [query],
        convert_to_numpy=True,
        normalize_embeddings=True
    ).astype("float32")


    # --------------------------------------------------
    # FAISS search
    # --------------------------------------------------

    scores, indices = index.search(
        query_embedding,
        top_k
    )


    results = []


    for score, index_id in zip(
        scores[0],
        indices[0]
    ):

        if index_id == -1:
            continue


        results.append({
            "text": chunks[index_id]["text"],
            "metadata": chunks[index_id]["metadata"],
            "score": float(score)
        })


    return results

# --------------------------------------------------
# Main
# --------------------------------------------------

if __name__ == "__main__":

    build_vector_store()