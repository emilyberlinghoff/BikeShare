def main():
    import sys
    if 'google.colab' in sys.modules:
        get_ipython().system('pip install --quiet tqdm')

    import pandas as pd
    import numpy as np
    from datetime import datetime
    from math import radians, sin, cos, asin, sqrt
    from tqdm import tqdm

    # Enable progress bars in Pandas
    tqdm.pandas()

    ############################################################################
    # 1) CONFIG & LOOKUP TABLES
    ############################################################################
    TRIPS_CSV = '/content/Bike share ridership 2024-07.csv'
    STATION_INFO_JSON = 'https://tor.publicbikesystem.net/ube/gbfs/v1/en/station_information'
    WEATHER_FILES = {
        "TORONTO_CITY": "weather_toronto_city.csv",
        "TORONTO_CITY_CENTRE": "weather_toronto_citycentre.csv",
        "TORONTO_INTL_A": "weather_toronto_intl_a.csv",
        "TORONTO_NORTH_YORK": "weather_toronto_northyork.csv"
    }

    REGION_COORDS = {
        "TORONTO_CITY": (43.6667, -79.4000),
        "TORONTO_CITY_CENTRE": (43.6275, -79.3961),
        "TORONTO_INTL_A": (43.6767, -79.6310),
        "TORONTO_NORTH_YORK": (43.7800, -79.4678)
    }

    # Convert numeric Month → word
    MONTH_NAMES = {
        1: 'January', 2: 'February', 3: 'March', 4: 'April',
        5: 'May', 6: 'June', 7: 'July', 8: 'August',
        9: 'September', 10: 'October', 11: 'November', 12: 'December'
    }

    ############################################################################
    # 2) HELPER FUNCTIONS
    ############################################################################
    def haversine_distance(lat1, lon1, lat2, lon2):
        """ Great-circle distance in km between two lat/lon points. """
        rlat1, rlon1, rlat2, rlon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlon = rlon2 - rlon1
        dlat = rlat2 - rlat1
        a = sin(dlat / 2)**2 + cos(rlat1) * cos(rlat2) * sin(dlon / 2)**2
        c = 2 * asin(np.sqrt(a))
        return 6371 * c

    def nearest_region(lat, lon):
        """ Return the weather region closest to lat/lon. """
        min_dist = float('inf')
        candidate = None
        for region_name, (r_lat, r_lon) in REGION_COORDS.items():
            dist = haversine_distance(lat, lon, r_lat, r_lon)
            if dist < min_dist:
                min_dist = dist
                candidate = region_name
        return candidate

    def load_weather_data():
        """
        Load each region's CSV.
        Parse "Date/Time (LST)" → a DateTime, from which we get 'Date' & 'Hour'.
        """
        region_dfs = {}
        for region_name, csv_path in WEATHER_FILES.items():
            try:
                df = pd.read_csv(csv_path)
                if "Date/Time (LST)" in df.columns:
                    df["DateTime"] = pd.to_datetime(df["Date/Time (LST)"], errors="coerce")
                    df["Date"] = df["DateTime"].dt.date
                    df["Hour"] = df["DateTime"].dt.hour
                else:
                    # Possibly daily data or another format
                    if "Date" not in df.columns:
                        df["Date"] = np.nan
                    if "Hour" not in df.columns:
                        df["Hour"] = np.nan

                region_dfs[region_name] = df
            except FileNotFoundError:
                print(f"Warning: {csv_path} not found for region {region_name}.")
                region_dfs[region_name] = pd.DataFrame()
        return region_dfs

    def lookup_weather(region_name, trip_date, trip_hour, weather_data):
        """
        Return (Temp (°C), Precip. Amount (mm)) from the matching row
        in the region's DataFrame, matched on date/hour (if hourly).
        """
        df = weather_data.get(region_name, pd.DataFrame())
        if df.empty:
            return None, None

        region_df = df[df["Date"] == trip_date]
        if region_df.empty:
            return None, None

        # If daily or no hour info, just first row of that date
        if region_name == "TORONTO_NORTH_YORK" or region_df["Hour"].isnull().all():
            row = region_df.iloc[0]
            return row.get("Temp (°C)", None), row.get("Precip. Amount (mm)", None)

        # Otherwise match the hour
        match_df = region_df[region_df["Hour"] == float(trip_hour)]
        if not match_df.empty:
            row = match_df.iloc[0]
            return row.get("Temp (°C)", None), row.get("Precip. Amount (mm)", None)
        else:
            return None, None

    ############################################################################
    # 3) MAIN SCRIPT
    ############################################################################
    # A) Read the historical trips
    trips = pd.read_csv(TRIPS_CSV)

    # B) Parse times behind the scenes, but keep original "Start Time" format in the final
    parsed_start_times = pd.to_datetime(trips["Start Time"], format="%m/%d/%Y %H:%M")
    trips["Hour"] = parsed_start_times.dt.hour
    trips["AM_PM"] = trips["Hour"].apply(lambda x: "AM" if x < 12 else "PM")
    trips["Month"] = parsed_start_times.dt.month.map(MONTH_NAMES)
    trips["DayOfWeek"] = parsed_start_times.dt.day_name()
    trips["Date"] = parsed_start_times.dt.date  # for weather matching

    # C) Read station info
    station_info_json = pd.read_json(STATION_INFO_JSON)
    station_info = pd.json_normalize(station_info_json["data"]["stations"])
    station_info["station_id"] = station_info["station_id"].astype(int)

    # D) Remove unnecessary columns **before merging** to speed up merges
    #    (We keep: station_id, lat, lon, capacity, is_charging_station, nearby_distance
    #     plus any other columns you explicitly want.)
    #    We'll drop the rest (like name, post_code, physical_configuration, cross_street, etc.)

    columns_to_drop = [
        "name",
        "physical_configuration",
        "altitude",
        "address",
        "rental_methods",
        "groups",
        "obcn",
        "short_name",
        "_ride_code_support",
        "post_code",
        "cross_street"  # user wants it removed, if it exists
    ]
    # Drop them from station_info if present
    station_info.drop(columns=columns_to_drop, inplace=True, errors='ignore')
    # This leaves only the columns we didn't drop (like station_id, lat, lon, capacity, etc.)

    # E) Merge trips + station info
    trips.rename(columns={"Start Station Id": "station_id"}, inplace=True)
    merged = pd.merge(
        trips,
        station_info,
        on="station_id",
        how="left",
        suffixes=("", "_station")
    )

    # F) Determine nearest weather region
    def find_region_for_row(row):
        lat = row["lat"]
        lon = row["lon"]
        if pd.isnull(lat) or pd.isnull(lon):
            return None
        return nearest_region(lat, lon)

    merged["weather_region"] = merged.apply(find_region_for_row, axis=1)

    # G) Load weather data & row-by-row lookup
    all_weather_data = load_weather_data()

    def find_weather_for_row(row):
        region = row["weather_region"]
        date_ = row["Date"]
        hour_ = row["Hour"]
        if not region:
            return pd.Series([np.nan, np.nan])
        temp_val, precip_val = lookup_weather(region, date_, hour_, all_weather_data)
        return pd.Series([temp_val, precip_val])

    merged[["Temp (°C)", "Precip. Amount (mm)"]] = merged.progress_apply(find_weather_for_row, axis=1)

    # H) Final Cleanup
    #    1) Rename "Trip Duration" to indicate it's in seconds
    if "Trip  Duration" in merged.columns:
        merged.rename(columns={"Trip  Duration": "Trip Duration (seconds)"}, inplace=True)
    elif "Trip Duration" in merged.columns:
        merged.rename(columns={"Trip Duration": "Trip Duration (seconds)"}, inplace=True)

    #    2) Rename "station_id" back to "Start Station Id"
    merged.rename(columns={"station_id": "Start Station Id"}, inplace=True)

    #    3) Drop columns the user doesn't want in the final
    #       "Model" (Bike model), "Date" (redundant), etc.
    #       We'll keep "nearby_distance" as requested.
    #       We already dropped a bunch from station_info,
    #       but let's remove from the merged if still present.

    final_drops = [
        "Model",  # remove bike model
        "Date"    # redundant
    ]
    for col in final_drops:
        if col in merged.columns:
            merged.drop(columns=[col], inplace=True)

    # I) Save final output
    merged.to_csv("merged_bikeshare_with_weather.csv", index=False)
    print("Success! Created 'merged_bikeshare_with_weather.csv'. Unnecessary station info was removed prior to merging for efficiency.")
# End of main()

if __name__ == "__main__":
    main()
