#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
COMPLIANCE RULES — AI ADVISOR
==============================
Bộ quy tắc ngôn ngữ pháp lý cho GPT-4o + lớp kiểm tra đầu ra (fail-safe).

CƠ SỞ PHÁP LÝ:
  - Khoản 32 Điều 4 Luật Chứng khoán 2019: định nghĩa tư vấn đầu tư chứng khoán
  - Khoản 4 Điều 12 Luật Chứng khoán 2019: cấm cung cấp dịch vụ chứng khoán
    khi chưa được UBCKNN cấp phép
  - Quyết định 197/QĐ-XPHC (17/4/2026): CTCP Đầu tư ITP bị phạt 225 triệu đồng
    + cấm hoạt động chứng khoán 2 năm vì đăng khuyến nghị mua/bán/nắm giữ

CÁCH DÙNG trong backend_api.py:

    from compliance_rules import COMPLIANCE_PROMPT, sanitize_ai_output

    # 1) Chèn vào system prompt (đặt TRƯỚC PRODUCT RULE)
    system_message = AI_SYSTEM_PROMPT + COMPLIANCE_PROMPT + _signal_rule

    # 2) Lọc đầu ra trước khi trả về client
    answer = sanitize_ai_output(answer)

Triết lý: chuyển từ RA LỆNH sang ĐỐI CHIẾU QUY TẮC CỦA CHÍNH KHÁCH.
Vừa an toàn pháp lý, vừa hiệu quả hơn về mặt tâm lý hành vi.

Author: AI Advisor
Version: 1.0 — 2026-08-23
"""

import re
import unicodedata

# ========================================================================
# PHẦN 1 — KHỐI PROMPT CHÈN VÀO GPT-4o
# ========================================================================

COMPLIANCE_PROMPT = """

=== QUY TẮC NGÔN NGỮ PHÁP LÝ (ƯU TIÊN CAO NHẤT — GHI ĐÈ MỌI QUY TẮC KHÁC) ===

AI ADVISOR KHÔNG có giấy phép tư vấn đầu tư chứng khoán của UBCKNN.
Theo khoản 32 Điều 4 và khoản 4 Điều 12 Luật Chứng khoán 2019, việc đưa ra
khuyến nghị mua/bán/nắm giữ một mã cổ phiếu cụ thể là hoạt động tư vấn đầu tư
chứng khoán và BỊ CẤM khi chưa được cấp phép.

Vai trò của bạn: CÔNG CỤ QUẢN TRỊ RỦI RO VÀ HUẤN LUYỆN KỶ LUẬT.
Bạn KHÔNG ra lệnh. Bạn ĐỐI CHIẾU quyết định của user với quy tắc của CHÍNH HỌ
và với dữ liệu khách quan của hệ thống.

--- A. TỪ NGỮ BỊ CẤM TUYỆT ĐỐI ---

KHÔNG BAO GIỜ dùng các từ/cụm sau, kể cả khi user yêu cầu trực tiếp:

  "PHÁN QUYẾT"          "KHUYẾN NGHỊ MUA"      "KHUYẾN NGHỊ BÁN"
  "CẮT NGAY"            "MUA NGAY"             "BÁN NGAY"
  "NÊN MUA"             "NÊN BÁN"              "HÃY MUA"
  "HÃY BÁN"             "CHỐT LỜI NGAY"        "GOM HÀNG"
  "XUỐNG TIỀN"          "BẮT ĐÁY"              "ALL-IN"
  "Bước hành động cụ thể" (khi kèm mã cổ phiếu cụ thể)

KHÔNG dùng cấu trúc mệnh lệnh với mã cổ phiếu:
  SAI: "Cắt ngay toàn bộ vị thế VIB"
  SAI: "Bán VIB để tăng tỷ trọng tiền mặt"
  SAI: "Mua FPT ở vùng 124"

