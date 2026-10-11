
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "Data"

OUTPUT_FILE = DATA_DIR / "flood_data.csv"
RISK_OUTPUT = DATA_DIR / "risk_outputs.csv"

# Prototype weights: illustrative, not scientifically validated.
WEIGHTS = {
    "flood_area_score": 0.30,
    "rainfall_score": 0.25,
    "population_score": 0.25,
    "infrastructure_score": 0.20,
}


def classify_risk(score):
    if score < 25:
        return "Low"
    elif score < 50:
        return "Moderate"
    elif score < 75:
        return "High"
    return "Critical"


def main():
    # These example values are NOT historical measurements.
    # Replace them only when verified event-specific data is available.
    data = pd.DataFrame([{
        "event": "Kerala floods, July 2018",
        "location": "Ernakulam",
        "event_date": "2018-07-16",
        "flood_area_km2": 10.0,
        "rainfall_mm": 230.0,
        "population_exposed": 10000,
        "critical_infrastructure_affected": 5,
        "data_status": "ILLUSTRATIVE SCENARIO - NOT OBSERVED DATA",
    }])

    # Normalize indicators against explicitly chosen prototype references.
    data["flood_area_score"] = (
        data["flood_area_km2"] / 100 * 100
    ).clip(0, 100)

    data["rainfall_score"] = (
        data["rainfall_mm"] / 300 * 100
    ).clip(0, 100)

    data["population_score"] = (
        data["population_exposed"] / 100000 * 100
    ).clip(0, 100)

    data["infrastructure_score"] = (
        data["critical_infrastructure_affected"] / 50 * 100
    ).clip(0, 100)

    data["risk_score"] = (
        data["flood_area_score"] * WEIGHTS["flood_area_score"]
        + data["rainfall_score"] * WEIGHTS["rainfall_score"]
        + data["population_score"] * WEIGHTS["population_score"]
        + data["infrastructure_score"] * WEIGHTS["infrastructure_score"]
    ).round(2)

    data["risk_category"] = data["risk_score"].apply(classify_risk)

    data.to_csv(OUTPUT_FILE, index=False)
    data.to_csv(RISK_OUTPUT, index=False)

    print("\nFlood risk prototype generated.")
    print(data[[
        "event", "location", "risk_score", "risk_category",
        "data_status"
    ]].to_string(index=False))
    print(f"\nSaved input dataset: {OUTPUT_FILE}")
    print(f"Saved risk output:   {RISK_OUTPUT}")
    print("\nWARNING: This is an illustrative scenario,")
    print("not a validated assessment of the 2018 Kerala floods.")


if __name__ == "__main__":
    main()
