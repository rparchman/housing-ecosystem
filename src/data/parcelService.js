/**
 * parcelService.js
 * Michigan Housing App — Live REST Query Engine
 *
 * Handles all ArcGIS REST queries across 28 Michigan county endpoints.
 * No caching — all data is live from county servers.
 */

import counties from './counties.json';

// ─── Constants ───────────────────────────────────────────────────────────────

const DEFAULT_TIMEOUT_MS   = 10_000;
const MAX_RECORDS_PER_PAGE = 2_000;
const MAX_VIEWPORT_PARCELS = 5_000;  // stop paginating beyond this to keep map smooth
const DEBOUNCE_BETWEEN_REQUESTS_MS = 200;

// ─── County Registry ─────────────────────────────────────────────────────────

/**
 * Returns all counties cleared for use (tier 1 cleared + tier 2 with permission granted).
 * Tier 2 "pending" counties are excluded until permission_status === 'granted'.
 */
export function getActiveCounties() {
  return counties.filter(
    (c) => c.permission_status === 'cleared' || c.permission_status === 'granted'
  );
}

/**
 * Returns counties whose bounding box intersects the given map viewport.
 * @param {[number, number, number, number]} viewport  [west, south, east, north] in WGS84
 */
export function getCountiesInViewport(viewport) {
  const [west, south, east, north] = viewport;
  return getActiveCounties().filter((county) => {
    const [cWest, cSouth, cEast, cNorth] = county.bbox;
    return !(east < cWest || west > cEast || north < cSouth || south > cNorth);
  });
}

/**
 * Find a county config by county_id string.
 */
export function getCountyById(countyId) {
  return counties.find((c) => c.county_id === countyId) ?? null;
}

// ─── URL Builder ─────────────────────────────────────────────────────────────

/**
 * Builds an ArcGIS REST query URL for viewport-based parcel fetching.
 * @param {object} county     County config object from counties.json
 * @param {number[]} bbox     [west, south, east, north]
 * @param {number}  offset    Pagination offset (0, 2000, 4000, …)
 */
function buildViewportQueryUrl(county, bbox, offset = 0) {
  const [west, south, east, north] = bbox;
  const geometry = encodeURIComponent(`${west},${south},${east},${north}`);
  const params = new URLSearchParams({
    where:             '1=1',
    geometry,
    geometryType:      'esriGeometryEnvelope',
    inSR:              '4326',
    outSR:             '4326',
    spatialRel:        'esriSpatialRelIntersects',
    outFields:         '*',
    resultOffset:       String(offset),
    resultRecordCount:  String(Math.min(MAX_RECORDS_PER_PAGE, county.max_records ?? MAX_RECORDS_PER_PAGE)),
    f:                 'geojson',
  });
  return `${county.base_url}/query?${params.toString()}`;
}

/**
 * Builds an ArcGIS REST query URL for a single parcel ID lookup.
 * @param {object} county
 * @param {string} parcelId
 */
function buildParcelIdQueryUrl(county, parcelId) {
  const parcelField = county.field_map.parcel_id;
  const params = new URLSearchParams({
    where:     `${parcelField}='${parcelId}'`,
    outFields: '*',
    f:         'geojson',
  });
  return `${county.base_url}/query?${params.toString()}`;
}

/**
 * Builds an ArcGIS REST query URL for a fuzzy address search.
 * @param {object} county
 * @param {string} address   Raw address string from the user
 */
function buildAddressQueryUrl(county, address) {
  const addrField = county.field_map.property_address;
  const escaped   = address.replace(/'/g, "''").toUpperCase();
  const params = new URLSearchParams({
    where:     `UPPER(${addrField}) LIKE '%${escaped}%'`,
    outFields: '*',
    resultRecordCount: '50',
    f:         'geojson',
  });
  return `${county.base_url}/query?${params.toString()}`;
}

// ─── HTTP Fetch with Retry ────────────────────────────────────────────────────

/**
 * Fetches a URL with timeout and up to maxRetries retries on transient failures.
 * Returns the parsed JSON or throws a typed error.
 */
async function fetchWithRetry(url, signal, maxRetries = 2) {
  let lastError;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      const controller = new AbortController();
      const timeoutId  = setTimeout(() => controller.abort(), DEFAULT_TIMEOUT_MS);

      // Merge caller's signal with our timeout signal
      const combinedSignal = signal
        ? anySignal([signal, controller.signal])
        : controller.signal;

      const response = await fetch(url, { signal: combinedSignal });
      clearTimeout(timeoutId);

      if (response.status === 429) {
        // Rate limited — exponential backoff
        const delay = Math.pow(2, attempt) * 1000;
        await sleep(delay);
        lastError = new ParcelServiceError('RATE_LIMITED', `429 Too Many Requests — backed off ${delay}ms`);
        continue;
      }

      if (response.status >= 500) {
        await sleep(2000);
        lastError = new ParcelServiceError('SERVER_ERROR', `HTTP ${response.status}`);
        continue;
      }

      if (!response.ok) {
        // 4xx errors — don't retry
        throw new ParcelServiceError('CLIENT_ERROR', `HTTP ${response.status} for ${url}`);
      }

      const json = await response.json();
      return json;

    } catch (err) {
      if (err.name === 'AbortError') {
        throw new ParcelServiceError('TIMEOUT', `Request timed out after ${DEFAULT_TIMEOUT_MS}ms`);
      }
      if (err instanceof ParcelServiceError) throw err;
      lastError = err;
    }
  }

  throw lastError ?? new ParcelServiceError('UNKNOWN', 'Request failed after retries');
}

