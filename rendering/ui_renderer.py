# Starter file
import arcade

class UIRenderer:
    def __init__(self, width, height):
        self.width = width
        self.height = height

    def draw_driver_info(self, driver_name, team_name):
        arcade.draw_text(
            f"Driver: {driver_name}",
            20,
            self.height - 40,
            arcade.color.WHITE,
            16
        )

        arcade.draw_text(
            f"Team: {team_name}",
            20,
            self.height - 70,
            arcade.color.LIGHT_GRAY,
            14
        )

    def draw_speed(self, speed):
        arcade.draw_text(
            f"{int(speed)} km/h",
            self.width - 200,
            40,
            arcade.color.RED,
            28,
            bold=True
        )

    def draw_lap_time(self, lap_time):
        arcade.draw_text(
            f"Lap Time: {lap_time}",
            20,
            self.height - 100,
            arcade.color.YELLOW,
            14
        )