import logging
from datetime import date

import pytest

logger = logging.getLogger(__name__)

D = date
PHASE = 3


def synthetic_prod(
    daily_production_reports, start, days, phase=PHASE, tons=130.0
):
    """Tạo prod: mỗi ngày 2 kíp đúng ca đều có `tons` tấn."""
    out = {}
    for i in range(days):
        d = D.fromordinal(start.toordinal() + i)
        out[d] = {c: tons for c in daily_production_reports.on_duty(d, phase)}
    return out


def test_tc01_export_report_to_excel(daily_production_reports):
    daily_production_reports.export_report_to_excel(merge_spill=True)


def test_tc02_get_finished_production(daily_production_reports, debug=False):
    result = daily_production_reports.get_finished_production(
        from_date="2026-10-01", to_date="2026-10-02"
    )

    # result = [
    #     {
    #         "name": "cut_roll_production",
    #         "tags": {"crew": "A"},
    #         "columns": ["time", "sum"],
    #         "values": [["2026-10-01T17:00:00Z", 155.845]],
    #     },
    #     {
    #         "name": "cut_roll_production",
    #         "tags": {"crew": "B"},
    #         "columns": ["time", "sum"],
    #         "values": [
    #             ["2026-09-30T17:00:00Z", 105.804],
    #             ["2026-10-01T17:00:00Z", 150.272],
    #         ],
    #     },
    #     {
    #         "name": "cut_roll_production",
    #         "tags": {"crew": "C"},
    #         "columns": ["time", "sum"],
    #         "values": [["2026-09-30T17:00:00Z", 158.561]],
    #     },
    # ]

    if debug:
        logger.info(f"Result: {result}")


def test_tc03_get_roll_production(daily_production_reports, debug=False):
    result = daily_production_reports.get_roll_production(
        from_date="2026-10-01", to_date="2026-10-03", phase=3
    )

    if debug:
        logger.info(f"Result: {result}")


def test_tc04_get_steam(daily_production_reports, debug=False):
    result = daily_production_reports.get_steam(
        from_date="2026-10-01", to_date="2026-10-02"
    )

    if debug:
        logger.info(f"Result: {result}")


def test_tc05_get_water(daily_production_reports, debug=False):
    result = daily_production_reports.get_water(
        from_date="2026-10-01", to_date="2026-10-02"
    )

    if debug:
        logger.info(f"Result: {result}")


def test_tc06_get_run_time(daily_production_reports, debug=True):
    result = daily_production_reports.get_run_time(
        from_date="2026-10-01", to_date="2026-10-02"
    )

    if debug:
        logger.info(f"Run Time: {result[0]}")
        logger.info(f"Down Time: {result[1]}")


class TestOnDuty:
    @pytest.mark.parametrize(
        "d,expected",
        [
            (D(2026, 10, 1), ("B", "C")),
            (D(2026, 10, 2), ("A", "B")),
            (D(2026, 10, 3), ("A", "B")),
            (D(2026, 10, 4), ("C", "A")),
            (D(2026, 10, 5), ("C", "A")),
            (D(2026, 10, 6), ("B", "C")),
            (D(2026, 9, 16), ("C", "A")),
            (D(2026, 9, 27), ("A", "B")),
        ],
    )
    def test_cap_kip_theo_ngay(self, daily_production_reports, d, expected):
        """
        ĐẦU VÀO : (ngày, phase=3) như tham số
        ĐẦU RA  : cặp kíp tương ứng, ví dụ 2026-10-01
                  -> ("B","C"), 2026-10-04 -> ("C","A")
        """
        assert daily_production_reports.on_duty(d, PHASE) == expected

    def test_tuan_hoan_6_ngay(self, daily_production_reports):
        """
        input: d and d+6, d+12, phase=3
        output: cùng một cặp kíp (chu kỳ 6 ngày)
        """
        d = D(2026, 10, 1)
        assert daily_production_reports.on_duty(
            d, PHASE
        ) == daily_production_reports.on_duty(D(2026, 10, 13), PHASE)

    def test_doi_pha_la_doi_ngay(self, daily_production_reports):
        """
        input: phase=3 và phase=4 cho cùng một ngày d
        output: on_duty(d, 4) == on_duty(d+1, 3)
        (tăng pha 1 = dịch lịch 1 ngày)
        """
        d = D(2026, 10, 1)
        assert daily_production_reports.on_duty(
            d, 4
        ) == daily_production_reports.on_duty(D(2026, 10, 2), 3)

    def test_moi_ngay_dung_2_kip_khac_nhau(self, daily_production_reports):
        """
        ĐẦU VÀO : mọi ngày trong 12 ngày liên tiếp, phase=3
        ĐẦU RA  : mỗi ngày có đúng 2 kíp, khác nhau, thuộc {A,B,C}
        """
        for _ in range(12):
            duty = daily_production_reports.on_duty(
                D.fromordinal(D(2026, 10, 1).toordinal() + 1), PHASE
            )
            assert len(set(duty)) == 2 and set(duty) <= {"A", "B", "C"}


