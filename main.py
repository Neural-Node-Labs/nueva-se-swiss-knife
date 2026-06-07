import os
import sys
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, 
    QHBoxLayout, QLabel, QLineEdit, QPushButton, QCheckBox, 
    QTextEdit, QFileDialog, QListWidget, QListWidgetItem, QSplitter, 
    QDialog, QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor

try:
    from comparator import compare_folders, _diff_text_files, FileDiffResult
    from formatter import format_code
    from searcher import search_in_folder
except ImportError as e:
    print(f"\n[Engine Error] Core utility missing: {e}")
    sys.exit(1)

# SHARED JARVIS STYLESHEET EXTRAPOLATED FROM THE CHAT TEMPLATE
JARVIS_STYLE = """
    QMainWindow, QDialog { background-color: #040d1a; }
    QTabWidget::panel { border: 1px solid #0e2d5a; background-color: #071428; border-radius: 4px; }
    QTabBar::tab { background-color: #041020; color: #4a7a9e; padding: 12px 24px; font-family: 'Share Tech Mono', monospace; font-size: 12px; font-weight: bold; text-transform: uppercase; border: 1px solid #0e2d5a; margin-right: 4px; }
    QTabBar::tab:hover { color: #00d4ff; background-color: #071428; }
    QTabBar::tab:selected { color: #00d4ff; background-color: #071428; border-top: 2px solid #00d4ff; }
    QLabel { color: #c8e0ff; font-family: 'Share Tech Mono', monospace; font-size: 12px; }
    QLineEdit { background-color: #041020; border: 1px solid #0e2d5a; border-radius: 3px; padding: 8px; color: #00d4ff; font-family: 'Share Tech Mono', monospace; }
    QLineEdit:focus { border: 1px solid #00d4ff; }
    QTextEdit { background-color: #040d1a; border: 1px solid #0e2d5a; border-radius: 4px; color: #00ff88; padding: 10px; font-family: 'Share Tech Mono', monospace; font-size: 13px; }
    QListWidget { background-color: #041020; border: 1px solid #0e2d5a; color: #ff4040; font-family: 'Share Tech Mono', monospace; font-size: 12px; border-radius: 4px; }
    QListWidget::item:hover { background-color: #0a213f; color: #00d4ff; }
    QListWidget::item:selected { background-color: #0e2d5a; color: #00ff88; border-left: 3px solid #00ff88; }
    QPushButton { background-color: #071428; border: 1px solid #0e2d5a; border-radius: 3px; padding: 8px 16px; color: #00d4ff; font-family: 'Share Tech Mono', monospace; font-weight: bold; text-transform: uppercase; }
    QPushButton:hover { background-color: #0a213f; border: 1px solid #00d4ff; color: #fff; }
    QCheckBox { spacing: 8px; color: #4a7a9e; font-family: 'Share Tech Mono', monospace; }
    QCheckBox::indicator { width: 16px; height: 16px; border: 1px solid #0e2d5a; background: #041020; }
    QCheckBox::indicator:checked { border: 1px solid #00ff88; background-color: #071428; }
"""

