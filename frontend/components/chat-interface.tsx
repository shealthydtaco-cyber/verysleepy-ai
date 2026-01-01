"use client"

import { useState, useRef, useEffect } from "react"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Send, User, Bot, Volume2, Sparkles, Languages } from "lucide-react"
import { cn } from "@/lib/utils"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  timestamp: Date
}

export function ChatInterface({ onSwitchToVoice }: { onSwitchToVoice?: () => void }) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      role: "assistant",
      content: "Hello! How can I help you today?",
      timestamp: new Date(),
    },
  ])
  const [inputValue, setInputValue] = useState("")
  const [model, setModel] = useState("blunt")
  const [voice, setVoice] = useState("amy")
  const [memoryEnabled, setMemoryEnabled] = useState(true)
  const [isMemoryPanelOpen, setMemoryPanelOpen] = useState(false)
  const [prefs, setPrefs] = useState<Record<string, string>>({})
  const [longTerm, setLongTerm] = useState<Array<any>>([])
  const [selectedText, setSelectedText] = useState("")
  const [lastSent, setLastSent] = useState<string | null>(null)
  const [memoryStatus, setMemoryStatus] = useState<string | null>(null)
  const scrollRef = useRef<HTMLDivElement>(null)
  const backendUrl = (process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000").replace(/\/$/, "")

  const setPref = async (key: string, value: string) => {
    try {
      await fetch(`${backendUrl}/prefs`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ key, value }),
      })
    } catch (err) {
      console.error('setPref failed', err)
    }
  }

  const fetchMemoryAndPrefs = async () => {
    try {
      const snapRes = await fetch(`${backendUrl}/memory/snapshot`)
      if (snapRes.ok) {
        const snapJson = await snapRes.json()
        setLongTerm(snapJson.facts || [])
        setPrefs(snapJson.prefs || {})
        if (snapJson.prefs && (snapJson.prefs.memory_enabled === 'false' || snapJson.prefs.memory_enabled === '0')) {
          setMemoryEnabled(false)
        } else {
          setMemoryEnabled(true)
        }
        return
      }
    } catch (err) {
      // fallback to older endpoints
      console.error('snapshot fetch failed', err)
    }

    try {
      const memRes = await fetch(`${backendUrl}/memory`)
      const memJson = await memRes.json()
      setLongTerm(memJson.long_term || [])
    } catch (err) {
      console.error('fetch memory failed', err)
    }

    try {
      const prefsRes = await fetch(`${backendUrl}/prefs`)
      const prefsJson = await prefsRes.json()
      setPrefs(prefsJson || {})
      if (prefsJson && (prefsJson.memory_enabled === 'off' || prefsJson.memory_enabled === '0')) {
        setMemoryEnabled(false)
      } else {
        setMemoryEnabled(true)
      }
    } catch (err) {
      // prefs may not exist yet
      console.error('fetch prefs failed', err)
    }
  }

  const rememberText = async (content: string) => {
    try {
      const res = await fetch(`${backendUrl}/memory/remember`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content }),
      })
      if (res.ok) {
        setMemoryStatus('Saved')
        fetchMemoryAndPrefs()
      } else {
        const j = await res.json()
        setMemoryStatus(j?.detail || 'Failed to remember')
      }
    } catch (err) {
      console.error('remember failed', err)
      setMemoryStatus('Request failed')
    } finally {
      setTimeout(() => setMemoryStatus(null), 1500)
    }
  }

  const deleteMemoryItem = async (id: number) => {
    try {
      await fetch(`${backendUrl}/memory/${id}`, { method: 'DELETE' })
      fetchMemoryAndPrefs()
    } catch (err) {
      console.error('delete memory failed', err)
    }
  }

  const toggleMemoryEnabled = async () => {
    const newState = !memoryEnabled
    setMemoryEnabled(newState)
    try {
      await setPref('memory_enabled', newState ? 'on' : 'off')
    } catch (err) {
      console.error('toggle memory pref failed', err)
    }
  }

  const clearMemory = async () => {
    try {
      await fetch(`${backendUrl}/memory/clear`, { method: "POST" })
    } catch (err) {
      console.error('clear memory failed', err)
    }
  }

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return

    const userText = inputValue
    const newUserMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: userText,
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, newUserMessage])
    setLastSent(userText)
    setInputValue("")

    try {
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000"
      const res = await fetch(`${backendUrl.replace(/\/$/, "")}/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ input: userText, mode: model }),
      })

      const json = await res.json()

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: json?.response ?? "Sorry, I couldn't process your request.",
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, assistantMessage])
    } catch (err) {
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: "Network error: couldn't reach backend.",
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, assistantMessage])
    }
  }

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages])

  // selection listener (detect selected text anywhere)
  useEffect(() => {
    const onSelection = () => {
      try {
        const s = window.getSelection()?.toString() || ""
        setSelectedText(s)
      } catch (e) {
        setSelectedText("")
      }
    }
    document.addEventListener("selectionchange", onSelection)
    return () => document.removeEventListener("selectionchange", onSelection)
  }, [])

  // fetch memory/prefs when panel opens
  useEffect(() => {
    if (isMemoryPanelOpen) fetchMemoryAndPrefs()
  }, [isMemoryPanelOpen])

  return (
    <div className="flex flex-col h-screen w-full bg-black text-white shadow-2xl overflow-hidden">
      <div className="p-4 border-b border-white/10 flex items-center justify-between bg-white/5">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-blue-500/20 flex items-center justify-center border border-blue-500/40">
            <Bot className="w-4 h-4 text-blue-400" />
          </div>
          <div>
            <h2 className="text-sm font-semibold">AI Assistant</h2>
            <p className="text-[10px] text-white/40 uppercase tracking-wider">Ethereal Mode</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            className="text-[12px] px-2 py-1 rounded-full bg-white/5 border border-white/10 text-white/70"
            onClick={() => { setMemoryPanelOpen(true) }}
            title="Open memory panel"
          >
            🧠 <span className="ml-2">Memory: {memoryEnabled ? 'ON' : 'OFF'}</span>
          </button>
          <Select
            value={model}
            onValueChange={(v) => {
              setModel(v)
              setPref('mode', v)
            }}
          >
            <SelectTrigger size="sm" className="bg-white/5 border-white/10 text-white/70 h-8 rounded-full px-3">
              <Sparkles className="w-3 h-3 mr-1" />
              <SelectValue placeholder="Model" />
            </SelectTrigger>
            <SelectContent className="bg-neutral-900 border-white/10 text-white">
              <SelectItem value="blunt">Blunt</SelectItem>
              <SelectItem value="critical">Critical</SelectItem>
              <SelectItem value="balanced">Balanced</SelectItem>
              <SelectItem value="extreme">Extreme</SelectItem>
            </SelectContent>
          </Select>

          <Select
            value={voice}
            onValueChange={(v) => {
              setVoice(v)
              setPref('voice', v)
            }}
          >
            <SelectTrigger size="sm" className="bg-white/5 border-white/10 text-white/70 h-8 rounded-full px-3">
              <Languages className="w-3 h-3 mr-1" />
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

          <Button size="sm" variant="ghost" onClick={clearMemory} className="text-xs">
            Clear memory
          </Button>
        </div>
      </div>

      {/* Memory panel (slide-over) */}
      {isMemoryPanelOpen && (
        <div className="fixed right-6 top-20 w-[360px] max-h-[70vh] bg-neutral-900 border border-white/10 rounded-md shadow-2xl p-4 overflow-auto z-50">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold">What I remember about you</h3>
            <div className="flex gap-2 items-center">
              <div className="text-xs text-white/60">Memory: {memoryEnabled ? 'ON' : 'OFF'}</div>
              <Button size="sm" variant="ghost" onClick={toggleMemoryEnabled}>{memoryEnabled ? 'Turn Off' : 'Turn On'}</Button>
              <Button size="sm" variant="ghost" onClick={() => setMemoryPanelOpen(false)}>Close</Button>
            </div>
          </div>

          <div className="mb-4">
            <h4 className="text-xs text-white/60 mb-2">Preferences</h4>
            <div className="space-y-2">
              {Object.keys(prefs).length === 0 && <div className="text-sm text-white/50">No saved preferences.</div>}
              {Object.entries(prefs).map(([k, v]) => (
                <div key={k} className="flex items-center justify-between bg-white/5 p-2 rounded">
                  <div className="text-[13px]">{k}</div>
                  <div className="text-[13px] text-white/60">{v}</div>
                </div>
              ))}
              {memoryStatus && <div className="text-sm mt-2 text-white/70">{memoryStatus}</div>}
            </div>
          </div>

          <div>
            <h4 className="text-xs text-white/60 mb-2">Saved facts</h4>
            <div className="space-y-2">
              {longTerm.length === 0 && <div className="text-sm text-white/50">No saved facts.</div>}
              {longTerm.map((item: any) => (
                <div key={item.id} className="flex items-start justify-between bg-white/5 p-2 rounded">
                  <div className="text-sm">{item.content}</div>
                  <div className="flex flex-col items-end">
                    <div className="text-[11px] text-white/60">{item.source}</div>
                    <Button size="sm" variant="destructive" onClick={() => deleteMemoryItem(item.id)}>Delete</Button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      <ScrollArea className="flex-1 p-6" viewportRef={scrollRef}>
        <div className="space-y-6">
          {messages.map((message) => (
            <div
              key={message.id}
              className={cn("flex gap-3 max-w-[80%]", message.role === "user" ? "ml-auto flex-row-reverse" : "mr-auto")}
            >
              <div
                className={cn(
                  "w-8 h-8 rounded-full shrink-0 flex items-center justify-center border",
                  message.role === "user" ? "bg-white/10 border-white/20" : "bg-blue-500/10 border-blue-500/20",
                )}
              >
                {message.role === "user" ? (
                  <User className="w-4 h-4 text-white/70" />
                ) : (
                  <Bot className="w-4 h-4 text-blue-400" />
                )}
              </div>
              <div className="flex flex-col">
                <div
                  className={cn(
                    "px-4 py-3 rounded-2xl text-sm leading-relaxed",
                    message.role === "user"
                      ? "bg-white text-black font-medium rounded-tr-none"
                      : "bg-white/5 border border-white/10 text-white/90 rounded-tl-none",
                  )}
                >
                  {message.content}
                </div>
                {message.role === "assistant" && (
                  <div className="mt-1 flex gap-2">
                    <button
                      className="text-[11px] text-white/60 hover:text-white"
                      onClick={() => rememberText(message.content)}
                    >
                      Remember
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </ScrollArea>

      <div className="p-4 border-t border-white/10 bg-white/5">
        <div className="flex gap-2 items-center">
          <Input
            placeholder="Type a message..."
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSendMessage()}
            className="bg-white/5 border-white/10 focus-visible:ring-blue-500/50 h-11"
          />
          <Button
            size="sm"
            variant="ghost"
            disabled={!selectedText && !lastSent}
            className={`h-11 rounded-xl px-3 ${(!selectedText && !lastSent) ? 'opacity-50 cursor-not-allowed' : ''}`}
            onClick={() => {
              const content = selectedText ? selectedText : (lastSent || "")
              if (content) {
                rememberText(content)
                setLastSent(null)
                setSelectedText("")
              }
            }}
          >
            Remember this
          </Button>
          <Button
            size="icon"
            variant="ghost"
            onClick={onSwitchToVoice}
            className="h-11 w-11 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 text-white/70"
          >
            <Volume2 className="w-5 h-5" />
          </Button>
          <Button
            size="icon"
            onClick={handleSendMessage}
            className="h-11 w-11 bg-white hover:bg-white/90 text-black rounded-xl shrink-0"
          >
            <Send className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </div>
  )
}
