========================================================
⚡️ OVERCLOCK - Power System Simulator (Alpha Preview) ⚡️
========================================================

By: Watt-Bit Research (https://watt-bit.com)
Presented by: Augur VC (https://augurvc.com)

***ALPHA PREVIEW - IMPORTANT***
This is an early alpha version. You may encounter bugs or incomplete features. Your feedback is valuable!

🔒 SECURITY WARNINGS (Unsigned Application)
- **On Windows:** You will see "Windows protected your PC". Click **More info** → **Run anyway**.
- **On macOS:** You will see "can't be opened because it is from an unidentified developer." Click "Done", then:
  1. Open System Settings → Privacy & Security.
  2. Scroll to the bottom and find "OVERCLOCK was blocked to protect your Mac".
  3. Click **Open Anyway**, then **Open Anyway** again in the popup.
  4. Enter your system password.
  *This is only needed the first time you run the app.*

  NOTE: For MacOS, OVERCLOCK can take 30-45 seconds to open after its icon first appears in the application dock. Please be patient with it :-)

✨ WHAT IS OVERCLOCK?
OVERCLOCK allows you to build, simulate, and learn about watt-bit infrastructure. Drag-and-drop components, connect them, and run time-based simulations to understand energy flow, operations, and project economics.

🚀 CORE FEATURES
1. 🔧 Visual Modeling
   - Drag-and-drop components from the left-hand "Components" panel.
   - Components: Gas Generator, Battery Storage, Electrical Bus, Load, Cloud Workload, Grid Import/Export, Solar Array, Wind Turbine, Props.
   - Create connections with the **C** key or **Create Connection** button; use **A** to Autoconnect All.
   - Select components to edit parameters (capacity, cost, efficiency) in the floating Properties panel (toggle in **View** menu).
2. ⏱️ Time-Based Simulation
   - **Space:** Run/Pause hourly simulation.
   - **R:** Reset simulation to time 0.
   - **Time Slider:** Scrub through 8760 hours (1 year).
   - **Speed Control:** Adjust playback speed (1x, 2x, 3x).
3. 📈 Analysis & Insights
   - **CAPEX Display:** Shows total capital expenditure, updated on changes.
   - **IRR Display:** Calculates Internal Rate of Return for 12, 18, 36-month refresh cycles.
   - **Analytics Panel (P):** Real-time charts of generation, consumption, capacity.
   - **Historian View (\\):** Historical time-series charts after Autocomplete.
4. 🤖 Autocomplete (Enter)
   - Runs full-year simulation in the background.
   - Switches to Historian view on completion.
   - Displays final IRR.
5. 💾 Scenario Management
   - **Model → Save/Load/New** to manage designs in JSON format.
6. 🖼️ Other Features
   - **Screenshot:** Capture build or historian views.
   - **Zoom:** Zoom modeling view.
   - **Background Toggle:** Change canvas background.
   - **Hotkeys:** See below.

🎹 HOTKEYS
```
G: Add Gas Generator
B: Add Electrical Bus
L: Add Load
I: Add Grid Import
E: Add Grid Export
S: Add Battery Storage
W: Add Cloud Workload
C: Start Creating Connection
A: Autoconnect All
Space: Run/Pause
R: Reset
Enter: Autocomplete
\\: Toggle Build/Historian view
P: Toggle Analytics
Delete/Backspace: Delete selection
```

🚀 GETTING STARTED
1. Add components (e.g., Generator, Bus, Load).
2. Connect them (**C** or **A**).
3. Edit properties as needed.
4. Press **Space** to run simulation or **Enter** to Autocomplete.
5. Explore Analytics and Historian views.

📝 FEEDBACK
This is an alpha. Please report any bugs or suggestions! Thank you for testing OVERCLOCK. 