#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════╗
║          OMNIKON - Orchestrating AI Agent System          ║
║     Swarm Intelligence · Multithreaded · Parallel AI      ║
╚═══════════════════════════════════════════════════════════╝

Supports: OpenAI (gpt-4o-mini) | DeepSeek (deepseek-chat)
Usage:    python omnikon.py
"""

import os
import sys
import time
import threading
import queue
import json
import re
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Optional
from openai import OpenAI

# ─────────────────────────────────────────────
#  ANSI COLOR PALETTE
# ─────────────────────────────────────────────
class C:
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"

    # Omnikon brand colors
    CYAN    = "\033[96m"
    MAGENTA = "\033[95m"
    YELLOW  = "\033[93m"
    GREEN   = "\033[92m"
    RED     = "\033[91m"
    BLUE    = "\033[94m"
    WHITE   = "\033[97m"
    ORANGE  = "\033[38;5;208m"
    PURPLE  = "\033[38;5;141m"
    TEAL    = "\033[38;5;51m"

    # Agent colors (each swarm agent has its own color)
    AGENT_COLORS = [
        "\033[38;5;82m",   # lime green
        "\033[38;5;39m",   # sky blue
        "\033[38;5;213m",  # pink
        "\033[38;5;220m",  # gold
        "\033[38;5;203m",  # coral
        "\033[38;5;123m",  # aqua
        "\033[38;5;183m",  # lavender
        "\033[38;5;228m",  # cream yellow
    ]

def color(text: str, *codes: str) -> str:
    return "".join(codes) + text + C.RESET

def timestamp() -> str:
    return color(datetime.now().strftime("%H:%M:%S"), C.DIM)

# ─────────────────────────────────────────────
#  OMNIKON BANNER
# ─────────────────────────────────────────────
def print_banner():
    banner = f"""
{C.CYAN}{C.BOLD}
  ██████╗ ███╗   ███╗███╗   ██╗██╗██╗  ██╗ ██████╗ ███╗   ██╗
 ██╔═══██╗████╗ ████║████╗  ██║██║██║ ██╔╝██╔═══██╗████╗  ██║
 ██║   ██║██╔████╔██║██╔██╗ ██║██║█████╔╝ ██║   ██║██╔██╗ ██║
 ██║   ██║██║╚██╔╝██║██║╚██╗██║██║██╔═██╗ ██║   ██║██║╚██╗██║
 ╚██████╔╝██║ ╚═╝ ██║██║ ╚████║██║██║  ██╗╚██████╔╝██║ ╚████║
  ╚═════╝ ╚═╝     ╚═╝╚═╝  ╚═══╝╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝
{C.RESET}
{color("  ◆ Orchestrating AI Agent  ◆ Swarm Intelligence  ◆ Parallel Execution ◆", C.MAGENTA)}
{color("  ─────────────────────────────────────────────────────────────────────", C.DIM)}
"""
    print(banner)

# ─────────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────────
PROVIDERS = {
    "openai":   {"base_url": "https://api.openai.com/v1",       "model": "gpt-4o-mini"},
    "deepseek": {"base_url": "https://api.deepseek.com/v1",     "model": "deepseek-chat"},
}

@dataclass
class OmnikonConfig:
    provider: str = "openai"
    api_key: str  = ""
    max_swarm_agents: int = 4
    timeout: int = 60

# ─────────────────────────────────────────────
#  SWARM AGENT
# ─────────────────────────────────────────────
@dataclass
class SwarmAgent:
    agent_id: int
    name: str
    role: str
    subtask: str
    color: str
    result: Optional[str] = None
    status: str = "idle"   # idle | running | done | error
    duration: float = 0.0

    def tag(self) -> str:
        return color(f"[{self.name}]", self.color, C.BOLD)

# ─────────────────────────────────────────────
#  PRINT LOCK (thread-safe console output)
# ─────────────────────────────────────────────
_print_lock = threading.Lock()

def safe_print(*args, **kwargs):
    with _print_lock:
        print(*args, **kwargs)

# ─────────────────────────────────────────────
#  LLM CLIENT
# ─────────────────────────────────────────────
def make_client(config: OmnikonConfig) -> OpenAI:
    cfg = PROVIDERS[config.provider]
    return OpenAI(api_key=config.api_key, base_url=cfg["base_url"])

def llm_call(client: OpenAI, model: str, system: str, user: str, timeout: int = 60) -> str:
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system",  "content": system},
            {"role": "user",    "content": user},
        ],
        temperature=0.7,
        max_tokens=800,
        timeout=timeout,
    )
    return response.choices[0].message.content.strip()

# ─────────────────────────────────────────────
#  ORCHESTRATOR — decomposes task into subtasks
# ─────────────────────────────────────────────
def orchestrate(client: OpenAI, model: str, task: str, max_agents: int) -> list[dict]:
    safe_print(f"\n{timestamp()} {color('◈ OMNIKON ORCHESTRATOR', C.MAGENTA, C.BOLD)} — Decomposing task...\n")

    system = f"""You are OMNIKON, an elite AI orchestrator.
