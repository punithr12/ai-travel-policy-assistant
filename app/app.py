import sys
import re
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from flask import Flask, request, jsonify, render_template

from src.agent import run_agent
from src.memory import get_history, clear_history


app = Flask(__name__)


@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")


@app.route("/ask", methods=["POST"])
def ask():
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "error": "Request body is required."
            }), 400

        question = data.get("question", "").strip()
        employee_id = data.get("employee_id", "").strip()
        session_id = data.get("session_id", "default").strip()

        if not question:
            return jsonify({
                "error": "Please enter a question."
            }), 400

        # Run the AI agent

        answer = run_agent(
            question=question,
            session_id=session_id
        )

        # Extract policy filenames mentioned by the agent
        policy_files = [
            "travel_policy_india.txt",
            "travel_policy_us.txt",
            "airport_policy.txt",
            "employee_eligibility.txt",
            "expense_policy.txt",
            "cancellation_policy.txt",
            "approval_policy.txt"
        ]

        sources = [
            filename
            for filename in policy_files
            if filename in answer
        ]

        return jsonify({
            "question": question,
            "answer": answer,
            "session_id": session_id,
            "employee_id": employee_id,
            "sources": sources
        })

    except Exception as error:
        print(f"Error in /ask: {error}")

        return jsonify({
            "error": "Sorry, something went wrong while processing your request."
        }), 500


@app.route("/history", methods=["GET"])
def history():
    try:
        session_id = request.args.get(
            "session_id",
            "default"
        ).strip()

        history_data = get_history(session_id)

        return jsonify({
            "session_id": session_id,
            "history": history_data
        })

    except Exception as error:
        print(f"Error in /history: {error}")

        return jsonify({
            "error": "Unable to retrieve conversation history."
        }), 500


@app.route("/clear", methods=["POST"])
def clear():
    try:
        data = request.get_json() or {}

        session_id = data.get(
            "session_id",
            "default"
        ).strip()

        clear_history(session_id)

        return jsonify({
            "message": "Conversation cleared successfully.",
            "session_id": session_id
        })

    except Exception as error:
        print(f"Error in /clear: {error}")

        return jsonify({
            "error": "Unable to clear conversation."
        }), 500


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "service": "AI Travel Policy Assistant"
    })


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False,
        use_reloader=False
    )