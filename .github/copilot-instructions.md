**Repository Overview**

- **Purpose:** Desktop PyQt GUI that coordinates force gauges, a motor controller, camera capture and plotting. Entry point is `main.py`; the UI class is generated into `ui_file.py` from `main.ui`.
- **Major components:** `mark10_force_reader.py` (serial reader, QThreads, data saver), `controller.py` (motor), `image_taker.py` (camera), `plotter.py` (matplotlib canvases), `ui_file.py` / `main.ui` (UI), `new.qrc` + `new_rc.py` (resources).

**How To Run / Dev Workflow (Windows PowerShell)**

- Create a venv and install runtime deps:

```powershell
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt   # if you create one; otherwise install PyQt5/PyQt6, pyserial, numpy, matplotlib
pip install pyserial numpy matplotlib
```

- Start the app:

```powershell
python main.py
```

- Packaging: a `main.spec` exists — build with PyInstaller when ready:

```powershell
pyinstaller main.spec
```

**Important Patterns & Conventions**

- UI generation: `ui_file.py` is generated from `main.ui`. Prefer regenerating the file with `pyuic6` (for PyQt6) instead of hand-editing the generated blocks.
  - Regenerate: `pyuic6 -x main.ui -o ui_file.py` or `python -m PyQt6.uic.pyuic main.ui -o ui_file.py`.
- Resources: stylesheets use `url(:/prefix/path)` with `new_rc.py`. PyQt6 changed resource tooling — if you see resource failures, either keep the generated `new_rc.py` (if present) or replace `:/...` references with direct file paths like `images/aa.png`.
- Threading: hardware readers are implemented as `QtCore.QThread` subclasses that emit signals (e.g., `mark10_f_values` sends `mark10_connection_fail_signal`, `mark10_connection_lost_signal`). Always start threads with `.start()` and stop them by toggling flags and closing handles (serial ports are closed inside exception handlers).
- Timers: GUI uses `QtCore.QTimer()` for polling/updating (example: `update_timer.start(100)`). Connect `timeout` to update handlers.
- Styling: many widgets use inline stylesheets with image references; if resources fail, check paths in `ui_file.py` stylesheets.

**Common Migration / Fix Items (PyQt5 → PyQt6)**

- Replace module imports: `from PyQt5 import QtCore, QtGui, QtWidgets` → `from PyQt6 import QtCore, QtGui, QtWidgets`.
- Enums are scoped and now use Python `Enum` classes. Typical quick fixes:
  - `Qt.AlignCenter` → `Qt.AlignmentFlag.AlignCenter`
  - `Qt.ImhDigitsOnly` → `Qt.InputMethodHint.ImhDigitsOnly`
  - `app.exec_()` → `app.exec()`
- Re-generating `ui_file.py` with `pyuic6` will fix many enum/flag differences automatically — do that before manual edits.

**Where to look for help when debugging a feature**

- UI & visuals: `main.ui` and `ui_file.py` (regenerate `ui_file.py` to apply Qt6 changes).
- Force gauge serial handling and threads: `mark10_force_reader.py` (look for `QThread`, `pyqtSignal`, `serial.Serial`, `in_waiting`, `readline()`).
- Motor commands: `controller.py` (COM control, connect/disconnect patterns).
- Plotting: `plotter.py` (matplotlib canvases are added to `graphing_layout` in `AppWindow`).
- Data saving: threads inside `mark10_force_reader.py` use `csv.writer` with `file_name` set by other components.

**AI Agent Guidance (do’s and don’ts)**

- Do regenerate `ui_file.py` from `main.ui` for PyQt6 changes; mention the exact command used in a PR. Do not hand-edit generated blocks unless necessary — if you do, mark the region and keep changes minimal.
- Do search for `Qt.` enum usages and run the app to catch errors; change to scoped enums or re-generate the UI.
- Do not remove or alter `QThread` start/stop logic; tests should validate threads stop by toggling the `should_read` flags and closing serial handles.
- When changing resource paths, update all stylesheet references in `ui_file.py` and commit `new_rc.py` removal only after a working alternative (direct file paths) is validated.

**Quick PR checklist for UI / PyQt changes**

- Regenerate `ui_file.py` (if changed) and verify no merge conflicts with hand edits.
- Run `python main.py` and smoke-test: open UI, click connect buttons (or run with simulated generator), and observe no enum or stylesheet exceptions.
- Verify threads start and stop without uncaught exceptions (watch console for serial errors).

If anything is unclear or you want this file merged into repository now, tell me and I'll iterate.
