"use client";

import { useRef, useState } from "react";
import type { BoardData } from "@/lib/kanban";

type Message = { role: "user" | "assistant"; content: string };

type ChatSidebarProps = {
  board: BoardData;
  onBoardRefresh: () => Promise<void>;
};

export const ChatSidebar = ({ board, onBoardRefresh }: ChatSidebarProps) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: "smooth" }), 50);
  };

  const handleSend = async () => {
    const text = input.trim();
    if (!text || loading) return;

    const userMessage: Message = { role: "user", content: text };
    const nextMessages = [...messages, userMessage];
    setMessages(nextMessages);
    setInput("");
    setLoading(true);
    scrollToBottom();

    try {
      const res = await fetch("/api/ai/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: text,
          history: messages.map((m) => ({ role: m.role, content: m.content })),
        }),
      });

      if (!res.ok) throw new Error("Request failed");

      const data: { message: string; board_updated: boolean } = await res.json();

      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: data.message },
      ]);

      if (data.board_updated) {
        await onBoardRefresh();
      }
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Sorry, something went wrong. Please try again." },
      ]);
    } finally {
      setLoading(false);
      scrollToBottom();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <aside className="flex w-80 shrink-0 flex-col rounded-3xl border border-[var(--stroke)] bg-white shadow-[var(--shadow)]">
      <div className="border-b border-[var(--stroke)] px-5 py-4">
        <p className="text-xs font-semibold uppercase tracking-[0.25em] text-[var(--gray-text)]">
          AI Assistant
        </p>
        <p className="mt-1 font-display text-lg font-semibold text-[var(--navy-dark)]">
          Chat
        </p>
      </div>

      <div className="flex min-h-0 flex-1 flex-col gap-3 overflow-y-auto p-4">
        {messages.length === 0 && (
          <p className="text-center text-xs text-[var(--gray-text)]">
            Ask the AI to move, add, or rename cards and columns.
          </p>
        )}
        {messages.map((msg, i) => (
          <div
            key={i}
            className={
              msg.role === "user"
                ? "self-end rounded-2xl rounded-br-sm bg-[var(--secondary-purple)] px-4 py-2.5 text-sm text-white"
                : "self-start rounded-2xl rounded-bl-sm bg-[var(--surface)] px-4 py-2.5 text-sm text-[var(--navy-dark)]"
            }
          >
            {msg.content}
          </div>
        ))}
        {loading && (
          <div className="self-start rounded-2xl rounded-bl-sm bg-[var(--surface)] px-4 py-2.5 text-sm text-[var(--gray-text)]">
            Thinking...
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="border-t border-[var(--stroke)] p-4">
        <div className="flex gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask the AI..."
            rows={2}
            className="flex-1 resize-none rounded-xl border border-[var(--stroke)] bg-[var(--surface)] px-3 py-2 text-sm text-[var(--navy-dark)] outline-none focus:border-[var(--primary-blue)] focus:ring-2 focus:ring-[var(--primary-blue)]/20"
          />
          <button
            onClick={handleSend}
            disabled={loading || !input.trim()}
            className="self-end rounded-xl bg-[var(--secondary-purple)] px-4 py-2 text-sm font-semibold text-white transition hover:opacity-90 disabled:opacity-40"
          >
            Send
          </button>
        </div>
        <p className="mt-2 text-xs text-[var(--gray-text)]">
          Enter to send, Shift+Enter for new line.
        </p>
      </div>
    </aside>
  );
};
