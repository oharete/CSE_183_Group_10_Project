# """
# This file defines the database models
# """

# import datetime
# from .common import db, Field, auth
# from pydal.validators import *
# import os
# import csv




# def get_user_email():
#     return auth.current_user.get('email') if auth.current_user else None

# def get_time():
#     return datetime.datetime.utcnow()


# ### Define your table below
# #
# # db.define_table('thing', Field('name'))
# #
# ## always commit your models to avoid problems later


# # Define the Species table
# # This table stores the common names of bird species.
# db.define_table(
#     "species",
#     Field("common_name", unique=True, requires=[IS_NOT_EMPTY()]),  # Common name of the bird
# )

# # Define the Checklists table
# # This table stores information about birding events.
# db.define_table(
#     "checklists",
#     Field("sampling_event_id", unique=True, requires=[IS_NOT_EMPTY()]),  # Unique ID for the sampling event
#     Field("latitude", "double", requires=[IS_FLOAT_IN_RANGE(-90, 90)]),  # Latitude of the observation
#     Field("longitude", "double", requires=[IS_FLOAT_IN_RANGE(-180, 180)]),  # Longitude of the observation
#     Field("observation_date", "date", requires=[IS_DATE()]),  # Date of observation
#     Field("time_started", "time"),  # Time the observation started
#     Field("observer_id", requires=[IS_NOT_EMPTY()]),  # ID of the observer
#     # Field("duration_minutes", "integer"),  # Duration of the observation in minutes
#     Field("duration_minutes", "float"),  # Duration of the observation in minutes
# )

# # Define the Sightings table
# # This table links species to checklists and records the count of observed birds.
# db.define_table(
#     "sightings",
#     Field("sampling_event_id", "reference checklists", requires=[IS_NOT_EMPTY()]),  # Link to checklists
#     Field("common_name", "reference species", requires=[IS_NOT_EMPTY()]),  # Link to species
#     Field("observation_count", "integer", requires=[IS_INT_IN_RANGE(1, None)]),  # Count of observed birds
# )

# # Commit the schema
# db.commit()

# # Load species.csv
# # Use relative paths
# base_path = os.path.dirname(__file__)
# # uploads_path = os.path.join(base_path, "apps", "uploads")
# uploads_path = os.path.join(base_path, "uploads")

# species_csv = os.path.join(uploads_path, "species.csv")
# checklist_csv = os.path.join(uploads_path, "checklists.csv")
# sightings_csv = os.path.join(uploads_path, "sightings.csv")

# with open(species_csv, "r") as f:
#     reader = csv.DictReader(f)
#     for row in reader:
#         try:
#             db.species.insert(common_name=row["COMMON NAME"])
#         except Exception as e:
#             print(f"Error inserting species: {row['COMMON NAME']} - {e}")

# # Load checklist.csv
# with open(checklist_csv, "r") as f:
#     reader = csv.DictReader(f, delimiter=",")  # Tab-delimited
#     for row in reader:
#         try:
#             db.checklists.insert(
#                 sampling_event_id=row["SAMPLING EVENT IDENTIFIER"],
#                 latitude=float(row["LATITUDE"]),
#                 longitude=float(row["LONGITUDE"]),
#                 observation_date=row["OBSERVATION DATE"],
#                 time_started=row["TIME OBSERVATIONS STARTED"] or None,
#                 observer_id=row["OBSERVER ID"],
#                 duration_minutes=int(row["DURATION MINUTES"]) if row["DURATION MINUTES"] else None,
#             )
#         except Exception as e:
#             print(f"Error inserting checklist: {row} - {e}")

