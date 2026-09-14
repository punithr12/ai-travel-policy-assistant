import json
import ollama

from .embeddings import search_policy
from .tools.employee_tools import check_employee_eligibility
from .tools.trip_tools import validate_trip
from .tools.reimbursement_tools import calculate_reimbursement
from .memory import get_history, add_message


MODEL_NAME = "qwen3:1.7b"


# ---------------------------------------------------------
# Tool definitions given to the LLM
# ---------------------------------------------------------

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_policy",
            "description": (
                "Search the company travel and expense policy knowledge base "
                "for policy information."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The policy question to search for."
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_employee_eligibility",
            "description": (
                "Check an employee's travel eligibility using the company "
                "employee eligibility records."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "employee_id": {
                        "type": "string",
                        "description": "The employee ID, such as EMP001."
                    }
                },
                "required": ["employee_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "validate_trip",
            "description": (
                "Validate a business trip using employee eligibility, "
                "trip type, trip amount, time, and applicable travel policy."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "employee_id": {
                        "type": "string"
                    },
                    "trip_type": {
                        "type": "string"
                    },
                    "amount": {
                        "type": "number"
                    },
                    "time": {
                        "type": "string",
                        "description": "Time in HH:MM format."
                    }
                },
                "required": [
                    "employee_id",
                    "trip_type",
                    "amount",
                    "time"
                ]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_reimbursement",
            "description": (
                "Calculate the reimbursable amount and the amount requiring "
                "review based on trip amount and policy limit."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "trip_amount": {
                        "type": "number"
                    },
                    "policy_limit": {
                        "type": "number"
                    }
                },
                "required": [
                    "trip_amount",
                    "policy_limit"
                ]
            }
        }
    }
]


# ---------------------------------------------------------
# Execute the selected tool
# ---------------------------------------------------------

def execute_tool(tool_name, arguments):


    if tool_name == "search_policy":
        results = search_policy(
            arguments["query"],
            top_k=3
        )

        formatted_results = []

        for result in results:
            formatted_results.append({
                "source": result["metadata"]["source"],
                "text": result["text"],
                "score": result["score"]
            })

        return formatted_results

    elif tool_name == "check_employee_eligibility":
        return check_employee_eligibility(
            arguments["employee_id"]
        )

    elif tool_name == "validate_trip":
        return validate_trip(
            arguments["employee_id"],
            arguments["trip_type"],
            arguments["amount"],
            arguments["time"]
        )

    elif tool_name == "calculate_reimbursement":
        return calculate_reimbursement(
            arguments["trip_amount"],
            arguments["policy_limit"]
        )

    else:
        return {
            "status": "Error",
            "message": f"Unknown tool: {tool_name}"
        }


# ---------------------------------------------------------
# Agent
# ---------------------------------------------------------

