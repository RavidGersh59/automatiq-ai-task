// src/Chat.tsx
import React, { useState } from "react";
import { sendAuthMessage, sendRagMessage } from "./api";
import { UserInfo } from "./types";
import "./App.css";

export default function Chat() {
  const [messages, setMessages] = useState<string[]>([
    "Welcome to the employee database assistant. Please write your name and id.",
  ]);

  const [input, setInput] = useState("");
  const [userInfo, setUserInfo] = useState<UserInfo>({
    name: null,
    id: null,
    division: null,
  });

  const [systemMsg, setSystemMsg] = useState(
    "Welcome to the employee database assistant. Please write your name and id."
  );

  const [authenticated, setAuthenticated] = useState(false);

  function resetConversation() {
    setAuthenticated(false);

    const welcome =
      "Welcome to the employee database assistant. Please write your name and id.";

    setSystemMsg(welcome);
    setMessages([welcome]);
    setUserInfo({ name: null, id: null, division: null });
    setInput("");
  }

  async function handleSend() {
    if (!input.trim()) return;

    setMessages((prev) => [...prev, "You: " + input]);

    if (!authenticated) {
      // AUTHENTICATION FLOW
      const result = await sendAuthMessage(input, userInfo, systemMsg);

      setMessages((prev) => [...prev, "Bot: " + result.system_last_message]);
      setUserInfo(result.user_info);
      setSystemMsg(result.system_last_message);

      if (result.authenticated) setAuthenticated(true);
    } else {
      // RAG FLOW — backend handles conversation memory
      const result = await sendRagMessage(input, userInfo);

      setMessages((prev) => [...prev, "Bot: " + result.system_reply]);
    }

    setInput("");
  }

  return (
    <div className="chat-container">
      <div className="chat-box">
        {messages.map((m, i) => (
          <div key={i} className="msg">
            {m}
          </div>
        ))}
      </div>

      <div className="input-row">
        <input
          type="text"
          placeholder="Write a message..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") handleSend();
          }}
        />

        <button onClick={handleSend}>Send</button>
        <button onClick={resetConversation} style={{ marginLeft: "10px" }}>
          Reset
        </button>
      </div>

      {authenticated && <div className="success">Authenticated! 🎉</div>}
    </div>
  );
}


