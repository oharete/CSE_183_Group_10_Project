"use strict";

const app = Vue.createApp({
  data() {
    return {
      map: null, // Leaflet map instance
      selectedSpecies: '', // User's selected species
      speciesSuggestions: [], // Suggestions for species
    };
  },
  methods: {
    initMap() {
      // Initialize the map
      this.map = L.map('map').setView([37.7749, -122.4194], 10);
      L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>',
      }).addTo(this.map);
    },
    fetchSpecies() {
      // Fetch species suggestions (mocked here; replace with actual API call)
      axios
        .get(`/api/species?suggest=${this.selectedSpecies}`)
        .then((response) => {
          this.speciesSuggestions = response.data.species || []; // Update suggestions
        })
        .catch((error) => {
          console.error('Error fetching species suggestions:', error);
        });
    },
    selectSpecies(speciesName) {
      // Handle species selection
      this.selectedSpecies = speciesName;
      this.speciesSuggestions = []; // Clear suggestions
      this.updateMapWithSpecies(speciesName); // Update the map
    },
    updateMapWithSpecies(species) {
      // Fetch and display density data for the selected species (mocked here)
      axios
        .get(`/api/density?species=${species}`)
        .then((response) => {
          const data = response.data.density;
          // Clear existing map layers except the tile layer
          this.map.eachLayer((layer) => {
            if (layer instanceof L.Marker || layer instanceof L.Circle) {
              this.map.removeLayer(layer);
            }
          });
          // Add density markers
          data.forEach((point) => {
            L.circle([point.lat, point.lng], {
              radius: point.density * 10, // Adjust radius based on density
              color: 'red',
              fillOpacity: 0.5,
            }).addTo(this.map);
          });
        })
        .catch((error) => {
          console.error('Error updating map with species data:', error);
        });
    },
  },
  mounted() {
    this.initMap(); // Initialize the map
  },
});

app.mount('#app');