# ── INTERACTIVE LINE-BY-LINE MERGE CONSOLE WITH FIXED 2-LINE SLOTS ───────
class MergeConsoleDialog(QDialog):
    def __init__(self, diff_result: FileDiffResult, parent=None):
        super().__init__(parent)
        self.diff_result = diff_result
        self.setWindowTitle(f"NUEVA SE SWISS KNIFE // SUB-ELEMENT VECTOR RESOLVER: {diff_result.relative_path}")
        self.resize(1250, 780)
        self.setStyleSheet(JARVIS_STYLE)

        self.working_lines_state = []
        self.init_ui()
        self.build_interactive_matrix()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(12)

        meta_label = QLabel(
            f"📐 ACTIVE ARRAY NODES: {self.diff_result.relative_path}\n"
            f"Left Pointer: {self.diff_result.left_path or 'Empty'} | Right Pointer: {self.diff_result.right_path or 'Empty'}"
        )
        meta_label.setStyleSheet("color: #4a7a9e; font-size: 11px;")
        main_layout.addWidget(meta_label)

        splitter = QSplitter(Qt.Orientation.Vertical)

        matrix_container = QWidget()
        matrix_layout = QVBoxLayout(matrix_container)
        matrix_layout.setContentsMargins(0, 0, 0, 0)
        matrix_layout.addWidget(QLabel("🕵️ LIVE INTERACTIVE DELTA BUFFER STREAM (LINE OPTION CONTROLS):"))

        self.matrix_table = QTableWidget()
        self.matrix_table.setColumnCount(5)
        self.matrix_table.setHorizontalHeaderLabels([
            "LOC L", "LEFT SOURCE CHANNEL", "RESOLVE STATUS", "RIGHT SOURCE CHANNEL", "LOC R"
        ])

        self.matrix_table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.matrix_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        self.matrix_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.matrix_table.setColumnWidth(0, 55)
        self.matrix_table.setColumnWidth(2, 110)
        self.matrix_table.setColumnWidth(4, 55)
        self.matrix_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.matrix_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)

        self.matrix_table.verticalHeader().setDefaultSectionSize(48)

        self.matrix_table.setStyleSheet("""
            QTableWidget {
                background-color: #041020;
                gridline-color: #0e2d5a;
                border: 1px solid #0e2d5a;
                color: #c8e0ff;
                font-family: 'Share Tech Mono', monospace;
            }
            QHeaderView::section {
                background-color: #071428;
                color: #00d4ff;
                padding: 6px;
                border: 1px solid #0e2d5a;
                font-family: 'Share Tech Mono', monospace;
            }
        """)
        matrix_layout.addWidget(self.matrix_table)
        splitter.addWidget(matrix_container)

        output_container = QWidget()
        output_layout = QVBoxLayout(output_container)
        output_layout.setContentsMargins(0, 0, 0, 0)
        output_layout.addWidget(QLabel("🛠️ LIVE RE-SYNCHRONIZED CONSOLIDATED CODE BUFFER AREA:"))
        self.merge_buffer = QTextEdit()
        output_layout.addWidget(self.merge_buffer)
        splitter.addWidget(output_container)

        splitter.setSizes([450, 250])
        main_layout.addWidget(splitter)

        btn_layout = QHBoxLayout()

        self.btn_acc_left = QPushButton("BULK FORCE ALL LEFT")
        self.btn_acc_left.clicked.connect(self.bulk_accept_left)
        btn_layout.addWidget(self.btn_acc_left)

        self.btn_acc_right = QPushButton("BULK FORCE ALL RIGHT")
        self.btn_acc_right.clicked.connect(self.bulk_accept_right)
        btn_layout.addWidget(self.btn_acc_right)

        btn_layout.addStretch()

        self.btn_save = QPushButton("SAVE MERGED OUTPUT OBJECT TO DISK")
        self.btn_save.setStyleSheet("QPushButton { background-color: #051a14; border: 1px solid #00ff88; color: #00ff88; }")
        self.btn_save.clicked.connect(self.save_merged_file)
        btn_layout.addWidget(self.btn_save)

        main_layout.addLayout(btn_layout)

    def build_interactive_matrix(self):
        if not self.diff_result.line_diffs:
            if self.diff_result.left_path and not self.diff_result.right_path:
                try:
                    lines = Path(self.diff_result.left_path).read_text(encoding="utf-8", errors="replace").splitlines()
                    from comparator import LineDiff
                    self.diff_result.line_diffs = [
                        LineDiff(line_number_left=i+1, line_number_right=None, tag="delete", left_line=line, right_line="")
                        for i, line in enumerate(lines)
                    ]
                except Exception as e:
                    self.merge_buffer.setPlainText(f"// Left-only file read exception: {e}")
                    return
            elif self.diff_result.right_path and not self.diff_result.left_path:
                try:
                    lines = Path(self.diff_result.right_path).read_text(encoding="utf-8", errors="replace").splitlines()
                    from comparator import LineDiff
                    self.diff_result.line_diffs = [
                        LineDiff(line_number_left=None, line_number_right=i+1, tag="insert", left_line="", right_line=line)
                        for i, line in enumerate(lines)
                    ]
                except Exception as e:
                    self.merge_buffer.setPlainText(f"// Right-only file read exception: {e}")
                    return
            elif self.diff_result.left_path and self.diff_result.right_path:
                try:
                    self.diff_result.line_diffs = _diff_text_files(self.diff_result.left_path, self.diff_result.right_path)
                except Exception as e:
                    self.merge_buffer.setPlainText(f"// Parsing Exception pipeline aborted: {e}")
                    return

        diff_payload = self.diff_result.line_diffs
        self.matrix_table.setRowCount(len(diff_payload))
        self.working_lines_state = [""] * len(diff_payload)

        for idx, item in enumerate(diff_payload):
            tag = item.tag.upper()
            ln_l = str(item.line_number_left) if item.line_number_left else ""
            ln_r = str(item.line_number_right) if item.line_number_right else ""

            cell_l = QTableWidgetItem(ln_l)
            cell_l.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            cell_l.setForeground(QColor("#4a7a9e"))
            self.matrix_table.setItem(idx, 0, cell_l)

            cell_left_code = QTableWidgetItem(item.left_line)
            if tag == "DELETE":
                cell_left_code.setBackground(QColor("#240a0a"))
                cell_left_code.setForeground(QColor("#ff4040"))
            elif tag == "REPLACE":
                cell_left_code.setBackground(QColor("#2b1b05"))
                cell_left_code.setForeground(QColor("#f5a623"))
            self.matrix_table.setItem(idx, 1, cell_left_code)

            cell_right_code = QTableWidgetItem(item.right_line)
            if tag == "INSERT":
                cell_right_code.setBackground(QColor("#051a11"))
                cell_right_code.setForeground(QColor("#00ff88"))
            elif tag == "REPLACE":
                cell_right_code.setBackground(QColor("#2b1b05"))
                cell_right_code.setForeground(QColor("#00d4ff"))
            self.matrix_table.setItem(idx, 3, cell_right_code)

            cell_r = QTableWidgetItem(ln_r)
            cell_r.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            cell_r.setForeground(QColor("#4a7a9e"))
            self.matrix_table.setItem(idx, 4, cell_r)

            if tag == "EQUAL":
                self.working_lines_state[idx] = item.left_line
                blank_item = QTableWidgetItem("==")
                blank_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                blank_item.setForeground(QColor("#4a7a9e"))
                font = blank_item.font()
                font.setPointSize(10)
                blank_item.setFont(font)
                self.matrix_table.setItem(idx, 2, blank_item)
            else:
                self.set_row_action_buttons(idx, item)

        self.refresh_preview_buffer()

    def set_row_action_buttons(self, row_index: int, item):
        control_panel = QWidget()
        panel_layout = QHBoxLayout(control_panel)
        panel_layout.setContentsMargins(1, 1, 1, 1)
        panel_layout.setSpacing(4)
        panel_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        btn_l = QPushButton("◀ L")
        btn_l.setStyleSheet("QPushButton { font-size:10px; padding:2px; color:#ff4040; background-color:#1a0808; min-width: 42px; max-height: 20px; }")
        btn_l.clicked.connect(lambda checked, r_idx=row_index, data=item.left_line, obj=item: self.resolve_single_cell(r_idx, data, "L", obj))

        btn_r = QPushButton("R ▶")
        btn_r.setStyleSheet("QPushButton { font-size:10px; padding:2px; color:#00ff88; background-color:#04140e; min-width: 42px; max-height: 20px; }")
        btn_r.clicked.connect(lambda checked, r_idx=row_index, data=item.right_line, obj=item: self.resolve_single_cell(r_idx, data, "R", obj))

        panel_layout.addWidget(btn_l)
        panel_layout.addWidget(btn_r)
        self.matrix_table.setCellWidget(row_index, 2, control_panel)

    def resolve_single_cell(self, row_index: int, code_string: str, source_flag: str, original_item_obj):
        self.working_lines_state[row_index] = code_string

        undo_panel = QWidget()
        undo_layout = QVBoxLayout(undo_panel)
        undo_layout.setContentsMargins(1, 1, 1, 1)
        undo_layout.setSpacing(2)
        undo_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        status_color = "#00ff88" if source_flag == "R" else "#f5a623"
        status_lbl = QLabel(f"OK [{source_flag}]")
        status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_lbl.setStyleSheet(f"color: {status_color}; font-size: 10px; font-weight: bold; font-family: 'Share Tech Mono';")

        btn_undo = QPushButton("↩ Undo")
        btn_undo.setStyleSheet("""
            QPushButton {
                font-size: 9px;
                padding: 1px 2px;
                color: #c8e0ff;
                background-color: #0e2d5a;
                border: 1px solid #1a5fa8;
                border-radius: 2px;
                max-height: 15px;
                min-width: 58px;
            }
            QPushButton:hover { background-color: #ff4040; color: #fff; border: 1px solid #ff4040; }
        """)
        btn_undo.clicked.connect(lambda checked, r_idx=row_index, obj=original_item_obj: self.undo_single_resolution(r_idx, obj))

        undo_layout.addWidget(status_lbl)
        undo_layout.addWidget(btn_undo)
        self.matrix_table.setCellWidget(row_index, 2, undo_panel)

        self.refresh_preview_buffer()

    def undo_single_resolution(self, row_index: int, original_item_obj):
        self.working_lines_state[row_index] = ""
        self.set_row_action_buttons(row_index, original_item_obj)
        self.refresh_preview_buffer()

    def refresh_preview_buffer(self):
        compiled_stream = [line for line in self.working_lines_state if line is not None]
        self.merge_buffer.setPlainText("\n".join(compiled_stream))

    def bulk_accept_left(self):
        for idx, item in enumerate(self.diff_result.line_diffs):
            if item.tag.upper() != "EQUAL" and self.matrix_table.cellWidget(idx, 2) is not None:
                if self.matrix_table.cellWidget(idx, 2).findChild(QPushButton, ""):
                    if not self.matrix_table.cellWidget(idx, 2).findChild(QLabel):
                        self.resolve_single_cell(idx, item.left_line, "L", item)

    def bulk_accept_right(self):
        for idx, item in enumerate(self.diff_result.line_diffs):
            if item.tag.upper() != "EQUAL" and self.matrix_table.cellWidget(idx, 2) is not None:
                if self.matrix_table.cellWidget(idx, 2).findChild(QPushButton, ""):
                    if not self.matrix_table.cellWidget(idx, 2).findChild(QLabel):
                        self.resolve_single_cell(idx, item.right_line, "R", item)

    def save_merged_file(self):
        parent_window = self.parent()
        suggested_path = ""

        if parent_window:
            left_base = parent_window.left_input.text().strip()
            right_base = parent_window.right_input.text().strip()

            if self.diff_result.left_path and not self.diff_result.right_path and right_base:
                suggested_path = os.path.join(right_base, self.diff_result.relative_path)
            elif self.diff_result.right_path and not self.diff_result.left_path and left_base:
                suggested_path = os.path.join(left_base, self.diff_result.relative_path)

        if not suggested_path:
            suggested_path = str(self.diff_result.right_path if self.diff_result.right_path else self.diff_result.left_path)

        try:
            os.makedirs(os.path.dirname(suggested_path), exist_ok=True)
        except Exception:
            pass

        save_path, _ = QFileDialog.getSaveFileName(self, "COMMIT MERGED INTEGRITY VECTOR FILE OBJECT", suggested_path)
        if save_path:
            try:
                Path(save_path).write_text(self.merge_buffer.toPlainText(), encoding="utf-8")
                self.setWindowTitle("NUEVA SE SWISS KNIFE // WRITE PIPELINE MUTATION VERIFIED - LINE ACCEPTS SAVED")
            except Exception as e:
                self.merge_buffer.setPlainText(f"❌ STRUCTURAL WRITE ERROR PIPELINE EXCEPTION:\n{e}")


