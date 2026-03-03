import arcade
from f1_visualizer.core.track_utils import transform_track


class TrackRenderer:
    def __init__(self, x, y, screen_width, screen_height,
                 rotation=0, padding=50):

        # Use your full transformation pipeline
        x_trans, y_trans = transform_track(
            x, y,
            screen_width,
            screen_height,
            rotation=rotation,
            padding=padding
        )

        self.points = list(zip(x_trans, y_trans))

    def draw(self):
        """
        Draw only. No geometry logic.
        """

        # Track surface
        arcade.draw_line_strip(self.points, arcade.color.DARK_GRAY, 10)

        # Racing line
        arcade.draw_line_strip(self.points, arcade.color.WHITE, 3)