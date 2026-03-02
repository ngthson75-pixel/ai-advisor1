import { useState, useEffect, useRef } from "react";

const MARKET_MODES = {
  BULL: {
    mode: "TÍCH CỰC",
    emoji: "🟢",
    color: "#00E676",
    colorDim: "rgba(0, 230, 118, 0.15)",
    gradient: "linear-gradient(135deg, rgba(0,230,118,0.08) 0%, rgba(0,230,118,0.02) 100%)",
    borderColor: "rgba(0,230,118,0.3)",
    glowColor: "rgba(0,230,118,0.4)",
    description: "Thị trường uptrend — Ưu tiên tìm điểm mua",
    allocation: 80,
    riskScore: 32,
    factors: [
      { label: "VN-Index Trend", value: "Uptrend", positive: true },
      { label: "Thanh khoản", value: "Tăng 25% vs TB20", positive: true },
      { label: "Số CP tăng/giảm", value: "342 tăng / 158 giảm", positive: true },
      { label: "CP trên MA20", value: "68% (340/500)", positive: true },
      { label: "Tham khảo: NN", value: "Bán ròng nhẹ", positive: false, isRef: true },
    ],
  },
  SIDEWAYS: {
    mode: "THẬN TRỌNG",
    emoji: "🟡",
    color: "#FFD600",
    colorDim: "rgba(255, 214, 0, 0.15)",
    gradient: "linear-gradient(135deg, rgba(255,214,0,0.08) 0%, rgba(255,214,0,0.02) 100%)",
    borderColor: "rgba(255,214,0,0.3)",
    glowColor: "rgba(255,214,0,0.4)",
    description: "Thị trường sideway — Chỉ mua khi tín hiệu rõ ràng",
    allocation: 50,
    riskScore: 55,
    factors: [
      { label: "VN-Index Trend", value: "Sideway", positive: false },
      { label: "Thanh khoản", value: "Ngang TB20", positive: false },
      { label: "Số CP tăng/giảm", value: "260 tăng / 240 giảm", positive: false },
      { label: "CP trên MA20", value: "52% (260/500)", positive: true },
      { label: "Tham khảo: NN", value: "Bán ròng", positive: false, isRef: true },
    ],
  },
  BEAR: {
    mode: "PHÒNG THỦ",
    emoji: "🔴",
    color: "#FF1744",
    colorDim: "rgba(255, 23, 68, 0.15)",
    gradient: "linear-gradient(135deg, rgba(255,23,68,0.08) 0%, rgba(255,23,68,0.02) 100%)",
    borderColor: "rgba(255,23,68,0.3)",
    glowColor: "rgba(255,23,68,0.4)",
    description: "Thị trường downtrend — Hạn chế mua, ưu tiên bảo toàn vốn",
    allocation: 20,
    riskScore: 82,
    factors: [
      { label: "VN-Index Trend", value: "Downtrend", positive: false },
      { label: "Thanh khoản", value: "Giảm 30% vs TB20", positive: false },
      { label: "Số CP tăng/giảm", value: "150 tăng / 350 giảm", positive: false },
      { label: "CP trên MA20", value: "28% (140/500)", positive: false },
      { label: "Tham khảo: NN", value: "Bán ròng mạnh", positive: false, isRef: true },
    ],
  },
};

