async function askAssistant() {
    const employeeId = document.getElementById("employeeId").value.trim();
    const question = document.getElementById("question").value.trim();

    const answerElement = document.getElementById("answer");
    const sourceElement = document.getElementById("source");
    const errorElement = document.getElementById("errorMessage");
    const loadingElement = document.getElementById("loading");
    const askButton = document.getElementById("askButton");

    errorElement.textContent = "";

    if (!question) {
        errorElement.textContent = "Please enter a question.";
        return;
    }

    askButton.disabled = true;
    loadingElement.style.display = "block";
    answerElement.textContent = "";
    sourceElement.textContent = "";

    try {
        const response = await fetch("/ask", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                employee_id: employeeId,
                question: question,
                session_id: employeeId || "default"
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Unable to process the request.");
        }

        answerElement.textContent = data.answer;

        if (data.sources && data.sources.length > 0) {
            sourceElement.textContent =
                "Policy Source: " + data.sources.join(", ");
        }

        loadHistory();

        document.getElementById("question").value = "";

    } catch (error) {
        errorElement.textContent = error.message;
    } finally {
        askButton.disabled = false;
        loadingElement.style.display = "none";
    }
}


async function loadHistory() {
    const employeeId = document.getElementById("employeeId").value.trim();
    const sessionId = employeeId || "default";

    try {
        const response = await fetch(
            `/history?session_id=${encodeURIComponent(sessionId)}`
        );

        const data = await response.json();

        const historyElement = document.getElementById("history");

        if (!data.history || data.history.length === 0) {
            historyElement.textContent = "No conversation yet.";
            return;
        }

        historyElement.innerHTML = "";

        data.history.forEach(message => {
            const item = document.createElement("div");
            item.className = "history-item";

            const role = document.createElement("strong");
            role.textContent =
                message.role === "user" ? "User" : "Assistant";

            const content = document.createElement("div");
            content.textContent = message.content;

            item.appendChild(role);
            item.appendChild(content);

            historyElement.appendChild(item);
        });

    } catch (error) {
        console.error("History error:", error);
    }
}


async function clearConversation() {
    const employeeId = document.getElementById("employeeId").value.trim();
    const sessionId = employeeId || "default";

    try {
        const response = await fetch("/clear", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                session_id: sessionId
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Unable to clear conversation.");
        }

        document.getElementById("answer").textContent =
            "Conversation cleared.";

        document.getElementById("source").textContent = "";
        document.getElementById("history").textContent =
            "No conversation yet.";

        document.getElementById("errorMessage").textContent = "";

    } catch (error) {
        document.getElementById("errorMessage").textContent =
            error.message;
    }
}