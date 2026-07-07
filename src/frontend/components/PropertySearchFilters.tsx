import { useState } from 'react';
import { PropertySearchQuery } from '../models/propertySearch';

interface Props {
  onSearch: (query: PropertySearchQuery) => void;
}

export function PropertySearchFilters({ onSearch }: Props) {
  const [filters, setFilters] = useState<PropertySearchQuery>({
    page: 1,
    limit: 25,
    sort: 'date_added_desc',
  });

  function updateField<K extends keyof PropertySearchQuery>(key: K, value: PropertySearchQuery[K]) {
    setFilters((prev) => ({
      ...prev,
      [key]: value === '' ? undefined : value,
    }));
  }

  function handleSearch() {
    onSearch(filters);
  }

  return (
    <div style={{ padding: '16px', border: '1px solid #ddd', borderRadius: '8px' }}>
      <h2>Filters</h2>

      {/* Search text */}
      <div>
        <label>Search Text</label>
        <input
          type="text"
          value={filters.q || ''}
          onChange={(e) => updateField('q', e.target.value)}
        />
      </div>

      {/* City */}
      <div>
        <label>City</label>
        <input
          type="text"
          value={filters.city || ''}
          onChange={(e) => updateField('city', e.target.value)}
        />
      </div>

      {/* County */}
      <div>
        <label>County</label>
        <input
          type="text"
          value={filters.county || ''}
          onChange={(e) => updateField('county', e.target.value)}
        />
      </div>

      {/* ZIP */}
      <div>
        <label>ZIP Code</label>
        <input
          type="text"
          value={filters.zip || ''}
          onChange={(e) => updateField('zip', e.target.value)}
        />
      </div>

      {/* Parcel ID */}
      <div>
        <label>Parcel ID</label>
        <input
          type="text"
          value={filters.parcelId || ''}
          onChange={(e) => updateField('parcelId', e.target.value)}
        />
      </div>

      {/* Status */}
      <div>
        <label>Status</label>
        <select
          value={filters.status || ''}
          onChange={(e) => updateField('status', e.target.value)}
        >
          <option value="">Any</option>
          <option value="active">Active</option>
          <option value="sold">Sold</option>
          <option value="demo">Demo</option>
        </select>
      </div>

      {/* Price Range */}
      <div>
        <label>Min Price</label>
        <input
          type="number"
          value={filters.minPrice || ''}
          onChange={(e) => updateField('minPrice', Number(e.target.value))}
        />

        <label>Max Price</label>
        <input
          type="number"
          value={filters.maxPrice || ''}
          onChange={(e) => updateField('maxPrice', Number(e.target.value))}
        />
      </div>

      {/* Sqft Range */}
      <div>
        <label>Min Sqft</label>
        <input
          type="number"
          value={filters.minSqft || ''}
          onChange={(e) => updateField('minSqft', Number(e.target.value))}
        />

        <label>Max Sqft</label>
        <input
          type="number"
          value={filters.maxSqft || ''}
          onChange={(e) => updateField('maxSqft', Number(e.target.value))}
        />
      </div>

      {/* Land Bank Only */}
      <div>
        <label>
          <input
            type="checkbox"
            checked={filters.landBankOnly || false}
            onChange={(e) => updateField('landBankOnly', e.target.checked)}
          />
          Land Bank Only
        </label>
      </div>

      {/* Has Structure */}
      <div>
        <label>
          <input
            type="checkbox"
            checked={filters.hasStructure || false}
            onChange={(e) => updateField('hasStructure', e.target.checked)}
          />
          Has Structure
        </label>
      </div>

      {/* Sorting */}
      <div>
        <label>Sort</label>
        <select
          value={filters.sort || ''}
          onChange={(e) => updateField('sort', e.target.value)}
        >
          <option value="date_added_desc">Newest</option>
          <option value="price_asc">Price: Low → High</option>
          <option value="price_desc">Price: High → Low</option>
          <option value="sqft_desc">Sqft: Largest</option>
        </select>
      </div>

      {/* Search Button */}
      <button onClick={handleSearch} style={{ marginTop: '16px' }}>
        Search
      </button>
    </div>
  );
}
