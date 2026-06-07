import arcade
import math
import os
import sqlite3
import numpy as np


def draw_leaderboard(sorted_drivers, driver_metadata, car_colors, screen_height):
    start_x, start_y = 130, screen_height - 120 
    box_width = 240
    box_height = 28
    spacing = 32
    border_thickness = 3
    
    hitboxes = []

    for i, abbr in enumerate(sorted_drivers):
        meta = driver_metadata.get(abbr, {})
        color = car_colors.get(abbr, arcade.color.GRAY)
        curr_y = start_y - (i * spacing)
        
        # Border (Team Color)
        arcade.draw_rect_filled(
            arcade.rect.XYWH(start_x, curr_y, box_width, box_height), 
            color
        )
        # Inner Fill (Solid Black)
        arcade.draw_rect_filled(
            arcade.rect.XYWH(
                start_x, curr_y, 
                box_width - border_thickness, 
                box_height - border_thickness
            ), 
            arcade.color.BLACK
        )

        # Gap Logic
        if i == 0:
            gap_display = "INTERVAL"
        else:
            ahead_abbr = sorted_drivers[i - 1]
            ahead_meta = driver_metadata.get(ahead_abbr, {})
            dist_now = meta.get('total_distance', 0.0)
            dist_ahead = ahead_meta.get('total_distance', 0.0)
            gap_meters = dist_ahead - dist_now
            speed_kmh = meta.get('speed', 0.1) 
            speed_ms = max(speed_kmh / 3.6, 0.5) 
            gap_seconds = gap_meters / speed_ms
            gap_display = f"+{max(0, gap_seconds):.1f}s"
        
        arcade.draw_text(
            f"{i+1}  {abbr}", 
            start_x - 110, curr_y, 
            arcade.color.WHITE, 12, bold=True, anchor_y="center"
        )
        arcade.draw_text(
            gap_display, 
            start_x + 110, curr_y, 
            arcade.color.WHITE, 11, bold=True, anchor_x="right", anchor_y="center"
        )
        hitboxes.append({
            "left":   start_x - (box_width / 2),
            "right":  start_x + (box_width / 2),
            "bottom": curr_y - (box_height / 2),
            "top":    curr_y + (box_height / 2),
            "driver": abbr
        })
        
    return hitboxes


def draw_lap_number(sorted_drivers, driver_metadata, screen_width, screen_height, total_laps): 
    start_x = screen_width - 80
    start_y = screen_height - 75
    
    box_width = 80
    box_height = 50  
    border_thickness = 3
    
    if not sorted_drivers:
        return
        
    lead_abbr = sorted_drivers[0]
    meta = driver_metadata.get(lead_abbr, {}) 
    lap_number = int(meta.get('lap_number', 1))
    
    arcade.draw_rect_filled(
        arcade.rect.XYWH(start_x, start_y, box_width, box_height), 
        arcade.color.WHITE
    )
    arcade.draw_rect_filled(
        arcade.rect.XYWH(
            start_x, start_y, 
            box_width - border_thickness, 
            box_height - border_thickness
        ), 
        arcade.color.BLACK
    )

    arcade.draw_text(
        f"{lap_number} / {total_laps}\nLAPS", 
        start_x, 
        start_y, 
        arcade.color.WHITE, 
        14, 
        bold=True, 
        anchor_x="center", 
        anchor_y="center",
        multiline=True,       
        width=box_width,     
        align="center"     
    )

 
def draw_corners(corner_data, rotation, track_scale, offset_x, offset_y):
    """Renders corner markers and labels slightly offset from the track line."""
    if not corner_data:
        return

    rad = math.radians(rotation)
    cos_val = math.cos(rad)
    sin_val = math.sin(rad)
    push_distance = 15 

    for corner in corner_data:
        raw_x = corner['x']
        raw_y = corner['y']
        
        rx = raw_x * cos_val - raw_y * sin_val
        ry = raw_x * sin_val + raw_y * cos_val
        
        fx = (rx * track_scale) + offset_x
        fy = (ry * track_scale) + offset_y

        angle_rad = math.radians(corner.get('angle', 0) + rotation)
        fx += math.cos(angle_rad) * push_distance
        fy += math.sin(angle_rad) * push_distance
        
        arcade.draw_circle_filled(fx, fy, 3, arcade.color.YELLOW)
        
        label = corner['number']
        arcade.draw_text(
            label, 
            fx, 
            fy + 8,
            arcade.color.WHITE, 
            9, 
            bold=True, 
            anchor_x="center",
            font_name="Kenney Future"
        )


