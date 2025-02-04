# src/local/menus/scraping/menu.py
from typing import List
from ...menus.base_menu import BaseMenu
from .config import ScrapingConfig
from services.job_automation.jobup.scraper import JobScraper
from rich.console import Console
from rich import print as rprint
import os

console = Console()

class ScrapingMenu(BaseMenu):
    def __init__(self, session):
        super().__init__(session)
        self.config = ScrapingConfig()

    async def display(self):
        while True:
            self.print_header("Scraping Configuration")
            print("1. Set Search Term")
            print("2. Set Employment Grade")
            print("3. Set Publication Date")
            print("4. Set Categories")
            print("5. Set Regions")
            print("6. Set Number of Browsers")
            print("7. Show Current Configuration")
            print("8. Export Configuration")
            print("9. Import Configuration")
            print("10. Start Scraping")
            print("11. Back to Main Menu")

            choice = input("\nEnter your choice (1-11): ")

            if choice == '1':
                await self.set_search_term()
            elif choice == '2':
                await self.set_employment_grade()
            elif choice == '3':
                await self.set_publication_date()
            elif choice == '4':
                await self.set_categories()
            elif choice == '5':
                await self.set_regions()
            elif choice == '6':
                await self.set_browsers()
            elif choice == '7':
                await self.show_configuration()
            elif choice == '8':
                await self.export_configuration()
            elif choice == '9':
                await self.import_configuration()
            elif choice == '10':
                await self.start_scraping()
            elif choice == '11':
                break
            else:
                print("\nInvalid choice!")
                await self.wait_for_user()

    async def export_configuration(self):
        """Export the current configuration to a JSON file."""
        self.print_header("Export Configuration")
        
        # Get the export path
        default_path = os.path.join(os.getcwd(), "scraping_config.json")
        filepath = input(f"Enter export path (default: {default_path}): ").strip()
        if not filepath:
            filepath = default_path

        # Export the configuration
        if self.config.export_config(filepath):
            console.print(f"[green]Configuration exported successfully to: {filepath}[/green]")
        else:
            console.print("[red]Failed to export configuration[/red]")
        
        await self.wait_for_user()

    async def import_configuration(self):
        """Import configuration from a JSON file."""
        self.print_header("Import Configuration")
        
        # Get the import path
        filepath = input("Enter the path to the configuration file: ").strip()
        if not filepath:
            console.print("[red]No file path provided[/red]")
            await self.wait_for_user()
            return

        # Import the configuration
        if self.config.import_config(filepath):
            console.print(f"[green]Configuration imported successfully from: {filepath}[/green]")
        else:
            console.print("[red]Failed to import configuration[/red]")
        
        await self.wait_for_user()

    async def set_search_term(self):
        self.print_header("Set Search Term")
        term = input("Enter search term (press Enter to skip): ")
        self.config.term = term if term else None
        print(f"Search term set to: {self.config.term}")
        await self.wait_for_user()

    async def set_employment_grade(self):
        self.print_header("Set Employment Grade")
        try:
            print("Enter employment grade range (0-100)")
            min_grade = input("Minimum grade (press Enter to skip): ")
            max_grade = input("Maximum grade (press Enter to skip): ")

            self.config.employment_grade_min = int(min_grade) if min_grade else None
            self.config.employment_grade_max = int(max_grade) if max_grade else None

            print(f"Employment grade range set to: {self.config.employment_grade_min}-{self.config.employment_grade_max}")
        except ValueError:
            print("Invalid input! Please enter numbers only.")
        await self.wait_for_user()

    async def set_publication_date(self):
        self.print_header("Set Publication Date")
        dates = self.config.get_publication_dates()
        print("\nAvailable date ranges:")
        for date_id, date_name in dates.items():
            print(f"{date_id}. {date_name}")

        try:
            date_choice = input("\nSelect date range (press Enter to skip): ")
            self.config.publication_date = int(date_choice) if date_choice else None
            if self.config.publication_date:
                print(f"Publication date set to: {dates.get(self.config.publication_date)}")
        except ValueError:
            print("Invalid input! Please enter a number.")
        await self.wait_for_user()

    async def set_categories(self):
        self.print_header("Set Categories")
        categories = self.config.get_categories()
        subcategories = self.config.get_subcategories()

        print("\nCatégories disponibles:")
        for cat_id, cat_name in categories.items():
            print(f"\n{cat_id}. {cat_name}")
            if cat_id in subcategories:
                for sub_id, sub_name in subcategories[cat_id].items():
                    print(f"    {sub_id}. {sub_name}")

        print("\nVous pouvez sélectionner des catégories principales ou des sous-catégories.")
        try:
            cat_input = input("\nEntrez les IDs (séparés par des virgules, Enter pour passer): ")
            if cat_input:
                cat_list = [int(x.strip()) for x in cat_input.split(",")]
                valid_cats = []

                for cat_id in cat_list:
                    # Vérifie si c'est une catégorie principale
                    if cat_id in categories:
                        valid_cats.append(cat_id)
                    else:
                        # Vérifie si c'est une sous-catégorie valide
                        for main_cat_id, subs in subcategories.items():
                            if cat_id in subs:
                                valid_cats.append(cat_id)
                                break

                self.config.category = valid_cats
                print("\nCatégories sélectionnées:")
                for cat_id in valid_cats:
                    if cat_id in categories:
                        print(f"- {categories[cat_id]}")
                    else:
                        for main_cat_id, subs in subcategories.items():
                            if cat_id in subs:
                                print(f"  - {subs[cat_id]}")
                                break

        except ValueError:
            print("Entrée invalide! Veuillez entrer uniquement des nombres.")
        await self.wait_for_user()

    async def set_regions(self):
        self.print_header("Sélection des Régions")
        hierarchy = self.config.get_region_hierarchy()

        print("\nRégions disponibles :")
        # Affichage hiérarchique des régions
        for parent_id, region_data in hierarchy.items():
            print(f"\n{parent_id}. {region_data['name']}")
            if region_data['subregions']:
                for sub_id, sub_name in region_data['subregions'].items():
                    print(f"    {sub_id}. {sub_name}")

        print("\nNote:")
        print("- Pour sélectionner un canton et toutes ses sous-régions, entrez l'ID du canton")
        print("- Pour sélectionner des sous-régions spécifiques, entrez leurs IDs")

        try:
            reg_input = input("\nEntrez les IDs des régions (séparés par des virgules, Enter pour passer): ")
            if reg_input:
                selected_regions = set()  # Utiliser un set pour éviter les doublons
                input_ids = [int(x.strip()) for x in reg_input.split(",")]

                for input_id in input_ids:
                    # Vérifier si c'est une région principale
                    if input_id in hierarchy:
                        selected_regions.add(input_id)
                        # Ajouter automatiquement les sous-régions
                        selected_regions.update(hierarchy[input_id]['subregions'].keys())
                    else:
                        # Vérifier si c'est une sous-région
                        for parent_id, region_data in hierarchy.items():
                            if input_id in region_data['subregions']:
                                selected_regions.add(input_id)
                                break

                self.config.region = list(selected_regions)

                # Afficher la sélection de manière organisée
                print("\nRégions sélectionnées:")
                for parent_id, region_data in hierarchy.items():
                    if parent_id in selected_regions:
                        print(f"- {region_data['name']} (incluant toutes les sous-régions)")
                    else:
                        selected_subs = [sub_id for sub_id in selected_regions if sub_id in region_data['subregions']]
                        if selected_subs:
                            print(f"- Sous-régions de {region_data['name']}:")
                            for sub_id in selected_subs:
                                print(f"    - {region_data['subregions'][sub_id]}")

        except ValueError:
            print("Entrée invalide! Veuillez entrer uniquement des nombres.")
        await self.wait_for_user()

    async def show_configuration(self):
        self.print_header("Configuration Actuelle")

        # Configuration de base
        print(f"Terme de recherche: {self.config.term or 'Non défini'}")
        print(f"Taux d'occupation: {self.config.employment_grade_min or 'Min non défini'} - "
              f"{self.config.employment_grade_max or 'Max non défini'}")

        # Dates de publication
        dates = self.config.get_publication_dates()
        print(f"\nDate de publication: {dates.get(self.config.publication_date, 'Non défini')}")

        # Catégories
        if self.config.category:
            print("\nCatégories sélectionnées:")
            categories = self.config.get_categories()
            subcategories = self.config.get_subcategories()
            for cat_id in self.config.category:
                if cat_id in categories:
                    print(f"- {categories[cat_id]}")
                else:
                    for main_cat_id, subs in subcategories.items():
                        if cat_id in subs:
                            print(f"  - {subs[cat_id]}")
                            break

        # Régions avec la nouvelle structure hiérarchique
        if self.config.region:
            print("\nRégions sélectionnées:")
            hierarchy = self.config.get_region_hierarchy()
            selected_regions = set(self.config.region)

            for parent_id, region_data in hierarchy.items():
                if parent_id in selected_regions:
                    print(f"- {region_data['name']} (incluant toutes les sous-régions)")
                else:
                    selected_subs = selected_regions & set(region_data['subregions'].keys())
                    if selected_subs:
                        print(f"- Sous-régions de {region_data['name']}:")
                        for sub_id in selected_subs:
                            print(f"    - {region_data['subregions'][sub_id]}")

        print(f"\nNombre de navigateurs: {self.config.max_browsers}")
        await self.wait_for_user()
        # Affichage des régions
        if self.config.region:
            print("\nRégions sélectionnées:")
            regions = self.config.get_region_list()
            for reg_id in self.config.region:
                print(f"- {regions.get(reg_id)}")
        else:
            print("\nRégions: Non définies")

        print(f"\nNombre de navigateurs: {self.config.max_browsers}")
        await self.wait_for_user()

    async def set_browsers(self):
        self.print_header("Set Number of Browsers")
        try:
            browsers = input("Enter number of browsers (1-20, default is 5): ")
            if browsers:
                num_browsers = int(browsers)
                if 1 <= num_browsers <= 20:
                    self.config.max_browsers = num_browsers
                    print(f"Number of browsers set to: {num_browsers}")
                else:
                    print("Number must be between 1 and 20")
        except ValueError:
            print("Invalid input! Please enter a number.")
        await self.wait_for_user()

    async def start_scraping(self):
        self.print_header("Start Scraping")
        confirm = input("Do you want to start scraping with the current configuration? (yes/no): ")
        if confirm.lower() == 'yes':
            print("\nStarting scraper...")
            async with JobScraper(self.session, max_browsers=self.config.max_browsers) as scraper:
                await scraper.start_scraping(
                    term=self.config.term,
                    employment_grade_min=self.config.employment_grade_min,
                    employment_grade_max=self.config.employment_grade_max,
                    publication_date=self.config.publication_date,
                    category=self.config.category,
                    region=self.config.region
                    )
            print("Scraping completed!")
        await self.wait_for_user()