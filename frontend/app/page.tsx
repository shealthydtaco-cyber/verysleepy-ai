"use client"

import { useState } from "react"
import { VoiceInterface } from "@/components/voice-interface"
import { ChatInterface } from "@/components/chat-interface"
import { Button } from "@/components/ui/button"
import { MessageSquare, Mic } from "lucide-react"

export default function Home() {
  const [view, setView] = useState<"voice" | "chat">("voice")

  return (
    <main className="min-h-screen bg-neutral-950 flex items-center justify-center p-0 m-0 overflow-hidden">
      <div className="w-full h-screen flex flex-col justify-center">
        <div className="animate-in fade-in zoom-in-95 duration-500 flex-1 flex flex-col justify-center">
          {view === "voice" ? (
            <VoiceInterface onSwitchToChat={() => setView("chat")} />
          ) : (
            <ChatInterface onSwitchToVoice={() => setView("voice")} />
          )}
        </div>
      </div>
    </main>
  )
}
