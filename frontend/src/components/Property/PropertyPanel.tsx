/**
 * PropertyPanel — slide-in detail panel, editorial layout.
 * Asymmetric spacing. Display heading for price.
 * No icon+heading+text+button card pattern.
 *
 * Media: Photos ←→ AI Video Walkthrough (2-state toggle)
 * 3D model feature is commented out but preserved below.
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { motion } from 'framer-motion';
import { useComfortScores } from '../../hooks/useApi';
import { useQueryClient } from '@tanstack/react-query';
import ComfortRadar from '../Comfort/ComfortRadar';
// import ThreeViewer from './ThreeViewer';   // 3D — commented out
import VideoPlayer from './VideoPlayer';
import apiClient from '../../api/client';
import type { Property } from '../../types';
import './PropertyPanel.css';

interface PropertyPanelProps {
  property: Property;
  onClose: () => void;
}

// ─── 3D model types — preserved but inactive ──────────────────────────────────
// type ReconStatus = 'idle' | 'generating' | 'processing' | 'completed' | 'failed';
// function proxyModelUrl(propertyId: string): string {
//   return `${apiClient.defaults.baseURL}/3d/${propertyId}/model`;
// }

type VideoStatus = 'idle' | 'generating' | 'processing' | 'completed' | 'failed';

function proxyVideoUrl(propertyId: string): string {
  return `${apiClient.defaults.baseURL}/video/${propertyId}/stream`;
}

export default function PropertyPanel({ property, onClose }: PropertyPanelProps) {
  const [photoIdx, setPhotoIdx] = useState(0);
  const [activeTab, setActiveTab] = useState<'photos' | 'video'>('photos');

  // ─── 3D state — commented out ────────────────────────────────────────────────
  // const [reconStatus, setReconStatus] = useState<ReconStatus>(
  //   property.model_3d_url ? 'completed' : 'idle'
  // );
  // const [modelUrl, setModelUrl] = useState<string | null>(
  //   property.model_3d_url ? proxyModelUrl(property.id) : null
  // );
  // const [reconProgress, setReconProgress] = useState<number | null>(null);
  // const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // ─── Video state ──────────────────────────────────────────────────────────────
  const [videoStatus, setVideoStatus] = useState<VideoStatus>(
    property.video_walkthrough_url ? 'completed' :
      property.video_generation_status === 'processing' ? 'processing' : 'idle'
  );
  const [videoUrl, setVideoUrl] = useState<string | null>(
    property.video_walkthrough_url ? proxyVideoUrl(property.id) : null
  );
  const [videoProgress, setVideoProgress] = useState<number | null>(null);
  const videoPollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const queryClient = useQueryClient();
  const { data: comfort, isLoading: comfortLoading } = useComfortScores(property.id);

  // ─── Photo nav ────────────────────────────────────────────────────────────────
  const nextPhoto = () => {
    if (property.photos.length > 0) setPhotoIdx(i => (i + 1) % property.photos.length);
  };
  const prevPhoto = () => {
    if (property.photos.length > 0) setPhotoIdx(i => (i - 1 + property.photos.length) % property.photos.length);
  };

  // ─── 3D polling — commented out ───────────────────────────────────────────────
  // const pollStatus = useCallback(async () => { ... }, [property.id, queryClient]);
  // const triggerGenerate = useCallback(async () => { ... }, [...]);
  // useEffect(() => { if (!property.model_3d_url) triggerGenerate(); ... }, [property.id]);

  // ─── Video polling ────────────────────────────────────────────────────────────
  const pollVideoStatus = useCallback(async () => {
    try {
      const { data } = await apiClient.get(`/video/${property.id}/status`);

      if (data.status === 'completed' && data.video_url) {
        setVideoUrl(proxyVideoUrl(property.id));
        setVideoStatus('completed');
        setVideoProgress(100);
        queryClient.invalidateQueries({ queryKey: ['property', property.id] });
        if (videoPollRef.current) {
          clearInterval(videoPollRef.current);
          videoPollRef.current = null;
        }
      } else if (data.status === 'failed') {
        setVideoStatus('failed');
        if (videoPollRef.current) {
          clearInterval(videoPollRef.current);
          videoPollRef.current = null;
        }
      }
    } catch {
      // ignore transient polling errors
    }
  }, [property.id, queryClient]);

  // ─── Auto-generate video on panel open (mirrors old 3D behavior) ──────────────
  const triggerVideoGenerate = useCallback(async () => {
    if (videoStatus !== 'idle') return;
    setVideoStatus('generating');

    // Check if a job was already submitted (e.g. previous session)
    try {
      const statusRes = await apiClient.get(`/video/${property.id}/status`).catch(() => null);
      if (statusRes?.data) {
        if (statusRes.data.status === 'completed' && statusRes.data.video_url) {
          setVideoUrl(proxyVideoUrl(property.id));
          setVideoStatus('completed');
          setVideoProgress(100);
          return;
        }
        if (statusRes.data.status === 'processing') {
          setVideoStatus('processing');
          videoPollRef.current = setInterval(pollVideoStatus, 5000);
          return;
        }
      }
    } catch { /* no existing job */ }

    // Submit new generation
    try {
      const { data } = await apiClient.post(`/video/generate/${property.id}`);
      if (data.status === 'completed' && data.video_url) {
        setVideoUrl(proxyVideoUrl(property.id));
        setVideoStatus('completed');
        setVideoProgress(100);
      } else if (data.status === 'processing') {
        setVideoStatus('processing');
        setVideoProgress(0);
        videoPollRef.current = setInterval(pollVideoStatus, 5000);
      } else {
        // failed or not configured
        setVideoStatus('failed');
      }
    } catch (err: unknown) {
      console.warn('Video generation error:', err);
      setVideoStatus('failed');
    }
  }, [videoStatus, property.id, pollVideoStatus]);

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (videoPollRef.current) clearInterval(videoPollRef.current);
    };
  }, [property.id]);

  // ─── Derived state ────────────────────────────────────────────────────────────
  const UZS_TO_USD = 12800;
  const usdPrice = property.currency === 'UZS' ? property.price / UZS_TO_USD : property.price;

  const hasVideo = !!videoUrl;
  const isGeneratingVideo = videoStatus === 'generating' || videoStatus === 'processing';
  const showPhotos = activeTab === 'photos';
  const showVideoTab = activeTab === 'video';

  return (
    <motion.aside
      className="panel"
      initial={{ x: 400 }}
      animate={{ x: 0 }}
      exit={{ x: 400 }}
      transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
    >
      {/* ── Close ─ */}
      <button className="panel-x btn btn-ghost" onClick={onClose} aria-label="Close">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M18 6 6 18M6 6l12 12" />
        </svg>
      </button>

      {/* ── Tabs ─ */}
      <div className="panel-tabs">
        <button
          className={`panel-tab ${showPhotos ? 'panel-tab--active' : ''}`}
          onClick={() => setActiveTab('photos')}
        >
          Photos
        </button>
        <button
          className={`panel-tab ${showVideoTab ? 'panel-tab--active' : ''}`}
          onClick={() => setActiveTab('video')}
        >
          AI Video Walkthrough
        </button>
      </div>

      {/* ── Media ─ */}
      <div className="panel-media">
        {showPhotos ? (
          <div className="panel-gallery">
            {property.photos.length > 0 ? (
              <>
                <img
                  src={property.photos[photoIdx].replace('/media/n/', '/media/o/')}
                  alt={property.title}
                  className="gallery-img"
                  onError={(e) => {
                    (e.target as HTMLImageElement).style.display = 'none';
                  }}
                />
                {property.photos.length > 1 && (
                  <div className="gallery-nav">
                    <button className="gallery-arrow" onClick={prevPhoto} aria-label="Previous">‹</button>
                    <span className="mono gallery-idx">
                      {String(photoIdx + 1).padStart(2, '0')} / {String(property.photos.length).padStart(2, '0')}
                    </span>
                    <button className="gallery-arrow" onClick={nextPhoto} aria-label="Next">›</button>
                  </div>
                )}
              </>
            ) : (
              <div className="gallery-empty">
                <span className="label">No photos</span>
              </div>
            )}
          </div>
        ) : (
          /* ── Video Tab Content ─ */
          <div className="panel-video-content">
            {hasVideo ? (
              <div className="panel-viewer">
                <VideoPlayer videoUrl={videoUrl!} title={property.title} />
              </div>
            ) : isGeneratingVideo ? (
              <div className="panel-video-generating">
                <span className="panel-3d-label label">Generating walkthrough…</span>
                <div className="panel-3d-track" style={{ width: '120px' }}>
                  <motion.div
                    className="panel-3d-fill panel-3d-fill--indeterminate"
                    animate={{ width: ['15%', '80%', '15%'] }}
                    transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut' }}
                  />
                </div>
                {videoProgress != null && videoProgress > 0 && (
                  <span className="panel-3d-pct mono">{videoProgress}%</span>
                )}
              </div>
            ) : videoStatus === 'failed' ? (
              <div className="panel-video-generating">
                <span className="label" style={{ color: 'var(--score-low)', marginBottom: '12px' }}>Generation failed</span>
                <button
                  className="btn-chip"
                  onClick={() => { setVideoStatus('idle'); triggerVideoGenerate(); }}
                >
                  ↺ Retry
                </button>
              </div>
            ) : (
              <div className="panel-video-generating">
                <button
                  className="btn-chip btn-chip--video panel-generate-btn"
                  onClick={triggerVideoGenerate}
                >
                  ▶ Generate AI Walkthrough
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      {/* ── Content ─ */}
      <div className="panel-body">
        {/* Price — the hero, display-sized */}
        <p className="panel-price h-display h-lg mono" style={{ marginTop: '1.5rem', position: 'relative', zIndex: 10 }}>
          ${Math.round(usdPrice).toLocaleString('en-US')}
        </p>

        {/* Title */}
        <h1 className="panel-title" id="property-detail-title">{property.title}</h1>

        {/* Stats row */}
        <div className="panel-stats">
          {property.rooms && (
            <div className="stat">
              <span className="stat-val mono">{property.rooms}</span>
              <span className="stat-lbl label">Rooms</span>
            </div>
          )}
          {property.area_sqm && (
            <div className="stat">
              <span className="stat-val mono">{property.area_sqm}</span>
              <span className="stat-lbl label">m²</span>
            </div>
          )}
          {property.floor && (
            <div className="stat">
              <span className="stat-val mono">{property.floor}<span className="stat-sep">/</span>{property.total_floors}</span>
              <span className="stat-lbl label">Floor</span>
            </div>
          )}
          {property.district && (
            <div className="stat">
              <span className="stat-val">{property.district}</span>
              <span className="stat-lbl label">District</span>
            </div>
          )}
        </div>

        {/* Address */}
        {property.address && (
          <p className="panel-addr">{property.address}</p>
        )}

        {/* Description */}
        {property.description && (
          <div className="panel-desc">
            <p>{property.description}</p>
          </div>
        )}

        {/* ── Divider ─ */}
        <hr className="divider" />

        {/* ── Comfort Analytics ─ */}
        <div className="panel-comfort">
          <div className="panel-comfort-head">
            <span className="label">Comfort Analytics</span>
            {comfort && (
              <span className={`badge badge-score ${comfort.data_confidence === 'HIGH' ? 'badge-high' :
                comfort.data_confidence === 'MEDIUM' ? 'badge-mid' : 'badge-low'
                }`}>
                {comfort.data_confidence}
              </span>
            )}
          </div>

          {comfortLoading ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <div className="skeleton" style={{ height: 10, width: '80%' }} />
              <div className="skeleton" style={{ height: 10, width: '60%' }} />
              <div className="skeleton" style={{ height: 10, width: '70%' }} />
              <div className="skeleton" style={{ height: 10, width: '50%' }} />
              <div className="skeleton" style={{ height: 10, width: '65%' }} />
            </div>
          ) : comfort ? (
            <ComfortRadar scores={comfort} />
          ) : (
            <p className="panel-comfort-na">Computing scores…</p>
          )}
        </div>
      </div>
    </motion.aside>
  );
}
