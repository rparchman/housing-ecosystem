/**
 * SearchBar.jsx
 * Address + parcel ID search. Queries the active counties via searchByAddress()
 * and displays a result list below the input. Selecting a result pans the map
 * to that parcel and triggers the detail panel via onParcelSelect callback.
 */

import React, { useState, useCallback, useRef } from 'react';
import {
  View,
  Text,
  TextInput,
  StyleSheet,
  TouchableOpacity,
  FlatList,
  ActivityIndicator,
  Keyboard,
  Platform,
} from 'react-native';
import { searchByAddress } from '../data/parcelService';

const DEBOUNCE_MS = 400;
const MIN_QUERY   = 3;

export default function SearchBar({ onParcelSelect }) {
  const [query,   setQuery]   = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [focused, setFocused] = useState(false);

  const debounceRef = useRef(null);
  const abortRef    = useRef(null);
  const inputRef    = useRef(null);

  const runSearch = useCallback(async (text) => {
    if (text.length < MIN_QUERY) {
      setResults([]);
      return;
    }

    if (abortRef.current) abortRef.current.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setLoading(true);
    try {
      const res = await searchByAddress(text);
      if (!controller.signal.aborted) {
        setResults(res.features ?? []);
      }
    } catch {
      // silently ignore abort errors
    } finally {
      if (!controller.signal.aborted) setLoading(false);
    }
  }, []);

  const handleChangeText = useCallback((text) => {
    setQuery(text);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => runSearch(text), DEBOUNCE_MS);
  }, [runSearch]);

  const handleSelect = useCallback((feature) => {
    Keyboard.dismiss();
    setQuery(feature.properties?.property_address ?? '');
    setResults([]);
    onParcelSelect?.(feature);
  }, [onParcelSelect]);

  const handleClear = useCallback(() => {
    setQuery('');
    setResults([]);
    inputRef.current?.focus();
  }, []);

  const showDropdown = focused && (results.length > 0 || loading);

  return (
    <View style={styles.wrapper}>
      <View style={[styles.bar, focused && styles.barFocused]}>
        {/* Search icon */}
        <Text style={styles.icon}>🔍</Text>

        <TextInput
          ref={inputRef}
          style={styles.input}
          value={query}
          onChangeText={handleChangeText}
          onFocus={() => setFocused(true)}
          onBlur={() => setTimeout(() => setFocused(false), 150)}
          placeholder="Search address or parcel ID…"
          placeholderTextColor="#999"
          returnKeyType="search"
          autoCorrect={false}
          autoCapitalize="words"
          clearButtonMode="never"
        />

        {/* Loading / clear */}
        {loading ? (
          <ActivityIndicator size="small" color="#2a5caa" style={styles.actionIcon} />
        ) : query.length > 0 ? (
          <TouchableOpacity onPress={handleClear} hitSlop={12} style={styles.actionIcon}>
            <Text style={styles.clearText}>✕</Text>
          </TouchableOpacity>
        ) : null}
      </View>

      {/* Results dropdown */}
      {showDropdown && (
        <View style={styles.dropdown}>
          {results.length === 0 && !loading && (
            <Text style={styles.emptyText}>No results found</Text>
          )}
          <FlatList
            data={results}
            keyExtractor={(item, i) =>
              item.properties?.parcel_id ?? String(i)
            }
            renderItem={({ item }) => (
              <ResultRow feature={item} onPress={handleSelect} />
            )}
            keyboardShouldPersistTaps="handled"
            ItemSeparatorComponent={() => <View style={styles.sep} />}
          />
        </View>
      )}
    </View>
  );
}

function ResultRow({ feature, onPress }) {
  const { property_address, owner_name, assessed_value, county } =
    feature.properties ?? {};

  return (
    <TouchableOpacity
      style={styles.resultRow}
      onPress={() => onPress(feature)}
      activeOpacity={0.7}
    >
      <View style={styles.resultLeft}>
        <Text style={styles.resultAddress} numberOfLines={1}>
          {property_address ?? 'Unknown Address'}
        </Text>
        <Text style={styles.resultMeta} numberOfLines={1}>
          {[owner_name, county].filter(Boolean).join(' · ')}
        </Text>
      </View>
      {assessed_value != null && (
        <Text style={styles.resultValue}>
          ${assessed_value.toLocaleString()}
        </Text>
      )}
    </TouchableOpacity>
  );
}

// ─── Styles ───────────────────────────────────────────────────────────────────

const styles = StyleSheet.create({
  wrapper: {
    position: 'absolute',
    top:      Platform.OS === 'ios' ? 54 : 10,
    left:     12,
    right:    12,
    zIndex:   100,
  },
  bar: {
    flexDirection:   'row',
    alignItems:      'center',
    backgroundColor: '#ffffff',
    borderRadius:    24,
    paddingHorizontal: 14,
    paddingVertical:   10,
    shadowColor:     '#000',
    shadowOffset:    { width: 0, height: 2 },
    shadowOpacity:   0.15,
    shadowRadius:    6,
    elevation:       5,
    borderWidth:     1.5,
    borderColor:     'transparent',
  },
  barFocused: {
    borderColor: '#2a5caa',
  },
  icon: {
    fontSize:    16,
    marginRight: 8,
    color:       '#888',
  },
  input: {
    flex:      1,
    fontSize:  15,
    color:     '#1a1a1a',
    padding:   0,
  },
  actionIcon: {
    marginLeft: 8,
  },
  clearText: {
    fontSize: 14,
    color:    '#999',
  },

  // Dropdown
  dropdown: {
    backgroundColor: '#fff',
    borderRadius:    14,
    marginTop:       6,
    maxHeight:       280,
    shadowColor:     '#000',
    shadowOffset:    { width: 0, height: 4 },
    shadowOpacity:   0.12,
    shadowRadius:    8,
    elevation:       8,
    overflow:        'hidden',
  },
  emptyText: {
    padding:   16,
    color:     '#999',
    textAlign: 'center',
    fontSize:  14,
  },
  sep: {
    height:          1,
    backgroundColor: '#f0f0f0',
    marginHorizontal: 14,
  },
  resultRow: {
    flexDirection:  'row',
    alignItems:     'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical:   12,
  },
  resultLeft: {
    flex:         1,
    paddingRight: 10,
  },
  resultAddress: {
    fontSize:   14,
    fontWeight: '600',
    color:      '#1a1a1a',
  },
  resultMeta: {
    fontSize:  12,
    color:     '#888',
    marginTop:  2,
  },
  resultValue: {
    fontSize:   13,
    fontWeight: '700',
    color:      '#2a5caa',
  },
});
