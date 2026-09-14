from src.agent import run_agent


SESSION_ID = "test_employee_001"


print("\n--- Conversation 1 ---")
answer1 = run_agent(
    "Is EMP001 eligible for company travel?",
    session_id=SESSION_ID
)

print("\nAssistant:", answer1)


print("\n--- Conversation 2 ---")
answer2 = run_agent(
    "What about an airport ride costing INR 2500 at 22:30?",
    session_id=SESSION_ID
)

print("\nAssistant:", answer2)