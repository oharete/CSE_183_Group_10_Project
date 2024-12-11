"use strict";

// Vue.js application setup
const app = Vue.createApp({
    data() {
        return {
            selectedSpecies: '', // Stores the species selected by the user
            speciesSuggestions: [], // Stores the list of species suggestions for the dropdown
            map: null, // Leaflet map instance
            drawingLayer: null // Layer group for managing drawn shapes
        };
    },
    methods: {
        // Redirects the user to the Checklist page
        goToChecklist() {
            window.location.href = '/checklist';
        },
        // Redirects the user to the User Stats page
        goToStats() {
            window.location.href = '/user_stats';
        },
        // Fetches species suggestions based on user input
        fetchSpecies() {
            axios.get(`/api/species?suggest=${this.selectedSpecies}`) // API call to fetch species suggestions
                .then(response => {
                    this.speciesSuggestions = response.data.species; // Updates the suggestions array with response data
                })
                .catch(error => {
                    console.error('Error fetching species suggestions:', error);
                });
        },
        // Handles selection of a species from the dropdown
        selectSpecies(speciesName) {
            this.selectedSpecies = speciesName; // Updates the selected species
            this.speciesSuggestions = []; // Clears the suggestions dropdown
            this.updateMapWithSpecies(speciesName); // Updates the map to show data for the selected species
        },
        // Updates the map with bird density data for the selected species
        updateMapWithSpecies(species) {
            axios.get(`/api/density?species=${species}`) // API call to fetch bird density data
                .then(response => {
                    const data = response.data.density;
                    // Clear existing map layers (except for the drawing layer)
                    this.map.eachLayer(layer => {
                        if (layer !== this.drawingLayer && layer.options && layer.options.attribution !== undefined) {
                            this.map.removeLayer(layer);
                        }
                    });
                    // Add heatmap or density markers to the map
                    data.forEach(point => {
                        L.circle([point.lat, point.lng], {
                            radius: point.density * 10, // Adjust size based on density
                            color: 'red',
                            fillOpacity: 0.5
                        }).addTo(this.map);
                    });
                })
                .catch(error => {
                    console.error('Error updating map with species data:', error);
                });
        },
        // Displays statistics for the selected map region
        showRegionStats() {
            const bounds = this.drawingLayer.getBounds(); // Get bounds of the drawn rectangle
            if (!bounds.isValid()) {
                alert('Please draw a region on the map first.');
                return;
            }
            // Extract bounds coordinates
            const region = {
                north: bounds.getNorth(),
                south: bounds.getSouth(),
                east: bounds.getEast(),
                west: bounds.getWest()
            };
            axios.post('/api/region_stats', region) // API call to fetch region statistics
                .then(response => {
                    const stats = response.data;
                    console.log('Region statistics:', stats);
                    alert(`Region Stats:\nSpecies Count: ${stats.species_count}\nObservation Count: ${stats.observation_count}`);
                })
                .catch(error => {
                    console.error('Error fetching region statistics:', error);
                });
        },
        // Initializes the Leaflet map and adds necessary controls and layers
        initMap() {
            this.map = L.map('map').setView([37.7749, -122.4194], 10); // Initializes the map with a default center
            L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
                maxZoom: 19,
                attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            }).addTo(this.map); // Adds the OpenStreetMap tile layer

            this.drawingLayer = L.featureGroup().addTo(this.map); // Layer to manage user-drawn shapes

            const drawControl = new L.Control.Draw({
                edit: {
                    featureGroup: this.drawingLayer // Allows editing of drawn shapes
                },
                draw: {
                    rectangle: true // Enables drawing of rectangles on the map
                }
            });
            this.map.addControl(drawControl); // Adds the drawing control to the map

            // Event listener for when a rectangle is created
            this.map.on(L.Draw.Event.CREATED, (event) => {
                const layer = event.layer; // The newly created layer
                this.drawingLayer.addLayer(layer); // Adds the layer to the drawing group
                console.log('Rectangle drawn:', layer.getBounds()); // Logs the bounds of the rectangle
            });
        }
    },
    // Lifecycle hook that runs after the Vue instance is mounted
    mounted() {
        this.initMap(); // Initializes the map after the component is mounted
    }
});

app.mount('#app'); // Mounts the Vue instance to the #app element
