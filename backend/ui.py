# ui.py
import threading
import queue
import tkinter as tk
from tkinter import ttk, scrolledtext
from main import process_input   # we will add this function
from stt import record_and_transcribe
from tts import speak

result_queue = queue.Queue()

VOICE_MODELS = {
    "English 1": "en_1.onnx",
    "English 2": "en_2.onnx",
    "Telugu 1": "te_1.onnx",
    "Telugu 2": "te_2.onnx",
    "Telugu 3": "te_3.onnx"
}

OPINION_MODES = ["balanced", "critical", "blunt"]

class ChatUI:
    def __init__(self, root):
        root.title("AI Assistant")
        root.geometry("900x600")
        root.configure(bg="#1e1e1e")

        self.chat = scrolledtext.ScrolledText(
            root, bg="#121212", fg="white",
            font=("Consolas", 11), wrap=tk.WORD
        )
        self.chat.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.chat.configure(state=tk.DISABLED)

        # Tag styles for cleaner UI
        self.chat.tag_config(
            "user",
            foreground="#E5E7EB",
            background="#2563EB",
            lmargin1=10, lmargin2=10, rmargin=80
        )
        self.chat.tag_config(
            "ai",
            foreground="#E5E7EB",
            background="#111827",
            lmargin1=80, lmargin2=80, rmargin=10
        )

        bottom = tk.Frame(root, bg="#1e1e1e")
        bottom.pack(fill=tk.X, padx=10, pady=5)

        self.entry = tk.Entry(
            bottom, font=("Segoe UI", 11), bg="#2a2a2a", fg="white"
        )
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.entry.bind("<Return>", self.send_text)

        tk.Button(
            bottom, text="▶", width=3,
            command=self.send_text
        ).pack(side=tk.LEFT)

        tk.Button(
            bottom, text="🎤", width=3,
            command=self.voice_input
        ).pack(side=tk.LEFT, padx=5)

        # status label shown while AI is working
        self.status_label = tk.Label(bottom, text="", foreground="white", background="#1e1e1e")
        self.status_label.pack(side=tk.LEFT, padx=8)

        options = tk.Frame(root, bg="#1e1e1e")
        options.pack(fill=tk.X, padx=10)

        self.mode_var = tk.StringVar(value="blunt")
        ttk.Label(options, text="Mode:", foreground="white", background="#1e1e1e").pack(side=tk.LEFT)
        ttk.Combobox(options, textvariable=self.mode_var, values=OPINION_MODES, width=10).pack(side=tk.LEFT, padx=5)

        self.voice_var = tk.StringVar(value="English 1")
        ttk.Label(options, text="Voice:", foreground="white", background="#1e1e1e").pack(side=tk.LEFT)
        ttk.Combobox(options, textvariable=self.voice_var, values=list(VOICE_MODELS.keys()), width=12).pack(side=tk.LEFT, padx=5)

        # Speak replies checkbox
        self.speak_var = tk.BooleanVar(value=True)
        self.speak_checkbox = tk.Checkbutton(options, text="🔊 Speak replies", variable=self.speak_var, fg="white", bg="#1e1e1e", selectcolor="#1e1e1e")
        self.speak_checkbox.pack(side=tk.LEFT, padx=10)

        # start polling results from background AI thread
        self.poll_results()

    def add_message(self, sender, text):
        tag = "user" if sender.lower() == "you" else ("ai" if sender.lower() == "ai" else "system")
        self.chat.configure(state=tk.NORMAL)
        # header
        self.chat.insert(tk.END, f"{sender}:\n", tag)
        self.chat.insert(tk.END, f"{text}\n\n", tag)
        self.chat.configure(state=tk.DISABLED)
        self.chat.see(tk.END)

    def run_ai_background(self, user_text):
        try:
            response = process_input(user_text, self.mode_var.get())
        except Exception as e:
            response = f"Error: {e}"
        # include selected voice model to play
        voice_model = VOICE_MODELS.get(self.voice_var.get(), None)
        result_queue.put((response, voice_model))

    def poll_results(self):
        try:
            while True:
                response, voice_model = result_queue.get_nowait()
                # add the actual response
                self.add_message("AI", response)
                # voice output in background if enabled
                if voice_model and self.speak_var.get():
                    threading.Thread(target=speak, args=(response, voice_model), daemon=True).start()
                # re-enable input and clear status
                self.entry.config(state=tk.NORMAL)
                self.status_label.config(text="")
        except queue.Empty:
            pass
        # schedule next poll
        self.chat.after(100, self.poll_results)

    def send_text(self, event=None):
        text = self.entry.get().strip()
        if not text:
            return
        self.entry.delete(0, tk.END)
        self.add_message("You", text)

        # disable input while AI is thinking and show status
        self.entry.config(state=tk.DISABLED)
        self.status_label.config(text="Thinking...")

        # run AI in background thread
        threading.Thread(target=self.run_ai_background, args=(text,), daemon=True).start()

    def voice_input(self):
        self.add_message("System", "Listening...")
        text = record_and_transcribe(6)
        self.add_message("You", text)

        # disable input while AI is thinking and show status
        self.entry.config(state=tk.DISABLED)
        self.status_label.config(text="Thinking...")

        threading.Thread(target=self.run_ai_background, args=(text,), daemon=True).start()


if __name__ == "__main__":
    root = tk.Tk()
    ChatUI(root)
    root.mainloop()
