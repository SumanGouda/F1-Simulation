import os
import arcade
from utils.helpers import get_driver_telemetry

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

    card_w          = 300
    card_h          = 120
    card_spacing    = 20
    y_cor           = 75

    total_cards_width   = num_selected * card_w + (num_selected - 1) * card_spacing
    x_cor               = (screen_width - total_cards_width) / 2

    for i, drv in enumerate(drv_list):
        current_x       = x_cor + i * (card_w + card_spacing)
        current_frame   = app.driver_row_counters.get(drv, 0)
        current_lap     = app.driver_metadata[drv].get('lap_number', 1)

        (hist_speed, hist_brake, hist_throttle, hist_rpm, hist_gear, max_lap_rows) = get_driver_telemetry(
            db_file=db_path, abbr=drv, current_frame=current_frame, current_lap=current_lap
        )
        current_speed = int(
            hist_speed[-1]) if (hist_speed is not None and len(hist_speed) > 0) else 0
        current_gear = int(
            hist_gear[-1]) if (hist_gear is not None and len(hist_gear) > 0) else 0

        center_x    = current_x + (card_w / 2)
        center_y    = y_cor + (card_h / 2)
        drv_color   = app.car_colors.get(drv, arcade.color.GRAY)

        arcade.draw_rect_outline(arcade.XYWH(
            center_x, center_y, card_w, card_h), drv_color, border_width=4)

        arcade.draw_text(drv, center_x, y_cor + card_h - 25,
                         arcade.color.WHITE, 14, bold=True, anchor_x="center")

        # Current Gear (Top-Left inside the card)
        arcade.draw_text(
            f"G: {current_gear if current_gear > 0 else 'N'}", current_x +
            15, y_cor + card_h - 55,
            arcade.color.LIGHT_GOLDENROD_YELLOW, 11, bold=True, anchor_x="left"
        )

        # Speed value (Top-Right inside the card)
        arcade.draw_text(
            f"{current_speed} km/h",  center_x, y_cor + card_h - 55,
            arcade.color.WHITE, 11, bold=True, anchor_x="right"
        )

        # RPM Bar
        current_rpm = int(hist_rpm[-1]) if (hist_rpm is not None and len(hist_rpm) > 0) else 0
        max_rpm     = 15000
        rpm_pct     = min(current_rpm / max_rpm, 1.0)

        bar_w       = (card_w / 2) + 30
        bar_h       = 8
        bar_x       = current_x + 15
        bar_y       = y_cor + 30

        # Background bar (empty)
        arcade.draw_rect_filled(
            arcade.rect.XYWH(bar_x + bar_w / 2, bar_y, bar_w, bar_h), (40, 40, 40)
        )

        # Filled portion based on RPM %
        filled_w = bar_w * rpm_pct
        if filled_w > 0:
            if rpm_pct < 0.5:
                bar_color = (0, 120, 255)      # deep blue — low RPM
            elif rpm_pct < 0.7:
                bar_color = (0, 200, 255)      # cyan blue — mid RPM
            elif rpm_pct < 0.85:
                bar_color = (180, 0, 255)      # purple — high RPM
            else:
                bar_color = (255, 20, 20)      # red flash — near limiter

            arcade.draw_rect_filled(
                arcade.rect.XYWH(bar_x + filled_w / 2, bar_y, filled_w, bar_h),
                bar_color
            )

        # RPM label
        arcade.draw_text(
            f"0", bar_x, bar_y - 16, arcade.color.ASH_GREY, 9, anchor_x="left"
        )
        arcade.draw_text(
            f"{int(max_rpm / 1000)}", bar_x + bar_w, bar_y - 16, arcade.color.ASH_GREY, 9, anchor_x="right"
        )
        arcade.draw_text(
            f"x 1000rpm", bar_x + (bar_w/2), bar_y - 16, arcade.color.ASH_GREY, 9, anchor_x="center"
        )

        # Throttle & Brake vertical bars 
        current_throttle = int(hist_throttle[-1]) if (hist_throttle is not None and len(hist_throttle) > 0) else 0
        current_brake    = int(hist_brake[-1])    if (hist_brake    is not None and len(hist_brake)    > 0) else 0

        # Normalize to 0-1
        max_t = 100.0 if current_throttle > 1 else 1.0
        max_b = 100.0 if current_brake    > 1 else 1.0
        throttle_pct = min(current_throttle / max_t, 1.0)
        brake_pct    = min(current_brake    / max_b, 1.0)

        v_bar_w      = 14
        v_bar_h      = card_h - 40
        v_bar_y_base = y_cor + 10
        right_edge_x = current_x + card_w - 15

        # Throttle bar (right side, left of brake)
        throttle_x   = right_edge_x - v_bar_w - 6

        # Background
        arcade.draw_rect_filled(
            arcade.rect.XYWH(throttle_x, v_bar_y_base + v_bar_h / 2, v_bar_w, v_bar_h), (40, 40, 40)
        )
        # Fill from bottom up
        filled_h = v_bar_h * throttle_pct
        if filled_h > 0:
            arcade.draw_rect_filled(
                arcade.rect.XYWH(throttle_x, v_bar_y_base + filled_h / 2, v_bar_w, filled_h),
                (0, 200, 80)   # green
            )
        arcade.draw_text("T", throttle_x, v_bar_y_base + v_bar_h + 8,
                        arcade.color.LIGHT_GREEN, 9, bold=True, anchor_x="center")

        # Brake bar  
        brake_x = right_edge_x

        # Background
        arcade.draw_rect_filled(
            arcade.rect.XYWH(brake_x, v_bar_y_base + v_bar_h / 2, v_bar_w, v_bar_h),
            (40, 40, 40)
        )
        # Fill from bottom up
        filled_h = v_bar_h * brake_pct
        if filled_h > 0:
            arcade.draw_rect_filled(
                arcade.rect.XYWH(brake_x, v_bar_y_base + filled_h / 2, v_bar_w, filled_h),
                (220, 30, 30)  # red
            )
        arcade.draw_text("B", brake_x, v_bar_y_base + v_bar_h + 8,
                        arcade.color.RED, 9, bold=True, anchor_x="center")