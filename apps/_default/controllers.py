"""
This file defines actions, i.e. functions the URLs are mapped into
The @action(path) decorator exposed the function at URL:

    http://127.0.0.1:8000/{app_name}/{path}

If app_name == '_default' then simply

    http://127.0.0.1:8000/{path}

If path == 'index' it can be omitted:

    http://127.0.0.1:8000/

The path follows the bottlepy syntax.

@action.uses('generic.html')  indicates that the action uses the generic.html template
@action.uses(session)         indicates that the action uses the session
@action.uses(db)              indicates that the action uses the db
@action.uses(T)               indicates that the action uses the i18n & pluralization
@action.uses(auth.user)       indicates that the action requires a logged in user
@action.uses(auth)            indicates that the action requires the auth object

session, db, T, auth, and tempates are examples of Fixtures.
Warning: Fixtures MUST be declared with @action.uses({fixtures}) else your app will result in undefined behavior
"""

from py4web import action, request, abort, redirect, URL
from yatl.helpers import A
from .common import db, session, T, cache, auth, logger, authenticated, unauthenticated, flash, Field
from py4web.utils.url_signer import URLSigner
from .models import get_user_email

import datetime

import json
from py4web.core import HTTP
import uuid
import datetime


url_signer = URLSigner(session)

@action('index')
@action.uses('index.html', db, auth)
def index():
    return dict()

@action("api/species", method=["GET"])
@action.uses(db)
def api_species():
    suggest = request.query.get("suggest", "").strip().lower()
    species = db(db.species.common_name.lower().contains(suggest)).select().as_list()
    return dict(species=species)

@action("api/density", method=["GET"])
@action.uses(db)
def api_density():
    try:
        # Get the species name from the query parameter
        species_name = request.query.get("species", "").strip()
        
        if not species_name:
            print("Warning: 'species' query parameter is missing or empty.")
            return dict(error="The 'species' query parameter is required.")
        
        # Fetch the species ID from the species table
        species_row = db(db.species.common_name == species_name).select().first()
        if not species_row:
            print(f"No species found for name: {species_name}")
            return dict(density=[])

        # Query sightings and join with checklists for relevant data
        rows = db(
            (db.sightings.common_name == species_row.id) &
            (db.sightings.sampling_event_id == db.checklists.id)
        ).select(
            db.checklists.latitude,
            db.checklists.longitude,
            db.sightings.observation_count
        )
        
        if not rows:
            print(f"No sightings found for species: {species_name}")
            return dict(density=[])

        # Construct the density response
        density_data = [
            {
                "lat": row.checklists.latitude,
                "lng": row.checklists.longitude,
                "density": row.sightings.observation_count,
            }
            for row in rows
            if row.checklists.latitude is not None and
               row.checklists.longitude is not None and
               row.sightings.observation_count is not None
        ]

        print(f"Density data retrieved for species: {species_name}, count: {len(density_data)}")
        return dict(density=density_data)

    except Exception as e:
        print(f"Error processing /api/density request: {str(e)}")
        raise HTTP(500, f"Internal Server Error: {str(e)}")

@action("api/region_stats", method=["GET"])
@action.uses(db)
def api_region_stats():
    try:
        # Get region boundaries from query parameters
        north = float(request.query.get("north"))
        south = float(request.query.get("south"))
        east = float(request.query.get("east"))
        west = float(request.query.get("west"))

        # Validate inputs
        if not (south <= north and west <= east):
            return dict(error="Invalid region boundaries.")

        # Query sightings within the region
        rows = db(
            (db.checklists.latitude <= north) &
            (db.checklists.latitude >= south) &
            (db.checklists.longitude <= east) &
            (db.checklists.longitude >= west) &
            (db.sightings.sampling_event_id == db.checklists.id)
        ).select(
            db.sightings.common_name,
            db.sightings.observation_count.sum().with_alias("total_observations"),
            groupby=db.sightings.common_name
        )

        # Prepare response data
        species_stats = [
            {
                "common_name": row.sightings.common_name,
                "total_observations": row.total_observations,
            }
            for row in rows
        ]

        return dict(
            total_species=len(species_stats),
            species_stats=species_stats,
        )

    except Exception as e:
        print(f"Error processing /api/region_stats request: {str(e)}")
        raise HTTP(500, f"Internal Server Error: {str(e)}")


