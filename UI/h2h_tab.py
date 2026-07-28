import os
import arcade
from utils.helpers import get_driver_telemetry, get_tyre_data, get_sector_times

def draw_h2h_selection_panel(self):
    panel_x, panel_y = 20, 170
    panel_w, panel_h, row_h, spacing = 100, 600, 24, 28

    # Background
    arcade.draw_rect_filled(
        arcade.rect.XYWH(panel_x + panel_w/2, panel_y +
                         panel_h/2, panel_w, panel_h), (20, 20, 20)
    )
    arcade.draw_text("MAX : 3", panel_x, panel_y + panel_h +
                     15, arcade.color.WHITE, 13, bold=True, anchor_x="left")

    self.h2h_panel_hitboxes = {}
    for i, abbr in enumerate(self.initial_drivers):
        row_y = panel_y + panel_h - (i * spacing) - 20
        is_selected = abbr in self.h2h_selected
        color = self.car_colors.get(abbr, arcade.color.GRAY)
        bg_color = (40, 40, 40) if not is_selected else color

        arcade.draw_rect_filled(arcade.rect.XYWH(
            panel_x + panel_w/2, row_y, panel_w - 20, row_h), bg_color)
        arcade.draw_text(abbr, panel_x + 20, row_y,
                         arcade.color.WHITE, 11, bold=True, anchor_y="center")

        self.h2h_panel_hitboxes[abbr] = {
            "left": panel_x, "right": panel_x + panel_w, "bottom": row_y - row_h/2, "top": row_y + row_h/2
        }

    # Compare button
    if len(self.h2h_selected) >= 2:
        btn_x, btn_y = panel_x + panel_w/2, panel_y - 25
        btn_width = panel_w
        btn_height = 35
        arcade.draw_rect_filled(
            arcade.rect.XYWH(btn_x, btn_y, btn_width,
                             btn_height), arcade.color.DARK_RED
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
    num_selected    = len(drv_list)
    if num_selected == 0 or not os.path.exists(db_path):
        return

    card_w       = 300
    card_h       = 120
    card_spacing = 20
    y_cor        = 75

    total_cards_width = num_selected * card_w + (num_selected - 1) * card_spacing
    x_cor = (screen_width - total_cards_width) / 2

    # Tyre compound color and shorthand code map
    TYRE_MAP = {
        "SOFT":         ("S", arcade.color.RED),
        "MEDIUM":       ("M", arcade.color.YELLOW),
        "HARD":         ("H", arcade.color.WHITE),
        "INTERMEDIATE": ("I", arcade.color.GREEN),
        "WET":          ("W", arcade.color.AZURE),  
    }

    for i, drv in enumerate(drv_list):
        current_x       = x_cor + i * (card_w + card_spacing)
        current_frame   = app.driver_row_counters.get(drv, 0)
        current_lap     = app.driver_metadata[drv].get('lap_number', 1)

        # Telemetry Data
        (hist_speed, hist_brake, hist_throttle, hist_rpm, hist_gear, max_lap_rows) = get_driver_telemetry(
            db_path, abbr=drv, current_frame=current_frame, current_lap=current_lap
        )

        current_speed        = int(hist_speed[-1]) if (hist_speed is not None and len(hist_speed) > 0) else 0
        current_gear         = int(hist_gear[-1]) if (hist_gear is not None and len(hist_gear) > 0) else 0
        compound, tyre_life  = get_tyre_data(db_path, drv, current_lap)

        center_x    = current_x + (card_w / 2)
        center_y    = y_cor + (card_h / 2)
        drv_color   = app.car_colors.get(drv, arcade.color.GRAY)
 
        # 1. CARD CONTAINER & DRIVER HEADER 
        arcade.draw_rect_outline(arcade.XYWH(center_x, center_y, card_w, card_h), drv_color, border_width=4)
        arcade.draw_text(drv, center_x, y_cor + card_h - 22, arcade.color.WHITE, 14, bold=True, anchor_x="center")
 
        # 2. ROW 1: TEXT METRICS (GEAR, SPEED, TYRE) 
        row1_y = y_cor + card_h - 52

        # Gear (Left)
        arcade.draw_text(
            f"G: {current_gear if current_gear > 0 else 'N'}", 
            current_x + 15, row1_y, 
            arcade.color.LIGHT_GOLDENROD_YELLOW, 11, bold=True, anchor_x="left"
        )

        # Speed (Middle-Left)
        arcade.draw_text(
            f"{current_speed} km/h", 
            current_x + 85, row1_y, 
            arcade.color.WHITE, 11, bold=True, anchor_x="left"
        )

        # Tyre (Middle-Right)
        compound_key = str(compound).strip().upper() if compound else ""
        tyre_code, tyre_color = TYRE_MAP.get(compound_key, (compound_key[:1] if compound_key else "?", arcade.color.GRAY))
 
        arcade.draw_text(
            f"{tyre_code} : {tyre_life}", 
            current_x + 175, row1_y, 
            tyre_color, 11, bold=True, anchor_x="left"
        )
 
        # 3. ROW 2: HORIZONTAL RPM BAR 
        current_rpm = int(hist_rpm[-1]) if (hist_rpm is not None and len(hist_rpm) > 0) else 0
        max_rpm = 15000
        rpm_pct = min(current_rpm / max_rpm, 1.0)

        rpm_bar_w = 210
        rpm_bar_h = 8
        rpm_bar_x = current_x + 15
        rpm_bar_y = y_cor + 28

        # Background Track
        arcade.draw_rect_filled(
            arcade.rect.XYWH(rpm_bar_x + rpm_bar_w / 2, rpm_bar_y, rpm_bar_w, rpm_bar_h), (40, 40, 40)
        )

        # Fill
        filled_w = rpm_bar_w * rpm_pct
        if filled_w > 0:
            if rpm_pct < 0.5:
                bar_color = (0, 120, 255)
            elif rpm_pct < 0.7:
                bar_color = (0, 200, 255)
            elif rpm_pct < 0.85:
                bar_color = (180, 0, 255)
            else:
                bar_color = (255, 20, 20)

            arcade.draw_rect_filled(
                arcade.rect.XYWH(rpm_bar_x + filled_w / 2, rpm_bar_y, filled_w, rpm_bar_h), bar_color
            )

        # RPM Scale Labels
        arcade.draw_text("0", rpm_bar_x, rpm_bar_y - 15, arcade.color.ASH_GREY, 8, anchor_x="left")
        arcade.draw_text(f"{int(max_rpm / 1000)}", rpm_bar_x + rpm_bar_w, rpm_bar_y - 15, arcade.color.ASH_GREY, 8, anchor_x="right")
        arcade.draw_text("x1000 RPM", rpm_bar_x + (rpm_bar_w / 2), rpm_bar_y - 15, arcade.color.ASH_GREY, 8, anchor_x="center")
 
        # 4. RIGHT SIDE: VERTICAL THROTTLE & BRAKE BARS 
        current_throttle = int(hist_throttle[-1]) if (hist_throttle is not None and len(hist_throttle) > 0) else 0
        current_brake = int(hist_brake[-1]) if (hist_brake is not None and len(hist_brake) > 0) else 0

        max_t = 100.0 if current_throttle > 1 else 1.0
        max_b = 100.0 if current_brake > 1 else 1.0
        throttle_pct = min(current_throttle / max_t, 1.0)
        brake_pct    = min(current_brake / max_b, 1.0)

        v_bar_w      = 12
        v_bar_h      = 60
        v_bar_y_base = y_cor + 12

        # Throttle Bar Alignment
        throttle_x = current_x + card_w - 45
        arcade.draw_rect_filled(
            arcade.rect.XYWH(throttle_x, v_bar_y_base + v_bar_h / 2, v_bar_w, v_bar_h), (40, 40, 40)
        )
        filled_t_h = v_bar_h * throttle_pct
        if filled_t_h > 0:
            arcade.draw_rect_filled(
                arcade.rect.XYWH(throttle_x, v_bar_y_base + filled_t_h / 2, v_bar_w, filled_t_h), (0, 200, 80)
            )
        arcade.draw_text("T", throttle_x, v_bar_y_base + v_bar_h + 6, arcade.color.LIGHT_GREEN, 9, bold=True, anchor_x="center")

        # Brake Bar Alignment
        brake_x = current_x + card_w - 22
        arcade.draw_rect_filled(
            arcade.rect.XYWH(brake_x, v_bar_y_base + v_bar_h / 2, v_bar_w, v_bar_h), (40, 40, 40)
        )
        filled_b_h = v_bar_h * brake_pct
        if filled_b_h > 0:
            arcade.draw_rect_filled(
                arcade.rect.XYWH(brake_x, v_bar_y_base + filled_b_h / 2, v_bar_w, filled_b_h), (220, 30, 30)
            )
        arcade.draw_text("B", brake_x, v_bar_y_base + v_bar_h + 6, arcade.color.RED, 9, bold=True, anchor_x="center")

def draw_sector_times(app, x_cor, y_cor, drv_list, lapnumber):
    """
    Header row followed by driver cards.
    First driver shows absolute sector times (white).
    Rest show delta vs first driver (green = faster/negative, yellow = slower/positive).
    """
    if not drv_list:
        return

    # Fetch sector times for all drivers
    all_times = {}
    for drv in drv_list: 
        s1, s2, s3 = get_sector_times(app.db_path, drv, lapnumber)

        def to_f(v):
            try: return float(v)
            except: return None

        all_times[drv] = (to_f(s1), to_f(s2), to_f(s3))

    ref_s1, ref_s2, ref_s3 = all_times[drv_list[0]]

    col_widths = [60, 75, 75, 75]
    card_h = 28
    total_w = sum(col_widths)
    padding_y = 10

    def fmt(val, ref, is_ref_driver):
        if val is None:
            return "N/A", arcade.color.GRAY
        if is_ref_driver:
            return f"{val:.3f}", arcade.color.WHITE
        if ref is None:
            return "N/A", arcade.color.GRAY
        
        delta = val - ref
        color = arcade.color.LIGHT_GREEN if delta < 0 else arcade.color.YELLOW
        return f"{delta:+.3f}", color

    # -----------------------------------------------------------------
    # 1. HEADER ROW ("DRV", "S1", "S2", "S3")
    # -----------------------------------------------------------------
    header_y = y_cor
    header_center_y = header_y + (card_h / 2)

    # Background box for header
    arcade.draw_rect_filled(
        arcade.rect.XYWH(x_cor + (total_w / 2), header_center_y, total_w, card_h),
        (30, 30, 30, 240)
    )

    header_curr_x = x_cor
    header_titles = ["DRV", "S1", "S2", "S3"]
    for idx, (width, title) in enumerate(zip(col_widths, header_titles)):
        cell_center_x = header_curr_x + (width / 2)
        arcade.draw_text(
            title, cell_center_x, header_center_y,
            arcade.color.LIGHT_GRAY, 11, bold=True,
            anchor_x="center", anchor_y="center"
        )
        if idx < 3:
            arcade.draw_line(
                header_curr_x + width, header_y + 2,
                header_curr_x + width, header_y + card_h - 2,
                (70, 70, 70), 1
            )
        header_curr_x += width

    # -----------------------------------------------------------------
    # 2. DRIVER CARDS (Reference + Delta Drivers)
    # -----------------------------------------------------------------
    for idx, drv in enumerate(drv_list):
        s1, s2, s3 = all_times[drv]
        is_ref_driver = (idx == 0)

        # Shift driver cards down below header row
        card_y = header_y - (idx + 1) * (card_h + padding_y)
        center_x = x_cor + (total_w / 2)
        center_y = card_y + (card_h / 2)
        drv_color = app.car_colors.get(drv, arcade.color.GRAY)

        # Card Background & Outline
        arcade.draw_rect_filled(
            arcade.rect.XYWH(center_x, center_y, total_w, card_h), (20, 20, 20, 220)
        )
        arcade.draw_rect_outline(
            arcade.rect.XYWH(center_x, center_y, total_w, card_h), drv_color, border_width=2
        )

        # Format sector values (Absolute time for driver 1, Delta for driver 2+)
        s1_text, s1_color = fmt(s1, ref_s1, is_ref_driver)
        s2_text, s2_color = fmt(s2, ref_s2, is_ref_driver)
        s3_text, s3_color = fmt(s3, ref_s3, is_ref_driver)

        columns = [
            (drv, drv_color, arcade.color.BLACK),
            (s1_text, None, s1_color),
            (s2_text, None, s2_color),
            (s3_text, None, s3_color)
        ]

        curr_col_x = x_cor
        for c_idx, (width, (val_text, bg_col, txt_col)) in enumerate(zip(col_widths, columns)):
            cell_center_x = curr_col_x + (width / 2)

            if c_idx == 0:
                # Driver abbreviation badge with team color
                arcade.draw_rect_filled(
                    arcade.rect.XYWH(cell_center_x, center_y, width, card_h - 4), bg_col
                )
                arcade.draw_text(
                    str(val_text), cell_center_x, center_y, txt_col, 11, bold=True,
                    anchor_x="center", anchor_y="center"
                )
            else:
                # Sector value / Delta time
                arcade.draw_text(
                    str(val_text), cell_center_x, center_y, txt_col, 11, bold=True,
                    anchor_x="center", anchor_y="center"
                )
                # Vertical grid lines
                if c_idx < 3:
                    arcade.draw_line(
                        curr_col_x + width, card_y + 2,
                        curr_col_x + width, card_y + card_h - 2,
                        (60, 60, 60), 1
                    )

            curr_col_x += width

            