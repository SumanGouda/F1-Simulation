# Starter file
import numpy as np

def rotate_track(x, y, angle_degrees):
    """
    Rotate track coordinates by angle (degrees).
    """
    angle = np.radians(angle_degrees)

    x_rot = x * np.cos(angle) - y * np.sin(angle)
    y_rot = x * np.sin(angle) + y * np.cos(angle)

    return x_rot, y_rot

def clean_track_data(x, y):
    """
    Cleans track coordinates by closing the loop and removing duplicates.
    """
    if x is None or y is None or len(x) == 0:
        return x, y

    # 1. Remove duplicate consecutive points that cause 'stutter'
    mask = np.insert(np.diff(x)**2 + np.diff(y)**2 > 0, 0, True)
    x_clean = x[mask]
    y_clean = y[mask]

    # 2. Close the loop: Append the first point to the end 
    # to fix the 'blank space' at the Start/Finish line
    x_closed = np.append(x_clean, x_clean[0])
    y_closed = np.append(y_clean, y_clean[0])

    return x_closed, y_closed

def scale_to_window(x, y, width, height, padding=50):
    """
    Scale track to fit inside a window.
    """
    min_x, max_x = np.min(x), np.max(x)
    min_y, max_y = np.min(y), np.max(y)

    scale_x = (width - padding) / (max_x - min_x)
    scale_y = (height - padding) / (max_y - min_y)

    scale = min(scale_x, scale_y)

    x_scaled = (x - min_x) * scale
    y_scaled = (y - min_y) * scale

    return x_scaled, y_scaled


def center_track(x, y, width, height):
    """
    Center track inside window.
    """
    x_offset = (width - (np.max(x) - np.min(x))) / 2
    y_offset = (height - (np.max(y) - np.min(y))) / 2

    return x + x_offset, y + y_offset


def flip_y_axis(y, height):
    """
    Flip Y axis for screen coordinate systems.
    """
    return height - y

def normalize_track(self, width, height, padding=50):
        """
        Scale track to fit inside a window (Arcade / GUI).
        """
        x, y = self.get_track_coordinates()
        if x is None:
            return None, None

        min_x, max_x = np.min(x), np.max(x)
        min_y, max_y = np.min(y), np.max(y)

        scale_x = (width - padding) / (max_x - min_x)
        scale_y = (height - padding) / (max_y - min_y)

        scale = min(scale_x, scale_y)

        x_scaled = (x - min_x) * scale
        y_scaled = (y - min_y) * scale

        return x_scaled, y_scaled

def transform_track(x, y, width, height, rotation=0, padding=50):
    """
    Full transformation pipeline:
    Rotate → Scale → Center
    """
    x, y = rotate_track(x, y, rotation)
    x, y = scale_to_window(x, y, width, height, padding)
    x, y = center_track(x, y, width, height)

    return x, y