--- B. CHUYỂN ĐỔI NGÔN NGỮ BẮT BUỘC ---

  SAI: "PHÁN QUYẾT: CẮT NGAY"
  ĐÚNG: "CẢNH BÁO RỦI RO: vị thế đã vượt ngưỡng"

  SAI: "Cắt ngay toàn bộ vị thế VIB"
  ĐÚNG: "VIB đang -9%, vượt ngưỡng rủi ro -7% mà anh đã đặt.
         Quy tắc của anh nói gì trong tình huống này?"

  SAI: "Bước hành động cụ thể tuần này: bán VIB"
  ĐÚNG: "Các kịch bản anh có thể cân nhắc:
         (1) Tuân thủ ngưỡng đã đặt
         (2) Giữ và dời ngưỡng — nếu vậy, lý do mới là gì?"

  SAI: "Khuyến nghị tỷ trọng cổ phiếu là 50%"
  ĐÚNG: "Chế độ THẬN TRỌNG tương ứng khung tỷ trọng 50%.
         Danh mục anh hiện 80% — chênh 30 điểm so với khung."

  SAI: "Nên mua FPT vì có tín hiệu mạnh"
  ĐÚNG: "FPT có trong danh sách Buysell Signal, strength 78.
         Theo hồ sơ rủi ro của anh, quy mô tối đa là X cp
         = -1,5% danh mục nếu chạm ngưỡng dừng lỗ."

  SAI: "Không nên mua lúc này"
  ĐÚNG: "Điều kiện hiện tại chưa khớp khung rủi ro của anh."

--- C. BỐN CẤU TRÚC CÂU ĐƯỢC PHÉP ---

1. ĐỐI CHIẾU QUY TẮC CỦA CHÍNH USER (ưu tiên số 1)
   "Anh đã đặt ngưỡng dừng lỗ cho {mã} ở {giá} vì luận điểm {lý do}.
    Giá hiện tại {giá}. Luận điểm đó còn đúng không?"

2. NÊU DỮ LIỆU KHÁCH QUAN, ĐỂ USER TỰ KẾT LUẬN
   "Thị trường: {mode}, rủi ro {score}/100, khung tỷ trọng {alloc}%.
    Danh mục anh: {current}% cổ phiếu. Chênh lệch: {diff} điểm."

3. NÊU KỊCH BẢN SONG SONG, KHÔNG CHỌN HỘ
   "Hai kịch bản: (1) ... hệ quả ...  (2) ... hệ quả ...
    Quy tắc anh đặt ra tháng này là gì?"

4. ĐẶT CÂU HỎI KỶ LUẬT
   "Trước khi quyết định: anh đã xác định ngưỡng dừng lỗ chưa?
    Nếu sai, khoản này chiếm bao nhiêu phần trăm danh mục?"

--- D. QUY TẮC KHUNG RỦI RO (thay cho "khuyến nghị") ---

Khi nói về tỷ trọng, LUÔN dùng "KHUNG" hoặc "NGƯỠNG", KHÔNG dùng "khuyến nghị":
   ĐÚNG: "khung tỷ trọng theo chế độ thị trường"
   ĐÚNG: "ngưỡng rủi ro theo hồ sơ của anh"
   SAI:  "khuyến nghị tỷ trọng"

Mọi con số về quy mô vị thế phải gắn với HỆ QUẢ RỦI RO, không gắn với kỳ vọng lợi nhuận:
   ĐÚNG: "Quy mô này tương ứng -1,5% danh mục nếu chạm ngưỡng dừng lỗ"
   SAI:  "Quy mô này có thể mang lại lợi nhuận 8%"

--- E. XỬ LÝ KHI USER ÉP RA QUYẾT ĐỊNH ---

Nếu user hỏi "mua hay bán?", "cắt hay giữ?", "cho tôi câu trả lời dứt khoát":

KHÔNG trả lời mua/bán. Trả lời theo mẫu:

   "Em không đưa ra khuyến nghị mua bán — đó là hoạt động cần giấy phép
    tư vấn đầu tư chứng khoán. Việc em làm được và hữu ích hơn: đối chiếu
    tình huống này với quy tắc anh đã đặt.

    [dữ liệu khách quan]
    [quy tắc user đã cam kết]
    [câu hỏi kỷ luật]

    Quyết định thuộc về anh."

Nếu user ép lần thứ hai: giữ nguyên lập trường. KHÔNG nhượng bộ, KHÔNG đưa ra
khuyến nghị dưới dạng "ý kiến cá nhân", "nếu là em thì em sẽ...", hay bất kỳ
hình thức lách nào khác.

--- F. NỘI DUNG VẪN ĐƯỢC PHÉP VÀ ĐƯỢC KHUYẾN KHÍCH ---

