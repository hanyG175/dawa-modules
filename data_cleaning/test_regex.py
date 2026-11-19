import re

text1 = "Les cas de survenue de survenue de survenues de survenues de survenues de survenues de survenues"
text2 = "La dose de l'administration de la dose de l'administration de la dose de l'administration"
text3 = "blabla l'a"

def fix_moa(text):
    if not isinstance(text, str): return text
    
    # fix stuttering phrases (3 or more words repeating)
    # We can use a regex that catches repeated phrases.
    import re
    # Match a sequence of words that is repeated 2 or more times
    # (\b(?:\w+\b\W*?){2,5})\1+
    pattern = r'(\b(?:\w+\b\W*?){2,8}?)\1{2,}'
    # keep substituting while matches are found
    prev = None
    curr = text
    while curr != prev:
        prev = curr
        curr = re.sub(pattern, r'\1', curr, flags=re.IGNORECASE)
    
    # remove trailing short articles
    curr = re.sub(r'(?i)\b(?:l\'a|à|de|et|l\')\s*$', '', curr).strip()
    return curr

print(fix_moa(text1))
print(fix_moa(text2))
print(fix_moa(text3))
