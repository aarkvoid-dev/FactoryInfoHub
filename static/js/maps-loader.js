/**
 * Google Maps Dynamic Loader
 * 
 * Only loads the Google Maps API on pages that actually have map elements.
 * Detects .js-map, .js-map-tour, .js-map-single elements and loads Maps API on demand.
 * After Maps API loads, initializes all maps with copied logic from main.js
 * so the main.js calls become no-ops (safe guards).
 */
(function() {
  'use strict';

  var mapSelectors = ['.js-map', '.js-map-tour', '.js-map-single'];
  var hasMap = false;

  // Check if any map element exists on this page
  for (var i = 0; i < mapSelectors.length; i++) {
    if (document.querySelector(mapSelectors[i])) {
      hasMap = true;
      break;
    }
  }

  // No map elements found — never load Google Maps API
  if (!hasMap) {
    return;
  }

  // Map element exists — load Google Maps API dynamically
  var script = document.createElement('script');
  script.src = 'https://maps.googleapis.com/maps/api/js?key=AIzaSyAAz77U5XQuEME6TpftaMdX0bBelQxXRlM&callback=googleMapsInitMaps';
  script.async = true;
  script.defer = true;
  document.body.appendChild(script);
})();

/**
 * Callback fired when Google Maps API has loaded.
 * Initializes all map instances on the page.
 */
window.googleMapsInitMaps = function() {
  // ---- .js-map (multi-marker map) ----
  function initMap() {
    var el = document.querySelector('.js-map');
    if (!el) return;

    var locations = [];

    // Try to read locations from a data attribute or nearby script
    var elLocations = document.querySelector('.js-map-locations');
    if (elLocations) {
      try {
        locations = JSON.parse(elLocations.textContent);
      } catch(e) {
        locations = [];
      }
    }

    // Default locations if none provided
    if (!locations.length) {
      var centerAttr = el.getAttribute('data-center');
      if (centerAttr) {
        var parts = centerAttr.split(',');
        locations = [{ lat: parseFloat(parts[0]), lng: parseFloat(parts[1]) }];
      } else {
        locations = [{ lat: 40.7127281, lng: -74.0060152 }];
      }
    }

    var center = locations[0];

    var map = new google.maps.Map(el, {
      zoom: 12,
      center: center,
      disableDefaultUI: true,
    });

    var bounds = new google.maps.LatLngBounds();

    locations.forEach(function(location) {
      new google.maps.Marker({
        position: location,
        map: map,
      });
      bounds.extend(location);
    });

    if (locations.length > 1) {
      map.fitBounds(bounds);
    }
  }

  // ---- .js-map-tour (tour map) ----
  function initMapTourPages() {
    var el = document.querySelector('.js-map-tour');
    if (!el) return;

    var locations = [];

    var elLocations = document.querySelector('.js-map-tour-locations');
    if (elLocations) {
      try {
        locations = JSON.parse(elLocations.textContent);
      } catch(e) {
        locations = [];
      }
    }

    if (!locations.length) {
      var centerAttr = el.getAttribute('data-center');
      if (centerAttr) {
        var parts = centerAttr.split(',');
        locations = [{ lat: parseFloat(parts[0]), lng: parseFloat(parts[1]) }];
      } else {
        locations = [{ lat: 40.7127281, lng: -74.0060152 }];
      }
    }

    var map = new google.maps.Map(el, {
      zoom: 10,
      center: locations[0],
      disableDefaultUI: true,
    });

    locations.forEach(function(location) {
      new google.maps.Marker({
        position: location,
        map: map,
      });
    });
  }

  // ---- .js-map-single (single marker map) ----
  function initMapSingle() {
    var el = document.querySelector('.js-map-single');
    if (!el) return;

    var center = { lat: 40.7127281, lng: -74.0060152 };
    var centerAttr = el.getAttribute('data-center');
    if (centerAttr) {
      var parts = centerAttr.split(',');
      center = { lat: parseFloat(parts[0]), lng: parseFloat(parts[1]) };
    }

    new google.maps.Map(el, {
      zoom: 12,
      center: center,
      disableDefaultUI: true,
    });
  }

  initMap();
  initMapTourPages();
  initMapSingle();
};