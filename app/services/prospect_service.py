import json
import os
from typing import List
import pandas as pd

from app.utils.csv_loader import load_csv
from app.config import CONFIG_REGION_JSON, CONFIG_USER_PREFERENCES_JSON, CONFIG_PROSPECTS_CSV
from app.models.prospect import Prospect
from app.repositories.prospect_repository import ProspectRepository

class ProspectService:
    """
    Service for qualifying sales prospects based on geographic location rules.
    
    This service manages the qualification of prospects based on location preferences
    defined by users.
    
    The qualification logic applies hierarchical region rules, where prospects can be 
    included or excluded based on their specific location (country/state) or any region
    they belong to (continent, economic zones, etc.).
    """
    def __init__(self, prospect_repository: ProspectRepository):
        self.country_regions = {}
        self.user_preferences = {}
        self.prospect_repository = prospect_repository

        # Load data from data files
        self.load_country_regions()
        self.load_user_preferences()

    def load_country_regions(self, filepath: str= CONFIG_REGION_JSON):
        """Load country to regions mapping"""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"JSON file not found at: {filepath}")
        try:
            with open(filepath, 'r') as f:
                self.country_regions = json.load(f)
        except Exception as e:
            raise RuntimeError(f"Error loading JSON file {filepath}: {e}")

    def load_user_preferences(self, filepath: str= CONFIG_USER_PREFERENCES_JSON):
        """Load user location preferences"""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"JSON file not found at: {filepath}")
        try:
            with open(filepath, 'r') as f:
                self.user_preferences = json.load(f)
        except Exception as e:
            raise RuntimeError(f"Error loading JSON file {filepath}: {e}")
            
        # Handle null values in preferences
        for user_id, prefs in self.user_preferences.items():
            if prefs.get('location_include') is None:
                prefs['location_include'] = []
            if prefs.get('location_exclude') is None:
                prefs['location_exclude'] = []

    def get_regions_for_location(self, country: str, state: str = None) -> List[str]:
        """Get all regions for a given location"""
        location = f"US-{state}" if country == "US" and state else country
        regions = self.country_regions.get(location, [])
        
        # Add country regions if it's a US state
        if country == "US" and state:
            regions.extend(self.country_regions.get("US", []))
        
        return regions

    def is_prospect_qualified(self, prospect_country: str, prospect_state: str, 
                          user_includes: List[str], user_excludes: List[str]) -> bool:
        """
        Determine if a prospect qualifies based on location preferences.
        
        Args:
            prospect_country: The prospect's country code
            prospect_state: The prospect's state code (if US)
            user_includes: List of locations/regions to include
            user_excludes: List of locations/regions to exclude
            
        Returns:
            bool: True if prospect qualifies, False otherwise
        """
        # Validate inputs
        if not prospect_country:
            return False
        
        # Format location for comparison
        location = f"US-{prospect_state}" if prospect_country == "US" and prospect_state else prospect_country
        # Fetch regions for this location
        prospect_regions = self.get_regions_for_location(prospect_country, prospect_state)
        
        if "All" in user_includes:
            included = True
        else:
            included = (location in user_includes or 
                any(region in user_includes for region in prospect_regions))
            
        excluded = (location in user_excludes or 
                any(region in user_excludes for region in prospect_regions))
            
        return included and not excluded

    def qualify_prospects(self, prospects_file: str = CONFIG_PROSPECTS_CSV) -> int:
        """Process prospects and determine qualification
        
        Args:
            prospects_file: Path to the CSV file containing prospect data
            
        Returns:
            int: Number of prospects processed
        """
        prospects_df = load_csv(prospects_file)
        
        prospects_to_add: List[Prospect] = []
        
        for _, prospect in prospects_df.iterrows():
            user_id = prospect['user_id']
            prospect_id = prospect['prospect_id']
            company_country = prospect['company_country']
            company_state = prospect['company_state'] if pd.notna(prospect['company_state']) else None
            
            user_prefs = self.user_preferences.get(user_id)
            qualified = False
            
            if user_prefs:
                # Determine qualification only if user preferences exist
                qualified = self.is_prospect_qualified(
                    company_country,
                    company_state,
                    user_prefs['location_include'],
                    user_prefs['location_exclude']
                )
            else:
                # If no user preferences, set qualified to True
                qualified = True
            
            prospects_to_add.append(Prospect(
                user_id=user_id,
                prospect_id=prospect_id,
                company_country=company_country,
                company_state=company_state,
                qualified=qualified
            ))

        self.prospect_repository.add_prospects(prospects=prospects_to_add)
        
        return len(prospects_df)