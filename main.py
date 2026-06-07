#!/usr/bin/env python3
import os
import sys
import json
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QComboBox,
    QGroupBox, QSpinBox, QSplitter, QFileDialog
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

JARVIS_STYLE = """
    QMainWindow, QDialog { background-color: #040d1a; }
    QLabel { color: #c8e0ff; font-family: 'Share Tech Mono', monospace; font-size: 11px; text-transform: uppercase; letter-spacing: 1px; }
    QLineEdit { background-color: #041020; border: 1px solid #0e2d5a; border-radius: 3px; padding: 8px; color: #00d4ff; font-family: 'Share Tech Mono', monospace; }
    QLineEdit:focus { border: 1px solid #00d4ff; }
    QTextEdit { background-color: #040d1a; border: 1px solid #0e2d5a; border-radius: 4px; color: #00ff88; padding: 10px; font-family: 'Share Tech Mono', monospace; font-size: 12px; }
    QComboBox, QSpinBox { background-color: #041020; border: 1px solid #0e2d5a; border-radius: 3px; padding: 6px; color: #00d4ff; font-family: 'Share Tech Mono', monospace; }
    QPushButton { background-color: #071428; border: 1px solid #0e2d5a; border-radius: 3px; padding: 8px 14px; color: #00d4ff; font-family: 'Share Tech Mono', monospace; font-weight: bold; text-transform: uppercase; letter-spacing: 1px; }
    QPushButton:hover { background-color: #0a213f; border: 1px solid #00d4ff; color: #fff; }
    QPushButton:disabled { background-color: #020810; color: #2a405a; border: 1px solid #041428; }
    QGroupBox { border: 1px solid #0e2d5a; border-radius: 4px; margin-top: 10px; padding-top: 15px; color: #00d4ff; font-family: 'Share Tech Mono', monospace; font-size: 11px; text-transform: uppercase; letter-spacing: 1px; }
    QSplitter::handle { background-color: #0e2d5a; }
"""

