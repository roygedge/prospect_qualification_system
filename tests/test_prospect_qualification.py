import pytest
import pandas as pd
from unittest.mock import MagicMock, patch, mock_open
from app.services.prospect_service import ProspectService
from app.models.prospect import Prospect


@pytest.fixture
def mock_repository():
    """Create a mock repository for testing."""
    return MagicMock()


@pytest.fixture
def test_regions():
    """Sample region mapping for testing."""
    return {
        "US": ["North America"],
        "US-CA": ["West Coast", "California"],
        "US-WA": ["West Coast", "Washington"],
        "US-NY": ["East Coast", "New York"],
        "US-TX": ["South", "Texas"],
        "CA": ["North America", "Canada"],
        "MX": ["North America", "Latin America"],
        "UK": ["Europe", "United Kingdom"],
        "FR": ["Europe", "European Union"],
        "DE": ["Europe", "European Union"],
        "NG": ["Africa", "Nigeria"],
        "JP": ["Asia", "Japan"],
        "": []  # Edge case: empty location
    }


@pytest.fixture
def test_preferences():
    """Sample user preferences for testing."""
    return {
        "us_california_with_ny_exclusion": {
            "location_include": ["US-CA", "North America"],
            "location_exclude": ["US-NY"]
        },
        "europe_only_with_africa_exclusion": {
            "location_include": ["Europe"],
            "location_exclude": ["Africa"]
        },
        "empty_preferences": {
            "location_include": [],
            "location_exclude": []
        },
        "null_preferences": {
            "location_include": None,
            "location_exclude": None
        },
        "conflicting_regions": {
            "location_include": ["US-CA"],
            "location_exclude": ["North America"]  # Conflicting rules
        },
        "hierarchical_exclusion": {
            "location_include": ["Asia", "Europe"],
            "location_exclude": ["Japan"]  # Hierarchical conflict
        },
        "west_coast_tech": {
            "location_include": ["West Coast", "California"],
            "location_exclude": []  # Simple inclusion of west coast regions
        },
        "european_union_only": {
            "location_include": ["European Union"],
            "location_exclude": []  # Simple inclusion of EU countries
        }
    }


@pytest.fixture
def prospect_service(mock_repository, test_regions, test_preferences):
    """Create a service instance with test data."""
    # Create service with mock repository
    service = ProspectService(mock_repository)
    
    # Replace loaded data with test data
    service.country_regions = test_regions
    service.user_preferences = test_preferences
    
    return service


class TestGetRegionsForLocation:
    """Tests for the get_regions_for_location method."""
    
    def test_us_state(self, prospect_service):
        """Test getting regions for a US state."""
        regions = prospect_service.get_regions_for_location("US", "CA")
        assert set(regions) == set(["West Coast", "California", "North America"])
    
    def test_country_only(self, prospect_service):
        """Test getting regions for a country with no state."""
        regions = prospect_service.get_regions_for_location("UK", None)
        assert set(regions) == set(["Europe", "United Kingdom"])
    
    def test_nonexistent_location(self, prospect_service):
        """Test getting regions for a nonexistent location."""
        regions = prospect_service.get_regions_for_location("XYZ", None)
        assert regions == []
    
    def test_empty_country(self, prospect_service):
        """Test getting regions for an empty country string."""
        regions = prospect_service.get_regions_for_location("", None)
        assert regions == []
    
    def test_none_country(self, prospect_service):
        """Test getting regions when country is None."""
        regions = prospect_service.get_regions_for_location(None, None)
        assert regions == []
    
    def test_none_state(self, prospect_service):
        """Test getting regions when state is None but country is valid."""
        regions = prospect_service.get_regions_for_location("US", None)
        assert regions == ["North America"]
    
    def test_empty_state(self, prospect_service):
        """Test getting regions when state is empty string."""
        regions = prospect_service.get_regions_for_location("US", "")
        assert regions == ["North America"]