class TestDetectPhase:
    @pytest.mark.parametrize("true_phase", range(6))
    def test_tim_dung_pha(self, daily_production_reports, true_phase):
        """
        ĐẦU VÀO : 12 ngày từ 01/10, mỗi ngày kíp đúng ca
            có 130 tấn, sinh theo pha true_phase (0..5)
        ĐẦU RA  : đúng true_phase
        """
        prod = synthetic_prod(
            daily_production_reports, D(2026, 10, 1), 12, phase=true_phase
        )
        assert daily_production_reports.detect_phase(prod) == true_phase

    def test_chiu_duoc_nhieu(self, daily_production_reports):
        """
        ĐẦU VÀO : dữ liệu pha 3 (12 ngày) +
            thêm vài số lẻ ở kíp nghỉ (13.861, 3.225) + 1 ngày kíp A chỉ 10 tấn
        ĐẦU RA  : vẫn là 3
        """
        prod = synthetic_prod(daily_production_reports, D(2026, 10, 1), 12)
        d1, d2 = D(2026, 10, 1), D(2026, 10, 2)
        prod[d1]["A"] = 13.861
        prod[d2]["C"] = 3.225
        prod[d2]["A"] = 10.0
        assert daily_production_reports.detect_phase(prod) == PHASE

    def test_dung_du_lieu_nhieu_thang(self, daily_production_reports):
        """
        ĐẦU VÀO : 29 ngày từ 16/09 (qua 2 tháng), pha 3
        ĐẦU RA  : 3
        """
        assert (
            daily_production_reports.detect_phase(
                synthetic_prod(daily_production_reports, D(2026, 9, 16), 29)
            )
            == PHASE
        )


class TestMergeSpill:
    def base(self):
        return {
            D(2026, 9, 17): {"A": 81.163, "C": 45.0},
            D(2026, 9, 18): {"B": 113.12, "C": 121.664},
            D(2026, 9, 19): {"A": 13.861, "B": 78.565, "C": 130.461},
        }

    def test_gop_vao_ca_truoc_cua_cung_kip(self, daily_production_reports):
        """
        ĐẦU VÀO : 19/09 kíp A nghỉ nhưng có 13.861 tấn;
            A làm việc gần nhất trước đó là 17/09 (81.163 tấn)
        ĐẦU RA  : new[17/09]["A"] = 95.024 ; new[19/09]
            không còn "A" ; log có đúng 1 dòng nhắc
            2026-09-19 -> 2026-09-17
        """
        new, log = daily_production_reports.merge_spill(self.base(), PHASE)
        assert new[D(2026, 9, 17)]["A"] == pytest.approx(95.024)
        assert "A" not in new[D(2026, 9, 19)]
        assert (
            len(log) == 1 and "2026-09-19" in log[0] and "2026-09-17" in log[0]
        )

    def test_khong_sua_du_lieu_goc(self, daily_production_reports):
        """
        ĐẦU VÀO : prod gốc (có spill)
        ĐẦU RA  : prod gốc không bị thay đổi
            (vẫn A=13.861 ở 19/09, A=81.163 ở 17/09)
        """
        prod = self.base()
        daily_production_reports.merge_spill(prod, PHASE)
        assert (
            prod[D(2026, 9, 19)]["A"] == 13.861
            and prod[D(2026, 9, 17)]["A"] == 81.163
        )

    def test_tao_ngay_dich_neu_chua_co(self, daily_production_reports):
        """
        ĐẦU VÀO : chỉ có 29/09 {"B": 3.225} (kíp B nghỉ ngày C,A);
            B làm gần nhất trước đó là 27/09 (chưa có trong prod)
        ĐẦU RA  : new[27/09] = {"B": 3.225} ; new[29/09] = {}
        """
        new, log = daily_production_reports.merge_spill(
            {D(2026, 9, 29): {"B": 3.225}}, PHASE
        )
        assert new[D(2026, 9, 27)] == {"B": 3.225}
        assert new[D(2026, 9, 29)] == {}
        assert len(log) == 1

    def test_khong_gop_gia_tri_0(self, daily_production_reports):
        """
        ĐẦU VÀO : 05/10 (C,A) kíp B nghỉ có 0 tấn
        ĐẦU RA  : không đổi, log rỗng
        """
        prod = {D(2026, 10, 5): {"C": 93.539, "A": 135.966, "B": 0}}
        new, log = daily_production_reports.merge_spill(prod, PHASE)
        assert new == prod and log == []

    def test_khong_gop_kip_dung_ca_san_luong_thap(
        self, daily_production_reports
    ):
        """
        ĐẦU VÀO : 20/09 (A,B) kíp A đúng ca nhưng chỉ 10.297 tấn
        ĐẦU RA  : không đổi, log rỗng (kíp đúng ca không phải spill)
        """
        prod = {D(2026, 9, 20): {"A": 10.297, "B": 135.232}}
        new, log = daily_production_reports.merge_spill(prod, PHASE)
        assert new == prod and log == []

    def test_khong_gop_new_tu_nguong_tro_len(self, daily_production_reports):
        """
        ĐẦU VÀO : 19/09 (B,C) kíp A nghỉ nhưng có
            45 tấn (>= MIN_TON=20)
        ĐẦU RA  : không đổi, log rỗng (đây là bất
            thường để cảnh báo, không phải cuộn lẻ)
        """
        prod = {D(2026, 9, 19): {"A": 45.0, "B": 79.0, "C": 130.0}}
        new, log = daily_production_reports.merge_spill(prod, PHASE)
        assert new == prod and log == []

    def test_khong_co_spill(self, daily_production_reports):
        """
        ĐẦU VÀO : dữ liệu sạch 12 ngày
        ĐẦU RA  : giống hệt đầu vào, log rỗng
        """
        prod = synthetic_prod(daily_production_reports, D(2026, 10, 1), 12)
        new, log = daily_production_reports.merge_spill(prod, PHASE)
        assert new == prod and log == []


