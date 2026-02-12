-- BƯỚC 1: XÓA WEAK SIGNALS
DELETE FROM signals
WHERE action = 'BUY'
  AND (
    (strategy = 'PULLBACK' AND strength < 75)
    OR 
    (strategy = 'EMA_CROSS' AND strength < 80)
  );

-- BƯỚC 2: XÓA DUPLICATES (GIỮ TỐT NHẤT)
WITH ranked_signals AS (
  SELECT 
    id,
    ROW_NUMBER() OVER (
      PARTITION BY ticker, date 
      ORDER BY strength DESC, id ASC
    ) as rn
  FROM signals
  WHERE action = 'BUY'
)
DELETE FROM signals
WHERE id IN (
  SELECT id FROM ranked_signals WHERE rn > 1
);