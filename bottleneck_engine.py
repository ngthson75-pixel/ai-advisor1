#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BOTTLENECK ENGINE — AI ADVISOR
===============================
CORE của hành trình nâng cấp trình độ nhà đầu tư.

Trả lời câu hỏi: "Điểm nghẽn DUY NHẤT đang cản trở nhà đầu tư này là gì,
và can thiệp nào sửa được nó?"

NGUYÊN TẮC:
  - Mỗi lúc CHỈ MỘT điểm nghẽn. Nói 5 điều cần sửa = user sửa 0 điều.
  - Chạy được NGAY NGÀY ĐẦU chỉ với bài IIS 15 câu (không cần đợi 300 lệnh).
  - Độ chính xác tăng dần khi có dữ liệu lệnh thật.

NĂM ĐIỂM NGHẼN:
  B1 Hành vi          — FOMO, hoảng loạn, mua theo tip      (Q3,Q4,Q5)
  B2 Quản trị rủi ro  — không đặt/dời ngưỡng dừng lỗ, sai size (Q1,Q2)
  B3 Phương pháp      — chưa có neo phong cách, đánh lệch hồ sơ (method_clarity)
  B4 Thích nghi       — thắng BULL, mất sạch SIDEWAYS/BEAR   (win rate theo regime)
  B5 Kiến thức        — chưa hiểu cơ chế                      (kt_score)

BA MỨC ĐỘ TIN CẬY:
  prior     — chỉ từ bài IIS test (< 6 lệnh)
  hybrid    — IIS + xu hướng cá nhân sơ bộ (6-19 lệnh)
  personal  — cá nhân hóa hoàn toàn (>= 20 lệnh)

CÁCH DÙNG trong backend_api.py:

    from bottleneck_engine import init_bottleneck_routes
    init_bottleneck_routes(app, Session)

    # hoặc gọi trực tiếp để inject vào system prompt:
    from bottleneck_engine import diagnose
    bn = diagnose(Session, user_email)

