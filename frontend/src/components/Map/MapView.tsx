/**
 * MapView — Mapbox GL JS v3 with dark-style, custom property markers.
 * Markers use mono typography for prices. No bouncing, no pulsing.
 */

import { useRef, useEffect, useState } from 'react';
import Map, { Marker, NavigationControl, Popup } from 'react-map-gl';
import type { MapRef } from 'react-map-gl';
import { config } from '../../config';
import type { Property } from '../../types';
import { useProperties } from '../../hooks/useApi';
import './MapView.css';

interface MapViewProps {
  properties: Property[];
  selectedProperty: Property | null;
  onPropertySelect: (property: Property) => void;
  flyTo: [number, number] | null;
}

export default function MapView({
  properties,
  selectedProperty,
  onPropertySelect,
  flyTo,
}: MapViewProps) {
  const mapRef = useRef<MapRef>(null);
  const [hoveredId, setHoveredId] = useState<string | null>(null);

  const { data: allProperties } = useProperties({ limit: 100 });
  const displayProperties = properties.length > 0
    ? properties
    : allProperties?.results || [];

  useEffect(() => {
    if (flyTo && mapRef.current) {
      mapRef.current.flyTo({
        center: flyTo,
        zoom: 15,
        duration: 1800,
        essential: true,
      });
    }
  }, [flyTo]);

  // Force map resize on initial render to fix black map / cropped map bug
  useEffect(() => {
    const timer = setTimeout(() => {
      window.dispatchEvent(new Event('resize'));
    }, 300);
    return () => clearTimeout(timer);
  }, []);

  const UZS_TO_USD = 12800;

  const fmtPrice = (price: number, currency: string) => {
    const usdPrice = currency === 'UZS' ? price / UZS_TO_USD : price;
    if (usdPrice >= 1_000_000) return `${(usdPrice / 1_000_000).toFixed(1)}m`;
    if (usdPrice >= 1_000) return `${(usdPrice / 1_000).toFixed(1)}k`;
    return `${Math.round(usdPrice)}`;
  };


  const scoreColor = (score: number | null | undefined) => {
    if (!score) return 'var(--text-ghost)';
    if (score >= 70) return 'var(--score-high)';
    if (score >= 40) return 'var(--score-mid)';
    return 'var(--score-low)';
  };

  return (
    <Map
      ref={mapRef}
      mapboxAccessToken={config.mapboxToken}
      initialViewState={{
        longitude: config.map.center.lng,
        latitude: config.map.center.lat,
        zoom: config.map.zoom,
        pitch: 50,
        bearing: -15,
      }}
      style={{ width: '100%', height: '100%' }}
      mapStyle={config.map.style}
      maxPitch={65}
      antialias
    >
      <NavigationControl position="bottom-right" showCompass showZoom visualizePitch />

      {displayProperties.map((p) => {
        const isSelected = selectedProperty?.id === p.id;
        const isHovered = hoveredId === p.id;

        return (
          <Marker
            key={p.id}
            longitude={p.location.coordinates[0]}
            latitude={p.location.coordinates[1]}
            anchor="bottom"
            onClick={(e) => {
              e.originalEvent.stopPropagation();
              onPropertySelect(p);
            }}
          >
            <div
              className={`pin ${isSelected ? 'pin--active' : ''} ${isHovered ? 'pin--hover' : ''}`}
              onMouseEnter={() => setHoveredId(p.id)}
              onMouseLeave={() => setHoveredId(null)}
              style={{ '--pin-accent': scoreColor(p.comfort_score?.overall_score) } as React.CSSProperties}
            >
              <span className="pin-price mono">${fmtPrice(p.price, p.currency)}</span>
              {p.rooms && <span className="pin-rooms">{p.rooms}r</span>}
              <div className="pin-dot" />
            </div>
          </Marker>
        );
      })}

      {/* Hover popup — editorial, not card-like */}
      {hoveredId && (() => {
        const p = displayProperties.find(x => x.id === hoveredId);
        if (!p || selectedProperty?.id === p.id) return null;
        return (
          <Popup
            longitude={p.location.coordinates[0]}
            latitude={p.location.coordinates[1]}
            anchor="bottom"
            offset={48}
            closeButton={false}
            closeOnClick={false}
            className="map-popup"
          >
            <div className="popup-inner">
              <p className="popup-title">{p.title}</p>
              <div className="popup-row">
                <span className="mono popup-price">${Math.round(p.currency === 'UZS' ? p.price / UZS_TO_USD : p.price).toLocaleString()}</span>
                {p.rooms && <span className="popup-meta">{p.rooms} rooms</span>}
                {p.area_sqm && <span className="popup-meta">{p.area_sqm} m²</span>}
              </div>
            </div>
          </Popup>
        );
      })()}
    </Map>
  );
}
