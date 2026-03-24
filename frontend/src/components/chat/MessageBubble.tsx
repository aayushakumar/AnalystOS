"use client";

import type { ChatMessage } from "@/lib/types";
import { AnswerCard } from "@/components/answer/AnswerCard";
import { BrainCircuit, User } from "lucide-react";
import { cn } from "@/lib/utils";

interface MessageBubbleProps {
  message: ChatMessage;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";

  if (isUser) {
    return (
      <div className="flex justify-end py-2">
        <div className="flex max-w-[80%] items-start gap-3">
          <div className="rounded-2xl rounded-tr-sm bg-primary px-4 py-2.5 text-sm text-primary-foreground">
            {message.content}
          </div>
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/20">
            <User className="h-4 w-4 text-primary" />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex py-2">
      <div
        className={cn(
          "flex max-w-full items-start gap-3",
          message.answer ? "w-full" : "max-w-[80%]"
        )}
      >
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-accent">
          <BrainCircuit className="h-4 w-4 text-primary" />
        </div>
        {message.answer ? (
          <div className="min-w-0 flex-1">
            <AnswerCard answer={message.answer} />
          </div>
        ) : (
          <div className="rounded-2xl rounded-tl-sm bg-accent px-4 py-2.5 text-sm">
            {message.content}
          </div>
        )}
      </div>
    </div>
  );
}
