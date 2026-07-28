import arcade
import numpy as np
from utils.helpers import get_driver_telemetry

def draw_focused_driver_telemetry(app, leader_lap, get_screen_coords, draw_track, box_geometry=(50, 160, 900, 500)):
    abbr    = app.selected_driver
    pos     = app.current_car_positions.get(abbr)

    if pos is not None and pos != (0, 0):
        active_scale = app.track_scale_focused

        fx, fy  = get_screen_coords(pos[0], pos[1], app.rotation, active_scale, app.foc_offset_x, app.foc_offset_y)
        color   = app.car_colors.get(abbr, arcade.color.GRAY)

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
        current_lap = app.driver_metadata[abbr].get('lap_number', 1)

        (hist_speed, hist_brake, hist_throttle, hist_rpm, hist_gear, max_lap_rows) = get_driver_telemetry(
            db_path=app.db_path, abbr=abbr, current_frame=current_frame, current_lap=current_lap
        )           # Do not remove the hist_gear variable

        box_x, box_y, box_w, box_h  = box_geometry
        center_x, center_y          = box_x + (box_w / 2), box_y + (box_h / 2)

        arcade.draw_rect_filled(arcade.XYWH(center_x, center_y, box_w, box_h), arcade.color.BLACK)
        arcade.draw_rect_outline(arcade.XYWH(center_x, center_y, box_w, box_h), arcade.color.DARK_GRAY, border_width=2)

        legend_y = box_y + box_h + 15
        arcade.draw_text("LIVE TELEMETRY PANEL:", box_x, legend_y, arcade.color.WHITE, 12, bold=True)

        arcade.draw_text("■ SPEED",    box_x + 230, legend_y, color, 11, bold=True)
        arcade.draw_text("■ BRAKE",    box_x + 550, legend_y, arcade.color.RED, 11, bold=True)
        arcade.draw_text("■ THROTTLE", box_x + 430, legend_y, arcade.color.GREEN, 11, bold=True)
        arcade.draw_text("■ RPM",      box_x + 340, legend_y, arcade.color.LIGHT_GOLDENROD_YELLOW, 11, bold=True)

        max_b = 100.0 if (hist_brake is not None and len(hist_brake) > 0 and max(hist_brake) > 1.1) else 1.0
        max_t = 100.0 if (hist_throttle is not None and len(hist_throttle) > 0 and max(hist_throttle) > 1.1) else 1.0
        
        solo_datasets = [
            {"data": hist_speed, "max": 380.0,   "color": color},
            {"data": hist_rpm,   "max": 13000.0,
            "color": arcade.color.LIGHT_GOLDENROD_YELLOW},
        ]
        # 3 sections : speed, rpm, throttle+brake
        section_h = (box_h - 20) / 3
        plot_left_pad = 60
        plot_right_pad = 20

        for i, target in enumerate(solo_datasets):
            if target["data"] is not None and len(target["data"]) >= 2:
                section_y = box_y + ((i + 1) * section_h) + 5
                __draw_tel(
                    telemetry_data=target["data"], max_rows=max_lap_rows, 
                    origin_x=box_x + plot_left_pad, origin_y=section_y, plot_width=box_w - plot_left_pad - plot_right_pad, 
                    plot_height=section_h - 15, color=target["color"], title="", max_val=target["max"]
                )

        overlay_section_y = box_y + (0 * section_h) + 20
        for data, col, mx in [
            (hist_throttle, arcade.color.GREEN, max_t),
            (hist_brake,    arcade.color.RED,   max_b),
        ]:
            if data is not None and len(data) >= 2:
                __draw_tel(
                    telemetry_data=data, max_rows=max_lap_rows, origin_x=box_x + plot_left_pad, origin_y=overlay_section_y,
                    plot_width=box_w - plot_left_pad - plot_right_pad, plot_height=section_h - 15, color=col, title="", max_val=mx
                )

def __draw_tel(telemetry_data, max_rows, origin_x, origin_y, plot_width, plot_height, color, title="SPEED", max_val=350.0):
    if telemetry_data is None or len(telemetry_data) < 2:
        return

    indices     = np.arange(len(telemetry_data))
    screen_x    = origin_x + (indices / (max_rows - 1)) * plot_width
    screen_y    = origin_y + (telemetry_data / max_val) * plot_height

    chart_points = np.column_stack((screen_x, screen_y))

    arcade.draw_text(title, origin_x + (plot_width / 2), origin_y + plot_height + 12,
                     arcade.color.WHITE, font_size=10, bold=True, anchor_x="center", anchor_y="center")
    arcade.draw_text(f"{int(max_val)}",     origin_x - 5, origin_y + plot_height,
                     arcade.color.ASH_GREY, font_size=10, anchor_x="right", anchor_y="center")
    arcade.draw_text(f"{int(max_val / 2)}", origin_x - 5, origin_y + (plot_height / 2),
                     arcade.color.ASH_GREY, font_size=10, anchor_x="right", anchor_y="center")
    arcade.draw_text("0",                   origin_x - 5, origin_y,
                     arcade.color.ASH_GREY, font_size=10, anchor_x="right", anchor_y="center")
    arcade.draw_line_strip(chart_points, color, 2)


