# ---------------------------------------------------------
# Conversation Memory
# ---------------------------------------------------------

conversation_history = {}


def get_history(session_id):
    """
    Return the conversation history for a session.
    """
    return conversation_history.get(session_id, [])


def add_message(session_id, role, content):
    """
    Add a message to the conversation history.
    """
    if session_id not in conversation_history:
        conversation_history[session_id] = []

    conversation_history[session_id].append({
        "role": role,
        "content": content
    })


def clear_history(session_id):
    """
    Clear the conversation history for a session.
    """
    conversation_history.pop(session_id, None)


def format_history(session_id):
    """
    Convert conversation history into text that can be
    included in the agent prompt.
    """
    history = get_history(session_id)

    if not history:
        return "No previous conversation."

    formatted = []

    for message in history:
        role = message["role"].capitalize()
        content = message["content"]

        formatted.append(
            f"{role}: {content}"
        )

    return "\n".join(formatted)


if __name__ == "__main__":

    session_id = "test_session"

    add_message(
        session_id,
        "user",
        "Is EMP001 eligible for travel?"
    )

    add_message(
        session_id,
        "assistant",
        "EMP001 is eligible for company travel."
    )

    print("\nConversation Memory Test")
    print("=" * 60)
    print(format_history(session_id))

    clear_history(session_id)

    print("\nAfter clearing:")
    print(format_history(session_id))