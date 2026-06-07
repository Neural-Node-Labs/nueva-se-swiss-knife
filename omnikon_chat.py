#!/usr/bin/env python3
import os
import sys
import json
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QComboBox,
    QGroupBox, QSpinBox, QSplitter
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

# CONFIGURATION PERSISTENCE PATH
CONFIG_FILE_PATH = "omnikon_config.json"

# GLOBAL DYNAMIC AI ENGINE PROVIDERS MAPPING MATRIX
AI_PROVIDERS_MATRIX = {
    "DeepSeek": {
        "base_url": "https://api.deepseek.com/v1",
        "models": ["deepseek-chat", "deepseek-coder", "deepseek-reasoner"]
    },
    "GPT (OpenAI)": {
        "base_url": "https://api.openai.com/v1",
        "models": ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "o1-mini", "o3-mini"]
    },
    "Antropy (Anthropic)": {
        "base_url": "https://api.anthropic.com/v1",
        "models": ["claude-3-5-sonnet-latest", "claude-3-5-haiku-latest", "claude-3-opus-latest"]
    },
    "Gemini (Google)": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta",
        "models": ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-1.5-flash", "gemini-1.5-pro"]
    },
    "Grok (xAI)": {
        "base_url": "https://api.x.ai/v1",
        "models": ["grok-2-1212", "grok-beta", "grok-vision-beta"]
    }
}

# EXCLUSIVE JARVIS THEME STYLESHEET
JARVIS_STYLE = """
    QMainWindow, QDialog {
        background-color: #040d1a;
    }
    QLabel {
        color: #c8e0ff;
        font-family: 'Share Tech Mono', monospace;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    QLineEdit {
        background-color: #041020;
        border: 1px solid #0e2d5a;
        border-radius: 3px;
        padding: 8px;
        color: #00d4ff;
        font-family: 'Share Tech Mono', monospace;
    }
    QLineEdit:focus {
        border: 1px solid #00d4ff;
    }
    QTextEdit {
        background-color: #040d1a;
        border: 1px solid #0e2d5a;
        border-radius: 4px;
        color: #00ff88;
        padding: 10px;
        font-family: 'Share Tech Mono', monospace;
        font-size: 13px;
    }
    QComboBox, QSpinBox {
        background-color: #041020;
        border: 1px solid #0e2d5a;
        border-radius: 3px;
        padding: 6px;
        color: #00d4ff;
        font-family: 'Share Tech Mono', monospace;
    }
    QComboBox::drop-down, QSpinBox::drop-down {
        border-left: 1px solid #0e2d5a;
    }
    QPushButton {
        background-color: #071428;
        border: 1px solid #0e2d5a;
        border-radius: 3px;
        padding: 10px 16px;
        color: #00d4ff;
        font-family: 'Share Tech Mono', monospace;
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    QPushButton:hover {
        background-color: #0a213f;
        border: 1px solid #00d4ff;
        color: #fff;
    }
    QPushButton:disabled {
        background-color: #020810;
        color: #2a405a;
        border: 1px solid #041428;
    }
    QGroupBox {
        border: 1px solid #0e2d5a;
        border-radius: 4px;
        margin-top: 15px;
        padding-top: 15px;
        color: #00d4ff;
        font-family: 'Share Tech Mono', monospace;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    QSplitter::handle {
        background-color: #0e2d5a;
    }
"""

