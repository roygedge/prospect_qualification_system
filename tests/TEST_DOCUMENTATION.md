# Prospect Qualification Tests Documentation

## Overview

This document provides a comprehensive guide to the test cases implemented for the Prospect Qualification module. The tests focus on verifying the correctness of the qualification logic used to determine whether prospects qualify based on location criteria.

## Running the Tests

To run the tests:

```bash
# Install pytest if not already installed
pip install pytest

pip install -r requirements.txt

# Run all tests
pytest 
```

## Test Structure

The test suite follows a pytest-based organization with fixtures and parameterized tests to thoroughly cover all edge cases and business logic. The tests are organized into the following sections:

1. **Region Retrieval Tests** - Testing the `get_regions_for_location` method
2. **Qualification Logic Tests** - Testing the `is_prospect_qualified` method
3. **User-Specific Rule Tests** - Testing qualification logic for specific user preference configurations
4. **End-to-End Qualification Tests** - Testing the `qualify_prospects` method with various data scenarios

## Test Coverage

### 1. Region Retrieval Tests

Tests for the mapping of locations to regions:

| Test Case | Description | Expected Behavior |
|-----------|-------------|-------------------|
| US state | Testing US state (e.g., "US", "CA") | Returns ["West Coast", "California", "North America"] |
| Country only | Testing country with no state (e.g., "UK") | Returns ["Europe", "United Kingdom"] |
| Nonexistent location | Testing unknown location code | Returns empty list |
| Empty country | Testing with empty string country | Returns empty list |
| None country | Testing with None as country | Returns empty list |
| None state | Testing with None as state but valid country | Returns country-level regions |
| Empty state | Testing with empty string state | Returns country-level regions |

### 2. Qualification Logic Tests

Tests for the core qualification logic:

| Test Case | Description | Expected Behavior |
|-----------|-------------|-------------------|
| Direct inclusion | Location directly in inclusion list | Qualifies (True) |
| Region inclusion | Location's region in inclusion list | Qualifies (True) |
| Exclusion override | Location in inclusion list but also in exclusion list | Doesn't qualify (False) |
| No match | Location not in any inclusion list | Doesn't qualify (False) |
| Empty preferences | Empty inclusion and exclusion lists | Doesn't qualify (False) |
| Empty country | Empty string as country | Doesn't qualify (False) |
| None country | None as country | Doesn't qualify (False) |
| None state | None as state for US country | Depends on inclusion rules |
| Hierarchical region matching | Location in a hierarchical region | Qualifies if region is included |
| Hierarchical exclusion | Location in included region but specifically excluded | Doesn't qualify (False) |
| Case sensitivity | Testing case sensitivity in location codes | Codes are case sensitive |

### 3. User-Specific Rule Tests

Tests for specific user preference configurations:

#### Conflicting Regions Rules
Tests the behavior when inclusion and exclusion rules might conflict:
- Direct inclusion takes precedence over region exclusion (US-CA qualifies even if North America is excluded)
- Non-included locations in excluded regions don't qualify (US-TX)
- Locations in excluded regions don't qualify unless directly included (CA)
- Null values and empty strings don't qualify

#### Hierarchical Exclusion Rules
Tests the behavior of hierarchical region exclusions:
- Locations in included regions qualify if not specifically excluded (UK in Europe)
- Locations specifically excluded don't qualify even if their region is included (JP in Asia)
- Null values and empty strings don't qualify

#### West Coast Tech Rules
Tests simple regional inclusion without exclusions:
- US states in the West Coast region qualify (CA, WA)
- US states outside West Coast don't qualify (TX)
- Non-US countries don't qualify even if named similarly (CA for Canada)
- Null values and empty strings don't qualify

#### European Union Only Rules
Tests simple membership-based inclusion:
- EU member countries qualify (FR, DE)
- Non-EU European countries don't qualify (UK)
- Non-European countries don't qualify (US)
- Null values and empty strings don't qualify

### 4. End-to-End Qualification Tests

Tests for the full qualification process:

| Test Case | Description | Expected Behavior |
|-----------|-------------|-------------------|
| End-to-end processing | Process full CSV dataset | Correct count, repository called, output file created |
| Empty dataframe | Process empty CSV | Zero count, repository called with empty list |
| Null values | Process data with various null patterns | Correct handling of nulls |
| Unknown user | Process prospect with unknown user_id | Prospect created but not qualified |

#### Key Behaviors Tested:
- Repository is always called, even with empty datasets
- Unknown users are processed but marked as unqualified
- Null values in data are handled gracefully
- Output file is created and written correctly
- Batch processing works correctly for multiple prospects

### 5. Property-Based Tests

The test suite includes property-based tests that use actual application data to thoroughly test the qualification logic with various randomized inputs. These tests are designed to uncover edge cases that might be missed by traditional unit testing approaches.

1. "All" Inclusion Tests
2. Region-Based Qualification Tests
3. US State Qualification Tests
4. Real User Preferences Tests
5. Complex User Cases Tests

### Running Property-Based Tests

```bash
# Run property-based tests
pytest tests/test_property_based.py -v
```

### Property-Based Test Coverage

The property-based tests load actual JSON configuration from:
- `app/data/country-to-regions-mapping.json` - For country-to-region mappings
- `app/data/users-locations-settings.json` - For user location preferences