Break the user's task into {max_agents} parallel subtasks for specialist swarm agents.
Each agent has a unique role and a concrete subtask.

Respond ONLY with valid JSON — a list of objects:
[
  {{"agent_id": 1, "name": "AgentName", "role": "Role description", "subtask": "Specific subtask"}},
  ...
]
No extra text. No markdown fences. Pure JSON only."""

    user = f"Main task: {task}\n\nDecompose into exactly {max_agents} parallel subtasks."

    raw = llm_call(client, model, system, user)

    # Strip any accidental markdown fences
    raw = re.sub(r"```[a-z]*", "", raw).strip().strip("`").strip()

    try:
        agents_data = json.loads(raw)
    except json.JSONDecodeError:
        # fallback: extract JSON array
        match = re.search(r"\[.*\]", raw, re.DOTALL)
        if match:
            agents_data = json.loads(match.group())
        else:
            raise ValueError(f"Orchestrator returned invalid JSON:\n{raw}")

    return agents_data

# ─────────────────────────────────────────────
#  SWARM WORKER — each agent runs in a thread
# ─────────────────────────────────────────────
def run_swarm_agent(agent: SwarmAgent, config: OmnikonConfig, task: str) -> SwarmAgent:
    cfg = PROVIDERS[config.provider]
    client = make_client(config)

    safe_print(f"{timestamp()} {agent.tag()} {color('▶ Starting', agent.color)}  — {color(agent.role, C.DIM)}")

    agent.status = "running"
    start = time.time()

    system = f"""You are {agent.name}, a specialist AI agent in the OMNIKON swarm.
Your role: {agent.role}
Be precise, thorough, and structured. Respond with actionable content only."""

    user = f"""Main task context: {task}

Your specific subtask: {agent.subtask}

Deliver a complete, well-structured response for your subtask."""

    try:
        result = llm_call(client, cfg["model"], system, user, config.timeout)
        agent.result = result
        agent.status = "done"
    except Exception as e:
        agent.result = f"ERROR: {e}"
        agent.status = "error"

    agent.duration = time.time() - start

    status_icon = color("✔", C.GREEN) if agent.status == "done" else color("✘", C.RED)
    safe_print(
        f"{timestamp()} {agent.tag()} {status_icon} "
        f"{color(f'Completed in {agent.duration:.1f}s', C.DIM)}"
    )
    return agent

# ─────────────────────────────────────────────
#  SYNTHESIZER — merges all agent results
# ─────────────────────────────────────────────
def synthesize(client: OpenAI, model: str, task: str, agents: list[SwarmAgent]) -> str:
    safe_print(f"\n{timestamp()} {color('◈ SYNTHESIZER', C.YELLOW, C.BOLD)} — Merging swarm results...\n")

    combined = "\n\n".join(
        f"=== {a.name} ({a.role}) ===\n{a.result}"
        for a in agents if a.status == "done"
    )

    system = """You are the OMNIKON Synthesizer.