// ─── Paginated Viewport Fetch ─────────────────────────────────────────────────

/**
 * Fetches all parcels for a single county within the given viewport.
 * Paginates automatically, stopping at MAX_VIEWPORT_PARCELS.
 *
 * @param {object} county
 * @param {number[]} bbox
 * @param {AbortSignal} signal   Pass AbortController.signal to cancel on map pan
 * @returns {Promise<GeoJSON.FeatureCollection>}
 */
async function fetchCountyParcels(county, bbox, signal) {
  const allFeatures = [];
  let offset        = 0;

  while (true) {
    const url  = buildViewportQueryUrl(county, bbox, offset);
    const data = await fetchWithRetry(url, signal);

    const features = data?.features ?? [];
    allFeatures.push(...features);

    const done =
      features.length < (county.max_records ?? MAX_RECORDS_PER_PAGE) ||
      allFeatures.length >= MAX_VIEWPORT_PARCELS;

    if (done) break;
    offset += MAX_RECORDS_PER_PAGE;
  }

  return {
    type:     'FeatureCollection',
    features: allFeatures,
    _county:  county.county_id,  // metadata for normalizer
  };
}

// ─── County Router ────────────────────────────────────────────────────────────

/**
 * Dispatches parallel REST queries to all counties that intersect the viewport.
 * Each county is queried independently — failure of one never blocks others.
 *
 * @param {number[]} viewport    [west, south, east, north]
 * @param {AbortSignal} signal
 * @param {function} onCountyResult   Callback fired as each county completes (for progressive rendering)
 * @returns {Promise<{ results: NormalizedFeatureCollection[], errors: CountyError[] }>}
 */
export async function queryViewport(viewport, signal, onCountyResult) {
  const intersecting = getCountiesInViewport(viewport);

  if (intersecting.length === 0) {
    return { results: [], errors: [] };
  }

  const settled = await Promise.allSettled(
    intersecting.map(async (county, idx) => {
      // Stagger requests slightly to avoid slamming all endpoints simultaneously
      if (idx > 0) await sleep(idx * DEBOUNCE_BETWEEN_REQUESTS_MS);

      const raw        = await fetchCountyParcels(county, viewport, signal);
      const normalized = normalizeFeatureCollection(raw, county);

      if (onCountyResult) onCountyResult(normalized, county);
      return normalized;
    })
  );

  const results = [];
  const errors  = [];

  settled.forEach((outcome, idx) => {
    if (outcome.status === 'fulfilled') {
      results.push(outcome.value);
    } else {
      errors.push({
        county:  intersecting[idx].county_id,
        display: intersecting[idx].display_name,
        error:   outcome.reason,
      });
    }
  });

  return { results, errors };
}

/**
 * Looks up a specific parcel by ID across all counties (or a specific county).
 * @param {string} parcelId
 * @param {string|null} countyId   If provided, only search that county
 */
export async function lookupParcel(parcelId, countyId = null) {
  const targets = countyId
    ? getActiveCounties().filter((c) => c.county_id === countyId)
    : getActiveCounties();

  const results = await Promise.allSettled(
    targets.map(async (county) => {
      const url  = buildParcelIdQueryUrl(county, parcelId);
      const data = await fetchWithRetry(url, null);
      if (!data?.features?.length) return null;
      return normalizeFeatureCollection({ ...data, _county: county.county_id }, county);
    })
  );

  return results
    .filter((r) => r.status === 'fulfilled' && r.value !== null)
    .map((r) => r.value);
}

/**
 * Searches all active counties for parcels matching an address string.
 * Only searches counties whose bbox intersects the given viewport (if provided).
 */
export async function searchByAddress(address, viewport = null) {
  const targets = viewport ? getCountiesInViewport(viewport) : getActiveCounties();

  const results = await Promise.allSettled(
    targets.map(async (county) => {
      const url  = buildAddressQueryUrl(county, address);
      const data = await fetchWithRetry(url, null);
      if (!data?.features?.length) return null;
      return normalizeFeatureCollection({ ...data, _county: county.county_id }, county);
    })
  );

  return results
    .filter((r) => r.status === 'fulfilled' && r.value !== null)
    .flatMap((r) => r.value.features);
}

