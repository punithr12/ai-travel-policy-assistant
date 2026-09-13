import json
import ollama

from .embeddings import search_policy
from .tools.employee_tools import check_employee_eligibility
from .tools.trip_tools import validate_trip
from .tools.reimbursement_tools import calculate_reimbursement


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

def run_agent(question):

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

5. You may use multiple tools when necessary.

6. Never invent employee records, policy limits, approval status,
   reimbursement amounts, or policy rules.

7. Business rules and calculations must come from the tools.

8. If the available information is insufficient, clearly say so.

9. Never change the status returned by a business tool.
   For example:
   - "Approved" means approved.
   - "Needs Approval" means approval is required, not rejected.
   - "Rejected" means rejected.
   - "Needs Review" means further review is required.

10. Do not interpret "Needs Approval" as "Not Allowed".

11. For policy answers, mention the actual policy filename when
    the search results provide one.

12. When a trip is late-night but otherwise covered by policy,
    do not reject it solely because it is between 10 PM and 6 AM.
    The supplied policy allows late-night business travel,
    while normal spending and approval limits still apply.

13. Give a concise and direct final answer.
"""
        },
        {
            "role": "user",
            "content": question
        }
    ]

    response = ollama.chat(
        model=MODEL_NAME,
        messages=messages,
        tools=TOOLS
    )

    message = response["message"]

    # Keep the assistant's tool-call message in the conversation
    messages.append(message)

    # -----------------------------------------------------
    # Execute tool calls
    # -----------------------------------------------------

    tool_calls = message.get("tool_calls", [])

    if not tool_calls:
        return message.get("content", "")

    for tool_call in tool_calls:

        function = tool_call["function"]

        tool_name = function["name"]
        arguments = function["arguments"]

        # Some Ollama versions return arguments as JSON text,
        # while others may return a dictionary.
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
    # Ask the LLM to produce the final answer
    # -----------------------------------------------------

    final_response = ollama.chat(
        model=MODEL_NAME,
        messages=messages,
        tools=TOOLS
    )

    return final_response["message"]["content"]


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