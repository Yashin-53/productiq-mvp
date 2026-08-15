export default function ConfidenceGauge({ value = 0, size = 92, label = 'Confidence' }) {
  const pct = Math.max(0, Math.min(100, value));
  const color = pct >= 90 ? 'var(--verified)' : pct >= 75 ? '#a3d977' : pct >= 55 ? 'var(--review)' : 'var(--conflict)';
  const r = (size - 14) / 2;
  const circumference = Math.PI * r; // half circle
  const offset = circumference - (pct / 100) * circumference;
  const cx = size / 2;
  const cy = size / 2 + 4;

  return (
    <div className="gauge-wrap">
      <svg width={size} height={size / 2 + 16} viewBox={`0 0 ${size} ${size / 2 + 16}`}>
        <path
          d={`M ${cx - r} ${cy} A ${r} ${r} 0 0 1 ${cx + r} ${cy}`}
          fill="none" stroke="var(--border)" strokeWidth="7" strokeLinecap="round"
        />
        <path
          d={`M ${cx - r} ${cy} A ${r} ${r} 0 0 1 ${cx + r} ${cy}`}
          fill="none" stroke={color} strokeWidth="7" strokeLinecap="round"
          strokeDasharray={circumference} strokeDashoffset={offset}
          style={{ transition: 'stroke-dashoffset .5s ease, stroke .3s' }}
        />
        <text x={cx} y={cy - 6} textAnchor="middle" fontFamily="var(--mono)" fontSize="18" fontWeight="700" fill="var(--text)">
          {pct}%
        </text>
      </svg>
      <div className="gauge-label">{label}</div>
    </div>
  );
}
