import json
import os
import random
from typing import Dict, List

import pytest
from hypothesis import strategies as st
from unittest.mock import MagicMock

from app.services.prospect_service import ProspectService

# Paths to actual data files
CONFIG_REGION_JSON = 'app/data/country-to-regions-mapping.json'
CONFIG_USER_PREFERENCES_JSON = 'app/data/users-locations-settings.json'


@pytest.fixture
def regions_data():
    """Load the actual region mapping data."""
    with open(CONFIG_REGION_JSON, 'r') as f:
        return json.load(f)


@pytest.fixture
def user_preferences():
    """Load the actual user preferences data."""
    with open(CONFIG_USER_PREFERENCES_JSON, 'r') as f:
        return json.load(f)


@pytest.fixture
def prospect_service(regions_data, user_preferences):
    """Create a service instance with actual data."""
    mock_repository = MagicMock()
    service = ProspectService(mock_repository)
    service.country_regions = regions_data
    service.user_preferences = user_preferences
    return service


def all_locations(regions_data):
    """Get all possible locations from the region mapping."""
    return list(regions_data.keys())


def all_regions(regions_data):
    """Get all unique regions from the region mapping."""
    regions = set()
    for region_list in regions_data.values():
        regions.update(region_list)
    return list(regions)


class TestPropertyBasedQualification:
    """Property-based tests for prospect qualification logic."""
    
    def test_all_in_includes(self, prospect_service, regions_data):
        """Test that 'All' in includes qualifies every location not explicitly excluded."""
        locations = all_locations(regions_data)
        
        # Sample random locations to test
        test_locations = random.sample(locations, min(50, len(locations)))
        
        for location in test_locations:
            # Skip US states for this test
            if location.startswith("US-"):
                continue
                
            # For 'All' includes with no excludes
            qualified = prospect_service.is_prospect_qualified(
                location, None, ["All"], []
            )
            assert qualified is True, f"Location {location} should qualify with 'All' include"
            
            # For 'All' includes with this location excluded
            qualified = prospect_service.is_prospect_qualified(
                location, None, ["All"], [location]
            )
            assert qualified is False, f"Location {location} should not qualify when specifically excluded"
    
    def test_region_based_qualification(self, prospect_service, regions_data):
        """Test region-based qualification with various combinations."""
        # Find locations that belong to multiple regions
        multi_region_locations = [(loc, regions) for loc, regions in regions_data.items() 
                                 if len(regions) > 1 and not loc.startswith("US-")]
        
        if not multi_region_locations:
            pytest.skip("No multi-region locations found for testing")
            
        # Sample random multi-region locations
        test_locations = random.sample(multi_region_locations, 
                                      min(20, len(multi_region_locations)))
        
        for location, regions in test_locations:
            # Test that including any region qualifies the location
            for region in regions:
                qualified = prospect_service.is_prospect_qualified(
                    location, None, [region], []
                )
                assert qualified is True, f"Location {location} should qualify with region {region}"
            
            # Test that excluding any region disqualifies even if others are included
            for exclude_region in regions:
                includes = [r for r in regions if r != exclude_region]
                if not includes:
                    continue
                    
                qualified = prospect_service.is_prospect_qualified(
                    location, None, includes, [exclude_region]
                )
                assert qualified is False, f"Location {location} should not qualify when region {exclude_region} is excluded"
    
    def test_us_state_qualification(self, prospect_service, regions_data):
        """Test US state qualification with various combinations."""
        # Get all US states
        us_states = [loc for loc in regions_data.keys() if loc.startswith("US-")]
        
        if not us_states:
            pytest.skip("No US states found for testing")
            
        # Sample random US states
        test_states = random.sample(us_states, min(20, len(us_states)))
        
        for state_code in test_states:
            state = state_code[3:]  # Extract state from "US-XX"
            
            # Test direct inclusion
            qualified = prospect_service.is_prospect_qualified(
                "US", state, [state_code], []
            )
            assert qualified is True, f"US state {state} should qualify when directly included"
            
            # Test region inclusion (US states belong to "US" region)
            qualified = prospect_service.is_prospect_qualified(
                "US", state, ["US"], []
            )
            assert qualified is True, f"US state {state} should qualify with US region include"
            
            # Test North America inclusion
            qualified = prospect_service.is_prospect_qualified(
                "US", state, ["North America"], []
            )
            assert qualified is True, f"US state {state} should qualify with North America include"
            
            # Test direct exclusion overrides region inclusion
            qualified = prospect_service.is_prospect_qualified(
                "US", state, ["US", "North America"], [state_code]
            )
            assert qualified is False, f"US state {state} should not qualify when directly excluded"
    
    def test_real_user_preferences(self, prospect_service, user_preferences, regions_data):
        """Test with actual user preferences from the JSON file."""
        # Sample random user preferences
        user_ids = list(user_preferences.keys())
        test_user_ids = random.sample(user_ids, min(20, len(user_ids)))
        
        # Sample random locations
        locations = all_locations(regions_data)
        test_locations = random.sample(locations, min(30, len(locations)))
        
        for user_id in test_user_ids:
            user_prefs = user_preferences[user_id]
            includes = user_prefs.get('location_include') or []
            excludes = user_prefs.get('location_exclude') or []
            
            for location in test_locations:
                # Skip US states for simplicity
                if location.startswith("US-"):
                    continue
                    
                # Test qualification with actual user preferences
                qualified = prospect_service.is_prospect_qualified(
                    location, None, includes, excludes
                )
                
                # We don't assert anything here because we don't know the expected result
                # This is just to exercise the qualification logic with real data
                print(f"User {user_id} {'qualifies' if qualified else 'does not qualify'} {location}")
                
    @pytest.mark.parametrize("user_case", [
        # User with "All" include and specific excludes
        "5d3d89cb-5a97-4905-ad4c-1989e25afe3d",
        # User with region exclusions
        "8ee5158d-19f7-4b04-b3a4-048e76c14b4b",
        # User with complex region includes
        "1b00386a-cc00-4dac-8ff2-4402dd4b8812",
        # User with US state excludes
        "bba2ff16-16f7-41f6-b9ca-269272bcba20",
    ])
    def test_complex_user_cases(self, prospect_service, user_preferences, regions_data, user_case):
        """Test specific complex user preference cases."""
        if user_case not in user_preferences:
            pytest.skip(f"User case {user_case} not found in user preferences")
            
        user_prefs = user_preferences[user_case]
        includes = user_prefs.get('location_include') or []
        excludes = user_prefs.get('location_exclude') or []
        
        # Sample different types of locations
        regular_countries = [loc for loc in regions_data.keys() 
                            if not loc.startswith("US-") and len(regions_data[loc]) > 0]
        us_states = [loc for loc in regions_data.keys() if loc.startswith("US-")]
        
        test_locations = []
        if regular_countries:
            test_locations.extend(random.sample(regular_countries, min(5, len(regular_countries))))
        if us_states:
            test_locations.extend(random.sample(us_states, min(5, len(us_states))))
        
        for location in test_locations:
            country = location if not location.startswith("US-") else "US"
            state = None if not location.startswith("US-") else location[3:]
            
            qualified = prospect_service.is_prospect_qualified(
                country, state, includes, excludes
            )
            
            # Verify against our understanding of the rules
            if "All" in includes:
                # Location should qualify unless explicitly excluded
                if location in excludes:
                    assert qualified is False, f"Location {location} should not qualify when excluded with All include"
                else:
                    # Check if any region is excluded
                    loc_regions = regions_data.get(location, [])
                    region_excluded = any(region in excludes for region in loc_regions)
                    if region_excluded:
                        assert qualified is False, f"Location {location} should not qualify when its region is excluded"
                    else:
                        assert qualified is True, f"Location {location} should qualify with All include and no exclusions"


if __name__ == "__main__":
    pytest.main(["-v", "test_property_based.py"]) 