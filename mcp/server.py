import sys
from pathlib import Path


# ---------------------------------------------------------
# Project paths
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOCAL_MCP_DIR = Path(__file__).resolve().parent


# ---------------------------------------------------------
# Prevent the local mcp/ folder from shadowing the
# installed MCP package.
#
# Keep Python's standard library and site-packages intact.
# ---------------------------------------------------------

original_sys_path = sys.path.copy()

sys.path = [
    path
    for path in sys.path
    if Path(path if path else ".").resolve()
    not in {
        PROJECT_ROOT,
        LOCAL_MCP_DIR,
    }
]


# ---------------------------------------------------------
# Import the installed MCP SDK
# ---------------------------------------------------------

from mcp.server import MCPServer


# ---------------------------------------------------------
# Restore project imports
# ---------------------------------------------------------

sys.path = original_sys_path

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from src.embeddings import search_policy
from src.tools.employee_tools import check_employee_eligibility


# ---------------------------------------------------------
# Create MCP server
# ---------------------------------------------------------

mcp = MCPServer("AI Travel Policy Assistant")


# ---------------------------------------------------------
# Tool 1: Search Company Policy
# ---------------------------------------------------------

@mcp.tool()
def search_company_policy(query: str) -> list:
    """
    Search the company travel and expense policy
    knowledge base.
    """

    results = search_policy(
        query,
        top_k=3
    )

    formatted_results = []

    for result in results:
        formatted_results.append(
            {
                "source": result["metadata"]["source"],
                "text": result["text"],
                "score": result["score"]
            }
        )

    return formatted_results


# ---------------------------------------------------------
# Tool 2: Check Employee Eligibility
# ---------------------------------------------------------

@mcp.tool()
def check_employee(employee_id: str) -> dict:
    """
    Check employee eligibility using the company
    employee eligibility records.
    """

    return check_employee_eligibility(
        employee_id
    )


# ---------------------------------------------------------
# Start MCP Server
# ---------------------------------------------------------

if __name__ == "__main__":
    mcp.run()