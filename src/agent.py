import json
import re
import ollama

from .embeddings import search_policy
from .tools.employee_tools import check_employee_eligibility
from .tools.trip_tools import validate_trip
from .tools.reimbursement_tools import calculate_reimbursement
from .memory import get_history, add_message


MODEL_NAME = "qwen3:1.7b"


# =========================================================
# Tool definitions
# =========================================================

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
                "Validate a specific business trip using employee eligibility, "
                "trip type, amount, time, and policy rules."
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
                "Calculate the reimbursable amount and amount requiring "
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


# =========================================================
# Helper functions
# =========================================================

def extract_employee_id(text):
    """
    Extract an explicitly mentioned employee ID.

    Example:
        "Can EMP003 take an airport trip?"
        -> "EMP003"
    """

    if not text:
        return None

    match = re.search(r"\bEMP\d{3}\b", text.upper())

    if match:
        return match.group(0)

    return None


def extract_time(text):
    """
    Extract a time in HH:MM format from the user's question.

    Example:
        "at 22:30" -> "22:30"

    Returns None when no time is provided.
    """

    if not text:
        return None

    match = re.search(
        r"\b([01]?\d|2[0-3]):([0-5]\d)\b",
        text
    )

    if match:
        hour = int(match.group(1))
        minute = match.group(2)

        return f"{hour:02d}:{minute}"

    return None


def extract_amount(text):
    """
    Extract a numeric amount from the current question.

    This is intentionally simple because the LLM is still responsible
    for understanding the question.
    """

    if not text:
        return None

    match = re.search(
        r"(?:USD|INR|\$|₹)?\s*(\d+(?:\.\d+)?)",
        text.upper()
    )

    if match:
        return float(match.group(1))

    return None


def has_trip_details(question):
    """
    Determine whether the question contains enough information
    for a specific trip validation attempt.

    Required:
        employee ID
        trip type
        amount
        time

    Time is intentionally required because validate_trip requires it.
    """

    employee = extract_employee_id(question)
    amount = extract_amount(question)
    time = extract_time(question)

    trip_words = [
        "airport",
        "office",
        "customer",
        "partner",
        "business trip",
        "ride",
        "travel"
    ]

    has_trip_type = any(
        word in question.lower()
        for word in trip_words
    )

    return (
        employee is not None
        and amount is not None
        and time is not None
        and has_trip_type
    )


# =========================================================
# Execute tools
# =========================================================

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
def is_supported_question(question):
    """
    Check whether the question is related to the Travel & Policy Assistant.
    """

    q = question.lower()

    travel_keywords = [
        "travel",
        "trip",
        "ride",
        "airport",
        "business travel",
        "business trip",
        "reimbursement",
        "expense",
        "approval",
        "eligible",
        "eligibility",
        "employee",
        "policy",
        "cancellation",
        "late night",
        "limit",
        "allowed",
        "allowed trip",
        "company travel",
        "manager approval",
        "airport trip",
        "cost",
        "costing",
        "amount",
        "usd",
        "inr",
        "emp"
    ]

    return any(
        keyword in q
        for keyword in travel_keywords
    )


# =========================================================
# Agent
# =========================================================

