/**
 * Search Results — left-aligned panel, editorial list layout.
 * No card grid. Divider-separated items with asymmetric content.
 */

import { motion } from 'framer-motion';
import type { Property, SearchResponse } from '../../types';
import './SearchResults.css';

interface SearchResultsProps {
  response: SearchResponse;
  onPropertySelect: (property: Property) => void;
  onClose: () => void;
}

export default function SearchResults({
  response,
  onPropertySelect,
  onClose,
}: SearchResultsProps) {
  const { parsed_filters, results, total } = response;

  // Build a human-readable summary of what was parsed
  const filterParts: string[] = [];
  if (parsed_filters.rooms) filterParts.push(`${parsed_filters.rooms} rooms`);
  if (parsed_filters.max_price) filterParts.push(`≤ $${(parsed_filters.max_price / 1000).toFixed(0)}k`);
  if (parsed_filters.district) filterParts.push(parsed_filters.district);
  if (parsed_filters.proximity_to) filterParts.push(`near ${parsed_filters.proximity_to.replace('_', ' ')}`);

  const getDisplayScore = (property: Property) => {
    if (!property.comfort_score) return null;

    const categories = [
      { key: 'transport', label: '🚇 Transport', val: property.comfort_score.transport_score },
      { key: 'shopping', label: '🛍️ Shopping', val: property.comfort_score.shopping_score },
      { key: 'education', label: '📚 Education', val: property.comfort_score.education_score },
      { key: 'green_space', label: '🌳 Parks', val: property.comfort_score.green_space_score },
      { key: 'safety', label: '🛡️ Safety', val: property.comfort_score.safety_score },
      { key: 'healthcare', label: '🏥 Health', val: property.comfort_score.healthcare_score },
      { key: 'entertainment', label: '🎭 Fun', val: property.comfort_score.entertainment_score },
    ];

    const sortCat = parsed_filters.sort_by_comfort;
    let selected = null;

    if (sortCat && sortCat !== 'overall') {
      selected = categories.find(c => c.key === sortCat);
    }

    if (!selected) {
      // Find the highest score category
      selected = categories.reduce((prev, current) => {
        return (current.val || 0) > (prev.val || 0) ? current : prev;
      });
    }

    if (!selected || selected.val == null) return null;

    const score = selected.val;
    const cls = score >= 70 ? 'badge-high' : score >= 40 ? 'badge-mid' : 'badge-low';
    const icon = selected.label.split(' ')[0];

    return (
      <span className={`badge badge-score ${cls}`} title={selected.label}>
        {icon} {score.toFixed(0)}
      </span>
    );
  };

  return (
    <motion.aside
      className="results"
      initial={{ x: -20, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      exit={{ x: -20, opacity: 0 }}
      transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
    >
      {/* Header */}
      <header className="results-head">
        <div className="results-head-top">
          <span className="label">Search results</span>
          <button className="btn btn-ghost" onClick={onClose} aria-label="Close">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M18 6 6 18M6 6l12 12" />
            </svg>
          </button>
        </div>
        <p className="results-count h-display h-lg">
          <span className="mono">{total}</span> {total === 1 ? 'property' : 'properties'}
        </p>
        {filterParts.length > 0 && (
          <div className="results-filters">
            {filterParts.map((f, i) => (
              <span className="badge-tag" key={i}>{f}</span>
            ))}
          </div>
        )}
      </header>

      {/* List — no cards, divider-separated editorial items */}
      <div className="results-list">
        {results.length === 0 ? (
          <div className="results-empty">
            <p>No matches found.</p>
            <p className="results-empty-sub">Try widening your criteria.</p>
          </div>
        ) : (
          results.map((property, index) => (
            <motion.article
              key={property.id}
              className="result-item"
              onClick={() => onPropertySelect(property)}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.04, duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
              role="button"
              tabIndex={0}
              id={`result-${property.id}`}
            >
              <div className="result-left">
                <span className="result-index mono">{String(index + 1).padStart(2, '0')}</span>
              </div>
              <div className="result-body">
                <div className="result-price-row">
                  <span className="result-price mono">${property.price.toLocaleString()}</span>
                  {getDisplayScore(property)}
                  {property.model_3d_url && (
                    <span className="badge-tag">3D</span>
                  )}
                </div>
                <p className="result-title">{property.title}</p>
                <div className="result-meta">
                  {property.rooms && <span>{property.rooms} rooms</span>}
                  {property.area_sqm && <span>{property.area_sqm} m²</span>}
                  {property.floor && <span>Floor {property.floor}/{property.total_floors}</span>}
                </div>
              </div>
            </motion.article>
          ))
        )}
      </div>
    </motion.aside>
  );
}
