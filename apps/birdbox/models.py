"""
This file defines the database models
"""

import datetime
from .common import db, Field, auth
from pydal.validators import *


def get_user_email():
    return auth.current_user.get('email') if auth.current_user else None

def get_time():
    return datetime.datetime.utcnow()


### Define your table below
#
# db.define_table('thing', Field('name'))
#
## always commit your models to avoid problems later
# Define the Species table
# This table stores the common names of bird species.
db.define_table(
    "species",
    Field("common_name", unique=True, requires=[IS_NOT_EMPTY()]),  # Common name of the bird
)

# Define the Checklists table
# This table stores information about birding events.
db.define_table(
    "checklists",
    Field("sampling_event_id", unique=True, requires=[IS_NOT_EMPTY()]),  # Unique ID for the sampling event
    Field("latitude", "double", requires=[IS_FLOAT_IN_RANGE(-90, 90)]),  # Latitude of the observation
    Field("longitude", "double", requires=[IS_FLOAT_IN_RANGE(-180, 180)]),  # Longitude of the observation
    Field("observation_date", "date", requires=[IS_DATE()]),  # Date of observation
    Field("time_started", "time"),  # Time the observation started
    Field("observer_id", requires=[IS_NOT_EMPTY()]),  # ID of the observer
    Field("duration_minutes", "integer"),  # Duration of the observation in minutes
)

# Define the Sightings table
# This table links species to checklists and records the count of observed birds.
db.define_table(
    "sightings",
    Field("sampling_event_id", "reference checklists", requires=[IS_NOT_EMPTY()]),  # Link to checklists
    Field("common_name", "reference species", requires=[IS_NOT_EMPTY()]),  # Link to species
    Field("observation_count", "integer", requires=[IS_INT_IN_RANGE(1, None)]),  # Count of observed birds
)

# Commit the schema
db.commit()


