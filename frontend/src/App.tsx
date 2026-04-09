import { useState, useCallback } from 'react';
import { Routes, Route } from 'react-router-dom';
import MapView from './components/Map/MapView';
import PropertyPanel from './components/Property/PropertyPanel';
import AISearchBar from './components/Search/AISearchBar';
import SearchResults from './components/Search/SearchResults';
import NavBar from './components/Nav/NavBar';
import Dashboard from './components/Dashboard/Dashboard';
import AdminPage from './components/Admin/AdminPage';
import AdminLoginPage from './components/Admin/AdminLoginPage';
import LoginPage from './components/Auth/LoginPage';
import RegisterPage from './components/Auth/RegisterPage';
import ProtectedRoute from './components/Auth/ProtectedRoute';
import AdminProtectedRoute from './components/Auth/AdminProtectedRoute';
import type { Property, SearchResponse } from './types';

export default function App() {
  const [selectedProperty, setSelectedProperty] = useState<Property | null>(null);
  const [searchResults, setSearchResults] = useState<SearchResponse | null>(null);
  const [isPanelOpen, setIsPanelOpen] = useState(false);
  const [flyTo, setFlyTo] = useState<[number, number] | null>(null);

  const handlePropertySelect = useCallback((property: Property) => {
    setSelectedProperty(property);
    setIsPanelOpen(true);
    setFlyTo(property.location.coordinates as [number, number]);
  }, []);

  const handleSearchResults = useCallback((results: SearchResponse) => {
    setSearchResults(results);
    setSelectedProperty(null);
    setIsPanelOpen(false);
    if (results.results.length > 0) {
      const first = results.results[0];
      setFlyTo(first.location.coordinates as [number, number]);
    }
  }, []);

  const handleClosePanel = useCallback(() => {
    setIsPanelOpen(false);
    setSelectedProperty(null);
  }, []);

  const handleCloseResults = useCallback(() => {
    setSearchResults(null);
  }, []);

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/admin/login" element={<AdminLoginPage />} />
      <Route
        path="/analytics"
        element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/admin"
        element={
          <AdminProtectedRoute>
            <AdminPage />
          </AdminProtectedRoute>
        }
      />
      <Route
        path="/*"
        element={
          <ProtectedRoute>
            <div className="app-layout">
              {/* Map fills entire viewport */}
              <div className="map-area">
                <MapView
                  properties={searchResults?.results || []}
                  selectedProperty={selectedProperty}
                  onPropertySelect={handlePropertySelect}
                  flyTo={flyTo}
                />

                {/* Nav — pinned top-left, minimal */}
                <NavBar />

                {/* AI Search — pinned top-center */}
                <AISearchBar onResults={handleSearchResults} avoidRightPanel={isPanelOpen} />

                {/* Search Results — left panel overlay */}
                {searchResults && !isPanelOpen && (
                  <SearchResults
                    response={searchResults}
                    onPropertySelect={handlePropertySelect}
                    onClose={handleCloseResults}
                  />
                )}
              </div>

              {/* Property detail — slides in from right */}
              {isPanelOpen && selectedProperty && (
                <PropertyPanel
                  property={selectedProperty}
                  onClose={handleClosePanel}
                />
              )}
            </div>
          </ProtectedRoute>
        }
      />
    </Routes>
  );
}