class TestBuildColumns:
    def test_khong_bao_gio_none_va_kip_nghi_ban_0(
        self, daily_production_reports
    ):
        """
        ĐẦU VÀO : days=[01/10 (B,C), 02/10 (A,B), 03/10 (A,B)],
            tons chỉ có 01/10 {B:105.80449, C:158.561}, phase=3
        ĐẦU RA  : A=[0,0,0] ; B=[105.804,0,0] ; C=[158.561,0,0]
            (kíp nghỉ / ngày thiếu dữ liệu = 0, không None)
        """
        days = [D(2026, 10, 1), D(2026, 10, 2), D(2026, 10, 3)]
        cols = daily_production_reports.build_columns(
            days, {D(2026, 10, 1): {"B": 105.80449, "C": 158.561}}, 3
        )
        assert cols == {
            "A": [0, 0, 0],
            "B": [105.804, 0, 0],
            "C": [158.561, 0, 0],
        }

    def test_so_le_kip_nghi_bi_bo_khi_khong_gop(self, daily_production_reports):
        """
        ĐẦU VÀO : 19/09 (B,C) có A=13.861 (kíp nghỉ), merge_spill=False
        ĐẦU RA  : cột A = [0] (số lẻ bị bỏ)
        """
        cols = daily_production_reports.build_columns(
            [D(2026, 9, 19)],
            {D(2026, 9, 19): {"A": 13.861, "B": 79.565, "C": 130.461}},
            3,
        )
        assert cols["A"] == [0] and cols["B"] == [79.565]

    def test_gop_so_le_vao_ca_truoc(self, daily_production_reports):
        """
        ĐẦU VÀO : days=[17/09, 19/09]; 17/09 (C,A) A=81.163 ;
            19/09 (B,C) A=13.861 ; merge_spill=True
        ĐẦU RA  : cột A = [95.024, 0]  (13.861 cộng vào 17/09 của chính kíp A)
        """
        tons = {
            D(2026, 9, 17): {"A": 81.163, "C": 45.0},
            D(2026, 9, 19): {"A": 13.861, "B": 79.565, "C": 130.461},
        }
        cols = daily_production_reports.build_columns(
            [D(2026, 9, 17), D(2026, 9, 19)], tons, 3, merge_spill=True
        )
        assert cols["A"] == [95.024, 0]
