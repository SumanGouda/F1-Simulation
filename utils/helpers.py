# utils/helpers.py
import numpy as np

def get_screen_coords(x, y, rotation, track_scale, offset_x, offset_y):
    # 1. Rotate [cite: 2026-01-20]
    rad = np.radians(rotation)
    tx = x * np.cos(rad) - y * np.sin(rad)
    ty = x * np.sin(rad) + y * np.cos(rad)

    # 2. Scale and Offset [cite: 2026-01-20]
    return (tx * track_scale) + offset_x, (ty * track_scale) + offset_y

def prepare_track_layout(raw_x, raw_y, screen_width, screen_height, padding_left, rotation):
    """Fits the track perfectly within the available screen space."""
    draw_width = screen_width - padding_left - 100
    draw_height = screen_height - 150
    
    # 1. Rotate raw coordinates first to find the true 'footprint' [cite: 2026-01-20]
    rad = np.radians(rotation)
    x_rot = raw_x * np.cos(rad) - raw_y * np.sin(rad)
    y_rot = raw_x * np.sin(rad) + raw_y * np.cos(rad)
    
    # 2. Calculate the width and height of the track in 'data units' [cite: 2026-01-20]
    data_width = max(x_rot) - min(x_rot)
    data_height = max(y_rot) - min(y_rot)
    
    # 3. Calculate the scale based on the footprint, not track length [cite: 2026-01-20]
    # This prevents the 'zoomed in' look.
    scale_x = draw_width / data_width
    scale_y = draw_height / data_height
    track_scale = min(scale_x, scale_y) * 0.9  # 0.9 adds a little margin

    # 4. Apply scale and calculate offsets [cite: 2026-01-20]
    x_scaled = x_rot * track_scale
    y_scaled = y_rot * track_scale

    track_center_x = (min(x_scaled) + max(x_scaled)) / 2
    track_center_y = (min(y_scaled) + max(y_scaled)) / 2
    screen_center_x = padding_left + (draw_width / 2)
    screen_center_y = screen_height / 2

    offset_x = screen_center_x - track_center_x
    offset_y = screen_center_y - track_center_y
    
    track_points = [(xi + offset_x, yi + offset_y) for xi, yi in zip(x_scaled, y_scaled)]
    
    return track_points, offset_x, offset_y, track_scale