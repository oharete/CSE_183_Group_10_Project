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
from py4web.core import HTTP
from py4web.utils.grid import Grid, GridClassStyleBulma
from py4web.utils.form import Form, FormStyleBulma
from yatl.helpers import A
from .common import (
    db, session, T, cache, auth, logger, authenticated,
    unauthenticated, flash, Field
)
from .models import get_user_email

import datetime
import json
import uuid
import random


@action('index')
@action.uses('index.html', db, auth)
def index():
    # Render the index.html template and provide access to the database (db) and authentication (auth) services
    return dict()

@action('api/species', method=['GET'])
@action.uses(db)
def get_species():
    # Get the 'suggest' query parameter from the request, stripping whitespace and converting it to lowercase
    query = request.query.get('suggest', '').strip().lower()

    # Query the database for species whose common names contain the search query
    species = db(db.species.common_name.contains(query)).select().as_list()

    # Return the matching species as a dictionary
    return dict(species=species)

@action('api/density', method=['GET'])
@action.uses(db)
def density():
    # Retrieve the 'species' parameter from the query string
    species = request.query.get('species')

    if species:
        # Fetch density data for the specified species
        rows = db(
            (db.sightings.common_name == db.species.id) &  # Match species ID in sightings and species tables
            (db.species.common_name == species) &          # Filter by the specified species name
            (db.sightings.sampling_event_id == db.checklists.id)  # Match sampling event IDs in sightings and checklists
        ).select(
            db.checklists.latitude,  # Latitude of the sightings
            db.checklists.longitude, # Longitude of the sightings
            db.sightings.observation_count # Observation count for the sightings
        )
    else:
        # Fetch aggregated density data for all species
        rows = db(
            (db.sightings.common_name == db.species.id) &  # Match species ID in sightings and species tables
            (db.sightings.sampling_event_id == db.checklists.id)  # Match sampling event IDs in sightings and checklists
        ).select(
            db.checklists.latitude,  # Latitude of the sightings
            db.checklists.longitude, # Longitude of the sightings
            db.sightings.observation_count # Observation count for the sightings
        )

    # Prepare density data for response
    density_data = []
    for row in rows:
        # Append each sighting's data to the density_data list
        density_data.append({
            'lat': row.checklists.latitude,  # Latitude of the sighting
            'lng': row.checklists.longitude, # Longitude of the sighting
            'density': row.sightings.observation_count  # Observation count (density)
        })

    # Return the density data as a dictionary
    return dict(density=density_data)

@action('get_random_bird', method=['GET'])
@action.uses(db)
def get_random_bird():
    rows = db(db.species).select()
    if rows:
        random_bird = random.choice(rows)
        return dict(common_name=random_bird.common_name)
    else:
        return dict(error="No birds found")



@action('location')
@action.uses('location.html')
def species():
    return dict()  

@action('checklist')
@action.uses('checklist.html', db, auth, session)
def checklists():
    return dict( 
        get_species_url=URL("get_species"),
        save_checklist_url=URL("save_checklist"),
    )  

#for checklist html
#an endpoint to retrieve species filtered by the search query.
@action("get_species", method=["GET"])
@action.uses(db, auth, session)
def get_species():
    query = request.query.get("query", "").strip().lower()
    print(f"Received query: {query}")
    species = db(db.species.common_name.contains(query)).select().as_list()
    return dict(species=species)

@action("save_checklist", method=["POST"])
@action.uses(db, auth, session)
def save_checklist():
    # Check if the user is logged in
    if not auth.current_user:
        raise HTTP(403, "Please log in to submit your checklist.")  # Unauthorized if not logged in

    data = request.json
    checklist_id = data.get("checklist_id")  # For updates
    species_data = data.get("species", [])  # Array of species and counts
    print("this is species_data", species_data)
    
    # Validate that species_data is not empty
    if not species_data:
        raise HTTP(400, "Species data is required.")  # Bad Request if no species data provided
    
    if checklist_id:
        # If the checklist_id is provided, update the existing checklist record
        checklist = db.checklists.get(checklist_id)
        if not checklist:
            raise HTTP(404, "Checklist not found.")
        
        # Update the checklist observation date and observer ID (if needed)
        checklist.update_record(
            observation_date=datetime.datetime.utcnow(),
            observer_id=auth.current_user.get("email"),
        )
        
        # Remove all related sightings for the checklist (if any)
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

    # Insert a record in the user_checklists table to associate the checklist with the user
    user_email = auth.current_user.get("email")  # Get the logged-in user's email
    for item in species_data:
        print("this is item ", item)
        species_row = db(db.species.common_name == item["common_name"]).select().first()
        if species_row:
            species_id = species_row.id  # Use species_id (integer)
        else:
            raise HTTP(400, f"Species {item['common_name']} not found.")
        
        # Insert species_id instead of common_name in user_checklists table
        db.user_checklists.insert(
            user_email=user_email,
            checklist_id=checklist_id,
            species_id=species_id,  # Save species_id, not common_name
            observation_count=item["count"],  # Observation count
        )

    return dict(status="success", checklist_id=checklist_id)

