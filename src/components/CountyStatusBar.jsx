/**
 * CountyStatusBar.jsx
 * Horizontal scrolling row of county "chip" indicators that appear at the
 * bottom of the map. Each chip shows which counties are in the viewport and
 * their current data-load status: loading / loaded / error / zoom_in.
 */

import React from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  ActivityIndicator,
} from 'react-native';

const STATUS_CONFIG = {
  loading:  { color: '#2a5caa', bg: '#e3f0ff', icon: null,  label: '…'  },
  loaded:   { color: '#2e7d32', bg: '#e8f5e9', icon: '✓',   label: ''   },
  error:    { color: '#c62828', bg: '#ffebee', icon: '!',   label: ''   },
  zoom_in:  { color: '#888',    bg: '#f5f5f5', icon: '⊕',   label: ''   },
};

export default function CountyStatusBar({ statuses }) {
  if (!statuses || statuses.length === 0) return null;

  return (
    <View style={styles.container}>
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.scroll}
      >
        {statuses.map((s) => (
          <CountyChip key={s.county_id} status={s} />
        ))}
      </ScrollView>
    </View>
  );
}

function CountyChip({ status }) {
  const cfg = STATUS_CONFIG[status.status] ?? STATUS_CONFIG.zoom_in;

  return (
    <View style={[styles.chip, { backgroundColor: cfg.bg }]}>
      {status.status === 'loading' ? (
        <ActivityIndicator size="small" color={cfg.color} style={styles.spinner} />
      ) : (
        cfg.icon && (
          <Text style={[styles.chipIcon, { color: cfg.color }]}>{cfg.icon}</Text>
        )
      )}
      <Text style={[styles.chipName, { color: cfg.color }]}>
        {status.display_name}
      </Text>
      {status.status === 'loaded' && status.count > 0 && (
        <Text style={[styles.chipCount, { color: cfg.color }]}>
          {status.count.toLocaleString()}
        </Text>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    bottom:   90,
    left:     0,
    right:    0,
  },
  scroll: {
    paddingHorizontal: 12,
    gap: 6,
    flexDirection: 'row',
  },
  chip: {
    flexDirection:    'row',
    alignItems:       'center',
    paddingHorizontal: 10,
    paddingVertical:    5,
    borderRadius:      16,
    gap:               4,
    shadowColor:      '#000',
    shadowOffset:     { width: 0, height: 1 },
    shadowOpacity:    0.10,
    shadowRadius:     3,
    elevation:        2,
  },
  spinner: {
    marginRight: 2,
  },
  chipIcon: {
    fontSize:   12,
    fontWeight: '700',
  },
  chipName: {
    fontSize:   12,
    fontWeight: '600',
  },
  chipCount: {
    fontSize:  11,
    opacity:    0.75,
  },
});
