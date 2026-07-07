/**
 * ParcelDetailPanel.jsx
 * Slides up from the bottom when user taps a parcel polygon.
 * Shows all normalized fields + required county attribution.
 */

import React, { useRef, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Linking,
  Platform,
} from 'react-native';
import BottomSheet, { BottomSheetScrollView } from '@gorhom/bottom-sheet';

const SNAP_POINTS = ['35%', '75%'];

export default function ParcelDetailPanel({ parcel, onClose }) {
  const sheetRef = useRef(null);

  useEffect(() => {
    if (parcel) sheetRef.current?.snapToIndex(0);
  }, [parcel]);

  const handleClose = useCallback(() => {
    sheetRef.current?.close();
    onClose?.();
  }, [onClose]);

  if (!parcel) return null;

  const assessedDisplay  = formatCurrency(parcel.assessed_value);
  const taxableDisplay   = formatCurrency(parcel.taxable_value);
  const acreageDisplay   = parcel.acreage != null ? `${parcel.acreage.toFixed(3)} ac` : '—';

  return (
    <BottomSheet
      ref={sheetRef}
      index={0}
      snapPoints={SNAP_POINTS}
      enablePanDownToClose
      onClose={onClose}
      backgroundStyle={styles.sheet}
      handleIndicatorStyle={styles.handle}
    >
      <BottomSheetScrollView contentContainerStyle={styles.content}>

        {/* Header row */}
        <View style={styles.headerRow}>
          <View style={styles.headerLeft}>
            <Text style={styles.address} numberOfLines={2}>
              {parcel.property_address ?? 'No address on record'}
            </Text>
            {parcel.property_city && (
              <Text style={styles.cityLine}>{parcel.property_city}</Text>
            )}
          </View>
          <TouchableOpacity onPress={handleClose} style={styles.closeBtn} hitSlop={12}>
            <Text style={styles.closeBtnText}>✕</Text>
          </TouchableOpacity>
        </View>

        {/* Class badge */}
        {parcel.property_class_label && (
          <View style={[styles.badge, classBadgeStyle(parcel.property_class_label)]}>
            <Text style={styles.badgeText}>{parcel.property_class_label}</Text>
          </View>
        )}

        {/* Value row */}
        <View style={styles.valueRow}>
          <ValueCard label="Assessed Value (SEV)" value={assessedDisplay} />
          <ValueCard label="Taxable Value" value={taxableDisplay} />
          <ValueCard label="Acreage" value={acreageDisplay} />
        </View>

        <Divider />

        {/* Owner info */}
        <Section title="Owner">
          <Row label="Name"    value={parcel.owner_name} />
          {parcel.owner_name2 && <Row label="Co-owner" value={parcel.owner_name2} />}
          {parcel.owner_care_of && <Row label="Care Of" value={parcel.owner_care_of} />}
          <Row label="Mailing Address" value={formatMailingAddress(parcel)} />
        </Section>

        <Divider />

        {/* Parcel details */}
        <Section title="Parcel Details">
          <Row label="Parcel ID"      value={parcel.parcel_id} mono />
          <Row label="Municipality"   value={parcel.municipality} />
          <Row label="School District"value={parcel.school_district} />
          <Row label="County"         value={parcel.county} />
          <Row label="FIPS"           value={parcel.fips} mono />
        </Section>

        <Divider />

        {/* Attribution — required by county data licenses */}
        <View style={styles.attribution}>
          <Text style={styles.attributionLabel}>Data Source</Text>
          <Text style={styles.attributionText}>{parcel._attribution}</Text>
          <Text style={styles.attributionNote}>
            Parcel data is public record. Values reflect county assessment records
            and may not represent current market value.
          </Text>
        </View>

      </BottomSheetScrollView>
    </BottomSheet>
  );
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function ValueCard({ label, value }) {
  return (
    <View style={styles.valueCard}>
      <Text style={styles.valueCardAmount}>{value ?? '—'}</Text>
      <Text style={styles.valueCardLabel}>{label}</Text>
    </View>
  );
}

function Section({ title, children }) {
  return (
    <View style={styles.section}>
      <Text style={styles.sectionTitle}>{title}</Text>
      {children}
    </View>
  );
}

function Row({ label, value, mono = false }) {
  if (!value) return null;
  return (
    <View style={styles.row}>
      <Text style={styles.rowLabel}>{label}</Text>
      <Text style={[styles.rowValue, mono && styles.rowMono]} selectable>
        {value}
      </Text>
    </View>
  );
}

function Divider() {
  return <View style={styles.divider} />;
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function formatCurrency(val) {
  if (val == null) return '—';
  return '$' + val.toLocaleString('en-US');
}

function formatMailingAddress(parcel) {
  const parts = [parcel.owner_address, parcel.owner_city, parcel.owner_zip]
    .filter(Boolean);
  return parts.join(', ') || null;
}

function classBadgeStyle(label) {
  const colors = {
    Agricultural: { backgroundColor: '#e8f5e9', borderColor: '#66bb6a' },
    Commercial:   { backgroundColor: '#fff3e0', borderColor: '#ffa726' },
    Industrial:   { backgroundColor: '#ede7f6', borderColor: '#9575cd' },
    Residential:  { backgroundColor: '#e3f2fd', borderColor: '#42a5f5' },
  };
  return colors[label] ?? { backgroundColor: '#f5f5f5', borderColor: '#bdbdbd' };
}

// ─── Styles ───────────────────────────────────────────────────────────────────

const styles = StyleSheet.create({
  sheet: {
    backgroundColor: '#ffffff',
    borderTopLeftRadius:  20,
    borderTopRightRadius: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: -3 },
    shadowOpacity: 0.12,
    shadowRadius: 8,
    elevation: 10,
  },
  handle: {
    backgroundColor: '#d0d0d0',
    width: 36,
  },
  content: {
    paddingHorizontal: 18,
    paddingBottom: 40,
  },

  // Header
  headerRow: {
    flexDirection:  'row',
    alignItems:     'flex-start',
    justifyContent: 'space-between',
    paddingTop:     6,
    marginBottom:   8,
  },
  headerLeft: { flex: 1, paddingRight: 8 },
  address: {
    fontSize:   18,
    fontWeight: '700',
    color:      '#1a1a1a',
    lineHeight: 24,
  },
  cityLine: {
    fontSize: 14,
    color:    '#555',
    marginTop: 2,
  },
  closeBtn: {
    width:           32,
    height:          32,
    borderRadius:    16,
    backgroundColor: '#f0f0f0',
    alignItems:      'center',
    justifyContent:  'center',
  },
  closeBtnText: {
    fontSize: 14,
    color:    '#555',
  },

  // Badge
  badge: {
    alignSelf:   'flex-start',
    paddingHorizontal: 10,
    paddingVertical:    4,
    borderRadius:      12,
    borderWidth:        1,
    marginBottom:       12,
  },
  badgeText: {
    fontSize:   12,
    fontWeight: '600',
  },

  // Value row
  valueRow: {
    flexDirection:  'row',
    justifyContent: 'space-between',
    gap:            8,
    marginBottom:   4,
  },
  valueCard: {
    flex:            1,
    backgroundColor: '#f7f9fc',
    borderRadius:    10,
    padding:         12,
    alignItems:      'center',
  },
  valueCardAmount: {
    fontSize:   15,
    fontWeight: '700',
    color:      '#2a5caa',
    textAlign:  'center',
  },
  valueCardLabel: {
    fontSize:  10,
    color:     '#777',
    marginTop:  4,
    textAlign: 'center',
  },

  // Sections / rows
  divider: {
    height:          1,
    backgroundColor: '#ececec',
    marginVertical:  14,
  },
  section: { marginBottom: 4 },
  sectionTitle: {
    fontSize:     12,
    fontWeight:   '700',
    color:        '#2a5caa',
    textTransform:'uppercase',
    letterSpacing: 0.8,
    marginBottom: 10,
  },
  row: {
    flexDirection:  'row',
    justifyContent: 'space-between',
    alignItems:     'flex-start',
    marginBottom:   8,
    gap:            12,
  },
  rowLabel: {
    fontSize: 13,
    color:    '#777',
    flex:     1,
  },
  rowValue: {
    fontSize:  13,
    color:     '#1a1a1a',
    flex:      2,
    textAlign: 'right',
  },
  rowMono: {
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    fontSize:   12,
  },

  // Attribution
  attribution: {
    backgroundColor: '#f7f9fc',
    borderRadius:    10,
    padding:         12,
    marginTop:       4,
  },
  attributionLabel: {
    fontSize:     11,
    fontWeight:   '700',
    color:        '#555',
    textTransform:'uppercase',
    letterSpacing: 0.6,
    marginBottom:  4,
  },
  attributionText: {
    fontSize:  13,
    color:     '#333',
    marginBottom: 6,
  },
  attributionNote: {
    fontSize:  11,
    color:     '#888',
    lineHeight: 16,
  },
});
