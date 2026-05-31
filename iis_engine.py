#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IIS ENGINE — Investor Intelligence Score
AI-Advisor | v1.0

Chấm điểm IIS Test 15 câu, xác định profile và phương pháp phù hợp.
Tích hợp vào backend_api.py qua init_iis_routes().

Profiles:
  Khởi Hành   (0–24)
  Định Hướng  (25–39)
  Phát Triển  (40–54)
  Vững Vàng   (55–69)
  Tinh Thông  (70–84)
  Chuyên Gia  (85–100)

Phương pháp:
  luot_song  — Lướt Sóng AI (ngắn hạn)
  bat_song   — Bắt Sóng AI (trung hạn)
  tich_san   — Tích Sản AI (dài hạn)
  hybrid_sm  — Hybrid Lướt + Bắt (1/3 + 2/3)
  hybrid_ml  — Hybrid Bắt + Tích (1/3 + 2/3)
"""

# ── Question bank ────────────────────────────────────────────────────────
# dim: 'kl' = Kỷ Luật | 'pp' = Phương Pháp | 'kt' = Kiến Thức
# score: điểm cho từng đáp án (index 0-3)
# method: 's'=Lướt, 'm'=Bắt, 'l'=Tích (chỉ cho dim='pp')

IIS_QUESTIONS = [
    # ── Chiều 1: IIS Kỷ Luật Q0–Q4 ─────────────────────────────────────
    {
        'id': 'Q1',
        'dim': 'kl',
        'text': 'Bạn thường đặt stop loss như thế nào?',
        'options': [
            {'text': 'Không bao giờ đặt stop loss',                                  'score': 0},
            {'text': 'Đặt sau khi mua, dựa trên cảm giác',                           'score': 1},
            {'text': 'Đặt trước khi mua, dựa trên vùng hỗ trợ kỹ thuật',             'score': 3},
            {'text': 'Đặt trước, không bao giờ dời xuống — chỉ được kéo lên',        'score': 4},
        ]
    },
    {
        'id': 'Q2',
        'dim': 'kl',
        'text': 'Cổ phiếu đang lỗ 8%, SL đặt ở -12%. Giá giảm thêm 3%. Bạn làm gì?',
        'options': [
            {'text': 'Dời stop loss xuống -16% để tránh bị dừng lỗ',                 'score': 0},
            {'text': 'Thoát ngay, không chờ stop hit',                               'score': 1},
            {'text': 'Giữ nguyên plan, chờ stop loss hit đúng mức đã đặt',            'score': 3},
            {'text': 'Xem lại luận điểm — nếu vẫn đúng giữ, sai thì cắt ngay',       'score': 4},
        ]
    },
    {
        'id': 'Q3',
        'dim': 'kl',
        'text': 'HPG tăng trần 3 phiên liên tiếp. Mọi người trong group đang mua ồ ạt. Bạn chưa có vị thế. Bạn làm gì?',
        'options': [
            {'text': 'Mua ngay, sợ bỏ lỡ cơ hội',                                   'score': 0},
            {'text': 'Hỏi thêm vài người trong group rồi quyết định',                'score': 1},
            {'text': 'Kiểm tra setup kỹ thuật, chỉ mua nếu đủ điều kiện',             'score': 3},
            {'text': 'Chờ pullback về vùng hỗ trợ — không mua đuổi theo đám đông',   'score': 4},
        ]
    },
    {
        'id': 'Q4',
        'dim': 'kl',
        'text': 'VN-Index đột ngột giảm 2% trong phiên. Cổ phiếu bạn đang lỗ 6%. Phản xạ đầu tiên của bạn?',
        'options': [
            {'text': 'Mở app ngay, cân nhắc bán hết để cắt lỗ',                      'score': 0},
            {'text': 'Hồi hộp, theo dõi giá liên tục',                               'score': 1},
            {'text': 'Kiểm tra: stop loss hit chưa? Nếu chưa hit → giữ nguyên plan', 'score': 3},
            {'text': 'Tắt app, làm việc khác — thị trường 1 ngày không ảnh hưởng plan','score': 4},
        ]
    },
    {
        'id': 'Q5',
        'dim': 'kl',
        'text': 'Ba lệnh gần nhất của bạn được đặt dựa trên cơ sở nào?',
        'options': [
            {'text': 'Tip từ group, người quen, hoặc thấy nhiều người đang mua',      'score': 0},
            {'text': 'Cảm tính + xem chart sơ qua',                                  'score': 1},
            {'text': 'Setup kỹ thuật rõ ràng, có entry/SL xác định',                 'score': 3},
            {'text': 'Hệ thống cụ thể: entry, SL, TP, size — xác định trước khi mua','score': 4},
        ]
    },

    # ── Chiều 2: IIS Phương Pháp Q5–Q9 ─────────────────────────────────
    {
        'id': 'Q6',
        'dim': 'pp',
        'text': 'Mỗi ngày bạn có bao nhiêu thời gian thực sự cho việc đầu tư?',
        'options': [
            {'text': 'Dưới 20 phút — check cuối tuần là chủ yếu',                    'method': 'l'},
            {'text': '20–45 phút — buổi sáng trước giờ làm hoặc tối',               'method': 'm'},
            {'text': '45–90 phút — xem trước và sau giờ giao dịch',                  'method': 'm'},
            {'text': 'Trên 90 phút — theo dõi được trong giờ giao dịch',             'method': 's'},
        ]
    },
    {
        'id': 'Q7',
        'dim': 'pp',
        'text': 'Bạn giữ một lệnh đang lỗ 7% sau 2 tuần. Luận điểm đầu tư vẫn còn giá trị. Cảm giác thật sự của bạn?',
        'options': [
            {'text': 'Rất khó chịu, muốn thoát sớm cho nhẹ đầu',                    'method': 's'},
            {'text': 'Lo nhưng kiên nhẫn được thêm 2–3 tuần',                        'method': 'm'},
            {'text': 'Bình thường — tôi mua vì FA tốt, giá ngắn hạn không phải vấn đề','method': 'l'},
        ]
    },
    {
        'id': 'Q8',
        'dim': 'pp',
        'text': 'Bạn thích phân tích cổ phiếu bằng cách nào nhất?',
        'options': [
            {'text': 'Biểu đồ kỹ thuật — MA, RSI, Volume, candlestick',              'method': 's'},
            {'text': 'Kết hợp: TA để timing entry, FA để chọn cổ phiếu chất lượng',  'method': 'm'},
            {'text': 'Báo cáo tài chính — P/E, ROE, tăng trưởng EPS, dòng tiền',    'method': 'l'},
        ]
    },
    {
        'id': 'Q9',
        'dim': 'pp',
        'text': 'Trong 1 năm, bạn muốn thực hiện bao nhiêu lệnh giao dịch?',
        'options': [
            {'text': '3–10 lệnh — rất chọn lọc, mỗi lệnh giữ rất lâu',              'method': 'l'},
            {'text': '10–30 lệnh — chọn lọc, giữ vài tháng mỗi lệnh',               'method': 'm'},
            {'text': '30–80 lệnh — nhiều cơ hội, mỗi lệnh ngắn hơn',                'method': 's'},
        ]
    },
    {
        'id': 'Q10',
        'dim': 'pp',
        'text': 'Công việc và lối sống của bạn hiện tại?',
        'options': [
            {'text': 'Rất bận — ít có thời gian theo dõi thị trường ban ngày',        'method': 'l'},
            {'text': 'Văn phòng — có thể check điện thoại giữa giờ nghỉ',            'method': 'm'},
            {'text': 'Linh hoạt — có thể theo dõi thị trường trong giờ giao dịch',   'method': 's'},
        ]
    },

    # ── Chiều 3: IIS Kiến Thức Q10–Q14 ──────────────────────────────────
    {
        'id': 'Q11',
        'dim': 'kt',
        'text': 'Hệ thống giao dịch có: win rate 42%, lãi trung bình +16%, lỗ trung bình -6%. Bạn đánh giá thế nào?',
        'options': [
            {'text': 'Tệ — thua nhiều hơn thắng, không dùng được',                   'score': 0},
            {'text': 'Bình thường — cần thêm thông tin mới kết luận được',            'score': 1},
            {'text': 'Tốt — EV = (0.42×16)-(0.58×6) = +3.2% mỗi lệnh, dương',       'score': 4},
        ]
    },
    {
        'id': 'Q12',
        'dim': 'kt',
        'text': 'VN-Index đang nằm dưới MA20, MA50 và MA200 cùng lúc. Market breadth âm 3 tuần liên tiếp. Bạn nên làm gì?',
        'options': [
            {'text': 'Mua cổ phiếu tốt đang rẻ hơn — cơ hội tốt',                   'score': 0},
            {'text': 'Chờ xem thêm vài phiên rồi quyết định',                        'score': 1},
            {'text': 'Giảm tỷ trọng, tăng tiền mặt, không mở lệnh mới',              'score': 3},
            {'text': 'Chuyển sang chế độ Bear — chiến lược và tỷ trọng thay đổi hoàn toàn','score': 4},
        ]
    },
    {
        'id': 'Q13',
        'dim': 'kt',
        'text': 'Tài khoản 400 triệu. Quy tắc risk 2% mỗi lệnh. Stop loss dự kiến -8% từ giá mua. Bạn mua tối đa bao nhiêu tiền?',
        'options': [
            {'text': 'Không biết tính — thường mua theo cảm tính',                   'score': 0},
            {'text': 'Khoảng 50–80 triệu, ước chừng',                                'score': 1},
            {'text': '400M × 2% = 8M risk. 8M ÷ 8% = 100 triệu tối đa',             'score': 4},
        ]
    },
    {
        'id': 'Q14',
        'dim': 'kt',
        'text': 'Cổ phiếu Y: P/E = 7 (ngành P/E = 16), ROE = 24%, nợ/vốn = 0.25, EPS tăng 35% YoY. Bạn kết luận gì?',
        'options': [
            {'text': 'Không đọc được các chỉ số này',                                'score': 0},
            {'text': 'Có vẻ tốt nhưng chưa chắc — cần hỏi thêm',                    'score': 1},
            {'text': 'Cổ phiếu đang rẻ hơn ngành, nền tảng tốt — đáng nghiên cứu sâu','score': 3},
            {'text': 'Discount 56% so ngành + ROE cao + tăng trưởng mạnh + nợ thấp = Value play tiềm năng','score': 4},
        ]
    },
    {
        'id': 'Q15',
        'dim': 'kt',
        'text': 'Sau khi mua, bạn sẽ bán khi nào? (chọn mô tả đúng thực tế nhất)',
        'options': [
            {'text': 'Khi thấy lãi đủ rồi, hoặc khi cần tiền',                      'score': 0},
            {'text': 'Khi lãi 10–15% hoặc khi nghe tin xấu về cổ phiếu đó',         'score': 1},
            {'text': 'Khi đạt target price đã đặt trước, hoặc stop loss hit',        'score': 3},
            {'text': 'Khi stop loss hit, trailing stop kích hoạt, hoặc luận điểm thay đổi cơ bản','score': 4},
        ]
    },
]

# ── Level definitions ─────────────────────────────────────────────────────
IIS_LEVELS = [
    {'name': 'Khởi Hành',  'min': 0,  'max': 24,  'color': 'danger',  'ai_role': 'Bảo vệ'},
    {'name': 'Định Hướng', 'min': 25, 'max': 39,  'color': 'warning', 'ai_role': 'Dạy'},
    {'name': 'Phát Triển', 'min': 40, 'max': 54,  'color': 'default', 'ai_role': 'Huấn luyện'},
    {'name': 'Vững Vàng',  'min': 55, 'max': 69,  'color': 'info',    'ai_role': 'Tối ưu'},
    {'name': 'Tinh Thông', 'min': 70, 'max': 84,  'color': 'success', 'ai_role': 'Đồng hành'},
    {'name': 'Chuyên Gia', 'min': 85, 'max': 100, 'color': 'premium', 'ai_role': 'Alumni'},
]

# ── Method definitions ────────────────────────────────────────────────────
METHOD_INFO = {
    'luot_song': {
        'name': 'Lướt Sóng AI',
        'horizon': 'Ngắn hạn',
        'hold': '3 ngày – 3 tuần',
        'win_rate': '45–55%',
        'rr': '1:2–3',
        'strategies': ['PULLBACK', 'EMA_CROSS', 'BREAKOUT'],
        'bucket_pct': 100,
    },
    'bat_song': {
        'name': 'Bắt Sóng AI',
        'horizon': 'Trung hạn',
        'hold': '3 tuần – 4 tháng',
        'win_rate': '50–62%',
        'rr': '1:3–5',
        'strategies': ['TREND_FOLLOWING', 'EARNINGS_MOMENTUM', 'FA_HYBRID'],
        'bucket_pct': 100,
    },
    'tich_san': {
        'name': 'Tích Sản AI',
        'horizon': 'Dài hạn',
        'hold': '4 tháng – 2+ năm',
        'win_rate': '60–70%',
        'rr': '1:5–15',
        'strategies': ['VALUE', 'GROWTH'],
        'bucket_pct': 100,
    },
    'hybrid_sm': {
        'name': 'Hybrid Lướt + Bắt',
        'horizon': 'Ngắn + Trung hạn',
        'hold': 'Linh hoạt',
        'win_rate': '47–58%',
        'rr': '1:2.5–4',
        'strategies': ['PULLBACK', 'EMA_CROSS', 'TREND_FOLLOWING', 'FA_HYBRID'],
        'bucket_pct': None,
        'buckets': {'luot_song': 33, 'bat_song': 67},
    },
    'hybrid_ml': {
        'name': 'Hybrid Bắt + Tích',
        'horizon': 'Trung + Dài hạn',
        'hold': 'Linh hoạt',
        'win_rate': '52–65%',
        'rr': '1:3.5–8',
        'strategies': ['TREND_FOLLOWING', 'FA_HYBRID', 'VALUE', 'GROWTH'],
        'bucket_pct': None,
        'buckets': {'bat_song': 33, 'tich_san': 67},
    },
}

# ── Scoring functions ─────────────────────────────────────────────────────

def score_iis(answers) -> dict:
    """
    answers: list of 15 integers, each = index of chosen option (0-based)
    Returns: full IIS result dict

    Example:
        result = score_iis([3,2,3,2,3, 1,1,1,1,2, 2,2,2,1,2])
    """
    if len(answers) != 15:
        raise ValueError(f"Expected 15 answers, got {len(answers)}")

    kl_raw = 0   # max 20 (5 câu × 4 điểm)
    kt_raw = 0   # max 20 (5 câu × 4 điểm)
    method_votes = {'s': 0, 'm': 0, 'l': 0}

    for i, q in enumerate(IIS_QUESTIONS):
        ans_idx = answers[i]
        opt = q['options'][ans_idx]

        if q['dim'] == 'kl':
            kl_raw += opt.get('score', 0)
        elif q['dim'] == 'kt':
            kt_raw += opt.get('score', 0)
        elif q['dim'] == 'pp':
            method_votes[opt.get('method', 'm')] += 1

    # Normalise to 0-100
    kl_score = round(kl_raw / 20 * 100)
    kt_score = round(kt_raw / 20 * 100)

    # IIS total (Kỷ Luật 50% + Kiến Thức 50%)
    total = round(kl_score * 0.5 + kt_score * 0.5)

    # Level
    level = _get_level(total)

    # Method — detect hybrid if top-2 methods are close
    method_key = _detect_method(method_votes)

    return {
        'kl_score': kl_score,
        'kt_score': kt_score,
        'total': total,
        'level': level,
        'method': method_key,
        'method_info': METHOD_INFO[method_key],
        'method_votes': method_votes,
        'improve_tips': _get_tips(kl_score, kt_score),
    }


def _get_level(total: int) -> dict:
    for lvl in IIS_LEVELS:
        if lvl['min'] <= total <= lvl['max']:
            return lvl
    return IIS_LEVELS[-1]


def _detect_method(votes: dict) -> str:
    """
    Votes: {'s': int, 'm': int, 'l': int} (5 votes total from Q6-Q10)
    Returns method key. Hybrid if top-2 are tied or 1 vote apart.
    """
    sorted_v = sorted(votes.items(), key=lambda x: x[1], reverse=True)
    top, second = sorted_v[0], sorted_v[1]

    # Clear winner (gap >= 2)
    if top[1] - second[1] >= 2:
        return {'s': 'luot_song', 'm': 'bat_song', 'l': 'tich_san'}[top[0]]

    # Hybrid: top-2 are close
    combo = tuple(sorted([top[0], second[0]]))
    hybrid_map = {
        ('m', 's'): 'hybrid_sm',
        ('l', 'm'): 'hybrid_ml',
        ('l', 's'): 'hybrid_sm',  # edge case: go shorter of the two
    }
    return hybrid_map.get(combo, 'bat_song')


def _get_tips(kl, kt):
    tips = []
    if kl < 50:
        tips.append('Ưu tiên xây kỷ luật: luôn đặt stop loss trước khi mua và hoàn thành pre-trade checklist.')
    elif kl < 70:
        tips.append('Kỷ luật đang tốt — tiếp tục duy trì, đặc biệt khi thị trường biến động.')
    if kt < 50:
        tips.append('Nâng kiến thức: học cách tính Risk-Reward, đọc Market Regime và FA cơ bản.')
    elif kt < 70:
        tips.append('Kiến thức khá tốt — hãy áp dụng EV thinking vào từng quyết định giao dịch.')
    return tips


# ── Update IIS from behavior (40% weight) ────────────────────────────────

def update_iis_from_behavior(
    base_test_score: int,
    checklist_rate: float,    # 0.0–1.0
    stop_loss_rate: float,    # 0.0–1.0
    clearance_opens: int,     # số lần mở Clearance Card trong 30 ngày
) -> int:
    """
    Cập nhật IIS kết hợp điểm test (60%) + hành vi thực tế (40%).
    Chạy cuối mỗi tháng, lưu vào cột iis_score trong bảng users.

    checklist_rate : tỷ lệ hoàn thành checklist trước lệnh (0-1)
    stop_loss_rate : tỷ lệ lệnh có đặt stop loss (0-1)
    clearance_opens: số lần mở Clearance Card (max thưởng tại 20 lần)
    """
    behavior_score = (
        checklist_rate  * 40 +   # max 40
        stop_loss_rate  * 40 +   # max 40
        min(clearance_opens, 20) / 20 * 20  # max 20
    )  # behavior_score: 0–100

    combined = round(base_test_score * 0.6 + behavior_score * 0.4)
    return max(0, min(100, combined))


# ── Level-up trigger check ────────────────────────────────────────────────

LEVEL_UP_TRIGGERS = {
    'Khởi Hành': {
        'next': 'Định Hướng',
        'conditions': [
            'stop_loss_rate >= 0.6',    # đặt SL ít nhất 60% lệnh
            'clearance_opens >= 3',      # mở Clearance Card ít nhất 3 lần
            'checklist_completions >= 3',
        ],
        'description': 'Đặt stop loss ≥ 3 lệnh · Mở Clearance Card ≥ 3 lần · Hoàn thành checklist ≥ 3 lần',
    },
    'Định Hướng': {
        'next': 'Phát Triển',
        'conditions': [
            'checklist_rate >= 0.7',     # 7/10 lệnh có checklist
            'no_avg_down_30d == True',   # không average down ngoài kế hoạch 30 ngày
            'email_open_streak >= 10',   # mở email 10 ngày liên tiếp
        ],
        'description': 'Checklist ≥ 70% lệnh · Không average down 30 ngày · Mở email 10 ngày liên tiếp',
    },
    'Phát Triển': {
        'next': 'Vững Vàng',
        'conditions': [
            'checklist_rate >= 1.0',     # 10/10 lệnh có checklist
            'held_to_target >= 1',       # ít nhất 1 lệnh giữ đến target
            'kl_score_improvement >= 10',# IIS Kỷ Luật tăng ≥ 10 điểm vs baseline
        ],
        'description': 'Checklist 10/10 lệnh · Giữ ≥ 1 lệnh đến target · IIS Kỷ Luật +10 điểm',
    },
    'Vững Vàng': {
        'next': 'Tinh Thông',
        'conditions': [
            'win_rate_3m >= 0.45',       # win rate ≥ 45% trong 3 tháng
            'monthly_report_streak >= 3',# đọc Monthly Report 3 tháng liên tiếp
            'discipline_streak >= 20',   # streak kỷ luật 20 ngày
        ],
        'description': 'Win rate ≥ 45% (3 tháng) · Đọc Monthly Report 3 tháng · Streak 20 ngày',
    },
    'Tinh Thông': {
        'next': 'Chuyên Gia',
        'conditions': [
            'iis_retest >= 70',          # IIS ≥ 70 trên lần retest sau 90 ngày
            'positive_return_quarters >= 2',  # return dương 2 quý liên tiếp
            'bias_improved >= 2',        # ≥ 2 bias đã cải thiện trong Monthly Report
        ],
        'description': 'IIS retest ≥ 70 · Return dương 2 quý · ≥ 2 bias đã cải thiện',
    },
}


def check_level_up(current_level_name: str, metrics: dict) -> dict:
    """
    Kiểm tra user có đủ điều kiện lên level tiếp theo không.
    metrics: dict với các key tương ứng conditions trên.

    Returns:
        {
          'eligible': bool,
          'next_level': str or None,
          'met': list of str,      # conditions đã đạt
          'unmet': list of str,    # conditions chưa đạt
        }
    """
    trigger = LEVEL_UP_TRIGGERS.get(current_level_name)
    if not trigger:
        return {'eligible': False, 'next_level': None, 'met': [], 'unmet': []}

    met, unmet = [], []
    for cond in trigger['conditions']:
        key = cond.split(' ')[0]
        val = metrics.get(key)
        try:
            eligible = bool(eval(cond, {}, metrics))
        except Exception:
            eligible = False
        if eligible:
            met.append(cond)
        else:
            unmet.append(cond)

    return {
        'eligible': len(unmet) == 0,
        'next_level': trigger['next'] if len(unmet) == 0 else None,
        'met': met,
        'unmet': unmet,
        'description': trigger['description'],
    }


# ── Flask route registration ─────────────────────────────────────────────

def init_iis_routes(app, Session):
    """
    Đăng ký IIS routes vào Flask app.
    Gọi trong backend_api.py sau khi tạo app:
        from iis_engine import init_iis_routes
        init_iis_routes(app, Session)
    """
    from flask import request, jsonify
    from sqlalchemy import Column, Integer, String, Float, DateTime, Text
    from sqlalchemy.ext.declarative import declarative_base
    import json as _json

    _Base = declarative_base()

    class IISResult(_Base):
        """Lưu kết quả IIS Test của từng user."""
        __tablename__ = 'iis_results'
        id           = Column(Integer, primary_key=True)
        user_id      = Column(String(100), nullable=False)
        kl_score     = Column(Integer)
        kt_score     = Column(Integer)
        total        = Column(Integer)
        level_name   = Column(String(50))
        method       = Column(String(30))
        answers_json = Column(Text)   # lưu raw answers để audit
        source       = Column(String(20), default='test')  # 'test' | 'behavior_update'
        created_at   = Column(DateTime, default=__import__('datetime').datetime.now)

    from sqlalchemy import inspect as _inspect
    try:
        from sqlalchemy import create_engine as _ce
        _engine = Session.kw.get('bind') or Session().bind
        _Base.metadata.create_all(_engine)
        print("✅ IIS: iis_results table created/verified")
    except Exception as e:
        print(f"⚠️ IIS table init: {e}")

    # ── GET /api/iis/questions ─────────────────────────────────
    @app.route('/api/iis/questions', methods=['GET'])
    def iis_questions():
        """Trả về danh sách câu hỏi (không có đáp án điểm số)."""
        questions = []
        for q in IIS_QUESTIONS:
            opts = []
            for o in q['options']:
                opts.append({'text': o['text']})
            questions.append({'id': q['id'], 'text': q['text'], 'dim': q['dim'], 'options': opts})
        return jsonify({'questions': questions, 'total': len(questions)})

    # ── POST /api/iis/submit ───────────────────────────────────
    @app.route('/api/iis/submit', methods=['POST'])
    def iis_submit():
        """
        Body: { "user_id": "...", "answers": [0,1,2,...] }
        Returns: full IIS result
        """
        data = request.get_json() or {}
        user_id = data.get('user_id', 'anonymous')
        answers = data.get('answers', [])

        if len(answers) != 15:
            return jsonify({'error': f'Expected 15 answers, got {len(answers)}'}), 400

        try:
            result = score_iis(answers)
        except Exception as e:
            return jsonify({'error': str(e)}), 400

        # Save to DB
        session = Session()
        try:
            record = IISResult(
                user_id=user_id,
                kl_score=result['kl_score'],
                kt_score=result['kt_score'],
                total=result['total'],
                level_name=result['level']['name'],
                method=result['method'],
                answers_json=_json.dumps(answers),
            )
            session.add(record)
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"⚠️ IIS save error: {e}")
        finally:
            session.close()

        return jsonify({
            'success': True,
            'iis': {
                'kl_score': result['kl_score'],
                'kt_score': result['kt_score'],
                'total': result['total'],
                'level': result['level']['name'],
                'level_color': result['level']['color'],
                'ai_role': result['level']['ai_role'],
                'method': result['method'],
                'method_name': result['method_info']['name'],
                'method_horizon': result['method_info']['horizon'],
                'method_hold': result['method_info']['hold'],
                'method_win_rate': result['method_info']['win_rate'],
                'method_rr': result['method_info']['rr'],
                'method_strategies': result['method_info']['strategies'],
                'buckets': result['method_info'].get('buckets'),
                'improve_tips': result['improve_tips'],
            }
        })

    # ── GET /api/iis/result/<user_id> ──────────────────────────
    @app.route('/api/iis/result/<user_id>', methods=['GET'])
    def iis_result(user_id):
        """Lấy kết quả IIS mới nhất của user."""
        session = Session()
        try:
            record = session.query(IISResult)\
                .filter_by(user_id=user_id)\
                .order_by(IISResult.created_at.desc())\
                .first()
            if not record:
                return jsonify({'has_result': False}), 200
            return jsonify({
                'has_result': True,
                'total': record.total,
                'level': record.level_name,
                'method': record.method,
                'kl_score': record.kl_score,
                'kt_score': record.kt_score,
                'tested_at': record.created_at.isoformat() if record.created_at else None,
            })
        finally:
            session.close()

    # ── GET /api/iis/levels ────────────────────────────────────
    @app.route('/api/iis/levels', methods=['GET'])
    def iis_levels():
        return jsonify({'levels': IIS_LEVELS, 'triggers': LEVEL_UP_TRIGGERS})

    print("✅ IIS routes registered: /api/iis/questions, /api/iis/submit, /api/iis/result, /api/iis/levels")


# ── CLI quick-test ────────────────────────────────────────────────────────
if __name__ == '__main__':
    # Mô phỏng 3 profile khác nhau
    test_cases = [
        {
            'name': 'Nhà đầu tư Vững Vàng — Bắt Sóng',
            'answers': [3,2,3,2,3,  2,1,1,1,2,  2,2,2,2,2],
        },
        {
            'name': 'Nhà đầu tư Khởi Hành — Hybrid',
            'answers': [0,0,1,0,1,  3,0,0,2,2,  0,0,0,0,0],
        },
        {
            'name': 'Nhà đầu tư Tinh Thông — Lướt Sóng',
            'answers': [3,3,3,3,3,  3,0,0,2,2,  2,3,2,3,3],
        },
    ]

    for tc in test_cases:
        r = score_iis(tc['answers'])
        print(f"\n{'='*55}")
        print(f"  {tc['name']}")
        print(f"  IIS Kỷ Luật : {r['kl_score']}/100")
        print(f"  IIS Kiến Thức: {r['kt_score']}/100")
        print(f"  Tổng IIS     : {r['total']}/100  →  {r['level']['name']}")
        print(f"  Phương pháp  : {r['method_info']['name']}")
        if r['improve_tips']:
            print(f"  Tips         : {r['improve_tips'][0][:60]}...")
