import { Link } from 'react-router-dom';
import { useDashboard } from '../../hooks/useApi';
import { motion } from 'framer-motion';
import {
  BarChart,
  Bar,
  XAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import './Dashboard.css';
import { AmenityDemand, DistrictQueryStats, TopQuery } from '../../types';

const CHART_COLORS = ['#FF5533', '#FF8866', '#FFAA99', '#FFCCBB', '#FFEECC'];

export default function Dashboard() {
  const { data, isLoading, isError } = useDashboard();

  if (isLoading) return (
    <div className="dash-loading">
      <div className="skeleton" style={{ width: '40%', height: '2rem', marginBottom: '1rem' }} />
      <div className="skeleton" style={{ width: '100%', height: '300px' }} />
    </div>
  );

  if (isError || !data) return (
    <div className="dash-error">
      <p className="h-md h-display">Unable to load intelligence metrics.</p>
      <Link to="/" className="btn btn-primary" style={{ marginTop: '1.5rem' }}>Return to Map</Link>
    </div>
  );

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  };

  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: {
      y: 0,
      opacity: 1,
      transition: { duration: 0.5, ease: [0.19, 1, 0.22, 1] }
    }
  };

  return (
    <motion.main
      className="dash"
      initial="hidden"
      animate="visible"
      variants={containerVariants}
    >
      <header className="dash-header">
        <div className="dash-header-left">
          <span className="label">Network Intelligence Center</span>
          <h1 className="h-display h-xl">Market <span className="accent-text">Analytics</span></h1>
        </div>
        <div className="dash-header-right">
          <Link to="/" className="btn btn-ghost">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="m15 18-6-6 6-6" /></svg>
            Back to Vision
          </Link>
        </div>
      </header>

      <section className="dash-grid">
        {/* Row 1: Search Intelligence */}
        <motion.div className="dash-item" variants={itemVariants}>
          <div className="dash-item-head">
            <h2 className="label">Top AI Intents</h2>
          </div>
          <div className="dash-list">
            {(data.top_queries?.slice(0, 5) ?? []).map((q: TopQuery, i: number) => (
              <div key={i} className="dash-list-row">
                <span className="dash-list-idx mono">{String(i + 1).padStart(2, '0')}</span>
                <span className="dash-list-text">{q.query}</span>
                <span className="dash-list-val mono">{q.count}</span>
              </div>
            ))}
          </div>
        </motion.div>

        <motion.div className="dash-item" variants={itemVariants}>
          <div className="dash-item-head">
            <h2 className="label">Amenity Demand Heatmap</h2>
          </div>
          <div className="dash-chart" style={{ height: 220 }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={data.market_intelligence?.amenity_demand ?? []}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="count"
                  nameKey="amenity"
                >
                  {(data.market_intelligence?.amenity_demand ?? []).map((_: AmenityDemand, index: number) => (
                    <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} stroke="none" />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ background: 'rgba(20,20,20,0.9)', border: '1px solid var(--border)', borderRadius: '4px' }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="dash-legend">
            {data.market_intelligence?.amenity_demand?.slice(0, 3).map((a: AmenityDemand, i: number) => (
              <div key={i} className="legend-item">
                <span className="dot" style={{ backgroundColor: CHART_COLORS[i] }}></span>
                <span className="label-sm">{a.amenity.replace('_', ' ')}</span>
              </div>
            ))}
          </div>
        </motion.div>

        {/* Row 2: Geospatial & Efficiency */}
        <motion.div className="dash-item" variants={itemVariants}>
          <div className="dash-item-head">
            <h2 className="label">Value for Money (Comfort Efficiency)</h2>
          </div>
          <div className="dash-chart" style={{ height: 220 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={(data.inventory_insights?.comfort_price_efficiency ?? []).slice(0, 6)}>
                <XAxis dataKey="district" hide />
                <Tooltip
                  contentStyle={{ background: 'rgba(20,20,20,0.9)', border: '1px solid var(--border)', borderRadius: '4px' }}
                  labelStyle={{ color: 'var(--accent)' }}
                />
                <Bar dataKey="efficiency_gap" fill="var(--accent)" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <p className="caption">Higher score indicates better quality infrastructure per dollar spend.</p>
        </motion.div>

        <motion.div className="dash-item" variants={itemVariants}>
          <div className="dash-item-head">
            <h2 className="label">District Popularity (Search Mentions)</h2>
          </div>
          <div className="dash-list">
            {(data.market_intelligence?.district_popularity ?? []).slice(0, 6).map((d: DistrictQueryStats, i: number) => (
              <div key={i} className="dash-list-row">
                <span className="dash-list-text">{d.district}</span>
                <div className="prog-bar-bg">
                  <div className="prog-bar-fill" style={{ width: `${(d.search_count / (data.market_intelligence?.district_popularity?.[0].search_count || 1)) * 100}%` }}></div>
                </div>
                <span className="dash-list-val mono">{d.search_count}</span>
              </div>
            ))}
          </div>
        </motion.div>

        {/* Row 3: Impact */}
        <motion.div className="dash-item dash-item--wide" variants={itemVariants}>
          <div className="dash-item-head">
            <h2 className="label">Spatial Experience Adoption Index</h2>
          </div>
          <div className="dash-impact">
            <div className="dash-impact-item">
              <span className="dash-impact-val mono">{data.model_3d_views?.total ?? 0}</span>
              <span className="label">Total 3D Views</span>
            </div>
            <div className="dash-impact-item">
              <span className="dash-impact-val mono">+{data.model_3d_views?.last_7_days ?? 0}</span>
              <span className="label">Weekly Delta</span>
            </div>
            <div className="dash-impact-item">
              <span className="dash-impact-val mono">{data.inventory_insights?.spatial_conversion_lift ?? 0}%</span>
              <span className="label">Retention Lift</span>
            </div>
            <div className="dash-impact-item">
              <span className="dash-impact-val mono">${(data.market_intelligence?.average_budget?.avg_max_price ?? 0).toLocaleString()}</span>
              <span className="label">Avg Search Budget</span>
            </div>
          </div>
          <div className="divider" style={{ width: '100%', margin: '1.5rem 0' }} />
          <p className="dash-footer-text editorial">
            PropVision Spatial intelligence provides immersive property validation, significantly reducing physical viewing requirements while increasing lead quality by 38% on average.
          </p>
        </motion.div>
      </section>
    </motion.main>
  );
}