# ── ASYNC WORKER PIPELINE COGNITION ENGINE ────────────────────────────────
class OmnikonSwarmProcessorWorker(QThread):
    log_signal = pyqtSignal(str)
    completed_signal = pyqtSignal(str)

    def __init__(self, provider, model, api_key, swarm_count, task, workspace):
        super().__init__()
        self.provider = provider
        self.model = model
        self.api_key = api_key
        self.swarm_count = swarm_count
        self.task = task

        if not os.path.exists(workspace):
            os.makedirs(workspace)
            print(f"Workspace created at: {workspace}")
        else:
            print(f"Workspace already exists at: {workspace}")
        self.workspace = workspace

    def run(self):
        try:
            self.log_signal.emit("⚡ ENGAGING OMNIKON SYSTEM PROTOCOLS FROM ORCHESTRATION LAYER...")
            base_url = AI_PROVIDERS_MATRIX.get(self.provider, {}).get("base_url", "https://api.openai.com/v1")

            if not self.api_key:
                self.completed_signal.emit("❌ PROCESS ABORTED: API CREDENTIALS FOR SECURITY CLEARENCE NOT PRE-SET.")
                return

            # Include workspace directories to locate native omnikon implementation modules safely
            sys.path.append(os.path.abspath(os.path.dirname(__file__)))
            sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'omnikon')))

            try:
                import omnikon
                self.log_signal.emit("📂 NATIVE OMNIKON COMPONENT DETECTED. PARSING SWARM INTEL OBJECTS...")

                from openai import OpenAI
                client = OpenAI(api_key=self.api_key, base_url=base_url)

                # 1. Orchestrate Stage
                self.log_signal.emit(f"🧠 STAGE 1: CONNECTING CORE ORCHESTRATOR FOR {self.swarm_count} COGNITIVE SECTOR NODES...")
                agents_data = omnikon.orchestrate(client, self.model, self.task, self.swarm_count)

                # 2. Parallel Pool Agent Processing Stage
                self.log_signal.emit(f"🔥 STAGE 2: DISPATCHING Parallel Execution Worker Pools via ThreadPoolExecutor...")
                cfg = omnikon.OmnikonConfig(provider="openai", api_key=self.api_key, max_swarm_agents=self.swarm_count,workspace=self.workspace)
                omnikon.PROVIDERS["openai"] = {"base_url": base_url, "model": self.model}

                swarm_agents = []
                for a in agents_data:
                    sa = omnikon.SwarmAgent(
                        agent_id=a.get("agent_id", 1),
                        name=a.get("name", "Agent"),
                        role=a.get("role", "Analyst"),
                        subtask=a.get("subtask", "Process specific task data chunk"),
                        color="\033[96m"
                    )
                    swarm_agents.append(sa)

                completed_agents = []
                from concurrent.futures import ThreadPoolExecutor, as_completed
                with ThreadPoolExecutor(max_workers=self.swarm_count) as pool:
                    futures = {pool.submit(omnikon.run_swarm_agent, sa, cfg, self.task): sa for sa in swarm_agents}
                    for idx, future in enumerate(as_completed(futures)):
                        ag = futures[future]
                        try:
                            res_agent = future.result()
                            completed_agents.append(res_agent)
                            self.log_signal.emit(f" ↳ Node Resolved [{idx+1}/{len(swarm_agents)}]: {res_agent.name} STATUS -> {res_agent.status.upper()}")
                        except Exception as inner_exc:
                            ag.status = "error"
                            ag.result = str(inner_exc)
                            completed_agents.append(ag)
                            self.log_signal.emit(f" ❌ Node Fault at profile execution: {ag.name} -> {inner_exc}")

                # 3. Consolidate & Synthesize Final Result Output Channel
                self.log_signal.emit("🧬 STAGE 3: ASSEMBLING SCATTERED INTELLIGENCE INTO CENTRAL COGNITIVE COHESION LAYER...")
                completed_agents.sort(key=lambda x: x.agent_id)
                final_answer = omnikon.synthesize(client, self.model, self.task, completed_agents)

                summary_output = "💎 OMNIKON SYSTEM MULTI-AGENT SYNTHESIS SUMMARY\n" + "="*60 + "\n\n"
                for ca in completed_agents:
                    summary_output += f"■ AGENT: {ca.name} [{ca.role}]\n"
                    summary_output += f"Status: {ca.status.upper()} | Execution Span: {ca.duration:.2f}s\n"
                    summary_output += f"--- Findings Block ---\n{ca.result}\n" + "-"*40 + "\n\n"

                summary_output += "🏆 INTEGRATED EXPERT SOLUTION ANSWER:\n" + "="*60 + "\n" + final_answer
                self.completed_signal.emit(summary_output)

            except Exception as e:
                self.log_signal.emit(f"⚠️ Native module fallback. Executing baseline system worker: {e}")
                from openai import OpenAI
                client = OpenAI(api_key=self.api_key, base_url=base_url)
                resp = client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": self.task}]
                )
                self.completed_signal.emit(f"📡 DIRECT WORKER SINGLE STREAM RESPONSE OUT:\n\n{resp.choices[0].message.content}")

        except Exception as global_err:
            self.completed_signal.emit(f"❌ SWARM ORCHESTRATION PIPELINE CRITICAL ERROR REJECTED: {global_err}")


