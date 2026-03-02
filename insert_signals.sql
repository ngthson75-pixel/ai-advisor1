-- =====================================================
-- Copy Production Signals to Staging
-- Generated: 2026-02-13 16:59:40
-- Total signals: 91
-- =====================================================

-- Clear existing signals
TRUNCATE TABLE signals RESTART IDENTITY CASCADE;

-- Insert signals
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('C69', 'PULLBACK', 16600, 14800, 17900, 0.75, 80.0, 'Penny', 38.7, '2026-02-11', 'BUY', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('HTI', 'PULLBACK', 25900, 24200, 28000, 1.2, 80.0, 'Mid Cap', 38.8, '2026-02-11', 'BUY', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('PGC', 'PULLBACK', 14200, 13600, 15300, 2.05, 80.0, 'Penny', 34.0, '2026-02-11', 'BUY', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('TIP', 'PULLBACK', 19300, 18300, 20800, 1.5, 80.0, 'Penny', 56.1, '2026-02-11', 'BUY', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('BAF', 'PULLBACK', 37600, 35500, 40700, 1.4, 80.0, 'Mid Cap', 39.2, '2026-02-11', 'BUY', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('SZL', 'PULLBACK', 47200, 46000, 51000, 3.09, 80.0, 'Mid Cap', 31.0, '2026-02-11', 'BUY', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('CTR', 'PULLBACK', 93000, 90700, 100400, 3.23, 80.0, 'Blue Chip', 35.8, '2026-02-11', 'BUY', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('CTG', 'PULLBACK', 37900, 36300, 40900, 1.94, 80.0, 'Mid Cap', 35.3, '2026-02-11', 'BUY', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('STB', 'PULLBACK', 61100, 56000, 66000, 0.96, 80.0, 'Blue Chip', 39.3, '2026-02-11', 'BUY', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('ASG', 'EMA_CROSS', 16800, 16100, 18500, 2.58, 85.0, 'Penny', 45.8, '2026-02-11', 'BUY', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('ASP', 'EMA_CROSS', 4800, 4600, 5300, 2.47, 85.0, 'Penny', 58.1, '2026-02-11', 'BUY', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('CLC', 'EMA_CROSS', 56700, 52200, 62400, 1.26, 85.0, 'Blue Chip', 52.8, '2026-02-11', 'BUY', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('TCO', 'EMA_CROSS', 10200, 9100, 11200, 0.92, 85.0, 'Penny', 52.7, '2026-02-11', 'BUY', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('LSS', 'EMA_CROSS', 9700, 9200, 10700, 2.0, 85.0, 'Penny', 51.2, '2026-02-11', 'BUY', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('QCG', 'EMA_CROSS', 14800, 13900, 16200, 1.81, 90.0, 'Penny', 53.2, '2026-02-11', 'BUY', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('VPI', 'EMA_CROSS', 59700, 53900, 65700, 1.02, 90.0, 'Blue Chip', 71.6, '2026-02-11', 'BUY', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('HDB', 'PULLBACK', 27800, 26400, 30000, 1.56, 90.0, 'Mid Cap', 40.0, '2026-02-11', 'BUY', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('VSC', 'EMA_CROSS', 23500, 20900, 25900, 0.91, 100.0, 'Mid Cap', 56.6, '2026-02-11', 'BUY', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('HT1', 'STOP_LOSS', 15000, 15400, 16500, NULL, 100.0, 'Unknown', NULL, '2026-02-10', 'SELL', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('TCB', 'STOP_LOSS', 36600, 34800, 39600, 1.12, 100.0, 'Unknown', NULL, '2026-02-10', 'SELL', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('VTP', 'STOP_LOSS', 113700, 106000, 122800, 1.79, 100.0, 'Unknown', NULL, '2026-02-10', 'SELL', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('HAP', 'TAKE_PROFIT', 7300, 7200, 7900, 1.61, 80.0, 'Unknown', NULL, '2026-02-10', 'SELL', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('SSI', 'STOP_LOSS', 31600, 30300, 34100, 1.01, 100.0, 'Unknown', NULL, '2026-02-10', 'SELL', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('BCM', 'STOP_LOSS', 71900, 66400, 77700, 2.06, 100.0, 'Unknown', NULL, '2026-02-10', 'SELL', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('DBC', 'STOP_LOSS', 29000, 26600, 31900, 1.79, 100.0, 'Unknown', NULL, '2026-02-10', 'SELL', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('BAB', 'STOP_LOSS', 12900, 12200, 14200, 2.02, 100.0, 'Unknown', NULL, '2026-02-10', 'SELL', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('VHM', 'STOP_LOSS', 140000, 133000, 151200, 5.53, 100.0, 'Unknown', NULL, '2026-02-10', 'SELL', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('VCB', 'STOP_LOSS', 68000, 64600, 73400, 1.44, 100.0, 'Unknown', NULL, '2026-02-10', 'SELL', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('HT1', 'STOP_LOSS', 15000, 15400, 16500, 0.13, 100.0, 'Unknown', NULL, '2026-02-06', 'SELL', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('TCB', 'STOP_LOSS', 34600, 34200, 37300, 0.2, 100.0, 'Unknown', NULL, '2026-02-06', 'SELL', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('BAB', 'STOP_LOSS', 12900, 12400, 13900, 1.24, 100.0, 'Unknown', NULL, '2026-02-06', 'SELL', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('BCM', 'STOP_LOSS', 71900, 66400, 77700, 1.61, 100.0, 'Unknown', NULL, '2026-02-06', 'SELL', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('VHM', 'STOP_LOSS', 140000, 133000, 151200, 5.89, 100.0, 'Unknown', NULL, '2026-02-06', 'SELL', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('VHM', 'STOP_LOSS', 140000, 133000, 151200, 6.06, 100.0, 'Unknown', NULL, '2026-02-05', 'SELL', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('SZC', 'TAKE_PROFIT', 32800, 29800, 36100, 2.5, 80.0, 'Unknown', NULL, '2026-02-05', 'SELL', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('BAF', 'PULLBACK', 37600, 35300, 40700, 1.27, 80.0, 'Mid Cap', 44.5, '2026-02-04', 'BUY', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('CTR', 'PULLBACK', 99000, 90600, 106900, 0.95, 80.0, 'Blue Chip', 33.2, '2026-02-04', 'BUY', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('HAP', 'PULLBACK', 7300, 7200, 7900, 4.93, 80.0, 'Penny', 39.7, '2026-02-04', 'BUY', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('VTP', 'PULLBACK', 113700, 106000, 122800, 1.18, 80.0, 'Blue Chip', 29.7, '2026-02-04', 'BUY', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('BCM', 'PULLBACK', 71900, 66400, 77700, 1.04, 80.0, 'Blue Chip', 38.9, '2026-02-04', 'BUY', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('HDB', 'PULLBACK', 27600, 26400, 29800, 1.9, 80.0, 'Mid Cap', 34.6, '2026-02-04', 'BUY', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('SSI', 'PULLBACK', 31600, 30300, 34100, 2.09, 80.0, 'Mid Cap', 34.7, '2026-02-04', 'BUY', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('FPT', 'PULLBACK', 101900, 96600, 110100, 1.54, 80.0, 'Blue Chip', 56.0, '2026-02-04', 'BUY', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('L18', 'EMA_CROSS', 26700, 25900, 29400, 3.18, 85.0, 'Mid Cap', 40.6, '2026-02-04', 'BUY', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('ABI', 'EMA_CROSS', 20900, 19500, 23000, 1.54, 85.0, 'Mid Cap', 50.0, '2026-02-04', 'BUY', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('PVP', 'EMA_CROSS', 15400, 14000, 16900, 1.1, 85.0, 'Penny', 57.1, '2026-02-04', 'BUY', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('KBC', 'EMA_CROSS', 37200, 33800, 40900, 1.13, 85.0, 'Mid Cap', 53.0, '2026-02-04', 'BUY', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('DBC', 'EMA_CROSS', 29000, 26600, 31900, 1.2, 85.0, 'Mid Cap', 56.9, '2026-02-04', 'BUY', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('LAS', 'EMA_CROSS', 16900, 16000, 18600, 1.79, 90.0, 'Penny', 41.5, '2026-02-04', 'BUY', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('HAX', 'EMA_CROSS', 11900, 10500, 13100, 0.85, 90.0, 'Penny', 66.1, '2026-02-04', 'BUY', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('KDC', 'EMA_CROSS', 52700, 48700, 58000, 1.33, 90.0, 'Blue Chip', 80.0, '2026-02-04', 'BUY', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('CTD', 'EMA_CROSS', 86000, 74700, 94600, 0.76, 90.0, 'Blue Chip', 76.6, '2026-02-04', 'BUY', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('BMI', 'EMA_CROSS', 19900, 17800, 21900, 0.94, 100.0, 'Penny', 54.1, '2026-02-04', 'BUY', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('GEG', 'EMA_CROSS', 15200, 14200, 16700, 1.64, 100.0, 'Penny', 55.0, '2026-02-04', 'BUY', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('HPG', 'EMA_CROSS', 28300, 25800, 31100, 1.14, 100.0, 'Mid Cap', 57.4, '2026-02-04', 'BUY', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('PC1', 'PULLBACK', 22800, 22200, 24700, 2.77, 80.0, 'Mid Cap', 36.4, '2026-01-27', 'BUY', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('HT1', 'EMA_CROSS', 15000, 15400, 16500, -4.01, 85.0, 'Penny', 42.2, '2026-01-27', 'BUY', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('FPT', 'EMA_CROSS', 102100, 94400, 112300, 1.33, 85.0, 'Blue Chip', 58.6, '2026-01-27', 'BUY', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('L18', 'PULLBACK', 26400, 26100, 28500, 8.04, 80.0, 'Mid Cap', 39.7, '2026-02-02', 'BUY', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('BAF', 'PULLBACK', 37400, 35200, 40300, 1.37, 80.0, 'Mid Cap', 47.1, '2026-02-02', 'BUY', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('BCM', 'PULLBACK', 70900, 66000, 76600, 1.16, 80.0, 'Blue Chip', 53.7, '2026-02-02', 'BUY', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('ABI', 'EMA_CROSS', 20500, 19500, 22600, 2.09, 85.0, 'Mid Cap', 56.7, '2026-02-02', 'BUY', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('VOS', 'EMA_CROSS', 13600, 12600, 15000, 1.34, 85.0, 'Penny', 53.2, '2026-02-02', 'BUY', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('HAP', 'EMA_CROSS', 7400, 7100, 8200, 2.44, 85.0, 'Penny', 44.4, '2026-02-02', 'BUY', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('PET', 'EMA_CROSS', 34200, 31600, 37600, 1.32, 85.0, 'Mid Cap', 49.0, '2026-02-02', 'BUY', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('TCL', 'EMA_CROSS', 35000, 33400, 38600, 2.09, 85.0, 'Mid Cap', 57.8, '2026-02-02', 'BUY', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('VSH', 'EMA_CROSS', 44400, 42600, 48800, 2.47, 85.0, 'Mid Cap', 55.6, '2026-02-02', 'BUY', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('PPC', 'EMA_CROSS', 10000, 9600, 11000, 2.9, 85.0, 'Penny', 41.7, '2026-02-02', 'BUY', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('VCI', 'EMA_CROSS', 36000, 34000, 39600, 1.84, 85.0, 'Mid Cap', 52.9, '2026-02-02', 'BUY', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('CTI', 'EMA_CROSS', 23800, 22200, 26200, 1.45, 90.0, 'Mid Cap', 63.6, '2026-02-02', 'BUY', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('CTG', 'PULLBACK', 39400, 36100, 42500, 0.98, 90.0, 'Mid Cap', 35.3, '2026-02-02', 'BUY', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('CTR', 'PULLBACK', 96700, 89900, 104400, 1.14, 80.0, 'Blue Chip', 39.3, '2026-01-30', 'BUY', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('PC1', 'PULLBACK', 24200, 22300, 26100, 1.01, 80.0, 'Mid Cap', 50.6, '2026-01-30', 'BUY', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('BCM', 'PULLBACK', 68100, 65900, 73500, 2.48, 80.0, 'Blue Chip', 46.8, '2026-01-30', 'BUY', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('MBB', 'PULLBACK', 27200, 25100, 29400, 1.04, 80.0, 'Mid Cap', 38.4, '2026-01-30', 'BUY', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('BAB', 'EMA_CROSS', 12900, 12200, 14200, 1.88, 85.0, 'Penny', 51.2, '2026-01-30', 'BUY', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('CNG', 'EMA_CROSS', 27000, 24700, 29700, 1.18, 85.0, 'Mid Cap', 59.7, '2026-01-30', 'BUY', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('HAP', 'EMA_CROSS', 7500, 7100, 8200, 2.0, 85.0, 'Penny', 49.1, '2026-01-30', 'BUY', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('SZC', 'EMA_CROSS', 32200, 29700, 35400, 1.3, 85.0, 'Mid Cap', 57.3, '2026-01-30', 'BUY', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('DBC', 'EMA_CROSS', 28200, 26500, 31000, 1.71, 85.0, 'Mid Cap', 57.5, '2026-01-30', 'BUY', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('DCM', 'EMA_CROSS', 36600, 33300, 40300, 1.12, 85.0, 'Mid Cap', 55.6, '2026-01-30', 'BUY', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('CTG', 'PULLBACK', 38800, 36000, 41800, 1.14, 90.0, 'Mid Cap', 28.0, '2026-01-30', 'BUY', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('PGD', 'EMA_CROSS', 24200, 23000, 26600, 2.08, 100.0, 'Mid Cap', 54.1, '2026-01-30', 'BUY', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('TCB', 'PULLBACK', 36600, 34800, 39600, 1.6, 75.0, 'Blue Chip', 65.0, '2026-01-30', 'BUY', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('HPG', 'PULLBACK', 26200, 24900, 28300, 1.6, 75.0, 'Blue Chip', 65.0, '2026-01-30', 'BUY', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('VHM', 'PULLBACK', 140000, 133000, 151200, 1.6, 75.0, 'Blue Chip', 65.0, '2026-01-30', 'BUY', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('VCB', 'PULLBACK', 68000, 64600, 73400, 1.6, 75.0, 'Blue Chip', 65.0, '2026-01-30', 'BUY', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('TCB', 'PULLBACK', 36600, 34800, 39600, 1.6, 75.0, 'Blue Chip', 65.0, '2026-01-25', 'BUY', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('HPG', 'PULLBACK', 26200, 24900, 28300, 1.6, 75.0, 'Blue Chip', 65.0, '2026-01-25', 'BUY', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('VHM', 'PULLBACK', 140000, 133000, 151200, 1.6, 75.0, 'Blue Chip', 65.0, '2026-01-25', 'BUY', NOW());
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('VCB', 'PULLBACK', 68000, 64600, 73400, 1.6, 75.0, 'Blue Chip', 65.0, '2026-01-25', 'BUY', NOW());