/**
 * AI Search Bar — floating over map, asymmetrically offset.
 * Monospaced AI label, craft details throughout.
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useSearch } from '../../hooks/useApi';
import type { SearchResponse } from '../../types';
import './AISearchBar.css';

interface AISearchBarProps {
  onResults: (results: SearchResponse) => void;
  avoidRightPanel?: boolean;
}

const HINTS = [
  '2-room flat near metro, under $70k',
  '3 xonali kvartira Chilanzar',
  'квартира рядом с парком Юнусабад',
  'spacious apartment near school, Sergeli',
  'studio under $35,000 with park nearby',
];

export default function AISearchBar({ onResults, avoidRightPanel = false }: AISearchBarProps) {
  const [query, setQuery] = useState('');
  const [hintIdx, setHintIdx] = useState(0);
  const [isFocused, setIsFocused] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const search = useSearch();

  // Cycle hints every 4 seconds
  useEffect(() => {
    if (isFocused) return;
    const id = setInterval(() => setHintIdx(i => i + 1), 4000);
    return () => clearInterval(id);
  }, [isFocused]);

  const currentHint = HINTS[hintIdx % HINTS.length];

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      if (!query.trim() || search.isPending) return;
      try {
        const results = await search.mutateAsync(query);
        onResults(results);
      } catch {
        /* handled in UI */
      }
    },
    [query, search, onResults]
  );

  return (
    <div className={`search-wrap ${avoidRightPanel ? 'search-wrap--panel-open' : ''}`}>
      <motion.form
        className="search-bar"
        onSubmit={handleSubmit}
        initial={{ y: -16, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1], delay: 0.15 }}
      >
        {/* Search icon */}
        <svg className="search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
          <circle cx="11" cy="11" r="7" />
          <path d="m20 20-3.5-3.5" />
        </svg>

        <input
          ref={inputRef}
          type="text"
          className="search-field"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          placeholder={currentHint}
          autoComplete="off"
          spellCheck={false}
          id="ai-search-input"
        />

        {/* AI indicator — mono, small, precise */}
        <span className="search-ai-tag mono">AI</span>

        <button
          type="submit"
          className="search-go"
          disabled={search.isPending || !query.trim()}
          aria-label="Search"
        >
          {search.isPending ? (
            <span className="search-spin" />
          ) : (
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
              <path d="M5 12h14M12 5l7 7-7 7" />
            </svg>
          )}
        </button>
      </motion.form>



      {/* Status line */}
      <AnimatePresence>
        {search.isPending && (
          <motion.p
            className="search-status"
            initial={{ opacity: 0, y: -6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
          >
            Parsing query…
          </motion.p>
        )}
        {search.isError && (
          <motion.p
            className="search-status search-status--err"
            initial={{ opacity: 0, y: -6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
          >
            Failed to parse — try rephrasing.
          </motion.p>
        )}
      </AnimatePresence>
    </div>
  );
}
