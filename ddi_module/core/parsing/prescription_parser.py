import re
from dataclasses import dataclass, asdict
from typing import Optional

@dataclass
class PrescriptionData:
    medecin_prescripteur: Optional[str] = None
    patient: Optional[str] = None
    date: Optional[str] = None
    medicaments_detectes: Optional[str] = None
    instructions: Optional[str] = None

    def to_dict(self):
        return asdict(self)

class PrescriptionParser:
    """Parses text from a medical prescription (ordonnance) OCR image."""
    
    def parse(self, text: str) -> PrescriptionData:
        # Regex heuristics for French prescriptions
        date_match = re.search(r'\b(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})\b', text)
        dr_match = re.search(r'(?:Dr\.?|Docteur)\s+([A-Z][a-zA-Zéèêëàâäôöûüùïîç\-\s]+)', text)
        patient_match = re.search(r'(?:M\.|Mme\.?|Monsieur|Madame|Patient)\s+([A-Z][a-zA-Zéèêëàâäôöûüùïîç\-\s]+)', text)
        
        # Clean text to isolate potential meds (mock logic for demo)
        lines = text.split('\n')
        meds = []
        for line in lines:
            line_cl = line.strip()
            if len(line_cl) > 4 and re.search(r'(mg|g|ml|comprimé|gélule|boîte|matin|soir)', line_cl, re.IGNORECASE):
                meds.append(line_cl)
                
        medicaments_detectes = "\n".join(meds) if meds else "Liste brute:\n" + text[:200] + "..."

        return PrescriptionData(
            medecin_prescripteur=dr_match.group(1).strip() if dr_match else "Non détecté",
            patient=patient_match.group(1).strip() if patient_match else "Non détecté",
            date=date_match.group(1) if date_match else "Non détectée",
            medicaments_detectes=medicaments_detectes,
            instructions="Extraction OCR brute - à valider par le médecin."
        )
