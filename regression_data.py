import requests
import csv
from datetime import datetime

# Replace these with the real URLs to your station_status and station_information endpoints
STATION_STATUS_URL = 'https://tor.publicbikesystem.net/ube/gbfs/v1/en/station_status'
STATION_INFO_URL = 'https://tor.publicbikesystem.net/ube/gbfs/v1/en/station_information'

def main():
    # 1. Fetch JSON from the two endpoints
    status_resp = requests.get(STATION_STATUS_URL).json()
    info_resp = requests.get(STATION_INFO_URL).json()

    # 2. Parse the top-level metadata and station arrays
    # Note: Adjust these keys if your JSON structure differs
    last_updated = status_resp['last_updated']
    station_status_list = status_resp['data']['stations']
    station_info_list = info_resp['data']['stations']

    # 3. Convert last_updated to a datetime for the extra columns
    dt = datetime.fromtimestamp(last_updated)
    hour = dt.hour
    am_pm = 'AM' if hour < 12 else 'PM'
    month = dt.month
    day_of_week = dt.strftime('%A')  # e.g. "Monday"

    # 4. Convert station_info_list into a dict keyed by station_id for quick lookup
    info_dict = {}
    for station in station_info_list:
        station_id = station['station_id']
        info_dict[station_id] = station

    # 5. Define which columns we'll put in the CSV
    fieldnames = [
        'station_id',
        'name',
        'lat',
        'lon',
        'capacity',
        'is_charging_station',
        'num_bikes_available',
        'num_docks_available',
        'hour',
        'am_pm',
        'month',
        'day_of_week'
    ]

    # 6. Merge and write out to CSV
    with open('combined.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for status_station in station_status_list:
            st_id = status_station['station_id']

            # Ensure this station exists in the info feed
            if st_id in info_dict:
                info_station = info_dict[st_id]

                # Build one row with merged data
                row = {
                    'station_id': st_id,
                    'name': info_station.get('name'),
                    'lat': info_station.get('lat'),
                    'lon': info_station.get('lon'),
                    'capacity': info_station.get('capacity'),
                    'is_charging_station': info_station.get('is_charging_station'),
                    'num_bikes_available': status_station.get('num_bikes_available'),
                    'num_docks_available': status_station.get('num_docks_available'),
                    'hour': hour,
                    'am_pm': am_pm,
                    'month': month,
                    'day_of_week': day_of_week
                }

                # Write the row to the CSV
                writer.writerow(row)

    print("Created combined.csv with merged station data.")

if __name__ == "__main__":
    main()