class TestIsProspectQualified:
    """Tests for the is_prospect_qualified method."""
    
    def test_direct_inclusion(self, prospect_service):
        """Test qualification via direct location inclusion."""
        qualified = prospect_service.is_prospect_qualified("US", "CA", ["US-CA"], [])
        assert qualified is True
    
    def test_region_inclusion(self, prospect_service):
        """Test qualification via region inclusion."""
        qualified = prospect_service.is_prospect_qualified("CA", None, ["North America"], [])
        assert qualified is True
    
    def test_exclusion_overrides_inclusion(self, prospect_service):
        """Test exclusion rules override inclusion rules."""
        qualified = prospect_service.is_prospect_qualified("US", "NY", ["North America"], ["US-NY"])
        assert qualified is False
    
    def test_no_match(self, prospect_service):
        """Test when location doesn't match any inclusion rule."""
        qualified = prospect_service.is_prospect_qualified("NG", None, ["Europe"], [])
        assert qualified is False
    
    def test_empty_preferences(self, prospect_service):
        """Test with empty inclusion and exclusion lists."""
        qualified = prospect_service.is_prospect_qualified("US", "CA", [], [])
        assert qualified is False
    
    def test_empty_country(self, prospect_service):
        """Test with empty country string."""
        qualified = prospect_service.is_prospect_qualified("", "CA", ["US-CA"], [])
        assert qualified is False
    
    def test_none_country(self, prospect_service):
        """Test with None country."""
        qualified = prospect_service.is_prospect_qualified(None, "CA", ["US-CA"], [])
        assert qualified is False
    
    def test_none_state(self, prospect_service):
        """Test with None state for US country code."""
        qualified = prospect_service.is_prospect_qualified("US", None, ["US-CA"], [])
        assert qualified is False
        
        # But should qualify if "US" is in the inclusions
        qualified = prospect_service.is_prospect_qualified("US", None, ["US"], [])
        assert qualified is True
    
    def test_hierarchical_region_match(self, prospect_service):
        """Test qualification via hierarchical region matching."""
        # UK is in Europe
        qualified = prospect_service.is_prospect_qualified("UK", None, ["Europe"], [])
        assert qualified is True
    
    def test_hierarchical_exclusion(self, prospect_service):
        """Test hierarchical exclusion rules."""
        # JP is in Asia, but also specifically "Japan"
        qualified = prospect_service.is_prospect_qualified("JP", None, ["Asia"], ["Japan"])
        assert qualified is False
    
    def test_case_sensitivity(self, prospect_service):
        """Test case sensitivity in location codes."""
        # Use lowercase "us" instead of "US"
        qualified = prospect_service.is_prospect_qualified("us", "CA", ["US-CA"], [])
        assert qualified is False  # Should be case sensitive


@pytest.mark.parametrize(
    "country,state,expected", [
        ("US", "CA", False),   # Direct inclusion
        ("US", "TX", False),  # Not directly included
        ("CA", None, False),  # In North America which is excluded
        (None, None, False),  # None values
        ("", "", False),      # Empty strings
    ]
)
def test_conflicting_regions_rules(prospect_service, country, state, expected):
    """Test qualification rules with conflicting include/exclude regions."""
    preferences = prospect_service.user_preferences["conflicting_regions"]
    qualified = prospect_service.is_prospect_qualified(
        country, state,
        preferences["location_include"],
        preferences["location_exclude"]
    )
    assert qualified is expected


@pytest.mark.parametrize(
    "country,state,expected", [
        ("UK", None, True),   # In Europe, not excluded
        ("JP", None, False),  # In Asia, but excluded via Japan
        (None, None, False),  # None values
        ("", "", False),      # Empty strings
    ]
)
def test_hierarchical_exclusion_rules(prospect_service, country, state, expected):
    """Test qualification rules with hierarchical region exclusions."""
    preferences = prospect_service.user_preferences["hierarchical_exclusion"]
    qualified = prospect_service.is_prospect_qualified(
        country, state,
        preferences["location_include"],
        preferences["location_exclude"]
    )
    assert qualified is expected


@pytest.mark.parametrize(
    "country,state,expected", [
        ("US", "CA", True),   # California is in West Coast
        ("US", "WA", True),   # Washington is in West Coast
        ("US", "TX", False),  # Texas is not in West Coast
        ("CA", None, False),  # Canada is not in West Coast
        (None, None, False),  # None values
        ("", "", False),      # Empty strings
    ]
)
def test_west_coast_tech_rules(prospect_service, country, state, expected):
    """Test qualification rules for West Coast tech companies."""
    preferences = prospect_service.user_preferences["west_coast_tech"]
    qualified = prospect_service.is_prospect_qualified(
        country, state,
        preferences["location_include"],
        preferences["location_exclude"]
    )
    assert qualified is expected


@pytest.mark.parametrize(
    "country,state,expected", [
        ("FR", None, True),   # France is in EU
        ("DE", None, True),   # Germany is in EU
        ("UK", None, False),  # UK is not in EU
        ("US", None, False),  # US is not in EU
        (None, None, False),  # None values
        ("", "", False),      # Empty strings
    ]
)
def test_european_union_only_rules(prospect_service, country, state, expected):
    """Test qualification rules for EU-only prospects."""
    preferences = prospect_service.user_preferences["european_union_only"]
    qualified = prospect_service.is_prospect_qualified(
        country, state,
        preferences["location_include"],
        preferences["location_exclude"]
    )
    assert qualified is expected


