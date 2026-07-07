/**
 * MapScreen.jsx
 * Michigan Housing App — Main Map Screen
 *
 * Renders a Mapbox GL map centered on Michigan. On viewport change (pan/zoom),
 * queries all active counties that intersect the viewport and renders parcel
 * polygons as a GeoJSON fill layer. Tapping a parcel opens the detail panel.
 */

import React, { useCallback, useRef, useState, useEffect } from 'react';
import {
  StyleSheet,
  View,
  Text,
  ActivityIndicator,
  Platform,
} from 'react-native';
import MapboxGL from '@rnmapbox/maps';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { SafeAreaView } from 'react-native-safe-area-context';

import { queryViewport, getCountiesInViewport } from '../data/parcelService';
import ParcelDetailPanel from '../components/ParcelDetailPanel';
import SearchBar from '../components/SearchBar';
import CountyStatusBar from '../components/CountyStatusBar';

// ─── Mapbox token — set via .env or replace here ─────────────────────────────
// IMPORTANT: Never commit a real token to source control.
// Use: MAPBOX_ACCESS_TOKEN env var, or react-native-config
MapboxGL.setAccessToken(process.env.MAPBOX_ACCESS_TOKEN ?? 'pk.YOUR_TOKEN_HERE');

// ─── Constants ────────────────────────────────────────────────────────────────

// Michigan geographic center: 44.3148° N, 85.6024° W
const MICHIGAN_CENTER = [-85.6024, 44.3148];
const MICHIGAN_ZOOM   = 6.5;
const PARCEL_MIN_ZOOM = 14;  // don't query below this — parcels too dense to be useful

const LAYER_ID_FILL   = 'parcel-fill';
const LAYER_ID_STROKE = 'parcel-stroke';
const LAYER_ID_LABEL  = 'parcel-label';
const SOURCE_ID       = 'parcels';

// Debounce viewport queries so we don't fire on every pixel of a pan
const QUERY_DEBOUNCE_MS = 600;

// ─── Component ────────────────────────────────────────────────────────────────

