"use strict";

const app = Vue.createApp({
  data() {
    return {
      map: null, // Leaflet map instance
      drawingLayer: null, // Layer group for user-drawn shapes
      heatLayer: null, // Heatmap layer instance
      selectedSpecies: '', // User's selected species
      speciesSuggestions: [], // Suggestions for species
      loadingHeatmap: false, // Show loading indicator while heatmap is being updated

      // For checklist page
      searchQuery: "", // Search bar input
      species: [], // Full list of species fetched from the server
      filteredSpecies: [], // Filtered species list based on the search query
    };
  },
  methods: {
    initMap() {
      // Initialize the map with a default location in case geolocation fails
      this.map = L.map('map').setView([36.9905, -122.0584], 10);
      console.log("Map initialized with default location.");
      L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
        attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>',
      }).addTo(this.map);

      // Add drawing layer
      this.drawingLayer = L.featureGroup().addTo(this.map);
      const drawControl = new L.Control.Draw({
        edit: { featureGroup: this.drawingLayer },
        draw: { rectangle: true },
      });
      this.map.addControl(drawControl);

      // Event listener for rectangle creation
      this.map.on(L.Draw.Event.CREATED, (event) => {
        const layer = event.layer;
        this.drawingLayer.clearLayers(); // Clear existing shapes
        this.drawingLayer.addLayer(layer); // Add the new rectangle
      });
    },
    centerMapOnUser() {
      if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
          (position) => {
            const { latitude, longitude } = position.coords;
            console.log("User's location:", { latitude, longitude });
            this.map.setView([latitude, longitude], 10); // Center map on user's location
          },
          (error) => {
            console.error("Geolocation error:", error);
            alert(
              "Unable to retrieve your location. The map will remain on the default region."
            );
          }
        );
      } else {
        console.error("Geolocation is not supported by your browser.");
        alert("Geolocation is not supported by your browser.");
      }
    },    
    updateHeatmap(data) {
      // Remove existing heatmap layer, if any
      if (this.heatLayer) {
        this.map.removeLayer(this.heatLayer);
      }

      // Convert density data to a format usable by Leaflet.heat
      const heatData = data.map((point) => [point.lat, point.lng, point.density]);
      this.heatLayer = L.heatLayer(heatData, {
        radius: 25,
        blur: 15,
        maxZoom: 17,
      }).addTo(this.map);
    },
    fetchDensity() {
      // Fetch density data for the selected species or all species
      const speciesQuery = this.selectedSpecies
        ? `?species=${encodeURIComponent(this.selectedSpecies)}`
        : '';
      axios
        .get(`/api/density${speciesQuery}`)
        .then((response) => {
          if (response.data.density && response.data.density.length > 0) {
            this.updateHeatmap(response.data.density);
          } else {
            alert(
              this.selectedSpecies
                ? `No density data available for species: ${this.selectedSpecies}.`
                : 'No density data available for all species.'
            );
          }
        })
        .catch((error) => {
          console.error('Error fetching density data:', error);
        });
    },
    fetchSpecies() {
      if (this.selectedSpecies.trim() === "") {
        // Clear suggestions if the search box is empty
        this.speciesSuggestions = [];
        return;
      }

      axios
        .get(`/api/species?suggest=${this.selectedSpecies}`)
        .then((response) => {
          this.speciesSuggestions = response.data.species.map((s) => ({
            id: s.id,
            name: s.common_name,
          }));
        })
        .catch((error) => {
          console.error("Error fetching species suggestions:", error);
        });
    },
    selectSpecies(speciesName) {
      // Handle species selection
      this.selectedSpecies = speciesName;
      this.speciesSuggestions = [];
      this.fetchDensity(); // Update heatmap with selected species
    },

    // Redirect to the Location page
    showRegionStats() {
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

      // Redirect to the Location Page with region bounds as query parameters
      const queryParams = new URLSearchParams(region).toString();
      window.location.href = `/location?${queryParams}`;
    },

    // Redirect to the Checklist page
    goToChecklist() {
      window.location.href = "/checklist";
    }, 

    // Redirect to the Stats page
    goToStats() {
      window.location.href = "/user_stats"; // maybe change if iian needs 
    },

    // For checklist
    fetchSpeciesChecklist() {
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
    this.centerMapOnUser();
    this.fetchDensity(); // Load heatmap for all species by default
  },
});

app.mount('#app');
 