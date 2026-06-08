# F1 Race Replay - Arcade Edition

## 🏎 Overview
F1 Race Replay is a Python-based desktop application that lets you relive past Formula 1 races like a real race engineer. 
Built with the Arcade library and powered by real FastF1 telemetry data, it renders a live race replay with car positions 
updating lap by lap on the actual circuit layout. The app displays a real-time leaderboard with gap intervals, 
live session weather conditions (air temp, track temp, humidity, wind speed), lap counter, and full driver telemetry 
(speed, RPM, throttle, brake) accessible by clicking any driver. Playback speed can be controlled at any time 
using the slow, pause, and fast controls.

## 📸 Screenshots / Demo
GIF or image of the replay running

## ⚙️ Features
- Race replay with real telemetry
- Live leaderboard
- Playback controls (slow/pause/fast)
- Weather card
- Focused driver telemetry panel
- Dynamic GP + year selection

## 🛠 Tech Stack
- Python
- Arcade (rendering)
- FastF1 (data)
- SQLite (storage)
- Tkinter (selection UI)

## 📁 Project Structure

```
F1_SIMULATION/
├── assets/
│   ├── fonts/
│   └── images/
├── config/
│   └── settings.py
├── database/
    └── .db files
├── core/
│   ├── data_exporter.py
│   ├── session_manager.py
│   └── telemetry_processor.py
├── rendering/ 
│   ├── selection_dialog.py
│   └── ui_renderer.py
├── utils/
│   ├── helpers.py
│   └── track_utils.py
├── .gitignore
├── main.py
├── README.md
└── requirements.txt
```

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Git

### Installation

**1. Clone the repository**
```bash
https://github.com/SumanGouda/F1-Simulation
cd F1_SIMULATION
```

**2. Create a virtual environment**
```bash
python -m venv .venv
```

**3. Activate the virtual environment**
```bash
# Windows
.venv\Scripts\activate

# Mac/Linux
source .venv/bin/activate
```

**4. Install dependencies**
```bash
pip install -r requirements.txt
```

### Running

```bash
python main.py
```

A selection dialog will appear — choose a **year** and **Grand Prix location** from the dropdown menus and click **Start Replay**. The race replay window will launch and begin loading telemetry data automatically.

> **Note:** First run for a new GP will take longer as FastF1 downloads and caches the session data. Subsequent runs for the same GP and year will load instantly from the local cache.

## 📊 Data Pipeline

```
FastF1 API → SessionManager → DataExporter → SQLite (.db) → Arcade Renderer
```

**1. FastF1 API**
When a year and GP are selected, `SessionManager` uses the FastF1 library to fetch the official race session data including lap telemetry, weather, circuit layout, and results. Data is cached locally in the `cache/` folder so repeat runs don't require a re-download.

**2. DataExporter**
Once the session is loaded, `DataExporter` processes and writes all data into a single SQLite `.db` file stored in `database/race_{location}_{year}/`. Each driver gets their own telemetry table (`telemetry_ver`, `telemetry_nor` etc.), alongside a shared `weather` table and a `laps` table.

**3. SQLite**
The `.db` file acts as the backbone of the replay. Every frame, the Arcade window queries the database for each driver's current position, speed, RPM, throttle, brake, DRS, and lap number using a row offset that advances based on playback speed.

**4. Arcade Renderer**
The renderer reads the queried data each frame and draws the track layout, car positions, leaderboard, weather card, lap counter, playback controls, and telemetry charts in real time.

## 🎮 Controls

| Action | How |
|--------|-----|
| Select driver for focused view | Click on any driver row in the leaderboard |
| Return to full track view | Click anywhere on the empty track area |
| Pause / Resume replay | Click the ⏸ pause icon (bottom left) |
| Increase playback speed | Click the ⏩ fast icon (bottom left) |
| Decrease playback speed | Click the ⏪ slow icon (bottom left) | 

> Playback speed ranges from **0.5×** to **5.0×** in increments of 0.5. Current speed is shown on the icon when active.
## 🗺 Roadmap

- [ ] Pit stop animations and strategy overlay
- [ ] Side by side driver telemetry comparison
- [ ] Tyre compound tracking on leaderboard
- [ ] DRS zone indicators on track layout
- [ ] Sector time display per driver
- [ ] Support for Qualifying and Sprint sessions
- [ ] Export replay as video

## 📄 License

This project is licensed under the MIT License.