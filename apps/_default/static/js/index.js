"use strict";

const app = Vue.createApp({
  data() {
    return {
      map: null, // Leaflet map instance
      drawingLayer: null, // Layer group for user-drawn shapes
      selectedSpecies: '', // User's selected species
      speciesSuggestions: [], // Suggestions for species

      //for checklist page
      searchQuery: "", // Search bar input
      species: [], // Full list of species fetched from the server
      filteredSpecies: [], // Filtered species list based on the search query
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

      // Add a drawing layer
      this.drawingLayer = L.featureGroup().addTo(this.map);

      // Add drawing controls
      const drawControl = new L.Control.Draw({
        edit: { featureGroup: this.drawingLayer },
        draw: { rectangle: true },
      });
      this.map.addControl(drawControl);

      // Event listener for when a rectangle is created
      this.map.on(L.Draw.Event.CREATED, (event) => {
        const layer = event.layer;
        this.drawingLayer.clearLayers(); // Remove previous shapes
        this.drawingLayer.addLayer(layer); // Add the new rectangle
      });
    },
    showRegionStats() {
      // Get the bounds of the drawn rectangle
      const layers = this.drawingLayer.getLayers();
      if (layers.length === 0) {
        alert('Please draw a region on the map first.');
        return;
      }
      const bounds = layers[0].getBounds();
      const region = {
        north: bounds.getNorth(),
        south: bounds.getSouth(),
        east: bounds.getEast(),
        west: bounds.getWest(),
      };

      // Fetch and display region statistics (mocked here; replace with API call)
      axios
        .post('/api/region_stats', region)
        .then((response) => {
          const stats = response.data;
          alert(
            `Region Stats:\nSpecies Count: ${stats.species_count}\nObservation Count: ${stats.observation_count}`
          );
        })
        .catch((error) => {
          console.error('Error fetching region statistics:', error);
        });
    },
    fetchSpecies() {
      // Fetch species suggestions (same as before)
      axios
        .get(`/api/species?suggest=${this.selectedSpecies}`)
        .then((response) => {
          this.speciesSuggestions = response.data.species || [];
        })
        .catch((error) => {
          console.error('Error fetching species suggestions:', error);
        });
    },
    selectSpecies(speciesName) {
      // Handle species selection (same as before)
      this.selectedSpecies = speciesName;
      this.speciesSuggestions = [];
      this.updateMapWithSpecies(speciesName);
    },
    updateMapWithSpecies(species) {
      // Update map with species data (same as before)
      axios
        .get(`/api/density?species=${species}`)
        .then((response) => {
          const data = response.data.density;
          this.map.eachLayer((layer) => {
            if (layer instanceof L.Circle) {
              this.map.removeLayer(layer);
            }
          });
          data.forEach((point) => {
            L.circle([point.lat, point.lng], {
              radius: point.density * 10,
              color: 'red',
              fillOpacity: 0.5,
            }).addTo(this.map);
          });
        })
        .catch((error) => {
          console.error('Error updating map with species data:', error);
        });
    },
    //for checklist
    fetchSpeciesChecklist() {
      // Fetch species filtered by the search query
      console.log("am i here?")
      fetch(`${get_species_url}?query=${encodeURIComponent(this.searchQuery)}`)
        .then((response) => response.json())
        .then((data) => {
          this.filteredSpecies = data.species.map((item) => ({
            ...item,
            count: 0, // Initialize count for each species
          }));
        })
        .catch((error) => {
          console.error("Error fetching species:", error);
        });
    },
    incrementCount(species) {
      species.count += 1; // Increment count
    },
    decrementCount(species) {
      if (species.count > 0) {
        species.count -= 1; // Decrement count
      }
    },
    submitChecklist() {
      const species = this.filteredSpecies.filter((s) => s.count > 0); // Only species with a count > 0
      fetch("/save_checklist", {
          method: "POST",
          headers: {
              "Content-Type": "application/json",
          },
          body: JSON.stringify({ species }),
      })
          .then((response) => response.json())
          .then((data) => {
              if (data.status === "success") {
                  alert("Checklist submitted successfully!");
                  this.clearChecklist(); // Reset the checklist after submission
              } else {
                  alert(`Error: ${data.message}`);
              }
          })
          .catch((error) => {
              console.error("Error submitting checklist:", error);
          });
  },
  clearChecklist() {
      this.filteredSpecies.forEach((s) => (s.count = 0)); // Reset counts
  },
  },
  mounted() {
    this.initMap();
  },
});

app.mount('#app');