Merge the specialist agents' outputs into one cohesive, well-structured final answer.
Eliminate redundancy. Preserve all key insights. Use clear headings."""

    user = f"Original task: {task}\n\nSwarm agent outputs:\n{combined}\n\nSynthesize into the final comprehensive answer."

    return llm_call(client, model, system, user)

# ─────────────────────────────────────────────
#  DISPLAY HELPERS
# ─────────────────────────────────────────────
def print_agent_cards(agents: list[SwarmAgent]):
    safe_print(color("\n  ┌─ SWARM AGENTS ACTIVATED ──────────────────────────────────┐", C.CYAN))
    for a in agents:
        bar = color(f"  │ {a.tag()}", C.CYAN)
        role_str = color(a.role[:40].ljust(40), C.DIM)
        safe_print(f"{bar} {role_str} {color('│', C.CYAN)}")
    safe_print(color("  └────────────────────────────────────────────────────────────┘\n", C.CYAN))

def print_agent_result(agent: SwarmAgent):
    w = 64
    border = color("─" * w, agent.color)
    safe_print(f"\n{border}")
    safe_print(f"{agent.tag()} {color(agent.role, C.BOLD)}")
    safe_print(color(f"Subtask: {agent.subtask}", C.DIM))
    safe_print(border)
    # Wrap and indent result
    for line in (agent.result or "").split("\n"):
        safe_print(f"  {line}")
    safe_print(f"{border}\n")

def print_final(result: str):
    w = 66
    top    = color("╔" + "═" * w + "╗", C.MAGENTA)
    bottom = color("╚" + "═" * w + "╝", C.MAGENTA)
    title  = color("  OMNIKON FINAL SYNTHESIZED ANSWER  ".center(w), C.MAGENTA, C.BOLD)
    safe_print(f"\n{top}")
    safe_print(color("║", C.MAGENTA) + title + color("║", C.MAGENTA))
    safe_print(color("╠" + "═" * w + "╣", C.MAGENTA))
    for line in result.split("\n"):
        safe_print(color("║ ", C.MAGENTA) + line)
    safe_print(f"{bottom}\n")

def print_summary(agents: list[SwarmAgent], total_time: float):
    safe_print(color("\n  ┌─ EXECUTION SUMMARY ─────────────────────────────────────────┐", C.TEAL))
    for a in agents:
        icon = color("✔", C.GREEN) if a.status == "done" else color("✘", C.RED)
        bar_len = int((a.duration / max(ag.duration for ag in agents)) * 20)
        bar = color("█" * bar_len, a.color) + color("░" * (20 - bar_len), C.DIM)
        safe_print(f"  {color('│', C.TEAL)} {icon} {color(a.name.ljust(16), a.color)} {bar} {a.duration:.1f}s")
    safe_print(color(f"  │ Total wall-clock time: {total_time:.1f}s (parallel)", C.TEAL))
    safe_print(color("  └──────────────────────────────────────────────────────────────┘\n", C.TEAL))

# ─────────────────────────────────────────────
#  SETUP WIZARD
# ─────────────────────────────────────────────
def setup_config() -> OmnikonConfig:
    config = OmnikonConfig()

    print(color("  ◆ OMNIKON SETUP", C.CYAN, C.BOLD))
    print(color("  ─────────────────────────────────", C.DIM))

    # Provider
    print(f"\n  {color('Provider', C.YELLOW)} [{color('1', C.GREEN)}=OpenAI  {color('2', C.BLUE)}=DeepSeek]: ", end="")
    choice = input().strip()
    config.provider = "deepseek" if choice == "2" else "openai"
    print(f"  → Using {color(config.provider.upper(), C.GREEN, C.BOLD)}")

    # API Key
    env_key = "OPENAI_API_KEY" if config.provider == "openai" else "DEEPSEEK_API_KEY"
    api_key = os.environ.get(env_key, "")
    if api_key:
        print(f"  {color('✔', C.GREEN)} API key loaded from {color(env_key, C.DIM)}")
        config.api_key = api_key
    else:
        print(f"\n  {color('API Key', C.YELLOW)} (or set {env_key} env var): ", end="")
        config.api_key = input().strip()

    # Swarm size
    print(f"\n  {color('Swarm agents', C.YELLOW)} [2-8, default 4]: ", end="")
    n = input().strip()
    config.max_swarm_agents = max(2, min(8, int(n))) if n.isdigit() else 4
    print(f"  → {color(str(config.max_swarm_agents), C.GREEN)} parallel agents\n")

    return config

# ─────────────────────────────────────────────
#  SPINNING ANIMATION (while orchestrating)
# ─────────────────────────────────────────────
def spinner(stop_event: threading.Event, label: str, col: str):
    frames = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]
    i = 0
    while not stop_event.is_set():
        with _print_lock:
            sys.stdout.write(f"\r  {color(frames[i], col)} {label}   ")
            sys.stdout.flush()
        time.sleep(0.08)
        i = (i + 1) % len(frames)
    with _print_lock:
        sys.stdout.write("\r" + " " * 60 + "\r")
        sys.stdout.flush()

# Append these tracking capabilities cleanly to the end of omnikon.py

def read_workspace_recursive(folder_root: str) -> str:
    """Recursively walks down the target workspace folder path to construct an aggregated schema content stream for LLM context injection."""
    root_path = Path(folder_root)
    if not root_path.exists():
        return "Workspace folder context empty or unreachable."

    context_accumulator = []
    # Skip standard heavy dependency compilation bins for performance optimization
    ignored_patterns = {'.git', '__pycache__', 'node_modules', '.venv', 'env', 'build', 'dist'}

    for path_element in root_path.rglob('*'):
        if any(part in path_element.parts for part in ignored_patterns):
            continue

        if path_element.is_file():
            try:
                relative_path = path_element.relative_to(root_path).as_posix()
                content_accum = path_element.read_text(encoding='utf-8', errors='replace')
                context_accumulator.append(f"📦 FILE_PATH: {relative_path}\n--- CONTENT START ---\n{content_accum}\n--- CONTENT END ---\n")
            except Exception as e:
                pass # Bypass binary files or unreadable stream structures safely

    return "\n".join(context_accumulator) if context_accumulator else "Target workspace contains no initialized code files."

def orchestrate_with_workspace(client: OpenAI, model: str, task: str, max_agents: int, workspace_context: str) -> list[dict]:
    """Provides file environment system metrics to the Orchestration Layer to isolate task segments mapping to relevant directory locations."""
    system = f"""You are OMNIKON, an elite parallel AI swarm orchestrator with automated recursive file-system access.
