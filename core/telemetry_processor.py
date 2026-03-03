import numpy as np

class TelemetryProcessor:
    """
    Process telemetry data from a FastF1 Lap object
    and prepare it for visualization.
    """

    def __init__(self, lap):
        self.lap = lap
        self.telemetry = None
        self.pos_data = None

        if self.lap is not None:
            self._load_data()

    def _load_data(self):
        """
        Load telemetry and positional data.
        """
        try:
            self.telemetry = self.lap.get_telemetry()
            self.pos_data = self.lap.get_pos_data()
        except Exception as e:
            print(f"Error loading telemetry: {e}")

    def get_track_coordinates(self):
        """
        Return raw X, Y track coordinates.
        """
        if self.pos_data is None:
            return None, None

        return (
            self.pos_data['X'].to_numpy(),
            self.pos_data['Y'].to_numpy()
        )
        
    def get_speed_data(self):
        """
        Return speed array.
        """
        if self.telemetry is None:
            return None

        return self.telemetry['Speed'].to_numpy()

    def get_throttle_data(self):
        """
        Return throttle array.
        """
        if self.telemetry is None:
            return None

        return self.telemetry['Throttle'].to_numpy()
    
    def get_brake_data(self):
        """
        Return brake array.
        """
        if self.telemetry is None:
            return None

        return self.telemetry['Brake'].to_numpy()
    
    def get_RPM_data(self):
        """
        Return RPM array.
        """
        if self.telemetry is None:
            return None

        return self.telemetry['RPM'].to_numpy()
    
    