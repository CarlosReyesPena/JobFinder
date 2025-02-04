from dataclasses import dataclass, asdict, field
from typing import List, Optional, Dict
import json
import os
from pathlib import Path

@dataclass
class ScrapingConfig:
    term: Optional[str] = None
    employment_grade_min: Optional[int] = None
    employment_grade_max: Optional[int] = None
    publication_date: Optional[int] = None
    category: Optional[List[int]] = None
    benefit: Optional[int] = None
    region: Optional[List[int]] = None
    max_browsers: int = 5
    keywords: List[str] = field(default_factory=list)  # Store the keywords in the config

    def export_config(self, filepath: str) -> bool:
        """
        Export the current configuration to a JSON file.

        Args:
            filepath: Path where to save the configuration

        Returns:
            bool: True if export successful, False otherwise
        """
        try:
            # Convert the config to a dictionary
            config_dict = asdict(self)

            # Ensure the directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            # Save to file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=4)
            return True
        except Exception as e:
            print(f"Error exporting configuration: {e}")
            return False

    def import_config(self, filepath: str) -> bool:
        """
        Import configuration from a JSON file.

        Args:
            filepath: Path to the configuration file

        Returns:
            bool: True if import successful, False otherwise
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                config_dict = json.load(f)

            # Update the current configuration
            for key, value in config_dict.items():
                if hasattr(self, key):
                    setattr(self, key, value)
            return True
        except Exception as e:
            print(f"Error importing configuration: {e}")
            return False

    @staticmethod
    def _load_json(filename: str) -> Dict:
        """Charge un fichier JSON depuis le dossier de configuration."""
        config_dir = Path(__file__).parent / "data"
        config_dir.mkdir(exist_ok=True)

        file_path = config_dir / filename
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Warning: {filename} not found in {config_dir}")
            return {}
        except json.JSONDecodeError:
            print(f"Warning: {filename} is not a valid JSON file")
            return {}

    @staticmethod
    def get_region_list() -> Dict[int, str]:
        """Charge la liste des régions depuis le fichier JSON."""
        data = ScrapingConfig._load_json("regions.json")
        regions = {}

        if "regions" in data:
            for region in data["regions"]:
                # Ajouter la région principale
                regions[region["region_id"]] = region["name"]

                # Ajouter les sous-régions si elles existent
                if "subregions" in region:
                    for subregion in region["subregions"]:
                        regions[subregion["region_id"]] = subregion["name"]

        return regions

    @staticmethod
    def get_region_hierarchy() -> Dict[int, Dict]:
        """
        Retourne la hiérarchie complète des régions avec leurs sous-régions.
        """
        data = ScrapingConfig._load_json("regions.json")
        hierarchy = {}

        if "regions" in data:
            for region in data["regions"]:
                hierarchy[region["region_id"]] = {
                    "name": region["name"],
                    "subregions": {
                        sub["region_id"]: sub["name"]
                        for sub in region.get("subregions", [])
                    }
                }

        return hierarchy

    @staticmethod
    def get_categories() -> Dict[int, str]:
        """Charge les catégories principales depuis le fichier domains.json."""
        data = ScrapingConfig._load_json("domains.json")
        if isinstance(data, list):
            return {item["category_id"]: item["name"] for item in data}
        return {}

    @staticmethod
    def get_subcategories() -> Dict[int, Dict[int, str]]:
        """Charge et organise toutes les sous-catégories par catégorie principale."""
        data = ScrapingConfig._load_json("domains.json")
        subcategories = {}

        if isinstance(data, list):
            for item in data:
                cat_id = item["category_id"]
                subs = item.get("subdomains", [])
                if subs:
                    subcategories[cat_id] = {
                        sub["category_id"]: sub["name"]
                        for sub in subs
                    }

        return subcategories

    @staticmethod
    def get_publication_dates() -> Dict[int, str]:
        """Retourne les options de dates de publication disponibles."""
        return {
            1: "Aujourd'hui",
            3: "3 derniers jours",
            7: "7 derniers jours",
            14: "14 derniers jours",
            31: "31 derniers jours"
        }