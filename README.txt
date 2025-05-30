========================================================================
⚡️ **OVERCLOCK** – Watt-Bit Infrastructure Sandbox (Alpha 2025.01.02a) ⚡️
========================================================================

By **Watt-Bit Research** <https://watt-bit.com>  
Presented by **Augur VC** <https://augurvc.com>

> **EXPANDED ALPHA PREVIEW – READ ME FIRST**  
> This is pre-beta software. Bugs, missing polish, and rapidly-changing UX are expected. Your feedback shapes the roadmap!

---

## 🔒  Security & First-Run

**Unsigned binaries will trigger OS warnings.**

*Windows*  
1. Launch installer → **More info** → **Run anyway**.

*macOS*  
1. Launch app (Dock icon appears).  
2. System Settings → Privacy & Security → “OVERCLOCK was blocked …” → **Open Anyway** (twice).  
3. Enter your macOS password.  
*Allow 30–45 s for the first start-up.*

---

## ✨  What Is OVERCLOCK?

OVERCLOCK lets you model, simulate, and analyze watt-bit infrastructure — everything from natural gas and solar arrays feeding GPU clouds to grid-export revenue plays — over a full 8760-hour year.

---

## 🚀  Core Features

1. **Visual Modeling**  
   * Drag-and-drop components (Generator, Battery, Grid Import/Export, Bus, Load, Cloud, Solar, Wind, Props).  
   * **C** to create a connection, **A** to Autoconnect All.  
   * Properties panel fixed at right for live edits.

2. **Time-Based Simulation**  
   * **Space** – run/pause; **R** – reset.  
   * Slider scrubs the full year

3. **Analysis & Insights**  
   * Live **CAPEX** & **IRR** (12/18/36-mo refresh).  
   * **Analytics Panel (P)** – real-time charts.  
   * **Historian (\\)** – full-year data after Autocomplete.

4. **Autocomplete (Enter)**  
   * Runs the whole year in background, flips to Historian, and shows final IRR.

5. **Scenario Management** – Save/Load/New JSON designs.

6. **New 2025.01.02a**  
   * **Terminal Panel** in the right dock streams live logs (startup BIOS text, component events, sim status) for better feedback to user.  
   * **Status Jewels** – every component now shows a tiny animated hexagon reflecting health & state.  
   * **Improved CSV Import**  
   * **Component Re-skin & Unified Text** – high-res icons, cleaner fonts, color-coded $$ (green = revenue, red = cost), “MW | Mode” labels.  
   * **Properties Panel 2.0** – fixed to selected component display, click-to-open logic, sleeker styling, no title bar.  
   * **Particle FX** – puff on add *and* delete for tactile feedback.  
   * **Refinements** – improved buttons, widened Build/Historian toggle, export-icon fix, miscellaneous polish.

---

## 🎹  Hotkeys

G  – Add Gas Generator          E  – Add Grid Export
B  – Add Electrical Bus         S  – Add Battery
L  – Add Load                   W  – Add Cloud Workload
I  – Add Grid Import            C  – Start Creating Connection
A  – Autoconnect All            Space – Run / Pause
R  – Reset                      Enter – Autocomplete
\  – Toggle Build / Historian   P  – Toggle Analytics
Delete – Delete selection


## 🚀  Quick Start
	1.	Drop a Generator, Bus, and Load.
	2.	A to Autoconnect or C to wire manually.
	3.	Tweak parameters in the Properties panel.
	4.	Space to simulate, or Enter to Autocomplete.
	5.	Explore live charts (P) and Historian (\).

⸻

## 📝  Feedback & Bugs

Open an issue or email alpha@watt-bit.com. Crash logs and screenshots help immensely—thanks for pushing us toward beta!

⸻

## 🗒️  Changelog

2025.01.02a (Expanded Alpha)
	•	Fixed: Battery charge glitch during gas generator maintenance mode.
	•	Fixed: Export-connection icon mis-direction.
	•	Added: Terminal Panel with BIOS-style startup and live sim logs.
	•	Added: Animated status jewels on every component.
	•	Added: Tooltip framework (initial rollout).
	•	Component re-skin, unified fonts/colors, particle effects.
	•	Add-Component button and simulation controls restyled.
	•	Properties Panel overhaul + Selected Component display.
	•	Build/Historian toggle widened for better legibility.
	•	Robust CSV handler with import-format popup.
	•	Refactored: Properties Manager isolated; internal code cleanup for maintainability.
	•	Minor: Smoke particle tweaks, standard text boxes with subtle borders, consistent hover/press states across all icon buttons.