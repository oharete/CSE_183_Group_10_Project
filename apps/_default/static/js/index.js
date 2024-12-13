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
      randomBird: null,
      error: null,

      userStatsData: { //Iain work start
        speciesList: [], // Stores all species seen by the user
        trends: [], // Stores bird-watching trends over time
      },//Iain work end


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

      // Add tile layer from OpenStreetMap
      L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
        attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>',
      }).addTo(this.map);

      // Add a drawing layer for shapes
      this.drawingLayer = L.featureGroup().addTo(this.map);

      // Configure the draw control to enable only rectangle drawing
      const drawControl = new L.Control.Draw({
        edit: {
          featureGroup: this.drawingLayer, // Allow editing of drawn rectangles
          remove: true, // Allow removing of drawn rectangles
        },
        draw: {
          rectangle: {
            shapeOptions: {
              color: '#3388ff', // Border color of the rectangle
              weight: 2,        // Border thickness
            },
            showArea: true, // Show the area of the rectangle being drawn
          },
          polyline: false,       // Disable polyline
          polygon: false,        // Disable polygon
          circle: false,         // Disable circle
          circlemarker: false,   // Disable circle marker
          marker: false,         // Disable marker
        },
      });

      // Add the drawing control to the map
      this.map.addControl(drawControl);

      // Handle rectangle creation event
      this.map.on(L.Draw.Event.CREATED, (event) => {
        const layer = event.layer;
        this.drawingLayer.clearLayers(); // Remove any existing shapes
        this.drawingLayer.addLayer(layer); // Add the new rectangle to the drawing layer
        console.log("Rectangle created:", layer.getBounds());
      });

      console.log("Drawing tools initialized with rectangle only.");
    },


    centerMapOnUser() {
      // Check if geolocation is available in the browser
      if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
          (position) => {
            const { latitude, longitude } = position.coords;
            console.log("User's location:", { latitude, longitude });

            // Center the map on the user's location
            this.map.setView([latitude, longitude], 10);
          },
          (error) => {
            console.error("Geolocation error:", error);

            // Notify the user if geolocation fails
            alert(
              "Unable to retrieve your location. The map will remain on the default region."
            );
          }
        );
      } else {
        console.error("Geolocation is not supported by your browser.");

        // Notify the user if geolocation is not supported
        alert("Geolocation is not supported by your browser.");
      }
    },

    updateHeatmap(data) {
      // Remove the existing heatmap layer, if it exists
      if (this.heatLayer) {
        this.map.removeLayer(this.heatLayer);
      }

      // Format density data for the Leaflet heatmap plugin
      const heatData = data.map((point) => [point.lat, point.lng, point.density]);

      // Add a new heatmap layer with the provided data
      this.heatLayer = L.heatLayer(heatData, {
        radius: 25,
        blur: 15,
        maxZoom: 17,
      }).addTo(this.map);
    },

    fetchRandomBird() {
      fetch("/get_random_bird")
        .then((response) => response.json())
        .then((data) => {
          if (data.common_name) {
            this.randomBird = data.common_name;
            this.error = null;
          } else if (data.error) {
            this.randomBird = null;
            this.error = data.error;
          }
        })
        .catch((err) => {
          console.error("Error fetching random bird:", err);
          this.error = "Failed to fetch random bird.";
        });
    },

    fetchDensity() {
      // Build the API query for fetching density data based on the selected species
      const speciesQuery = this.selectedSpecies
        ? `?species=${encodeURIComponent(this.selectedSpecies)}`
        : '';

      axios
        .get(`/api/density${speciesQuery}`)
        .then((response) => {
          // Check if density data exists
          if (response.data.density && response.data.density.length > 0) {
            this.updateHeatmap(response.data.density); // Update the heatmap with fetched data
          } else {
            // Notify the user if no data is available
            alert(
              this.selectedSpecies
                ? `No density data available for species: ${this.selectedSpecies}.`
                : 'No density data available for all species.'
            );
          }
        })
        .catch((error) => {
          console.error('Error fetching density data:', error); // Log errors in the console
        });
    },

    fetchSpecies() {
      // Clear suggestions if the search box is empty
      if (this.selectedSpecies.trim() === "") {
        this.speciesSuggestions = [];
        return;
      }

      axios
        .get(`/api/species?suggest=${this.selectedSpecies}`)
        .then((response) => {
          // Update suggestions with the fetched species data
          this.speciesSuggestions = response.data.species.map((s) => ({
            id: s.id,
            name: s.common_name,
          }));
        })
        .catch((error) => {
          console.error("Error fetching species suggestions:", error); // Log errors in the console
        });
    },

    clearSelection() {
      this.selectedSpecies = ''; // Clear the selected species
      this.fetchDensity(); // Reload heatmap for all species
    },

    selectSpecies(speciesName) {
      // Update the selected species and clear suggestions
      this.selectedSpecies = speciesName;
      this.speciesSuggestions = [];
      this.fetchDensity(); // Update the heatmap for the selected species
    },

    showRegionStats() {
      // Get the drawn region from the map
      const layers = this.drawingLayer.getLayers();
      if (layers.length === 0) {
        alert('Please draw a region on the map first.'); // Notify user if no region is drawn
        return;
      }

      // Extract bounds from the drawn region
      const bounds = layers[0].getBounds();
      const region = {
        north: bounds.getNorth(),
        south: bounds.getSouth(),
        east: bounds.getEast(),
        west: bounds.getWest(),
      };

      // Save the selected region in localStorage for use in other pages
      localStorage.setItem('selectedRegion', JSON.stringify(region));

      // Redirect the user to the location page
      window.location.href = '/location';
    },

    goToChecklist() {
      // Redirect the user to the Checklist page
      window.location.href = "/checklist";
    },

    goToStats() {
      // Redirect the user to the Stats page
      window.location.href = "/user_stats";
    },


    /////////////// For checklist start
    fetchSpeciesChecklist() {
      // Fetch species filtered by the search query

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
      if (species.length === 0) {
        alert("No species with counts to submit.");
        return;
      }

      this.loading = true; // Set loading state
      axios.post("/save_checklist", { species })
        .then((response) => {
          const data = response.data;
          if (data.status === "success") {
            alert("Checklist submitted successfully!");
            this.clearChecklist(); // Reset the checklist after submission
          } else {
            alert(`Error: ${data.message}`);
          }
        })
        .catch((error) => {
          console.error("Error submitting checklist:", error);
          alert(
            error.response?.data?.message || "An error occurred while submitting the checklist."
          );
        })
        .finally(() => {
          this.loading = false; // Reset loading state
        });
    },
    clearChecklist() {
      this.filteredSpecies.forEach((s) => (s.count = 0)); // Reset counts
    },
  },
  /////////////// For checklist end

  mounted() {
    this.fetchRandomBird(); // Fetch a random bird on page load
    this.initMap();
    this.centerMapOnUser();
    this.fetchDensity(); // Load heatmap for all species by default
  },
});

app.mount('#app');
