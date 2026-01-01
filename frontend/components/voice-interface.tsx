"use client"

import { useState, useRef } from "react"
import { AIOrbContainer } from "./ai-orb"
import { Button } from "@/components/ui/button"
import { Mic, MicOff, Send, X, Volume2, Settings2, Sparkles, Languages } from "lucide-react"
import { cn } from "@/lib/utils"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

type InteractionState = "idle" | "listening" | "speaking"

export function VoiceInterface({ onSwitchToChat }: { onSwitchToChat?: () => void }) {
  const [state, setState] = useState<InteractionState>("idle")
  const [isMuted, setIsMuted] = useState(false)
  const [model, setModel] = useState("blunt")
  const [voice, setVoice] = useState("amy")

  const voiceMap: { [k: string]: string } = {
    amy: "en_US-amy-medium.onnx",
    sam: "en_US-sam-medium.onnx",
    maya: "te_IN-maya-medium.onnx",
    venkatesh: "te_IN-venkatesh-medium.onnx",
    padmavathi: "te_IN-padmavathi-medium.onnx",
  }

  // Recording & playback state
  const [isRecording, setIsRecording] = useState(false)
  const [transcript, setTranscript] = useState<string | null>(null)
  const [assistantReply, setAssistantReply] = useState<string | null>(null)
  const [playbackId, setPlaybackId] = useState<string | null>(null)
  const [memoryConfirmation, setMemoryConfirmation] = useState<{ candidate: string; disallowed: string | null } | null>(null)
  const [memoryStatus, setMemoryStatus] = useState<string | null>(null)

  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const recordedChunksRef = useRef<Blob[]>([])

  const backendUrl = (process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000").replace(/\/$/, "")

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mediaRecorder = new MediaRecorder(stream)
      recordedChunksRef.current = []

      mediaRecorder.ondataavailable = (e: BlobEvent) => {
        if (e.data.size > 0) recordedChunksRef.current.push(e.data)
      }

      mediaRecorder.onstop = async () => {
        setIsRecording(false)
        setState("speaking")

        const blob = new Blob(recordedChunksRef.current, { type: recordedChunksRef.current[0]?.type || "audio/webm" })
        const form = new FormData()
        form.append("file", blob, "input.webm")

        try {
          const res = await fetch(`${backendUrl}/stt`, { method: "POST", body: form })
          const j = await res.json()
          const text = j?.transcript ?? ""
          setTranscript(text)

          const containsMemoryCommand = !!j?.contains_memory_command
          const disallowedReason = j?.disallowed_memory_reason ?? null

          // If transcript contains explicit 'remember' command, require confirmation before saving.
          if (containsMemoryCommand) {
            // show confirmation UI instead of automatically saving
            setMemoryConfirmation({ candidate: text, disallowed: disallowedReason })
          }

          // Send to assistant; mark source as 'voice' so backend won't auto-save long-term memory
          const qRes = await fetch(`${backendUrl}/query`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ input: text, mode: model, source: 'voice' }),
          })
          const qj = await qRes.json()
          const reply = qj?.output ?? qj?.text ?? ''
          setAssistantReply(reply)
          const speakRes = await fetch(`${backendUrl}/speak`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text: reply, voice: voiceMap[voice] ?? "en_US-lessac", volume: 1.0 }),
          })
          const sj = await speakRes.json()
          setPlaybackId(sj?.id ?? null)
        } catch (err) {
          console.error(err)
        } finally {
          setState("idle")
        }
      }

      mediaRecorderRef.current = mediaRecorder
      mediaRecorder.start()
      setIsRecording(true)
      setState("listening")
    } catch (err) {
      console.error("Microphone access failed:", err)
    }
  }

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      mediaRecorderRef.current.stop()
      // stop all tracks
      mediaRecorderRef.current.stream.getTracks().forEach((t) => t.stop())
    }
  }

  const toggleListening = () => {
    if (isRecording) stopRecording()
    else startRecording()
  }

  const stopPlayback = async () => {
    if (!playbackId) return
    try {
      await fetch(`${backendUrl}/speak/${playbackId}/stop`, { method: "POST" })
    } catch (err) {
      console.error(err)
    } finally {
      setPlaybackId(null)
    }
  }

  return (
    <div className="flex flex-col items-center justify-between min-h-[600px] w-full max-w-4xl mx-auto bg-black text-white p-6 rounded-3xl border border-white/10 shadow-2xl overflow-hidden relative">
      {/* Header */}
      <div className="w-full flex items-center justify-between z-10">
        <div className="flex flex-col">
          <h2 className="text-sm font-medium tracking-widest uppercase opacity-50">Voice Assistant</h2>
          <div className="flex items-center gap-3 mt-1">
            <Select value={model} onValueChange={setModel}>
              <SelectTrigger
                size="sm"
                className="bg-white/5 border-white/10 text-white h-8 rounded-full px-3 hover:bg-white/10 transition-colors"
              >
                <Sparkles className="w-3 h-3 mr-1 opacity-50" />
                <SelectValue placeholder="Model" />
              </SelectTrigger>
              <SelectContent className="bg-neutral-900 border-white/10 text-white">
                <SelectItem value="blunt">Blunt</SelectItem>
                <SelectItem value="critical">Critical</SelectItem>
                <SelectItem value="balanced">Balanced</SelectItem>
                <SelectItem value="extreme">Extreme</SelectItem>
              </SelectContent>
            </Select>

            <Select value={voice} onValueChange={setVoice}>
              <SelectTrigger
                size="sm"
                className="bg-white/5 border-white/10 text-white h-8 rounded-full px-3 hover:bg-white/10 transition-colors"
              >
                <Languages className="w-3 h-3 mr-1 opacity-50" />
                <SelectValue placeholder="Voice" />
              </SelectTrigger>
              <SelectContent className="bg-neutral-900 border-white/10 text-white">
                <SelectItem value="amy">Amy (US)</SelectItem>
                <SelectItem value="sam">Sam (US)</SelectItem>
                <SelectItem value="maya">Maya (IN)</SelectItem>
                <SelectItem value="venkatesh">Venkatesh (IN)</SelectItem>
                <SelectItem value="padmavathi">Padmavathi (IN)</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="icon" className="rounded-full hover:bg-white/10">
            <Settings2 className="w-5 h-5" />
          </Button>
          <Button variant="ghost" size="icon" className="rounded-full hover:bg-white/10">
            <X className="w-5 h-5" />
          </Button>
        </div>
      </div>

      {/* Central Visualizer */}
      <div className="flex-1 w-full flex flex-col items-center justify-center">
        <AIOrbContainer state={state} />

        <div className="mt-8 text-center animate-in fade-in slide-in-from-bottom-4 duration-700">
          <p
            className={cn(
              "text-lg font-medium transition-all duration-500",
              state === "listening" ? "text-blue-400" : state === "speaking" ? "text-pink-400" : "text-white/40",
            )}
          >
            {state === "listening" ? "I'm listening..." : state === "speaking" ? "Processing..." : "Ready to chat"}
          </p>
          <p className="text-sm text-white/40 mt-1 italic">
            {state === "listening"
              ? "Speak naturally, I'm here."
              : state === "speaking"
                ? "Working on your request."
                : "Tap the mic to start."}
          </p>

          {transcript && (
            <p className="text-sm text-white/70 mt-3">Transcript: <span className="font-medium">{transcript}</span></p>
          )}

          {memoryConfirmation && (
            <div className="mt-3 p-3 bg-white/5 rounded">
              <div className="text-sm text-white/70">You said to remember:</div>
              <div className="mt-1 text-sm font-medium">{memoryConfirmation.candidate}</div>
              {memoryConfirmation.disallowed ? (
                <div className="mt-2 text-xs text-red-400">Cannot save this kind of content: {memoryConfirmation.disallowed}</div>
              ) : (
                <div className="mt-2 flex gap-2 items-center">
                  <Button size="sm" onClick={async () => {
                    try {
                      const res = await fetch(`${backendUrl}/memory/remember`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ content: memoryConfirmation.candidate, source: 'voice' })
                      })
                      if (res.ok) {
                        setMemoryStatus('Saved')
                      } else {
                        const j = await res.json()
                        setMemoryStatus(j?.detail || 'Failed')
                      }
                    } catch (err) {
                      setMemoryStatus('Request failed')
                    } finally {
                      setTimeout(() => { setMemoryStatus(null); setMemoryConfirmation(null) }, 1200)
                    }
                  }}>Remember</Button>
                  <Button size="sm" variant="ghost" onClick={() => setMemoryConfirmation(null)}>Dismiss</Button>
                  {memoryStatus && <div className="text-xs text-white/60 ml-2">{memoryStatus}</div>}
                </div>
              )}
            </div>
          )}

          {assistantReply && (
            <p className="text-sm text-white/70 mt-2">Reply: <span className="font-medium">{assistantReply}</span></p>
          )}
        </div>
      </div>

      {/* Controls */}
      <div className="w-full flex flex-col items-center gap-6 z-10 pb-4">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setIsMuted(!isMuted)}
            className={cn(
              "w-12 h-12 rounded-full border border-white/10 transition-colors",
              isMuted && "bg-red-500/20 text-red-400 border-red-500/40",
            )}
          >
            {isMuted ? <MicOff className="w-5 h-5" /> : <Volume2 className="w-5 h-5" />}
          </Button>

          <Button
            onClick={toggleListening}
            className={cn(
              "w-20 h-20 rounded-full transition-all duration-500 shadow-xl border-4",
              isRecording
                ? "bg-red-500 hover:bg-red-600 border-red-500/20 scale-110"
                : "bg-white hover:bg-white/90 border-white/20",
            )}
          >
            {isRecording ? (
              <div className="w-6 h-6 bg-white rounded-sm" />
            ) : (
              <Mic className="w-8 h-8 text-black" />
            )}
          </Button>

          {playbackId ? (
            <Button variant="ghost" size="icon" className="w-12 h-12 rounded-full border border-white/10" onClick={stopPlayback}>
              <X className="w-5 h-5" />
            </Button>
          ) : (
            <Button
              variant="ghost"
              size="icon"
              className="w-12 h-12 rounded-full border border-white/10"
              onClick={async () => {
                // quick test: speak a short phrase
                try {
                  const voiceMap: { [k: string]: string } = {
                    amy: "en_US-amy-medium.onnx",
                    sam: "en_US-sam-medium.onnx",
                    maya: "te_IN-maya-medium.onnx",
                    venkatesh: "te_IN-venkatesh-medium.onnx",
                    padmavathi: "te_IN-padmavathi-medium.onnx",
                  }
                  const res = await fetch(`${backendUrl}/speak`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ text: "Hello from the UI", voice: voiceMap[voice] ?? "en_US-lessac" }),
                  })
                  const j = await res.json()
                  setPlaybackId(j?.id ?? null)
                } catch (err) {
                  console.error(err)
                }
              }}
            >
              <Send className="w-5 h-5" />
            </Button>
          )}
        </div>

        <button
          onClick={onSwitchToChat}
          className="text-xs uppercase tracking-[0.2em] text-white/30 hover:text-white/60 transition-colors"
        >
          Return to Chat
        </button>
      </div>

      {/* Subtle Background Glows */}
      <div
        className={cn(
          "absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] rounded-full blur-[120px] transition-all duration-1000 opacity-20",
          state === "listening" ? "bg-blue-600" : state === "speaking" ? "bg-pink-600" : "bg-white/10",
        )}
      />
    </div>
  )
}