Break down the high-level request into exactly {max_agents} specific assignments for specialists.
Each agent can read, propose file modifications or generate new files inside their assignment block.

Respond ONLY with valid JSON — a list of objects:
[
  {{"agent_id": 1, "name": "FileSpecialistName", "role": "Role scope description", "subtask": "Step-by-step filesystem instruction template"}}
]
No extra conversational content, pure JSON format string array only."""

    user = f"WORKSPACE CONTEXT LAYOUT METRICS:\n{workspace_context}\n\nMISSION DIRECTIVE ORDER:\n{task}\n\nDecompose layout into exactly {max_agents} actions."

    raw = llm_call(client, model, system, user)
    raw = re.sub(r"```[a-z]*", "", raw).strip().strip("`").strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\[.*\]", raw, re.DOTALL)
        if match:
            return json.loads(match.group())
        raise ValueError(f"Orchestration schema mapping exception error generated on: {raw}")

def execute_agent_file_actions(agent: SwarmAgent, workspace_root_dir: str) -> list[str]:
    """Scans specialist responses for special actionable structural files block wrappers to emit automated creations or edits directly onto the workspace.

    Expected wrapper format inside specialist code blocks:
    <<<< CREATE_OR_WRITE: relative/path/to/file.py >>>>
    File contents here
    <<<< END_FILE >>>>
    """
    if not agent.result:
        return []

    actions_logged = []
    pattern = r"<<<< CREATE_OR_WRITE:\s*(.*?)\s*>>>>(.*?)<<<< END_FILE >>>>"
    matches = re.findall(pattern, agent.result, re.DOTALL)

    for rel_path_str, file_content in matches:
        try:
            target_path = Path(workspace_root_dir) / rel_path_str.strip()
            # Construct nested parent system folder routes automatically
            target_path.parent.mkdir(parents=True, exist_ok=True)

            # Flush generated updates cleanly to physical target vectors
            target_path.write_text(file_content.strip(), encoding='utf-8')
            actions_logged.append(f"Mutated file successfully: [{rel_path_str.strip()}] handled via {agent.name}")
        except Exception as e:
            actions_logged.append(f"Failed disk mutation step on [{rel_path_str.strip()}]: {e}")

    return actions_logged



# ─────────────────────────────────────────────
#  MAIN LOOP
# ─────────────────────────────────────────────
def main():
    print_banner()
    config = setup_config()

    cfg    = PROVIDERS[config.provider]
    client = make_client(config)

    print(color(f"  ◆ OMNIKON READY — {config.provider.upper()} / {cfg['model']}", C.GREEN, C.BOLD))
    print(color("  Type your task. Commands: 'exit' | 'help' | 'clear'\n", C.DIM))

    history: list[str] = []
    session_count = 0

    while True:
        # Prompt
        try:
            prompt_line = color(f"[{session_count}] ", C.DIM) + color("OMNIKON", C.CYAN, C.BOLD) + color(" ❯ ", C.MAGENTA)
            sys.stdout.write(f"\n{prompt_line}")
            sys.stdout.flush()
            task = input().strip()
        except (EOFError, KeyboardInterrupt):
            print(color("\n\n  ◆ OMNIKON shutting down. Goodbye.\n", C.MAGENTA))
            break

        if not task:
            continue
        if task.lower() == "exit":
            print(color("\n  ◆ OMNIKON shutting down. Goodbye.\n", C.MAGENTA))
            break
        if task.lower() == "clear":
            os.system("clear" if os.name != "nt" else "cls")
            print_banner()
            continue
        if task.lower() == "help":
            print(color("""
  ┌─ OMNIKON COMMANDS ──────────────────────────────────────┐
  │  Just type your task/question and press Enter           │
  │  OMNIKON will automatically:                            │
  │    1. Detect if task needs parallel swarm agents        │
  │    2. Decompose into subtasks via Orchestrator          │
  │    3. Spin up N parallel swarm agents (threads)         │
  │    4. Synthesize all results into a final answer        │
  │                                                         │
  │  Commands:  exit | help | clear                         │
  └─────────────────────────────────────────────────────────┘
