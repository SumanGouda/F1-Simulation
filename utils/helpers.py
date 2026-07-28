# utils/helpers.py
import numpy as np
import sqlite3
import os


def hex_to_rgb(hex_str):
    if not hex_str or not isinstance(hex_str, str):
        return (128, 128, 128)
    hex_str = hex_str.lstrip('#')
    return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))


def get_screen_coords(x, y, rotation, track_scale, offset_x, offset_y):
    rad = np.radians(rotation)
    tx  = x * np.cos(rad) - y * np.sin(rad)
    ty  = x * np.sin(rad) + y * np.cos(rad)
    return (tx * track_scale) + offset_x, (ty * track_scale) + offset_y


def calculate_weather_frame_ratio(driver_abbrs, db_path):
    """
    Calculates the ratio: (Max Telemetry Rows) / (Weather Rows).
    Tells the main loop how many frames to wait before shifting the weather row.
    """
    try:
        conn               = sqlite3.connect(db_path)
        max_telemetry_rows = 0

        for abbr in driver_abbrs:
            try:
                count = conn.execute(
                    f"SELECT COUNT(*) FROM telemetry_{abbr.lower()}"
                ).fetchone()[0]
                if count > max_telemetry_rows:
                    max_telemetry_rows = count
            except Exception:
                continue

        weather_rows = conn.execute("SELECT COUNT(*) FROM weather").fetchone()[0]
        conn.close()

        if weather_rows > 0:
            return max(1, max_telemetry_rows // weather_rows)

    except Exception as e:
        print(f"Error calculating frame ratio: {e}")

    return 1


def get_max_session_rows(driver_abbrs, db_path):
    max_rows = 0
    try:
        conn = sqlite3.connect(db_path)
        for abbr in driver_abbrs:
            try:
                count = conn.execute(
                    f"SELECT COUNT(*) FROM telemetry_{abbr.lower()}"
                ).fetchone()[0]
                if count > max_rows:
                    max_rows = count
            except Exception:
                continue
        conn.close()
    except Exception as e:
        print(f"Error getting max session rows: {e}")
    return max_rows


def prepare_track_layout(raw_x, raw_y, screen_width, screen_height, padding_left, rotation):
    """Fits the track perfectly within the available screen space."""
    draw_width  = screen_width  - padding_left - 100
    draw_height = screen_height - 150

    rad   = np.radians(rotation)
    x_rot = raw_x * np.cos(rad) - raw_y * np.sin(rad)
    y_rot = raw_x * np.sin(rad) + raw_y * np.cos(rad)

    data_width  = max(x_rot) - min(x_rot)
    data_height = max(y_rot) - min(y_rot)

    scale_x     = draw_width  / data_width
    scale_y     = draw_height / data_height
    track_scale = min(scale_x, scale_y) * 0.9

    x_scaled = x_rot * track_scale
    y_scaled = y_rot * track_scale

    track_center_x  = (min(x_scaled) + max(x_scaled)) / 2
    track_center_y  = (min(y_scaled) + max(y_scaled)) / 2
    screen_center_x = padding_left + (draw_width / 2)
    screen_center_y = screen_height / 2

    offset_x = screen_center_x - track_center_x
    offset_y = screen_center_y - track_center_y

    fx = x_scaled + offset_x
    fy = y_scaled + offset_y

    return fx, fy, offset_x, offset_y, track_scale


def get_results_from_db(db_path):
    if not os.path.exists(db_path):
        return {}, []

    try:
        conn   = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT Abbreviation, DriverNumber, TeamName, TeamColor,
                   Position, GridPosition, Time, Status, Points, Laps
            FROM results
            ORDER BY GridPosition ASC
        """)
        rows    = cursor.fetchall()
        columns = ['DriverNumber', 'TeamName', 'TeamColor', 'Position',
                   'GridPosition', 'Time', 'Status', 'Points', 'Laps']
        conn.close()

        driver_metadata = {}
        sorted_drivers  = []

        for row in rows:
            abbr = row[0]
            driver_metadata[abbr] = dict(zip(columns, row[1:]))
            sorted_drivers.append(abbr)

        return driver_metadata, sorted_drivers

    except Exception as e:
        print(f"Error fetching results from db: {e}")
        return {}, []


def get_driver_lap_positions(db_path):
    conn   = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT Abbreviation, GridPosition
        FROM results
        WHERE GridPosition IS NOT NULL
    """)
    grid_positions = {abbr: int(float(grid)) for abbr, grid in cursor.fetchall()
                      if grid is not None and int(float(grid)) > 0}

    cursor.execute("""
        SELECT Driver, LapNumber, Position
        FROM laps
        WHERE Position IS NOT NULL
        ORDER BY Driver, LapNumber ASC
    """)
    rows = cursor.fetchall()
    conn.close()

    driver_lap_map = {}
    for abbr, lap, position in rows:
        if abbr not in driver_lap_map:
            driver_lap_map[abbr] = {}
        driver_lap_map[abbr][int(float(lap))] = int(float(position))

    driver_lap_positions = {}
    for abbr, grid in grid_positions.items():
        positions = [grid]
        lap_data  = driver_lap_map.get(abbr, {})

        if not lap_data:
            continue

        max_driver_lap = max(lap_data.keys())

        for lap in range(1, max_driver_lap + 1):
            pos = lap_data.get(lap)
            if pos is not None:
                positions.append(pos)
            else:
                positions.append(positions[-1])

        driver_lap_positions[abbr] = positions

    return driver_lap_positions


