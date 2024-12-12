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

# @action("api/density", method=["GET"])
# @action.uses(db)
# def get_density():
#     species = request.query.get("species", "").strip().lower()
#     if not species:
#         return dict(density=[])  # No species provided, return empty density

#     # Query the database for the species
#     species_record = db(db.species.common_name.lower() == species).select().first()
#     if not species_record:
#         return dict(density=[])  # Species not found

#     # Get all sightings of the species
#     sightings = db(db.sightings.common_name == species_record.id).select()

#     # Prepare density data
#     density_data = []
#     for sighting in sightings:
#         checklist = db.checklists(sampling_event_id=sighting.sampling_event_id)
#         if checklist:
#             density_data.append({
#                 "lat": checklist.latitude,
#                 "lng": checklist.longitude,
#                 "density": sighting.observation_count
#             })

#     return dict(density=density_data)

# # @action("api/density", method=["GET"])
# # @action.uses(db)
# # def get_density():
# #     species = request.query.get("species", "").strip().lower()
# #     if not species:
# #         return dict(density=[])  # No species provided, return empty density

# #     # Debug: Log the incoming species
# #     print(f"Requested species: {species}")

# #     # Query the database for the species
# #     species_record = db(db.species.common_name.lower() == species).select().first()
# #     if not species_record:
# #         print("Species not found in the database.")
# #         return dict(density=[])  # Species not found

# #     # Debug: Log the species ID
# #     print(f"Species found: {species_record}")

# #     # Get all sightings of the species
# #     sightings = db(db.sightings.common_name == species_record.id).select()
# #     if not sightings:
# #         print("No sightings found for this species.")
# #         return dict(density=[])

# #     # Debug: Log the sightings
# #     print(f"Sightings found: {sightings}")

# #     # Prepare density data
# #     density_data = []
# #     for sighting in sightings:
# #         checklist = db.checklists(sampling_event_id=sighting.sampling_event_id)
# #         if checklist:
# #             density_data.append({
# #                 "lat": checklist.latitude,
# #                 "lng": checklist.longitude,
# #                 "density": sighting.observation_count
# #             })

# #     # Debug: Log the density data
# #     print(f"Density data: {density_data}")

# #     return dict(density=density_data)


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

@action("debug_sightings", method=["GET"])
@action.uses(db)
def debug_sightings():
    sightings = db(db.sightings).select().as_list()
    return dict(sightings=sightings)


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
@action.uses(db)
def get_species():
    query = request.query.get("query", "").strip().lower()
    print(f"Received query: {query}")
    species = db(db.species.common_name.contains(query)).select().as_list()
    return dict(species=species)

# an endpoint to save the checklist to the database.
@action("save_checklist", method=["POST"])
@action.uses(db, auth)
def save_checklist():
    data = request.json
    checklist_id = data.get("checklist_id")  # For updates
    species_data = data.get("species", [])  # Array of species and counts

    if checklist_id:
        checklist = db.checklists[checklist_id]
        if not checklist:
            raise HTTP(404, "Checklist not found.")
        checklist.update_record(
            observation_date=datetime.datetime.utcnow()
        )
        db(db.sightings.sampling_event_id == checklist_id).delete()
    else:
        checklist_id = db.checklists.insert(
            sampling_event_id=str(uuid.uuid4()),
            latitude=0,  # Placeholder
            longitude=0,  # Placeholder
            observation_date=datetime.datetime.utcnow(),
            observer_id=auth.current_user.get("email"),
        )

    for item in species_data:
        db.sightings.insert(
            sampling_event_id=checklist_id,
            common_name=item["common_name"],
            observation_count=item["count"],
        )

    return dict(status="success", checklist_id=checklist_id)

#Create an endpoint to retrieve submitted checklists.
@action("get_checklists", method=["GET"])
@action.uses(db, auth)
def get_checklists():
    checklists = db(db.checklists.observer_id == auth.current_user.get("email")).select().as_list()
    return dict(checklists=checklists)

#delete a checklist
@action("delete_checklist/<checklist_id>", method=["DELETE"])
@action.uses(db, auth)
def delete_checklist(checklist_id):
    checklist = db.checklists[checklist_id]
    if not checklist:
        raise HTTP(404, "Checklist not found.")
    db(db.sightings.sampling_event_id == checklist_id).delete()
    db(db.checklists.id == checklist_id).delete()
    return dict(status="success")

@action('user_stats')
@action.uses('user_stats.html')
def user_stats():
    return dict()  

