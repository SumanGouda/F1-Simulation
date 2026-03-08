import os
from core.session_manager import SessionManager
from core.data_exporter import DataExporter

def main():
    # 1. Initialize and Load Session
    print("Loading F1 Session data from FastF1... (This may take a minute)")
    sm = SessionManager(year=2025, gp="Bahrain", session_type="R")
    
    # Check if session loaded successfully
    if sm.session is None:
        print("Failed to load session. Please check your internet connection or GP name.")
        return

    # 2. Initialize the Exporter with the loaded session [cite: 2026-01-20]
    exporter = DataExporter(sm)
    
    # 3. Run the export process 
    print(f"Beginning export to {exporter.base_path}...")
    exporter.export_all_drivers()
    
    print("\n--- Export Finished Successsfully ---")
    print(f"Location: {os.path.abspath(exporter.base_path)}")
    print("You can now use the SQLite Viewer in VS Code to inspect the .db files.")

if __name__ == "__main__":
    main()