"use client";

import { useEffect, useRef } from "react";
import type { ChatMessage } from "@/lib/types";
import { MessageBubble } from "./MessageBubble";
import { InputBar } from "./InputBar";
import { ScrollArea } from "@/components/ui/scroll-area";
import { BrainCircuit, Sparkles } from "lucide-react";

interface ChatPanelProps {
  messages: ChatMessage[];
  isLoading: boolean;
  onSend: (message: string) => void;
}

const EXAMPLE_QUESTIONS = [
  "What was our total revenue last quarter?",
  "Show me the top 10 customers by lifetime value",
  "Compare monthly order counts year over year",
  "What's the average order value by product category?",
];

export function ChatPanel({ messages, isLoading, onSend }: ChatPanelProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const isEmpty = messages.length === 0;

  return (
    <div className="flex h-full flex-col">
      {isEmpty ? (
        <div className="flex flex-1 flex-col items-center justify-center gap-8 px-4">
          <div className="flex flex-col items-center gap-4">
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/10">
              <BrainCircuit className="h-8 w-8 text-primary" />
            </div>
            <div className="text-center">
              <h1 className="text-2xl font-semibold tracking-tight">
                AnalystOS
              </h1>
              <p className="mt-1 text-sm text-muted-foreground">
                Ask any question about your data. I&apos;ll write the SQL,
                run it, and explain the results.
              </p>
            </div>
          </div>

          <div className="grid w-full max-w-2xl grid-cols-2 gap-3">
            {EXAMPLE_QUESTIONS.map((q) => (
              <button
                key={q}
                onClick={() => onSend(q)}
                className="group flex items-start gap-3 rounded-lg border border-border/50 bg-card p-4 text-left text-sm transition-all hover:border-primary/30 hover:bg-accent"
              >
                <Sparkles className="mt-0.5 h-4 w-4 shrink-0 text-primary/60 transition-colors group-hover:text-primary" />
                <span className="text-muted-foreground transition-colors group-hover:text-foreground">
                  {q}
                </span>
              </button>
            ))}
          </div>
        </div>
      ) : (
        <ScrollArea className="flex-1">
          <div className="mx-auto max-w-3xl space-y-1 px-4 py-6">
            {messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}
            {isLoading && (
              <div className="flex items-center gap-2 px-4 py-3">
                <div className="flex gap-1">
                  <span className="h-2 w-2 animate-bounce rounded-full bg-primary/60 [animation-delay:0ms]" />
                  <span className="h-2 w-2 animate-bounce rounded-full bg-primary/60 [animation-delay:150ms]" />
                  <span className="h-2 w-2 animate-bounce rounded-full bg-primary/60 [animation-delay:300ms]" />
                </div>
                <span className="text-sm text-muted-foreground">
                  Analyzing...
                </span>
              </div>
            )}
            <div ref={bottomRef} />
          </div>
        </ScrollArea>
      )}

      <div className="border-t bg-card/50 p-4">
        <div className="mx-auto max-w-3xl">
          <InputBar onSend={onSend} isLoading={isLoading} />
        </div>
      </div>
    </div>
  );
}