""", C.CYAN))
            continue

        session_count += 1
        wall_start = time.time()

        # ── STEP 1: Orchestrate (decompose into subtasks) ──
        stop_spin = threading.Event()
        spin = threading.Thread(
            target=spinner,
            args=(stop_spin, color("Orchestrating task...", C.MAGENTA), C.MAGENTA),
            daemon=True
        )
        spin.start()

        try:
            agents_data = orchestrate(client, cfg["model"], task, config.max_swarm_agents)
        except Exception as e:
            stop_spin.set()
            print(color(f"\n  ✘ Orchestration failed: {e}", C.RED))
            continue
        finally:
            stop_spin.set()
            spin.join()

        # ── STEP 2: Build SwarmAgent objects ──
        agents: list[SwarmAgent] = []
        for i, ad in enumerate(agents_data):
            a = SwarmAgent(
                agent_id = ad.get("agent_id", i + 1),
                name     = ad.get("name",     f"Agent-{i+1}"),
                role     = ad.get("role",     "Specialist"),
                subtask  = ad.get("subtask",  task),
                color    = C.AGENT_COLORS[i % len(C.AGENT_COLORS)],
            )
            agents.append(a)

        print_agent_cards(agents)

        # ── STEP 3: Launch parallel swarm (ThreadPoolExecutor) ──
        print(color(f"  ◆ Launching {len(agents)} swarm agents in parallel...\n", C.CYAN))

        completed_agents: list[SwarmAgent] = []
        with ThreadPoolExecutor(max_workers=len(agents), thread_name_prefix="swarm") as pool:
            futures = {
                pool.submit(run_swarm_agent, agent, config, task): agent
                for agent in agents
            }
            for future in as_completed(futures):
                try:
                    completed_agents.append(future.result())
                except Exception as e:
                    ag = futures[future]
                    ag.status = "error"
                    ag.result = str(e)
                    completed_agents.append(ag)

        # Sort back to original order
        completed_agents.sort(key=lambda a: a.agent_id)

        # ── STEP 4: Show each agent's result ──
        print(color("\n  ◆ SWARM RESULTS\n", C.YELLOW, C.BOLD))
        for agent in completed_agents:
            print_agent_result(agent)

        # ── STEP 5: Synthesize ──
        stop_spin2 = threading.Event()
        spin2 = threading.Thread(
            target=spinner,
            args=(stop_spin2, color("Synthesizing final answer...", C.YELLOW), C.YELLOW),
            daemon=True
        )
        spin2.start()

        try:
            final = synthesize(client, cfg["model"], task, completed_agents)
        except Exception as e:
            stop_spin2.set()
            print(color(f"\n  ✘ Synthesis failed: {e}", C.RED))
            final = "\n".join(
                f"[{a.name}]: {a.result}"
                for a in completed_agents if a.status == "done"
            )
        finally:
            stop_spin2.set()
            spin2.join()

        wall_time = time.time() - wall_start

        print_final(final)
        print_summary(completed_agents, wall_time)

        history.append(f"[{session_count}] {task[:60]}")

if __name__ == "__main__":
    main()
