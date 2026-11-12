from datetime import date, datetime

import pytest

import miza_datahub.services.grafana_time as grafana_time

D = date
NOW = datetime(2026, 10, 16, 10, 30, tzinfo=grafana_time.TZ)


class TestResolveDays:
    def test_iso_utc_cua_grafana(self):
        """
        ĐẦU VÀO : from=2026-09-13T17:00:00.000Z, to=2026-10-04T16:59:59.000Z
        ĐẦU RA  : 21 ngày, 14/09/2026 -> 04/10/2026
            (17:00Z = 00:00 giờ VN; 16:59:59Z = 23:59:59 giờ VN)
        """
        days, s, e = grafana_time.resolve_days(
            "2026-09-13T17:00:00.000Z", "2026-10-04T16:59:59.000Z"
        )
        assert (days[0], days[-1], len(days)) == (
            D(2026, 9, 14),
            D(2026, 10, 4),
            21,
        )

    def test_now_tru_30_ngay(self):
        """
        ĐẦU VÀO: from=now-30d, to=now, now=16/10/2026 10:30
        ĐẦU RA: 16/09 -> 16/10 (31 ngày)
        """
        days, *_ = grafana_time.resolve_days("now-30d", "now", now=NOW)
        assert (days[0], days[-1], len(days)) == (
            D(2026, 9, 16),
            D(2026, 10, 16),
            31,
        )

    def test_tuan_truoc_lam_tron(self):
        """
        ĐẦU VÀO : from=now-1w/w, to=now-1w/w,
            now=Thứ Sáu 16/10, tuần bắt đầu thứ Hai
        ĐẦU RA  : 05/10 (T2) -> 11/10 (CN), 7 ngày
            (from làm tròn đầu tuần, to làm tròn cuối tuần)
        """
        days, *_ = grafana_time.resolve_days("now-1w/w", "now-1w/w", now=NOW)
        assert (days[0], days[-1], len(days)) == (
            D(2026, 10, 5),
            D(2026, 10, 11),
            7,
        )

    def test_tuan_bat_dau_chu_nhat(self):
        """
        ĐẦU VÀO: như trên nhưng week_start=6 (CN)
        ĐẦU RA: 04/10 (CN) -> 10/10 (T7)
        """
        days, *_ = grafana_time.resolve_days(
            "now-1w/w", "now-1w/w", now=NOW, week_start=6
        )
        assert (days[0], days[-1]) == (D(2026, 10, 4), D(2026, 10, 10))

    def test_hom_nay(self):
        """
        ĐẦU VÀO: from=now/d, to=now/d
        ĐẦU RA: đúng 1 ngày [16/10]
        """
        days, *_ = grafana_time.resolve_days("now/d", "now/d", now=NOW)
        assert days == [D(2026, 10, 16)]

    def test_thang_nay_va_thang_truoc(self):
        d1, *_ = grafana_time.resolve_days("now/M", "now/M", now=NOW)
        d2, *_ = grafana_time.resolve_days("now-1M/M", "now-1M/M", now=NOW)
        assert (d1[0], d1[-1], len(d1)) == (D(2026, 10, 1), D(2026, 10, 31), 31)
        assert (d2[0], d2[-1], len(d2)) == (D(2026, 9, 1), D(2026, 9, 30), 30)

    def test_epoch_ms_va_ngay_thuan(self):
        days, *_ = grafana_time.resolve_days("1790787600000", "2026-10-03")
        assert days == [D(2026, 10, 1), D(2026, 10, 2), D(2026, 10, 3)]

    def test_to_dung_00h_loai_ngay_do(self):
        days, *_ = grafana_time.resolve_days(
            "2026-09-30T17:00:00Z", "2026-10-02T17:00:00Z"
        )
        assert days == [D(2026, 10, 1), D(2026, 10, 2)]

    def test_cong_tru_ket_hop(self):
        assert grafana_time.parse_grafana_time(
            "now-1d/d+6h", now=NOW
        ) == datetime(2026, 10, 15, 6, 0, tzinfo=grafana_time.TZ)

    def test_bieu_thuc_sai(self):
        with pytest.raises(ValueError):
            grafana_time.parse_grafana_time("now-abc")
        with pytest.raises(ValueError):
            grafana_time.parse_grafana_time("hello")

    def test_to_nho_hon_from(self):
        with pytest.raises(ValueError):
            grafana_time.resolve_days("now", "now-1d", now=NOW)
