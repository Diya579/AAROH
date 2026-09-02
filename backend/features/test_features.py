from text_features import extract_text_features


test_text = (
    "I feel very afraid and I don't feel safe. "
    "I need someone to talk to."
)

features = extract_text_features(test_text)

print("\nTEXT:")
print(test_text)

print("\nEXTRACTED FEATURES:")

for name, value in features.items():
    print(f"{name}: {value}")