class TestQualifyProspects:
    """Tests for the qualify_prospects method."""
    
    @pytest.fixture
    def test_csv_data(self):
        return (
            "user_id,prospect_id,company_country,company_state\n"
            "us_california_with_ny_exclusion,prospect1,US,CA\n"
            "us_california_with_ny_exclusion,prospect2,US,NY\n"
            "us_california_with_ny_exclusion,prospect3,CA,\n"
            "europe_only_with_africa_exclusion,prospect4,UK,\n"
            "europe_only_with_africa_exclusion,prospect5,NG,\n"
            "empty_preferences,prospect6,US,TX\n"
            "unknown_user,prospect7,US,CA"
        )
    
    @patch('app.services.prospect_service.load_csv')
    def test_qualify_prospects_end_to_end(self, mock_load_csv, prospect_service, test_csv_data):
        """Test end-to-end prospect qualification process."""
        # Setup mock for csv loading
        mock_df = pd.read_csv(pd.io.common.StringIO(test_csv_data))
        mock_load_csv.return_value = mock_df
        
        # Run with mocked file operations
        with patch('builtins.open', mock_open()) as mock_file:
            count = prospect_service.qualify_prospects("dummy_path")
            
            # Should process 7 rows
            assert count == 7
            
            # Verify repository was called
            prospect_service.prospect_repository.add_prospects.assert_called_once()
            
            # Verify the prospects were created correctly
            args, kwargs = prospect_service.prospect_repository.add_prospects.call_args
            prospects = kwargs['prospects']
            
            # Check a few key prospects
            assert any(p.user_id == "us_california_with_ny_exclusion" and p.company_state == "CA" and p.qualified for p in prospects)
            assert any(p.user_id == "us_california_with_ny_exclusion" and p.company_state == "NY" and not p.qualified for p in prospects)
            assert any(p.user_id == "unknown_user" and p.qualified for p in prospects)
    
    @patch('app.services.prospect_service.load_csv')
    def test_empty_dataframe(self, mock_load_csv, prospect_service):
        """Test handling of empty dataframe."""
        # Empty dataframe
        mock_load_csv.return_value = pd.DataFrame(columns=[
            'user_id', 'prospect_id', 'company_country', 'company_state'
        ])
        
        with patch('builtins.open', mock_open()) as mock_file:
            count = prospect_service.qualify_prospects("dummy_path")
            assert count == 0
            
            # Repository should still be called with empty list
            prospect_service.prospect_repository.add_prospects.assert_called_once()
    
    @patch('app.services.prospect_service.load_csv')
    def test_with_null_values(self, mock_load_csv, prospect_service):
        """Test handling of null values in dataframe."""
        # Dataframe with various null patterns
        data = {
            'user_id': ['user1', 'user1', None, 'user2'],
            'prospect_id': ['prospect1', None, 'prospect3', 'prospect4'],
            'company_country': [None, 'US', 'CA', 'UK'],
            'company_state': ['CA', None, None, None]
        }
        mock_load_csv.return_value = pd.DataFrame(data)
        
        with patch('builtins.open', mock_open()) as mock_file:
            count = prospect_service.qualify_prospects("dummy_path")
            assert count == 4
            
            # Repository should be called
            prospect_service.prospect_repository.add_prospects.assert_called_once()
    
    @patch('app.services.prospect_service.load_csv')
    def test_unknown_user(self, mock_load_csv, prospect_service):
        """Test handling of unknown user."""
        # CSV with unknown user - fixed formatting with proper commas
        data = (
            "user_id,prospect_id,company_country,company_state\n"
            "unknown_user,prospect1,US,CA"
        )
        mock_df = pd.read_csv(pd.io.common.StringIO(data))
        mock_load_csv.return_value = mock_df
        
        with patch('builtins.open', mock_open()) as mock_file:
            count = prospect_service.qualify_prospects("dummy_path")
            assert count == 1
            
            # Should still create prospect object
            args, kwargs = prospect_service.prospect_repository.add_prospects.call_args
            assert len(kwargs['prospects']) == 1
            
            # For unknown user (no preferences), prospect should be qualified
            prospect = kwargs['prospects'][0]
            assert prospect.user_id == "unknown_user"
            assert prospect.qualified is True  # Changed to True since no preferences means qualified 