class OmnikonSwarmProcessorWorker(QThread):
    log_signal = pyqtSignal(str)
    completed_signal = pyqtSignal(str)

    def __init__(self, provider, model, api_key, swarm_count, task, workspace_path):
        super().__init__()
        self.provider = provider
        self.model = model
        self.api_key = api_key
        self.swarm_count = swarm_count
        self.task = task
        self.workspace_path = workspace_path

    def run(self):
        try:
            self.log_signal.emit("⚡ ENGAGING OMNIKON SYSTEM PROTOCOLS FROM ORCHESTRATION LAYER...")
            base_url = AI_PROVIDERS_MATRIX.get(self.provider, {}).get("base_url", "https://api.openai.com/v1")

            if not self.api_key:
                self.completed_signal.emit("❌ PROCESS ABORTED: API CREDENTIALS NOT FOUND.")
                return

            sys.path.append(os.path.abspath(os.path.dirname(__file__)))
            import omnikon

            from openai import OpenAI
            client = OpenAI(api_key=self.api_key, base_url=base_url)

            cfg = omnikon.OmnikonConfig(
                provider="openai",
                api_key=self.api_key,
                max_swarm_agents=self.swarm_count,
                workspace_root=self.workspace_path
            )
            omnikon.PROVIDERS["openai"] = {"base_url": base_url, "model": self.model}

            # Read files layout recursively inside specified workspace parameters
            self.log_signal.emit(f"📂 SCANNING WORKSPACE RECURSIVELY: {self.workspace_path}")
            workspace_context = omnikon.read_workspace_recursive(self.workspace_path)

            # 1. Orchestrate Stage
            self.log_signal.emit(f"🧠 STAGE 1: ORCHESTRATOR DECOMPOSING TASK WITH DIRECT WORKSPACE MAP...")
            agents_data = omnikon.orchestrate_with_workspace(client, self.model, self.task, self.swarm_count, workspace_context)

            # 2. Parallel Processing
            self.log_signal.emit(f"🔥 STAGE 2: DISPATCHING {len(agents_data)} PARALLEL FILE SYSTEM MODIFIERS...")
            swarm_agents = []
            for i, a in enumerate(agents_data):
                sa = omnikon.SwarmAgent(
                    agent_id=a.get("agent_id", i+1),
                    name=a.get("name", "FileAgent"),
                    role=a.get("role", "Modifier"),
                    subtask=a.get("subtask", "Process files"),
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

                        # Process file manipulation calls if agent emitted structural disk outputs
                        actions_logged = omnikon.execute_agent_file_actions(res_agent, self.workspace_path)
                        for action in actions_logged:
                            self.log_signal.emit(f"   💾 {action}")

                        self.log_signal.emit(f" ↳ Node Resolved [{idx+1}/{len(swarm_agents)}]: {res_agent.name}")
                    except Exception as inner_exc:
                        ag.status = "error"
                        ag.result = str(inner_exc)
                        completed_agents.append(ag)
                        self.log_signal.emit(f" ❌ Node Fault: {ag.name} -> {inner_exc}")

            # 3. Final Consolidation Output Channel
            self.log_signal.emit("🧬 STAGE 3: SYNTHESIZING COMPLETED WORKSPACE MUTATIONS...")
            completed_agents.sort(key=lambda x: x.agent_id)
            final_answer = omnikon.synthesize(client, self.model, self.task, completed_agents)

            summary_output = "💎 OMNIKON SYSTEM DISK MUTATION SUMMARY\n" + "="*60 + "\n\n"
            for ca in completed_agents:
                summary_output += f"■ AGENT: {ca.name} [{ca.role}]\n"
                summary_output += f"--- Execution Results ---\n{ca.result}\n" + "-"*40 + "\n\n"
            summary_output += "🏆 INTEGRATED SOLUTIONS AND TARGET STATE LAYOUT:\n" + "="*60 + "\n" + final_answer
            self.completed_signal.emit(summary_output)

        except Exception as global_err:
            self.completed_signal.emit(f"❌ SWARM MUTATION PIPELINE CRITICAL ERROR: {global_err}")


class OmnikonStandaloneApplication(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🛸 OMNIKON SWARM COGNITION TERMINAL // WORKSPACE ENVIRONMENT CONSOLE")
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
        config_box = QGroupBox("🤖 OMNIKON WORKSPACE ENVIRONMENT CORE")
        config_box.setFixedWidth(440)
        config_layout = QVBoxLayout(config_box)
        config_layout.setSpacing(10)

        # Active Workspace Matrix Folder Direction Picker
        config_layout.addWidget(QLabel("📂 SELECTED ACTIVE ENVIRONMENT WORKSPACE TARGET:"))
        workspace_picker_layout = QHBoxLayout()
        self.input_workspace_dir = QLineEdit()
        self.input_workspace_dir.setPlaceholderText("Target project working branch folder context...")
        self.btn_browse_workspace = QPushButton("Browse")
        self.btn_browse_workspace.clicked.connect(self.select_workspace_directory)
        workspace_picker_layout.addWidget(self.input_workspace_dir)
        workspace_picker_layout.addWidget(self.btn_browse_workspace)
        config_layout.addLayout(workspace_picker_layout)

        config_layout.addWidget(QLabel("📡 OPERATIONAL AI NETWORK PROVIDER:"))
        self.combo_provider = QComboBox()
        self.combo_provider.addItems(list(AI_PROVIDERS_MATRIX.keys()))
        self.combo_provider.currentTextChanged.connect(self.handle_provider_changed_event)
        config_layout.addWidget(self.combo_provider)

        config_layout.addWidget(QLabel("🧠 MATRIX SPECIFIC COGNITIVE MODEL:"))
        self.combo_model = QComboBox()
        config_layout.addWidget(self.combo_model)

        config_layout.addWidget(QLabel("🔑 SECURITY API AUTHENTICATION ACCESS PASS-KEY:"))
        self.input_api_key = QLineEdit()
        self.input_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        config_layout.addWidget(self.input_api_key)

        config_layout.addWidget(QLabel("🔥 ACTIVE MULTI-THREADED SWARM AGENTS COUNT:"))
        self.spin_swarm_agents = QSpinBox()
        self.spin_swarm_agents.setRange(1, 16)
        self.spin_swarm_agents.setValue(4)
        config_layout.addWidget(self.spin_swarm_agents)

        self.btn_save_settings = QPushButton("💾 COMMIT CONFIG VALUES TO DISK")
        self.btn_save_settings.clicked.connect(self.save_configuration_settings)
        config_layout.addWidget(self.btn_save_settings)

        config_layout.addSpacing(10)
        config_layout.addWidget(QLabel("📝 FILE CREATION / SYSTEM MODIFICATION MISSION PROMPT:"))
        self.input_task_directive = QTextEdit()
        self.input_task_directive.setPlaceholderText("Describe changes or files you wish Omnikon to recursively evaluate, generate or rewrite inside the designated target workspace folder...")
        config_layout.addWidget(self.input_task_directive)

        self.btn_execute_swarm = QPushButton("🚀 ENGAGE FILE-SYSTEM MUTATION ENGINE")
        self.btn_execute_swarm.setStyleSheet("QPushButton { background-color: #051a14; border: 1px solid #00ff88; color: #00ff88; font-size: 13px; } QPushButton:hover { background-color: #00ff88; color: #040d1a; }")
        self.btn_execute_swarm.clicked.connect(self.execute_omnikon_swarm_pipeline)
        config_layout.addWidget(self.btn_execute_swarm)

        main_layout.addWidget(config_box)

        # RIGHT MONITOR PANELS
        display_splitter = QSplitter(Qt.Orientation.Vertical)

        log_widget_wrapper = QWidget()
        log_wrapper_layout = QVBoxLayout(log_widget_wrapper)
        log_wrapper_layout.setContentsMargins(0, 0, 0, 0)
        log_wrapper_layout.addWidget(QLabel("📡 REAL-TIME DISK OPERATIONS MONITOR STATUS:"))
        self.console_stream_monitor = QTextEdit()
        self.console_stream_monitor.setReadOnly(True)
        self.console_stream_monitor.setStyleSheet("QTextEdit { color: #00d4ff; font-size: 11px; background-color: #020812; }")
        log_wrapper_layout.addWidget(self.console_stream_monitor)
        display_splitter.addWidget(log_widget_wrapper)

        output_widget_wrapper = QWidget()
        output_wrapper_layout = QVBoxLayout(output_widget_wrapper)
        output_wrapper_layout.setContentsMargins(0, 0, 0, 0)
        output_wrapper_layout.addWidget(QLabel("🏆 SYNTHESIZED FINAL RUN SUMMARY OUTPUT DATA CHANNEL:"))
        self.output_final_view = QTextEdit()
        self.output_final_view.setReadOnly(True)
        output_wrapper_layout.addWidget(self.output_final_view)
        display_splitter.addWidget(output_widget_wrapper)

        display_splitter.setSizes([300, 500])
        main_layout.addWidget(display_splitter)

        self.handle_provider_changed_event(self.combo_provider.currentText())

    def select_workspace_directory(self):
        selected_dir = QFileDialog.getExistingDirectory(self, "Select Active Workspace Folder Root Context")
        if selected_dir:
            self.input_workspace_dir.setText(selected_dir)

    def handle_provider_changed_event(self, selected_provider_text):
        self.combo_model.clear()
        provider_data = AI_PROVIDERS_MATRIX.get(selected_provider_text, {})
        self.combo_model.addItems(provider_data.get("models", []))

    def load_configuration_settings(self):
        if os.path.exists(CONFIG_FILE_PATH):
            try:
                with open(CONFIG_FILE_PATH, "r", encoding="utf-8") as f:
                    config = json.load(f)

                self.input_workspace_dir.setText(config.get("workspace_root_dir", ""))
                saved_provider = config.get("selected_provider", "")
                if saved_provider in AI_PROVIDERS_MATRIX:
                    self.combo_provider.setCurrentText(saved_provider)
                    self.handle_provider_changed_event(saved_provider)

                saved_model = config.get("selected_model", "")
                if saved_model: self.combo_model.setCurrentText(saved_model)
                self.input_api_key.setText(config.get("api_key", ""))
                self.spin_swarm_agents.setValue(config.get("swarm_agents_count", 4))
                self.console_stream_monitor.append("⚙️ JARVIS INTERNAL CONFIG MATRIX LOADED.")
            except Exception as e:
                self.console_stream_monitor.append(f"⚠️ Warning loading settings: {e}")

    def save_configuration_settings(self):
        config_payload = {
            "workspace_root_dir": self.input_workspace_dir.text().strip(),
            "selected_provider": self.combo_provider.currentText(),
            "selected_model": self.combo_model.currentText(),
            "api_key": self.input_api_key.text().strip(),
            "swarm_agents_count": self.spin_swarm_agents.value()
        }
        try:
            with open(CONFIG_FILE_PATH, "w", encoding="utf-8") as f:
                json.dump(config_payload, f, indent=4)
            self.console_stream_monitor.append("✅ SETTINGS PERSISTED SECURELY TO LOCAL CACHE DESCRIPTOR.")
        except Exception as e:
            self.console_stream_monitor.append(f"❌ CACHE WRITE FAILURE: {e}")

    def execute_omnikon_swarm_pipeline(self):
        task_prompt = self.input_task_directive.toPlainText().strip()
        workspace_path = self.input_workspace_dir.text().strip()

        if not workspace_path or not os.path.isdir(workspace_path):
            self.output_final_view.setPlainText("❌ DISPATCH DECLINED: VALID WORKSPACE TARGET DIRECTORY MUST BE ASSIGNED.")
            return
        if not task_prompt:
            self.output_final_view.setPlainText("❌ DISPATCH DECLINED: DIRECTIVE MISSION STATEMENT CANNOT BE EMPTY.")
            return

        self.btn_execute_swarm.setEnabled(False)
        self.output_final_view.setPlainText("📡 PARSING FILE REPOSITORIES AND CREATING ISOLATED BACKGROUND POOL WORKERS...")
        self.console_stream_monitor.clear()

        self.swarm_thread = OmnikonSwarmProcessorWorker(
            provider=self.combo_provider.currentText(),
            model=self.combo_model.currentText(),
            api_key=self.input_api_key.text().strip(),
            swarm_count=self.spin_swarm_agents.value(),
            task=task_prompt,
            workspace_path=workspace_path
        )

        self.swarm_thread.log_signal.connect(lambda msg: self.console_stream_monitor.append(msg))
        self.swarm_thread.completed_signal.connect(self.handle_swarm_pipeline_finished_event)
        self.swarm_thread.start()

    def handle_swarm_pipeline_finished_event(self, synthesis_final_result_text):
        self.output_final_view.setPlainText(synthesis_final_result_text)
        self.btn_execute_swarm.setEnabled(True)
        self.console_stream_monitor.append("🏁 PIPELINE EXECUTION LOOP AND FILE MUTATIONS FINISHED.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = OmnikonStandaloneApplication()
    window.show()
    sys.exit(app.exec())