# ── BACKGROUND THREAD WORKERS FOR DATA MAPPING ───────────────────────────
class CompareWorker(QThread):
    progress = pyqtSignal(int, int, str)
    finished_signal = pyqtSignal(object)
    error_signal = pyqtSignal(str)

    def __init__(self, left, right, patterns):
        super().__init__()
        self.left, self.right, self.patterns = left, right, patterns

    def run(self):
        try:
            def callback(current, total, path):
                self.progress.emit(current, total, str(path))
            result = compare_folders(self.left, self.right, callback, self.patterns)
            self.finished_signal.emit(result)
        except Exception as e:
            self.error_signal.emit(str(e))


class SearchWorker(QThread):
    progress = pyqtSignal(int, int, str)
    finished_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, folder, query, regex, case):
        super().__init__()
        self.folder, self.query, self.regex, self.case = folder, query, regex, case

    def run(self):
        try:
            def callback(current, total, current_file):
                self.progress.emit(current, total, str(current_file))
            res = search_in_folder(self.folder, self.query, self.regex, self.case, callback)
            if not res.matches:
                self.finished_signal.emit("SEARCH OPERATIONS TERMINATED: 0 SPECIFIC PATTERNS CAPTURED.")
                return
            lines = ["🔍 [NUEVA SE SWISS KNIFE COGNITIVE VECTOR INDICES RESULTS MAP]"]
            for m in res.matches:
                lines.append(f"Node Target Vector Pointer ──► {m.relative_path} [Line Context: {m.line_number}]")
                lines.append(f"   ┃ Core Buffer Data Array Fragment:  {m.line_content.strip()}\n   ┗" + "━"*50)
            self.finished_signal.emit("\n".join(lines))
        except Exception as e:
            self.error_signal.emit(str(e))


