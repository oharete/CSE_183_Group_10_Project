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

@action('api/species', method=['GET'])
@action.uses(db)
def get_species():
    query = request.query.get('suggest', '').strip().lower()
    species = db(db.species.common_name.contains(query)).select().as_list()
    return dict(species=species)


@action('api/density', method=['GET'])
@action.uses(db)
def density():
    # Get the species parameter from the query string
    species = request.query.get('species')

    if species:
        # Fetch density data for the specified species
        rows = db(
            (db.sightings.common_name == db.species.id) &
            (db.species.common_name == species) &
            (db.sightings.sampling_event_id == db.checklists.id)
        ).select(
            db.checklists.latitude, db.checklists.longitude,
            db.sightings.observation_count
        )
    else:
        # Fetch aggregated density data for all species
        rows = db(
            (db.sightings.common_name == db.species.id) &
            (db.sightings.sampling_event_id == db.checklists.id)
        ).select(
            db.checklists.latitude, db.checklists.longitude,
            db.sightings.observation_count
        )

    # Prepare density data
    density_data = []
    for row in rows:
        density_data.append({
            'lat': row.checklists.latitude,
            'lng': row.checklists.longitude,
            'density': row.sightings.observation_count
        })

    # Return the density data
    return dict(density=density_data)




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



# code for location page
@action('api/region_stats', method=["POST"])
@action.uses(db)
def region_stats():
    try:
        # Get region bounds from the request
        data = request.json
        north, south, east, west = data['north'], data['south'], data['east'], data['west']

        # Query for sightings within the region bounds
        sightings = db(
            (db.checklists.latitude <= north) &
            (db.checklists.latitude >= south) &
            (db.checklists.longitude <= east) &
            (db.checklists.longitude >= west)
        ).select()

        # Process the data
        species_stats = {}
        for sighting in sightings:
            checklist_id = sighting.id
            species = db(db.sightings.sampling_event_id == checklist_id).select()
            for s in species:
                species_name = db.species[s.common_name].common_name
                if species_name not in species_stats:
                    species_stats[species_name] = {'sightings': 0, 'checklists': 0}
                species_stats[species_name]['sightings'] += s.observation_count
                species_stats[species_name]['checklists'] += 1

        # Get top contributors
        top_contributors = db(
            (db.checklists.latitude <= north) &
            (db.checklists.latitude >= south) &
            (db.checklists.longitude <= east) &
            (db.checklists.longitude >= west)
        ).select(db.checklists.observer_id, db.checklists.id.count(), groupby=db.checklists.observer_id, orderby=~db.checklists.id.count())

        return dict(
            species_stats=species_stats,
            top_contributors=[{'observer_id': c.observer_id, 'checklists': c['id.count']} for c in top_contributors]
        )
    except Exception as e:
        return dict(error=str(e))
