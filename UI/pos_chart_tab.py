import arcade
from utils.helpers import get_driver_lap_positions

def draw_position_chart(db_path, total_laps, total_drivers, origin_x, origin_y, plot_w, plot_h,
                        car_colors=None, retired_icon=None, finished_icon=None):

    driver_lap_positions = get_driver_lap_positions(db_path)
    car_colors           = car_colors or {}

    # Only include drivers with valid grid positions (> 0)
    driver_lap_positions = {
        abbr: positions for abbr, positions in driver_lap_positions.items()
        if positions and positions[0] > 0
    }

    grid_to_abbr = {positions[0]: abbr for abbr, positions in driver_lap_positions.items()}

    # --- Background ---
    arcade.draw_rect_filled(
        arcade.rect.XYWH(origin_x + plot_w / 2, origin_y + plot_h / 2, plot_w, plot_h),
        (10, 10, 10)
    )

    # --- Horizontal grid lines + left side driver labels ---
    for pos in range(1, total_drivers + 1):
        y             = origin_y + plot_h - ((pos - 1) / max(total_drivers - 1, 1)) * plot_h
        driver_at_pos = grid_to_abbr.get(pos)

        arcade.draw_line(origin_x, y, origin_x + plot_w, y, (40, 40, 40), 1)

        if driver_at_pos is None:
            continue

        label_color = car_colors.get(driver_at_pos, arcade.color.GRAY)
        arcade.draw_text(
            driver_at_pos, origin_x - 8, y, label_color, 12,
            bold=True, anchor_x="right", anchor_y="center"
        )

    # --- Vertical grid lines + lap number labels ---
    lap_interval = 6
    for lap in range(0, total_laps + 1, lap_interval):
        x = origin_x + (lap / max(total_laps, 1)) * plot_w
        arcade.draw_line(x, origin_y, x, origin_y + plot_h, (40, 40, 40), 1)
        arcade.draw_text(str(lap), x, origin_y - 15, arcade.color.GRAY, 12, anchor_x="center")

    # --- X axis label ---
    arcade.draw_text(
        "LAPS", origin_x + plot_w / 2, origin_y - 40,
        arcade.color.WHITE, 15, bold=True, anchor_x="center"
    )

    # --- Driver lines ---
    for abbr, positions in driver_lap_positions.items():
        color      = car_colors.get(abbr, arcade.color.WHITE)
        is_retired = len(positions) <= total_laps

        points = []
        for i, pos in enumerate(positions):
            if pos <= 0:
                continue
            x = origin_x + (i / max(total_laps, 1)) * plot_w
            y = origin_y + plot_h - ((pos - 1) / max(total_drivers - 1, 1)) * plot_h
            points.append((x, y))

        if len(points) >= 2:
            arcade.draw_line_strip(points, color, 3)

        if points:
            last_x, last_y = points[-1]
            icon_size      = 18

            if is_retired:
                if retired_icon:
                    arcade.draw_texture_rect(
                        retired_icon,
                        arcade.rect.XYWH(last_x + icon_size / 2, last_y, icon_size, icon_size)
                    )
            else:
                arcade.draw_text(
                    abbr, last_x + icon_size + 5, last_y,
                    color, 12, bold=True, anchor_x="left", anchor_y="center"
                )
                if finished_icon:
                    arcade.draw_texture_rect(
                        finished_icon,
                        arcade.rect.XYWH(last_x + icon_size / 2, last_y, icon_size, icon_size)
                    )

