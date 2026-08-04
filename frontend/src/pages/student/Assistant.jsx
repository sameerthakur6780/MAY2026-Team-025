import { useState, useRef, useEffect } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import { STUDENT_NAV } from "@/lib/navConfig";
import { CHAT_STARTERS, mockAssistantReply } from "@/lib/mockData";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Sparkles, Send, Bot, User } from "lucide-react";

export default function StudentAssistant() {
  const [messages, setMessages] = useState([
    { role: "assistant", content: "Hi Aarav! I'm your SmartBatch AI assistant. Ask me about homework, tests, timetable or any concept you're stuck on." },
  ]);
  const [input, setInput] = useState("");
  const [typing, setTyping] = useState(false);
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, typing]);

  const send = (text) => {
    const q = (text ?? input).trim();
    if (!q) return;
    setMessages(m => [...m, { role: "user", content: q }]);
    setInput("");
    setTyping(true);
    setTimeout(() => {
      setMessages(m => [...m, { role: "assistant", content: mockAssistantReply(q) }]);
      setTyping(false);
    }, 700);
  };

  return (
    <DashboardLayout title="AI Assistant" subtitle="Your personal tutor bot. Ask anything." nav={STUDENT_NAV}>
      <Card className="border-soft shadow-none">
        <CardContent className="p-0">
          <div className="flex items-center gap-3 p-5 border-b border-soft">
            <div className="w-10 h-10 rounded-xl bg-forest flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="font-display font-semibold text-[#1C1C1C]">SmartBatch Assistant</div>
              <div className="text-xs text-forest inline-flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-forest animate-pulse" /> Online
              </div>
            </div>
          </div>

          <div className="h-[440px] overflow-y-auto p-6 space-y-4" data-testid="chat-scroll">
            {messages.map((m, i) => (
              <div key={i} data-testid={`msg-${i}`} className={`flex gap-3 ${m.role === "user" ? "flex-row-reverse" : ""}`}>
                <div className={`w-8 h-8 rounded-full shrink-0 flex items-center justify-center ${m.role === "user" ? "bg-terracotta text-white" : "bg-sage text-forest"}`}>
                  {m.role === "user" ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                </div>
                <div className={`max-w-[75%] rounded-2xl p-3.5 text-sm leading-relaxed ${m.role === "user" ? "bg-forest text-white rounded-tr-sm" : "bg-[#F0EEE8] text-[#1C1C1C] rounded-tl-sm"}`}>
                  {m.content}
                </div>
              </div>
            ))}
            {typing && (
              <div className="flex gap-3">
                <div className="w-8 h-8 rounded-full bg-sage flex items-center justify-center"><Bot className="w-4 h-4 text-forest" /></div>
                <div className="bg-[#F0EEE8] rounded-2xl rounded-tl-sm p-3.5">
                  <div className="flex gap-1">
                    <span className="w-2 h-2 rounded-full bg-[#5C5C5C] animate-pulse" />
                    <span className="w-2 h-2 rounded-full bg-[#5C5C5C] animate-pulse" style={{ animationDelay: "0.15s" }} />
                    <span className="w-2 h-2 rounded-full bg-[#5C5C5C] animate-pulse" style={{ animationDelay: "0.3s" }} />
                  </div>
                </div>
              </div>
            )}
            <div ref={endRef} />
          </div>

          {messages.length <= 1 && (
            <div className="px-6 pb-4 flex flex-wrap gap-2">
              {CHAT_STARTERS.map((s, i) => (
                <button key={i} data-testid={`starter-${i}`} onClick={() => send(s)}
                  className="px-3 py-1.5 rounded-full border border-soft text-xs font-medium text-[#5C5C5C] hover:border-forest hover:text-forest transition-colors">
                  {s}
                </button>
              ))}
            </div>
          )}

          <form onSubmit={e => { e.preventDefault(); send(); }} className="flex items-center gap-3 p-5 border-t border-soft" data-testid="chat-form">
            <Input data-testid="chat-input" value={input} onChange={e => setInput(e.target.value)} placeholder="Ask your doubt…" className="border-soft" />
            <Button type="submit" data-testid="chat-send-btn" className="bg-forest hover:bg-[#162D24] text-white gap-2 rounded-full px-5"><Send className="w-4 h-4" /> Send</Button>
          </form>
        </CardContent>
      </Card>
    </DashboardLayout>
  );
}
