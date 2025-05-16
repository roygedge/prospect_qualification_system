# Prospect Qualification System

A system for qualifying business prospects based on geographic location preferences and regional rules.

## Overview

The Prospect Qualification System is designed to automatically qualify business prospects based on their geographic location and user-defined preferences. It processes prospect data from CSV files and applies qualification rules based on country, state, and regional preferences.

## Setup and Installation

**Prerequisites**:
   ```bash
   # Install docker.io
   # Install PostgreSQL
   # Install Python 3.8+
   ```
**Configure Data Files**:
   - Place your prospects CSV in `app/data/prospects.csv`
   - Update region mappings in `app/data/country-to-regions-mapping.json`
   - Set user preferences in `app/data/users-locations-settings.json`

**Run the project**:
   ```bash
   git clone https://github.com/roygedge/prospect_qualification_system.git
   cd prospect_qualification
   docker-compose up --build
   ```

## Usage

1. Open your browser and navigate to [http://0.0.0.0:8000/](http://0.0.0.0:8000/) to view the welcome page.
2. To run the qualification process, go to [http://0.0.0.0:8000/qualify](http://0.0.0.0:8000/qualify).
3. After running, you will see a summary showing:
   - The total number of processed prospects
   - How many were qualified
   - How many were not qualified
4. All qualified prospects are automatically saved to the database.

## System Architecture

The system is built using:
- Python with SQLAlchemy ORM
- PostgreSQL database
- Pandas for data processing
- JSON configuration for region mappings and user preferences

Key components:
- `ProspectService`: Core business logic for qualification
- `ProspectRepository`: Database operations and optimization
- `Prospect` model: Data structure and database schema

## Database Design

### Key Features:
- Unique constraint on (user_id, prospect_id) to prevent duplicates
- Optimized indexes for common queries
- Timestamp tracking for creation and updates
- Efficient storage types for each column

## Qualification Mechanism

Prospects are qualified based on the following rules:

1. **Special Case - "All" in Includes**:
   - If "All" is in the user's `location_include` list, the prospect is qualified unless their location or region is explicitly excluded in `location_exclude`.

2. **US Prospects with State Information**:
   - Format: "US-{STATE}" (e.g., "US-CA")
   - Qualified if either:
     - Their specific location is in `location_include` AND not in `location_exclude`
     - Their region is in `location_include` AND neither their location nor region is in `location_exclude`

3. **Non-US Countries or US without State**:
   - Format: Country code (e.g., "CA")
   - Qualified if either:
     - Their country is in `location_include` AND not in `location_exclude`
     - Their region is in `location_include` AND neither their country nor region is in `location_exclude`

4. **No Preferences**:
   - Set as qualified prospect

## Configuration

### Data Files
- `prospects.csv`: List of prospects with their locations
- `country-to-regions-mapping.json`: Defines which locations belong to which regions
- `users-locations-settings.json`: User preferences for location inclusion/exclusion


## Performance Considerations

- Batch processing for database operations
- Optimized database indexes
- Efficient data structures for location lookups
- Minimal database queries per operation

## Testing

Automated tests are provided to ensure the correctness and reliability of the prospect qualification system.

### How to Run Tests

You can run all tests using pytest. From the project root directory, run:

```bash
pytest
```
### More Information

- The `tests/` directory contains all test cases, fixtures, and additional documentation about the testing approach and scenarios covered.
