from risk.risk_scoring import calculate_risk


# Test case
features = {
    "fear": 0.5,
    "intimidation": 0.0,
    "hopelessness": 0.5,
    "isolation": 0.0,
    "sleep_disturbance": 0.75,
    "low_social_support": 0.25,
    "data_quality_insufficient": 0
}


longitudinal = {
    "current_distress": 0.75,
    "distress_change": 0.25,
    "distress_from_baseline": 0.50
}


result = calculate_risk(features, longitudinal)


print("\nAAROH RISK ASSESSMENT")
print("----------------------")
print("Risk Score:", result["risk_score"])
print("Risk Level:", result["risk_level"])

print("\nContributing Factors:")

for reason in result["reasons"]:
    print("-", reason)