// ─── Normalizer ───────────────────────────────────────────────────────────────

/**
 * Maps a raw ArcGIS GeoJSON FeatureCollection to the app's unified schema.
 * Every feature gets a `properties` object with consistent field names regardless
 * of which county it came from.
 *
 * Unified schema fields:
 *   parcel_id, owner_name, owner_name2, owner_address, owner_city, owner_zip,
 *   property_address, property_city, property_class, assessed_value,
 *   taxable_value, acreage, municipality, school_district, county, fips
 *
 * @param {object} collection   Raw GeoJSON FeatureCollection with _county metadata
 * @param {object} county       County config from counties.json
 * @returns {NormalizedFeatureCollection}
 */
function normalizeFeatureCollection(collection, county) {
  const fm = county.field_map;

  const features = (collection.features ?? []).map((feature) => {
    const p = feature.properties ?? {};

    const normalized = {
      // ── Identity ─────────────────────────────────────
      parcel_id:        valueOf(p, fm.parcel_id),
      county:           county.display_name,
      fips:             county.fips,
      county_id:        county.county_id,

      // ── Owner ─────────────────────────────────────────
      owner_name:       valueOf(p, fm.owner_name),
      owner_name2:      valueOf(p, fm.owner_name2),
      owner_care_of:    valueOf(p, fm.owner_care_of),
      owner_address:    valueOf(p, fm.owner_address),
      owner_city:       valueOf(p, fm.owner_city),
      owner_zip:        valueOf(p, fm.owner_zip),

      // ── Property Location ──────────────────────────────
      property_address: valueOf(p, fm.property_address),
      property_city:    valueOf(p, fm.property_city),

      // ── Classification & Value ─────────────────────────
      property_class:   valueOf(p, fm.property_class),
      property_class_label: classLabel(valueOf(p, fm.property_class)),
      assessed_value:   toNumber(p, fm.assessed_value),
      taxable_value:    toNumber(p, fm.taxable_value),
      acreage:          toFloat(p, fm.acreage),

      // ── Government ────────────────────────────────────
      municipality:     valueOf(p, fm.municipality),
      school_district:  valueOf(p, fm.school_district),

      // ── Attribution (required by county license) ───────
      _attribution:     county.attribution,
      _tier:            county.tier,
      _confidence:      county.field_confidence,

      // ── Raw passthrough for debugging ──────────────────
      _raw: p,
    };

    return { ...feature, properties: normalized };
  });

  return {
    type:        'FeatureCollection',
    features,
    _county_id:  county.county_id,
    _count:      features.length,
    _attribution: county.attribution,
  };
}

// ─── Normalizer Helpers ───────────────────────────────────────────────────────

/** Safely reads a field by name, returns null if missing/blank */
function valueOf(props, fieldName) {
  if (!fieldName) return null;
  const val = props[fieldName];
  if (val === null || val === undefined || val === '') return null;
  return String(val).trim();
}

/** Reads a field and parses it as an integer (for SEV / TV) */
function toNumber(props, fieldName) {
  const val = props[fieldName];
  if (val === null || val === undefined) return null;
  const n = parseInt(val, 10);
  return isNaN(n) ? null : n;
}

/** Reads a field and parses it as a float (for acreage) */
function toFloat(props, fieldName) {
  const val = props[fieldName];
  if (val === null || val === undefined) return null;
  const n = parseFloat(val);
  return isNaN(n) ? null : n;
}

/**
 * Converts a Michigan MCL 211.34c property class code to a human-readable label.
 * Handles both numeric codes (101, 201…) and string prefixes.
 */
function classLabel(code) {
  if (!code) return null;
  const prefix = String(code).substring(0, 1);
  const map = {
    '1': 'Agricultural',
    '2': 'Commercial',
    '3': 'Industrial',
    '4': 'Residential',
    '5': 'Timber Cutover',
    '6': 'Developmental Rights',
  };
  return map[prefix] ?? `Class ${code}`;
}

// ─── Utility ─────────────────────────────────────────────────────────────────

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Creates an AbortSignal that aborts when ANY of the given signals abort.
 * Polyfill for environments without AbortSignal.any().
 */
function anySignal(signals) {
  if (typeof AbortSignal?.any === 'function') return AbortSignal.any(signals);
  const controller = new AbortController();
  signals.forEach((sig) =>
    sig.addEventListener('abort', () => controller.abort(sig.reason), { once: true })
  );
  return controller.signal;
}

// ─── Custom Error Class ───────────────────────────────────────────────────────

export class ParcelServiceError extends Error {
  /**
   * @param {'TIMEOUT'|'RATE_LIMITED'|'SERVER_ERROR'|'CLIENT_ERROR'|'UNKNOWN'} code
   * @param {string} message
   */
  constructor(code, message) {
    super(message);
    this.name = 'ParcelServiceError';
    this.code = code;
  }
}
