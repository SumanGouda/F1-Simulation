import os
import math
import arcade 
import sqlite3
import numpy as np

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

def draw_leaderboard(sorted_drivers, driver_metadata, car_colors, screen_height):
    leaderboard_center_x    = 15 + (170/2)
    leaderboard_top_y       = screen_height - 120

    box_width           = 170
    box_height          = 24
    row_spacing         = 28
    border_thickness    = 2.5

    text_left_x         = leaderboard_center_x - 75
    text_right_x        = leaderboard_center_x + 75

    hitboxes = []

    for i, abbr in enumerate(sorted_drivers):
        meta    = driver_metadata.get(abbr, {})
        color   = car_colors.get(abbr, arcade.color.GRAY)
        row_y   = leaderboard_top_y - (i * row_spacing)

        # Border (team color)
        arcade.draw_rect_filled(
            arcade.rect.XYWH(leaderboard_center_x, row_y, box_width, box_height),color
        )
        # Inner fill (black)
        arcade.draw_rect_filled(
            arcade.rect.XYWH(
                leaderboard_center_x, row_y, box_width - border_thickness, box_height - border_thickness
            ), arcade.color.BLACK
        )

        # Gap calculation
        if i == 0:
            gap_display = "INTERVAL"
        else:
            ahead_abbr      = sorted_drivers[i - 1]
            ahead_meta      = driver_metadata.get(ahead_abbr, {})
            dist_now        = meta.get('total_distance', 0.0)
            dist_ahead      = ahead_meta.get('total_distance', 0.0)
            gap_meters      = dist_ahead - dist_now
            speed_kmh       = meta.get('speed', 0.1)
            speed_ms        = max(speed_kmh / 3.6, 0.5)
            gap_seconds     = gap_meters / speed_ms
            gap_display     = f"+{max(0, gap_seconds):.1f}s"

        arcade.draw_text(
            f"{i+1}  {abbr}", text_left_x, row_y,
            arcade.color.WHITE, 12, bold=True, anchor_y="center"
        )
        arcade.draw_text(
            gap_display, text_right_x, row_y,
            arcade.color.WHITE, 11, bold=True, anchor_x="right", anchor_y="center"
        )

        hitboxes.append({
            "left"      :       leaderboard_center_x - (box_width / 2),
            "right"     :       leaderboard_center_x + (box_width / 2),
            "bottom"    :       row_y - (box_height / 2),
            "top"       :       row_y + (box_height / 2),
            "driver"    :       abbr
        })

    return hitboxes

def draw_lap_number(sorted_drivers, driver_metadata, total_laps):
    if not sorted_drivers:
        return

    lead_abbr   = sorted_drivers[0]
    meta        = driver_metadata.get(lead_abbr, {})
    lap_number  = int(meta.get('lap_number', 1))

    text_x      = 20                   # (Increase this to move right)
    text_y      = 835                  # (Decrease this to move up)
    font_size   = 14

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
            print(
                f"❌ ERROR: Icon folder not found at {os.path.abspath(icon_path)}")
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

    box_width, box_height   = 260, 140
    padding                 = 20
    center_x                = screen_width - (box_width / 2) - padding
    center_y                = screen_height - (box_height / 2) - padding - 40

    right_align             = center_x + (box_width / 2) - 15
    title_left              = center_x - (box_width / 2) + 15

    top_y_text              = center_y + (box_height / 2) - 15
    icon_size               = 16
    font_size               = 13

    row1_y                  = top_y_text - 25    # Air Temp (Closer to title)
    row2_y                  = row1_y - 22        # Track Temp
    row3_y                  = row2_y - 22        # Humidity
    row4_y                  = row3_y - 22        # Wind Speed

    # Title & Status
    arcade.draw_text("SESSION WEATHER", title_left, top_y_text,
                     arcade.color.YELLOW, font_size, bold=True)

    status_text             = "DRY" if not weather_row['Rainfall'] else "RAIN"
    status_color            = arcade.color.LIGHT_GREEN if not weather_row[
        'Rainfall'] else arcade.color.SKY_BLUE
    arcade.draw_text(status_text, right_align, top_y_text,
                     status_color, font_size, anchor_x="right", bold=True)

    if draw_weather_card.icons: 
        icon_x              = right_align - (icon_size / 2)
        text_x              = right_align - icon_size - 10

        # Row 1: Air Temp
        temp                = weather_row['AirTemp']
        icon_key            = 'air_hot' if temp >= 25 else 'air_cold'
        arcade.draw_text(
            f"{temp}°C : Air Temp", 
            text_x, row1_y, arcade.color.WHITE, 
            font_size, anchor_x="right", anchor_y="center"
        )
        arcade.draw_texture_rect(draw_weather_card.icons[icon_key], 
            arcade.rect.XYWH(icon_x, row1_y, icon_size, icon_size))

        # Row 2: Track Temp
        arcade.draw_text(f"{weather_row['TrackTemp']}°C : Track Temp", text_x, row2_y,
            arcade.color.WHITE, font_size, anchor_x="right", anchor_y="center")
        arcade.draw_texture_rect(draw_weather_card.icons['track'], arcade.rect.XYWH(
            icon_x, row2_y, icon_size, icon_size))

        # Row 3: Humidity
        arcade.draw_text(f"{weather_row['Humidity']}% : Humidity", text_x, row3_y,
            arcade.color.WHITE, font_size, anchor_x="right", anchor_y="center")
        arcade.draw_texture_rect(draw_weather_card.icons['humidity'], arcade.rect.XYWH(
            icon_x, row3_y, icon_size, icon_size))

        # Row 4: Wind Speed
        arcade.draw_text(f"{weather_row['WindSpeed']} m/s : Wind Speed", text_x,
            row4_y, arcade.color.WHITE, font_size, anchor_x="right", anchor_y="center")
        arcade.draw_texture_rect(draw_weather_card.icons['wind'], arcade.rect.XYWH(
            icon_x, row4_y, icon_size, icon_size))

    else:
        arcade.draw_text(f"{weather_row['AirTemp']}°C : Air Temp",    right_align,
                         row1_y, arcade.color.WHITE, font_size, anchor_x="right")
        arcade.draw_text(f"{weather_row['TrackTemp']}°C : Track Temp",
                         right_align, row2_y, arcade.color.WHITE, font_size, anchor_x="right")
        arcade.draw_text(f"{weather_row['Humidity']}% : Humidity",    right_align,
                         row3_y, arcade.color.WHITE, font_size, anchor_x="right")
        arcade.draw_text(f"{weather_row['WindSpeed']} m/s : Wind Speed",
                         right_align, row4_y, arcade.color.WHITE, font_size, anchor_x="right")

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