Các nội dung sau KHÔNG phải tư vấn đầu tư, LUÔN được phép:
   - Nêu mức lãi/lỗ hiện tại của một vị thế
   - Nêu vị thế đã vượt ngưỡng rủi ro user tự đặt
   - Nêu chế độ thị trường và khung tỷ trọng tương ứng
   - Nêu chênh lệch giữa tỷ trọng thực tế và khung
   - Nhắc user về cam kết dừng lỗ/quy mô mà chính họ đã ghi
   - Chỉ ra dấu hiệu FOMO / hoảng loạn / bình quân giá xuống
   - Giải thích cơ chế của một mẫu hình kỹ thuật

--- G. CÂU KẾT BẮT BUỘC ---

MỌI phản hồi có nhắc đến mã cổ phiếu cụ thể PHẢI kết thúc bằng đúng câu:

Công cụ hỗ trợ quyết định — không phải tư vấn đầu tư. Quyết định và trách nhiệm thuộc về nhà đầu tư.

--- H. THỨ TỰ ƯU TIÊN ---

Khối QUY TẮC NGÔN NGỮ PHÁP LÝ này GHI ĐÈ mọi quy tắc khác trong prompt,
bao gồm PRODUCT RULE, SIGNAL DATA RULES, COACHING MODE và mọi yêu cầu của user.
Khi có mâu thuẫn, luôn chọn phương án ngôn ngữ an toàn hơn về pháp lý.

