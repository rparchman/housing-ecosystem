import { PropertySearchResult } from '../models/propertySearch';

interface Props {
  results: PropertySearchResult[];
}

export function PropertySearchResults({ results }: Props) {
  if (!results.length) {
    return <div>No properties found.</div>;
  }

  return (
    <div style={{ marginTop: '20px' }}>
      {results.map((p) => (
        <div
          key={p.id}
          style={{
            padding: '12px',
            borderBottom: '1px solid #ddd',
            display: 'flex',
            justifyContent: 'space-between',
          }}
        >
          <div>
            <strong>{p.address}</strong>
            <div>{p.city}, {p.county} {p.zip}</div>
            <div>Parcel: {p.parcelId}</div>
            <div>Status: {p.status}</div>
          </div>

          <div style={{ textAlign: 'right' }}>
            <div>${p.price ?? 'N/A'}</div>
            <div>{p.sqft ? `${p.sqft} sqft` : 'No sqft'}</div>
            <div>{p.landBank ? 'Land Bank' : ''}</div>
          </div>
        </div>
      ))}
    </div>
  );
}
