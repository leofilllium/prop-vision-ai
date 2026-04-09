/**
 * VideoPlayer — Cinematic Scroll-to-Seek Player
 *
 * Scroll wheel forward  → advance currentTime (forward through property tour)
 * Scroll wheel backward → rewind  currentTime
 * Click                 → play / pause toggle
 *
 * Visual "zoom illusion": video scales from 1.0 → 1.08 as progress increases,
 * giving the sensation of "zooming in" to the property as you scroll forward.
 *
 * No native browser controls — fully custom progress bar + time display.
 */

import { useRef, useState, useCallback, useEffect } from 'react';
import './VideoPlayer.css';

interface VideoPlayerProps {
  videoUrl: string;
  title?: string;
}

function formatTime(secs: number): string {
  if (!isFinite(secs) || isNaN(secs)) return '0:00';
  const m = Math.floor(secs / 60);
  const s = Math.floor(secs % 60);
  return `${m}:${s.toString().padStart(2, '0')}`;
}

/** Clamp value between min and max */
function clamp(v: number, min: number, max: number) {
  return Math.max(min, Math.min(max, v));
}

export default function VideoPlayer({ videoUrl, title }: VideoPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const rootRef = useRef<HTMLDivElement>(null);
  const progressTrackRef = useRef<HTMLDivElement>(null);

  const [duration, setDuration] = useState(0);
  const [currentTime, setCurrentTime] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [hinted, setHinted] = useState(false);           // user scrolled at least once
  const [showPlayFlash, setShowPlayFlash] = useState<'play' | 'pause' | null>(null);
  const [scrollDir, setScrollDir] = useState<'fwd' | 'back' | null>(null);
  const [seekBadge, setSeekBadge] = useState<string | null>(null);

  // Custom cursor
  const [cursor, setCursor] = useState({ x: 0, y: 0, visible: false });

  // Drag state for progress bar
  const dragging = useRef(false);

  // Timers
  const scrollDirTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const seekBadgeTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const playFlashTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Zoom — RAF lerp so scale animates smoothly regardless of timeupdate granularity
  const targetScaleRef = useRef(1.0);
  const displayScaleRef = useRef(1.0);
  const rafRef = useRef<number | null>(null);

  // ── Video event handlers ─────────────────────────────────────────────────
  const handleTimeUpdate = useCallback(() => {
    if (videoRef.current) setCurrentTime(videoRef.current.currentTime);
  }, []);

  const handleDurationChange = useCallback(() => {
    if (videoRef.current) setDuration(videoRef.current.duration);
  }, []);

  const handlePlay = useCallback(() => setIsPlaying(true), []);
  const handlePause = useCallback(() => setIsPlaying(false), []);

  // ── Scroll-to-seek ───────────────────────────────────────────────────────
  const SEEK_PER_TICK = 0.01; // seconds per scroll tick

  const handleWheel = useCallback((e: WheelEvent) => {
    e.preventDefault();
    const video = videoRef.current;
    if (!video || !duration) return;

    setHinted(true);

    const delta = e.deltaY > 0 ? SEEK_PER_TICK : -SEEK_PER_TICK;
    const next = clamp(video.currentTime + delta, 0, duration);
    video.currentTime = next;
    setCurrentTime(next);

    // Direction indicator
    const dir = delta > 0 ? 'fwd' : 'back';
    setScrollDir(dir);
    if (scrollDirTimer.current) clearTimeout(scrollDirTimer.current);
    scrollDirTimer.current = setTimeout(() => setScrollDir(null), 600);

    // Seek badge
    const sign = delta > 0 ? '+' : '';
    const badgeText = `${sign}${Math.abs(delta).toFixed(2)}s`;
    setSeekBadge(badgeText);
    if (seekBadgeTimer.current) clearTimeout(seekBadgeTimer.current);
    seekBadgeTimer.current = setTimeout(() => setSeekBadge(null), 600);

  }, [duration]);

  useEffect(() => {
    const root = rootRef.current;
    if (!root) return;
    root.addEventListener('wheel', handleWheel, { passive: false });
    return () => root.removeEventListener('wheel', handleWheel);
  }, [handleWheel]);

  // ── Click to play/pause ──────────────────────────────────────────────────
  const handleClick = useCallback(() => {
    const video = videoRef.current;
    if (!video) return;
    if (video.paused) {
      video.play();
      setShowPlayFlash('play');
    } else {
      video.pause();
      setShowPlayFlash('pause');
    }
    if (playFlashTimer.current) clearTimeout(playFlashTimer.current);
    playFlashTimer.current = setTimeout(() => setShowPlayFlash(null), 700);
    setHinted(true);
  }, []);

  // ── Progress bar scrubbing ───────────────────────────────────────────────
  const seekToFraction = useCallback((fraction: number) => {
    const video = videoRef.current;
    if (!video || !duration) return;
    const t = clamp(fraction * duration, 0, duration);
    video.currentTime = t;
    setCurrentTime(t);
    setHinted(true);
  }, [duration]);

  const getTrackFraction = useCallback((e: React.MouseEvent | MouseEvent) => {
    const track = progressTrackRef.current;
    if (!track) return 0;
    const rect = track.getBoundingClientRect();
    return clamp((e.clientX - rect.left) / rect.width, 0, 1);
  }, []);

  const handleTrackMouseDown = useCallback((e: React.MouseEvent) => {
    dragging.current = true;
    seekToFraction(getTrackFraction(e));
  }, [seekToFraction, getTrackFraction]);

  useEffect(() => {
    const onMove = (e: MouseEvent) => {
      if (dragging.current) seekToFraction(getTrackFraction(e));
    };
    const onUp = () => { dragging.current = false; };
    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
    return () => {
      window.removeEventListener('mousemove', onMove);
      window.removeEventListener('mouseup', onUp);
    };
  }, [seekToFraction, getTrackFraction]);

  // ── Custom cursor tracking ───────────────────────────────────────────────
  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    const root = rootRef.current;
    if (!root) return;
    const rect = root.getBoundingClientRect();
    setCursor({ x: e.clientX - rect.left, y: e.clientY - rect.top, visible: true });
  }, []);

  const handleMouseLeave = useCallback(() => {
    setCursor(c => ({ ...c, visible: false }));
  }, []);

  // ── Progress (for progress bar only) ────────────────────────────────────
  const progress = duration > 0 ? currentTime / duration : 0;

  // ── Zoom illusion: keep targetScale in sync with currentTime ─────────────
  useEffect(() => {
    targetScaleRef.current = 1.0 + (duration > 0 ? currentTime / duration : 0) * 0.08;
  }, [currentTime, duration]);

  // ── RAF lerp loop: smoothly drives displayScale → targetScale ────────────
  // Writes directly to the DOM element — no React re-render per frame.
  // Lerp factor 0.12 at 60 fps ≈ 130 ms time-constant: responsive to scroll,
  // smooth enough to bridge the ~250 ms gaps between timeupdate events.
  useEffect(() => {
    const tick = () => {
      const target = targetScaleRef.current;
      const prev = displayScaleRef.current;
      const next = prev + (target - prev) * 0.12;
      if (Math.abs(next - prev) > 0.00005) {
        displayScaleRef.current = next;
        if (videoRef.current) {
          videoRef.current.style.transform = `scale(${next})`;
        }
      }
      rafRef.current = requestAnimationFrame(tick);
    };
    rafRef.current = requestAnimationFrame(tick);
    return () => {
      if (rafRef.current !== null) cancelAnimationFrame(rafRef.current);
    };
  }, []); // intentionally empty — refs handle target updates without re-subscribing

  // ── Cleanup ──────────────────────────────────────────────────────────────
  useEffect(() => {
    return () => {
      if (scrollDirTimer.current) clearTimeout(scrollDirTimer.current);
      if (seekBadgeTimer.current) clearTimeout(seekBadgeTimer.current);
      if (playFlashTimer.current) clearTimeout(playFlashTimer.current);
    };
  }, []);

  return (
    <div
      ref={rootRef}
      className="vp-root"
      onClick={handleClick}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
    >
      {/* ── Video ── */}
      <video
        ref={videoRef}
        className="vp-video"
        src={videoUrl}
        muted
        playsInline
        preload="metadata"
        onTimeUpdate={handleTimeUpdate}
        onDurationChange={handleDurationChange}
        onLoadedMetadata={handleDurationChange}
        onPlay={handlePlay}
        onPause={handlePause}
      />

      {/* ── Gradient overlays ── */}
      <div className="vp-gradient-top" />
      <div className="vp-gradient-bottom" />

      {/* ── Title badge ── */}
      {title && <div className="vp-title">{title}</div>}

      {/* ── Scroll hint ── */}
      <div className={`vp-hint ${hinted ? 'vp-hint--hidden' : ''}`}>
        <div className="vp-hint-icon">
          <div className="vp-hint-scroll-icon">
            <span>▲</span>
            <span>▼</span>
          </div>
        </div>
        <span className="vp-hint-text">Scroll to Explore</span>
        <span className="vp-hint-sub">up · backward &nbsp;/&nbsp; down · forward</span>
      </div>

      {/* ── Seek direction sidebar ── */}
      <div className={`vp-scroll-dir ${scrollDir ? 'vp-scroll-dir--visible' : ''}`}>
        <span className={`vp-scroll-dir-arrow ${scrollDir === 'fwd' ? 'vp-scroll-dir-arrow--active' : ''}`}>↓</span>
        <span style={{ fontSize: 9, color: 'rgba(255,255,255,0.3)', letterSpacing: '0.08em' }}>SEEK</span>
        <span className={`vp-scroll-dir-arrow ${scrollDir === 'back' ? 'vp-scroll-dir-arrow--active' : ''}`}>↑</span>
      </div>

      {/* ── Seek badge ── */}
      <div className={`vp-seek-badge ${seekBadge ? '' : 'vp-seek-badge--hidden'}`}>
        {seekBadge}
      </div>

      {/* ── Play/pause flash ── */}
      {showPlayFlash && (
        <div className="vp-play-flash">
          <div className="vp-play-flash-icon">
            {showPlayFlash === 'play' ? (
              <svg viewBox="0 0 24 24" fill="currentColor">
                <polygon points="5,3 19,12 5,21" />
              </svg>
            ) : (
              <svg viewBox="0 0 24 24" fill="currentColor">
                <rect x="6" y="4" width="4" height="16" rx="1" />
                <rect x="14" y="4" width="4" height="16" rx="1" />
              </svg>
            )}
          </div>
        </div>
      )}

      {/* ── Custom cursor ── */}
      {cursor.visible && (
        <div
          className="vp-cursor"
          style={{ left: cursor.x, top: cursor.y }}
        >
          <div className="vp-cursor-ring">
            <div className="vp-cursor-arrows">
              <span className="vp-cursor-arrow">↑</span>
              <span className="vp-cursor-arrow">↓</span>
            </div>
          </div>
        </div>
      )}

      {/* ── Bottom controls ── */}
      <div
        className="vp-controls"
        onClick={e => e.stopPropagation()} // don't toggle play when clicking controls
      >
        {/* Time row */}
        <div className="vp-time-row">
          <span className="vp-time">
            {formatTime(currentTime)}
            <span className="vp-time-sep"> / </span>
            {formatTime(duration)}
          </span>
          <button
            className="vp-playback-btn"
            onClick={handleClick}
            aria-label={isPlaying ? 'Pause' : 'Play'}
          >
            {isPlaying ? (
              <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                <rect x="6" y="4" width="4" height="16" rx="1" />
                <rect x="14" y="4" width="4" height="16" rx="1" />
              </svg>
            ) : (
              <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                <polygon points="5,3 19,12 5,21" />
              </svg>
            )}
          </button>
        </div>

        {/* Progress track */}
        <div
          ref={progressTrackRef}
          className="vp-progress-track"
          onMouseDown={handleTrackMouseDown}
        >
          <div
            className="vp-progress-fill"
            style={{ width: `${progress * 100}%` }}
          />
          <div
            className="vp-progress-thumb"
            style={{ left: `${progress * 100}%` }}
          />
        </div>
      </div>
    </div>
  );
}
