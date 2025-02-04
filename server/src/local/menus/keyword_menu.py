from typing import Optional, List
from sqlmodel import Session
from services.generation.keyword_generator import KeywordGenerator
from services.job_automation.keyword_scraping_scheduler import KeywordScrapingScheduler
from local.menus.scraping.config import ScrapingConfig
from .base_menu import BaseMenu
from rich.console import Console
from rich.table import Table
import asyncio
import os
import logging
from services.job_automation.jobup.auto_apply import AutoApply

console = Console()
logger = logging.getLogger(__name__)

class KeywordMenu(BaseMenu):
    def __init__(self, session: Optional[Session]):
        super().__init__(session)
        self.keyword_generator = KeywordGenerator(self.session)
        self.scraping_config = ScrapingConfig()

        # Load existing configuration if available
        config_path = os.path.join(os.getcwd(), "scraping_config.json")
        if os.path.exists(config_path):
            if self.scraping_config.import_config(config_path):
                self._current_keywords = self.scraping_config.keywords.copy()
            else:
                self._current_keywords = []
        else:
            self._current_keywords = []

        self._scheduler: Optional[KeywordScrapingScheduler] = None
        self._scheduler_task: Optional[asyncio.Task] = None

    async def display(self):
        """Display the keyword generator menu and handle user input."""
        while True:
            self.print_header("Job Search Keyword Generator")
            print("1. Generate Keywords")
            print("2. Start Automatic Scraping with Current Keywords")
            print("3. Stop Automatic Scraping")
            print("4. Configure Scraping Parameters")
            print("5. Check and Process Quick Apply Jobs")
            print("6. Manage Keywords")
            print("7. Back to Main Menu")

            choice = input("\nEnter your choice (1-7): ")

            if choice == "1":
                await self.generate_keywords()
            elif choice == "2":
                await self.start_automatic_scraping()
            elif choice == "3":
                await self.stop_automatic_scraping()
            elif choice == "4":
                await self.configure_scraping()
            elif choice == "5":
                await self.check_and_process_quick_apply()
            elif choice == "6":
                await self.manage_keywords()
            elif choice == "7":
                if self._scheduler and self._scheduler.running:
                    console.print("[yellow]Warning: Automatic scraping is still running[/yellow]")
                    if input("Do you want to stop it before exiting? (y/n): ").lower() == 'y':
                        await self.stop_automatic_scraping()
                break
            else:
                print("\nInvalid choice!")
                await self.wait_for_user()

    async def configure_scraping(self):
        """Configure scraping parameters using the existing configuration system"""
        self.print_header("Configure Scraping Parameters")

        # Load existing configuration if available
        config_path = os.path.join(os.getcwd(), "scraping_config.json")
        if os.path.exists(config_path):
            if input("Found existing configuration. Do you want to load it? (y/n): ").lower() == 'y':
                if self.scraping_config.import_config(config_path):
                    console.print("[green]Configuration loaded successfully[/green]")
                else:
                    console.print("[red]Failed to load configuration[/red]")

        # Configure parameters
        while True:
            print("\n1. Set Employment Grade")
            print("2. Set Publication Date")
            print("3. Set Categories")
            print("4. Set Regions")
            print("5. Show Current Configuration")
            print("6. Export Configuration")
            print("7. Import Configuration")
            print("8. Back")

            subchoice = input("\nEnter your choice (1-8): ")

            if subchoice == "1":
                await self.set_employment_grade()
            elif subchoice == "2":
                await self.set_publication_date()
            elif subchoice == "3":
                await self.set_categories()
            elif subchoice == "4":
                await self.set_regions()
            elif subchoice == "5":
                await self.show_configuration()
            elif subchoice == "6":
                await self.export_configuration()
            elif subchoice == "7":
                await self.import_configuration()
            elif subchoice == "8":
                break
            else:
                print("\nInvalid choice!")
                await self.wait_for_user()

    async def set_employment_grade(self):
        """Set employment grade range"""
        self.print_header("Set Employment Grade")
        try:
            print("Enter employment grade range (0-100)")
            min_grade = input("Minimum grade (press Enter to skip): ")
            max_grade = input("Maximum grade (press Enter to skip): ")

            self.scraping_config.employment_grade_min = int(min_grade) if min_grade else None
            self.scraping_config.employment_grade_max = int(max_grade) if max_grade else None

            print(f"Employment grade range set to: {self.scraping_config.employment_grade_min}-{self.scraping_config.employment_grade_max}")
        except ValueError:
            print("Invalid input! Please enter numbers only.")
        await self.wait_for_user()

    async def set_publication_date(self):
        """Set publication date filter"""
        self.print_header("Set Publication Date")
        dates = self.scraping_config.get_publication_dates()
        print("\nAvailable date ranges:")
        for date_id, date_name in dates.items():
            print(f"{date_id}. {date_name}")

        try:
            date_choice = input("\nSelect date range (press Enter to skip): ")
            self.scraping_config.publication_date = int(date_choice) if date_choice else None
            if self.scraping_config.publication_date:
                print(f"Publication date set to: {dates.get(self.scraping_config.publication_date)}")
        except ValueError:
            print("Invalid input! Please enter a number.")
        await self.wait_for_user()

    async def set_categories(self):
        """Set job categories"""
        self.print_header("Set Categories")
        categories = self.scraping_config.get_categories()
        subcategories = self.scraping_config.get_subcategories()

        print("\nAvailable categories:")
        for cat_id, cat_name in categories.items():
            print(f"\n{cat_id}. {cat_name}")
            if cat_id in subcategories:
                for sub_id, sub_name in subcategories[cat_id].items():
                    print(f"    {sub_id}. {sub_name}")

        try:
            cat_input = input("\nEnter category IDs (comma-separated, Enter to skip): ")
            if cat_input:
                self.scraping_config.category = [int(x.strip()) for x in cat_input.split(",")]
        except ValueError:
            print("Invalid input! Please enter numbers only.")
        await self.wait_for_user()

    async def set_regions(self):
        """Set regions for job search"""
        self.print_header("Set Regions")
        hierarchy = self.scraping_config.get_region_hierarchy()

        print("\nAvailable regions:")
        for parent_id, region_data in hierarchy.items():
            print(f"\n{parent_id}. {region_data['name']}")
            if region_data['subregions']:
                for sub_id, sub_name in region_data['subregions'].items():
                    print(f"    {sub_id}. {sub_name}")

        try:
            reg_input = input("\nEnter region IDs (comma-separated, Enter to skip): ")
            if reg_input:
                self.scraping_config.region = [int(x.strip()) for x in reg_input.split(",")]
        except ValueError:
            print("Invalid input! Please enter numbers only.")
        await self.wait_for_user()

    async def show_configuration(self):
        """Display current scraping configuration"""
        self.print_header("Current Configuration")

        # Employment grade
        print(f"Employment grade: {self.scraping_config.employment_grade_min or 'Min not set'} - "
              f"{self.scraping_config.employment_grade_max or 'Max not set'}")

        # Publication date
        dates = self.scraping_config.get_publication_dates()
        if self.scraping_config.publication_date:
            print(f"Publication date: {dates.get(self.scraping_config.publication_date)}")
        else:
            print("Publication date: Not set")

        # Categories
        if self.scraping_config.category:
            print("\nSelected categories:")
            categories = self.scraping_config.get_categories()
            subcategories = self.scraping_config.get_subcategories()
            for cat_id in self.scraping_config.category:
                if cat_id in categories:
                    print(f"- {categories[cat_id]}")
                else:
                    for main_cat_id, subs in subcategories.items():
                        if cat_id in subs:
                            print(f"  - {subs[cat_id]}")
                            break

        # Regions
        if self.scraping_config.region:
            print("\nSelected regions:")
            regions = self.scraping_config.get_region_list()
            for reg_id in self.scraping_config.region:
                print(f"- {regions.get(reg_id)}")

        await self.wait_for_user()

    async def export_configuration(self):
        """Export the current configuration"""
        self.print_header("Export Configuration")

        default_path = os.path.join(os.getcwd(), "scraping_config.json")
        filepath = input(f"Enter export path (default: {default_path}): ").strip() or default_path

        if self.scraping_config.export_config(filepath):
            console.print(f"[green]Configuration exported to: {filepath}[/green]")
        else:
            console.print("[red]Failed to export configuration[/red]")

        await self.wait_for_user()

    async def import_configuration(self):
        """Import a configuration file"""
        self.print_header("Import Configuration")

        filepath = input("Enter configuration file path: ").strip()
        if not filepath:
            console.print("[red]No file path provided[/red]")
            await self.wait_for_user()
            return

        if self.scraping_config.import_config(filepath):
            # Sync the imported keywords with _current_keywords
            self._current_keywords = self.scraping_config.keywords.copy()
            console.print(f"[green]Configuration imported from: {filepath}[/green]")
            if self._current_keywords:
                console.print(f"[green]Imported {len(self._current_keywords)} keywords[/green]")
                self.display_keywords_numbered()
        else:
            console.print("[red]Failed to import configuration[/red]")

        await self.wait_for_user()

    def display_keywords(self, keywords_response):
        """Display generated keywords in a formatted table"""
        if not keywords_response:
            console.print("[red]Failed to generate keywords.[/red]")
            return

        # Store the keywords for potential automatic scraping
        self._current_keywords = keywords_response.keywords

        # Create and display the main keywords table
        keywords_table = Table(title="Generated Job Search Keywords")
        keywords_table.add_column("Keywords", style="cyan")

        for keyword in keywords_response.keywords:
            keywords_table.add_row(keyword)

        console.print(keywords_table)

    async def generate_keywords(self):
        """Generate keywords based on user input"""
        self.print_header("Generate Job Search Keywords")
        console.print("This tool will analyze your CV and preferences to generate relevant job search keywords.")

        try:
            user_id = int(console.input("[cyan]Enter your user ID: [/cyan]"))
        except ValueError:
            console.print("[red]Invalid user ID. Please enter a number.[/red]")
            await self.wait_for_user()
            return

        # Language selection
        print("\nSelect language for keyword generation:")
        print("1. English (en)")
        print("2. French (fr)")
        print("3. German (de)")

        lang_choice = input("\nEnter your choice (1-3): ").strip()
        language = None
        if lang_choice == "1":
            language = "english"
        elif lang_choice == "2":
            language = "french"
        elif lang_choice == "3":
            language = "german"

        with console.status("[bold green]Generating keywords..."):
            keywords_response = await self.keyword_generator.generate_keywords(
                user_id=user_id,
                language=language
            )

        if keywords_response and keywords_response.keywords:
            # Add new keywords to existing ones
            new_keywords = [k for k in keywords_response.keywords if k not in self._current_keywords]
            if new_keywords:
                self._current_keywords.extend(new_keywords)
                self.scraping_config.keywords = self._current_keywords
                console.print(f"[green]Added {len(new_keywords)} new keywords[/green]")
            else:
                console.print("[yellow]No new keywords were added (all already exist)[/yellow]")

            self.display_keywords_numbered()
        else:
            console.print("[red]Failed to generate keywords.[/red]")

        await self.wait_for_user()

    async def start_automatic_scraping(self):
        """Start automatic scraping with the generated keywords"""
        if not self._current_keywords:
            console.print("[red]No keywords available. Please generate keywords first.[/red]")
            await self.wait_for_user()
            return

        if self._scheduler and self._scheduler.running:
            console.print("[yellow]Automatic scraping is already running.[/yellow]")
            await self.wait_for_user()
            return

        # Get user input asynchronously
        try:
            user_id_str = await asyncio.to_thread(console.input, "[cyan]Enter your user ID: [/cyan]")
            user_id = int(user_id_str)
        except ValueError:
            console.print("[red]Invalid user ID. Please enter a number.[/red]")
            await self.wait_for_user()
            return

        try:
            interval_str = await asyncio.to_thread(
                console.input,
                "[cyan]Enter interval between scraping rounds in minutes (default: 60): [/cyan]"
            )
            interval = int(interval_str) if interval_str else 60
        except ValueError:
            console.print("[red]Invalid interval. Using default (60 minutes).[/red]")
            interval = 60

        max_browsers_str = await asyncio.to_thread(
            console.input,
            "[cyan]Enter maximum number of browsers (default: 5): [/cyan]"
        )
        max_browsers = int(max_browsers_str) if max_browsers_str else 5

        # Create and start the scheduler with the current scraping configuration
        self._scheduler = KeywordScrapingScheduler(
            session=self.session,
            user_id=user_id,
            keywords=self._current_keywords,
            interval_seconds=interval * 60,  # Convert minutes to seconds
            max_browsers=max_browsers,
            scraping_config=self.scraping_config  # Pass the current configuration
        )

        # Start the scheduler in the background
        self._scheduler_task = asyncio.create_task(self._scheduler.run())

        def handle_scheduler_done(task):
            try:
                task.result()
            except Exception as e:
                logger.error(f"Scheduler task failed: {e}")
            finally:
                self._scheduler = None
                self._scheduler_task = None

        self._scheduler_task.add_done_callback(handle_scheduler_done)

        console.print("[green]Automatic scraping started successfully![/green]")
        console.print(f"[blue]Using {len(self._current_keywords)} keywords with {interval} minute intervals[/blue]")
        await self.wait_for_user()

    async def stop_automatic_scraping(self):
        """Stop the automatic scraping process"""
        if not self._scheduler or not self._scheduler.running:
            console.print("[yellow]No automatic scraping is currently running.[/yellow]")
        else:
            self._scheduler.stop()
            if self._scheduler_task:
                try:
                    await asyncio.wait_for(self._scheduler_task, timeout=10)
                except asyncio.TimeoutError:
                    console.print("[yellow]Warning: Scheduler task did not complete within timeout[/yellow]")
                finally:
                    self._scheduler = None
                    self._scheduler_task = None
            console.print("[green]Automatic scraping stopped successfully![/green]")
        await self.wait_for_user()

    async def check_and_process_quick_apply(self):
        """Check and process pending quick apply jobs."""
        self.print_header("Quick Apply Jobs Status")

        try:
            user_id = int(console.input("[cyan]Enter your user ID: [/cyan]"))
        except ValueError:
            console.print("[red]Invalid user ID. Please enter a number.[/red]")
            await self.wait_for_user()
            return

        # Create AutoApply instance
        auto_apply = AutoApply(self.session, user_id)

        console.print("[cyan]Checking quick apply jobs status...[/cyan]")
        with console.status("[bold green]Processing...", spinner="dots"):
            result = await auto_apply.check_and_process_pending_jobs()

        # Display detailed results
        console.print("\n[bold]Quick Apply Jobs Status:[/bold]")
        console.print(f"Total quick apply jobs found: {result['total_quick_apply']}")
        console.print(f"Already applied to: {result['already_applied']}")
        console.print(f"Pending jobs found: {result['pending']}")

        if result['pending'] > 0:
            console.print("\n[bold]Application Results:[/bold]")
            app_results = result['application_results']['summary']
            console.print(f"[green]Successfully applied: {app_results['successful']}[/green]")
            console.print(f"[yellow]Failed applications: {app_results['failed']}[/yellow]")
            console.print(f"[red]Errors encountered: {app_results['errors']}[/red]")

        await self.wait_for_user()

    async def manage_keywords(self):
        """Manage the list of keywords"""
        while True:
            self.print_header("Keyword Management")
            print("Current Keywords:")
            self.display_keywords_numbered()

            print("\n1. Add Keywords Manually")
            print("2. Remove Keywords")
            print("3. Clear All Keywords")
            print("4. Back")

            choice = input("\nEnter your choice (1-4): ")

            if choice == "1":
                await self.add_keywords_manually()
            elif choice == "2":
                await self.remove_keywords()
            elif choice == "3":
                if input("Are you sure you want to clear all keywords? (y/n): ").lower() == 'y':
                    self._current_keywords = []
                    self.scraping_config.keywords = []
                    console.print("[green]All keywords cleared[/green]")
            elif choice == "4":
                break
            else:
                print("\nInvalid choice!")
            await self.wait_for_user()

    def display_keywords_numbered(self):
        """Display keywords with numbers for selection"""
        if not self._current_keywords:
            console.print("[yellow]No keywords available[/yellow]")
            return

        keywords_table = Table(title="Current Keywords")
        keywords_table.add_column("#", style="cyan")
        keywords_table.add_column("Keyword", style="green")

        for i, keyword in enumerate(self._current_keywords, 1):
            keywords_table.add_row(str(i), keyword)

        console.print(keywords_table)

    async def add_keywords_manually(self):
        """Add keywords manually"""
        self.print_header("Add Keywords Manually")
        print("Enter keywords (one per line, empty line to finish):")

        while True:
            keyword = input().strip()
            if not keyword:
                break
            if keyword not in self._current_keywords:
                self._current_keywords.append(keyword)
                self.scraping_config.keywords = self._current_keywords
                console.print(f"[green]Added keyword: {keyword}[/green]")
            else:
                console.print(f"[yellow]Keyword already exists: {keyword}[/yellow]")

    async def remove_keywords(self):
        """Remove selected keywords"""
        self.print_header("Remove Keywords")
        if not self._current_keywords:
            console.print("[yellow]No keywords to remove[/yellow]")
            return

        self.display_keywords_numbered()
        print("\nEnter the numbers of keywords to remove (comma-separated):")
        try:
            numbers = input().strip()
            if not numbers:
                return

            indices = [int(n.strip()) for n in numbers.split(",")]
            indices.sort(reverse=True)  # Sort in reverse to remove from end first

            removed = []
            for idx in indices:
                if 1 <= idx <= len(self._current_keywords):
                    removed.append(self._current_keywords.pop(idx - 1))

            self.scraping_config.keywords = self._current_keywords
            if removed:
                console.print(f"[green]Removed keywords: {', '.join(removed)}[/green]")
            else:
                console.print("[yellow]No keywords were removed[/yellow]")

        except ValueError:
            console.print("[red]Invalid input. Please enter numbers separated by commas.[/red]")