"""
Quick test script to verify API endpoints work
"""
import requests
import json

BASE_URL = "http://localhost:5000"

def test_status():
    print("Testing /api/status...")
    try:
        response = requests.get(f"{BASE_URL}/api/status")
        print(f"  Status: {response.status_code}")
        print(f"  Response: {response.json()}")
        return response.ok
    except Exception as e:
        print(f"  Error: {e}")
        return False

def test_venues():
    print("\nTesting /api/venues...")
    try:
        response = requests.get(f"{BASE_URL}/api/venues")
        print(f"  Status: {response.status_code}")
        venues = response.json()
        print(f"  Venues: {venues}")
        return response.ok and len(venues) > 0
    except Exception as e:
        print(f"  Error: {e}")
        return False

def test_bulk_recommendations():
    print("\nTesting /api/bulk-recommendations...")
    try:
        data = {
            "venue": None,
            "day_of_week": 5,
            "hour": 22,
            "is_weekend": True,
            "event_type": "regular",
            "inventory_level": 1.0
        }
        response = requests.post(
            f"{BASE_URL}/api/bulk-recommendations",
            json=data,
            headers={"Content-Type": "application/json"}
        )
        print(f"  Status: {response.status_code}")
        if response.ok:
            recs = response.json()
            print(f"  Recommendations: {len(recs)}")
            if len(recs) > 0:
                print(f"  First rec: {recs[0].get('bottle', 'N/A')}")
        else:
            print(f"  Error: {response.text}")
        return response.ok
    except Exception as e:
        print(f"  Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_demand_prediction():
    print("\nTesting /api/demand-prediction...")
    try:
        data = {
            "venue": "NYX Rooftop Lounge",
            "bottle": "Grey Goose",
            "type": "Vodka",
            "price": 350,
            "day_of_week": 5,
            "hour": 22,
            "is_weekend": True,
            "event_type": "DJ",
            "inventory_level": 1.0
        }
        response = requests.post(
            f"{BASE_URL}/api/demand-prediction",
            json=data,
            headers={"Content-Type": "application/json"}
        )
        print(f"  Status: {response.status_code}")
        if response.ok:
            preds = response.json()
            print(f"  Predictions: {len(preds)}")
        else:
            error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
            print(f"  Error: {error_data.get('error', response.text)}")
        return response.ok
    except Exception as e:
        print(f"  Error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Testing Web API Endpoints")
    print("=" * 60)
    
    results = []
    results.append(("Status", test_status()))
    results.append(("Venues", test_venues()))
    results.append(("Bulk Recommendations", test_bulk_recommendations()))
    results.append(("Demand Prediction", test_demand_prediction()))
    
    print("\n" + "=" * 60)
    print("Results:")
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {name}: {status}")
    print("=" * 60)

