"use strict";

const app = Vue.createApp({
    data() {
        return {
            selectedSpecies: '',
            speciesSuggestions: [],
            map: null,
            drawingLayer: null,
            rectangle: null,
        };
    },
    methods: {
        // Fetch species suggestions for autocomplete
        fetchSpecies() {
            axios.get(`/api/species?suggest=${this.selectedSpecies}`)
                .then(response => {
                    this.speciesSuggestions = response.data.species;
                })
                .catch(error => {
                    console.error('Error fetching species suggestions:', error);
                });
        },
        // Handle species selection
        selectSpecies(speciesName) {
            this.selectedSpecies = speciesName;
            this.speciesSuggestions = [];
            this.updateMapWithSpecies(speciesName);
        },
        // Update map with density for the selected species
        updateMapWithSpecies(species) {
            axios.get(`/api/density?species=${species}`)
                .then(response => {
                    const data = response.data.density;
                    this.map.eachLayer(layer => {
                        if (layer !== this.drawingLayer && layer.options && layer.options.attribution !== undefined) {
                            this.map.removeLayer(layer);
                        }
                    });
                    data.forEach(point => {
                        L.circle([point.lat, point.lng], {
                            radius: point.density * 10,
                            color: 'red',
                            fillOpacity: 0.5,
                        }).addTo(this.map);
                    });
                })
                .catch(error => {
                    console.error('Error updating map with species data:', error);
                });
        },
        // Show statistics for the selected region
        showRegionStats() {
            if (!this.rectangle) {
                alert('Please draw a region on the map first.');
                return;
            }
            const bounds = this.rectangle.getBounds();
            const region = {
                north: bounds.getNorth(),
                south: bounds.getSouth(),
                east: bounds.getEast(),
                west: bounds.getWest(),
            };
            axios.post('/api/region_stats', region)
                .then(response => {
                    const stats = response.data;
                    alert(`Region Stats:\nSpecies Count: ${stats.species_count}\nObservation Count: ${stats.observation_count}`);
                })
                .catch(error => {
                    console.error('Error fetching region statistics:', error);
                });
        },
        // Initialize the map
        initMap() {
            try {
                this.map = L.map('map').setView([37.7749, -122.4194], 10);
                L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
                    maxZoom: 19,
                    attribution: '&copy; OpenStreetMap contributors',
                }).addTo(this.map);

                this.drawingLayer = L.featureGroup().addTo(this.map);

                const drawControl = new L.Control.Draw({
                    edit: {
                        featureGroup: this.drawingLayer,
                    },
                    draw: {
                        rectangle: true,
                    },
                });
                this.map.addControl(drawControl);

                this.map.on(L.Draw.Event.CREATED, (event) => {
                    if (this.rectangle) {
                        this.drawingLayer.clearLayers();
                    }
                    this.rectangle = event.layer;
                    this.drawingLayer.addLayer(this.rectangle);
                    console.log('Rectangle drawn:', this.rectangle.getBounds());
                });
            } catch (error) {
                console.error('Error initializing the map:', error);
            }
        },
    },
    mounted() {
        this.initMap();
    },
});

app.mount('#app');
