import { PropertyDetail } from '../models/propertyDetail';

interface Props {
  property: PropertyDetail;
}

export function PropertyDetailHeader({ property }: Props) {
  return (
    <div style={{ marginBottom: '20px' }}>
      <h1>{property.address}</h1>
      <h2>{property.city}, {property.county} {property.zip}</h2>
      <h3>{property.price ? `$${property.price}` : 'No Price Listed'}</h3>
    </div>
  );
}