def draw_weather_card(weather_row, screen_width, screen_height):
    if weather_row is None:
        return

    if not hasattr(draw_weather_card, "icons"):
        icon_path = "assets/images"
        if not os.path.exists(icon_path):
            print(f"❌ ERROR: Icon folder not found at {os.path.abspath(icon_path)}")
            draw_weather_card.icons = None
        else:
            try:
                draw_weather_card.icons = {
                    'air_hot':  arcade.load_texture(os.path.join(icon_path, "air_hot.png")),
                    'air_cold': arcade.load_texture(os.path.join(icon_path, "air_cold.png")),
                    'track':    arcade.load_texture(os.path.join(icon_path, "track_temp.png")),
                    'humidity': arcade.load_texture(os.path.join(icon_path, "humidity.png")),
                    'wind':     arcade.load_texture(os.path.join(icon_path, "wind.png"))
                }
                print("✅ Weather icons loaded successfully.")
            except Exception as e:
                print(f"❌ ERROR: Failed to load icons: {e}")
                draw_weather_card.icons = None

    box_width, box_height = 260, 110
    padding = 20 
    center_x = screen_width - (box_width / 2) - padding
    center_y = screen_height - (box_height / 2) - padding - 100

    left_align = center_x - (box_width / 2) + 15
    mid_point  = center_x + (box_width / 2) - 85 
    
    top_y_text = center_y + (box_height / 2) - 20
    row1_y = center_y + 5    
    row2_y = center_y - 25   
    icon_size = 16      
    font_size = 13

    arcade.draw_text("SESSION WEATHER", left_align, top_y_text, arcade.color.YELLOW, font_size, bold=True)
    
    status_text  = "DRY" if not weather_row['Rainfall'] else "RAIN"
    status_color = arcade.color.LIGHT_GREEN if not weather_row['Rainfall'] else arcade.color.SKY_BLUE
    arcade.draw_text(status_text, center_x + (box_width / 2) - 45, top_y_text, status_color, font_size, bold=True)

    if draw_weather_card.icons:
        temp = weather_row['AirTemp'] 
        icon_key = 'air_hot' if temp >= 25 else 'air_cold'
        arcade.draw_texture_rect(draw_weather_card.icons[icon_key],
            arcade.rect.XYWH(left_align + 7, row1_y, icon_size, icon_size))
        arcade.draw_text(f"{temp}°C", left_align + 28, row1_y, arcade.color.WHITE, font_size, anchor_y="center")

        arcade.draw_texture_rect(draw_weather_card.icons['track'],
            arcade.rect.XYWH(mid_point + 7, row1_y, icon_size, icon_size))
        arcade.draw_text(f"{weather_row['TrackTemp']}°C", mid_point + 28, row1_y, arcade.color.WHITE, font_size, anchor_y="center")
        
        arcade.draw_texture_rect(draw_weather_card.icons['humidity'],
            arcade.rect.XYWH(left_align + 7, row2_y, icon_size, icon_size))
        arcade.draw_text(f"{weather_row['Humidity']}%", left_align + 28, row2_y, arcade.color.WHITE, font_size, anchor_y="center")
 
        arcade.draw_texture_rect(draw_weather_card.icons['wind'],
            arcade.rect.XYWH(mid_point + 7, row2_y, icon_size, icon_size))
        arcade.draw_text(f"{weather_row['WindSpeed']}m/s", mid_point + 28, row2_y, arcade.color.WHITE, font_size, anchor_y="center")
        
    else: 
        arcade.draw_text(f"Air: {weather_row['AirTemp']}°C",    left_align, row1_y, arcade.color.WHITE, font_size)
        arcade.draw_text(f"Trk: {weather_row['TrackTemp']}°C",  mid_point,  row1_y, arcade.color.WHITE, font_size)
        arcade.draw_text(f"Hum: {weather_row['Humidity']}%",    left_align, row2_y, arcade.color.WHITE, font_size)
        arcade.draw_text(f"Wnd: {weather_row['WindSpeed']}m/s", mid_point,  row2_y, arcade.color.WHITE, font_size)


