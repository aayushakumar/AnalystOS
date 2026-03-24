"use client";

import { useState } from "react";
import { useChat } from "@/hooks/useChat";
import { ChatPanel } from "@/components/chat/ChatPanel";
import { TracePanel } from "@/components/trace/TracePanel";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  BrainCircuit,
  PanelRightClose,
  PanelRightOpen,
  Plus,
  FlaskConical,
} from "lucide-react";
import Link from "next/link";

export default function HomePage() {
  const chat = useChat();
  const [traceOpen, setTraceOpen] = useState(true);

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-background">
      {/* ── Left Sidebar ── */}
      <aside className="flex w-16 flex-col items-center gap-2 border-r bg-card py-4">
        <Tooltip>
          <TooltipTrigger asChild>
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
              <BrainCircuit className="h-5 w-5 text-primary" />
            </div>
          </TooltipTrigger>
          <TooltipContent side="right">AnalystOS</TooltipContent>
        </Tooltip>

        <Separator className="my-2 w-8" />

        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="h-10 w-10"
              onClick={chat.clearMessages}
            >
              <Plus className="h-5 w-5" />
            </Button>
          </TooltipTrigger>
          <TooltipContent side="right">New Chat</TooltipContent>
        </Tooltip>

        <div className="flex-1" />

        <Tooltip>
          <TooltipTrigger asChild>
            <Link href="/eval">
              <Button variant="ghost" size="icon" className="h-10 w-10">
                <FlaskConical className="h-5 w-5" />
              </Button>
            </Link>
          </TooltipTrigger>
          <TooltipContent side="right">Eval Dashboard</TooltipContent>
        </Tooltip>

        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="h-10 w-10"
              onClick={() => setTraceOpen((o) => !o)}
            >
              {traceOpen ? (
                <PanelRightClose className="h-5 w-5" />
              ) : (
                <PanelRightOpen className="h-5 w-5" />
              )}
            </Button>
          </TooltipTrigger>
          <TooltipContent side="right">
            {traceOpen ? "Hide" : "Show"} Trace Panel
          </TooltipContent>
        </Tooltip>
      </aside>

      {/* ── Center Chat ── */}
      <main className="flex flex-1 flex-col overflow-hidden">
        <ChatPanel
          messages={chat.messages}
          isLoading={chat.isLoading}
          onSend={chat.sendMessage}
        />
      </main>

      {/* ── Right Trace Panel ── */}
      {traceOpen && (
        <aside className="w-[380px] border-l bg-card">
          <TracePanel
            trace={chat.currentTrace}
            liveSteps={chat.liveSteps}
            isLoading={chat.isLoading}
          />
        </aside>
      )}
    </div>
  );
}