def run_agent(question, session_id="default", employee_id=None):

    question = (question or "").strip()
    if not question:
        return "Please enter a travel or company policy question."

    if not is_supported_question(question):
        return ("I can only assist with company travel and policy-related questions.")

    # -----------------------------------------------------
    # Empty question
    # -----------------------------------------------------

    if not question:

        return (
            "Please enter a travel or company policy question."
        )


    # -----------------------------------------------------
    # UI employee
    # -----------------------------------------------------

    ui_employee_id = (employee_id or "").strip().upper()


    # -----------------------------------------------------
    # IMPORTANT:
    # Employee ID explicitly mentioned in CURRENT question
    # always overrides the UI employee.
    # -----------------------------------------------------

    explicit_employee_id = extract_employee_id(question)

    if explicit_employee_id:
        active_employee_id = explicit_employee_id
    else:
        active_employee_id = ui_employee_id


    # -----------------------------------------------------
    # Conversation history
    # -----------------------------------------------------

    history = get_history(session_id)

    previous_text = ""

    if history:

        previous_text = "\n".join(
            f"{message['role']}: {message['content']}"
            for message in history
        )


    # -----------------------------------------------------
    # Follow-up detection
    # -----------------------------------------------------

    lower_question = question.lower()

    follow_up_words = [
        "what if",
        "what about",
        "how about",
        "what happens if",
        "if it costs",
        "if the cost",
        "this trip",
        "that trip",
        "the trip",
        "it costs",
        "the amount"
    ]

    is_follow_up = any(
        phrase in lower_question
        for phrase in follow_up_words
    )


    # -----------------------------------------------------
    # Contextual question
    # -----------------------------------------------------

    if history and is_follow_up:

        contextual_question = f"""
Previous conversation:
{previous_text}

Current application employee:
{ui_employee_id if ui_employee_id else "Not provided"}

Current question employee ID:
{explicit_employee_id if explicit_employee_id else "Not explicitly provided"}

Active employee for this request:
{active_employee_id if active_employee_id else "Not provided"}

Current question:
{question}

FOLLOW-UP RULES:

- Resolve references such as "it", "this trip", "that trip",
  "the trip", "the amount", and "what if" using the previous
  conversation.

- Reuse only information that was actually established previously.

- If the current question explicitly provides an employee ID,
  that employee ID overrides all previous employee context.

- If the current question does NOT provide an employee ID,
  preserve the employee from the established conversation/application
  context.

- If the current question gives a new amount, use the new amount.

- Do not invent missing information.

- Retrieve the applicable policy when a policy limit is required.
"""

    else:

        contextual_question = f"""
Current application employee:
{ui_employee_id if ui_employee_id else "Not provided"}

Current question employee ID:
{explicit_employee_id if explicit_employee_id else "Not explicitly provided"}

Active employee for this request:
{active_employee_id if active_employee_id else "Not provided"}

Current question:
{question}
"""


    # =====================================================
    # System prompt
    # =====================================================

    system_prompt = f"""
You are a company Travel and Policy Assistant.

Your job is to answer employee questions using ONLY:

1. The company policy knowledge base.
2. The employee eligibility tool.
3. The trip validation tool.
4. The reimbursement calculation tool.
5. The conversation context provided to you.

=========================================================
EMPLOYEE ID PRIORITY
=========================================================

The employee ID in the CURRENT USER QUESTION has the highest priority.

Priority order:

1. Employee ID explicitly written in the current question.
2. Employee established in the current conversation for a follow-up.
3. Employee ID selected in the application.

If the current question contains an employee ID such as EMP003,
you MUST use EMP003.

NEVER use the application employee instead.

Example:

Application employee = EMP001
Current question = "Can EMP003 take an airport trip costing USD 100?"

Correct employee = EMP003.

EMP001 must NOT influence the employee, country, currency,
eligibility, policy limit, or trip validation.

=========================================================
EMPLOYEE CONTEXT
=========================================================

Current active employee for this request:

{active_employee_id if active_employee_id else "No employee identified"}

If the active employee is known, use that employee consistently.

Do not mix information between employees.

=========================================================
EMPLOYEE ELIGIBILITY
=========================================================

Use check_employee_eligibility when employee eligibility
information is required.

Always preserve the exact Status returned by the tool.

Valid statuses:

- Eligible
- Approval Required
- Not Eligible

Rules:

- "Eligible" means Eligible.
- "Approval Required" means Approval Required.
- "Not Eligible" means Not Eligible.
- Manager Approval = "No" does NOT automatically mean Not Eligible.
- Never infer Status from Manager Approval.
- The Status returned by the employee tool is authoritative.

=========================================================
EMPLOYEE-SPECIFIC QUESTIONS
=========================================================

When an employee ID is explicitly present in the current question:

1. Identify that employee.
2. Check that employee's actual country and status.
3. Use that employee's country to determine the applicable policy.
4. Never use another employee's country or status.

Example:

EMP003 is United States.

Therefore:

EMP003 + USD 100

must be evaluated using the United States policy,
not the India policy.

=========================================================
POLICY QUESTIONS
=========================================================

Use search_policy for:

- travel policies
- airport travel
- reimbursement limits
- eligible trip types
- restrictions
- documentation
- approval rules
- late-night travel
- cancellation policy
- other company policy questions

Answer only from retrieved policy information.

Never invent a policy limit.

=========================================================
SPECIFIC TRIP VALIDATION
=========================================================

Use validate_trip only when all required trip details are available:

- Employee ID
- Trip type
- Amount
- Time

NEVER invent a missing time.

If the user does not provide a time, do NOT create one.

If full trip validation cannot be performed because a required
detail is missing, use the available policy and employee information
and clearly state what is missing.

=========================================================
COUNTRY AND CURRENCY
=========================================================

Always determine the employee's actual country before applying
country-specific limits.

India airport/travel standard limit:

INR 2,000

United States airport/travel standard limit:

USD 75

Do not compare USD amounts with INR limits.

Do not compare INR amounts with USD limits.

Never transfer a country's limit to another country.

=========================================================
APPROVAL
=========================================================

Employee eligibility and trip approval are DIFFERENT.

Employee status may be:

- Eligible
- Approval Required
- Not Eligible

Trip validation status may be:

- Approved
- Needs Approval
- Rejected
- Needs Review

Never call "Needs Approval" the employee's eligibility status.

Example:

Employee status = Eligible
Trip status = Needs Approval

Correct:

"The employee is Eligible, but this specific trip Needs Approval."

If the trip exceeds the applicable country limit,
additional approval is required for the excess.

Do not reject a trip simply because approval is required.

=========================================================
LATE-NIGHT TRAVEL
=========================================================

The supplied policy allows approved business airport travel
between 10 PM and 6 AM.

This is a permitted travel window, NOT a requirement.

If no time is provided:

- Do NOT assume late-night travel.
- Do NOT claim the trip is within the late-night window.
- Do NOT invent a time.

Normal spending and approval limits still apply.

=========================================================
REIMBURSEMENT
=========================================================

Use search_policy to establish the applicable policy limit.

Use calculate_reimbursement when an actual reimbursement calculation
is required.

Do not claim an amount is fully reimbursable unless the applicable
limit has been established.

Never invent reimbursement amounts.

=========================================================
UNSUPPORTED POLICY / HALLUCINATION RULES
=========================================================

Answer only from information explicitly supported by the retrieved
policy context and tools.

Never:

- invent employee records
- invent policy limits
- invent approval records
- invent reimbursement amounts
- invent hotel limits
- invent flight limits
- invent rental car limits
- transfer an airport limit to a hotel
- transfer an airport limit to a flight
- transfer an airport limit to a rental car
- transfer an India limit to the US
- transfer a US limit to India
- invent trip times
- invent trip amounts

If the requested expense type or policy limit is not defined
in the available policies, explicitly state:

"The provided company policy does not specify this."

=========================================================
EXPENSE INFORMATION
=========================================================

For expense reimbursement questions, use only the required fields
stated in the expense policy.

Required expense information includes:

- Employee ID
- Date
- Amount
- Currency
- Purpose
- Expense type
- Approval reference if required

Do NOT claim that trip time or employee eligibility status
are required expense fields unless the policy explicitly states so.

Do not mix trip validation requirements with expense reimbursement
documentation requirements.

=========================================================
FOLLOW-UP / MEMORY
=========================================================

Use previous conversation context for genuine follow-up questions.

For example:

Previous:
EMP001 asks about an airport trip.

Current:
"What if it costs 2500?"

Interpret the new amount as belonging to the previously established
airport trip.

However:

If the current question explicitly contains a DIFFERENT employee ID,
the current employee ID overrides previous context.

Example:

Previous:
EMP001 / India / airport trip

Current:
"Can EMP003 take an airport trip costing USD 100?"

Use EMP003 / United States.

Do NOT use EMP001 / India.

=========================================================
FINAL RESPONSE
=========================================================

Give a clear and concise answer.

Preserve tool results exactly.

Do not expose internal reasoning.

For policy questions, mention the relevant policy filename
when the policy search result provides one.

If information is unavailable, say so clearly.

Do not invent information to make the answer appear complete.
"""


    # =====================================================
    # Build messages
    # =====================================================

    messages = [
        {
            "role": "system",
            "content": system_prompt
        }
    ]


    # Add previous conversation
    for message in history:
        messages.append(message)


    # Add current question
    messages.append(
        {
            "role": "user",
            "content": contextual_question
        }
    )


    # =====================================================
    # First LLM call
    # =====================================================

    response = ollama.chat(
        model=MODEL_NAME,
        messages=messages,
        tools=TOOLS
    )

    message = response["message"]


    # Add assistant tool-call message
    messages.append(message)


    # =====================================================
    # Execute tool calls
    # =====================================================

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

            try:
                arguments = json.loads(arguments)

            except json.JSONDecodeError:

                arguments = {}


        # =================================================
        # HARD SAFETY CHECK
        # =================================================
        # Python, not the LLM, decides the employee ID.
        # =================================================

        if tool_name in [
            "check_employee_eligibility",
            "validate_trip"
        ]:

            if active_employee_id:

                arguments["employee_id"] = active_employee_id


        # =================================================
        # Prevent invented trip time
        # =================================================

        if tool_name == "validate_trip":

            actual_time = extract_time(question)

            if actual_time:

                arguments["time"] = actual_time

            else:

                # Do not allow the LLM to invent a time.
                # Skip validation and retrieve policy instead.

                print(
                    "\n[Agent] Skipping validate_trip: "
                    "no trip time was provided."
                )

                policy_result = execute_tool(
                    "search_policy",
                    {
                        "query": question
                    }
                )

                messages.append(
                    {
                        "role": "tool",
                        "content": json.dumps(policy_result)
                    }
                )

                continue


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


    # =====================================================
    # Final LLM response
    # =====================================================

    final_response = ollama.chat(
        model=MODEL_NAME,
        messages=messages,
        tools=TOOLS
    )


    answer = final_response["message"]["content"]


    # =====================================================
    # Store conversation
    # =====================================================

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


# =========================================================
# Command-line testing
# =========================================================

if __name__ == "__main__":

    print("\nAI Travel Policy Agent")
    print("=" * 70)

    question = input("\nEnter your question: ")

    answer = run_agent(question)

    print("\nFinal Answer")
    print("=" * 70)
    print(answer)