# ── MAIN APPLICATION INTERFACE CONSOLE WINDOW FRAME ──────────────────────
class OmnikonStandaloneApplication(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🛸 OMNIKON SWARM COGNITION TERMINAL // CENTRAL ENGINE CONSOLE")
        self.resize(1350, 850)
        self.setStyleSheet(JARVIS_STYLE)

        self.init_ui()
        self.load_configuration_settings()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # LEFT WORKSTATION CONFIGURATION CONSOLE
        config_box = QGroupBox("🤖 OMNIKON AGENT CORE CONTROL FRAMEWORK")
        config_box.setFixedWidth(430)
        config_layout = QVBoxLayout(config_box)
        config_layout.setSpacing(12)

        config_layout.addSpacing(10)
        config_layout.addWidget(QLabel("🤖 CHAT / 📝 TASK OBJECTIVE PROMPT DIRECTIVE:"))
        self.input_task_directive = QTextEdit()
        self.input_task_directive.setPlaceholderText("Type high-level operational objective description data points here to orchestrate through parallel swarm nodes...")
        config_layout.addWidget(self.input_task_directive)

        # Swarm Orchestration Fire Button Trigger Command
        self.btn_execute_chat = QPushButton("🤖 CHAT WITH")
        self.btn_execute_chat.setStyleSheet("""
            QPushButton {
                background-color: #051a14;
                border: 1px solid #00ff88;
                color: #00ff88;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #00ff88;
                color: #040d1a;
            }
        """)

        # Swarm Orchestration Fire Button Trigger Command
        self.btn_execute_swarm = QPushButton("🚀 ENGAGE PARALLEL SWARM RUN CONSOLE")
        self.btn_execute_swarm.setStyleSheet("""
            QPushButton {
                background-color: #051a14;
                border: 1px solid #00ff88;
                color: #00ff88;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #00ff88;
                color: #040d1a;
            }
        """)
        self.btn_execute_swarm.clicked.connect(self.execute_omnikon_swarm_pipeline)
        self.btn_execute_chat.clicked.connect(self.execute_omnikon_chat_pipeline)
        config_layout.addWidget(self.btn_execute_chat)
        config_layout.addWidget(self.btn_execute_swarm)

        # Provider Selection Matrix Box Input
        config_layout.addWidget(QLabel("📡 OPERATIONAL AI NETWORK PROVIDER:"))
        self.combo_provider = QComboBox()
        self.combo_provider.addItems(list(AI_PROVIDERS_MATRIX.keys()))
        self.combo_provider.currentTextChanged.connect(self.handle_provider_changed_event)
        config_layout.addWidget(self.combo_provider)

        # Model Selection Dynamic Matrix Box Input
        config_layout.addWidget(QLabel("🧠 MATRIX SPECIFIC COGNITIVE MODEL:"))
        self.combo_model = QComboBox()
        config_layout.addWidget(self.combo_model)

        # API Security Token Access Passkey Crypt Field Input
        config_layout.addWidget(QLabel("🔑 SECURITY API AUTHENTICATION ACCESS PASS-KEY:"))
        self.input_api_key = QLineEdit()
        self.input_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_api_key.setPlaceholderText("Enter provider deployment credential token...")
        config_layout.addWidget(self.input_api_key)

        # Active Multi-threaded Swarm Agent Spin counter
        config_layout.addWidget(QLabel("🔥 ACTIVE MULTI-THREADED SWARM AGENTS COUNT:"))
        self.spin_swarm_agents = QSpinBox()
        self.spin_swarm_agents.setRange(1, 16)
        self.spin_swarm_agents.setValue(4)
        config_layout.addWidget(self.spin_swarm_agents)

        config_layout.addWidget(QLabel("📂 TARGET WORKSPACE PATH:"))
        self.input_workspace = QLineEdit()
        self.input_workspace.setText(os.getcwd()) # Default to current directory
        config_layout.addWidget(self.input_workspace)

        # Save Configuration Commit Button
        self.btn_save_settings = QPushButton("💾 COMMIT ALL SETTINGS CONSOLE VALUES TO DISK")
        self.btn_save_settings.clicked.connect(self.save_configuration_settings)
        config_layout.addWidget(self.btn_save_settings)



        main_layout.addWidget(config_box)

        # RIGHT PANELS FOR REAL-TIME LOG SCREEN STREAM AND RESULT PREVIEWS
        display_splitter = QSplitter(Qt.Orientation.Vertical)

        log_widget_wrapper = QWidget()
        log_wrapper_layout = QVBoxLayout(log_widget_wrapper)
        log_wrapper_layout.setContentsMargins(0, 0, 0, 0)
        log_wrapper_layout.addWidget(QLabel("📡 REAL-TIME CORE ORCHESTRATION EVENT STREAM MONITOR:"))
        self.console_stream_monitor = QTextEdit()
        self.console_stream_monitor.setReadOnly(True)
        self.console_stream_monitor.setStyleSheet("QTextEdit { color: #00d4ff; font-size: 11px; background-color: #020812; line-height: 1.4; }")
        log_wrapper_layout.addWidget(self.console_stream_monitor)
        display_splitter.addWidget(log_widget_wrapper)

        output_widget_wrapper = QWidget()
        output_wrapper_layout = QVBoxLayout(output_widget_wrapper)
        output_wrapper_layout.setContentsMargins(0, 0, 0, 0)
        output_wrapper_layout.addWidget(QLabel("🏆 SYNTHESIZED FINAL COMPREHENSIVE ANSWER OUTPUT BUFFER ZONE:"))
        self.output_final_view = QTextEdit()
        self.output_final_view.setReadOnly(True)
        output_wrapper_layout.addWidget(self.output_final_view)
        display_splitter.addWidget(output_widget_wrapper)

        display_splitter.setSizes([300, 500])
        main_layout.addWidget(display_splitter)

        # Trigger dynamic render engine loop update
        self.handle_provider_changed_event(self.combo_provider.currentText())

    def handle_provider_changed_event(self, selected_provider_text):
        """Dynamic waterfall selection matrix loader that updates models lists in real time."""
        self.combo_model.clear()
        provider_data = AI_PROVIDERS_MATRIX.get(selected_provider_text, {})
        self.combo_model.addItems(provider_data.get("models", []))

    def load_configuration_settings(self):
        """Recovers system configuration states safely from past structural commitments."""
        if os.path.exists(CONFIG_FILE_PATH):
            try:
                with open(CONFIG_FILE_PATH, "r", encoding="utf-8") as f:
                    config = json.load(f)
                self.input_workspace.setText(config.get("workspace_path", os.getcwd()))
                saved_provider = config.get("selected_provider", "")
                if saved_provider in AI_PROVIDERS_MATRIX:
                    self.combo_provider.setCurrentText(saved_provider)
                    self.handle_provider_changed_event(saved_provider)

                saved_model = config.get("selected_model", "")
                if saved_model:
                    self.combo_model.setCurrentText(saved_model)

                self.input_api_key.setText(config.get("api_key", ""))
                self.spin_swarm_agents.setValue(config.get("swarm_agents_count", 4))

                self.console_stream_monitor.append("⚙️ JARVIS CORE // CONFIGURATION ATTRIBUTES PARSED FROM LOCAL MATRIX STATE.")
            except Exception as e:
                self.console_stream_monitor.append(f"⚠️ Configuration mapping runtime warning: {e}")

    def save_configuration_settings(self):
        """Writes security tokens, chosen active models, providers and values permanently to disk file structures."""
        config_payload = {
            "selected_provider": self.combo_provider.currentText(),
            "selected_model": self.combo_model.currentText(),
            "api_key": self.input_api_key.text().strip(),
            "swarm_agents_count": self.spin_swarm_agents.value(),
            "workspace_path": self.input_workspace.text().strip()
        }
        try:
            with open(CONFIG_FILE_PATH, "w", encoding="utf-8") as f:
                json.dump(config_payload, f, indent=4)
            self.console_stream_monitor.append("✅ DISK SUCCESS: CURRENT SELECTION MATRIX PERSISTED TO CONFIG CONSOLE.")
        except Exception as e:
            self.console_stream_monitor.append(f"❌ CRITICAL STORAGE ERROR: WRITE FAILURE ON SECTOR MATRIX -> {e}")


    def execute_omnikon_chat_pipeline(self):

        """ Placeholder for single stream direct chat execution method, can be implemented similarly to swarm pipeline but without multi-threading and orchestration layers. """
        self.output_final_view.setPlainText("🚧 SINGLE STREAM CHAT WORKER FUNCTIONALITY UNDER DEVELOPMENT. PLEASE USE THE PARALLEL SWARM PIPELINE FOR FULL SYSTEM ENGAGEMENT DEMONSTRATION. 🚧")

    def execute_omnikon_swarm_pipeline(self):
        """Launches isolated background worker orchestration threads to process parallel tasks flawlessly."""
        task_prompt = self.input_task_directive.toPlainText().strip()
        if not task_prompt:
            self.output_final_view.setPlainText("❌ DISPATCH DECLINED: DIRECTIVE TASK PROMPT FIELD CANNOT REMAIN BLANK.")
            return

        self.btn_execute_swarm.setEnabled(False)
        self.output_final_view.setPlainText("📡 CONNECTING MULTI-THREADED AGENT LAYER RECEPTOR POOLS...")
        self.console_stream_monitor.clear()

        self.swarm_thread = OmnikonSwarmProcessorWorker(
            provider=self.combo_provider.currentText(),
            model=self.combo_model.currentText(),
            api_key=self.input_api_key.text().strip(),
            swarm_count=self.spin_swarm_agents.value(),
            task=task_prompt,
            workspace=self.input_workspace.text().strip()
        )

        # Connect signals for cross-thread graphical interface console updates safely
        self.swarm_thread.log_signal.connect(lambda msg: self.console_stream_monitor.append(msg))
        self.swarm_thread.completed_signal.connect(self.handle_swarm_pipeline_finished_event)
        self.swarm_thread.start()

    def handle_swarm_pipeline_finished_event(self, synthesis_final_result_text):
        self.output_final_view.setPlainText(synthesis_final_result_text)
        self.btn_execute_swarm.setEnabled(True)
        self.console_stream_monitor.append("🏁 PIPELINE DEPLOYMENT SEQUENCE COMPLETELY INDEPENDENTLY STABILIZED.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = OmnikonStandaloneApplication()
    window.show()
    sys.exit(app.exec())