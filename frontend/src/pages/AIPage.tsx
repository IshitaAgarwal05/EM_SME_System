import { useState, useRef, useEffect } from "react";
import { DashboardLayout } from "../components/layout/DashboardLayout";
import api from "../lib/api";
import { Send, Bot, User, Loader2 } from "lucide-react";

type Message = {
    role: "user" | "assistant";
    content: string;
};

export default function AIPage() {
    const [messages, setMessages] = useState<Message[]>([
        { role: "assistant", content: "Hello! I'm Clara, your Event Assistant. How can I help you today?" }
    ]);
    const [input, setInput] = useState("");
    const [loading, setLoading] = useState(false);
    const bottomRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    const sendMessage = async () => {
        if (!input.trim() || loading) return;

        const userMsg: Message = { role: "user", content: input };
        setMessages(prev => [...prev, userMsg]);
        setInput("");
        setLoading(true);

        try {
            // Send chat history for context
            const history = messages.map(m => ({ role: m.role, content: m.content }));
            const res = await api.post("/ai/chat", {
                message: userMsg.content,
                history: history
            });

            setMessages(prev => [...prev, { role: "assistant", content: res.data.response }]);
        } catch (e) {
            console.error(e);
            setMessages(prev => [...prev, { role: "assistant", content: "Sorry, I encountered an error. Please try again." }]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <DashboardLayout>
            <div className="flex h-[calc(100vh-8rem)] flex-col rounded-lg border bg-white shadow-sm overflow-hidden">
                <div className="flex items-center gap-3 border-b bg-gray-50 p-4">
                    <div className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-600 text-white">
                        <Bot className="h-5 w-5" />
                    </div>
                    <div>
                        <h3 className="font-semibold text-gray-900">Clara</h3>
                        <p className="text-xs text-gray-500">Your AI Event Assistant</p>
                    </div>
                </div>

                <div className="flex-1 overflow-y-auto p-4 space-y-4">
                    {messages.map((m, i) => (
                        <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                            <div className={`flex max-w-[80%] gap-3 rounded-lg p-3 ${m.role === 'user'
                                ? 'bg-blue-600 text-white'
                                : 'bg-gray-100 text-gray-900'
                                }`}>
                                {m.role === 'assistant' && <Bot className="h-5 w-5 shrink-0 mt-0.5" />}
                                <div className="text-sm whitespace-pre-wrap">{m.content}</div>
                                {m.role === 'user' && <User className="h-5 w-5 shrink-0 mt-0.5" />}
                            </div>
                        </div>
                    ))}
                    {loading && (
                        <div className="flex justify-start">
                            <div className="flex items-center gap-2 rounded-lg bg-gray-100 p-3">
                                <Loader2 className="h-4 w-4 animate-spin text-gray-500" />
                                <span className="text-xs text-gray-500">Thinking...</span>
                            </div>
                        </div>
                    )}
                    <div ref={bottomRef} />
                </div>

                <div className="border-t p-4">
                    <div className="flex gap-2">
                        <input
                            className="flex-1 rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                            placeholder="Type your message..."
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
                        />
                        <button
                            onClick={sendMessage}
                            disabled={loading || !input.trim()}
                            className="inline-flex items-center justify-center rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-500 disabled:opacity-50"
                        >
                            <Send className="h-4 w-4" />
                        </button>
                    </div>
                </div>
            </div>
        </DashboardLayout>
    );
}