def draw_track(fx, fy, drv, current_lap, db_root, scale=1.0):
    if fx is None or fy is None:
        return 
    
    track_points = np.column_stack((fx, fy))

    if scale != 1.0:
        cx = sum(p[0] for p in track_points) / len(track_points)
        cy = sum(p[1] for p in track_points) / len(track_points)
        track_points = [
            (cx + (p[0] - cx) * scale, cy + (p[1] - cy) * scale)
            for p in track_points
        ]
 
    db_path = db_root 
    
    if not hasattr(draw_track, "current_status"):
        draw_track.current_status = "1"
        draw_track.last_checked_lap = -1

    if current_lap != draw_track.last_checked_lap:
        try:
            leader = drv[0]
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor() 
            query = "SELECT TrackStatus FROM laps WHERE Driver = ? AND LapNumber = ?"
            cursor.execute(query, (leader, current_lap))
            result = cursor.fetchone()
            if result:
                draw_track.current_status = str(result[0])
                draw_track.last_checked_lap = current_lap
            conn.close()
        except Exception as e:
            print(f"Database injection error in draw_track: {e}")

    status_colors = {
        '1': arcade.color.WHITE,
        '2': arcade.color.YELLOW,
        '4': arcade.color.ORANGE,
        '5': arcade.color.DARK_RED,
        '6': arcade.color.VIVID_VIOLET,
        '7': arcade.color.RED
    }
    priority_order = ['5', '4', '6', '7', '2', '1']

    color = arcade.color.ASH_GREY
    for code in priority_order:
        if code in draw_track.current_status:
            color = status_colors[code]
            break

    arcade.draw_line_strip(track_points, color, 6)
    arcade.draw_line_strip(track_points, arcade.color.BLACK, 3)


def draw_focused_driver_telemetry(app, leader_lap, get_screen_coords, draw_track, draw_tel, box_geometry=(50, 160, 900, 500)):
    """
    Renders the focused car view, track layout, and queries/draws real-time 
    telemetry charts for the selected driver inside a customizable bounding box.
    """
    abbr = app.selected_driver
    pos = app.current_car_positions.get(abbr)
    
    if pos is not None and pos != (0, 0): 
        active_scale = app.track_scale_focused 

        fx, fy = get_screen_coords(
            pos[0], pos[1],
            app.rotation, active_scale, app.foc_offset_x, app.foc_offset_y
        )
        color = app.car_colors.get(abbr, arcade.color.GRAY)
        
        try: 
            rank = app.sorted_drivers.index(abbr) + 1
            rank_text = f"P{rank}"
        except ValueError:
            rank_text = "P??"
         
        arcade.draw_circle_filled(fx, fy, 10, color)  
        arcade.draw_circle_outline(fx, fy, 13, arcade.color.WHITE, 2) 
        arcade.draw_text(f"{abbr} [{rank_text}]", fx + 18, fy, arcade.color.WHITE, 12, bold=True, anchor_y="center")
             
        if app.raw_x is not None and app.raw_y is not None:
            track_fx, track_fy = get_screen_coords(
                app.raw_x, app.raw_y,
                app.rotation, active_scale, app.foc_offset_x, app.foc_offset_y
            ) 
            draw_track(track_fx, track_fy, app.sorted_drivers, leader_lap, app.db_path, scale=1.0)

        db_file = app.db_path
        hist_speed    = None
        hist_brake    = None
        hist_throttle = None
        hist_rpm      = None
        max_lap_rows  = 1000 
        
        if os.path.exists(db_file):
            try:
                current_frame = app.driver_row_counters.get(abbr, 0)
                current_lap   = app.driver_metadata[abbr].get('lap_number', 1)
                table_name    = f"telemetry_{abbr.lower()}"
                
                conn = sqlite3.connect(db_file)
                cursor = conn.cursor()
                
                cursor.execute(f"SELECT MIN(rowid) FROM {table_name} WHERE lap_number = ?", (current_lap,))
                lap_start_row = cursor.fetchone()[0]
                
                if lap_start_row is not None:
                    relative_lap_frame = max(1, current_frame - lap_start_row + 1)
                    
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE lap_number = ?", (current_lap,))
                    max_lap_rows = max(2, cursor.fetchone()[0])
                    
                    query = f"""
                        SELECT speed, brake, throttle, rpm FROM {table_name} 
                        WHERE lap_number = ? 
                        ORDER BY rowid ASC 
                        LIMIT ?
                    """
                    cursor.execute(query, (current_lap, relative_lap_frame))
                    rows = cursor.fetchall()
                    
                    if rows:
                        hist_speed    = np.array([r[0] for r in rows if r[0] is not None])
                        hist_brake    = np.array([r[1] for r in rows if r[1] is not None])
                        hist_throttle = np.array([r[2] for r in rows if r[2] is not None])
                        hist_rpm      = np.array([r[3] for r in rows if r[3] is not None])
                        
                conn.close()
            except Exception as e:
                print(f"Error reading live lap telemetry streams for {abbr}: {e}")

        box_x, box_y, box_w, box_h = box_geometry

        center_x = box_x + (box_w / 2)
        center_y = box_y + (box_h / 2)
        
        arcade.draw_rect_filled(arcade.XYWH(center_x, center_y, box_w, box_h), arcade.color.BLACK)
        arcade.draw_rect_outline(arcade.XYWH(center_x, center_y, box_w, box_h), arcade.color.DARK_GRAY, border_width=2)

        legend_y = box_y + box_h + 15
        arcade.draw_text("LIVE TELEMETRY PANEL:", box_x, legend_y, arcade.color.WHITE, 12, bold=True)
        
        arcade.draw_text("■ SPEED",    box_x + 230, legend_y, color,                              11, bold=True)
        arcade.draw_text("■ RPM",      box_x + 340, legend_y, arcade.color.LIGHT_GOLDENROD_YELLOW, 11, bold=True)
        arcade.draw_text("■ THROTTLE", box_x + 430, legend_y, arcade.color.GREEN,                  11, bold=True)
        arcade.draw_text("■ BRAKE",    box_x + 550, legend_y, arcade.color.RED,                    11, bold=True)

        max_t = 100.0 if (hist_throttle is not None and len(hist_throttle) > 0 and max(hist_throttle) > 1.1) else 1.0
        max_b = 100.0 if (hist_brake    is not None and len(hist_brake)    > 0 and max(hist_brake)    > 1.1) else 1.0

        solo_datasets = [
            {"data": hist_speed, "max": 380.0,   "color": color},
            {"data": hist_rpm,   "max": 13000.0, "color": arcade.color.LIGHT_GOLDENROD_YELLOW},
        ]

        section_h      = (box_h - 20) / 3   # 3 sections : speed, rpm, throttle+brake
        plot_left_pad  = 60
        plot_right_pad = 20

        for i, target in enumerate(solo_datasets):
            if target["data"] is not None and len(target["data"]) >= 2:
                section_y = box_y + ((i + 1) * section_h) + 5 
                draw_tel(
                    telemetry_data=target["data"],
                    max_rows=max_lap_rows,
                    origin_x=box_x + plot_left_pad,
                    origin_y=section_y,
                    plot_width=box_w - plot_left_pad - plot_right_pad,
                    plot_height=section_h - 15,
                    color=target["color"],
                    title="",
                    max_val=target["max"]
                )
 
        overlay_section_y = box_y + (0 * section_h) + 20
        for data, col, mx in [
            (hist_throttle, arcade.color.GREEN, max_t),
            (hist_brake,    arcade.color.RED,   max_b),
        ]:
            if data is not None and len(data) >= 2:
                draw_tel(
                    telemetry_data=data,
                    max_rows=max_lap_rows,
                    origin_x=box_x + plot_left_pad,
                    origin_y=overlay_section_y,
                    plot_width=box_w - plot_left_pad - plot_right_pad,
                    plot_height=section_h - 15,
                    color=col,
                    title="",
                    max_val=mx
                )

                                        