def get_tyre_data(db_path, abbr, current_lap):
    """Returns (compound, tyre_life) for a given driver and lap."""
    compound  = "N/A"
    tyre_life = 0

    if not os.path.exists(db_path):
        return compound, tyre_life

    try:
        conn   = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT Compound, TyreLife FROM laps WHERE Driver = ? AND LapNumber = ?",
            (abbr, current_lap)
        )
        row = cursor.fetchone()
        conn.close()

        if row:
            compound  = row[0] if row[0] is not None else "N/A"
            tyre_life = int(row[1]) if row[1] is not None else 0

    except Exception as e:
        print(f"Error fetching tyre data for {abbr} on Lap {current_lap}: {e}")

    return compound, tyre_life


def get_driver_telemetry(db_path, abbr, current_frame, current_lap):
    hist_speed    = None
    hist_brake    = None
    hist_throttle = None
    hist_rpm      = None
    hist_gear     = None
    max_lap_rows  = 1000

    if not os.path.exists(db_path):
        return hist_speed, hist_brake, hist_throttle, hist_rpm, hist_gear, max_lap_rows

    try:
        table_name = f"telemetry_{abbr.lower()}"
        conn       = sqlite3.connect(db_path)
        cursor     = conn.cursor()

        cursor.execute(f"SELECT MIN(rowid) FROM {table_name} WHERE lap_number = ?", (current_lap,))
        lap_start_row = cursor.fetchone()[0]

        if lap_start_row is not None:
            relative_lap_frame = max(1, current_frame - lap_start_row + 1)

            cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE lap_number = ?", (current_lap,))
            max_lap_rows = max(2, cursor.fetchone()[0])

            cursor.execute(f"""
                SELECT speed, brake, throttle, rpm, ngear FROM {table_name}
                WHERE lap_number = ?
                ORDER BY rowid ASC
                LIMIT ?
            """, (current_lap, relative_lap_frame))
            rows = cursor.fetchall()

            if rows:
                hist_speed    = np.array([r[0] for r in rows if r[0] is not None])
                hist_brake    = np.array([r[1] for r in rows if r[1] is not None])
                hist_throttle = np.array([r[2] for r in rows if r[2] is not None])
                hist_rpm      = np.array([r[3] for r in rows if r[3] is not None])
                hist_gear     = np.array([r[4] for r in rows if r[4] is not None])

        conn.close()

    except Exception as e:
        print(f"Error reading live lap telemetry streams for {abbr}: {e}")

    return hist_speed, hist_brake, hist_throttle, hist_rpm, hist_gear, max_lap_rows


def get_sector_times(db_path, abbr, current_lap):
    """Returns (s1, s2, s3) sector times for the given driver and lap number."""
    if not os.path.exists(db_path):
        return None, None, None

    try:
        conn   = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT Sector1Time, Sector2Time, Sector3Time
            FROM laps
            WHERE Driver = ? AND LapNumber = ?
        """, (abbr, int(current_lap)))

        row = cursor.fetchone()
        conn.close()

        if row:
            s1 = row[0] if row[0] is not None else None
            s2 = row[1] if row[1] is not None else None
            s3 = row[2] if row[2] is not None else None
            return s1, s2, s3

        return None, None, None

    except Exception as e:
        print(f"Error fetching sector times for {abbr} lap {current_lap}: {e}")
        return None, None, None