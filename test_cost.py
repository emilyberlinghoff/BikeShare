from datetime import datetime

def calculate_station_payout(station: dict, current_time: datetime) -> float:
    """
    Calculate the payout for visiting a specific station at a given time.
    
    Args:
        station: Dictionary containing station information including predictions
        current_time: Current datetime for which to calculate the payout
        
    Returns:
        float: The calculated payout for visiting this station
    """
    try:
        # Get the prediction key for the current time
        prediction_key = current_time.strftime('%Y-%m-%d %H:00:00')
        
        # Get the prediction for this time
        if prediction_key not in station['predictions']:
            return 0.0  # No prediction available, no payout
            
        prediction = station['predictions'][prediction_key]
        
        # Base payout factors
        base_payout = 100.0  # Base payout for any station
        
        # ------------------- REVENUE CALCULATION -------------------
        # Demand-based multiplier (higher demand = higher payout)
        demand_multiplier = 1.0
        if prediction['predicted_demand'] > 0:
            demand_multiplier = min(2.0, 1.0 + (prediction['predicted_demand'] / 20.0))
        
        # Time-based multiplier (rush hours have higher payouts)
        time_multiplier = 1.0
        hour = current_time.hour
        if 7 <= hour <= 9 or 16 <= hour <= 18:  # Rush hours
            time_multiplier = 1.5
        elif 22 <= hour or hour <= 5:  # Late night/early morning
            time_multiplier = 0.7
            
        # Weather-based multiplier (bad weather = higher payout)
        weather_multiplier = 1.0
        if prediction['precipitation'] in ['heavy rain', 'heavy snow']:
            weather_multiplier = 1.3
        elif prediction['precipitation'] in ['light rain', 'light snow']:
            weather_multiplier = 1.1
            
        # Temperature-based multiplier (extreme temperatures = higher payout)
        temp_multiplier = 1.0
        if prediction['temperature'] in ['below -10°C', 'above 25°C']:
            temp_multiplier = 1.2

        # Calculate total revenue
        total_revenue = base_payout * demand_multiplier * time_multiplier * weather_multiplier * temp_multiplier

        # ------------------- REDUCTION CALCULATION -------------------
        # Cost factors HARD CODED
        fuel_cost_per_liter = 1.5  # / liter
        driver_cost_per_hour = 25.0  # / hour
        truck_fuel_efficiency = 0.2  # Liters / km
        truck_maintenance_cost_per_km = 0.1  # / km

        # Fuel cost multiplier
        fuel_cost_multiplier = 1.0
        if fuel_cost_per_liter > 1.5:
            gas_overage = fuel_cost_per_liter - 1.5
            fuel_cost_multiplier -= 0.05 * (gas_overage / 0.1) # For each +0.1 increase in fuel cost, reduce payout by 5%
            # floor to 0.5 so it never goes below half
            if fuel_cost_multiplier < 0.5:
                fuel_cost_multiplier = 0.5
        
        # Driver cost multiplier
        driver_cost_multiplier = 1.0
        if driver_cost_per_hour > 25.0:
            driver_overage = driver_cost_per_hour - 25.0
            driver_cost_multiplier -= 0.05 * driver_overage # For each +$1 increase in driver cost, reduce payout by %5
            # floor to 0.5 so it never goes below half
            if driver_cost_multiplier < 0.5:
                driver_cost_multiplier = 0.5

        # Truck fuel efficiency multiplier
        truck_fuel_efficiency_multiplier = 1.0
        if truck_fuel_efficiency < 0.2:
            fuel_overage = 0.2 - truck_fuel_efficiency
            truck_fuel_efficiency_multiplier -= 0.05 * (fuel_overage / 0.01) # For each +0.01 increase in fuel efficiency, reduce payout by %5
            # floor to 0.5 so it never goes below half
            if truck_fuel_efficiency_multiplier < 0.5:
                truck_fuel_efficiency_multiplier = 0.5

        # Truck maintenance cost multiplier
        truck_maintenance_cost_multiplier = 1.0
        if truck_maintenance_cost_per_km > 0.1:
            maintenance_overage = truck_maintenance_cost_per_km - 0.1
            truck_maintenance_cost_multiplier -= 0.05 * maintenance_overage # For each +$0.01 increase in maintenance cost, reduce payout by %5
            # floor to 0.5 so it never goes below half
            if truck_maintenance_cost_multiplier < 0.5:
                truck_maintenance_cost_multiplier = 0.5
        
        # Calculate total reduction
        total_reduction = base_payout * (1 - fuel_cost_multiplier) + base_payout * (1 - driver_cost_multiplier) + base_payout * (1 - truck_fuel_efficiency_multiplier) + base_payout * (1 - truck_maintenance_cost_multiplier)
        
        # ------------------- TOTAL -------------------
        # Calculate final payout
        final_payout = total_revenue - total_reduction

        # Round to 2 decimal places
        return round(final_payout, 2)
        
    except Exception as e:
        print(f"Error calculating payout for station {station['name']}: {e}")
        return 0.0

def test_cost_function():
    # Create a simple test station
    test_station = {
        'name': 'Test Station',
        'predictions': {
            '2024-03-20 08:00:00': {  # Rush hour
                'predicted_demand': 15,
                'temperature': '15°C to 20°C',
                'precipitation': 'none'
            }
        }
    }
    
    # Test time (rush hour)
    test_time = datetime(2024, 3, 20, 8, 0)
    
    # Calculate payout
    payout = calculate_station_payout(test_station, test_time)
    
    # Print results
    print("\nCost Function Test Results:")
    print("=" * 40)
    print(f"Station: {test_station['name']}")
    # print(f"Time: {test_time.strftime('%Y-%m-%d %H:%M')}")
    # print(f"Predicted Demand: {test_station['predictions']['2024-03-20 08:00:00']['predicted_demand']}")
    # print(f"Temperature: {test_station['predictions']['2024-03-20 08:00:00']['temperature']}")
    # print(f"Precipitation: {test_station['predictions']['2024-03-20 08:00:00']['precipitation']}")
    # print("-" * 40)
    # print(f"Calculated Payout: ${payout:.2f}")
    # print("=" * 40)

if __name__ == "__main__":
    test_cost_function()