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
            
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        text = re.sub(r'www\.[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', '', text)
        text = re.sub(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', '', text)
        text = re.sub(r'([a-zA-Zéàèùâêîôûç])-\s*\n\s*([a-zA-Zéàèùâêîôûç])', r'\1\2', text)
        text = re.sub(r'[ \t]+', ' ', text)
        text = text.replace('\r\n', '\n')
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r'[^\w\s\.,;:\'\"\(\)\-\?!éèêëàâäôöûüùïîçœÉÈÊËÀÂÄÔÖÛÜÙÏÎÇŒ%°+]', ' ', text)
        text = re.sub(r' +', ' ', text)
        return text.strip()


class FrenchDrugNoticeParser:
    """Parser specifically designed for French Medical Documents (Notice Patient/RCP)."""
    
    def __init__(self):
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
        clean_text = MedicalTextCleaner.clean(text)
        combined_pattern = "|".join([f"(?P<{k}>{p})" for k, p in self.header_patterns.items()])
        nom_medicament = self._extract_drug_name(clean_text)
        sections: Dict[str, str] = {}
        matches = list(re.finditer(combined_pattern, clean_text, re.IGNORECASE))
        
        if not matches:
            return DrugNoticeData(nom_medicament=nom_medicament, texte_brut_nettoye=clean_text)
            
        for i, match in enumerate(matches):
            matched_key = [k for k, v in match.groupdict().items() if v is not None][0]
            start_pos = match.end()
            end_pos = matches[i+1].start() if i + 1 < len(matches) else len(clean_text)
            content = clean_text[start_pos:end_pos].strip()
            content = re.sub(r'^[:\-.]\s*', '', content)
            sections[matched_key] = content

        return DrugNoticeData(
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

    def _extract_drug_name(self, clean_text: str) -> Optional[str]:
        lines = clean_text.split('\n')[:15]
        skip_words = [r'notice', r'information', r'utilisateur', r'patient', r'résumé', r'caractéristiques', r'ansm', r'médicament']
        
        for line in lines:
            line_cl = line.strip()
            if len(line_cl) < 3 or len(line_cl) > 80:
                continue
            if any(re.search(sw, line_cl, re.IGNORECASE) for sw in skip_words):
                continue
            if re.search(r'[a-zA-Z]', line_cl):
                return line_cl

        return "Inconnu"
