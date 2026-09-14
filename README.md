# AI Travel & Policy Assistant

An AI-powered Travel & Policy Assistant that helps employees understand company travel policies, check employee eligibility, validate trips, calculate reimbursement amounts, and maintain conversation context.

The system combines **RAG (Retrieval-Augmented Generation)**, **FAISS semantic search**, **LLM tool calling**, **conversation memory**, **MCP**, and a **Flask web application**.

---

## Project Objective

The objective of this project is to build an AI assistant that can:

- Answer company travel policy questions.
- Retrieve relevant information from company policy documents.
- Check employee travel eligibility.
- Validate travel requests based on employee and policy information.
- Calculate reimbursement amounts.
- Determine when additional approval is required.
- Maintain conversation context across follow-up questions.
- Provide policy source attribution.
- Handle unsupported questions and errors safely.
- Provide a simple Flask-based web dashboard.

---

## Project Architecture

```text
User
  |
  v
Flask Web Application
  |
  v
AI Agent
  |
  +--------------------+
  |                    |
  v                    v
RAG / FAISS          Tools
  |                    |
  v                    +--> Employee Eligibility
Policy Documents       |
                       +--> Trip Validation
                       |
                       +--> Reimbursement Calculation
  |
  v
Ollama LLM
(qwen3:1.7b)
  |
  v
Final Response
  |
  v
Conversation Memory
```

---

## Technologies Used

- Python
- Flask
- Pandas
- Sentence Transformers
- FAISS
- Ollama
- Qwen3 1.7B
- MCP
- HTML
- CSS
- JavaScript
- Git & GitHub

---

## Project Structure

```text
ai-travel-policy-assistant/
│
├── app/
│   ├── app.py
│   ├── templates/
│   │   └── index.html
│   └── static/
│       ├── css/
│       │   └── style.css
│       └── js/
│           └── app.js
│
├── data/
│   ├── company_policy/
│   │   ├── airport_policy.txt
│   │   ├── approval_policy.txt
│   │   ├── cancellation_policy.txt
│   │   ├── employee_eligibility.txt
│   │   ├── expense_policy.txt
│   │   ├── travel_policy_india.txt
│   │   └── travel_policy_us.txt
│   │
│   ├── employees.csv
│   └── vector_store/
│       ├── policy.index
│       └── policy_chunks.pkl
│
├── mcp/
│   └── server.py
│
├── src/
│   ├── ingestion.py
│   ├── preprocessing.py
│   ├── embeddings.py
│   ├── rag.py
│   ├── agent.py
│   ├── memory.py
│   │
│   └── tools/
│       ├── employee_tools.py
│       ├── trip_tools.py
│       └── reimbursement_tools.py
│
├── tests/
│   └── test_cases.md
│
├── requirements.txt
└── README.md
```

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/punithr12/ai-travel-policy-assistant.git
cd ai-travel-policy-assistant
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

### 3. Activate the virtual environment

Linux / macOS:

```bash
source venv/bin/activate
```

Windows:

```bash
venv\Scripts\activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

---

## Ollama Setup

The project uses Ollama to run the local LLM.

Install Ollama and pull the required model:

```bash
ollama pull qwen3:1.7b
```

Make sure Ollama is running before starting the application.

The application communicates with the local Ollama server.

---

## Policy Data

The policy documents are stored in:

```text
data/company_policy/
```

The system loads the policy `.txt` files, cleans the content, adds metadata, and splits the documents into chunks.

The current policy knowledge base contains:

- India travel policy
- US travel policy
- Airport travel policy
- Employee eligibility policy
- Expense policy
- Cancellation policy
- Approval policy

---

## RAG Pipeline

The RAG pipeline follows these steps:

```text
Policy Documents
      |
      v
Document Ingestion
      |
      v
Text Cleaning
      |
      v
Chunking
      |
      v
Sentence Transformer Embeddings
      |
      v
FAISS Vector Index
      |
      v
Semantic Search
      |
      v
Relevant Policy Context
      |
      v
Ollama LLM
      |
      v
