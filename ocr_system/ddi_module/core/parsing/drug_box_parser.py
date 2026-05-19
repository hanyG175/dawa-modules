import re
from dataclasses import dataclass, asdict
from typing import Optional

@dataclass
class DrugBoxData:
    nom_medicament: Optional[str] = None
    dosage: Optional[str] = None
    forme_pharmaceutique: Optional[str] = None
    quantite: Optional[str] = None

    def to_dict(self):
        return asdict(self)

class DrugBoxParser:
    """Parses text extracted from a picture of a drug box."""
    
    def parse(self, text: str) -> DrugBoxData:
        dosage = re.search(r'(\d+(?:,\d+)?\s*(?:mg|g|ml|µg|UI|mcg|%))', text, re.IGNORECASE)
        forme = re.search(r'(comprimé|gélule|sirop|solution|sachet|suppositoire|ampoule)s?', text, re.IGNORECASE)
        qte = re.search(r'(\d+)\s*(?:comprimés|gélules|sachets|ampoules|ml)', text, re.IGNORECASE)
        
        lines = [line.strip() for line in text.split('\n') if len(line.strip()) > 3]
        nom = lines[0] if lines else "Non détecté"
        if dosage and nom.endswith(dosage.group(1)):
            nom = nom.replace(dosage.group(1), '').strip()
            
        return DrugBoxData(
            nom_medicament=nom,
            dosage=dosage.group(1) if dosage else "Non détecté",
            forme_pharmaceutique=forme.group(1).capitalize() if forme else "Non détectée",
            quantite=qte.group(0) if qte else "Non détectée",
        )
