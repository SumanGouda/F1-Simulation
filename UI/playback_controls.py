def draw_playback_controls(app):
    import arcade 

    LEADERBOARD_LEFT    = 15
    btn_size            = 36
    btn_gap             = 8
    btn_center_y        = app.height - 25

    buttons = [
        ("SLOW",  LEADERBOARD_LEFT + btn_size // 2),
        ("PAUSE", LEADERBOARD_LEFT + btn_size + btn_gap + btn_size // 2),
        ("FAST",  LEADERBOARD_LEFT + btn_size * 2 + btn_gap * 2 + btn_size // 2),
    ]

    hitboxes = {}
    for name, cx in buttons:
        icon_key = "PLAY" if (name == "PAUSE" and app.is_paused) else name
        arcade.draw_texture_rect(
            app.btn_icons[icon_key],
            arcade.rect.XYWH(cx, btn_center_y, btn_size, btn_size)
        )
        hitboxes[name] = {
            "left":   cx - btn_size / 2,
            "right":  cx + btn_size / 2,
            "bottom": btn_center_y - btn_size / 2,
            "top":    btn_center_y + btn_size / 2,
        }
    app.control_hitboxes = hitboxes

def on_slow(app):
    app.race_speed = max(0.5, round(app.race_speed - 0.5, 1))

def on_pause(app):
    app.is_paused = not app.is_paused

def on_fast(app):
    app.race_speed = min(5.0, round(app.race_speed + 0.5, 1))