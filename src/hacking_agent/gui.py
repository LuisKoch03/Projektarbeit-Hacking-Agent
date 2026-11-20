"""Small Tkinter chat interface for the hacking agent."""

from dataclasses import replace
import shutil
import subprocess
import threading
import tkinter as tk
from tkinter import messagebox, ttk

from openai import BadRequestError, OpenAI

from .config import Settings
from .llm import create_agent, ollama_model_capabilities
from .paths import COMPOSE_FILE, PROJECT_ROOT


class AgentWindow:
    """Configure a model and chat with the agent."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Hacking Agent")
        self.root.geometry("850x650")
        self.messages: list[dict[str, str]] = []

        self.provider = tk.StringVar(value="ollama")
        self.model = tk.StringVar()
        self.base_url = tk.StringVar(value="https://api.openai.com/v1")
        self.api_model = tk.StringVar()
        self.api_key = tk.StringVar()
        self.status = tk.StringVar(value="Bereit")

        settings = ttk.LabelFrame(root, text="KI-Modell", padding=8)
        settings.pack(fill="x", padx=10, pady=(10, 5))
        ttk.Radiobutton(
            settings,
            text="Ollama lokal",
            variable=self.provider,
            value="ollama",
            command=self._update_provider,
        ).grid(row=0, column=0, sticky="w")
        ttk.Radiobutton(
            settings,
            text="OpenAI-kompatible API",
            variable=self.provider,
            value="openai",
            command=self._update_provider,
        ).grid(row=0, column=1, sticky="w", padx=(15, 0))
        ttk.Button(settings, text="Modelle neu laden", command=self.load_models).grid(
            row=0, column=2, sticky="e"
        )

        self.models_frame = ttk.Frame(settings)
        self.models_frame.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(6, 0))
        self.api_frame = ttk.Frame(settings)
        self.api_frame.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(6, 0))
        ttk.Label(self.api_frame, text="Base URL").grid(row=0, column=0, sticky="w")
        ttk.Entry(self.api_frame, textvariable=self.base_url, width=36).grid(
            row=0, column=1, padx=5, sticky="ew"
        )
        ttk.Label(self.api_frame, text="Modell").grid(row=0, column=2, sticky="w")
        ttk.Entry(self.api_frame, textvariable=self.api_model, width=20).grid(
            row=0, column=3, padx=5, sticky="ew"
        )
        ttk.Label(self.api_frame, text="API-Key").grid(row=1, column=0, sticky="w")
        ttk.Entry(self.api_frame, textvariable=self.api_key, show="*").grid(
            row=1, column=1, columnspan=3, padx=5, pady=(5, 0), sticky="ew"
        )
        self.api_frame.columnconfigure(1, weight=1)
        self.api_frame.columnconfigure(3, weight=1)
        settings.columnconfigure(2, weight=1)

        self.chat = tk.Text(root, wrap="word", state="disabled")
        self.chat.pack(fill="both", expand=True, padx=10, pady=5)
        entry_frame = ttk.Frame(root)
        entry_frame.pack(fill="x", padx=10, pady=5)
        self.prompt = ttk.Entry(entry_frame)
        self.prompt.pack(side="left", fill="x", expand=True)
        self.prompt.bind("<Return>", lambda _event: self.send())
        self.send_button = ttk.Button(entry_frame, text="Senden", command=self.send)
        self.send_button.pack(side="left", padx=(6, 0))
        ttk.Label(root, textvariable=self.status).pack(anchor="w", padx=10, pady=(0, 8))

        self._update_provider()
        self.load_models()
        self.send_button.configure(state="disabled")
        self.status.set("Docker-Tools werden vorbereitet …")
        threading.Thread(target=self._prepare_runtime, daemon=True).start()
        self.prompt.focus_set()

    def _prepare_runtime(self) -> None:
        """Build tool images and start ZAP on the first application launch."""
        docker = shutil.which("docker")
        if docker is None or not COMPOSE_FILE.is_file():
            self.root.after(
                0,
                self._runtime_ready,
                "Docker Desktop oder compose.yaml fehlt; Chat bleibt verfügbar.",
            )
            return

        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        commands = [
            [docker, "compose", "-f", str(COMPOSE_FILE), "build", "nmap", "hashcat"],
            [docker, "compose", "-f", str(COMPOSE_FILE), "up", "-d", "zap"],
        ]
        try:
            for command in commands:
                result = subprocess.run(
                    command,
                    cwd=PROJECT_ROOT,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=1800,
                    check=False,
                    shell=False,
                    creationflags=flags,
                )
                if result.returncode:
                    detail = result.stderr.strip() or result.stdout.strip()
                    raise RuntimeError(detail or f"Docker Exit-Code {result.returncode}")
        except (OSError, RuntimeError, subprocess.TimeoutExpired) as error:
            self.root.after(0, self._runtime_ready, f"Docker-Setup fehlgeschlagen: {error}")
            return
        self.root.after(0, self._runtime_ready, "Bereit")

    def _runtime_ready(self, status: str) -> None:
        self.status.set(status)
        self.send_button.configure(state="normal")

    def _update_provider(self) -> None:
        if self.provider.get() == "openai":
            self.api_frame.grid()
            self.models_frame.grid_remove()
        else:
            self.models_frame.grid()
            self.api_frame.grid_remove()

    def load_models(self) -> None:
        for child in self.models_frame.winfo_children():
            child.destroy()
        try:
            base_url = Settings.from_env().base_url
            with OpenAI(
                api_key="ollama", base_url=base_url, timeout=5, max_retries=0
            ) as client:
                all_models = sorted({item.id for item in client.models.list()})
        except Exception as error:
            all_models = []
            self.status.set(f"Ollama nicht erreichbar: {error}")

        if not all_models:
            ttk.Label(self.models_frame, text="Keine lokalen Modelle gefunden.").pack(
                anchor="w"
            )
            self.provider.set("openai")
            self._update_provider()
            return

        settings = Settings.from_env()
        models = all_models
        hidden_models: list[str] = []
        capability_check_failed = False
        if settings.enable_tools:
            tool_models: list[str] = []
            for name in all_models:
                try:
                    capabilities = ollama_model_capabilities(settings, name)
                except Exception:
                    capability_check_failed = True
                    break
                if "tools" in capabilities:
                    tool_models.append(name)
                else:
                    hidden_models.append(name)

            if not capability_check_failed:
                models = tool_models

        if not models:
            ttk.Label(
                self.models_frame,
                text=(
                    "Kein installiertes Ollama-Modell unterstützt Tools. "
                    "Bitte ein Tool-Calling-Modell installieren."
                ),
            ).pack(anchor="w")
            self.model.set("")
            self.status.set("Kein toolfähiges Ollama-Modell gefunden")
            return

        for name in models:
            ttk.Radiobutton(
                self.models_frame, text=name, variable=self.model, value=name
            ).pack(side="left", padx=(0, 12))
        if self.model.get() not in models:
            self.model.set(models[0])
        if hidden_models and not capability_check_failed:
            self.status.set(
                f"{len(models)} toolfähige(s) Modell(e); "
                f"{len(hidden_models)} Textmodell(e) ausgeblendet"
            )
        elif capability_check_failed:
            self.status.set(
                f"{len(models)} Modell(e) gefunden; Toolfähigkeit wird beim Aufruf geprüft"
            )
        else:
            self.status.set(f"{len(models)} Ollama-Modell(e) gefunden")

    def _selected_settings(self) -> Settings:
        settings = Settings.from_env()
        if self.provider.get() == "ollama":
            model = self.model.get().strip()
            if not model:
                raise ValueError("Bitte ein Ollama-Modell auswählen.")
            return replace(settings, provider="ollama", model=model)

        key = self.api_key.get().strip()
        model = self.api_model.get().strip()
        base_url = self.base_url.get().strip()
        if not key or not model or not base_url:
            raise ValueError("Für die API werden Base URL, Modell und API-Key benötigt.")
        return replace(
            settings,
            provider="openai",
            api_key=key,
            base_url=base_url,
            model=model,
        )

    def _append(self, role: str, content: str) -> None:
        self.chat.configure(state="normal")
        self.chat.insert("end", f"{role}: {content}\n\n")
        self.chat.configure(state="disabled")
        self.chat.see("end")

    def send(self) -> None:
        prompt = self.prompt.get().strip()
        if not prompt:
            return
        try:
            settings = self._selected_settings()
        except ValueError as error:
            messagebox.showerror("Konfiguration", str(error))
            return

        self.prompt.delete(0, "end")
        self._append("Du", prompt)
        self.messages.append({"role": "user", "content": prompt})
        self.send_button.configure(state="disabled")
        self.status.set("Agent arbeitet …")
        threading.Thread(target=self._request, args=(settings,), daemon=True).start()

    def _request(self, settings: Settings) -> None:
        try:
            try:
                result = create_agent(settings).invoke({"messages": self.messages})
            except BadRequestError as error:
                if (
                    settings.provider != "ollama"
                    or "does not support tools" not in str(error).lower()
                ):
                    raise
                raise ValueError(
                    f"Das Modell '{settings.model}' unterstützt keine Tool-Aufrufe. "
                    "Bitte unter 'Ollama lokal' ein toolfähiges Modell wählen "
                    "und die Modelle neu laden."
                )
            content = str(result["messages"][-1].content)
        except Exception as error:
            self.root.after(0, self._finish_error, str(error))
            return
        self.root.after(0, self._finish, content)

    def _finish(self, content: str) -> None:
        self.messages.append({"role": "assistant", "content": content})
        self._append("Agent", content)
        self.status.set("Bereit")
        self.send_button.configure(state="normal")
        self.prompt.focus_set()

    def _finish_error(self, error: str) -> None:
        self._append("Fehler", error)
        self.status.set("Fehler")
        self.send_button.configure(state="normal")


def main() -> None:
    root = tk.Tk()
    AgentWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()