# # Load sightings.csv
# # with open(sightings_csv, "r") as f:
# #     reader = csv.DictReader(f, delimiter=",")  # Tab-delimited
# #     for row in reader:
# #         try:
# #             db.sightings.insert(
# #                 sampling_event_id=row["SAMPLING EVENT IDENTIFIER"],
# #                 common_name=row["COMMON NAME"],
# #                 observation_count=int(row["OBSERVATION COUNT"]),
# #             )
# #         except Exception as e:
# #             print(f"Error inserting sighting: {row} - {e}")
# with open(sightings_csv, "r", encoding="utf-8") as f:
#     reader = csv.DictReader(f, delimiter=",")  # Comma-delimited
#     for row in reader:
#         try:
#             # Preprocess observation_count
#             observation_count = row["OBSERVATION COUNT"]
#             if observation_count.isdigit():
#                 observation_count = int(observation_count)
#             else:
#                 # observation_count = 0  # or handle appropriately
#                 observation_count=observation_count

#             species_record = db(db.species.common_name == row["COMMON NAME"]).select().first()

#             # Insert into the database
#             db.sightings.insert(
#                 sampling_event_id=row["SAMPLING EVENT IDENTIFIER"],
#                 # common_name=row["COMMON NAME"],
#                 common_name=species_record.id,  
#                 observation_count=observation_count,
#             )
#         except Exception as e:
#             print(f"Error inserting sighting: {row} - {e}")


# db.commit()
# print("CSV data loaded successfully.")


import sqlite3
import pandas as pd

# File paths
checklists_path = '/mnt/data/checklists.csv'
sightings_path = '/mnt/data/sightings.csv'
species_path = '/mnt/data/species.csv'

def load_data_to_db():
    # Connect to SQLite database (or create it if it doesn't exist)
    conn = sqlite3.connect('bird_watch.db')
    cursor = conn.cursor()

    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS checklists (
            sampling_event_id TEXT PRIMARY KEY,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            observation_date TEXT NOT NULL,
            time_observations_started TEXT,
            observer_id TEXT NOT NULL,
            duration_minutes REAL
        );
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sightings (
            sampling_event_id TEXT NOT NULL,
            common_name TEXT NOT NULL,
            observation_count INTEGER NOT NULL,
            FOREIGN KEY (sampling_event_id) REFERENCES checklists(sampling_event_id)
        );
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS species (
            common_name TEXT PRIMARY KEY
        );
    ''')

    # Load CSV files
    checklists_df = pd.read_csv(checklists_path)
    sightings_df = pd.read_csv(sightings_path)
    species_df = pd.read_csv(species_path)

    # Rename columns to match database schema
    checklists_df.rename(columns={
        'SAMPLING EVENT IDENTIFIER': 'sampling_event_id',
        'LATITUDE': 'latitude',
        'LONGITUDE': 'longitude',
        'OBSERVATION DATE': 'observation_date',
        'TIME OBSERVATIONS STARTED': 'time_observations_started',
        'OBSERVER ID': 'observer_id',
        'DURATION MINUTES': 'duration_minutes'
    }, inplace=True)

    sightings_df.rename(columns={
        'SAMPLING EVENT IDENTIFIER': 'sampling_event_id',
        'COMMON NAME': 'common_name',
        'OBSERVATION COUNT': 'observation_count'
    }, inplace=True)

    species_df.rename(columns={
        'COMMON NAME': 'common_name'
    }, inplace=True)

    # Handle data type conversion
    checklists_df['latitude'] = pd.to_numeric(checklists_df['latitude'], errors='coerce')
    checklists_df['longitude'] = pd.to_numeric(checklists_df['longitude'], errors='coerce')
    checklists_df['duration_minutes'] = pd.to_numeric(checklists_df['duration_minutes'], errors='coerce')

    sightings_df['observation_count'] = pd.to_numeric(sightings_df['observation_count'], errors='coerce').fillna(0).astype(int)

    # Insert data into tables
    checklists_df.to_sql('checklists', conn, if_exists='replace', index=False)
    sightings_df.to_sql('sightings', conn, if_exists='replace', index=False)
    species_df.to_sql('species', conn, if_exists='replace', index=False)

    # Commit changes and close connection
    conn.commit()
    conn.close()

# Execute the function
load_data_to_db()
