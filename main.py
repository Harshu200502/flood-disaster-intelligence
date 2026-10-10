
from report_generator import generate_flood_report, retrieve_guidance


def main():
    # Illustrative test values only, not verified flood observations.
    scenario_data = {
        "location": "Chennai, Tamil Nadu",
        "event_date": "2023-12-05",
        "rainfall_mm": 120,
        "rainfall_period": "24 hours",
        "flood_extent_km2": 18.5,
        "population_exposed": None,
        "infrastructure_exposed": None,
        "data_source": "SIMULATED DEMO DATA",
    }

    # Replace this with Sandhya's actual risk-engine output.
    risk_result = {
        "risk_level": "High",
        "risk_score": None,
        "basis": "Illustrative demo classification; not validated",
    }

    query = (
        "Flood safety, evacuation, emergency response, "
        "population exposure, and uncertainty"
    )

    print("Retrieving flood guidance...")
    guidance = retrieve_guidance(query, top_k=3)

    print("Generating situation report...")
    result = generate_flood_report(
        scenario_data=scenario_data,
        risk_result=risk_result,
        retrieved_guidance=guidance,
    )

    print("\n" + "=" * 55)
    print("FLOOD DISASTER INTELLIGENCE")
    print("=" * 55)
    print("Generation status:", result["status"])
    print("\n" + result["report"])

    print("\nRETRIEVED SOURCES")
    for item in result["evidence"]:
        print(f"\nSource: {item['source']}")
        print(f"Relevance: {item['relevance_score']}")
        print(item["text"])

    print("\nWarning:", result["warning"])


if __name__ == "__main__":
    main()