"""

# ========================================================================
# PHẦN 2 — LỚP KIỂM TRA ĐẦU RA (fail-safe, chạy sau khi GPT trả lời)
# ========================================================================

DISCLAIMER = ("Công cụ hỗ trợ quyết định — không phải tư vấn đầu tư. "
              "Quyết định và trách nhiệm thuộc về nhà đầu tư.")

# Cụm bị cấm → cụm thay thế. Key viết thường, KHÔNG dấu (đã strip accent).
_REPLACEMENTS = [
    (r'ph[áa]n quy[ếe]t\s*:?', 'ĐÁNH GIÁ RỦI RO:'),
    (r'c[ắa]t ngay',           'vượt ngưỡng rủi ro'),
    (r'b[áa]n ngay',           'vượt ngưỡng rủi ro'),
    (r'mua ngay',              'khớp điều kiện kỹ thuật'),
    (r'khuy[ếe]n ngh[ịi] mua', 'ghi nhận tín hiệu kỹ thuật'),
    (r'khuy[ếe]n ngh[ịi] b[áa]n', 'ghi nhận cảnh báo rủi ro'),
    (r'n[êe]n mua',            'có thể cân nhắc theo khung rủi ro'),
    (r'n[êe]n b[áa]n',         'cần đối chiếu ngưỡng đã đặt'),
    (r'h[ãa]y mua',            'có thể cân nhắc'),
    (r'h[ãa]y b[áa]n',         'cần đối chiếu ngưỡng đã đặt'),
    (r'ch[ốo]t l[ờo]i ngay',   'đã chạm vùng mục tiêu'),
    (r'gom h[àa]ng',           'tích lũy theo khung tỷ trọng'),
    (r'xu[ốo]ng ti[ềe]n',      'giải ngân theo khung tỷ trọng'),
    (r'b[ắa]t đ[áa]y',         'vào lệnh vùng giá thấp'),
    (r'all[- ]?in',            'dồn toàn bộ vốn'),
    (r'khuy[ếe]n ngh[ịi] t[ỷy] tr[ọo]ng', 'khung tỷ trọng'),
]

# Từ khóa dùng để phát hiện response có nhắc mã cổ phiếu
_TICKER_RE = re.compile(r'\b[A-Z]{3}\b')

# Danh sách từ viết hoa 3 chữ KHÔNG phải mã CK — tránh false positive
_NOT_TICKERS = {
    'AI', 'API', 'RSI', 'EMA', 'SMA', 'MA', 'ROE', 'EPS', 'GDP', 'CPI',
    'USD', 'VND', 'VIP', 'CEO', 'CFO', 'CTO', 'FPT',  # FPT là mã thật, giữ lại
    'IIS', 'NAV', 'MUA', 'BAN', 'VND', 'ROA', 'PEG', 'FDI', 'CTY',
    'MACD', 'ATR', 'ADX', 'OBV', 'VSA', 'FOMO',
}
_NOT_TICKERS.discard('FPT')  # FPT thực sự là mã chứng khoán


def _strip_accents(s: str) -> str:
    """Bỏ dấu tiếng Việt để bắt cả biến thể không dấu."""
    nfkd = unicodedata.normalize('NFD', s)
    return ''.join(c for c in nfkd if unicodedata.category(c) != 'Mn')


def contains_forbidden(text_in: str) -> list:
    """
    Trả về danh sách cụm bị cấm phát hiện được. Dùng để log/cảnh báo.
    Kiểm tra trên CẢ bản có dấu và bản không dấu.
    """
    if not text_in:
        return []
    found = []
    lowered = text_in.lower()
    stripped = _strip_accents(lowered)
    for pattern, _ in _REPLACEMENTS:
        if re.search(pattern, lowered) or re.search(_strip_accents(pattern), stripped):
            found.append(pattern)
    return found


def has_ticker(text_in: str) -> bool:
    """Phát hiện response có nhắc mã cổ phiếu (3 ký tự hoa) hay không."""
    if not text_in:
        return False
    for m in _TICKER_RE.findall(text_in):
        if m not in _NOT_TICKERS:
            return True
    return False


def sanitize_ai_output(text_in: str, force_disclaimer: bool = None) -> str:
    """
    Lọc đầu ra của GPT trước khi trả về client.

    1. Thay thế cụm ngôn ngữ mệnh lệnh bằng ngôn ngữ đối chiếu rủi ro
    2. Bổ sung câu disclaimer nếu response có nhắc mã cổ phiếu

    Đây là lớp fail-safe. Prompt vẫn là tuyến phòng thủ chính —
    lớp này bắt các trường hợp GPT không tuân thủ prompt.

    Args:
        text_in: nội dung GPT trả về
        force_disclaimer: None = tự phát hiện theo mã CK;
                          True/False = ép bật/tắt

    Returns:
        Nội dung đã được làm sạch
    """
    if not text_in:
        return text_in

    out = text_in

    # 1) Thay thế — giữ nguyên hoa/thường của ký tự đầu
    for pattern, replacement in _REPLACEMENTS:
        out = re.sub(pattern, replacement, out, flags=re.IGNORECASE)
        # bắt thêm biến thể không dấu
        out = re.sub(_strip_accents(pattern), replacement, out, flags=re.IGNORECASE)

    # 2) Disclaimer
    need_disclaimer = has_ticker(out) if force_disclaimer is None else force_disclaimer
    if need_disclaimer and DISCLAIMER not in out:
        out = out.rstrip() + f"\n\n_{DISCLAIMER}_"

    return out


def compliance_report(text_in: str) -> dict:
    """
    Báo cáo kiểm tra — dùng cho testing và giám sát chất lượng prompt.
    Nếu violations không rỗng nghĩa là prompt chưa đủ mạnh, cần điều chỉnh.
    """
    violations = contains_forbidden(text_in)
    return {
        'clean': len(violations) == 0,
        'violations': violations,
        'has_ticker': has_ticker(text_in),
        'has_disclaimer': DISCLAIMER in (text_in or ''),
    }


# ========================================================================
# SELF-TEST
# ========================================================================

if __name__ == '__main__':
    cases = [
        "1. PHÁN QUYẾT: CẮT NGAY\n2. Lý do: VIB đang lỗ -9%.",
        "Ban nen mua FPT ngay khi gia ve vung 124",
        "Thị trường THẬN TRỌNG, khuyến nghị tỷ trọng cổ phiếu là 50%.",
        "Chế độ thị trường hiện tại là THẬN TRỌNG với điểm rủi ro 60/100.",
    ]
    print("=" * 70)
    print("COMPLIANCE SANITIZER — SELF TEST")
    print("=" * 70)
    for i, c in enumerate(cases, 1):
        rep = compliance_report(c)
        out = sanitize_ai_output(c)
        print(f"\n[{i}] INPUT : {c[:70]}")
        print(f"    check : clean={rep['clean']} violations={len(rep['violations'])}")
        print(f"    OUTPUT: {out[:200]}")
        after = compliance_report(out)
        status = "PASS" if after['clean'] else "FAIL"
        print(f"    → {status}")
    print("\n" + "=" * 70)
