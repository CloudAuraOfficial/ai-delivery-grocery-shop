"use client";

import { useState, useRef, useEffect } from "react";
import Link from "next/link";
import { sendChatMessage } from "@/lib/api";
import { formatPrice } from "@/lib/utils";
import type { ChatMessage, ProductReference } from "@/lib/types";

const suggestedQuestions = [
  "What baby products are on BOGO?",
  "Find organic milk options",
  "What are today's daily deals?",
  "Which stores are in Lakeland?",
  "Recommend ingredients for a pasta dinner",
];

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [products, setProducts] = useState<ProductReference[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | undefined>();
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async (message?: string) => {
    const text = message || input.trim();
    if (!text || loading) return;

    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setLoading(true);

    try {
      const response = await sendChatMessage(text, sessionId);
      setSessionId(response.sessionId);
      setMessages((prev) => [...prev, { role: "assistant", content: response.message }]);
      setProducts(response.products);
    } catch {
      setMessages((prev) => [...prev, { role: "assistant", content: "Sorry, I'm having trouble connecting. Please try again." }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex flex-col" style={{ height: "calc(100vh - 160px)" }}>
      <div className="mb-4">
        <h1 className="text-2xl font-bold text-foreground">AI Shopping Assistant</h1>
        <p className="text-muted text-sm">Ask about products, deals, stores, or get meal recommendations</p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-4 mb-4 pr-2">
        {messages.length === 0 && (
          <div className="text-center py-12">
            <div className="text-5xl mb-4">💬</div>
            <h2 className="text-lg font-semibold text-foreground mb-4">How can I help you today?</h2>
            <div className="flex flex-wrap gap-2 justify-center">
              {suggestedQuestions.map((q) => (
                <button
                  key={q}
                  onClick={() => handleSend(q)}
                  className="text-sm px-4 py-2 bg-surface border border-border rounded-full hover:bg-primary/5 hover:border-primary/30 text-muted hover:text-primary transition-all"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            <div className={`max-w-[80%] rounded-2xl px-5 py-3 text-sm leading-relaxed ${
              msg.role === "user"
                ? "bg-primary text-white rounded-br-md"
                : "bg-surface border border-border text-foreground rounded-bl-md"
            }`}>
              <div className="whitespace-pre-wrap">{msg.content}</div>
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-surface border border-border rounded-2xl rounded-bl-md px-5 py-3">
              <div className="flex gap-1">
                <span className="w-2 h-2 bg-muted rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                <span className="w-2 h-2 bg-muted rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                <span className="w-2 h-2 bg-muted rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
              </div>
            </div>
          </div>
        )}

        {/* Product references — clickable */}
        {products.length > 0 && messages.length > 0 && !loading && (
          <div>
            <div className="text-xs text-muted mb-2 font-medium">Related products:</div>
            <div className="flex flex-wrap gap-2">
              {products.map((p) => (
                <Link
                  key={p.sku}
                  href={`/products?q=${encodeURIComponent(p.name)}`}
                  className="text-xs bg-white border border-border rounded-lg px-3 py-2.5 flex items-center gap-2 hover:border-primary hover:shadow-md transition-all group cursor-pointer"
                >
                  <span className="font-medium group-hover:text-primary transition-colors">{p.name}</span>
                  <span className="text-primary font-bold">{formatPrice(p.price)}</span>
                  {p.dealType && <span className="bg-red-100 text-red-700 px-1.5 py-0.5 rounded text-[10px]">{p.dealType}</span>}
                  <span className="text-muted group-hover:text-primary transition-colors">→</span>
                </Link>
              ))}
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="flex gap-3">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          placeholder="Ask about products, deals, or stores..."
          className="flex-1 px-5 py-3 border border-border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
          disabled={loading}
        />
        <button
          onClick={() => handleSend()}
          disabled={!input.trim() || loading}
          className="px-6 py-3 bg-primary text-white font-medium rounded-xl hover:bg-primary-dark transition-colors disabled:opacity-40"
        >
          Send
        </button>
      </div>
    </div>
  );
}
