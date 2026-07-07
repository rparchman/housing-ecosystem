import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { getPropertyDetail } from '../api/propertyDetailApi';
import { PropertyDetail } from '../models/propertyDetail';
import { PropertyDetailHeader } from './PropertyDetailHeader';
import { PropertyDetailMap } from './PropertyDetailMap';
import { PropertyDetailAttachments } from './PropertyDetailAttachments';
import { PropertyHistory } from './PropertyHistory';

// inside the component render, after attachments:
<PropertyHistory propertyId={property.id} />

export function PropertyDetailPage() {
  const { id } = useParams();
  const [property, setProperty] = useState<PropertyDetail | null>(null);

  useEffect(() => {
    if (!id) return;

    getPropertyDetail(id).then(setProperty);
  }, [id]);

  if (!property) {
    return <div>Loading...</div>;
  }

  return (
    <div style={{ padding: '20px' }}>
      <PropertyDetailHeader property={property} />

      <h3>Property Information</h3>
      <div>
        <div>Parcel ID: {property.parcelId}</div>
        <div>Address: {property.address}</div>
        <div>City: {property.city}</div>
        <div>County: {property.county}</div>
        <div>ZIP: {property.zip}</div>
        <div>Status: {property.status}</div>
        <div>Land Bank: {property.landBank ? 'Yes' : 'No'}</div>
        <div>Price: {property.price ? `$${property.price}` : 'N/A'}</div>
        <div>Sqft: {property.sqft ?? 'N/A'}</div>
      </div>

      <h3>County Data</h3>
      <div>
        <div>Assessed Value: {property.assessedValue ?? 'N/A'}</div>
        <div>Taxable Value: {property.taxableValue ?? 'N/A'}</div>
        <div>Year Built: {property.yearBuilt ?? 'N/A'}</div>
        <div>Lot Size: {property.lotSize ? `${property.lotSize} sqft` : 'N/A'}</div>
      </div>

      <PropertyDetailMap lat={property.lat} lng={property.lng} />

      <PropertyDetailAttachments attachments={property.attachments} />
    </div>
  );
}
