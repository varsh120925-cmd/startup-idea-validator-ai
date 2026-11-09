/**
 * AI Startup Advisor Chat Controller
 */
function initAdvisorChat(ideaId) {
    const chatMessages = document.getElementById("chatMessages");
    const chatInput = document.getElementById("chatInput");
    const sendBtn = document.getElementById("sendBtn");
    const clearBtn = document.getElementById("clearChatBtn");

    if (!chatMessages || !chatInput || !sendBtn) return;

    // Scroll to bottom helper
    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    scrollToBottom();

    // Send message function
    async function sendMessage(text) {
        const query = (text || chatInput.value).trim();
        if (!query) return;

        chatInput.value = "";
        chatInput.disabled = true;
        sendBtn.disabled = true;

        // Append user bubble
        appendBubble("user", query);
        scrollToBottom();

        // Show typing indicator
        const typingEl = document.createElement("div");
        typingEl.className = "chat-bubble assistant text-muted";
        typingEl.id = "typingIndicator";
        typingEl.innerHTML = '<i class="bi bi-robot me-2"></i> Advisor is analyzing your startup metrics...';
        chatMessages.appendChild(typingEl);
        scrollToBottom();

        try {
            const res = await fetch(`/api/idea/${ideaId}/chat`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: query })
            });
            const data = await res.json();

            // Remove typing indicator
            const ind = document.getElementById("typingIndicator");
            if (ind) ind.remove();

            if (data.status === "success") {
                appendBubble("assistant", data.reply, data.source);
            } else {
                appendBubble("assistant", "⚠️ " + (data.message || "Failed to get advice. Please try again."));
            }
        } catch (err) {
            const ind = document.getElementById("typingIndicator");
            if (ind) ind.remove();
            appendBubble("assistant", "⚠️ Network error connecting to advisor. Please retry.");
        } finally {
            chatInput.disabled = false;
            sendBtn.disabled = false;
            chatInput.focus();
            scrollToBottom();
        }
    }

    function appendBubble(role, content, source) {
        const bubble = document.createElement("div");
        bubble.className = `chat-bubble ${role}`;

        if (role === "assistant") {
            let formattedContent = formatMarkdown(content);
            let metaHtml = source ? `<div class="text-muted mt-2 pt-1 border-top" style="font-size: 0.72rem;"><i class="bi bi-shield-check text-primary"></i> ${source}</div>` : '';
            bubble.innerHTML = `<div>${formattedContent}</div>${metaHtml}`;
        } else {
            bubble.textContent = content;
        }

        chatMessages.appendChild(bubble);
    }

    function formatMarkdown(text) {
        if (!text) return "";
        let html = text
            .replace(/### (.*?)\n/g, '<h5 class="fw-bold text-primary mt-2 mb-1">$1</h5>')
            .replace(/## (.*?)\n/g, '<h4 class="fw-bold text-navy mt-2 mb-1">$1</h4>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`([^`]+)`/g, '<code class="bg-light px-1 rounded text-primary">$1</code>')
            .replace(/^\s*-\s+(.*)$/gm, '<li class="mb-1">$1</li>')
            .replace(/^\s*\d+\.\s+(.*)$/gm, '<li class="mb-1">$1</li>')
            .replace(/\n\n/g, '<br/><br/>');
        return html;
    }

    // Event listeners
    sendBtn.addEventListener("click", () => sendMessage());
    chatInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Prompt chips
    document.querySelectorAll(".prompt-chip").forEach((chip) => {
        chip.addEventListener("click", () => {
            const promptText = chip.getAttribute("data-prompt") || chip.textContent.trim();
            sendMessage(promptText);
        });
    });

    // Clear chat
    if (clearBtn) {
        clearBtn.addEventListener("click", async () => {
            if (confirm("Are you sure you want to clear chat history for this idea?")) {
                await fetch(`/api/idea/${ideaId}/chat/clear`, { method: "POST" });
                chatMessages.innerHTML = `
                    <div class="chat-bubble assistant">
                        <strong>Hello founder!</strong> Chat history has been reset. How can I help you validate or scale your startup today?
                    </div>
                `;
            }
        });
    }
}
