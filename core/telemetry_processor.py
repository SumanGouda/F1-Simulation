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
    
    def get_gear_data(self):
        """
        Return gear array.
        """
        if self.telemetry is None:
            return None

        return self.telemetry['nGear'].to_numpy()
   
    def get_drs_data(self):
        """
        Return DRS array.
        """
        if self.telemetry is None:
            return None

        return self.telemetry['DRS'].to_numpy()
    
    def get_driver_ahead(self):
        """
        Returns a cleaned array of the driver ahead.
        Logic: 
        1. If both DriverAhead and DistanceToDriverAhead are missing -> NaN (Leading).
        2. If only DriverAhead is missing -> Fill with previous known driver.
        """
        if self.telemetry is None:
            return None

        if 'DriverAhead' in self.telemetry.columns:
            # Create a temporary series to work with
            driver_ahead = self.telemetry['DriverAhead']
            distance_ahead = self.telemetry['DistanceToDriverAhead'] if 'DistanceToDriverAhead' in self.telemetry.columns else None

            # Logic: If both are missing, the driver is truly in "Clean Air"
            if distance_ahead is not None:
                is_leading = driver_ahead.isna() & distance_ahead.isna()
                
                driver_ahead = driver_ahead.ffill()
                driver_ahead[is_leading] = np.nan

            return driver_ahead.to_numpy()
        
        return None
    
    def get_distance_ahead(self):
        """
        Calculates the time gap to the driver ahead in seconds.
        Formula: Distance (m) / (Speed (km/h) / 3.6)
        Returns a NumPy array rounded to 3 decimal places.
        """
        if self.telemetry is None:
            return None

        if 'DistanceToDriverAhead' in self.telemetry.columns and 'Speed' in self.telemetry.columns:
            # 1. Get raw distance (m) and speed (km/h)
            dist_m = self.telemetry['DistanceToDriverAhead']
            speed_kmh = self.telemetry['Speed']

            # 2. Convert speed to m/s to match distance units
            speed_ms = speed_kmh / 3.6

            # 3. Calculate time gap
            # We use .replace(0, np.nan) to avoid DivisionByZero errors if a car is stationary
            time_gap = dist_m / speed_ms.replace(0, np.nan)

            # 4. Round to 3 decimal places and return as NumPy
            return np.round(time_gap.to_numpy(), 3)
        
        return None