@action("my_checklist")
@action.uses("my_checklist.html", db, session, auth)
def my_checklist():
    # Make sure the user is logged in
    if not auth.current_user:
        raise HTTP(403, "You must be logged in to view your checklists.")
    
    user_email = auth.current_user.get('email')
    
    # Select checklists associated with the current user
    checklists = db(db.user_checklists.user_email == user_email).select()
    
    checklist_items = []
    for user_checklist in checklists:
        # Get the checklist data from the checklists table
        checklist = db.checklists[user_checklist.checklist_id]
        
        # Retrieve the species based on species_id from the species table
        species = db(db.species.id == user_checklist.species_id).select().first()
        
        if species:
            common_name = species.common_name
        else:
            common_name = "Unknown species"  # Fallback if species is not found
        
        # Add the relevant fields to display, including the user_observation_count
        checklist_items.append({
            'sampling_event_id': checklist.sampling_event_id,
            'latitude': checklist.latitude,
            'longitude': checklist.longitude,
            'observation_date': checklist.observation_date,
            'common_name': common_name,  # Retrieved from species table
            'user_observation_count': user_checklist.observation_count,  # Fetch from user_checklists
        })
    
    return dict(checklist_items=checklist_items)

#also Iain
@action('user_stats')
@action.uses('user_stats.html')
def user_stats():
    return dict()  


#iain
@action("api/user_stats/species", method=["GET"])
@action.uses(db)
def user_stats_species():
    query = request.query.get("suggest", "").strip().lower()
    species = db(db.species.common_name.lower().contains(query)).select(db.species.common_name).as_list()
    return dict(species=species)



@action("api/user_stats/trends", method=["GET"])
@action.uses(db)
def user_stats_trends():
    species_name = request.query.get("species", "").strip()

    if not species_name:
        return dict(error="Species name is required.", trends=[])

    # Validate the species name exists in the database
    species_row = db(db.species.common_name == species_name).select().first()
    if not species_row:
        return dict(error="Species not found.", trends=[])

    # Query trends for the specified species
    trends = db(
        (db.sightings.common_name == species_row.id) &
        (db.sightings.sampling_event_id == db.checklists.id)
    ).select(
        db.checklists.observation_date,
        db.sightings.observation_count.sum().with_alias("total_count"),
        groupby=db.checklists.observation_date
    )

    return dict(trends=[
        {"date": str(trend["checklists.observation_date"]), "count": trend["total_count"]}
        for trend in trends
    ])






# code for location page
@action('api/region_stats', method=["POST"])
@action.uses(db)
def region_stats():
    try:
        # Get region bounds from the request
        data = request.json
        north, south, east, west = data['north'], data['south'], data['east'], data['west']
        logger.info(f"Received bounds: north={north}, south={south}, east={east}, west={west}")

        # Query for sightings within the region bounds
        sightings = db(
            (db.checklists.latitude <= north) &
            (db.checklists.latitude >= south) &
            (db.checklists.longitude <= east) &
            (db.checklists.longitude >= west) &
            (db.sightings.sampling_event_id == db.checklists.id) &
            (db.sightings.common_name == db.species.id)  # Corrected field name
        ).select(
            db.species.common_name,
            db.sightings.observation_count,
            db.checklists.id
        )

        # Process the data
        species_stats = {}
        for sighting in sightings:
            species_name = sighting.species.common_name
            checklist_id = sighting.checklists.id
            if species_name not in species_stats:
                species_stats[species_name] = {'sightings': 0, 'checklists': set()}
            species_stats[species_name]['sightings'] += sighting.sightings.observation_count
            species_stats[species_name]['checklists'].add(checklist_id)

        # Convert checklists set to counts
        for species in species_stats:
            species_stats[species]['checklists'] = len(species_stats[species]['checklists'])

        # Get top contributors
        top_contributors = db(
            (db.checklists.latitude <= north) &
            (db.checklists.latitude >= south) &
            (db.checklists.longitude <= east) &
            (db.checklists.longitude >= west)
        ).select(
            db.checklists.observer_id,
            db.checklists.id.count().with_alias("checklist_count"),
            groupby=db.checklists.observer_id,
            orderby=~db.checklists.id.count()
        )

        # Prepare response
        response = dict(
            species_stats=species_stats,
            top_contributors=[
                {'observer_id': c.checklists.observer_id, 'checklists': c.checklist_count}
                for c in top_contributors
            ]
        )

        logger.info(f"Region stats computed successfully: {response}")
        return response

    except Exception as e:
        logger.error(f"Error in region_stats: {e}")
        return dict(error=f"Error: {e}")

#graph for locations page
@action('api/species_graph', method=["GET"])
@action.uses(db)
def species_graph():
    # Get the species name from the query parameters
    species_name = request.query.get("species")
    
    if not species_name:
        return dict(error="Species parameter is missing.")

    # Find the species ID for the given species name
    species_row = db(db.species.common_name == species_name).select().first()
    if not species_row:
        return dict(error=f"Species '{species_name}' not found.")

    # Query the database for sightings trends
    trends = db(
        (db.sightings.common_name == species_row.id) &
        (db.sightings.sampling_event_id == db.checklists.id)
    ).select(
        db.checklists.observation_date,
        db.sightings.observation_count.sum().with_alias("total_count"),
        groupby=db.checklists.observation_date
    )

    # Process the data into the format expected by the frontend
    graph_data = [
        {"date": str(trend["checklists.observation_date"]), "count": trend["total_count"]}
        for trend in trends
    ]

    return dict(data=graph_data)

