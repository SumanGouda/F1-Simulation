import arcade
import math
import os
import sqlite3
import numpy as np
from utils.helpers import get_driver_telemetry

def draw_leaderboard(sorted_drivers, driver_metadata, car_colors, screen_height):
    leaderboard_center_x = 15 + (170/2)
    leaderboard_top_y    = screen_height - 120

    box_width        = 170
    box_height       = 24
    row_spacing      = 28
    border_thickness = 2.5

    text_left_x  = leaderboard_center_x - 75
    text_right_x = leaderboard_center_x + 75

    hitboxes = []

    for i, abbr in enumerate(sorted_drivers):
        meta  = driver_metadata.get(abbr, {})
        color = car_colors.get(abbr, arcade.color.GRAY)
        row_y = leaderboard_top_y - (i * row_spacing)

        # Border (team color)
        arcade.draw_rect_filled(
            arcade.rect.XYWH(leaderboard_center_x, row_y, box_width, box_height),
            color
        )
        # Inner fill (black)
        arcade.draw_rect_filled(
            arcade.rect.XYWH(
                leaderboard_center_x, row_y,
                box_width - border_thickness,
                box_height - border_thickness
            ),
            arcade.color.BLACK
        )

        # Gap calculation
        if i == 0:
            gap_display = "INTERVAL"
        else:
            ahead_abbr    = sorted_drivers[i - 1]
            ahead_meta    = driver_metadata.get(ahead_abbr, {})
            dist_now      = meta.get('total_distance', 0.0)
            dist_ahead    = ahead_meta.get('total_distance', 0.0)
            gap_meters    = dist_ahead - dist_now
            speed_kmh     = meta.get('speed', 0.1)
            speed_ms      = max(speed_kmh / 3.6, 0.5)
            gap_seconds   = gap_meters / speed_ms
            gap_display   = f"+{max(0, gap_seconds):.1f}s"

        arcade.draw_text(
            f"{i+1}  {abbr}",
            text_left_x, row_y,
            arcade.color.WHITE, 12, bold=True, anchor_y="center"
        )
        arcade.draw_text(
            gap_display,
            text_right_x, row_y,
            arcade.color.WHITE, 11, bold=True, anchor_x="right", anchor_y="center"
        )

        hitboxes.append({
            "left":   leaderboard_center_x - (box_width / 2),
            "right":  leaderboard_center_x + (box_width / 2),
            "bottom": row_y - (box_height / 2),
            "top":    row_y + (box_height / 2),
            "driver": abbr
        })

    return hitboxes

def draw_lap_number(sorted_drivers, driver_metadata, screen_height, screen_width, total_laps): 
    if not sorted_drivers:
        return
         
    lead_abbr = sorted_drivers[0]
    meta = driver_metadata.get(lead_abbr, {}) 
    lap_number = int(meta.get('lap_number', 1))
     
    text_x = screen_width - (screen_width - 20)  # (Increase this to move right)
    text_y = screen_height - 80     # (Increase this to move up)
    font_size = 14

    arcade.draw_text(
        f"LAP : {lap_number} / {total_laps}", text_x, text_y, arcade.color.WHITE, 
        font_size=font_size, bold=True, anchor_x="left", anchor_y="center"
    )

