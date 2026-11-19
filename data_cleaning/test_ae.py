import pandas as pd
import re

text = "DERMATOLOGIE: HÉMATOLOGIE: SYSTÈME NERVEUX:"

def is_empty_headers(text):
    if pd.isna(text): return True
    # Count lowercase characters. If it's very few, it's just headers.
    lowers = len(re.sub(r'[^a-z]', '', text))
    # If the text has colons and is mostly uppercase
    if ':' in text and lowers < 15 and len(text) > 10:
        return True
    return False

print(is_empty_headers(text))
print(is_empty_headers("DERMATOLOGIE: HÉMATOLOGIE: Nothing else really here."))
print(is_empty_headers("DERMATOLOGIE: rash. HÉMATOLOGIE: anemia. SYSTÈME NERVEUX: headache."))
