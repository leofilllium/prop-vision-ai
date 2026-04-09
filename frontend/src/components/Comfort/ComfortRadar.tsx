/**
 * ComfortRadar — NOT a radar chart (too generic/AI-feeling).
 * Instead: horizontal progress bars with mono numbers,
 * a large overall score, and minimal labels.
 */

import type { ComfortScoreDetail } from '../../types';
import './ComfortRadar.css';

interface ComfortRadarProps {
  scores: ComfortScoreDetail;
}

const DIMS = [
  { key: 'transport',   label: 'Transport',   icon: '→' },
  { key: 'shopping',    label: 'Shopping',     icon: '□' },
  { key: 'education',   label: 'Education',    icon: '△' },
  { key: 'green_space', label: 'Green Space',  icon: '○' },
  { key: 'safety',      label: 'Safety',       icon: '◇' },
  { key: 'healthcare',  label: 'Healthcare',   icon: '✚' },
  { key: 'entertainment', label: 'Entertainment', icon: '★' },
] as const;

export default function ComfortRadar({ scores }: ComfortRadarProps) {
  const scoreColor = (s: number) => {
    if (s >= 70) return 'var(--score-high)';
    if (s >= 40) return 'var(--score-mid)';
    return 'var(--score-low)';
  };

  const overall = scores.overall_score;

  return (
    <div className="comfort">
      {/* Overall — large, left-aligned, not centered in a circle */}
      <div className="comfort-overall">
        <span className="comfort-overall-num mono" style={{ color: scoreColor(overall) }}>
          {overall.toFixed(0)}
        </span>
        <div className="comfort-overall-meta">
          <span className="comfort-overall-of mono">/100</span>
          <span className="label">Overall</span>
        </div>
      </div>

      {/* Dimension bars */}
      <div className="comfort-dims">
        {DIMS.map(({ key, label, icon }) => {
          const dimScores = scores.scores[key as keyof typeof scores.scores];
          const val = dimScores.score;

          return (
            <div className="comfort-dim" key={key}>
              <div className="comfort-dim-head">
                <span className="comfort-dim-icon">{icon}</span>
                <span className="comfort-dim-label">{label}</span>
                <span className="comfort-dim-val mono" style={{ color: scoreColor(val) }}>
                  {val.toFixed(0)}
                </span>
              </div>
              <div className="comfort-bar">
                <div
                  className="comfort-bar-fill"
                  style={{
                    width: `${val}%`,
                    background: scoreColor(val),
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