def run_agent(question, session_id="default"):
    history = get_history(session_id)

    contextual_question = question

    if history:
        previous_text = " ".join(
            message["content"]
            for message in history
        )

        lower_question = question.lower()

        cost_follow_up = (
            "what if" in lower_question
            and ("cost" in lower_question or "price" in lower_question)
        )

        if cost_follow_up:
            contextual_question = (
                f"Previous conversation:\n{previous_text}\n\n"
                f"Current question:\n{question}\n\n"
                "Determine the applicable company travel policy limit "
                "for the trip discussed in the previous conversation."
            )
    """
    Run the travel policy agent with conversation memory.
    """



    messages = [
        {
            "role": "system",
            "content": """
You are a company Travel and Policy Assistant.

Your job is to answer employee questions using the available
company policy search and business tools.

Rules:

1. Use search_policy for company policy questions.

2. Use check_employee_eligibility when an employee ID is involved
   and eligibility information is required.

3. Use validate_trip when the user asks whether a specific trip
   is allowed or valid.

4. Use calculate_reimbursement when reimbursement amounts need
   to be calculated.

4a. Use validate_trip only when the user provides enough specific
    trip details such as a trip type together with an amount and time,
    or explicitly asks to validate a specific trip.

4b. For general policy questions such as "Can I take an airport trip?",
    use search_policy instead of validate_trip.

4c. If a follow-up question adds only a cost to a previously discussed
    trip, first use the previous conversation to understand the trip
    and use search_policy to determine the applicable policy limit.
    Do not require unrelated details that were never provided.

4d. Do not ask for trip date, trip time, or approval status when the
    user is asking only about whether a type of trip is covered by
    company policy.

5. You may use multiple tools when necessary.

6. Never invent employee records, policy limits, approval status,
   reimbursement amounts, or policy rules.

7. Business rules and calculations must come from the tools.

8. If the available information is insufficient, clearly say so.

9. Never change the status returned by a business tool.

10. Do not interpret "Needs Approval" as "Not Allowed".

11. For policy answers, mention the actual policy filename when
    the search results provide one.

12. When a trip is late-night but otherwise covered by policy,
    do not reject it solely because it is between 10 PM and 6 AM.
    The supplied policy allows late-night business travel,
    while normal spending and approval limits still apply.

13. Always use the previous conversation history to resolve follow-up
    questions before asking the user to repeat information.

14. When a follow-up uses words such as "it", "this trip", "that trip",
    "the amount", "what if", or similar references, identify what the
    reference means from the previous conversation.

15. Preserve the employee ID, trip type, country, amount, and other
    relevant details from the previous conversation when they are
    available.

16. If the user asks a follow-up about the cost of a previously
    discussed trip, do not ask for the employee ID again if it is
    already known.

17. If a follow-up asks what happens when a previously discussed trip
    costs a particular amount, retrieve the applicable policy limit
    and explain whether the amount is within the limit or requires
    approval.

18. Never invent missing trip details. Only reuse details that are
    actually present in the conversation or provided by the user.

19. When a user asks about an amount exceeding a policy limit,
    clearly distinguish:
    - Trip amount
    - Policy limit
    - Amount requiring approval or review

20. If the required information is not available, do not guess.
    Say that additional information is required.

21. Never state that an amount is fully reimbursable unless the
    applicable policy limit has been established from the available
    policy data or a tool result..
"""
        }
    ]

    # Add previous conversation to the messages
    for message in history:
        messages.append(message)

    # Add current user question
    messages.append(
        {
            "role": "user",
            "content": contextual_question
        }
    )

    # -----------------------------------------------------
    # First LLM call
    # -----------------------------------------------------

    response = ollama.chat(
        model=MODEL_NAME,
        messages=messages,
        tools=TOOLS
    )

    message = response["message"]

    # Keep the assistant's response/tool-call message
    messages.append(message)

    # -----------------------------------------------------
    # Execute tool calls
    # -----------------------------------------------------

    tool_calls = message.get("tool_calls", [])

    if not tool_calls:

        answer = message.get("content", "")

        add_message(
            session_id,
            "user",
            question
        )

        add_message(
            session_id,
            "assistant",
            answer
        )

        return answer

    for tool_call in tool_calls:

        function = tool_call["function"]

        tool_name = function["name"]
        arguments = function["arguments"]

        if isinstance(arguments, str):
            arguments = json.loads(arguments)

        print(f"\n[Agent Tool Call] {tool_name}")
        print(f"[Arguments] {arguments}")

        result = execute_tool(
            tool_name,
            arguments
        )

        print(f"[Tool Result] {result}")

        messages.append(
            {
                "role": "tool",
                "content": json.dumps(result)
            }
        )

    # -----------------------------------------------------
    # Final LLM response
    # -----------------------------------------------------

    final_response = ollama.chat(
        model=MODEL_NAME,
        messages=messages,
        tools=TOOLS
    )

    answer = final_response["message"]["content"]

    # -----------------------------------------------------
    # Store conversation in memory
    # -----------------------------------------------------

    add_message(
        session_id,
        "user",
        question
    )

    add_message(
        session_id,
        "assistant",
        answer
    )

    return answer


# ---------------------------------------------------------
# Command-line testing
# ---------------------------------------------------------

if __name__ == "__main__":

    print("\nAI Travel Policy Agent")
    print("=" * 70)

    question = input("\nEnter your question: ")

    answer = run_agent(question)

    print("\nFinal Answer")
    print("=" * 70)
    print(answer)