/* ── Circular Gauge ─────────────────────────────────────── */
function RiskGauge({ score, color, size = 160 }) {
  const [animatedScore, setAnimatedScore] = useState(0);
  const radius = (size - 20) / 2;
  const circumference = 2 * Math.PI * radius;
  const progress = (animatedScore / 100) * circumference;

  useEffect(() => {
    let frame;
    let start = null;
    const duration = 1200;
    const from = 0;
    const to = score;
    function animate(ts) {
      if (!start) start = ts;
      const elapsed = ts - start;
      const t = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - t, 3);
      setAnimatedScore(Math.round(from + (to - from) * eased));
      if (t < 1) frame = requestAnimationFrame(animate);
    }
    frame = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(frame);
  }, [score]);

  return (
    <div style={{ position: "relative", width: size, height: size }}>
      <svg width={size} height={size} style={{ transform: "rotate(-90deg)" }}>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="rgba(255,255,255,0.06)"
          strokeWidth="8"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={circumference - progress}
          style={{
            transition: "stroke-dashoffset 0.05s linear",
            filter: `drop-shadow(0 0 6px ${color})`,
          }}
        />
      </svg>
      <div
        style={{
          position: "absolute",
          inset: 0,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <span
          style={{
            fontSize: size * 0.28,
            fontWeight: 800,
            color: color,
            lineHeight: 1,
            fontFamily: "'JetBrains Mono', monospace",
          }}
        >
          {animatedScore}
        </span>
        <span
          style={{
            fontSize: 11,
            color: "rgba(255,255,255,0.45)",
            marginTop: 2,
            letterSpacing: "0.08em",
            textTransform: "uppercase",
          }}
        >
          Risk Score
        </span>
      </div>
    </div>
  );
}

/* ── Allocation Bar ─────────────────────────────────────── */
function AllocationBar({ percent, color }) {
  const [width, setWidth] = useState(0);
  useEffect(() => {
    const t = setTimeout(() => setWidth(percent), 100);
    return () => clearTimeout(t);
  }, [percent]);

  return (
    <div style={{ width: "100%" }}>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          marginBottom: 8,
          alignItems: "baseline",
        }}
      >
        <span
          style={{
            fontSize: 12,
            color: "rgba(255,255,255,0.5)",
            letterSpacing: "0.05em",
            textTransform: "uppercase",
          }}
        >
          Tỷ trọng khuyến nghị
        </span>
        <span
          style={{
            fontSize: 28,
            fontWeight: 800,
            color: color,
            fontFamily: "'JetBrains Mono', monospace",
          }}
        >
          {percent}%
        </span>
      </div>
      <div
        style={{
          width: "100%",
          height: 8,
          borderRadius: 4,
          background: "rgba(255,255,255,0.06)",
          overflow: "hidden",
        }}
      >
        <div
          style={{
            width: `${width}%`,
            height: "100%",
            borderRadius: 4,
            background: `linear-gradient(90deg, ${color}, ${color}88)`,
            transition: "width 1.2s cubic-bezier(0.22, 1, 0.36, 1)",
            boxShadow: `0 0 12px ${color}66`,
          }}
        />
      </div>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          marginTop: 6,
          fontSize: 10,
          color: "rgba(255,255,255,0.3)",
        }}
      >
        <span>0% — Giữ tiền mặt</span>
        <span>100% — Full cổ phiếu</span>
      </div>
    </div>
  );
}

/* ── Factor Row ─────────────────────────────────────────── */
function FactorRow({ factor, delay }) {
  const [visible, setVisible] = useState(false);
  useEffect(() => {
    const t = setTimeout(() => setVisible(true), delay);
    return () => clearTimeout(t);
  }, [delay]);

  const isRef = factor.isRef;

  return (
    <div
      style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        padding: "8px 0",
        borderBottom: "1px solid rgba(255,255,255,0.04)",
        opacity: visible ? (isRef ? 0.45 : 1) : 0,
        transform: visible ? "translateX(0)" : "translateX(-8px)",
        transition: "all 0.4s ease",
      }}
    >
      <span style={{ fontSize: isRef ? 12 : 13, color: "rgba(255,255,255,0.55)", fontStyle: isRef ? "italic" : "normal" }}>
        {factor.label}
      </span>
      <span
        style={{
          fontSize: isRef ? 12 : 13,
          fontWeight: 600,
          color: isRef
            ? "rgba(255,255,255,0.4)"
            : factor.positive ? "#00E676" : "#FF5252",
          display: "flex",
          alignItems: "center",
          gap: 4,
        }}
      >
        {!isRef && <span style={{ fontSize: 8 }}>{factor.positive ? "▲" : "▼"}</span>}
        {factor.value}
      </span>
    </div>
  );
}

