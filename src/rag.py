import ollama

from .embeddings import search_policy


MODEL_NAME = "qwen3:1.7b"


def build_context(results):
    """
    Build the policy context that will be provided to the LLM.
    """

    context_parts = []

    for result in results:
        source = result["metadata"]["source"]

        context_parts.append(
            f"""
Policy Source: {source}

{result["text"]}
"""
        )

    return "\n".join(context_parts)


def create_prompt(question, context):
    """
    Create a grounded RAG prompt.
    """

    return f"""
You are a company Travel and Policy Assistant.

Answer the user's question using ONLY the policy information
provided in the context below.

Rules:
1. Do not use outside knowledge.
2. Do not invent or assume policy rules.
3. If the context does not contain enough information to answer,
   clearly say that the information is not available in the
   company policy knowledge base.
4. Give a concise and direct answer.
5. Mention the actual policy filename when citing a source.
6. If multiple policies are relevant, mention their actual
   filenames.
7. Do not refer to sources as "Policy Source 1", "Policy Source 2",
   etc. Use the actual filenames.

Policy Context:
--------------------
{context}
--------------------

User Question:
{question}

Answer:
"""


def generate_answer(question):
    """
    Retrieve relevant policies and generate a grounded answer.
    """

    results = search_policy(question, top_k=3)

    context = build_context(results)

    prompt = create_prompt(question, context)

    response = ollama.chat(
        model=MODEL_NAME,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    answer = response["message"]["content"]

    return answer, results


if __name__ == "__main__":

    question = input("\nEnter your policy question: ")

    answer, results = generate_answer(question)

    print("\nRAG Answer")
    print("=" * 70)
    print(answer)

    print("\nRetrieved Sources")
    print("=" * 70)

    for result in results:

        source = result["metadata"]["source"]
        score = result["score"]

        print(
            f"- {source} "
            f"(score: {score:.4f})"
        )