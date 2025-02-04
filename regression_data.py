{
  "nbformat": 4,
  "nbformat_minor": 0,
  "metadata": {
    "colab": {
      "provenance": [],
      "authorship_tag": "ABX9TyPJ1yEmUWD+010/GFYnJ6CI",
      "include_colab_link": true
    },
    "kernelspec": {
      "name": "python3",
      "display_name": "Python 3"
    },
    "language_info": {
      "name": "python"
    }
  },
  "cells": [
    {
      "cell_type": "markdown",
      "metadata": {
        "id": "view-in-github",
        "colab_type": "text"
      },
      "source": [
        "<a href=\"https://colab.research.google.com/github/emilyberlinghoff/bike/blob/main/regression_data.py\" target=\"_parent\"><img src=\"https://colab.research.google.com/assets/colab-badge.svg\" alt=\"Open In Colab\"/></a>"
      ]
    },
    {
      "cell_type": "code",
      "execution_count": null,
      "metadata": {
        "id": "8uQlcwEMQbwk"
      },
      "outputs": [],
      "source": [
        "import requests\n",
        "import csv\n",
        "from datetime import datetime\n",
        "\n",
        "# Replace these with the real URLs to your station_status and station_information endpoints\n",
        "STATION_STATUS_URL = 'https://tor.publicbikesystem.net/ube/gbfs/v1/en/station_status'\n",
        "STATION_INFO_URL = 'https://tor.publicbikesystem.net/ube/gbfs/v1/en/station_information'\n",
        "\n",
        "def main():\n",
        "    # 1. Fetch JSON from the two endpoints\n",
        "    status_resp = requests.get(STATION_STATUS_URL).json()\n",
        "    info_resp = requests.get(STATION_INFO_URL).json()\n",
        "\n",
        "    # 2. Parse the top-level metadata and station arrays\n",
        "    # Note: Adjust these keys if your JSON structure differs\n",
        "    last_updated = status_resp['last_updated']\n",
        "    station_status_list = status_resp['data']['stations']\n",
        "    station_info_list = info_resp['data']['stations']\n",
        "\n",
        "    # 3. Convert last_updated to a datetime for the extra columns\n",
        "    dt = datetime.fromtimestamp(last_updated)\n",
        "    hour = dt.hour\n",
        "    am_pm = 'AM' if hour < 12 else 'PM'\n",
        "    month = dt.month\n",
        "    day_of_week = dt.strftime('%A')  # e.g. \"Monday\"\n",
        "\n",
        "    # 4. Convert station_info_list into a dict keyed by station_id for quick lookup\n",
        "    info_dict = {}\n",
        "    for station in station_info_list:\n",
        "        station_id = station['station_id']\n",
        "        info_dict[station_id] = station\n",
        "\n",
        "    # 5. Define which columns we'll put in the CSV\n",
        "    fieldnames = [\n",
        "        'station_id',\n",
        "        'name',\n",
        "        'lat',\n",
        "        'lon',\n",
        "        'capacity',\n",
        "        'is_charging_station',\n",
        "        'num_bikes_available',\n",
        "        'num_docks_available',\n",
        "        'hour',\n",
        "        'am_pm',\n",
        "        'month',\n",
        "        'day_of_week'\n",
        "    ]\n",
        "\n",
        "    # 6. Merge and write out to CSV\n",
        "    with open('combined.csv', 'w', newline='', encoding='utf-8') as csvfile:\n",
        "        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)\n",
        "        writer.writeheader()\n",
        "\n",
        "        for status_station in station_status_list:\n",
        "            st_id = status_station['station_id']\n",
        "\n",
        "            # Ensure this station exists in the info feed\n",
        "            if st_id in info_dict:\n",
        "                info_station = info_dict[st_id]\n",
        "\n",
        "                # Build one row with merged data\n",
        "                row = {\n",
        "                    'station_id': st_id,\n",
        "                    'name': info_station.get('name'),\n",
        "                    'lat': info_station.get('lat'),\n",
        "                    'lon': info_station.get('lon'),\n",
        "                    'capacity': info_station.get('capacity'),\n",
        "                    'is_charging_station': info_station.get('is_charging_station'),\n",
        "                    'num_bikes_available': status_station.get('num_bikes_available'),\n",
        "                    'num_docks_available': status_station.get('num_docks_available'),\n",
        "                    'hour': hour,\n",
        "                    'am_pm': am_pm,\n",
        "                    'month': month,\n",
        "                    'day_of_week': day_of_week\n",
        "                }\n",
        "\n",
        "                # Write the row to the CSV\n",
        "                writer.writerow(row)\n",
        "\n",
        "    print(\"Created combined.csv with merged station data.\")\n",
        "\n",
        "if __name__ == \"__main__\":\n",
        "    main()\n"
      ]
    }
  ]
}