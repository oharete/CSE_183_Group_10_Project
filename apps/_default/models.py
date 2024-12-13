"""
This file defines the database models and loads data from CSV files.
"""
import os
import csv
import datetime
from pydal.validators import IS_NOT_EMPTY, IS_INT_IN_RANGE, IS_FLOAT_IN_RANGE, IS_DATE
from .common import db, Field, auth  # Adjust imports as needed for your environment

def get_user_email():
    return auth.current_user.get('email') if auth.current_user else None

def get_time():
    return datetime.datetime.utcnow()

# Define the database tables
db.define_table(
    "species",
    Field("common_name", "string", unique=True, requires=IS_NOT_EMPTY())
)

db.define_table(
    "checklists",
    Field("sampling_event_id", "string", unique=True, requires=IS_NOT_EMPTY()),
    Field("latitude", "double", requires=IS_FLOAT_IN_RANGE(-90, 90)),
    Field("longitude", "double", requires=IS_FLOAT_IN_RANGE(-180, 180)),
    Field("observation_date", "date", requires=IS_DATE()),
    Field("time_started", "time"),
    Field("observer_id", requires=IS_NOT_EMPTY()),
    Field("duration_minutes", "double"),
)
# User-Checklist association table 
db.define_table(
    "user_checklists",
    Field('user_email', default=get_user_email),
    Field("checklist_id", "reference checklists", requires=IS_NOT_EMPTY()),
    Field("species_id", "reference species", requires=IS_NOT_EMPTY()),
    Field("observation_count", "integer", requires=IS_INT_IN_RANGE(1, None)),
)
db.define_table(
    "sightings",
    Field("sampling_event_id", "reference checklists", requires=IS_NOT_EMPTY()),
    Field("common_name", "reference species", requires=IS_NOT_EMPTY()),
    Field("observation_count", "integer", requires=IS_INT_IN_RANGE(1, None)),
)

db.commit()

# Base paths for CSV files
base_path = os.path.dirname(__file__)
uploads_path = os.path.join(base_path, "uploads")

species_csv = os.path.join(uploads_path, "species.csv")
checklist_csv = os.path.join(uploads_path, "checklists.csv")
sightings_csv = os.path.join(uploads_path, "sightings.csv")

# Verify file existence and preview contents
def validate_and_preview(file_path, rows=5):
    if not os.path.exists(file_path):
        print(f"Error: File not found - {file_path}")
        return False
    print(f"Preview of {file_path}:")
    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for i, row in enumerate(reader):
            print(row)
            if i >= rows - 1:
                break
    return True

if not validate_and_preview(species_csv):
    exit(1)
if not validate_and_preview(checklist_csv):
    exit(1)
if not validate_and_preview(sightings_csv):
    exit(1)

# Helper to safely cast values
def safe_cast(value, cast_type, default=None):
    try:
        return cast_type(value)
    except (ValueError, TypeError):
        return default

# Load species CSV
with open(species_csv, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        try:
            db.species.insert(common_name=row["COMMON NAME"])
        except Exception as e:
            print(f"Error inserting species: {row['COMMON NAME']} - {e}")

# Load checklist CSV
with open(checklist_csv, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        try:
            db.checklists.insert(
                sampling_event_id=row["SAMPLING EVENT IDENTIFIER"],
                latitude=safe_cast(row["LATITUDE"], float),
                longitude=safe_cast(row["LONGITUDE"], float),
                observation_date=safe_cast(row["OBSERVATION DATE"], str),
                time_started=row["TIME OBSERVATIONS STARTED"] or None,
                observer_id=row["OBSERVER ID"],
                duration_minutes=safe_cast(row["DURATION MINUTES"], float),
            )
        except Exception as e:
            print(f"Error inserting checklist: {row} - {e}")

# Load sightings CSV
# Load sightings CSV
with open(sightings_csv, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        try:
            # Check for the "X" value and set it to 0
            if row["OBSERVATION COUNT"] == "X":
                observation_count = 0
            else:
                observation_count = safe_cast(row["OBSERVATION COUNT"], int)

            if observation_count is None:
                print(f"Warning: Invalid observation count '{row['OBSERVATION COUNT']}' for {row['COMMON NAME']}. Skipping.")
                continue

            species_record = db(db.species.common_name == row["COMMON NAME"]).select().first()
            if not species_record:
                print(f"Warning: Species '{row['COMMON NAME']}' not found. Skipping.")
                continue

            checklist_record = db(db.checklists.sampling_event_id == row["SAMPLING EVENT IDENTIFIER"]).select().first()
            if not checklist_record:
                print(f"Warning: Checklist with ID '{row['SAMPLING EVENT IDENTIFIER']}' not found. Skipping.")
                continue

            db.sightings.insert(
                sampling_event_id=checklist_record.id,
                common_name=species_record.id,
                observation_count=observation_count,
            )
        except Exception as e:
            print(f"Error inserting sighting: {row} - {e}")

db.commit()

print("CSV data loaded successfully.")