def draw_tel(telemetry_data, max_rows, origin_x, origin_y, plot_width, plot_height, color, title="SPEED", max_val=350.0):
    """
    Draws a telemetry line chart directly onto the Arcade window with a centered
    top heading and min, mid, and max Y-axis value indicators.
    """
    if telemetry_data is None or len(telemetry_data) < 2:
        return
          
    indices  = np.arange(len(telemetry_data))
    screen_x = origin_x + (indices / (max_rows - 1)) * plot_width
    screen_y = origin_y + (telemetry_data / max_val) * plot_height 
    
    chart_points = np.column_stack((screen_x, screen_y))
       
    arcade.draw_text(title, origin_x + (plot_width / 2), origin_y + plot_height + 12,
                     arcade.color.WHITE, font_size=10, bold=True, anchor_x="center", anchor_y="center")
    arcade.draw_text(f"{int(max_val)}",     origin_x - 5, origin_y + plot_height,        arcade.color.ASH_GREY, font_size=10, anchor_x="right", anchor_y="center")
    arcade.draw_text(f"{int(max_val / 2)}", origin_x - 5, origin_y + (plot_height / 2),  arcade.color.ASH_GREY, font_size=10, anchor_x="right", anchor_y="center")
    arcade.draw_text("0",                   origin_x - 5, origin_y,                       arcade.color.ASH_GREY, font_size=10, anchor_x="right", anchor_y="center")
    arcade.draw_line_strip(chart_points, color, 2)