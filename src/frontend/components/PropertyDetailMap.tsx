interface Props {
  lat: number | null;
  lng: number | null;
}

export function PropertyDetailMap({ lat, lng }: Props) {
  if (!lat || !lng) {
    return <div>No map location available.</div>;
  }

  return (
    <div style={{ marginTop: '20px' }}>
      <h3>Map</h3>
      <div
        style={{
          width: '100%',
          height: '300px',
          background: '#eee',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        Map Placeholder (lat: {lat}, lng: {lng})
      </div>
    </div>
  );
}
