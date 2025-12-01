"""
Service cost estimator library.
This file acts as a NON-CRUD library as required for the project.
"""

def estimate_cost(service_type, vehicle_category):
    base_cost = {
        "Oil Change": 50,
        "General Service": 120,
        "Brake Check": 70
    }

    vehicle_multiplier = {
        "Car": 1.0,
        "SUV": 1.3,
        "Motorbike": 0.7
    }

    # Get base price of selected service
    service_price = base_cost.get(service_type, 0)

    # Adjust price based on vehicle type
    multiplier = vehicle_multiplier.get(vehicle_category, 1.0)

    estimated_cost = service_price * multiplier
    return round(estimated_cost, 2)