# ── NUEVA SE SWISS KNIFE CONSOLE SYSTEM BASE INTERFACE LAYER ───────────────────────────
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NUEVA SE SWISS KNIFE // AI CONSOLE UTILITY WORKSPACE")
        self.resize(1150, 800)
        self.setStyleSheet(JARVIS_STYLE)

        self.cached_diff_map = {}
        self.raw_log_history = []  # Caches lines to implement fast local string queries
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        self.init_compare_tab()
        self.init_search_tab()
        self.init_formatter_tab()

    def init_compare_tab(self):
        tab = QWidget()
        tab.setStyleSheet("background-color: #071428;")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        for label_text, attr_name in [("SOURCE A DIR PATH:", "left_input"), ("SOURCE B DIR PATH:", "right_input")]:
            hl = QHBoxLayout()
            hl.addWidget(QLabel(label_text, minimumWidth=150))
            le = QLineEdit()
            setattr(self, attr_name, le)
            hl.addWidget(le)
            btn = QPushButton("MOUNT DIRECTORY")
            btn.clicked.connect(lambda checked, target=le: self.browse_folder(target))
            hl.addWidget(btn)
            layout.addLayout(hl)

        h_pat = QHBoxLayout()
        h_pat.addWidget(QLabel("SCAN BLACKLIST ARRS:", minimumWidth=150))
        self.compare_ignore = QLineEdit(".git, __pycache__, .DS_Store")
        h_pat.addWidget(self.compare_ignore)
        layout.addLayout(h_pat)

        self.btn_run_compare = QPushButton("RUN COGNITIVE DELTA VECTOR SCAN")
        self.btn_run_compare.setStyleSheet("QPushButton { background-color: #051a14; border: 1px solid #0087a8; color: #00ff88; padding: 12px; }")
        self.btn_run_compare.clicked.connect(self.start_folder_compare)
        layout.addWidget(self.btn_run_compare)

        self.compare_status = QLabel(">> STATUS CODE: INITIALIZED")
        self.compare_status.setStyleSheet("color: #4a7a9e;")
        layout.addWidget(self.compare_status)

        view_splitter = QSplitter(Qt.Orientation.Horizontal)

        left_panel = QWidget()
        lp_lay = QVBoxLayout(left_panel)
        lp_lay.setContentsMargins(0,0,0,0)
        lp_lay.addWidget(QLabel("❌ MUTATED OBJECT NODES DISCOVERED (DOUBLE CLICK TO MERGE):"))
        self.anomalies_sidebar = QListWidget()
        self.anomalies_sidebar.itemDoubleClicked.connect(self.open_merge_window)
        lp_lay.addWidget(self.anomalies_sidebar)
        view_splitter.addWidget(left_panel)

        right_panel = QWidget()
        rp_lay = QVBoxLayout(right_panel)
        rp_lay.setContentsMargins(0,0,0,0)

        # SEARCH FILTER INTERFACE FOR LOG STREAM INSPECTIONS
        search_filter_layout = QHBoxLayout()
        search_filter_layout.addWidget(QLabel("🔍 FILTER LOG RECORDS:", minimumWidth=130))
        self.log_search_input = QLineEdit()
        self.log_search_input.setPlaceholderText("Type keywords here (e.g., IDENTICAL, MODIFIED, filename)...")
        self.log_search_input.textChanged.connect(self.filter_console_logs)
        search_filter_layout.addWidget(self.log_search_input)
        rp_lay.addLayout(search_filter_layout)

        rp_lay.addWidget(QLabel("📋 SYSTEM CONSOLE RAW LOG INTERACTION STREAM:"))
        self.compare_output = QTextEdit()
        self.compare_output.setReadOnly(True)
        rp_lay.addWidget(self.compare_output)
        view_splitter.addWidget(right_panel)

        view_splitter.setSizes([350, 700])
        layout.addWidget(view_splitter)
        self.tabs.addTab(tab, "DIFF CONTROLLER")

    def init_search_tab(self):
        tab = QWidget()
        tab.setStyleSheet("background-color: #071428;")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)

        h_dir = QHBoxLayout()
        h_dir.addWidget(QLabel("INDEX REGION TARGET:", minimumWidth=150))
        self.search_folder_input = QLineEdit()
        btn_browse_s = QPushButton("RESOLVE SPACE")
        btn_browse_s.clicked.connect(lambda: self.browse_folder(self.search_folder_input))
        h_dir.addWidget(self.search_folder_input)
        h_dir.addWidget(btn_browse_s)
        layout.addLayout(h_dir)

        h_query = QHBoxLayout()
        h_query.addWidget(QLabel("REGEX KEYSTREAM STR:", minimumWidth=150))
        self.search_query_input = QLineEdit()
        h_query.addWidget(self.search_query_input)
        layout.addLayout(h_query)

        h_chk = QHBoxLayout()
        self.chk_regex = QCheckBox("USE ADVANCED EXTENDED REGEX MODELS")
        self.chk_case = QCheckBox("STRICT CASE ITERATION MATRIX CHECK")
        h_chk.addWidget(self.chk_regex)
        h_chk.addWidget(self.chk_case)
        layout.addLayout(h_chk)

        self.btn_run_search = QPushButton("DISPATCH NEURAL LOOKUP SUBSYSTEM")
        self.btn_run_search.clicked.connect(self.start_text_search)
        layout.addWidget(self.btn_run_search)

        self.search_status = QLabel(">> STATUS CODE: INITIALIZED")
        self.search_status.setStyleSheet("color: #4a7a9e;")
        layout.addWidget(self.search_status)

        self.search_output = QTextEdit()
        self.search_output.setReadOnly(True)
        layout.addWidget(self.search_output)
        self.tabs.addTab(tab, "VECTOR SEARCH")

    def init_formatter_tab(self):
        tab = QWidget()
        tab.setStyleSheet("background-color: #071428;")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)

        h_file = QHBoxLayout()
        h_file.addWidget(QLabel("FILE OBJECT SOURCE:", minimumWidth=150))
        self.formatter_file_input = QLineEdit()
        btn_browse_f = QPushButton("PULL OBJECT")
        btn_browse_f.clicked.connect(self.browse_single_file)
        h_file.addWidget(self.formatter_file_input)
        h_file.addWidget(btn_browse_f)
        layout.addLayout(h_file)

        self.formatter_text_area = QTextEdit()
        layout.addWidget(self.formatter_text_area)

        h_actions = QHBoxLayout()
        btn_format = QPushButton("OPTIMIZE AST STRUCTURAL LINTING PROPERTIES")
        btn_format.setStyleSheet("QPushButton { color: #f5a623; background-color: #211905; }")
        btn_format.clicked.connect(self.execute_buffer_format)
        h_actions.addWidget(btn_format)

        btn_clear = QPushButton("FLUSH CORES")
        btn_clear.clicked.connect(lambda: self.formatter_text_area.clear())
        h_actions.addWidget(btn_clear)
        layout.addLayout(h_actions)

        self.formatter_status = QLabel(">> STATUS CODE: INITIALIZED")
        self.formatter_status.setStyleSheet("color: #4a7a9e;")
        layout.addWidget(self.formatter_status)
        self.tabs.addTab(tab, "AST RECONSTRUCTOR")

    def browse_folder(self, target_line_edit):
        folder = QFileDialog.getExistingDirectory(self, "INDEX NUEVA SE SWISS KNIFE FILE TARGET STACK LOCATION")
        if folder: target_line_edit.setText(folder)

    def browse_single_file(self):
        f, _ = QFileDialog.getOpenFileName(self, "RESOLVE DATA OBJECT FILE STRUCT NODE")
        if f:
            self.formatter_file_input.setText(f)
            self.formatter_text_area.setPlainText(Path(f).read_text(encoding="utf-8", errors="replace"))

    def start_folder_compare(self):
        l, r = self.left_input.text().strip(), self.right_input.text().strip()
        if not l or not r: return
        self.btn_run_compare.setEnabled(False)
        self.anomalies_sidebar.clear()
        self.cached_diff_map.clear()
        self.raw_log_history.clear()

        patterns = [p.strip() for p in self.compare_ignore.text().split(",") if p.strip()]
        self.compare_thread = CompareWorker(l, r, patterns)
        self.compare_thread.progress.connect(lambda c, t, p: self.compare_status.setText(f">> MERGE INDEX MAP: {c}/{t} -> {p}"))
        self.compare_thread.error_signal.connect(lambda e: [self.btn_run_compare.setEnabled(True), self.compare_output.setPlainText(e)])
        self.compare_thread.finished_signal.connect(self.process_comparison_results)
        self.compare_thread.start()

    def process_comparison_results(self, result_payload):
        self.btn_run_compare.setEnabled(True)
        self.compare_status.setText(">> ARCHITECTURE CALCULATIONS RUNTIME CONSOLIDATED COMPLETED.")

        self.raw_log_history = [
            "⚡ [SYSTEM LOG: COMPARE CORE RUNTIME MATRIX DATA]",
            f"TOTAL EVALUATED OBJECT NODES: {result_payload.total_files_scanned}\n"
        ]

        for r in result_payload.results:
            status_str = r.status.value.upper()
            self.raw_log_history.append(f" ╰─► [{status_str}] {r.relative_path}")

            if r.status.value in ("modified", "left_only", "right_only", "binary_differ"):
                item_text = f"[{status_str}] {r.relative_path}"
                item = QListWidgetItem(item_text)
                self.anomalies_sidebar.addItem(item)
                self.cached_diff_map[item_text] = r

        self.filter_console_logs()

    def filter_console_logs(self):
        """Funnels lines from cached memory history applying matching rule subsets."""
        query = self.log_search_input.text().strip().lower()
        if not query:
            self.compare_output.setPlainText("\n".join(self.raw_log_history))
            return

        filtered_lines = []
        # Keep tracking header indices clean from filtering rules
        if len(self.raw_log_history) >= 2:
            filtered_lines.extend(self.raw_log_history[:2])
            target_pool = self.raw_log_history[2:]
        else:
            target_pool = self.raw_log_history

        for line in target_pool:
            if query in line.lower():
                filtered_lines.append(line)

        self.compare_output.setPlainText("\n".join(filtered_lines))

    def open_merge_window(self, item: QListWidgetItem):
        key = item.text()
        if key in self.cached_diff_map:
            diff_obj = self.cached_diff_map[key]
            dialog = MergeConsoleDialog(diff_obj, self)
            dialog.exec()

    def start_text_search(self):
        f, q = self.search_folder_input.text().strip(), self.search_query_input.text()
        if not f or not q: return
        self.btn_run_search.setEnabled(False)
        self.search_thread = SearchWorker(f, q, self.chk_regex.isChecked(), self.chk_case.isChecked())
        self.search_thread.finished_signal.connect(lambda s: [self.btn_run_search.setEnabled(True), self.search_output.setPlainText(s)])
        self.search_thread.start()

    def execute_buffer_format(self):
        try:
            fmt, msg, lang = format_code(self.formatter_text_area.toPlainText(), self.formatter_file_input.text())
            self.formatter_text_area.setPlainText(fmt)
            self.formatter_status.setText(f">> PIPELINE DEPLOYED RESOLVED: [{lang.value.upper()}] {msg}")
        except Exception as e: 
            self.formatter_status.setText(f">> PIPELINE FAULT: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())