# F1 Simulation 

An interactive desktop replay application built with Python, Arcade, and FastF1. This tool visualizes real-time Formula 1 telemetry, providing a pitwall-style dashboard including track maps, live leaderboards, session weather and many to come up over the next updates.

🌟 Key Features
Sequential SQL Replay: Optimized data handling using SQLite to stream telemetry row-by-row, ensuring 60 FPS performance without high RAM overhead.

> Dynamic Track Map: Auto-rotating and scaled track layout based on actual session coordinates.

> Pit Wall UI: Card-style weather information and leaderboards inspired by official F1 graphics.

> Frame-Sync Weather: Intelligent weather updates synced to telemetry frames using a custom frame-ratio logic.

> Driver Telemetry: Visualizes position, speed, gear, RPM, and DRS status for every driver on the grid.

## 📂 Project Structure

```text
F1_VISUALIZER/
├── core/
│   ├── session_manager.py      # FastF1 session handling
│   ├── data_exporter.py       # SQL database generation (sequential export)
│   └── telemetry_processor.py  # Coordinate & data processing logic
├── rendering/
│   └── ui_renderer.py         # Arcade drawing functions for cards & UI
├── utils/
│   └── helpers.py             # Coordinate conversion & math helpers
├── database/                  # Auto-generated .db files for each race
└── main.py                    # Main application loop & logic

```
## 🚀 Getting Started

Follow these steps to set up the environment and launch the F1 Telemetry Replay on your machine.

### 1. Prerequisites
Ensure you have **Python 3.10** or higher installed. You will also need the following libraries:
* `fastf1`: For Formula 1 data access.
* `arcade`: For the 2D hardware-accelerated engine.
* `pandas`: For data manipulation.
* `sqlite3`: (Built-in) For high-performance telemetry streaming.

### 2. Installation
Clone this repository and install the required dependencies:

### 3. Configuration
Open main.py and set the target race details at the top of the file:

```python 
year = 2025
GP_NAME = "bahrain"
```
### 4. Running the Application
Launch the visualizer by running the main script:
```bash
git clone https://github.com/yourusername/F1_VISUALIZER.git

cd F1_VISUALIZER

python -m venv .venv

# On Windows:
.venv\Scripts\activate

# On macOS/Linux:
source .venv/bin/activate

# Install dependencies from requirements.txt
pip install -r requirements.txt

python main.py

```

## 🤝 Contributing

Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

1. **Open an Issue:** For major changes, please open an issue first to discuss what you would like to change.
2. **Fork the Project:** Create your own copy of the repository.
3. **Create a Feature Branch:** `git checkout -b feature/AmazingFeature`
4. **Commit your Changes:** `git commit -m 'Add some AmazingFeature'`
5. **Push to the Branch:** `git push origin feature/AmazingFeature`
6. **Open a Pull Request:** Submit your changes for review.

Please make sure to update tests as appropriate to maintain project stability.

## 📄 License

Distributed under the **MIT License**. See `LICENSE` for more information.

---
*Developed by SumanGouda - [2026]*