/* ── Main Component ─────────────────────────────────────── */
export default function MarketRiskIntelligence() {
  const [activeMode, setActiveMode] = useState("SIDEWAYS");
  const [isTransitioning, setIsTransitioning] = useState(false);
  const data = MARKET_MODES[activeMode];

  const switchMode = (mode) => {
    if (mode === activeMode) return;
    setIsTransitioning(true);
    setTimeout(() => {
      setActiveMode(mode);
      setIsTransitioning(false);
    }, 200);
  };

  const now = new Date();
  const timeStr = now.toLocaleTimeString("vi-VN", {
    hour: "2-digit",
    minute: "2-digit",
  });
  const dateStr = now.toLocaleDateString("vi-VN", {
    weekday: "long",
    day: "numeric",
    month: "numeric",
    year: "numeric",
  });

  return (
    <div
      style={{
        fontFamily:
          "'SF Pro Display', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
        background: "#0B0F1A",
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: 20,
      }}
    >
      <link
        href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700;800&display=swap"
        rel="stylesheet"
      />
      <div style={{ width: "100%", maxWidth: 520 }}>
        {/* ── Header ── */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            marginBottom: 16,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <div
              style={{
                width: 8,
                height: 8,
                borderRadius: "50%",
                background: data.color,
                boxShadow: `0 0 8px ${data.color}`,
                animation: "pulse 2s ease-in-out infinite",
              }}
            />
            <span
              style={{
                fontSize: 13,
                fontWeight: 600,
                color: "rgba(255,255,255,0.7)",
                letterSpacing: "0.06em",
              }}
            >
              AI MARKET INTELLIGENCE
            </span>
          </div>
          <span style={{ fontSize: 11, color: "rgba(255,255,255,0.3)" }}>
            Cập nhật: {timeStr} · {dateStr}
          </span>
        </div>

        {/* ── Main Card ── */}
        <div
          style={{
            background: data.gradient,
            border: `1px solid ${data.borderColor}`,
            borderRadius: 16,
            padding: 28,
            position: "relative",
            overflow: "hidden",
            opacity: isTransitioning ? 0.5 : 1,
            transform: isTransitioning ? "scale(0.98)" : "scale(1)",
            transition: "all 0.2s ease",
          }}
        >
          {/* Ambient glow */}
          <div
            style={{
              position: "absolute",
              top: -60,
              right: -60,
              width: 200,
              height: 200,
              borderRadius: "50%",
              background: `radial-gradient(circle, ${data.glowColor}20 0%, transparent 70%)`,
              pointerEvents: "none",
            }}
          />

          {/* Market Mode Badge */}
          <div style={{ marginBottom: 24, position: "relative" }}>
            <div
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: 8,
                padding: "6px 14px",
                borderRadius: 8,
                background: data.colorDim,
                border: `1px solid ${data.borderColor}`,
                marginBottom: 12,
              }}
            >
              <span style={{ fontSize: 16 }}>{data.emoji}</span>
              <span
                style={{
                  fontSize: 14,
                  fontWeight: 700,
                  color: data.color,
                  letterSpacing: "0.1em",
                }}
              >
                CHẾ ĐỘ {data.mode}
              </span>
            </div>
            <p
              style={{
                fontSize: 14,
                color: "rgba(255,255,255,0.55)",
                margin: 0,
                lineHeight: 1.5,
              }}
            >
              {data.description}
            </p>
          </div>

          {/* Score + Allocation Row */}
          <div
            style={{
              display: "flex",
              gap: 28,
              alignItems: "center",
              marginBottom: 24,
            }}
          >
            <RiskGauge score={data.riskScore} color={data.color} size={140} />
            <div style={{ flex: 1 }}>
              <AllocationBar percent={data.allocation} color={data.color} />
            </div>
          </div>

          {/* Factors */}
          <div
            style={{
              background: "rgba(0,0,0,0.2)",
              borderRadius: 10,
              padding: "4px 14px",
            }}
          >
            <div
              style={{
                fontSize: 10,
                color: "rgba(255,255,255,0.3)",
                letterSpacing: "0.1em",
                textTransform: "uppercase",
                padding: "10px 0 4px",
              }}
            >
              Yếu tố phân tích
            </div>
            {data.factors.map((f, i) => (
              <FactorRow key={f.label} factor={f} delay={300 + i * 100} />
            ))}
          </div>
        </div>

        {/* ── Mode Switcher (Demo Only) ── */}
        <div
          style={{
            display: "flex",
            gap: 8,
            marginTop: 16,
            justifyContent: "center",
          }}
        >
          <span
            style={{
              fontSize: 11,
              color: "rgba(255,255,255,0.25)",
              alignSelf: "center",
              marginRight: 4,
            }}
          >
            Demo:
          </span>
          {Object.entries(MARKET_MODES).map(([key, val]) => (
            <button
              key={key}
              onClick={() => switchMode(key)}
              style={{
                padding: "6px 14px",
                borderRadius: 8,
                border:
                  activeMode === key
                    ? `1px solid ${val.color}66`
                    : "1px solid rgba(255,255,255,0.08)",
                background:
                  activeMode === key ? `${val.color}15` : "rgba(255,255,255,0.03)",
                color:
                  activeMode === key ? val.color : "rgba(255,255,255,0.4)",
                fontSize: 12,
                fontWeight: 600,
                cursor: "pointer",
                transition: "all 0.2s ease",
              }}
            >
              {val.emoji} {val.mode}
            </button>
          ))}
        </div>

        {/* ── Disclaimer ── */}
        <p
          style={{
            fontSize: 10,
            color: "rgba(255,255,255,0.2)",
            textAlign: "center",
            marginTop: 16,
            lineHeight: 1.5,
          }}
        >
          AI phân tích dựa trên dữ liệu kỹ thuật & thanh khoản. Đây là công
          cụ hỗ trợ, không phải tư vấn đầu tư.
        </p>
      </div>

      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.4; }
        }
      `}</style>
    </div>
  );
}