@action('test')
@action.uses('test.html')
def test():
    return dict()


@action('location')
@action.uses('location.html')
def species():
    return dict()  

@action('checklist')
@action.uses('checklist.html', db)
def checklists():
    return dict( 
        get_species_url=URL("get_species"),
        save_checklist_url=URL("save_checklist"),
    )  

#for checklist html
#an endpoint to retrieve species filtered by the search query.
@action("get_species", method=["GET"])
@action.uses(db, auth)
def get_species():
    query = request.query.get("query", "").strip().lower()
    print(f"Received query: {query}")
    species = db(db.species.common_name.contains(query)).select().as_list()
    return dict(species=species)

# an endpoint to save the checklist to the database.
@action("save_checklist", method=["POST"])
@action.uses(db, auth)
def save_checklist():
    # Check if the user is logged in
    
    #if not auth.current_user:
    #    return "Please log in to submit your checklist."  # Message if not logged in
    
    data = request.json
    checklist_id = data.get("checklist_id")  # For updates
    species_data = data.get("species", [])  # Array of species and counts
    print("im in save_checklist")
    print(species_data)
    
    if checklist_id:
        # If the checklist_id is provided, update the existing checklist record
        checklist = db.checklists[checklist_id]
        if not checklist:
            raise HTTP(404, "Checklist not found.")
        checklist.update_record(
            observation_date=datetime.datetime.utcnow()
        )
        # Remove all related sightings for the checklist, if any
        db(db.sightings.sampling_event_id == checklist_id).delete()
    else:
        # Insert a new checklist record without using uuid, instead using auto-incremented ID
        checklist_id = db.checklists.insert(
            latitude=0,  # Placeholder latitude value
            longitude=0,  # Placeholder longitude value
            observation_date=datetime.datetime.utcnow(),
            observer_id=auth.current_user.get("email"),
        )

    # Insert all species data related to this checklist
    for item in species_data:
        # Look up species_id based on common_name
        species_row = db(db.species.common_name == item["common_name"]).select().first()
        
        if species_row:
            species_id = species_row.id  # Use species_id (integer)
        else:
            raise HTTP(400, f"Species {item['common_name']} not found.")
        
        db.sightings.insert(
            sampling_event_id=checklist_id,  # Linking sighting to the checklist by its ID
            species_id=species_id,  # Insert the species_id instead of common_name
            observation_count=item["count"],
        )

    return dict(status="success", checklist_id=checklist_id)

#Create an endpoint to retrieve submitted checklists.
@action("get_checklists", method=["GET"])
@action.uses(db, auth)
def get_checklists():
    checklists = db(db.checklists.observer_id == auth.current_user.get("email")).select().as_list()
    return dict(checklists=checklists)



@action('user_stats')
@action.uses('user_stats.html')
def user_stats():
    return dict()  

@action("api/user_stats/species", method=["GET"])
@action.uses(db, auth)
def user_stats_species():
    user_id = auth.current_user.get("email")
    species = db(
        (db.checklists.observer_id == user_id) &
        (db.sightings.sampling_event_id == db.checklists.id) &
        (db.sightings.common_name == db.species.id)
    ).select(db.species.common_name, distinct=True).as_list()
    return dict(species=[s["common_name"] for s in species])
#iain
@action("api/user_stats/trends", method=["GET"])
@action.uses(db, auth)
def user_stats_trends():
    user_id = auth.current_user.get("email")
    trends = db(
        (db.checklists.observer_id == user_id)
    ).select(
        db.checklists.observation_date,
        db.sightings.observation_count.sum(),
        groupby=db.checklists.observation_date
    ).as_list()
    return dict(trends=[
        {"date": t["observation_date"], "count": t["_extra"]["SUM(sightings.observation_count)"]}
        for t in trends
    ])