Final Answer
```

The embedding model used is:

```text
all-MiniLM-L6-v2
```

The FAISS index is stored in:

```text
data/vector_store/policy.index
```

---

## Agent and Tools

The AI agent decides whether a user query requires:

- Policy retrieval
- Employee eligibility information
- Trip validation
- Reimbursement calculation
- A combination of the above

### Employee Eligibility

The employee tool retrieves employee information from:

```text
data/employees.csv
```

Example:

```text
EMP001 → Eligible
EMP002 → Approval Required
EMP004 → Not Eligible
```

### Trip Validation

The trip validation tool checks:

- Employee eligibility
- Country
- Trip type
- Trip amount
- Late-night travel
- Personal/business purpose
- Approval requirements

### Reimbursement Calculation

The reimbursement tool calculates the standard reimbursable amount based on the applicable country limit.

Example:

```text
India standard limit = INR 2,000

Trip amount = INR 1,500
Reimbursable amount = INR 1,500
```

For an amount above the standard limit:

```text
Trip amount = INR 2,500
Standard limit = INR 2,000
Amount requiring additional review = INR 500
```

---

## Conversation Memory

Conversation history is maintained using the memory module.

This allows the assistant to handle follow-up questions using previous conversation context.

Example:

```text
User:
Can I take an airport trip?

User:
What if it costs 2,500?
```

The assistant can use the previous conversation to understand what the follow-up question refers to.

---

## MCP

The project also includes an MCP server implementation under:

```text
mcp/server.py
```

The MCP server exposes project functionality for policy and employee-related operations.

Run the MCP server using:

```bash
python mcp/server.py
```

The server uses standard MCP communication and waits for MCP client requests.

---

## Flask Application

The Flask application provides a simple web dashboard.

Start the application using:

```bash
python app/app.py
```

The application runs at:

```text
http://127.0.0.1:5000
```

### Available API Routes

```text
GET  /
POST /ask
GET  /history
POST /clear
GET  /health
```

### `/ask`

Accepts an employee ID, question, and session ID.

Example request:

```json
{
    "employee_id": "EMP001",
    "question": "Is EMP001 eligible for company travel?",
    "session_id": "default"
}
```

### `/health`

Used to verify that the Flask service is running.

Example response:

```json
{
    "status": "healthy",
    "service": "AI Travel Policy Assistant"
}
```

---

## Web Dashboard

The dashboard provides:

- Employee ID input
- Question input
- Ask Assistant button
- Clear Conversation button
- Assistant response
- Policy source information
- Conversation history
- Error messages

---

## Testing

The project includes test scenarios covering:

### RAG Tests

- India reimbursement limit
- US reimbursement limit
- Airport travel policy
- Late-night airport travel
- Required expense information

### Employee Eligibility Tests

```text
EMP001
EMP002
EMP004
Unknown Employee ID
```

### Trip Validation Tests

```text
EMP001 - INR 1,500 airport trip
EMP001 - INR 2,500 airport trip
EMP003 - USD 50 airport trip
EMP003 - USD 100 airport trip
```

### Memory Test

```text
Can I take an airport trip?

What if it costs 2,500?
```

### Hallucination Tests

The assistant is also tested with unsupported questions such as:

```text
Hotel reimbursement
Maximum flight ticket amount
Rental car policy
```

The assistant should not invent policy information that is not available in the knowledge base.

### Error Handling Tests

Tests include:

- Empty questions
- Invalid employee IDs
- Invalid trip amounts
- Unsupported questions
- Missing policy information
- Tool/retrieval failures
- API errors

---

## Example Queries

```text
Is EMP001 eligible for company travel?
```

```text
What is the airport trip reimbursement limit in India?
```

```text
Can EMP001 take an airport trip costing INR 2,500?
```

```text
Can I take an airport trip at 11 PM for approved business travel?
```

```text
How much of a INR 2,500 airport trip is reimbursable?
```

---

## Key Features

### 1. Policy RAG

Retrieves relevant policy information from the company knowledge base before generating an answer.

### 2. Source Attribution

Responses can identify the policy document used to answer the question.

### 3. Tool Calling

The agent can invoke tools for employee eligibility, trip validation, and reimbursement calculations.

### 4. Conversation Memory

Maintains previous messages to support contextual follow-up questions.

### 5. Hallucination Prevention

The assistant is instructed not to invent policies, limits, approvals, or unsupported information.

### 6. Flask Dashboard

Provides a simple interface for employees to interact with the assistant.

### 7. MCP Integration

Includes an MCP server for exposing project functionality through the Model Context Protocol.

---

## Conclusion

The AI Travel & Policy Assistant combines retrieval, reasoning, tools, memory, and a web interface to provide a complete employee travel-policy assistance workflow.

The system is designed to provide policy-grounded responses while using structured tools for employee eligibility, trip validation, and reimbursement calculations.