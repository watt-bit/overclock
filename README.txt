=========================================================================
⚡️ **OVERCLOCK** – Watt-Bit Infrastructure Sandbox (Beta 2025.02.01b) ⚡️
=========================================================================

By **Watt-Bit Research** <https://watt-bit.com>  
Presented by **Augur VC** <https://augurvc.com>

> **OPEN BETA – READ ME FIRST**  
> This is beta software. Bugs, missing polish, and rapidly-changing UX are expected. Your feedback shapes the roadmap! 

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

A rich and high-impact user experience driven by opinionated design and configuration, careful attention to detail, more than 50 original graphics assets, and input from dozens of subject matter experts.

---

## 🚀  Core Features

1. **Node-Based Visual AI Infra Modeling**  
   * Drag-and-drop components (Generator, Battery, Grid Import/Export, Bus, Load, Cloud, Solar, Wind, Props). 
   * **C** to create a connection, **A** to Autoconnect All.  
   * Properties panel allows configuration of deep component operational simulation with multiple smart modes per component. Defaults "just work".
   * Powerlandia data sets offer moderate-fidelity simulations "out of the box".

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


## 🆕  Beta Highlights (2025)

- **Cinematic intro**: Augur → WBR → Title sequence with video background and synchronized music.
- **Integrated audio**: Low‑latency sound effects, precached at startup; background playlist with next‑track control and marquee title.
- **Fulsom Terminal panel**: Built‑in terminal shows status, errors, and UX hints with colored dots; replaces most popups.
- **Properties overlay**: Fixed 300px right‑side overlay with consistent styling; controls stay visible and grey‑out when inactive.
- **Selected component pill**: Clickable display of current selection; opens the corresponding properties panel.
- **Animated connections**: Soft gradient cores, breathing glow, flowing dashes, moving pulse, and subtle sparkles.
- **Scrub‑safe timeline**: Slider supports scrubbing with minimal analytics updates; clear connectivity checks and messages.
- **Overlays for metrics**: Always‑visible CAPEX and IRR labels anchored to the canvas.
- **CSV profile workflow**: Guided dialog explains expected 8760‑row CSV format before loading custom profiles.

---

## 🎧  Audio & Media

- **Background music**: Toggle from the top overlay (🎵), advance with ⏭. Song title marquee reflects current track; shows “--” when off.
- **Sound effects**: Button hover/click, place/delete component, simulation start/end, success/fail chimes.
- **Performance**: Uses PyQt6 multimedia; sound effects are pooled and precached for low latency. Video playback uses bundled FFmpeg in packaged builds.

---

## 🖥️  UI / UX Enhancements

- **TerminalWidget**: In‑app logging with blue/red bullet markers; scrolls to latest. No focus‑stealing popups for non‑critical events.
- **Properties Panel**: Right‑side overlay, fixed width, consistent styling; delete button auto‑disables during run/autocomplete; CSV helper dialog.
- **SelectedComponentDisplay**: Compact, clickable pill shows `<type> <id6>`; opens properties.
- **Connection visuals**: Cohesive animated cables with wavy path, hue‑shift gradient, dynamic pulse and endpoint glow.
- **Music controls**: Floating overlay centered between Build button and Properties panel; matches app theme.
- **Backgrounds and particles**: Title/intro visuals and subtle particle effects for adds/deletes and welcome text.

---

## 💾  Data & Scenarios

- **Built‑in datasets**: Powerlandia load and pool prices, solar/wind generation profiles in `src/data/`.
- **Scenario management**: New/Save/Load via toolbar and Model menu. Designs are JSON.
- **Autocomplete & Historian**: Enter runs to end in background and flips to Historian with final IRR.

---

## 🛠️  System Requirements

- **OS**: Windows 10/11, macOS 13+ (Apple Silicon and Intel supported).
- **Beta builds**: Unsigned; see Security & First‑Run above to bypass OS warnings.

---

## 🧩  Troubleshooting

- **App doesn’t open (macOS)**: System Settings → Privacy & Security → Open Anyway (twice). First launch may take 30–45s.
- **No audio**: Make sure system output isn’t muted; try toggling music (🎵) or advancing track (⏭). Some systems require first playback after the window is shown; wait a few seconds.
- **Black video on intro**: Older GPUs or codecs may delay start; audio still plays. Proceed to main screen with Enter.
- **Simulation won’t start**: Ensure a single connected network. The terminal displays a red‑dot error and the border flashes.