export default function MapScreen() {
  const mapRef       = useRef(null);
  const cameraRef    = useRef(null);
  const abortRef     = useRef(null);    // holds current AbortController
  const debounceRef  = useRef(null);

  const [geojson, setGeojson]           = useState(emptyCollection());
  const [loading, setLoading]           = useState(false);
  const [countyStatuses, setCountyStatuses] = useState([]);
  const [selectedParcel, setSelectedParcel] = useState(null);
  const [currentZoom, setCurrentZoom]   = useState(MICHIGAN_ZOOM);

  // ── Viewport query ─────────────────────────────────────────────────────────

  const handleRegionChange = useCallback((region) => {
    const zoom = region?.properties?.zoomLevel ?? 0;
    setCurrentZoom(zoom);

    if (zoom < PARCEL_MIN_ZOOM) {
      // Zoomed out too far — clear parcels, update county chips
      setGeojson(emptyCollection());
      const bbox = regionToBbox(region);
      setCountyStatuses(
        getCountiesInViewport(bbox).map((c) => ({
          county_id:    c.county_id,
          display_name: c.display_name,
          status:       'zoom_in',
          count:        0,
        }))
      );
      return;
    }

    // Cancel previous in-flight request
    if (abortRef.current) abortRef.current.abort();
    if (debounceRef.current) clearTimeout(debounceRef.current);

    debounceRef.current = setTimeout(async () => {
      const bbox       = regionToBbox(region);
      const controller = new AbortController();
      abortRef.current = controller;

      setLoading(true);
      setCountyStatuses(
        getCountiesInViewport(bbox).map((c) => ({
          county_id:    c.county_id,
          display_name: c.display_name,
          status:       'loading',
          count:        0,
        }))
      );

      // Accumulate features progressively as each county resolves
      const accumulated = [];

      const { results, errors } = await queryViewport(
        bbox,
        controller.signal,
        (normalized, county) => {
          // Progressive rendering — merge each county as it arrives
          accumulated.push(...normalized.features);
          setGeojson({ type: 'FeatureCollection', features: [...accumulated] });
          setCountyStatuses((prev) =>
            prev.map((s) =>
              s.county_id === county.county_id
                ? { ...s, status: 'loaded', count: normalized.features.length }
                : s
            )
          );
        }
      );

      // Mark errored counties
      errors.forEach(({ county, display }) => {
        setCountyStatuses((prev) =>
          prev.map((s) =>
            s.county_id === county
              ? { ...s, status: 'error', count: 0 }
              : s
          )
        );
      });

      setLoading(false);
    }, QUERY_DEBOUNCE_MS);
  }, []);

  // ── Parcel tap ─────────────────────────────────────────────────────────────

  const handleMapPress = useCallback(async (event) => {
    if (!mapRef.current) return;

    const { screenPointX, screenPointY } = event.properties;

    // Query rendered features at tap point (Mapbox client-side, instant)
    const features = await mapRef.current.queryRenderedFeaturesAtPoint(
      [screenPointX, screenPointY],
      null,                        // no filter
      [LAYER_ID_FILL]
    );

    if (features?.features?.length > 0) {
      setSelectedParcel(features.features[0].properties);
    } else {
      setSelectedParcel(null);
    }
  }, []);

  // ── Cleanup on unmount ─────────────────────────────────────────────────────
  useEffect(() => {
    return () => {
      if (abortRef.current) abortRef.current.abort();
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, []);

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <GestureHandlerRootView style={styles.root}>
      <SafeAreaView style={styles.root} edges={['top']}>

        {/* Search bar at top */}
        <SearchBar
          onParcelSelect={(parcel) => {
            setSelectedParcel(parcel.properties);
            cameraRef.current?.setCamera({
              centerCoordinate: parcel.geometry.coordinates[0][0],
              zoomLevel: 17,
              animationDuration: 800,
            });
          }}
        />

        {/* Map */}
        <MapboxGL.MapView
          ref={mapRef}
          style={styles.map}
          styleURL={MapboxGL.StyleURL.Street}
          onRegionDidChange={handleRegionChange}
          onPress={handleMapPress}
          compassEnabled
          compassViewPosition={3} /* bottom-right */
          attributionEnabled
          logoEnabled={false}
        >
          <MapboxGL.Camera
            ref={cameraRef}
            zoomLevel={MICHIGAN_ZOOM}
            centerCoordinate={MICHIGAN_CENTER}
            animationMode="none"
          />

          {/* Parcel GeoJSON source + layers */}
          {geojson.features.length > 0 && (
            <MapboxGL.ShapeSource
              id={SOURCE_ID}
              shape={geojson}
              tolerance={0.5}    /* simplify geometry for performance */
              buffer={64}
            >
              {/* Fill: color by property class */}
              <MapboxGL.FillLayer
                id={LAYER_ID_FILL}
                style={parcelFillStyle}
              />

              {/* Stroke */}
              <MapboxGL.LineLayer
                id={LAYER_ID_STROKE}
                style={parcelStrokeStyle}
              />

              {/* Address label at high zoom */}
              <MapboxGL.SymbolLayer
                id={LAYER_ID_LABEL}
                minZoomLevel={17}
                style={parcelLabelStyle}
              />
            </MapboxGL.ShapeSource>
          )}
        </MapboxGL.MapView>

        {/* Zoom prompt overlay */}
        {currentZoom < PARCEL_MIN_ZOOM && (
          <View style={styles.zoomPrompt} pointerEvents="none">
            <Text style={styles.zoomPromptText}>Zoom in to see parcels</Text>
          </View>
        )}

        {/* Loading spinner */}
        {loading && (
          <View style={styles.loadingBadge} pointerEvents="none">
            <ActivityIndicator size="small" color="#fff" />
            <Text style={styles.loadingText}>Loading parcels…</Text>
          </View>
        )}

        {/* County status chips */}
        <CountyStatusBar statuses={countyStatuses} />

        {/* Parcel detail bottom sheet */}
        {selectedParcel && (
          <ParcelDetailPanel
            parcel={selectedParcel}
            onClose={() => setSelectedParcel(null)}
          />
        )}

      </SafeAreaView>
    </GestureHandlerRootView>
  );
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function emptyCollection() {
  return { type: 'FeatureCollection', features: [] };
}

function regionToBbox(region) {
  const { visibleBounds } = region?.properties ?? {};
  if (visibleBounds) {
    // visibleBounds = [[NE_lng, NE_lat], [SW_lng, SW_lat]]
    const [[eLng, nLat], [wLng, sLat]] = visibleBounds;
    return [wLng, sLat, eLng, nLat];
  }
  // Fallback: use full Michigan bbox
  return [-90.4, 41.7, -82.1, 48.3];
}

// ─── Mapbox Layer Styles ──────────────────────────────────────────────────────

const CLASS_COLORS = {
  Agricultural: '#a3c98b',
  Commercial:   '#f4a460',
  Industrial:   '#b0b0d0',
  Residential:  '#7ec8e3',
  default:      '#cccccc',
};

const parcelFillStyle = {
  fillColor: [
    'match',
    ['get', 'property_class_label'],
    'Agricultural', CLASS_COLORS.Agricultural,
    'Commercial',   CLASS_COLORS.Commercial,
    'Industrial',   CLASS_COLORS.Industrial,
    'Residential',  CLASS_COLORS.Residential,
    CLASS_COLORS.default,
  ],
  fillOpacity: 0.35,
  fillOutlineColor: 'transparent',
};

const parcelStrokeStyle = {
  lineColor:   '#2a5caa',
  lineWidth:   1.2,
  lineOpacity: 0.7,
};

const parcelLabelStyle = {
  textField:     ['get', 'property_address'],
  textSize:      10,
  textColor:     '#111',
  textHaloColor: '#fff',
  textHaloWidth: 1.5,
  textMaxWidth:  8,
};

// ─── Styles ───────────────────────────────────────────────────────────────────

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: '#fff',
  },
  map: {
    flex: 1,
  },
  zoomPrompt: {
    position:        'absolute',
    bottom:          120,
    left:            0,
    right:           0,
    alignItems:      'center',
  },
  zoomPromptText: {
    backgroundColor: 'rgba(0,0,0,0.55)',
    color:           '#fff',
    paddingHorizontal: 14,
    paddingVertical:   7,
    borderRadius:    20,
    fontSize:        13,
    overflow:        'hidden',
  },
  loadingBadge: {
    position:        'absolute',
    top:             90,
    right:           12,
    flexDirection:   'row',
    alignItems:      'center',
    backgroundColor: 'rgba(42,92,170,0.85)',
    paddingHorizontal: 10,
    paddingVertical:   6,
    borderRadius:    16,
    gap:             6,
  },
  loadingText: {
    color:    '#fff',
    fontSize: 12,
  },
});
