import re
from dataclasses import dataclass, asdict
from typing import Dict, Optional, Any

@dataclass
class DrugNoticeData:
    nom_medicament: Optional[str] = None
    indications: Optional[str] = None
    contre_indications: Optional[str] = None
    precautions: Optional[str] = None
    interactions: Optional[str] = None
    grossesse_allaitement: Optional[str] = None
    posologie: Optional[str] = None
    effets_indesirables: Optional[str] = None
    conservation: Optional[str] = None
    composition: Optional[str] = None
    texte_brut_nettoye: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class MedicalTextCleaner:
    """Utility class to clean raw OCR text before parsing."""
    
    @staticmethod
    def clean(text: str) -> str:
        if not text:
            return ""
            
        # 1. Remove URLs/Links (often at the bottom of pages like www.ansm.sante.fr)
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        text = re.sub(r'www\.[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', '', text)
        
        # 2. Remove Email addresses
        text = re.sub(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', '', text)
        
        # 3. Handle typical OCR hyphenations and weird line breaks
        # Re-join words that were broken at the end of a line (e.g. médica- \n ment)
        text = re.sub(r'([a-zA-Zéàèùâêîôûç])-\s*\n\s*([a-zA-Zéàèùâêîôûç])', r'\1\2', text)
        
        # 4. Standardize spacing and newlines
        # Replace multiple spaces with a single space
        text = re.sub(r'[ \t]+', ' ', text)
        # Normalize line endings
        text = text.replace('\r\n', '\n')
        # Replace 3 or more newlines with just 2
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # 5. Remove junk characters (keep French letters, numbers, punctuation)
        # Often OCR translates images into weird utf-8 artifacts
        text = re.sub(r'[^\w\s\.,;:\'\"\(\)\-\?!éèêëàâäôöûüùïîçœÉÈÊËÀÂÄÔÖÛÜÙÏÎÇŒ%°+]', ' ', text)
        
        # Fix weird spacing added by the regex above
        text = re.sub(r' +', ' ', text)
        
        return text.strip()


class FrenchDrugNoticeParser:
    """Parser specifically designed for French Medical Documents (Notice Patient/RCP)."""
    
    def __init__(self):
        # We define a mapping of semantic fields to regex patterns which detect the Start Headers
        # Note: French notices often follow the EMA/ANSM 6 point standard.
        self.header_patterns = {
            'indications': r'(?:1\.\s*)?(?:Qu\'est-ce que|Indication(?:s)?\s*thérapeutique(?:s)?|Dans\s*quel(?:s)?\s*cas\s*est-il\s*utilisé|Pourquoi[^?]*prendre)',
            'contre_indications': r'(?:2\.\s*)?(?:Quelles\s*sont\s*les\s*informations\s*à\s*connaître|Contre-indication(?:s)?|Ne\s*prenez\s*jamais|Ne\s*l\'utilisez\s*jamais)',
            'precautions': r'(?:Mises\s*en\s*garde|Faites\s*attention|Précautions\s*d\'emploi)',
            'interactions': r'(?:Autres\s*médicaments\s*et|Prise\s*ou\s*utilisation\s*d\'autres|Interactions)',
            'grossesse_allaitement': r'(?:Grossesse(?:\s*,\s*| et )allaitement|Fertilité)',
            'posologie': r'(?:3\.\s*)?(?:Comment\s*prendre|Posologie|Comment\s*utiliser|Mode\s*d\'administration)',
            'effets_indesirables': r'(?:4\.\s*)?(?:Quels\s*sont\s*les\s*effets\s*indésirables|Effets\s*indésirables\s*(?:éventuels)?|Effets\s*secondaires)',
            'conservation': r'(?:5\.\s*)?(?:Comment\s*conserver|Conservation)',
            'composition': r'(?:6\.\s*)?(?:Contenu\s*de\s*l\'emballage|Ce\s*que\s*contient|Composition|Que\s*contient)',
        }

    def parse(self, text: str) -> DrugNoticeData:
        # Step 1: Clean OCR text to remove artifacts
        clean_text = MedicalTextCleaner.clean(text)
        
        # We will split text based on headers
        # We construct a massive regex to find all headers and their positions
        combined_pattern = "|".join([f"(?P<{k}>{p})" for k, p in self.header_patterns.items()])
        
        # Step 2: Extract Drug Name (Heuristic: usually in the first 5-10 lines, all caps or big)
        nom_medicament = self._extract_drug_name(clean_text)
        
        # Step 3: Segment the text
        sections: Dict[str, str] = {}
        matches = list(re.finditer(combined_pattern, clean_text, re.IGNORECASE))
        
        if not matches:
            # If standard headers fail, return the text as raw but cleaned
            return DrugNoticeData(nom_medicament=nom_medicament, texte_brut_nettoye=clean_text)
            
        for i, match in enumerate(matches):
            # Find which header matched
            matched_key = [k for k, v in match.groupdict().items() if v is not None][0]
            
            # The section content goes from the end of this match to the start of the next match
            start_pos = match.end()
            end_pos = matches[i+1].start() if i + 1 < len(matches) else len(clean_text)
            
            content = clean_text[start_pos:end_pos].strip()
            
            # Optional: Remove any leading bullet points or colons
            content = re.sub(r'^[:\-.]\s*', '', content)
            
            sections[matched_key] = content

        result = DrugNoticeData(
            nom_medicament=nom_medicament,
            texte_brut_nettoye=clean_text,
            indications=sections.get('indications'),
            contre_indications=sections.get('contre_indications'),
            precautions=sections.get('precautions'),
            interactions=sections.get('interactions'),
            grossesse_allaitement=sections.get('grossesse_allaitement'),
            posologie=sections.get('posologie'),
            effets_indesirables=sections.get('effets_indesirables'),
            conservation=sections.get('conservation'),
            composition=sections.get('composition')
        )
        
        return result

    def _extract_drug_name(self, clean_text: str) -> Optional[str]:
        # Usually the drug name is on the top. 
        # Skip generic notice words.
        lines = clean_text.split('\n')[:15]
        skip_words = [r'notice', r'information', r'utilisateur', r'patient', r'résumé', r'caractéristiques', r'ansm', r'médicament']
        
        for line in lines:
            line_cl = line.strip()
            if len(line_cl) < 3 or len(line_cl) > 80:
                continue
            
            # If the line contains "notice" skip it
            if any(re.search(sw, line_cl, re.IGNORECASE) for sw in skip_words):
                continue
            
            # Extract first legitimate line as drug name (capitalized or mix)
            # Many drugs have their dosage straight in the name (e.g. "DOLIPRANE 1000 mg, comprimé")
            if re.search(r'[a-zA-Z]', line_cl):
                return line_cl

        return "Inconnu"