def draw_corners(corner_data, rotation, scale, offset_x, offset_y):
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
        
        fx = (rx * scale) + offset_x
        fy = (ry * scale) + offset_y

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

    box_width, box_height = 260, 140
    padding = 20 
    center_x = screen_width - (box_width / 2) - padding
    center_y = screen_height - (box_height / 2) - padding - 40

    right_align = center_x + (box_width / 2) - 15
    title_left = center_x - (box_width / 2) + 15
    
    top_y_text = center_y + (box_height / 2) - 15
    icon_size = 16      
    font_size = 13 

    row1_y = top_y_text - 25    # Air Temp (Closer to title)
    row2_y = row1_y - 22        # Track Temp
    row3_y = row2_y - 22        # Humidity
    row4_y = row3_y - 22        # Wind Speed   

    # Title & Status 
    arcade.draw_text("SESSION WEATHER", title_left, top_y_text, arcade.color.YELLOW, font_size, bold=True)
    
    status_text  = "DRY" if not weather_row['Rainfall'] else "RAIN"
    status_color = arcade.color.LIGHT_GREEN if not weather_row['Rainfall'] else arcade.color.SKY_BLUE
    arcade.draw_text(status_text, right_align, top_y_text, status_color, font_size, anchor_x="right", bold=True)

    if draw_weather_card.icons:
        # Define the absolute right-most X position for the icons
        icon_x = right_align - (icon_size / 2) 
        text_x = right_align - icon_size - 10

        # Row 1: Air Temp
        temp = weather_row['AirTemp'] 
        icon_key = 'air_hot' if temp >= 25 else 'air_cold'
        arcade.draw_text(f"{temp}°C : Air Temp", text_x, row1_y, arcade.color.WHITE, font_size, anchor_x="right", anchor_y="center")
        arcade.draw_texture_rect(draw_weather_card.icons[icon_key], arcade.rect.XYWH(icon_x, row1_y, icon_size, icon_size))

        # Row 2: Track Temp
        arcade.draw_text(f"{weather_row['TrackTemp']}°C : Track Temp", text_x, row2_y, arcade.color.WHITE, font_size, anchor_x="right", anchor_y="center")
        arcade.draw_texture_rect(draw_weather_card.icons['track'], arcade.rect.XYWH(icon_x, row2_y, icon_size, icon_size))
        
        # Row 3: Humidity
        arcade.draw_text(f"{weather_row['Humidity']}% : Humidity", text_x, row3_y, arcade.color.WHITE, font_size, anchor_x="right", anchor_y="center")
        arcade.draw_texture_rect(draw_weather_card.icons['humidity'], arcade.rect.XYWH(icon_x, row3_y, icon_size, icon_size))
 
        # Row 4: Wind Speed
        arcade.draw_text(f"{weather_row['WindSpeed']} m/s : Wind Speed", text_x, row4_y, arcade.color.WHITE, font_size, anchor_x="right", anchor_y="center")
        arcade.draw_texture_rect(draw_weather_card.icons['wind'], arcade.rect.XYWH(icon_x, row4_y, icon_size, icon_size))
        
    else: 
        arcade.draw_text(f"{weather_row['AirTemp']}°C : Air Temp",    right_align, row1_y, arcade.color.WHITE, font_size, anchor_x="right")
        arcade.draw_text(f"{weather_row['TrackTemp']}°C : Track Temp",  right_align, row2_y, arcade.color.WHITE, font_size, anchor_x="right")
        arcade.draw_text(f"{weather_row['Humidity']}% : Humidity",    right_align, row3_y, arcade.color.WHITE, font_size, anchor_x="right")
        arcade.draw_text(f"{weather_row['WindSpeed']} m/s : Wind Speed", right_align, row4_y, arcade.color.WHITE, font_size, anchor_x="right")

def draw_track(fx, fy, drv, current_lap, db_root):
    if fx is None or fy is None:
        return 
    
    track_points = np.column_stack((fx, fy))
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

    arcade.draw_line_strip(track_points, color, 12)
    arcade.draw_line_strip(track_points, arcade.color.BLACK, 9)