Author: AI Advisor
Version: 1.0 — 2026-08-23
"""

import json
from datetime import datetime
from sqlalchemy import text

# ========================================================================
# CẤU HÌNH
# ========================================================================

# Ánh xạ câu hỏi Kỷ Luật (Q1-Q5, index 0-4 trong mảng answers)
# Điểm mỗi lựa chọn: [0, 1, 3, 4]
_OPT_SCORES = [0, 1, 3, 4]
_B2_QUESTIONS = [0, 1]        # Q1 đặt SL, Q2 dời SL       → quản trị rủi ro
_B1_QUESTIONS = [2, 3, 4]     # Q3 FOMO, Q4 panic, Q5 tip  → hành vi

# Câu Phương Pháp (Q6-Q10, index 5-9) — dùng tính method_clarity
_PP_QUESTIONS = [5, 6, 7, 8, 9]

# Ngưỡng ưu tiên khi điểm chênh nhau ít (điểm nghẽn nào gây hại nhanh hơn)
_TIE_THRESHOLD = 8
_PRIORITY = ['B1', 'B2', 'B4', 'B3', 'B5']

# Ngưỡng số lệnh để nâng mức tin cậy
_MIN_TRADES_HYBRID   = 6
_MIN_TRADES_PERSONAL = 20

BOTTLENECK_NAMES = {
    'B1': 'Hành vi',
    'B2': 'Quản trị rủi ro',
    'B3': 'Phương pháp',
    'B4': 'Thích nghi thị trường',
    'B5': 'Kiến thức',
}

# ========================================================================
# THƯ VIỆN CAN THIỆP — mỗi điểm nghẽn: chẩn đoán + MỘT việc duy nhất
# ========================================================================

INTERVENTIONS = {
    'B1': {
        'title': 'Hành vi — quyết định theo cảm xúc',
        'diagnosis_prior': (
            'Bài đánh giá cho thấy anh/chị dễ ra quyết định khi thị trường '
            'đang chạy hoặc khi thấy người khác hành động.'
        ),
        'action': 'Trước mỗi lệnh, mở Thẻ Quyết Định và đợi ít nhất 30 phút trước khi bấm mua.',
        'metric': 'Không có lệnh nào vào trong vòng 30 phút kể từ lúc nảy ý định.',
        'chips': ['Tôi có đang FOMO không?', 'Trước khi tôi mua'],
        'coach_note': (
            'User có điểm nghẽn HÀNH VI. Khi user hỏi về một mã đang tăng mạnh '
            'hoặc đang giảm mạnh, TRƯỚC TIÊN đối chiếu với cam kết tháng này của họ, '
            'sau đó mới nói về dữ liệu. Không giục hành động.'
        ),
    },
    'B2': {
        'title': 'Quản trị rủi ro — ngưỡng dừng lỗ và quy mô',
        'diagnosis_prior': (
            'Bài đánh giá cho thấy anh/chị chưa nhất quán trong việc đặt và '
            'giữ ngưỡng dừng lỗ, hoặc quy mô vị thế chưa theo quy tắc.'
        ),
        'action': 'Mọi lệnh phải có ngưỡng dừng lỗ xác định TRƯỚC khi mua — và không dời xuống.',
        'metric': '100% lệnh có ngưỡng dừng lỗ ghi trước; 0 lần dời ngưỡng.',
        'chips': ['Kiểm tra ngưỡng dừng lỗ danh mục', 'Tôi nên mua quy mô bao nhiêu'],
        'coach_note': (
            'User có điểm nghẽn QUẢN TRỊ RỦI RO. Mọi câu trả lời về cổ phiếu PHẢI '
            'nêu rõ ngưỡng dừng lỗ và hệ quả tính bằng % danh mục nếu chạm ngưỡng. '
            'Nếu user chưa có ngưỡng, hỏi trước khi phân tích tiếp.'
        ),
    },
    'B3': {
        'title': 'Phương pháp — chưa có neo phong cách',
        'diagnosis_prior': (
            'Câu trả lời của anh/chị phân tán giữa nhiều phong cách khác nhau. '
            'Chưa có neo phương pháp thường dẫn tới việc nhảy phong cách theo thị trường.'
        ),
        'action': 'Chọn MỘT phong cách và chỉ vào lệnh khớp phong cách đó trong 30 ngày.',
        'metric': '≥80% lệnh khớp khung thời gian của phong cách đã chọn.',
        'chips': ['Mã nào hợp hồ sơ của tôi', 'Phong cách của tôi phù hợp gì'],
        'coach_note': (
            'User có điểm nghẽn PHƯƠNG PHÁP. Khi thảo luận một mã, luôn nêu rõ '
            'mã đó thuộc khung thời gian nào và có khớp phong cách của user không. '
            'Nhắc user về khung nắm giữ tương ứng.'
        ),
    },
    'B4': {
        'title': 'Thích nghi — chưa điều chỉnh theo chế độ thị trường',
        'diagnosis_prior': (
            'Kết quả của anh/chị thay đổi mạnh giữa các chế độ thị trường — '
            'dấu hiệu của việc giữ nguyên cách đánh khi bối cảnh đã đổi.'
        ),
        'action': 'Mỗi sáng, đọc chế độ thị trường trước khi xem bất kỳ mã nào.',
        'metric': 'Tỷ trọng thực tế nằm trong khung của chế độ thị trường ≥80% số ngày.',
        'chips': ['Thị trường này tôi nên làm gì', 'Tỷ trọng của tôi có hợp lý'],
        'coach_note': (
            'User có điểm nghẽn THÍCH NGHI. Mọi câu trả lời PHẢI mở đầu bằng chế độ '
            'thị trường hiện tại và khung tỷ trọng tương ứng, trước khi nói về mã.'
        ),
    },
    'B5': {
        'title': 'Kiến thức — chưa nắm cơ chế',
        'diagnosis_prior': (
            'Bài đánh giá cho thấy anh/chị cần củng cố hiểu biết về tỷ lệ '
            'Rủi ro/Lợi nhuận, kỳ vọng toán học và chế độ thị trường.'
        ),
        'action': 'Với mỗi lệnh, viết một câu trả lời: "Vì sao setup này hoạt động?"',
        'metric': 'Mỗi lệnh có một dòng luận điểm ghi lại trước khi vào.',
        'chips': ['Giải thích setup này', 'Tỷ lệ R/R nghĩa là gì'],
        'coach_note': (
            'User có điểm nghẽn KIẾN THỨC. Kèm một giải thích cơ chế ngắn (2-3 câu) '
            'trong mỗi câu trả lời. Không dùng thuật ngữ mà không giải thích. '
            'KHÔNG mở khóa học — chỉ giải thích trong ngữ cảnh câu hỏi.'
        ),
    },
}


# ========================================================================
# TÍNH ĐIỂM TỪNG CHIỀU
# ========================================================================

def _score_from_answers(answers, question_idx):
    """
    Tính điểm 0-100 từ một nhóm câu hỏi.
    answers: list index lựa chọn (0-3) theo thứ tự câu hỏi.
    Trả về None nếu dữ liệu không dùng được.
    """
    if not answers or not isinstance(answers, list):
        return None
    total = 0
    max_total = 0
    for qi in question_idx:
        if qi >= len(answers):
            return None
        opt = answers[qi]
        if opt is None or not isinstance(opt, int) or opt < 0 or opt > 3:
            return None
        total += _OPT_SCORES[opt]
        max_total += 4
    if max_total == 0:
        return None
    return round(total / max_total * 100)


def _method_clarity(answers):
    """
    Độ rõ ràng phong cách: chênh lệch phiếu giữa lựa chọn số 1 và số 2.

    5/5 phiếu cùng một phong cách  → 100 (rất rõ)
    2/2/1 phân tán                 → 0   (mơ hồ — tín hiệu B3)

    Trả về None nếu không có dữ liệu answers.
    """
    if not answers or len(answers) < 10:
        return None
    # Ánh xạ lựa chọn → phong cách phải khớp IISTest.jsx (opt.method: s/m/l)
    # Vì backend không có bảng này, ta suy ra theo quy ước:
    #   Q6:  [l, m, m, s]     Q7:  [s, m, l]
    #   Q8:  [s, m, l]        Q9:  [l, m, s]
    #   Q10: [l, m, s]
    MAP = {
        5: ['l', 'm', 'm', 's'],
        6: ['s', 'm', 'l'],
        7: ['s', 'm', 'l'],
        8: ['l', 'm', 's'],
        9: ['l', 'm', 's'],
    }
    votes = {'s': 0, 'm': 0, 'l': 0}
    for qi, table in MAP.items():
        if qi >= len(answers):
            return None
        opt = answers[qi]
        if opt is None or not isinstance(opt, int) or opt >= len(table):
            continue
        votes[table[opt]] += 1
    total_votes = sum(votes.values())
    if total_votes < 4:
        return None
    ordered = sorted(votes.values(), reverse=True)
    gap = ordered[0] - ordered[1]
    return min(100, round(gap / 5 * 100))


def _load_iis(session, user_id):
    """Đọc IIS mới nhất. Trả về (profile_dict, answers_list_or_None)."""
    profile, answers = None, None
    try:
        row = session.execute(
            text("SELECT total, level_name, method, kl_score, kt_score, created_at "
                 "FROM iis_results WHERE user_id = :uid "
                 "ORDER BY created_at DESC LIMIT 1"),
            {"uid": str(user_id)}
        ).fetchone()
        if row:
            profile = {
                'total': row[0], 'level': row[1], 'method': row[2],
                'kl': row[3] or 0, 'kt': row[4] or 0,
                'tested_at': str(row[5]) if row[5] else None,
            }
    except Exception as e:
        print(f"[bottleneck] load iis error: {e}")
        return None, None

    # Cột answers có thể chưa tồn tại — degrade gracefully
    try:
        arow = session.execute(
            text("SELECT answers FROM iis_results WHERE user_id = :uid "
                 "ORDER BY created_at DESC LIMIT 1"),
            {"uid": str(user_id)}
        ).fetchone()
        if arow and arow[0]:
            raw = arow[0]
            answers = json.loads(raw) if isinstance(raw, str) else raw
            if not isinstance(answers, list):
                answers = None
    except Exception:
        answers = None   # bảng chưa có cột answers → dùng kl_score tổng

    return profile, answers


def _load_trade_stats(session, user_id):
    """
    Thống kê từ lệnh thật (nếu bảng trade_reviews đã tồn tại).
    Trả về dict hoặc None. Fail-soft: bảng chưa có → None.
    """
    try:
        row = session.execute(
            text("SELECT COUNT(*), AVG(process_score) "
                 "FROM trade_reviews WHERE user_email = :uid"),
            {"uid": str(user_id)}
        ).fetchone()
        if not row or not row[0]:
            return None
        n = int(row[0])
        if n == 0:
            return None

        stats = {'n_trades': n, 'avg_process': float(row[1] or 0)}

        # Tỷ lệ lệnh dời ngưỡng dừng lỗ → B2
        r2 = session.execute(
            text("SELECT COUNT(*) FROM trade_reviews "
                 "WHERE user_email = :uid AND q3_plan = 3"),
            {"uid": str(user_id)}
        ).fetchone()
        stats['n_moved_stop'] = int(r2[0]) if r2 else 0

        # Tỷ lệ lệnh vào ở trạng thái cảm xúc → B1
        r1 = session.execute(
            text("SELECT COUNT(*) FROM trade_reviews "
                 "WHERE user_email = :uid AND q2_emotion IN (3, 4)"),
            {"uid": str(user_id)}
        ).fetchone()
        stats['n_emotional'] = int(r1[0]) if r1 else 0

        # Chênh lệch kết quả giữa các chế độ thị trường → B4
        try:
            rows = session.execute(
                text("SELECT market_mode, "
                     "       SUM(CASE WHEN pnl_pct > 0 THEN 1 ELSE 0 END), "
                     "       COUNT(*) "
                     "FROM trade_reviews WHERE user_email = :uid "
                     "  AND market_mode IS NOT NULL "
                     "GROUP BY market_mode"),
                {"uid": str(user_id)}
            ).fetchall()
            wr = {}
            for mode, wins, cnt in rows:
                if cnt and cnt >= 3:
                    wr[mode] = round(float(wins) / float(cnt) * 100)
            stats['win_by_mode'] = wr
        except Exception:
            stats['win_by_mode'] = {}

        return stats
    except Exception:
        return None   # bảng chưa tồn tại — bình thường ở giai đoạn đầu


# ========================================================================
# CHẨN ĐOÁN
# ========================================================================

def diagnose(session_factory, user_id):
    """
    Chẩn đoán điểm nghẽn của một user.

    Args:
        session_factory: hàm Session của SQLAlchemy (gọi Session())
        user_id: email hoặc user_id

    Returns:
        dict — luôn trả về, kể cả khi chưa có IIS (bottleneck=None)
    """
    session = session_factory()
    try:
        profile, answers = _load_iis(session, user_id)

        if not profile:
            return {
                'has_iis': False,
                'bottleneck': None,
                'message': 'Chưa có kết quả IIS. Hãy làm bài đánh giá 15 câu (5 phút).',
                'chips': ['Làm bài đánh giá IIS là gì', 'Vì sao cần đo trình độ'],
            }

        stats = _load_trade_stats(session, user_id)
        n_trades = stats['n_trades'] if stats else 0

        # ---- Tính điểm 5 chiều ----
        scores = {}

        # B1 + B2: ưu tiên tách theo câu hỏi; nếu không có answers → dùng kl tổng
        b1_test = _score_from_answers(answers, _B1_QUESTIONS)
        b2_test = _score_from_answers(answers, _B2_QUESTIONS)
        if b1_test is None or b2_test is None:
            b1_test = b2_test = profile['kl']

        # Trộn với dữ liệu hành vi thật khi đã đủ lệnh
        if stats and n_trades >= _MIN_TRADES_HYBRID:
            obs_b1 = round((1 - stats['n_emotional'] / n_trades) * 100)
            obs_b2 = round((1 - stats['n_moved_stop'] / n_trades) * 100)
            w = 0.5 if n_trades < _MIN_TRADES_PERSONAL else 0.7
            scores['B1'] = round(b1_test * (1 - w) + obs_b1 * w)
            scores['B2'] = round(b2_test * (1 - w) + obs_b2 * w)
        else:
            scores['B1'] = b1_test
            scores['B2'] = b2_test

        # B3: độ rõ phong cách (proxy ngày 1)
        mc = _method_clarity(answers)
        if mc is not None:
            scores['B3'] = mc
        elif profile.get('method', '').startswith('hybrid'):
            scores['B3'] = 50   # hybrid = chưa có neo rõ ràng
        # nếu không tính được → bỏ B3 khỏi danh sách, không đoán bừa

        # B4: chỉ tính khi có đủ dữ liệu theo chế độ thị trường
        if stats and stats.get('win_by_mode') and len(stats['win_by_mode']) >= 2:
            vals = list(stats['win_by_mode'].values())
            spread = max(vals) - min(vals)
            scores['B4'] = max(0, 100 - spread)   # chênh càng lớn → điểm càng thấp

        # B5: kiến thức
        scores['B5'] = profile['kt']

        # ---- Chọn điểm nghẽn: thấp nhất, ưu tiên loại gây hại nhanh ----
        lowest = min(scores.values())
        candidates = [k for k, v in scores.items() if v - lowest <= _TIE_THRESHOLD]
        bottleneck = next((p for p in _PRIORITY if p in candidates), candidates[0])

        # ---- Mức tin cậy ----
        if n_trades >= _MIN_TRADES_PERSONAL:
            confidence = 'personal'
        elif n_trades >= _MIN_TRADES_HYBRID:
            confidence = 'hybrid'
        else:
            confidence = 'prior'

        info = INTERVENTIONS[bottleneck]
        diagnosis = info['diagnosis_prior']
        if confidence != 'prior' and stats:
            diagnosis = _personalize(bottleneck, stats, n_trades) or diagnosis

        return {
            'has_iis': True,
            'bottleneck': bottleneck,
            'bottleneck_name': BOTTLENECK_NAMES[bottleneck],
            'title': info['title'],
            'score': scores[bottleneck],
            'all_scores': scores,
            'diagnosis': diagnosis,
            'action': info['action'],
            'metric': info['metric'],
            'chips': info['chips'],
            'coach_note': info['coach_note'],
            'confidence': confidence,
            'n_trades': n_trades,
            'iis': {
                'total': profile['total'], 'level': profile['level'],
                'kl': profile['kl'], 'kt': profile['kt'],
                'method': profile['method'],
            },
        }
    except Exception as e:
        print(f"[bottleneck] diagnose error: {e}")
        return {'has_iis': False, 'bottleneck': None,
                'message': 'Chưa xác định được điểm nghẽn.', 'chips': []}
    finally:
        session.close()


def _personalize(bottleneck, stats, n):
    """Thay chẩn đoán chung bằng chẩn đoán dựa trên số liệu thật."""
    if bottleneck == 'B2' and stats.get('n_moved_stop'):
        k = stats['n_moved_stop']
        return (f'Trong {n} lệnh gần đây, anh/chị dời ngưỡng dừng lỗ {k} lần. '
                f'Đây là hành vi gây thiệt hại lớn nhất trong dữ liệu của anh/chị.')
    if bottleneck == 'B1' and stats.get('n_emotional'):
        k = stats['n_emotional']
        return (f'{k}/{n} lệnh được vào khi đang ở trạng thái sợ bỏ lỡ hoặc '
                f'muốn gỡ lệnh trước — không phải ở trạng thái bình thản.')
    if bottleneck == 'B4' and stats.get('win_by_mode'):
        wm = stats['win_by_mode']
        best = max(wm, key=wm.get)
        worst = min(wm, key=wm.get)
        return (f'Kết quả của anh/chị đạt {wm[best]}% trong chế độ {best} '
                f'nhưng chỉ {wm[worst]}% trong chế độ {worst}. '
                f'Cách đánh chưa điều chỉnh theo bối cảnh.')
    return None


# ========================================================================
# LƯU LỊCH SỬ ĐIỂM NGHẼN (theo tháng)
# ========================================================================

def persist(session_factory, user_id, result):
    """Ghi điểm nghẽn của tháng hiện tại. Idempotent theo (user, tháng)."""
    if not result or not result.get('bottleneck'):
        return False
    period = datetime.now().strftime('%Y-%m')
    session = session_factory()
    try:
        exists = session.execute(
            text("SELECT id FROM user_bottleneck "
                 "WHERE user_email = :u AND period = :p LIMIT 1"),
            {"u": str(user_id), "p": period}
        ).fetchone()
        if exists:
            session.execute(
                text("UPDATE user_bottleneck SET bottleneck=:b, score=:s, "
                     "all_scores=:a, intervention=:i, confidence=:c "
                     "WHERE id=:id"),
                {"b": result['bottleneck'], "s": int(result['score']),
                 "a": json.dumps(result['all_scores']),
                 "i": result['action'], "c": result['confidence'],
                 "id": exists[0]}
            )
        else:
            session.execute(
                text("INSERT INTO user_bottleneck "
                     "(user_email, period, bottleneck, score, all_scores, "
                     " intervention, confidence) "
                     "VALUES (:u,:p,:b,:s,:a,:i,:c)"),
                {"u": str(user_id), "p": period, "b": result['bottleneck'],
                 "s": int(result['score']), "a": json.dumps(result['all_scores']),
                 "i": result['action'], "c": result['confidence']}
            )
        session.commit()
        return True
    except Exception as e:
        print(f"[bottleneck] persist error: {e}")
        session.rollback()
        return False
    finally:
        session.close()


def history(session_factory, user_id, limit=6):
    """Lịch sử điểm nghẽn — dùng để hiển thị tiến bộ."""
    session = session_factory()
    try:
        rows = session.execute(
            text("SELECT period, bottleneck, score, confidence, resolved "
                 "FROM user_bottleneck WHERE user_email = :u "
                 "ORDER BY period DESC LIMIT :lim"),
            {"u": str(user_id), "lim": limit}
        ).fetchall()
        return [{
            'period': r[0], 'bottleneck': r[1],
            'bottleneck_name': BOTTLENECK_NAMES.get(r[1], r[1]),
            'score': r[2], 'confidence': r[3], 'resolved': bool(r[4]),
        } for r in rows]
    except Exception:
        return []
    finally:
        session.close()


# ========================================================================
# INJECT VÀO SYSTEM PROMPT
# ========================================================================

def build_bottleneck_section(result):
    """
    Tạo đoạn text chèn vào system prompt của GPT-4o.
    Gọi sau build_iis_coaching_section().
    """
    if not result or not result.get('bottleneck'):
        return ""
    return f"""

