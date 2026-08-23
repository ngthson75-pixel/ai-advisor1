-- ========================================================================
-- AI ADVISOR — MIGRATION v2.2
-- ========================================================================
-- ⚠️ CHẠY TAY trên CẢ HAI database, NGOÀI GIỜ GIAO DỊCH (sau 15:00 giờ VN):
--      1. Render PostgreSQL (production)
--      2. Supabase (staging)
--
-- Lý do chạy tay: create_all() dưới gunicorn KHÔNG thêm cột vào bảng đã tồn tại.
--
-- Tất cả lệnh đều idempotent — chạy lại nhiều lần không gây lỗi.
-- ========================================================================


-- ------------------------------------------------------------------------
-- 1. LƯU CÂU TRẢ LỜI IIS (để tách điểm nghẽn B1 vs B2)
-- ------------------------------------------------------------------------
-- Không có cột này, engine vẫn chạy nhưng chỉ dùng kl_score tổng
-- → không phân biệt được nghẽn Hành vi và nghẽn Quản trị rủi ro.

ALTER TABLE iis_results ADD COLUMN IF NOT EXISTS answers TEXT;


-- ------------------------------------------------------------------------
-- 2. LỊCH SỬ ĐIỂM NGHẼN THEO THÁNG
-- ------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS user_bottleneck (
  id            SERIAL PRIMARY KEY,
  user_email    VARCHAR(255) NOT NULL,
  period        VARCHAR(7)   NOT NULL,        -- '2026-08'
  bottleneck    VARCHAR(10),                  -- B1..B5
  score         INTEGER,
  all_scores    TEXT,                         -- JSON cả 5 chiều
  intervention  TEXT,                         -- "việc duy nhất" tháng này
  confidence    VARCHAR(10),                  -- prior | hybrid | personal
  resolved      BOOLEAN DEFAULT FALSE,
  created_at    TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ub_user_period
  ON user_bottleneck(user_email, period);


-- ------------------------------------------------------------------------
-- 3. LỊCH SỬ IIS (vẽ đường tiến bộ theo tháng)
-- ------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS iis_history (
  id          SERIAL PRIMARY KEY,
  user_email  VARCHAR(255) NOT NULL,
  period      VARCHAR(7)   NOT NULL,
  total       INTEGER,
  kl          INTEGER,
  kt          INTEGER,
  source      VARCHAR(20),                    -- 'test' | 'behavior'
  created_at  TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ih_user_period
  ON iis_history(user_email, period);


-- ------------------------------------------------------------------------
-- 4. HỒ SƠ RỦI RO (cho Thẻ Quyết Định — Sprint 2)
-- ------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS user_risk_profile (
  id            SERIAL PRIMARY KEY,
  user_email    VARCHAR(255) UNIQUE NOT NULL,
  nav           DECIMAL(15,2),
  risk_pct      DECIMAL(4,2) DEFAULT 1.0,     -- % NAV rủi ro tối đa mỗi lệnh
  max_positions INTEGER DEFAULT 8,
  data_tier     CHAR(1) DEFAULT 'C',          -- A: advisory | B: VIP tự khai | C: free
  updated_at    TIMESTAMP DEFAULT NOW()
);


-- ------------------------------------------------------------------------
-- 5. CAM KẾT TRƯỚC KHI VÀO LỆNH — BẢNG BẢN LỀ CỦA TOÀN HỆ THỐNG
-- ------------------------------------------------------------------------
-- Không có bảng này → không chấm được điểm quy trình → không có moat.

CREATE TABLE IF NOT EXISTS trade_commitments (
  id                SERIAL PRIMARY KEY,
  user_email        VARCHAR(255) NOT NULL,
  ticker            VARCHAR(10)  NOT NULL,
  signal_id         INTEGER,
  committed_entry   DECIMAL(10,2),
  committed_stop    DECIMAL(10,2),
  committed_target  DECIMAL(10,2),
  committed_shares  INTEGER,
  position_pct      DECIMAL(5,2),
  risk_pct_of_nav   DECIMAL(5,2),
  thesis            TEXT,
  market_mode       VARCHAR(20),
  profile_fit       INTEGER,
  verdict           VARCHAR(30),
  created_at        TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tc_user   ON trade_commitments(user_email);
CREATE INDEX IF NOT EXISTS idx_tc_ticker ON trade_commitments(ticker);


-- ------------------------------------------------------------------------
-- 6. ĐÁNH GIÁ SAU LỆNH — CHẤM QUY TRÌNH TÁCH KHỎI KẾT QUẢ
-- ------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS trade_reviews (
  id               SERIAL PRIMARY KEY,
  commitment_id    INTEGER,
  user_email       VARCHAR(255) NOT NULL,
  ticker           VARCHAR(10),
  actual_entry     DECIMAL(10,2),
  actual_shares    INTEGER,
  actual_stop      DECIMAL(10,2),
  exit_price       DECIMAL(10,2),
  exit_reason      VARCHAR(50),
  pnl_pct          DECIMAL(6,2),
  holding_days     INTEGER,
  q1_why           SMALLINT,      -- 1 thẻ QĐ | 2 tự phân tích | 3 nghe tin | 4 thấy giá chạy
  q2_emotion       SMALLINT,      -- 1 bình thản | 2 hào hứng | 3 sợ bỏ lỡ | 4 gỡ lệnh trước
  q3_plan          SMALLINT,      -- 1 đúng hết | 2 lệch size | 3 dời ngưỡng | 4 thoát cảm tính
  process_score    INTEGER,       -- 0..100
  quadrant         VARCHAR(20),   -- skill | cost | luck | lesson
  market_mode      VARCHAR(20),
  created_at       TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tr_user     ON trade_reviews(user_email);
CREATE INDEX IF NOT EXISTS idx_tr_quadrant ON trade_reviews(quadrant);


-- ------------------------------------------------------------------------
-- 7. REGIME GATE — 3 CỘT CHO BẢNG SIGNALS (Sprint 1)
-- ------------------------------------------------------------------------

ALTER TABLE signals ADD COLUMN IF NOT EXISTS market_mode         VARCHAR(20);
ALTER TABLE signals ADD COLUMN IF NOT EXISTS risk_score_at_entry INTEGER;
ALTER TABLE signals ADD COLUMN IF NOT EXISTS gate_blocked        BOOLEAN DEFAULT FALSE;


-- ========================================================================
-- KIỂM TRA SAU KHI CHẠY
-- ========================================================================
-- Chạy các lệnh dưới để xác nhận. Mỗi lệnh phải trả về kết quả, không lỗi.

-- SELECT column_name FROM information_schema.columns
--   WHERE table_name = 'iis_results' AND column_name = 'answers';

-- SELECT COUNT(*) FROM user_bottleneck;
-- SELECT COUNT(*) FROM trade_commitments;
-- SELECT COUNT(*) FROM trade_reviews;

-- SELECT column_name FROM information_schema.columns
--   WHERE table_name = 'signals'
--     AND column_name IN ('market_mode','risk_score_at_entry','gate_blocked');
-- ========================================================================