def draw_focused_driver_telemetry(app, leader_lap, get_screen_coords, draw_track, draw_tel, box_geometry=(50, 160, 900, 500)):
    abbr = app.selected_driver
    pos = app.current_car_positions.get(abbr)
    
    if pos is not None and pos != (0, 0): 
        active_scale = app.track_scale_focused 

        fx, fy = get_screen_coords(
            pos[0], pos[1], app.rotation, active_scale, app.foc_offset_x, app.foc_offset_y
        )
        color = app.car_colors.get(abbr, arcade.color.GRAY)
        
        try: 
            rank = app.sorted_drivers.index(abbr) + 1
            rank_text = f"P{rank}"
        except ValueError:
            rank_text = "P??"
        
        if app.raw_x is not None and app.raw_y is not None:
            track_fx, track_fy = get_screen_coords(
                app.raw_x, app.raw_y, app.rotation, active_scale, app.foc_offset_x, app.foc_offset_y
            ) 
            draw_track(track_fx, track_fy, app.sorted_drivers, leader_lap, app.db_path)

        arcade.draw_circle_filled(fx, fy, 7, color)  
        arcade.draw_circle_outline(fx, fy, 9, arcade.color.WHITE, 2) 
        arcade.draw_text(f"{abbr} [{rank_text}]", fx + 18, fy, arcade.color.WHITE, 12, bold=True, anchor_y="center")
             
        # LIVE TELEMETRY EXTRACTION   
        current_frame = app.driver_row_counters.get(abbr, 0)
        current_lap   = app.driver_metadata[abbr].get('lap_number', 1)
        
        (hist_speed, hist_brake, hist_throttle, hist_rpm, hist_gear, max_lap_rows) = get_driver_telemetry(
            db_file=app.db_path, abbr=abbr, current_frame=current_frame, current_lap=current_lap
        )           # Do not remove the hist_gear variable

        box_x, box_y, box_w, box_h = box_geometry
        center_x, center_y = box_x + (box_w / 2), box_y + (box_h / 2)
        
        arcade.draw_rect_filled(arcade.XYWH(center_x, center_y, box_w, box_h), arcade.color.BLACK)
        arcade.draw_rect_outline(arcade.XYWH(center_x, center_y, box_w, box_h), arcade.color.DARK_GRAY, border_width=2)

        legend_y = box_y + box_h + 15
        arcade.draw_text("LIVE TELEMETRY PANEL:", box_x, legend_y, arcade.color.WHITE, 12, bold=True)
        
        arcade.draw_text("■ SPEED",    box_x + 230, legend_y, color,                               11, bold=True)
        arcade.draw_text("■ RPM",      box_x + 340, legend_y, arcade.color.LIGHT_GOLDENROD_YELLOW, 11, bold=True)
        arcade.draw_text("■ THROTTLE", box_x + 430, legend_y, arcade.color.GREEN,                  11, bold=True)
        arcade.draw_text("■ BRAKE",    box_x + 550, legend_y, arcade.color.RED,                    11, bold=True)

        max_t = 100.0 if (hist_throttle is not None and len(hist_throttle) > 0 and max(hist_throttle) > 1.1) else 1.0
        max_b = 100.0 if (hist_brake     is not None and len(hist_brake)    > 0 and max(hist_brake)    > 1.1) else 1.0

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
                    telemetry_data=target["data"], max_rows=max_lap_rows, origin_x=box_x + plot_left_pad, origin_y=section_y, 
                    plot_width=box_w - plot_left_pad - plot_right_pad, plot_height=section_h - 15, color=target["color"], title="", max_val=target["max"]
                )
 
        overlay_section_y = box_y + (0 * section_h) + 20
        for data, col, mx in [
            (hist_throttle, arcade.color.GREEN, max_t),
            (hist_brake,    arcade.color.RED,   max_b),
        ]:
            if data is not None and len(data) >= 2:
                draw_tel(
                    telemetry_data=data, max_rows=max_lap_rows, origin_x=box_x + plot_left_pad, origin_y=overlay_section_y,
                    plot_width=box_w - plot_left_pad - plot_right_pad, plot_height=section_h - 15, color=col, title="", max_val=mx
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

def draw_tab_bar(start_x, base_y, pad, tabs, tab_w, tab_h):
    if not tabs:
        return {} 
       
    f1_red = (225, 6, 0) 

    tab_hitboxes = {}
    for i, label in enumerate(tabs): 
        x = start_x + (i * (tab_w + pad)) + (tab_w / 2)
        y = base_y
          
        arcade.draw_lbwh_rectangle_filled(
            left=x - tab_w / 2, bottom=y - tab_h / 2, width=tab_w, height=tab_h, color=f1_red
        ) 
        arcade.draw_text(
            text=label, x=x, y=y, color=arcade.color.WHITE, font_size=12, bold=True, anchor_x="center", anchor_y="center"
        )
        tab_hitboxes[label] = {
            "left": x - tab_w / 2,
            "right": x + tab_w / 2,
            "bottom": y - tab_h / 2,
            "top": y + tab_h / 2
        }
        
    return tab_hitboxes

def draw_h2h_selection_panel(self, screen_height, screen_width):
    panel_x, panel_y = screen_width - (screen_width - 20), screen_height - (screen_height - 150)
    panel_w, panel_h, row_h, spacing = 100, 600, 24, 28 

    # Background
    arcade.draw_rect_filled(
        arcade.rect.XYWH(panel_x + panel_w/2, panel_y + panel_h/2, panel_w, panel_h), (20, 20, 20)
    )
    arcade.draw_text("MAX : 3", panel_x, panel_y + panel_h + 15, arcade.color.WHITE, 13, bold=True, anchor_x="left")

    self.h2h_panel_hitboxes = {}
    for i, abbr in enumerate(self.initial_drivers):
        row_y     = panel_y + panel_h - (i * spacing) - 20
        is_selected = abbr in self.h2h_selected
        color     = self.car_colors.get(abbr, arcade.color.GRAY)
        bg_color  = (40, 40, 40) if not is_selected else color

        arcade.draw_rect_filled(arcade.rect.XYWH(panel_x + panel_w/2, row_y, panel_w - 20, row_h), bg_color)
        arcade.draw_text(abbr, panel_x + 20, row_y, arcade.color.WHITE, 11, bold=True, anchor_y="center")

        self.h2h_panel_hitboxes[abbr] = {
            "left": panel_x, "right": panel_x + panel_w, "bottom": row_y - row_h/2, "top": row_y + row_h/2
        }

    # Compare button
    if len(self.h2h_selected) >= 2:
        btn_x, btn_y = panel_x + panel_w/2, panel_y - 25
        btn_width = panel_w
        btn_height = 35
        arcade.draw_rect_filled(
            arcade.rect.XYWH(btn_x, btn_y, btn_width, btn_height), arcade.color.DARK_RED
        )
        arcade.draw_text(
            "COMPARE ▶", btn_x, btn_y, arcade.color.WHITE, 12, bold=True, anchor_x="center", anchor_y="center"
        )
        self.h2h_compare_btn = {
            "left": panel_x, "right": panel_x + panel_w, "bottom": btn_y - btn_height / 2, "top": btn_y + btn_height / 2
        }
    else:
        self.h2h_compare_btn = {}

def draw_data_card(app, drv_list, db_path, screen_width, screen_height):
    """
    Renders side-by-side transparent cards for however many drivers are selected,
    keeping them perfectly dynamically centered at the bottom of the screen.
    """
    num_selected = len(drv_list)
    if num_selected == 0 or not os.path.exists(db_path):
        return
 
    card_w = 300          
    card_h = 110          
    card_spacing = 20     
    y_cor = 85           
  
    total_cards_width = (num_selected * card_w) + ((num_selected - 1) * card_spacing)
    x_cor = (screen_width - total_cards_width) / 2         

    for i, drv in enumerate(drv_list): 
        current_x = x_cor + i * (card_w + card_spacing)
        
        current_frame = app.driver_row_counters.get(drv, 0)
        current_lap   = app.driver_metadata[drv].get('lap_number', 1)
        
        (hist_speed, hist_brake, hist_throttle, hist_rpm, hist_gear, max_lap_rows) = get_driver_telemetry(
            db_file=db_path, abbr=drv, current_frame=current_frame, current_lap=current_lap
        )
        
        current_speed = int(hist_speed[-1]) if (hist_speed is not None and len(hist_speed) > 0) else 0
        current_gear  = int(hist_gear[-1]) if (hist_gear is not None and len(hist_gear) > 0) else 0

        center_x = current_x + (card_w / 2)
        center_y = y_cor + (card_h / 2)
        drv_color = app.car_colors.get(drv, arcade.color.GRAY)
         
        arcade.draw_rect_outline(arcade.XYWH(center_x, center_y, card_w, card_h), drv_color, border_width=4)
         
        arcade.draw_text(drv, center_x, y_cor + card_h - 25, arcade.color.WHITE, 14, bold=True, anchor_x="center")
        
        # Current Gear (Top-Left inside the card)
        arcade.draw_text(
            f"G: {current_gear if current_gear > 0 else 'N'}", current_x + 15, y_cor + card_h - 55,  
            arcade.color.LIGHT_GOLDENROD_YELLOW, 11, bold=True, anchor_x="left"
        )
        
        # Speed value (Top-Right inside the card)
        arcade.draw_text(
            f"{current_speed} km/h",  center_x, y_cor + card_h - 55, 
            arcade.color.WHITE, 11, bold=True, anchor_x="right"
        )