=== ĐIỂM NGHẼN CỦA USER (ưu tiên coaching) ===
Điểm nghẽn: {result['bottleneck']} — {result['title']}
Chẩn đoán: {result['diagnosis']}
VIỆC DUY NHẤT tháng này: {result['action']}
Mức tin cậy: {result['confidence']} ({result['n_trades']} lệnh đã ghi nhận)

HƯỚNG DẪN COACHING:
{result['coach_note']}

QUAN TRỌNG: Khi user hỏi bất cứ điều gì liên quan đến quyết định giao dịch,
LUÔN đối chiếu với "VIỆC DUY NHẤT" ở trên. Đây là cam kết của chính user,
không phải lời khuyên của bạn. Đối chiếu, không phán xét.
KHÔNG liệt kê nhiều điểm cần cải thiện — chỉ tập trung MỘT điểm nghẽn này.
"""


# ========================================================================
# API ROUTES
# ========================================================================

def init_bottleneck_routes(app, session_factory):
    """Đăng ký routes. Gọi trong backend_api.py sau khi có Session."""
    from flask import jsonify

    @app.route('/api/bottleneck/<path:user_id>', methods=['GET'])
    def get_bottleneck(user_id):
        result = diagnose(session_factory, user_id)
        if result.get('bottleneck'):
            persist(session_factory, user_id, result)
        result['history'] = history(session_factory, user_id)
        return jsonify({'success': True, **result})

    @app.route('/api/chips/<path:user_id>', methods=['GET'])
    def get_chips(user_id):
        """
        Chip gợi ý cho khung chat — thay thế menu.
        Tối đa 2 chip. Ưu tiên: lệnh chờ đánh giá > điểm nghẽn.
        """
        chips = []

        # Ưu tiên 1: có lệnh đã đóng chưa đánh giá
        session = session_factory()
        try:
            row = session.execute(
                text("SELECT tc.ticker FROM trade_commitments tc "
                     "LEFT JOIN trade_reviews tr ON tr.commitment_id = tc.id "
                     "WHERE tc.user_email = :u AND tr.id IS NULL "
                     "ORDER BY tc.created_at DESC LIMIT 1"),
                {"u": str(user_id)}
            ).fetchone()
            if row:
                chips.append(f'Đánh giá lệnh {row[0]}')
        except Exception:
            pass
        finally:
            session.close()

        # Ưu tiên 2: chip theo điểm nghẽn
        result = diagnose(session_factory, user_id)
        for c in result.get('chips', []):
            if len(chips) >= 2:
                break
            chips.append(c)

        return jsonify({
            'success': True,
            'chips': chips[:2],
            'bottleneck': result.get('bottleneck'),
        })

    print("✅ Bottleneck routes registered: /api/bottleneck/*, /api/chips/*")


# ========================================================================
# SELF-TEST
# ========================================================================

if __name__ == '__main__':
    print("=" * 70)
    print("BOTTLENECK ENGINE — SELF TEST (không cần DB)")
    print("=" * 70)

    # Mô phỏng user trong ảnh chụp: IIS 50, kl=45, kt=55, hybrid_sm
    # answers: Q1..Q5 kỷ luật, Q6..Q10 phương pháp
    cases = [
        ("Nghẽn quản trị rủi ro (không đặt SL, hay dời)",
         [0, 0, 3, 3, 3,  1, 1, 1, 1, 1]),
        ("Nghẽn hành vi (FOMO, panic, mua theo tip)",
         [3, 3, 0, 0, 0,  0, 0, 0, 0, 0]),
        ("Nghẽn phương pháp (phiếu phân tán)",
         [3, 3, 3, 3, 3,  0, 2, 0, 2, 1]),
    ]

    for label, ans in cases:
        b1 = _score_from_answers(ans, _B1_QUESTIONS)
        b2 = _score_from_answers(ans, _B2_QUESTIONS)
        b3 = _method_clarity(ans)
        scores = {'B1': b1, 'B2': b2, 'B5': 55}
        if b3 is not None:
            scores['B3'] = b3
        lowest = min(scores.values())
        cand = [k for k, v in scores.items() if v - lowest <= _TIE_THRESHOLD]
        pick = next((p for p in _PRIORITY if p in cand), cand[0])
        print(f"\n{label}")
        print(f"  scores      : {scores}")
        print(f"  → điểm nghẽn: {pick} — {INTERVENTIONS[pick]['title']}")
        print(f"  → việc duy nhất: {INTERVENTIONS[pick]['action']}")
        print(f"  → chips     : {INTERVENTIONS[pick]['chips']}")

    print("\n" + "=" * 70)
