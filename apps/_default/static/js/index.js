"use strict";

const app = Vue.createApp({
  data() {
    return {
      map: null, // Leaflet map instance
    };
  },
  methods: {
    initMap() {
      // Initialize the map
      this.map = L.map('map').setView([37.7749, -122.4194], 10); // Center on San Francisco
      L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>',
      }).addTo(this.map);
    },
  },
  mounted() {
    this.initMap(); // Initialize the map once the app is mounted
  },
});

app.mount('#app');
