"use client"

import { useState } from "react"
import { VoiceInterface } from "@/components/voice-interface"
import { ChatInterface } from "@/components/chat-interface"
import { Button } from "@/components/ui/button"
import { MessageSquare, Mic } from "lucide-react"

export default function Home() {
  const [view, setView] = useState<"voice" | "chat">("voice")

  return (
    <main className="min-h-screen bg-neutral-950 flex flex-col items-center justify-center p-4">
      <div className="w-full max-w-5xl space-y-8">
        <div className="text-center space-y-2 flex flex-col items-center">
          <div className="flex items-center gap-4 mb-2">
            <Button
              variant={view === "voice" ? "default" : "outline"}
              size="sm"
              onClick={() => setView("voice")}
              className="rounded-full gap-2"
            >
              <Mic className="w-4 h-4" />
              Voice
            </Button>
            <Button
              variant={view === "chat" ? "default" : "outline"}
              size="sm"
              onClick={() => setView("chat")}
              className="rounded-full gap-2"
            >
              <MessageSquare className="w-4 h-4" />
              Chat
            </Button>
          </div>
          <h1 className="text-4xl font-bold tracking-tight text-white">Ethereal AI</h1>
          <p className="text-neutral-500">Advanced Fluid Intelligence Interface</p>
        </div>

        <div className="animate-in fade-in zoom-in-95 duration-500">
          {view === "voice" ? (
            <VoiceInterface onSwitchToChat={() => setView("chat")} />
          ) : (
            <ChatInterface onSwitchToVoice={() => setView("voice")} />
          )}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-12">
          <FeatureCard
            title="Fluid Ambience"
            description="Dynamic wave animations that respond to voice activity and system state."
          />
          <FeatureCard
            title="Ethereal Orb"
            description="A high-performance WebGL visualizer enclosed in a glass-morphism bubble."
          />
          <FeatureCard
            title="State Feedback"
            description="Clear visual communication through color shifts and pulsing motion patterns."
          />
        </div>
      </div>
    </main>
  )
}

function FeatureCard({ title, description }: { title: string; description: string }) {
  return (
    <div className="p-6 rounded-2xl bg-white/5 border border-white/10">
      <h3 className="text-white font-semibold mb-2">{title}</h3>
      <p className="text-neutral-400 text-sm leading-relaxed">{description}</p>
    </div>
  )
}
