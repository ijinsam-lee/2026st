import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
import pandas as pd
import numpy as np
import altair as alt
import datetime

st.set_page_config(page_title="동적 자산배분 대시보드", layout="centered", initial_sidebar_state="collapsed")

# 프리미엄 그레이/슬레이트 톤 스타일 및 탭 선택바 강조 스타일 주입
st.markdown("""
<style>
/* 글로벌 배경화면 및 메인 톤 조정 */
.stApp {
    background-color: #f8fafc;
}

/* 상단 탭 메뉴(전략 선택 영역)를 프리미엄 그레이 세그먼트 컨트롤러로 강조 */
.stTabs [data-baseweb="tab-list"] {
    background-color: #e2e8f0 !important; /* 차분하고 정돈된 미디엄 그레이 배경 */
    border: 1px solid #cbd5e1 !important;
    border-radius: 12px !important;
    padding: 5px !important;
    gap: 4px !important;
    box-shadow: inset 0 2px 4px 0 rgba(0, 0, 0, 0.06), 0 4px 6px -1px rgba(0, 0, 0, 0.05) !important;
    margin-bottom: 20px !important;
}

/* 탭 내부 개별 버튼들을 하나의 모던한 세그먼트로 구성 */
.stTabs [data-baseweb="tab"] {
    background-color: transparent !important;
    border-radius: 8px !important;
    padding: 10px 12px !important;
    font-weight: 800 !important;
    font-size: 0.85rem !important;
    color: #475569 !important; /* 세련된 다크그레이 글자색 */
    border: none !important;
    transition: all 0.2s ease-in-out !important;
    flex: 1 !important; /* 모바일 화면에서 동일 가로비율 배분 */
    text-align: center !important;
}

/* [선택된 탭 강조] 딥 슬레이트 그레이 컬러로 압도적인 선택 상태 시인성 제공 */
.stTabs [aria-selected="true"] {
    background-color: #1e293b !important; /* 다크 슬레이트 그레이 */
    color: #ffffff !important; /* 선명한 화이트 텍스트 */
    box-shadow: 0 4px 10px -2px rgba(30, 41, 59, 0.3) !important;
}

/* 시뮬레이션 설정 상자도 품격 있는 뉴트럴 그레이 톤 플레이트로 교체 */
.control-panel {
    background-color: #f1f5f9 !important; /* 부드러운 라이트 그레이 */
    border: 1px solid #cbd5e1 !important;
    border-radius: 12px !important;
    padding: 18px !important;
    margin-bottom: 20px !important;
}
.control-header {
    color: #0f172a !important; /* 차분한 블랙 계열 */
    font-weight: 800 !important;
    font-size: 0.98rem !important;
    margin-bottom: 4px !important;
}
.control-subheader {
    color: #475569 !important; /* 짙은 회색 */
    font-size: 0.8rem !important;
    line-height: 1.45 !important;
}

/* 매크로 시황판 카드 스타일 */
.macro-card {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 10px 12px;
    margin-bottom: 8px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.02);
}
.macro-title {
    font-size: 0.78rem;
    color: #64748b;
    font-weight: 600;
    margin-bottom: 2px;
}
.macro-value {
    font-size: 1.05rem;
    font-weight: 700;
    color: #0f172a;
}
.macro-delta-up {
    font-size: 0.75rem;
    color: #dc2626;
    font-weight: 600;
}
.macro-delta-down {
    font-size: 0.75rem;
    color: #2563eb;
    font-weight: 600;
}
.macro-delta-equal {
    font-size: 0.75rem;
    color: #64748b;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)

st.title("📈 동적 자산배분 대시보드")
st.caption("야후 파이낸스 실시간 데이터 기반 수시 리밸런싱 가이드 (2026년 전략 및 실시간 미국 ETF 랭킹 포함)")

# --- 1. 자산군 정의 ---
# 전략A 자산군 (최신 리스트 12개 자산 - 문구 및 데이터 불일치 수정완료)
OFFENSIVE_A = ["QQQ", "FEZ", "GLD", "IBB", "SMH", "EEM", "XLK", "LIT", "XLE", "UBT", "XLV", "QTUM"]
DEFENSIVE_A = ["BIL", "IEF", "AGG", "HYG", "TBF"]

# 전략B 자산군 (레버리지/인버스)
OFFENSIVE_B = ["TYD", "UPRO", "VNQ"]
DEFENSIVE_B = ["DOG", "RWM", "TBF"]

# 전략C (섹터로테이션) 자산군
OFFENSIVE_C = ["FDN", "LIT", "SMH", "XLE", "IGV", "QQQM", "XLU"] # 최신섹터반영
DEFENSIVE_C = ["GLD", "PDBC", "OILK", "SHY", "TLT"] # 3대 원자재 및 채권 방어자산

# 중복 없는 전체 티커 추출 (미국 ETF 랭킹 비교용 인기 자산군 SCHD, JEPI, TQQQ, SOXL, DIA, IWM, XLF 추가)
ALL_TICKERS = list(set(["TIP", "SPY"] + OFFENSIVE_A + DEFENSIVE_A + OFFENSIVE_B + DEFENSIVE_B + OFFENSIVE_C + DEFENSIVE_C + ["SCHD", "QQQM", "IGV", "XLU", "JEPI", "TQQQ", "SOXL", "DIA", "IWM", "XLF"]))

# ============================================================
# 혼합전략 백테스트 요약 지표 (안전장치 전/후 비교표용)
# ============================================================
def summarize_bt_mix(bt):
    """혼합전략 요약: 수익/위험 지표 + 집중도(단일 자산 최대 비중), 안전장치 발동 횟수."""
    if bt is None or len(bt) == 0:
        return None
    r = bt["monthly_return"].values / 100.0
    n = len(r)
    nav = bt["nav"].values
    sd = r.std(ddof=1) if n > 1 else np.nan
    allocs = list(bt["alloc"])
    max_w = [max([w for t, w in a.items() if t != "CASH (현금)"] or [0.0]) for a in allocs]
    cash_w = [a.get("CASH (현금)", 0.0) for a in allocs]
    turn = []
    for prev, cur in zip(allocs[:-1], allocs[1:]):
        keys = set(prev) | set(cur)
        turn.append(0.5 * sum(abs(cur.get(k, 0.0) - prev.get(k, 0.0)) for k in keys))
    modes = bt["mode"].astype(str)
    return {
        "CAGR (%)": ((nav[-1] / 100.0) ** (12.0 / n) - 1) * 100,
        "MDD (%)": float(bt["drawdown"].min()),
        "연변동성 (%)": sd * np.sqrt(12) * 100 if pd.notna(sd) else np.nan,
        "샤프": (r.mean() * 12) / (sd * np.sqrt(12)) if pd.notna(sd) and sd > 0 else np.nan,
        "최악 월 (%)": float(r.min() * 100),
        "단일자산 최대비중 (%)": float(np.max(max_w)),
        "평균 현금 (%)": float(np.mean(cash_w)),
        "연 턴오버 (%)": float(np.mean(turn) * 12) if turn else 0.0,
        "Cap 발동 (월)": int(modes.str.contains("Cap적용").sum()),
        "손절 발동 (월)": int(modes.str.contains("월중손절").sum()),
        "개월 수": n,
    }

# ============================================================
# 전략 A 실시간 백테스트 엔진 (TIP 11M 이동평균 카나리아 + 공격 Top4/방어 Top1 로테이션)
# ============================================================
@st.cache_data(ttl=3600)
def get_daily_price_history_a(tickers, start="2018-01-01"):
    df = yf.download(tickers, start=start, interval="1d", progress=False, auto_adjust=True)
    if isinstance(df.columns, pd.MultiIndex):
        if "Close" in df.columns.levels[0]:
            close = df["Close"]
        else:
            close = df.iloc[:, :len(tickers)]
    else:
        close = df[["Close"]] if "Close" in df.columns else df
    if isinstance(close, pd.Series):
        close = close.to_frame(tickers[0])
    return close.dropna(how="all")

def to_monthly_last_a(df):
    return df.resample("ME").last().dropna(how="all")

def calc_momentum_a(px_series, i, months_list):
    curr = px_series.iloc[i]
    rets = {}
    for m in months_list:
        if i - m >= 0:
            past = px_series.iloc[i - m]
            rets[m] = (curr / past - 1) * 100 if pd.notna(past) and past > 0 else np.nan
        else:
            rets[m] = np.nan
    return rets

@st.cache_data(ttl=3600)
def run_backtest_strategy_a_full(monthly_px):
    records = []
    nav = 100.0
    peak = 100.0
    monthly_returns = monthly_px.pct_change().shift(-1)

    for i in range(11, len(monthly_px) - 1):
        tip_window = monthly_px["TIP"].iloc[i - 10:i + 1]  # 최근 11개월 (당월 포함)
        tip_ma11 = tip_window.mean()
        tip_curr = monthly_px["TIP"].iloc[i]
        is_attack = tip_curr > tip_ma11

        alloc = {}
        if is_attack:
            scores = []
            for t in OFFENSIVE_A:
                if t in monthly_px.columns:
                    rets = calc_momentum_a(monthly_px[t], i, [1, 3, 6, 12])
                    if not np.isnan(rets[1]) and not np.isnan(rets[12]):
                        score = (rets[1] + rets[3] + rets[6] + rets[12]) / 4
                        scores.append((t, score))
            scores.sort(key=lambda x: x[1], reverse=True)
            if scores:
                for t, _ in scores[:4]:
                    alloc[t] = 25.0
            else:
                alloc["CASH (현금)"] = 100.0
        else:
            scores = []
            for t in DEFENSIVE_A:
                if t in monthly_px.columns:
                    rets = calc_momentum_a(monthly_px[t], i, [1, 3, 6, 9, 12])
                    if not np.isnan(rets[1]) and not np.isnan(rets[12]):
                        score = (rets[1] + rets[3] + rets[6] + rets[9] + rets[12]) / 5
                        scores.append((t, score))
            if scores:
                scores.sort(key=lambda x: x[1], reverse=True)
                top1, top1_score = scores[0]
                if top1_score > 0:
                    alloc[top1] = 100.0
                else:
                    alloc["CASH (현금)"] = 100.0
            else:
                alloc["CASH (현금)"] = 100.0

        port_ret = 0.0
        for t, w in alloc.items():
            if t != "CASH (현금)":
                nxt_ret = monthly_returns[t].iloc[i]
                if pd.notna(nxt_ret):
                    port_ret += (w / 100.0) * nxt_ret

        nav *= (1 + port_ret)
        peak = max(peak, nav)
        dd = (nav / peak - 1) * 100

        records.append({
            "date": monthly_px.index[i + 1],  # 수익이 실현되는 월말 시점 기준으로 기록
            "mode": "공격 (Offensive)" if is_attack else "방어 (Defensive)",
            "nav": nav,
            "monthly_return": port_ret * 100,
            "drawdown": dd,
            "weights_str": ", ".join([f"{t} {w}%" for t, w in alloc.items() if w > 0]),
            "alloc": dict(alloc),
        })

    return pd.DataFrame(records)

# ============================================================
# 전략 B 실시간 백테스트 엔진 (TIP 1-3-6-9-12M 모멘텀 카나리아 + 레버리지 몰빵)
# ============================================================
@st.cache_data(ttl=3600)
def run_backtest_strategy_b_full(monthly_px):
    records = []
    nav = 100.0
    peak = 100.0
    monthly_returns = monthly_px.pct_change().shift(-1)

    for i in range(11, len(monthly_px) - 1):
        if "TIP" not in monthly_px.columns:
            break
        tip_rets = calc_momentum_a(monthly_px["TIP"], i, [1, 3, 6, 9, 12])
        if any(np.isnan(v) for v in tip_rets.values()):
            continue
        tip_score_b = sum(tip_rets.values()) / 5
        is_attack = tip_score_b > 0

        alloc = {}
        if is_attack:
            scores = []
            for t in OFFENSIVE_B:
                if t in monthly_px.columns:
                    rets = calc_momentum_a(monthly_px[t], i, [1, 3, 6, 12])
                    if not np.isnan(rets[12]):
                        score = (12 * rets[1] + 4 * rets[3] + 2 * rets[6] + rets[12]) / 19
                        scores.append((t, score))
            if scores:
                scores.sort(key=lambda x: x[1], reverse=True)
                alloc[scores[0][0]] = 100.0
            else:
                alloc["CASH (현금)"] = 100.0
        else:
            candidates = []
            for t in DEFENSIVE_B:
                if t in monthly_px.columns:
                    rets = calc_momentum_a(monthly_px[t], i, [1, 3, 5, 6, 9, 12])
                    if not np.isnan(rets[12]) and not np.isnan(rets[5]):
                        simple_score = (rets[1] + rets[3] + rets[6] + rets[9] + rets[12]) / 5
                        candidates.append((t, rets[5], simple_score))
            if candidates:
                candidates.sort(key=lambda x: x[1], reverse=True)
                top_t, _, top_simple_score = candidates[0]
                if top_simple_score > 0:
                    alloc[top_t] = 100.0
                else:
                    alloc["CASH (현금)"] = 100.0
            else:
                alloc["CASH (현금)"] = 100.0

        port_ret = 0.0
        for t, w in alloc.items():
            if t != "CASH (현금)":
                nxt_ret = monthly_returns[t].iloc[i]
                if pd.notna(nxt_ret):
                    port_ret += (w / 100.0) * nxt_ret

        nav *= (1 + port_ret)
        peak = max(peak, nav)
        dd = (nav / peak - 1) * 100

        records.append({
            "date": monthly_px.index[i + 1],
            "mode": "공격 (Offensive)" if is_attack else "방어 (Defensive)",
            "nav": nav,
            "monthly_return": port_ret * 100,
            "drawdown": dd,
            "weights_str": ", ".join([f"{t} {w}%" for t, w in alloc.items() if w > 0]),
            "alloc": dict(alloc),
        })

    return pd.DataFrame(records)

# ============================================================
# 전략 C 실시간 백테스트 엔진 (S&P 500 실시간 배당수익률 카나리아 + 섹터 로테이션)
# ============================================================
@st.cache_data(ttl=3600)
def get_spy_dividend_history():
    try:
        divs = yf.Ticker("SPY").dividends
        if divs.index.tz is not None:
            divs.index = divs.index.tz_localize(None)
        return divs
    except Exception:
        return pd.Series(dtype=float)

@st.cache_data(ttl=3600)
def run_backtest_strategy_c_full(monthly_px, spy_divs):
    records = []
    nav = 100.0
    peak = 100.0
    monthly_returns = monthly_px.pct_change().shift(-1)

    for i in range(11, len(monthly_px) - 1):
        if "SPY" not in monthly_px.columns:
            break
        date = monthly_px.index[i]
        window_start = date - pd.Timedelta(days=365)
        div_sum = spy_divs[(spy_divs.index > window_start) & (spy_divs.index <= date)].sum()
        spy_price = monthly_px["SPY"].iloc[i]
        if pd.isna(spy_price) or spy_price <= 0 or div_sum <= 0:
            continue
        dy = (div_sum / spy_price) * 100
        is_attack = dy > 1.33

        alloc = {}
        if is_attack:
            scores = []
            for t in OFFENSIVE_C:
                if t in monthly_px.columns:
                    rets = calc_momentum_a(monthly_px[t], i, [1, 3, 6, 12])
                    if not np.isnan(rets[12]):
                        score = (rets[1] + rets[3] + rets[6] + rets[12]) / 4
                        scores.append((t, score))
            if scores:
                scores.sort(key=lambda x: x[1], reverse=True)
                alloc[scores[0][0]] = 100.0
            else:
                alloc["CASH (현금)"] = 100.0
        else:
            scores = []
            for t in DEFENSIVE_C:
                if t in monthly_px.columns:
                    rets = calc_momentum_a(monthly_px[t], i, [1, 3, 6, 9, 12])
                    if not np.isnan(rets[12]):
                        score = (rets[1] + rets[3] + rets[6] + rets[9] + rets[12]) / 5
                        scores.append((t, score))
            if scores:
                scores.sort(key=lambda x: x[1], reverse=True)
                top_t, top_score = scores[0]
                if top_score > 0:
                    alloc[top_t] = 100.0
                else:
                    alloc["CASH (현금)"] = 100.0
            else:
                alloc["CASH (현금)"] = 100.0

        port_ret = 0.0
        for t, w in alloc.items():
            if t != "CASH (현금)":
                nxt_ret = monthly_returns[t].iloc[i]
                if pd.notna(nxt_ret):
                    port_ret += (w / 100.0) * nxt_ret

        nav *= (1 + port_ret)
        peak = max(peak, nav)
        dd = (nav / peak - 1) * 100

        records.append({
            "date": monthly_px.index[i + 1],
            "mode": "공격 (Offensive)" if is_attack else "방어 (Defensive)",
            "nav": nav,
            "monthly_return": port_ret * 100,
            "drawdown": dd,
            "weights_str": ", ".join([f"{t} {w}%" for t, w in alloc.items() if w > 0]),
            "alloc": dict(alloc),
        })

    return pd.DataFrame(records)

# ============================================================
# 2026 혼합전략 백테스트 엔진 (전략A + 전략B + 전략C 각 33.33% 동일비중 혼합)
# ============================================================
@st.cache_data(ttl=3600)
def run_backtest_strategy_mix_full(monthly_px, spy_divs):
    bt_a = run_backtest_strategy_a_full(monthly_px)
    bt_b = run_backtest_strategy_b_full(monthly_px)
    bt_c = run_backtest_strategy_c_full(monthly_px, spy_divs)

    if bt_a.empty or bt_b.empty or bt_c.empty:
        return pd.DataFrame()

    bt_a = bt_a.set_index("date")
    bt_b = bt_b.set_index("date")
    bt_c = bt_c.set_index("date")

    common_dates = sorted(set(bt_a.index) & set(bt_b.index) & set(bt_c.index))
    if not common_dates:
        return pd.DataFrame()

    records = []
    nav = 100.0
    peak = 100.0
    for d in common_dates:
        ret_a = bt_a.loc[d, "monthly_return"] / 100.0
        ret_b = bt_b.loc[d, "monthly_return"] / 100.0
        ret_c = bt_c.loc[d, "monthly_return"] / 100.0
        port_ret = (ret_a + ret_b + ret_c) / 3.0

        nav *= (1 + port_ret)
        peak = max(peak, nav)
        dd = (nav / peak - 1) * 100

        mode_a_short = bt_a.loc[d, "mode"].split(" ")[0]
        mode_b_short = bt_b.loc[d, "mode"].split(" ")[0]
        mode_c_short = bt_c.loc[d, "mode"].split(" ")[0]
        mode_str = f"A:{mode_a_short} / B:{mode_b_short} / C:{mode_c_short}"
        def _fmt_third(alloc_dict):
            # 각 전략은 전체 자산의 1/3 → 전략 내 100% = 전체 33.3%
            return ", ".join([f"{t} {w / 3.0:.1f}%" for t, w in alloc_dict.items() if w > 0.01])
        weights_str = (
            f"A[{_fmt_third(bt_a.loc[d, 'alloc'])}] + "
            f"B[{_fmt_third(bt_b.loc[d, 'alloc'])}] + "
            f"C[{_fmt_third(bt_c.loc[d, 'alloc'])}]"
        )

        # 세 전략(각 33.33%)의 종목별 비중을 하나로 합산 (턴오버 계산용)
        combined_alloc = {}
        for src_bt in (bt_a, bt_b, bt_c):
            for tkr, w in src_bt.loc[d, "alloc"].items():
                combined_alloc[tkr] = combined_alloc.get(tkr, 0.0) + (w / 100.0) * (1.0 / 3.0) * 100.0

        records.append({
            "date": d,
            "mode": mode_str,
            "nav": nav,
            "monthly_return": port_ret * 100,
            "drawdown": dd,
            "weights_str": weights_str,
            "alloc": combined_alloc,
        })

    return pd.DataFrame(records)

# ============================================================
# 2026 혼합전략 [개선판] 백테스트 엔진
#   - 2019년 5월 무역전쟁 급락(-13.0% MDD) 원인 분석 결과, 특정 자산(SMH 41.66%, UPRO 33.33% 등)에
#     3개 전략의 비중이 중복 쏠리는 현상이 최대 낙폭의 핵심 원인으로 확인되었습니다.
#   - 1단계 개선: 단일 자산군 비중 상한(Cap)
#     3개 전략(각 33.33%)을 합산했을 때 특정 티커의 최종 비중이 상한(기본 25%)을 넘으면
#     초과분을 현금(CASH)으로 자동 전환하여 강제 분산시킵니다.
#   - 2단계 개선: 월중 하드스탑(Intra-month Stop-loss)
#     일별 가격으로 월중 누적 손실을 감시하다가, 포트폴리오가 월초(전월 말 종가) 대비 임계치
#     (기본 -7%)까지 하락하면 그 시점 이후 월말까지 전량 현금화한 것으로 간주해 추가 손실을 차단합니다.
# ============================================================
@st.cache_data(ttl=3600)
def run_backtest_strategy_mix_improved_full(
    monthly_px, spy_divs, daily_px=None,
    apply_cap=False, weight_cap=25.0,
    apply_stop_loss=False, stop_loss_pct=-7.0,
):
    bt_a = run_backtest_strategy_a_full(monthly_px)
    bt_b = run_backtest_strategy_b_full(monthly_px)
    bt_c = run_backtest_strategy_c_full(monthly_px, spy_divs)

    if bt_a.empty or bt_b.empty or bt_c.empty:
        return pd.DataFrame()

    bt_a = bt_a.set_index("date")
    bt_b = bt_b.set_index("date")
    bt_c = bt_c.set_index("date")

    common_dates = sorted(set(bt_a.index) & set(bt_b.index) & set(bt_c.index))
    if not common_dates:
        return pd.DataFrame()

    monthly_returns = monthly_px.pct_change().shift(-1)
    monthly_idx = monthly_px.index
    can_stop_loss = apply_stop_loss and daily_px is not None

    records = []
    nav = 100.0
    peak = 100.0

    for d in common_dates:
        alloc_a = dict(bt_a.loc[d, "alloc"])
        alloc_b = dict(bt_b.loc[d, "alloc"])
        alloc_c = dict(bt_c.loc[d, "alloc"])

        try:
            pos = monthly_idx.get_loc(d)
        except KeyError:
            continue
        # d는 "수익이 실현되는 시점"이므로, 그 직전 월(pos-1)이 리밸런싱 결정 시점
        decision_pos = pos - 1 if pos > 0 else None
        decision_date = monthly_idx[decision_pos] if decision_pos is not None else None

        # --- 3개 전략(각 33.33%) 결합 ---
        combined_alloc = {}
        for src in (alloc_a, alloc_b, alloc_c):
            for t, w in src.items():
                combined_alloc[t] = combined_alloc.get(t, 0.0) + (w / 100.0) * (1.0 / 3.0) * 100.0

        # --- 1단계 개선 로직: 단일 자산군 비중 상한(Cap) ---
        cap_note = ""
        combined_pre_cap = dict(combined_alloc)
        excess_cash = 0.0
        if apply_cap:
            capped_alloc = {}
            excess_cash = 0.0
            for t, w in combined_alloc.items():
                if t == "CASH (현금)":
                    continue
                if w > weight_cap:
                    capped_alloc[t] = weight_cap
                    excess_cash += (w - weight_cap)
                else:
                    capped_alloc[t] = w
            capped_alloc["CASH (현금)"] = combined_alloc.get("CASH (현금)", 0.0) + excess_cash
            if excess_cash > 0.01:
                cap_note = " 📐Cap적용"
            combined_alloc = capped_alloc

        final_alloc = combined_alloc

        # --- 수익률 계산 (기본: 월간 수익률) ---
        port_ret = 0.0
        if decision_pos is not None:
            for t, w in final_alloc.items():
                if t != "CASH (현금)" and t in monthly_returns.columns:
                    r = monthly_returns[t].iloc[decision_pos]
                    if pd.notna(r):
                        port_ret += (w / 100.0) * r

        # --- 2단계 개선 로직: 월중 하드스탑 (일별 가격으로 월중 낙폭 감시) ---
        stop_note = ""
        if can_stop_loss and decision_date is not None:
            tickers_held = [t for t in final_alloc if t != "CASH (현금)" and final_alloc[t] > 0.01 and t in daily_px.columns]
            day_mask = (daily_px.index > decision_date) & (daily_px.index <= d)
            day_slice = daily_px.loc[day_mask]
            prior_prices_df = daily_px.loc[:decision_date]

            if len(day_slice) > 0 and tickers_held and len(prior_prices_df) > 0:
                start_prices = prior_prices_df.iloc[-1]
                cum_val = pd.Series(0.0, index=day_slice.index)
                for t in tickers_held:
                    w = final_alloc[t] / 100.0
                    if pd.isna(start_prices[t]) or start_prices[t] == 0:
                        continue
                    t_ret = day_slice[t] / start_prices[t] - 1.0
                    cum_val = cum_val + (t_ret.fillna(0.0) * w)

                stop_triggered = cum_val[cum_val * 100.0 <= stop_loss_pct]
                if len(stop_triggered) > 0:
                    port_ret = stop_triggered.iloc[0]
                    stop_note = " 🛑월중손절"
                elif len(cum_val) > 0:
                    port_ret = cum_val.iloc[-1]  # 일별 경로 기준 최종 수익률 (월간 수익률과 근사적으로 일치)

        nav *= (1 + port_ret)
        peak = max(peak, nav)
        dd = (nav / peak - 1) * 100

        mode_a_short = bt_a.loc[d, "mode"].split(" ")[0]
        mode_b_short = bt_b.loc[d, "mode"].split(" ")[0]
        mode_c_short = bt_c.loc[d, "mode"].split(" ")[0]
        mode_str = f"A:{mode_a_short} / B:{mode_b_short} / C:{mode_c_short}{cap_note}{stop_note}"
        def _fmt_part(src_alloc):
            # 각 전략은 전체 자산의 1/3 (상한 적용 시 해당 티커 비중만큼 비례 축소)
            items = []
            for t, w in src_alloc.items():
                base = w / 3.0
                if apply_cap and t != "CASH (현금)" and combined_pre_cap.get(t, 0.0) > 0:
                    base *= final_alloc.get(t, 0.0) / combined_pre_cap[t]
                if base > 0.01:
                    items.append(f"{t} {base:.1f}%")
            return ", ".join(items)
        weights_str = f"A[{_fmt_part(alloc_a)}] + B[{_fmt_part(alloc_b)}] + C[{_fmt_part(alloc_c)}]"
        if apply_cap and excess_cash > 0.01:
            weights_str += f" + 상한초과분[CASH (현금) {excess_cash:.1f}%]"

        records.append({
            "date": d,
            "mode": mode_str,
            "nav": nav,
            "monthly_return": port_ret * 100,
            "drawdown": dd,
            "weights_str": weights_str,
            "alloc": dict(final_alloc),
        })

    return pd.DataFrame(records)

# 관심매크로 지표 정의 및 심볼 매핑 (미국 30년물 국채 금리 추가)
MACRO_TICKERS = {
    "미국 10년물 국채 금리": "^TNX",
    "미국 30년물 국채 금리": "^TYX",
    "달러/원": "USDKRW=X",
    "WTI유": "CL=F",
    "미국 물가연동채권": "TIP",
    "미국 달러 지수": "DX-Y.NYB",
    "달러/엔": "USDJPY=X",
    "CBOE VIX": "^VIX",
}

@st.cache_data(ttl=60) # 시황 데이터는 1분 단위 캐싱
def get_macro_market_pulse():
    macro_data = []
    for name, symbol in MACRO_TICKERS.items():
        price_val = "-"
        delta_val = "0.00"
        delta_pct_val = "0.00%"
        raw_delta_val = 0.0
        
        try:
            ticker = yf.Ticker(symbol)
            # 주말 데이터 대응을 위해 넉넉히 5일 데이터를 조회
            hist = ticker.history(period="5d")
            if not hist.empty and 'Close' in hist.columns and len(hist) >= 1:
                closes = hist['Close'].dropna()
                if len(closes) >= 1:
                    current_price = closes.iloc[-1]
                    prev_price = closes.iloc[-2] if len(closes) >= 2 else current_price
                    delta = current_price - prev_price
                    delta_pct = (delta / prev_price) * 100 if prev_price > 0 else 0.0
                    
                    if symbol in ["^TNX", "^TYX"]:
                        price_val = f"{current_price:.3f}%"
                        delta_val = f"{delta:+.3f}"
                    elif "KRW=X" in symbol:
                        price_val = f"{current_price:,.2f}원"
                        delta_val = f"{delta:+.2f}"
                    elif "=X" in symbol:
                        price_val = f"{current_price:,.4f}"
                        delta_val = f"{delta:+.4f}"
                    else:
                        price_val = f"{current_price:,.2f}"
                        delta_val = f"{delta:+.2f}"
                    
                    delta_pct_val = f"{delta_pct:+.2f}%"
                    raw_delta_val = delta
        except Exception:
            pass
        
        macro_data.append({
            "name": name,
            "symbol": symbol,
            "price": price_val,
            "delta": delta_val,
            "delta_pct": delta_pct_val,
            "raw_delta": raw_delta_val
        })
    return macro_data

with st.spinner("관심 시황판 실시간 매크로 지표 동기화 중..."):
    macro_pulse = get_macro_market_pulse()

with st.expander("🌍 실시간 글로벌 매크로 시황판", expanded=True):
    cols = st.columns(4)
    for idx, item in enumerate(macro_pulse):
        col_to_use = cols[idx % 4]
        delta_class = "macro-delta-equal"
        if item["raw_delta"] > 0:
            delta_class = "macro-delta-up"
        elif item["raw_delta"] < 0:
            delta_class = "macro-delta-down"
        
        col_to_use.markdown(f"""
        <div class="macro-card">
            <div class="macro-title">{item['name']} <small style='color:#94a3b8; font-size:0.65rem;'>{item['symbol']}</small></div>
            <div class="macro-value">{item['price']}</div>
            <div class="{delta_class}">{item['delta']} ({item['delta_pct']})</div>
        </div>
        """, unsafe_allow_html=True)

def get_usd_krw_rate():
    try:
        usd_krw = yf.Ticker("USDKRW=X")
        hist = usd_krw.history(period="5d")
        if not hist.empty and 'Close' in hist.columns:
            closes = hist['Close'].dropna()
            if len(closes) >= 1:
                return float(closes.iloc[-1])
    except Exception:
        pass
    return 1380.0 # 기본 백업 환율

# 배당 히스토리 직접 계산을 1순위 기본으로 사용 (yfinance API 변동에 따른 엣지케이스 완전 방지)
def get_sp500_dividend_yield():
    try:
        spy = yf.Ticker("SPY")
        
        # 1. 배당 히스토리 기반 직접 계산 (Primary)
        divs = spy.dividends
        if not divs.empty:
            utc_tz = divs.index.tz
            end_dt = pd.Timestamp.now(tz=utc_tz)
            start_dt = end_dt - pd.Timedelta(days=365)
            last_year_divs = divs.loc[start_dt:end_dt]
            sum_divs = last_year_divs.sum()
            
            hist = spy.history(period="1mo")
            if not hist.empty and 'Close' in hist.columns:
                closes = hist['Close'].dropna()
                if len(closes) >= 1:
                    curr_price = float(closes.iloc[-1])
                    if curr_price > 0:
                        return (sum_divs / curr_price) * 100

        # 2. .info 필드 보조 사용 (Fallback)
        dy = spy.info.get('dividendYield')
        if dy is not None:
            dy_val = float(dy)
            if dy_val < 0.15:
                return dy_val * 100
            return dy_val
    except Exception:
        pass
    return 1.32 # 기본값 백업

@st.cache_data(ttl=3600) 
def get_all_financial_data_v2(tickers):
    data_list = []
    now = datetime.datetime.now()
    start_date = (now - datetime.timedelta(days=450)).strftime('%Y-%m-%d')
    
    try:
        # 배치(Batch) 다운로드 방식으로 성능 극대화
        df_download = yf.download(tickers, start=start_date, interval="1mo", progress=False, auto_adjust=True)
        if 'Close' in df_download.columns:
            closes_df = df_download['Close']
        else:
            closes_df = df_download
            
        for ticker in tickers:
            try:
                if isinstance(closes_df, pd.DataFrame) and ticker in closes_df.columns:
                    closes = closes_df[ticker].dropna()
                elif isinstance(closes_df, pd.Series):
                    closes = closes_df.dropna()
                else:
                    continue
                    
                if len(closes) < 12:
                    continue
                
                # 가장 최근 종가 및 과거 종가 추출
                current_price = float(closes.iloc[-1])
                p1 = float(closes.iloc[-2]) if len(closes) >= 2 else current_price
                p3 = float(closes.iloc[-4]) if len(closes) >= 4 else current_price
                p5 = float(closes.iloc[-6]) if len(closes) >= 6 else current_price # 전략B/C 방어용 5개월 가격
                p6 = float(closes.iloc[-7]) if len(closes) >= 7 else current_price
                p9 = float(closes.iloc[-10]) if len(closes) >= 10 else current_price
                p12 = float(closes.iloc[-13]) if len(closes) >= 13 else float(closes.iloc[0])
                
                # 수익률 계산 (%)
                r1 = ((current_price - p1) / p1) * 100
                r3 = ((current_price - p3) / p3) * 100
                r5 = ((current_price - p5) / p5) * 100
                r6 = ((current_price - p6) / p6) * 100
                r9 = ((current_price - p9) / p9) * 100
                r12 = ((current_price - p12) / p12) * 100
                
                # 전략 A / C 공격용 스코어 계산 (1, 3, 6, 12 단순평균)
                score_a_off = (r1 + r3 + r6 + r12) / 4
                
                # 전략 A / C 방어용 스코어 계산 (1, 3, 6, 9, 12 단순평균)
                score_a_def = (r1 + r3 + r6 + r9 + r12) / 5
                
                # 전략 B용 스코어 계산 (가중평균 및 단순평균)
                score_b_off = (r1 * 12 + r3 * 4 + r6 * 2 + r12 * 1) / 19
                score_b_def_simple = (r1 + r3 + r6 + r9 + r12) / 5 # 전략B 방어자산 단순 모멘텀
                
                data_list.append({
                    "Ticker": ticker,
                    "현재가": round(current_price, 2),
                    "1M": round(r1, 1), 
                    "3M": round(r3, 1), 
                    "5M": round(r5, 1),
                    "6M": round(r6, 1), 
                    "9M": round(r9, 1), 
                    "12M": round(r12, 1),
                    "A_공격스코어": round(score_a_off, 2),
                    "A_방어스코어": round(score_a_def, 2),
                    "B_공격스코어": round(score_b_off, 2),
                    "B_단순모멘텀": round(score_b_def_simple, 2),
                    "raw_closes": closes.tolist()
                })
            except Exception:
                pass
    except Exception as e:
        st.error(f"금융 데이터 다운로드 중 오류 발생: {e}")
    
    return pd.DataFrame(data_list)

@st.cache_data(ttl=3600)
def get_historical_simulation_data(tickers):
    prices_dict = {}
    now = datetime.datetime.now()
    start_date = (now - datetime.timedelta(days=800)).strftime('%Y-%m-%d')
    
    try:
        df_download = yf.download(tickers, start=start_date, interval="1d", progress=False, auto_adjust=True)
        if 'Close' in df_download.columns:
            closes_df = df_download['Close']
        else:
            closes_df = df_download
            
        for ticker in tickers:
            if isinstance(closes_df, pd.DataFrame) and ticker in closes_df.columns:
                series = closes_df[ticker].dropna()
                if not series.empty:
                    prices_dict[ticker] = series
            elif isinstance(closes_df, pd.Series):
                series = closes_df.dropna()
                if not series.empty:
                    prices_dict[ticker] = series
    except Exception:
        pass
    
    spy_divs = pd.Series(dtype=float)
    try:
        spy_divs = yf.Ticker("SPY").dividends
    except Exception:
        pass
    
    return prices_dict, spy_divs

def compute_historical_portfolio_at_month_end(prices_dict, spy_divs, target_date, OFFENSIVE_A, DEFENSIVE_A, OFFENSIVE_B, DEFENSIVE_B, OFFENSIVE_C, DEFENSIVE_C):
    monthly_prices = {}
    for t, series in prices_dict.items():
        sub_series = series[series.index <= target_date]
        if sub_series.empty:
            continue
        
        df = sub_series.to_frame()
        df['year'] = df.index.year
        df['month'] = df.index.month
        last_idx = df.groupby(['year', 'month']).apply(lambda x: x.index[-1])
        m_closes = sub_series.loc[last_idx].tolist()
        
        if len(m_closes) < 13:
            continue
        monthly_prices[t] = m_closes

    if "TIP" not in monthly_prices or "SPY" not in monthly_prices:
        return {"CASH (현금)": 100.0}, False, False, False, 1.32

    def calc_momentum_and_scores(m_closes):
        curr = m_closes[-1]
        p1 = m_closes[-2] if len(m_closes) >= 2 else curr
        p3 = m_closes[-4] if len(m_closes) >= 4 else curr
        p5 = m_closes[-6] if len(m_closes) >= 6 else curr
        p6 = m_closes[-7] if len(m_closes) >= 7 else curr
        p9 = m_closes[-10] if len(m_closes) >= 10 else curr
        p12 = m_closes[-13] if len(m_closes) >= 13 else m_closes[0]

        r1 = ((curr - p1) / p1) * 100
        r3 = ((curr - p3) / p3) * 100
        r5 = ((curr - p5) / p5) * 100
        r6 = ((curr - p6) / p6) * 100
        r9 = ((curr - p9) / p9) * 100
        r12 = ((curr - p12) / p12) * 100

        score_a_off = (r1 + r3 + r6 + r12) / 4
        score_a_def = (r1 + r3 + r6 + r9 + r12) / 5
        score_b_off = (r1 * 12 + r3 * 4 + r6 * 2 + r12 * 1) / 19
        score_b_def_simple = (r1 + r3 + r6 + r9 + r12) / 5

        return {
            "curr": curr,
            "r1": r1, "r3": r3, "r5": r5, "r6": r6, "r9": r9, "r12": r12,
            "A_공격스코어": score_a_off,
            "A_방어스코어": score_a_def,
            "B_공격스코어": score_b_off,
            "B_단순모멘텀": score_b_def_simple
        }

    ticker_metrics = {}
    for t, m_closes in monthly_prices.items():
        ticker_metrics[t] = calc_momentum_and_scores(m_closes)

    # 1. 전략 A 배분
    tip_closes = monthly_prices["TIP"]
    tip_current = tip_closes[-1]
    tip_last11 = tip_closes[-11:]
    tip_ma11 = sum(tip_last11) / len(tip_last11)
    is_attack_a_hist = tip_current > tip_ma11

    alloc_a_hist = {}
    if is_attack_a_hist:
        off_scores = []
        for t in OFFENSIVE_A:
            if t in ticker_metrics:
                off_scores.append((t, ticker_metrics[t]["A_공격스코어"]))
        if off_scores:
            off_scores.sort(key=lambda x: x[1], reverse=True)
            for t, _ in off_scores[:4]:
                alloc_a_hist[t] = 25.0
        else:
            alloc_a_hist["CASH (현금)"] = 100.0
    else:
        def_scores = []
        for t in DEFENSIVE_A:
            if t in ticker_metrics:
                def_scores.append((t, ticker_metrics[t]["A_방어스코어"]))
        if def_scores:
            def_scores.sort(key=lambda x: x[1], reverse=True)
            top_1 = def_scores[0]
            if top_1[1] > 0:
                alloc_a_hist[top_1[0]] = 100.0
            else:
                alloc_a_hist["CASH (현금)"] = 100.0
        else:
            alloc_a_hist["CASH (현금)"] = 100.0

    # 2. 전략 B 배분
    tip_metrics = ticker_metrics["TIP"]
    tip_score_b_hist = (tip_metrics["r1"] + tip_metrics["r3"] + tip_metrics["r6"] + tip_metrics["r9"] + tip_metrics["r12"]) / 5
    is_attack_b_hist = tip_score_b_hist > 0

    alloc_b_hist = {}
    if is_attack_b_hist:
        off_scores = []
        for t in OFFENSIVE_B:
            if t in ticker_metrics:
                off_scores.append((t, ticker_metrics[t]["B_공격스코어"]))
        if off_scores:
            off_scores.sort(key=lambda x: x[1], reverse=True)
            alloc_b_hist[off_scores[0][0]] = 100.0
        else:
            alloc_b_hist["CASH (현금)"] = 100.0
    else:
        def_scores = []
        for t in DEFENSIVE_B:
            if t in ticker_metrics:
                def_scores.append((t, ticker_metrics[t]["r5"], ticker_metrics[t]["B_단순모멘텀"]))
        if def_scores:
            def_scores.sort(key=lambda x: x[1], reverse=True)
            top_1 = def_scores[0]
            if top_1[2] > 0:
                alloc_b_hist[top_1[0]] = 100.0
            else:
                alloc_b_hist["CASH (현금)"] = 100.0
        else:
            alloc_b_hist["CASH (현금)"] = 100.0

    # 3. 전략 C 배분 (이중 스케일링 버그 수정 완료)
    dy_val = 1.32
    if not spy_divs.empty:
        target_date_naive = target_date.tz_localize(None) if target_date.tz is not None else target_date
        start_dt = target_date_naive - pd.Timedelta(days=365)
        
        spy_divs_naive = spy_divs.copy()
        if spy_divs_naive.index.tz is not None:
            spy_divs_naive.index = spy_divs_naive.index.tz_localize(None)
        
        divs_in_range = spy_divs_naive.loc[start_dt:target_date_naive]
        sum_divs = divs_in_range.sum()
        
        spy_price = ticker_metrics.get("SPY", {}).get("curr", None)
        if spy_price and spy_price > 0:
            dy_val = float((sum_divs / spy_price) * 100)
        
    is_attack_c_hist = dy_val > 1.33

    alloc_c_hist = {}
    if is_attack_c_hist:
        off_scores = []
        for t in OFFENSIVE_C:
            if t in ticker_metrics:
                off_scores.append((t, ticker_metrics[t]["A_공격스코어"]))
        if off_scores:
            off_scores.sort(key=lambda x: x[1], reverse=True)
            alloc_c_hist[off_scores[0][0]] = 100.0
        else:
            alloc_c_hist["CASH (현금)"] = 100.0
    else:
        def_scores = []
        for t in DEFENSIVE_C:
            if t in ticker_metrics:
                def_scores.append((t, ticker_metrics[t]["A_방어스코어"]))
        if def_scores:
            def_scores.sort(key=lambda x: x[1], reverse=True)
            top_1 = def_scores[0]
            if top_1[1] > 0:
                alloc_c_hist[top_1[0]] = 100.0
            else:
                alloc_c_hist["CASH (현금)"] = 100.0
        else:
            alloc_c_hist["CASH (현금)"] = 100.0

    # 혼합 포트폴리오 비중 병합
    mixed_portfolio = {}
    for t, w in alloc_a_hist.items():
        mixed_portfolio[t] = mixed_portfolio.get(t, 0.0) + (w / 100.0) * 33.333
    for t, w in alloc_b_hist.items():
        mixed_portfolio[t] = mixed_portfolio.get(t, 0.0) + (w / 100.0) * 33.333
    for t, w in alloc_c_hist.items():
        mixed_portfolio[t] = mixed_portfolio.get(t, 0.0) + (w / 100.0) * 33.333

    clean_portfolio = {t: round(w, 2) for t, w in mixed_portfolio.items() if w > 0.01}
    return clean_portfolio, is_attack_a_hist, is_attack_b_hist, is_attack_c_hist, dy_val

with st.spinner("야후 파이낸스 실시간 데이터를 통합 집계 중..."):
    df_all = get_all_financial_data_v2(ALL_TICKERS)

if df_all.empty or "TIP" not in df_all["Ticker"].values:
    st.error("핵심 데이터 로딩에 실패했습니다. 페이지를 새로고침해 주세요.")
else:
    data_dict = df_all.set_index("Ticker").to_dict(orient="index")
    
    with st.spinner("지난 12개월(최근 1년) 월말 포트폴리오 데이터를 로딩 및 역동 연산 중..."):
        hist_prices, spy_divs_hist = get_historical_simulation_data(ALL_TICKERS)
    
    # TIP 데이터 추출
    tip_data = data_dict.get("TIP", {})
    tip_closes = tip_data.get("raw_closes", [])
    tip_current = tip_data.get("현재가", 0.0)
    
    # 최근 11개 월간 종가 평균 계산
    tip_last11 = tip_closes[-11:] if len(tip_closes) >= 11 else tip_closes
    tip_ma11 = sum(tip_last11) / len(tip_last11) if tip_last11 else 1.0
    tip_ratio = tip_current / tip_ma11 if tip_ma11 > 0 else 1.0
    is_attack_a = tip_ratio > 1.0

    # 전략 B 카나리아 신호 계산
    tip_score_b = (tip_data.get("1M", 0.0) + tip_data.get("3M", 0.0) + tip_data.get("6M", 0.0) + tip_data.get("9M", 0.0) + tip_data.get("12M", 0.0)) / 5
    is_attack_b = tip_score_b > 0

    # S&P 500 실시간 배당수익률 산출 및 시그널 매핑
    realtime_dy = get_sp500_dividend_yield()
    is_attack_c = realtime_dy > 1.33
    
    tab_2026, tab_a, tab_b, tab_c, tab_rank, tab_calc = st.tabs([
        "🏆 2026 혼합전략", 
        "🛡️ 전략 A", 
        "⚡ 전략 B", 
        "🔄 전략 C",
        "🇺🇸 미국 ETF 랭킹",
        "🧮 자산 계산기"
    ])


    # 스크롤해도 전략 탭 메뉴(혼합전략/A/B/C/ETF 랭킹/자산 계산기)가 화면 상단에 고정되도록 함
    components.html("""
<script>
(function () {
  var win = window.parent, doc = win.document;
  if (win.__tabStickyTimer) { win.clearInterval(win.__tabStickyTimer); }
  var PROPS = ['position', 'top', 'left', 'width', 'z-index', 'box-shadow', 'box-sizing', 'background-color', 'padding-top', 'padding-bottom'];
  function headerH() {
    var h = doc.querySelector('[data-testid="stHeader"]');
    return h ? h.getBoundingClientRect().height : 0;
  }
  function update() {
    var tl = doc.querySelector('.stTabs [role="tablist"]') || doc.querySelector('[role="tablist"]') || doc.querySelector('[data-baseweb="tab-list"]');
    if (!tl || !tl.parentNode) { return; }
    var ph = doc.getElementById('tab-sticky-ph');
    if (!ph || !ph.isConnected || ph.nextSibling !== tl) {
      if (ph) { ph.remove(); }
      ph = doc.createElement('div');
      ph.id = 'tab-sticky-ph';
      tl.parentNode.insertBefore(ph, tl);
    }
    var top = headerH();
    var r = ph.getBoundingClientRect();
    if (r.top <= top) {
      ph.style.height = (tl.offsetHeight + 20) + 'px';
      tl.style.setProperty('position', 'fixed', 'important');
      tl.style.setProperty('top', top + 'px', 'important');
      tl.style.setProperty('left', r.left + 'px', 'important');
      tl.style.setProperty('width', r.width + 'px', 'important');
      tl.style.setProperty('box-sizing', 'border-box', 'important');
      tl.style.setProperty('background-color', '#f8fafc', 'important');
      tl.style.setProperty('padding-top', '6px', 'important');
      tl.style.setProperty('padding-bottom', '2px', 'important');
      tl.style.setProperty('z-index', '999', 'important');
      tl.style.setProperty('box-shadow', '0 6px 14px -4px rgba(15,23,42,0.35)', 'important');
    } else {
      ph.style.height = '0px';
      PROPS.forEach(function (p) { tl.style.removeProperty(p); });
    }
  }
  win.__tabStickyTimer = win.setInterval(update, 100);
  update();
})();
</script>
""", height=0)

    with tab_2026:
        c_2026 = st.container()
    with tab_a:
        c_a = st.container()
    with tab_b:
        c_b = st.container()
    with tab_c:
        c_c = st.container()
    with tab_rank:
        c_rank = st.container()
    with tab_calc:
        c_calc = st.container()

    # [전략 A 할당 산출]
    alloc_a = {}
    if is_attack_a:
        df_off_a = df_all[df_all["Ticker"].isin(OFFENSIVE_A)].copy()
        if not df_off_a.empty:
            df_off_a = df_off_a.sort_values(by="A_공격스코어", ascending=False)
            top_4_a = df_off_a.head(4)
            for _, r in top_4_a.iterrows():
                alloc_a[r["Ticker"]] = 25.0
        else:
            alloc_a["CASH (현금)"] = 100.0
    else:
        df_def_a = df_all[df_all["Ticker"].isin(DEFENSIVE_A)].copy()
        if not df_def_a.empty:
            df_def_a = df_def_a.sort_values(by="A_방어스코어", ascending=False)
            top_1_a = df_def_a.iloc[0]
            if top_1_a["A_방어스코어"] > 0:
                alloc_a[top_1_a["Ticker"]] = 100.0
            else:
                alloc_a["CASH (현금)"] = 100.0
        else:
            alloc_a["CASH (현금)"] = 100.0

    # [전략 B 할당 산출]
    alloc_b = {}
    if is_attack_b:
        df_off_b = df_all[df_all["Ticker"].isin(OFFENSIVE_B)].copy()
        if not df_off_b.empty:
            df_off_b = df_off_b.sort_values(by="B_공격스코어", ascending=False)
            top_1_b = df_off_b.iloc[0]
            alloc_b[top_1_b["Ticker"]] = 100.0
        else:
            alloc_b["CASH (현금)"] = 100.0
    else:
        df_def_b = df_all[df_all["Ticker"].isin(DEFENSIVE_B)].copy()
        if not df_def_b.empty:
            df_def_b = df_def_b.sort_values(by="5M", ascending=False)
            top_1_b_def = df_def_b.iloc[0]
            if top_1_b_def["B_단순모멘텀"] > 0:
                alloc_b[top_1_b_def["Ticker"]] = 100.0
            else:
                alloc_b["CASH (현금)"] = 100.0
        else:
            alloc_b["CASH (현금)"] = 100.0

    # [전략 C 할당 산출]
    alloc_c = {}
    if is_attack_c:
        df_off_c = df_all[df_all["Ticker"].isin(OFFENSIVE_C)].copy()
        if not df_off_c.empty:
            df_off_c = df_off_c.sort_values(by="A_공격스코어", ascending=False)
            top_1_c = df_off_c.iloc[0]
            alloc_c[top_1_c["Ticker"]] = 100.0
        else:
            alloc_c["CASH (현금)"] = 100.0
    else:
        df_def_c = df_all[df_all["Ticker"].isin(DEFENSIVE_C)].copy()
        if not df_def_c.empty:
            df_def_c = df_def_c.sort_values(by="A_방어스코어", ascending=False)
            top_1_c_def = df_def_c.iloc[0]
            if top_1_c_def["A_방어스코어"] > 0:
                alloc_c[top_1_c_def["Ticker"]] = 100.0
            else:
                alloc_c["CASH (현금)"] = 100.0
        else:
            alloc_c["CASH (현금)"] = 100.0

    combined_alloc = {}
    contributions = {}

    def add_to_combined(alloc_dict, strategy_weight, strategy_name, mode_status):
        for ticker, asset_weight in alloc_dict.items():
            effective_weight = (asset_weight / 100.0) * strategy_weight
            combined_alloc[ticker] = combined_alloc.get(ticker, 0.0) + effective_weight
            
            if ticker not in contributions:
                contributions[ticker] = []
            contributions[ticker].append(f"{strategy_name} ({mode_status})")

    sig_a = "공격" if is_attack_a else "방어"
    sig_b = "공격" if is_attack_b else "방어"
    sig_c = "공격" if is_attack_c else "방어"

    add_to_combined(alloc_a, 33.333, "전략 A", sig_a)
    add_to_combined(alloc_b, 33.333, "전략 B", sig_b)
    add_to_combined(alloc_c, 33.333, "전략 C", sig_c)

    mix_data = []
    for ticker, weight in combined_alloc.items():
        if weight > 0.01:
            price = data_dict.get(ticker, {}).get("현재가", 1.0) if ticker != "CASH (현금)" else 1.0
            mix_data.append({
                "자산군 (Ticker)": ticker,
                "현재가 ($)": f"${price:.2f}" if ticker != "CASH (현금)" else "-",
                "배분 비중 (%)": round(weight, 2),
                "선택 근거 (참여 전략)": " + ".join(contributions[ticker])
            })
    df_mix = pd.DataFrame(mix_data).sort_values(by="배분 비중 (%)", ascending=False)

    # [선택 근거 상세] 각 전략이 어떤 기준·값으로 자산을 골랐는지 정리 (표시 전용, 배분 계산에는 영향 없음)
    basis_notes = {}

    def _note(ticker, text):
        basis_notes.setdefault(ticker, []).append(text)

    def _top_rows(tickers, col, n=1):
        return df_all[df_all["Ticker"].isin(tickers)].sort_values(by=col, ascending=False).head(n)

    # 전략 A
    if is_attack_a:
        for _rank, (_, _r) in enumerate(_top_rows(OFFENSIVE_A, "A_공격스코어", 4).iterrows(), start=1):
            _note(_r["Ticker"], f"A·공격: 공격스코어 {_rank}위 ({_r['A_공격스코어']:+.2f}%)")
    else:
        _d = _top_rows(DEFENSIVE_A, "A_방어스코어", 1)
        if not _d.empty:
            _r = _d.iloc[0]
            if _r["A_방어스코어"] > 0:
                _note(_r["Ticker"], f"A·방어: 방어스코어 1위 ({_r['A_방어스코어']:+.2f}%)")
            else:
                _note("CASH (현금)", f"A·방어: 1위 {_r['Ticker']} 방어스코어 {_r['A_방어스코어']:+.2f}% ≤ 0 → 현금")
    # 전략 B
    if is_attack_b:
        _d = _top_rows(OFFENSIVE_B, "B_공격스코어", 1)
        if not _d.empty:
            _r = _d.iloc[0]
            _note(_r["Ticker"], f"B·공격: 가중모멘텀 1위 ({_r['B_공격스코어']:+.2f}%)")
    else:
        _d = _top_rows(DEFENSIVE_B, "5M", 1)
        if not _d.empty:
            _r = _d.iloc[0]
            if _r["B_단순모멘텀"] > 0:
                _note(_r["Ticker"], f"B·방어: 5개월 수익률 1위 ({_r['5M']:+.1f}%, 단순모멘텀 {_r['B_단순모멘텀']:+.2f}%)")
            else:
                _note("CASH (현금)", f"B·방어: 5개월 1위 {_r['Ticker']} 단순모멘텀 {_r['B_단순모멘텀']:+.2f}% ≤ 0 → 현금")
    # 전략 C
    if is_attack_c:
        _d = _top_rows(OFFENSIVE_C, "A_공격스코어", 1)
        if not _d.empty:
            _r = _d.iloc[0]
            _note(_r["Ticker"], f"C·공격: 공격스코어 1위 ({_r['A_공격스코어']:+.2f}%)")
    else:
        _d = _top_rows(DEFENSIVE_C, "A_방어스코어", 1)
        if not _d.empty:
            _r = _d.iloc[0]
            if _r["A_방어스코어"] > 0:
                _note(_r["Ticker"], f"C·방어: 방어스코어 1위 ({_r['A_방어스코어']:+.2f}%)")
            else:
                _note("CASH (현금)", f"C·방어: 1위 {_r['Ticker']} 방어스코어 {_r['A_방어스코어']:+.2f}% ≤ 0 → 현금")

    def _ret_txt(ticker, col):
        v = data_dict.get(ticker, {}).get(col)
        return f"{v:+.1f}%" if v is not None and ticker != "CASH (현금)" else "-"

    df_mix_view = pd.DataFrame({
        "자산군": df_mix["자산군 (Ticker)"].values,
        "현재가 ($)": df_mix["현재가 ($)"].values,
        "배분 비중 (%)": df_mix["배분 비중 (%)"].values,
        "참여 전략 (신호)": df_mix["선택 근거 (참여 전략)"].values,
        "선택 기준 · 값": [" | ".join(basis_notes.get(t, ["-"])) for t in df_mix["자산군 (Ticker)"]],
        "1M": [_ret_txt(t, "1M") for t in df_mix["자산군 (Ticker)"]],
        "3M": [_ret_txt(t, "3M") for t in df_mix["자산군 (Ticker)"]],
        "6M": [_ret_txt(t, "6M") for t in df_mix["자산군 (Ticker)"]],
        "12M": [_ret_txt(t, "12M") for t in df_mix["자산군 (Ticker)"]],
    })

    with c_2026:
        st.header("🏆 2026년 혼합 전략")
        st.markdown(
            "안정 지향의 **전략 A**, 고수익 레버리지의 **전략 B**, 시황 로테이션인 **전략 C**를 "
            "각각 **$33.33\\%$씩 동일 비중**으로 혼합하여 시장 전반의 변동성을 완벽하게 제어하는 2026년 추천 전략 모델입니다."
        )

        with st.expander("📖 2026 동적 자산배분 혼합 전략 명세서 (작동원칙)", expanded=False):
            st.markdown("""
            ### 🎯 혼합전략 개요
            본 전략은 시장의 거시경제 지표와 자산별 모멘텀을 실시간으로 추적하여 작동합니다. 성격이 서로 다른
            3가지 동적 자산배분 전략(안정형, 공격형, 섹터로테이션)을 각각 **33.33%의 동일 비중**으로 혼합하여
            극대화된 안정성과 풍부한 수익성의 균형을 달성하는 것을 목표로 합니다.

            ---
            #### 🛡️ 전략 A: 대형 우량 자산 안정형 (배분 비중 33.33%)
            물가연동채(TIP)를 통해 거시경제 국면을 판독하고, 대형 우량 자산 중심의 안정 투자를 지향합니다.
            * **카나리아**: TIP 현재가 vs 11개월 이동평균(11MA) — 현재가 > 11MA면 공격, 이하면 방어
            * **공격 자산군 (12개)**: `QQQ, FEZ, GLD, IBB, SMH, EEM, XLK, LIT, XLE, UBT, XLV, QTUM`
            * **방어 자산군 (5개)**: `BIL, IEF, AGG, HYG, TBF`
            * **운용 가이드**: 공격 시 1·3·6·12개월 단순평균 모멘텀 상위 4종목에 각 25%씩 균등 분배. 방어 시 1·3·6·9·12개월 단순평균 모멘텀 1위 자산에 100% 투자하되, 그 스코어마저 0 이하면 현금 100%로 대피.

            #### ⚡ 전략 B: 레버리지 공격형 (배분 비중 33.33%)
            채권 실질금리 모멘텀의 급격한 변화를 바탕으로 3배 레버리지 자산에 초집중 투자합니다.
            * **카나리아**: TIP의 1·3·6·9·12개월 단순평균 모멘텀 — 양수(> 0)면 공격, 이하면 방어
            * **공격 자산군 (3개)**: `TYD(미국채 3X), UPRO(S&P500 3X), VNQ(리츠)`
            * **방어 자산군 (3개)**: `DOG(다우 인버스), RWM(러셀 인버스), TBF(미국채 장기 인버스)`
            * **운용 가이드**: 공격 시 가중평균 모멘텀 1위 자산에 100% 몰빵. 방어 시 최근 5개월 단순 수익률 1위 자산에 투자하되, 해당 자산 자체의 단순평균 모멘텀이 음수면 현금 100%로 피신.

            #### 🔄 전략 C: 배당 기반 섹터 로테이션 (배분 비중 33.33%)
            S&P 500의 실시간 배당수익률을 기반으로 주식 저평가/과열 국면을 판독합니다.
            * **카나리아**: SPY 실시간 배당수익률 — 1.33% 초과면 공격, 이하면 방어
            * **공격 자산군 (7개)**: `FDN, LIT, SMH, XLE, IGV, QQQM, XLU`
            * **방어 자산군 (5개)**: `GLD, PDBC, OILK, SHY, TLT`
            * **운용 가이드**: 공격 시 1·3·6·12개월 단순평균 모멘텀 1위 섹터에 100% 투자. 방어 시 1·3·6·9·12개월 단순평균 모멘텀 1위 자산에 투자하되, 그 스코어마저 0 이하면 현금 100%로 대피.

            ---
            #### 📝 핵심 모멘텀 스코어 산출 공식
            1. **단순 평균 모멘텀 스코어** (전략 A·C 공격형): 최근 1년 단기·중기·장기 수익률을 균등 반영
            $$\\text{Momentum Score} = \\frac{R_1 + R_3 + R_6 + R_{12}}{4}$$
            2. **방어 자산용 장기 모멘텀 스코어** (전략 A·B·C 방어형): 9개월 구간을 추가해 더 보수적으로 평가
            $$\\text{Defensive Momentum} = \\frac{R_1 + R_3 + R_6 + R_9 + R_{12}}{5}$$
            3. **가중 평균 모멘텀 스코어** (전략 B 공격형): 레버리지 특성상 최근 수익률에 높은 가중치 부여
            $$\\text{Weighted Momentum} = \\frac{12R_1 + 4R_3 + 2R_6 + R_{12}}{19}$$

            #### 🔁 리밸런싱 프로세스
            1. **카나리아 모니터링**: 매월 말 TIP 가격·모멘텀과 S&P 500 배당수익률을 통해 각 전략의 공격/방어 신호를 산출합니다.
            2. **전략별 자산 확정**: 전략 A는 모멘텀 상위 4자산(공격) 또는 1자산(방어), 전략 B·C는 각각 상위 1자산을 선정합니다.
            3. **동일비중 결합**: 세 전략의 산출 비중을 각 33.33%씩 환산·합산하여 매월 리밸런싱을 실행합니다.

            #### 🛡️ MDD 개선 장치 (선택 적용)
            2019년 5월 무역전쟁 급락 당시 -13.0%의 최대 낙폭(MDD)이 발생한 원인을 분석한 결과, 3개 전략이 독립적으로 신호를 계산하다 보니
            SMH(41.66%)·UPRO(33.33%) 등 특정 자산·섹터에 비중이 중복 쏠리는 현상이 핵심 원인으로 확인되었습니다. 아래 2가지 개선 장치를 선택적으로 적용할 수 있습니다.
            - ✅ **비중 상한 (적용 가능)**: 단일 자산군 비중 상한(Cap 25%) — 아래 백테스트 성과 분석 섹션의 체크박스로 지금 바로 켜고 끄며 비교할 수 있습니다.
            - ✅ **월중 하드스탑 (적용 가능)**: 월중 하드스탑(Intra-month Stop-loss) — 월중 낙폭이 -7%에 도달하면 즉시 현금화, 체크박스로 On/Off 가능합니다.

            > 실제 장기 성과(CAGR, MDD, 연도별/월별 수익률 등)는 아래 **🛑 2026 혼합전략 백테스트 성과 분석** 섹션에서 야후 파이낸스 실시간 데이터를 기반으로 항상 최신 상태로 자동 계산됩니다.
            """)

        st.markdown("### 🚦 실시간 카나리아 신호 요약")
        c_sig1, c_sig2, c_sig3 = st.columns(3)
        c_sig1.metric("전략A (TIP 비율)", f"{tip_ratio:.3f}", "공격" if is_attack_a else "방어", delta_color="inverse" if not is_attack_a else "normal")
        c_sig2.metric("전략B (TIP 모멘텀)", f"{tip_score_b:.2f}%", "공격" if is_attack_b else "방어", delta_color="inverse" if not is_attack_b else "normal")
        c_sig3.metric("전략C (배당수익률)", f"{realtime_dy:.2f}%", "공격" if is_attack_c else "방어", delta_color="inverse" if not is_attack_c else "normal")

        st.markdown("### 📊 포트폴리오 비중 분배 현황")
        chart_col = st.container()

        with chart_col:
            try:
                import altair as alt
                df_chart = df_mix.copy()
                df_chart["배분 비중 (%)"] = pd.to_numeric(df_chart["배분 비중 (%)"])
                df_chart["차트라벨"] = df_chart["자산군 (Ticker)"] + " (" + df_chart["배분 비중 (%)"].astype(str) + "%)"
                
                premium_colors = ["#3b82f6", "#ef4444", "#10b981", "#f59e0b", "#8b5cf6", "#ec4899", "#06b6d4", "#f97316"]
                color_scale = alt.Scale(domain=df_chart["차트라벨"].tolist(), range=premium_colors[:len(df_chart)])
                
                donut_chart = alt.Chart(df_chart).mark_arc(innerRadius=62, outerRadius=95, stroke='#ffffff', strokeWidth=2.5).encode(
                    theta=alt.Theta(field="배분 비중 (%)", type="quantitative"),
                    color=alt.Color(
                        field="차트라벨", 
                        type="nominal", 
                        scale=color_scale,
                        legend=alt.Legend(
                            orient="bottom",
                            title=None,
                            labelFontSize=11.5,
                            labelFontWeight="bold",
                            symbolType="circle",
                            symbolSize=110,
                            columns=2,
                            labelColor="#1e293b",
                            padding=15
                        )
                    ),
                    tooltip=[
                        alt.Tooltip("자산군 (Ticker)", title="자산군"),
                        alt.Tooltip("배분 비중 (%)", title="비중 (%)", format=".1f"),
                        alt.Tooltip("현재가 ($)", title="현재가")
                    ]
                ).properties(height=310).configure_view(strokeWidth=0)
                
                st.altair_chart(donut_chart, use_container_width=True)
            except Exception:
                st.info("시각화 뷰 로드 완료")
                st.bar_chart(df_mix.set_index("자산군 (Ticker)")["배분 비중 (%)"])
        
        st.dataframe(
            df_mix_view, use_container_width=True, hide_index=True,
            column_config={
                "선택 기준 · 값": st.column_config.TextColumn("선택 기준 · 값", width="large"),
                "참여 전략 (신호)": st.column_config.TextColumn("참여 전략 (신호)", width="medium"),
            },
        )
        st.caption("※ 선택 기준·값: 각 전략이 해당 자산을 고른 이유와 스코어입니다. 1M·3M·6M·12M은 해당 자산의 기간별 수익률입니다. 배분 비중은 전체 자산 대비 %입니다.")

        st.markdown("### 💰 실시간 리밸런싱 목표 수량 계산기")
        st.markdown("현재 환율과 실시간 주가를 기반으로, 설정한 원화 예산에 필요한 **자산별 목표 환전 달러** 및 **실제 매수 주수**를 계산해 드립니다.")
        
        live_exchange_rate = get_usd_krw_rate()
        st.info(f"💵 **실시간 적용 환율**: 1달러 = **{live_exchange_rate:,.2f}원** (야후 파이낸스 USDKRW=X 기준)")
        
        total_krw_budget = st.number_input(
            "총 투자 금액 입력 (원화 ₩)",
            min_value=0,
            value=10000000,
            step=100000,
            format="%d"
        )
        
        if total_krw_budget > 0:
            calc_data = []
            for _, row in df_mix.iterrows():
                ticker = row["자산군 (Ticker)"]
                weight = row["배분 비중 (%)"]
                
                krw_allocation = total_krw_budget * (weight / 100.0)
                usd_allocation = krw_allocation / live_exchange_rate
                
                if ticker == "CASH (현금)":
                    target_shares = "-"
                    current_price_str = "-"
                else:
                    price = data_dict.get(ticker, {}).get("현재가", 0.0)
                    current_price_str = f"${price:.2f}"
                    if price > 0:
                        target_shares = f"{usd_allocation / price:.1f} 주"
                    else:
                        target_shares = "계산 불가"
                
                calc_data.append({
                    "자산군 (Ticker)": ticker,
                    "배분 비중": f"{weight:.2f}%",
                    "배정액 (원화)": f"₩ {krw_allocation:,.0f}",
                    "목표 투자액 (달러)": f"${usd_allocation:,.2f}",
                    "현재가": current_price_str,
                    "목표 매수량": target_shares
                })
            
            st.dataframe(pd.DataFrame(calc_data), use_container_width=True, hide_index=True)

        if hist_prices and "SPY" in hist_prices:
            st.markdown("---")
            st.markdown("### 📅 월말 기준 리밸런싱 포트폴리오 역사 (최근 1년)")
            st.caption("매월 최종 영업일 마감 데이터를 기준으로 실시간 모멘텀과 시그널을 연산하여, 익월 1일 아침 리밸런싱 시 적용되는 혼합 포트폴리오 구성 비중입니다.")
            
            spy_series = hist_prices["SPY"]
            df_spy_dates = spy_series.to_frame()
            df_spy_dates['year'] = df_spy_dates.index.year
            df_spy_dates['month'] = df_spy_dates.index.month
            
            month_ends = df_spy_dates.groupby(['year', 'month']).apply(lambda x: x.index[-1]).tolist()
            
            now = datetime.datetime.now()
            completed_month_ends = [d for d in month_ends if not (d.year == now.year and d.month == now.month)]
            completed_12_months = completed_month_ends[-12:]
            completed_12_months.reverse()
            
            col_h1, col_h2 = st.columns(2)
            for idx, date in enumerate(completed_12_months):
                target_col = col_h1 if idx % 2 == 0 else col_h2
                
                # 변수명 재사용 이슈 방지를 위한 hist_sig_a, hist_sig_b, hist_sig_c 구분 수정
                hist_portfolio, hist_sig_a, hist_sig_b, hist_sig_c, dy_c = compute_historical_portfolio_at_month_end(
                    hist_prices, spy_divs_hist, date,
                    OFFENSIVE_A, DEFENSIVE_A, OFFENSIVE_B, DEFENSIVE_B, OFFENSIVE_C, DEFENSIVE_C
                )
                
                date_str = date.strftime("%Y년 %m월 %d일")
                sig_text_a = "🟢 공격" if hist_sig_a else "🛡️ 방어"
                sig_text_b = "🟢 공격" if hist_sig_b else "🛡️ 방어"
                sig_text_c = "🟢 공격" if hist_sig_c else "🛡️ 방어"
                
                with target_col:
                    with st.expander(f"📅 {date_str} 마감 기준 포트폴리오"):
                        sm1, sm2, sm3 = st.columns(3)
                        with sm1:
                            st.caption("전략A 신호")
                            st.markdown(f"**{sig_text_a}**")
                        with sm2:
                            st.caption("전략B 신호")
                            st.markdown(f"**{sig_text_b}**")
                        with sm3:
                            st.caption("전략C 신호")
                            st.markdown(f"**{sig_text_c}**<br/><small>({dy_c:.2f}%)</small>", unsafe_allow_html=True)
                        
                        st.markdown("**포트폴리오 비중:**")
                        hist_rows = [{"자산명(Ticker)": k, "배분비중 (%)": f"{v:.2f}%"} for k, v in hist_portfolio.items()]
                        if hist_rows:
                            st.dataframe(pd.DataFrame(hist_rows), use_container_width=True, hide_index=True)
                        else:
                            st.write("⚠️ 해당 기간 데이터 부족")

        st.markdown("---")
        st.markdown("### 🛑 2026 혼합전략 백테스트 성과 분석")

        with st.container():
            st.markdown('<div class="control-panel">', unsafe_allow_html=True)
            st.markdown('<div class="control-header">⚙️ 데이터 범위 및 리스크 관리 설정</div>', unsafe_allow_html=True)
            bt_start_label_mix = st.selectbox(
                "분석 및 백테스트 시작일",
                ["2018-01-01 (코로나 및 금리인상기 포함)", "2015-01-01 (장기 검증)", "2020-01-01 (최근 트렌드)"],
                index=1,
                key="bt_start_select_mix"
            )
            bt_start_mix = bt_start_label_mix.split(" ")[0]
            st.markdown("**🛡️ MDD 개선 로직 (단계별 적용 — 개별 On/Off 가능)**")
            _mc1, _mc2 = st.columns(2)
            mix_cap = _mc1.number_input("비중 상한 (%)", min_value=10.0, max_value=50.0, value=25.0, step=1.0, key="mix_cap_pct")
            mix_stop = _mc2.number_input("월중 하드스탑 (%)", min_value=-20.0, max_value=-1.0, value=-7.0, step=0.5, key="mix_stop_pct")
            apply_cap_mix = st.checkbox(
                f"비중 상한: 단일 자산군 비중 상한(Cap {mix_cap:.0f}%) 적용",
                value=False,
                key="apply_cap_mix",
                help="2019년 5월 무역전쟁 급락 시 SMH(41.66%)·UPRO(33.33%) 등 특정 자산에 3개 전략 비중이 겹치며 MDD가 커졌던 문제를 보완합니다. "
                     "3개 전략을 합산했을 때 단일 티커 비중이 위에서 설정한 상한을 넘으면 초과분을 현금으로 자동 전환합니다."
            )
            apply_stop_mix = st.checkbox(
                f"월중 하드스탑: 월중 낙폭 {mix_stop:.1f}% 도달 시 즉시 현금화",
                value=False,
                key="apply_stop_mix",
                help="월말 리밸런싱만으로는 2019년 5월 무역전쟁 급락 같은 월중 기습 악재에 대응할 수 없었던 한계를 보완합니다. "
                     "일별 가격으로 월중 누적 손실을 감시하다가 월초(전월 말) 대비 설정한 낙폭까지 하락하면, 그 시점 이후 월말까지 전량 현금 보유로 간주해 추가 손실을 차단합니다."
            )
            st.caption("선택한 시작일 기준으로 2026 혼합전략(전략A+B+C 33.33%씩) 백테스트 시뮬레이션이 즉시 재계산됩니다.")
            st.markdown('</div>', unsafe_allow_html=True)

        use_improved_mix = apply_cap_mix or apply_stop_mix

        with st.spinner("2026 혼합전략 실시간 백테스트 엔진 구동 중... (전략 A+B+C 통합 연산)"):
            try:
                bt_tickers_mix = sorted(set(
                    OFFENSIVE_A + DEFENSIVE_A + OFFENSIVE_B + DEFENSIVE_B + OFFENSIVE_C + DEFENSIVE_C
                    + ["TIP", "SPY", "QQQ"]
                ))
                daily_px_mix = get_daily_price_history_a(bt_tickers_mix, start=bt_start_mix)
                monthly_px_mix = to_monthly_last_a(daily_px_mix)
                spy_divs_mix = get_spy_dividend_history()
                if use_improved_mix:
                    bt_results_mix = run_backtest_strategy_mix_improved_full(
                        monthly_px_mix, spy_divs_mix, daily_px=daily_px_mix,
                        apply_cap=apply_cap_mix, weight_cap=mix_cap,
                        apply_stop_loss=apply_stop_mix, stop_loss_pct=mix_stop,
                    )
                else:
                    bt_results_mix = run_backtest_strategy_mix_full(monthly_px_mix, spy_divs_mix)
                bt_ok_mix = len(bt_results_mix) > 0
            except Exception as e:
                st.error(f"2026 혼합전략 백테스트 데이터 로딩 중 오류가 발생했습니다: {e}")
                bt_ok_mix = False

        if not bt_ok_mix:
            st.warning("백테스트 데이터가 부족하거나 오류가 있습니다. 잠시 후 다시 시도해 주세요.")
        else:
            st.caption(f"시뮬레이션 기간: {bt_results_mix['date'].iloc[0].strftime('%Y-%m')} ~ {bt_results_mix['date'].iloc[-1].strftime('%Y-%m')}")
            if use_improved_mix:
                applied_stages = []
                if apply_cap_mix:
                    applied_stages.append("비중상한")
                if apply_stop_mix:
                    applied_stages.append("월중손절")
                st.success(f"🛡️ [개선판] {' + '.join(applied_stages)} 로직이 적용된 결과입니다. 체크박스를 해제하면 기존 로직과 바로 비교할 수 있습니다.")

            total_days_mix = (bt_results_mix["date"].iloc[-1] - bt_results_mix["date"].iloc[0]).days
            total_years_mix = total_days_mix / 365.25 if total_days_mix > 0 else 1.0
            final_nav_mix = bt_results_mix["nav"].iloc[-1]

            cagr_mix = ((final_nav_mix / 100.0) ** (1 / total_years_mix) - 1) * 100
            mdd_mix = bt_results_mix["drawdown"].min()

            bmc1, bmc2, bmc3 = st.columns(3)
            bmc1.metric("연환산 복리 수익률 (CAGR)", f"{cagr_mix:.2f}%")
            bmc2.metric("최대 낙폭 (MDD)", f"{mdd_mix:.2f}%", delta_color="inverse")
            bmc3.metric("최종 자산 가치 (NAV)", f"{final_nav_mix:.1f}", "초기금 100 기준")

            st.markdown("##### 📈 자산 곡선 (NAV) 추이")
            chart_df_mix = bt_results_mix.copy()
            chart_df_mix["date_str"] = chart_df_mix["date"].dt.strftime("%Y-%m")

            qqq_ret_series_mix = monthly_px_mix["QQQ"].pct_change().reindex(bt_results_mix["date"])
            chart_df_mix["qqq_nav"] = (100 * (1 + qqq_ret_series_mix.fillna(0)).cumprod()).values

            nav_color_scale_mix = alt.Scale(domain=["2026 혼합전략", "QQQ"], range=["#0ea5e9", "#808080"])
            nav_long_mix = chart_df_mix.melt(
                id_vars="date_str", value_vars=["nav", "qqq_nav"], var_name="series", value_name="value"
            )
            nav_long_mix["series"] = nav_long_mix["series"].map({"nav": "2026 혼합전략", "qqq_nav": "QQQ"})

            nav_chart_mix = alt.Chart(nav_long_mix).mark_line(size=2.5).encode(
                x=alt.X("date_str:N", sort=None, title="년-월"),
                y=alt.Y("value:Q", title="NAV (기준 100)"),
                color=alt.Color("series:N", scale=nav_color_scale_mix, legend=alt.Legend(title=None, orient="bottom")),
                tooltip=[
                    alt.Tooltip("date_str:N", title="년-월"),
                    alt.Tooltip("series:N", title="구분"),
                    alt.Tooltip("value:Q", title="NAV", format=".1f"),
                ],
            ).properties(height=350)
            st.altair_chart(nav_chart_mix, use_container_width=True)

            # ------------------------------------------------------------
            # 연도별 수익률 (Annual Returns) — 막대 차트
            # ------------------------------------------------------------
            st.markdown("##### 📊 연도별 수익률 (%)")
            yearly_df_mix = bt_results_mix.copy()
            yearly_df_mix["year"] = yearly_df_mix["date"].dt.year
            yearly_returns_mix = (
                yearly_df_mix.groupby("year")["monthly_return"]
                .apply(lambda x: (np.prod(1 + x / 100.0) - 1) * 100)
                .reset_index(name="annual_return")
            )
            yearly_returns_mix["year_str"] = yearly_returns_mix["year"].astype(str)
            yearly_returns_mix["series"] = "2026 혼합전략"
            year_sort_order_mix = yearly_returns_mix["year_str"].tolist()

            qqq_monthly_ret_mix = monthly_px_mix["QQQ"].pct_change().reindex(bt_results_mix["date"]) * 100
            qqq_ret_df_mix = pd.DataFrame({
                "date": bt_results_mix["date"].values,
                "qqq_return": qqq_monthly_ret_mix.values,
            })
            qqq_ret_df_mix["year"] = pd.to_datetime(qqq_ret_df_mix["date"]).dt.year
            qqq_yearly_mix = (
                qqq_ret_df_mix.groupby("year")["qqq_return"]
                .apply(lambda x: (np.prod(1 + x / 100.0) - 1) * 100)
                .reset_index(name="annual_return")
            )
            qqq_yearly_mix["year_str"] = qqq_yearly_mix["year"].astype(str)
            qqq_yearly_mix["series"] = "QQQ"

            color_scale_mix = alt.Scale(domain=["2026 혼합전략", "QQQ"], range=["#0ea5e9", "#808080"])

            annual_bar_mix = alt.Chart(yearly_returns_mix).mark_bar(size=28).encode(
                x=alt.X("year_str:N", title="연도", sort=year_sort_order_mix),
                y=alt.Y("annual_return:Q", title="수익률 (%)"),
                color=alt.Color("series:N", scale=color_scale_mix, legend=alt.Legend(title=None, orient="bottom")),
                tooltip=[
                    alt.Tooltip("year_str:N", title="연도"),
                    alt.Tooltip("annual_return:Q", title="수익률", format="+.2f"),
                ],
            )
            annual_labels_mix = alt.Chart(yearly_returns_mix).mark_text(
                dy=alt.expr("datum.annual_return >= 0 ? -8 : 14"), fontWeight="bold", fontSize=11, color="#0f172a"
            ).encode(
                x=alt.X("year_str:N", sort=year_sort_order_mix),
                y=alt.Y("annual_return:Q"),
                text=alt.Text("annual_return:Q", format="+.1f"),
            )
            qqq_points_mix = alt.Chart(qqq_yearly_mix).mark_point(
                filled=True, size=110, stroke="white", strokeWidth=1.2
            ).encode(
                x=alt.X("year_str:N", sort=year_sort_order_mix),
                y=alt.Y("annual_return:Q"),
                color=alt.Color("series:N", scale=color_scale_mix, legend=alt.Legend(title=None, orient="bottom")),
                tooltip=[
                    alt.Tooltip("year_str:N", title="연도"),
                    alt.Tooltip("annual_return:Q", title="QQQ 수익률", format="+.2f"),
                ],
            )
            st.altair_chart(
                (annual_bar_mix + annual_labels_mix + qqq_points_mix).properties(height=320),
                use_container_width=True,
            )

            # ------------------------------------------------------------
            # 월별 수익률 (Monthly Returns) — 히트맵 테이블
            # ------------------------------------------------------------
            st.markdown("##### 🗓️ 월별 수익률 (%)")
            monthly_df_mix = bt_results_mix.copy()
            monthly_df_mix["year"] = monthly_df_mix["date"].dt.year
            monthly_df_mix["month"] = monthly_df_mix["date"].dt.month

            month_labels_mix = {1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
                                7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"}
            monthly_df_mix["month_label"] = monthly_df_mix["month"].map(month_labels_mix)
            monthly_df_mix["year_label"] = monthly_df_mix["year"].astype(str)

            avg_by_month_mix = monthly_df_mix.groupby(["month", "month_label"])["monthly_return"].mean().reset_index()
            avg_by_month_mix["year_label"] = "평균"

            heat_df_mix = pd.concat([
                monthly_df_mix[["year_label", "month", "month_label", "monthly_return"]],
                avg_by_month_mix[["year_label", "month", "month_label", "monthly_return"]],
            ], ignore_index=True)

            year_sort_order_full_mix = [str(y) for y in sorted(monthly_df_mix["year"].unique())] + ["평균"]
            month_sort_order_mix = [month_labels_mix[m] for m in range(1, 13)]

            heat_rect_mix = alt.Chart(heat_df_mix).mark_rect(stroke="white", strokeWidth=1.5).encode(
                x=alt.X("month_label:N", title=None, sort=month_sort_order_mix),
                y=alt.Y("year_label:N", title=None, sort=year_sort_order_full_mix),
                color=alt.Color(
                    "monthly_return:Q",
                    scale=alt.Scale(
                        type="threshold",
                        domain=[-3.5, -2.5, -1.5, -0.5, 0.5, 1.5, 2.5, 3.5],
                        range=["#cf6265", "#e67f82", "#ecaaab", "#f6d4d5", "#fafbff",
                               "#d7e4da", "#accab2", "#82ae8b", "#599265"],
                    ),
                    legend=alt.Legend(title="수익률 (%)", orient="bottom", gradientLength=220),
                ),
                tooltip=[
                    alt.Tooltip("year_label:N", title="연도"),
                    alt.Tooltip("month_label:N", title="월"),
                    alt.Tooltip("monthly_return:Q", title="수익률", format="+.2f"),
                ],
            )
            heat_text_mix = alt.Chart(heat_df_mix).mark_text(fontSize=10, fontWeight="bold").encode(
                x=alt.X("month_label:N", sort=month_sort_order_mix),
                y=alt.Y("year_label:N", sort=year_sort_order_full_mix),
                text=alt.Text("monthly_return:Q", format="+.1f"),
                color=alt.value("#334155"),
            )
            st.altair_chart(
                (heat_rect_mix + heat_text_mix).properties(height=32 * len(year_sort_order_full_mix) + 80),
                use_container_width=True,
            )

            st.markdown("##### 📉 낙폭 (Drawdown) 히스토리")
            dd_chart_mix = alt.Chart(chart_df_mix).mark_area(color="#fecaca", opacity=0.8).encode(
                x=alt.X("date_str:N", sort=None, title="년-월"),
                y=alt.Y("drawdown:Q", title="MDD (%)"),
                tooltip=["date_str", "drawdown"]
            ).properties(height=200)
            st.altair_chart(dd_chart_mix, use_container_width=True)

            _ser_a_mix = run_backtest_strategy_a_full(monthly_px_mix).set_index("date")["monthly_return"]
            _ser_b_mix = run_backtest_strategy_b_full(monthly_px_mix).set_index("date")["monthly_return"]
            _ser_c_mix = run_backtest_strategy_c_full(monthly_px_mix, spy_divs_mix).set_index("date")["monthly_return"]

            def _period_ret_mix(ser, a, b):
                sub = ser[(ser.index >= a) & (ser.index <= b)]
                return (np.prod(1 + sub.values / 100.0) - 1) * 100 if len(sub) else float("nan")

            st.markdown("##### 🚨 포트폴리오 드로우다운 Top 10")
            dd_vals_mix = bt_results_mix["drawdown"].values
            dd_dates_mix = bt_results_mix["date"].values
            n_mix = len(dd_vals_mix)
            episodes_mix = []
            i_ep = 0
            while i_ep < n_mix:
                if dd_vals_mix[i_ep] < -0.001:
                    start_i = i_ep
                    j_ep = i_ep
                    min_val = dd_vals_mix[i_ep]
                    min_idx = i_ep
                    while j_ep < n_mix and dd_vals_mix[j_ep] < -0.001:
                        if dd_vals_mix[j_ep] < min_val:
                            min_val = dd_vals_mix[j_ep]
                            min_idx = j_ep
                        j_ep += 1
                    episodes_mix.append({
                        "시작": pd.Timestamp(dd_dates_mix[start_i]).strftime("%Y/%m"),
                        "종료": pd.Timestamp(dd_dates_mix[min_idx]).strftime("%Y/%m"),
                        "드로우다운": min_val,
                        "_s": pd.Timestamp(dd_dates_mix[start_i]),
                        "_e": pd.Timestamp(dd_dates_mix[min_idx]),
                    })
                    i_ep = j_ep
                else:
                    i_ep += 1

            episodes_mix.sort(key=lambda x: x["드로우다운"])
            top10_mix = episodes_mix[:10]
            for idx, ep in enumerate(top10_mix):
                ep["순위"] = idx + 1
                ep["드로우다운"] = f"{ep['드로우다운']:.1f}%"
                ep["A 전략"] = f"{_period_ret_mix(_ser_a_mix, ep['_s'], ep['_e']):+.1f}%"
                ep["B 전략"] = f"{_period_ret_mix(_ser_b_mix, ep['_s'], ep['_e']):+.1f}%"
                ep["C 전략"] = f"{_period_ret_mix(_ser_c_mix, ep['_s'], ep['_e']):+.1f}%"
            if top10_mix:
                df_dd_top10_mix = pd.DataFrame(top10_mix)[["순위", "시작", "종료", "드로우다운", "A 전략", "B 전략", "C 전략"]].rename(columns={"드로우다운": "합계(A+B+C) 드로우다운"})
                st.dataframe(df_dd_top10_mix, use_container_width=True, hide_index=True)
                st.caption("※ 합계(A+B+C)는 세 전략을 1/3씩 섞은 혼합 포트폴리오의 낙폭이고, A·B·C 열은 같은 기간(시작~종료월) 각 전략을 단독(100%)으로 운용했을 때의 수익률입니다.")
            else:
                st.info("드로우다운 구간이 발견되지 않았습니다.")

            st.markdown("##### 🔻 폭락 시장 포트폴리오 성과")
            STRESS_PERIODS_MIX = [
                ("코로나 팬데믹", "2020-01-01", "2020-03-31"),
                ("2022 긴축 발작 (금리인상기)", "2022-01-01", "2022-10-31"),
                ("2018년 4분기 조정", "2018-10-01", "2018-12-31"),
            ]
            stress_rows_mix = []
            for label, s, e in STRESS_PERIODS_MIX:
                s_ts, e_ts = pd.Timestamp(s), pd.Timestamp(e)
                mask_mix = (bt_results_mix["date"] >= s_ts) & (bt_results_mix["date"] <= e_ts)
                sub_mix = bt_results_mix[mask_mix]
                if len(sub_mix) == 0:
                    continue
                port_cum_mix = (np.prod(1 + sub_mix["monthly_return"].values / 100.0) - 1) * 100
                qqq_sub_ret_mix = monthly_px_mix["QQQ"].pct_change().reindex(sub_mix["date"]).fillna(0.0)
                qqq_cum_mix = (np.prod(1 + qqq_sub_ret_mix.values) - 1) * 100
                stress_rows_mix.append({
                    "스트레스 기간": label,
                    "시작": s_ts.strftime("%Y/%m"),
                    "종료": e_ts.strftime("%Y/%m"),
                    "합계(A+B+C) 수익률": f"{port_cum_mix:+.1f}%",
                    "A 전략": f"{_period_ret_mix(_ser_a_mix, s_ts, e_ts):+.1f}%",
                    "B 전략": f"{_period_ret_mix(_ser_b_mix, s_ts, e_ts):+.1f}%",
                    "C 전략": f"{_period_ret_mix(_ser_c_mix, s_ts, e_ts):+.1f}%",
                    "QQQ 수익률": f"{qqq_cum_mix:+.1f}%",
                })
            if stress_rows_mix:
                st.dataframe(pd.DataFrame(stress_rows_mix), use_container_width=True, hide_index=True)
            else:
                st.info("선택한 시작일 범위 내 해당하는 폭락장 스트레스 기간 데이터가 없습니다. 시작일을 앞당겨 보세요.")

            st.markdown("##### 📊 주요 지표 비교 (vs QQQ)")

            def _fmt_pct_mix(x):
                return f"{x:.1f}%" if x is not None and not (isinstance(x, float) and np.isnan(x)) else "데이터 부족"

            port_ret_arr_mix = bt_results_mix["monthly_return"].values
            qqq_ret_arr_mix = qqq_monthly_ret_mix.values
            dd_arr_mix = bt_results_mix["drawdown"].values
            qqq_nav_arr_mix = chart_df_mix["qqq_nav"].values
            qqq_running_max_mix = np.maximum.accumulate(qqq_nav_arr_mix)
            qqq_dd_arr_mix = (qqq_nav_arr_mix / qqq_running_max_mix - 1) * 100

            period_ret_mix = (final_nav_mix / 100.0 - 1) * 100
            qqq_final_nav_mix = qqq_nav_arr_mix[-1]
            qqq_period_ret_mix = (qqq_final_nav_mix / 100.0 - 1) * 100
            qqq_cagr_mix = ((qqq_final_nav_mix / 100.0) ** (1 / total_years_mix) - 1) * 100

            last_date_mix2 = bt_results_mix["date"].iloc[-1]
            current_year_mix2 = last_date_mix2.year
            ytd_mask_mix = bt_results_mix["date"].dt.year == current_year_mix2
            port_ytd_mix = (np.prod(1 + bt_results_mix.loc[ytd_mask_mix, "monthly_return"].values / 100.0) - 1) * 100
            qqq_ytd_mix = (np.prod(1 + (qqq_ret_arr_mix[ytd_mask_mix.values] / 100.0)) - 1) * 100

            win_months_mix = int((port_ret_arr_mix > 0).sum())
            qqq_win_months_mix = int((qqq_ret_arr_mix > 0).sum())
            total_months_mix = len(port_ret_arr_mix)

            mdd_idx_mix = int(np.argmin(dd_arr_mix))
            mdd_date_mix = bt_results_mix["date"].iloc[mdd_idx_mix].strftime("%Y-%m")
            qqq_mdd_idx_mix = int(np.argmin(qqq_dd_arr_mix))
            qqq_mdd_date_mix = bt_results_mix["date"].iloc[qqq_mdd_idx_mix].strftime("%Y-%m")

            def _trailing_mix(arr, months):
                if len(arr) < months:
                    return None, None
                window = arr[-months:]
                cum = (np.prod(1 + window / 100.0) - 1) * 100
                ann_std = np.std(window, ddof=1) * np.sqrt(12) if len(window) > 1 else None
                return cum, ann_std

            ret_1y_mix, std_1y_mix = _trailing_mix(port_ret_arr_mix, 12)
            ret_3y_mix, std_3y_mix = _trailing_mix(port_ret_arr_mix, 36)
            ret_5y_mix, std_5y_mix = _trailing_mix(port_ret_arr_mix, 60)
            qqq_ret_1y_mix, qqq_std_1y_mix = _trailing_mix(qqq_ret_arr_mix, 12)
            qqq_ret_3y_mix, qqq_std_3y_mix = _trailing_mix(qqq_ret_arr_mix, 36)
            qqq_ret_5y_mix, qqq_std_5y_mix = _trailing_mix(qqq_ret_arr_mix, 60)

            mean_m_mix = np.mean(port_ret_arr_mix) / 100.0
            std_m_mix = np.std(port_ret_arr_mix, ddof=1) / 100.0 if total_months_mix > 1 else np.nan
            annual_vol_mix = std_m_mix * np.sqrt(12) * 100 if not np.isnan(std_m_mix) else np.nan
            sharpe_mix = (mean_m_mix * 12) / (std_m_mix * np.sqrt(12)) if std_m_mix and std_m_mix > 0 else np.nan

            downside_mix = port_ret_arr_mix[port_ret_arr_mix < 0] / 100.0
            downside_std_mix = np.std(downside_mix, ddof=1) if len(downside_mix) > 1 else np.nan
            sortino_mix = (mean_m_mix * 12) / (downside_std_mix * np.sqrt(12)) if downside_std_mix and downside_std_mix > 0 else np.nan

            ulcer_mix = np.sqrt(np.mean(dd_arr_mix ** 2))
            upi_mix = cagr_mix / ulcer_mix if ulcer_mix > 0 else np.nan

            qqq_mean_m_mix = np.mean(qqq_ret_arr_mix) / 100.0
            qqq_std_m_mix = np.std(qqq_ret_arr_mix, ddof=1) / 100.0 if total_months_mix > 1 else np.nan
            qqq_annual_vol_mix = qqq_std_m_mix * np.sqrt(12) * 100 if not np.isnan(qqq_std_m_mix) else np.nan
            qqq_sharpe_mix = (qqq_mean_m_mix * 12) / (qqq_std_m_mix * np.sqrt(12)) if qqq_std_m_mix and qqq_std_m_mix > 0 else np.nan

            qqq_downside_mix = qqq_ret_arr_mix[qqq_ret_arr_mix < 0] / 100.0
            qqq_downside_std_mix = np.std(qqq_downside_mix, ddof=1) if len(qqq_downside_mix) > 1 else np.nan
            qqq_sortino_mix = (qqq_mean_m_mix * 12) / (qqq_downside_std_mix * np.sqrt(12)) if qqq_downside_std_mix and qqq_downside_std_mix > 0 else np.nan

            qqq_ulcer_mix = np.sqrt(np.mean(qqq_dd_arr_mix ** 2))
            qqq_upi_mix = qqq_cagr_mix / qqq_ulcer_mix if qqq_ulcer_mix > 0 else np.nan

            alloc_list_mix = bt_results_mix["alloc"].tolist()
            monthly_turnovers_mix = []
            prev_alloc_mix = {}
            for alloc_d in alloc_list_mix:
                all_tk_mix = set(prev_alloc_mix.keys()) | set(alloc_d.keys())
                diff_mix = sum(abs(alloc_d.get(t, 0.0) - prev_alloc_mix.get(t, 0.0)) for t in all_tk_mix)
                monthly_turnovers_mix.append(diff_mix / 2.0)
                prev_alloc_mix = alloc_d
            avg_turnover_mix = np.mean(monthly_turnovers_mix) if monthly_turnovers_mix else 0.0
            annual_turnover_mix = avg_turnover_mix * 12

            metrics_rows_mix = [
                ("기간 수익률", _fmt_pct_mix(period_ret_mix), _fmt_pct_mix(qqq_period_ret_mix)),
                ("연환산 수익률 (CAGR)", _fmt_pct_mix(cagr_mix), _fmt_pct_mix(qqq_cagr_mix)),
                ("이번 달 수익률", _fmt_pct_mix(port_ret_arr_mix[-1]), _fmt_pct_mix(qqq_ret_arr_mix[-1])),
                ("올해 수익률 (YTD)", _fmt_pct_mix(port_ytd_mix), _fmt_pct_mix(qqq_ytd_mix)),
                ("월 최고 수익률", _fmt_pct_mix(port_ret_arr_mix.max()), _fmt_pct_mix(qqq_ret_arr_mix.max())),
                ("월 최저 수익률", _fmt_pct_mix(port_ret_arr_mix.min()), _fmt_pct_mix(qqq_ret_arr_mix.min())),
                ("수익 월 비중", f"{win_months_mix} / {total_months_mix}", f"{qqq_win_months_mix} / {total_months_mix}"),
                ("연 변동성", _fmt_pct_mix(annual_vol_mix), _fmt_pct_mix(qqq_annual_vol_mix)),
                ("최대 낙폭 (MDD)", _fmt_pct_mix(mdd_mix), _fmt_pct_mix(qqq_dd_arr_mix.min())),
                ("MDD 시점", mdd_date_mix, qqq_mdd_date_mix),
                ("1년 수익률", _fmt_pct_mix(ret_1y_mix), _fmt_pct_mix(qqq_ret_1y_mix)),
                ("3년 수익률", _fmt_pct_mix(ret_3y_mix), _fmt_pct_mix(qqq_ret_3y_mix)),
                ("5년 수익률", _fmt_pct_mix(ret_5y_mix), _fmt_pct_mix(qqq_ret_5y_mix)),
                ("1년 표준편차", _fmt_pct_mix(std_1y_mix), _fmt_pct_mix(qqq_std_1y_mix)),
                ("3년 표준편차", _fmt_pct_mix(std_3y_mix), _fmt_pct_mix(qqq_std_3y_mix)),
                ("5년 표준편차", _fmt_pct_mix(std_5y_mix), _fmt_pct_mix(qqq_std_5y_mix)),
                ("샤프 지수", f"{sharpe_mix:.2f}" if not np.isnan(sharpe_mix) else "데이터 부족", f"{qqq_sharpe_mix:.2f}" if not np.isnan(qqq_sharpe_mix) else "데이터 부족"),
                ("소티노 지수", f"{sortino_mix:.2f}" if not np.isnan(sortino_mix) else "데이터 부족", f"{qqq_sortino_mix:.2f}" if not np.isnan(qqq_sortino_mix) else "데이터 부족"),
                ("UPI 지수", f"{upi_mix:.2f}" if not np.isnan(upi_mix) else "데이터 부족", f"{qqq_upi_mix:.2f}" if not np.isnan(qqq_upi_mix) else "데이터 부족"),
                ("연간 턴오버", f"{annual_turnover_mix:.1f}%", "0.0%"),
            ]
            df_metrics_mix = pd.DataFrame(metrics_rows_mix, columns=["지표", "2026 혼합전략", "QQQ"])
            st.dataframe(df_metrics_mix, use_container_width=True, hide_index=True)
            st.caption(f"※ 기간: {bt_results_mix['date'].iloc[0].strftime('%Y-%m')} ~ {bt_results_mix['date'].iloc[-1].strftime('%Y-%m')} 야후 파이낸스 실시간 데이터 기준. 1/3/5년 지표는 해당 기간의 월 데이터가 충분할 때만 표시됩니다.")



            st.markdown("##### 🗓️ 월별 세부 리밸런싱 기록")
            display_bt_mix = bt_results_mix.copy()
            display_bt_mix["연월"] = display_bt_mix["date"].dt.strftime("%Y-%m")
            display_bt_mix["월 수익률"] = display_bt_mix["monthly_return"].apply(lambda x: f"{x:+.2f}%")
            display_bt_mix["낙폭"] = display_bt_mix["drawdown"].apply(lambda x: f"{x:.2f}%")
            display_bt_mix["NAV"] = display_bt_mix["nav"].apply(lambda x: f"{x:.1f}")
            st.caption("※ 전략 A·B·C는 각각 전체 자산의 33.3%씩 배분되며, 괄호 안 비중은 전체 자산 대비 비중입니다. (예: A[TBF 33.3%] = 전략 A가 TBF에 100% 투자)")

            st.dataframe(
                display_bt_mix[["연월", "mode", "월 수익률", "weights_str", "NAV", "낙폭"]].iloc[::-1],
                use_container_width=True, hide_index=True
            )

            st.markdown("---")
            st.markdown("### 🔬 MDD 안전장치 전/후 비교 (비중 상한 · 월중 하드스탑)")
            st.caption(f"같은 기간·같은 전략에서 안전장치만 바꿔 비교합니다. 상한 {mix_cap:.0f}% · 하드스탑 {mix_stop:.1f}%는 위 설정값입니다.")

            def _run_mix(cap=None, stop=None):
                return run_backtest_strategy_mix_improved_full(
                    monthly_px_mix, spy_divs_mix, daily_px=(daily_px_mix if stop is not None else None),
                    apply_cap=cap is not None, weight_cap=cap if cap is not None else 25.0,
                    apply_stop_loss=stop is not None, stop_loss_pct=stop if stop is not None else -7.0,
                )

            _mix_cases = {
                "① 안전장치 없음": {},
                f"② 상한 {mix_cap:.0f}%만": {"cap": mix_cap},
                f"③ 하드스탑 {mix_stop:.1f}%만": {"stop": mix_stop},
                "④ 상한 + 하드스탑": {"cap": mix_cap, "stop": mix_stop},
            }
            _mix_res = {k: _run_mix(**v) for k, v in _mix_cases.items()}
            _mix_rows = []
            for _k, _bt in _mix_res.items():
                _sm = summarize_bt_mix(_bt)
                if _sm:
                    _mix_rows.append({"방식": _k, **_sm})
            if _mix_rows:
                st.dataframe(pd.DataFrame(_mix_rows).round(2), use_container_width=True, hide_index=True)
                st.caption("안전장치는 MDD·최악의 달을 줄이는 대신 평상시 CAGR·샤프를 깎습니다. '발동 (월)'은 실제로 개입한 횟수입니다.")
                _nav_mix = pd.concat({_k.split(" ")[0]: _bt.set_index("date")["nav"] for _k, _bt in _mix_res.items() if len(_bt) > 0}, axis=1)
                st.line_chart(_nav_mix)

    with c_a:
        st.header("🛡️ 전략 A (안정형)")

        with st.expander("📖 전략 A 실행 명세서 (작동원칙)", expanded=False):
            st.markdown("""
            ### 🛡️ 전략 A 핵심 구조 (2단계 카나리아 로테이션 시스템)
            시장의 핵심 선행지표인 물가연동채(TIP)를 통해 거시경제 국면을 판독하고, 국면에 맞춰 공격/방어 자산군 내에서
            모멘텀 상위 종목으로 매월 자동 리밸런싱하는 규칙 기반 시스템입니다.

            #### 1단계 — 카나리아 국면 판독 (신호)
            * 매월 말 기준 TIP의 **현재가**와 **최근 11개월 이동평균선(11MA)**을 비교합니다.
            * **공격 국면**: `TIP 현재가 > TIP 11MA` (신호 비율 > 1.0)
            * **방어 국면**: `TIP 현재가 ≤ TIP 11MA` (신호 비율 ≤ 1.0)

            #### 2단계 — 공격/방어 자산 매수 규칙
            * **공격 국면 (공격 자산 12개 중 선택)**
                * 대상 자산: `QQQ, FEZ, GLD, IBB, SMH, EEM, XLK, LIT, XLE, UBT, XLV, QTUM`
                * 모멘텀 스코어: `(1M + 3M + 6M + 12M) 수익률 단순평균`
                * 행동: 스코어 **상위 4종목**에 각각 **25%씩 균등 배분**합니다. (절대 모멘텀 컷오프 없이 순위만으로 선정)
            * **방어 국면 (방어 자산 5개 중 선택)**
                * 대상 자산: `BIL, IEF, AGG, HYG, TBF`
                * 모멘텀 스코어: `(1M + 3M + 6M + 9M + 12M) 수익률 단순평균`
                * 행동: 스코어 **1위 자산**에 **100% 집중 투자**합니다.
                * 예외 조건 (절대 모멘텀 컷오프): 1위 자산의 스코어마저 **0 이하**이면, 하락장 방어를 위해 해당 비중을 **현금(CASH) 100%**로 대체합니다.

            #### 3단계 — 리밸런싱 주기
            * 매월 말 종가 기준으로 신호를 재판독하고, 위 규칙에 따라 포트폴리오를 전량 재배분합니다.
            * 월중에는 별도의 손절/이탈 로직 없이 월말 리밸런싱까지 배분을 그대로 유지합니다.

            #### 📝 모멘텀 계산 공식 요약
            $$\\text{공격 스코어} = \\frac{R_1 + R_3 + R_6 + R_{12}}{4} \\qquad \\text{방어 스코어} = \\frac{R_1 + R_3 + R_6 + R_9 + R_{12}}{5}$$

            > 실제 장기 성과(CAGR, MDD, 연도별/월별 수익률 등)는 아래 **🛑 전략 A 백테스트 성과 분석** 섹션에서 야후 파이낸스 실시간 데이터를 기반으로 항상 최신 상태로 자동 계산됩니다.
            """)

        st.markdown(
            "**1단계: 카나리아 신호 판단** \n"
            "신호 비율($TIP 현재가 / TIP_{11MA}$)이 $1.0$을 초과하면 공격 모드, 이하이면 방어 모드로 진입합니다."
        )
        col1, col2, col3 = st.columns(3)
        col1.metric("TIP 현재가", f"${tip_current:.2f}")
        col2.metric("TIP 11M 이평", f"${tip_ma11:.2f}")
        col3.metric("신호 비율 (현재/이평)", f"{tip_ratio:.3f}")
        
        if is_attack_a:
            st.success("🔥 **현재 모드: 공격 자산 모드** - 시장의 위험 신호가 낮습니다.")
            df_off_a = df_all[df_all["Ticker"].isin(OFFENSIVE_A)].copy()
            df_off_a = df_off_a.sort_values(by="A_공격스코어", ascending=False)
            
            st.write("**공격 자산 순위 (1-3-6-12M 단순 평균 모멘텀):**")
            st.dataframe(
                df_off_a[["Ticker", "현재가", "1M", "3M", "6M", "12M", "A_공격스코어"]]
                .rename(columns={"A_공격스코어": "모멘텀 스코어"}),
                use_container_width=True, hide_index=True
            )
            
            st.subheader("🎯 최종 포트폴리오 가이드 (각 25% 균등 분배)")
            for t, _ in alloc_a.items():
                p = data_dict.get(t, {}).get("현재가", 0.0)
                s = data_dict.get(t, {}).get("A_공격스코어", 0.0)
                st.info(f"**{t}** (25% 배분) - 현재가: ${p:.2f} (모멘텀: {s:.2f}%)")
        else:
            st.warning("🛡️ **현재 모드: 방어 자산 모드** - 하락장을 방어하는 구간입니다.")
            df_def_a = df_all[df_all["Ticker"].isin(DEFENSIVE_A)].copy()
            df_def_a = df_def_a.sort_values(by="A_방어스코어", ascending=False)
            
            st.write("**방어 자산 순위 (1-3-6-9-12M 단순 평균 모멘텀):**")
            st.dataframe(
                df_def_a[["Ticker", "현재가", "1M", "3M", "6M", "9M", "12M", "A_방어스코어"]]
                .rename(columns={"A_방어스코어": "모멘텀 스코어"}),
                use_container_width=True, hide_index=True
            )
            
            st.subheader("🎯 최종 포트폴리오 가이드")
            for t, _ in alloc_a.items():
                if t == "CASH (현금)":
                    st.error("🚨 **현금(CASH) 보유 : 비중 100%**")
                else:
                    p = data_dict.get(t, {}).get("현재가", 0.0)
                    s = data_dict.get(t, {}).get("A_방어스코어", 0.0)
                    st.info(f"**{t}** : 비중 **100%** (현재가: ${p:.2f}, 모멘텀: {s:.2f}%)")

        st.markdown("---")
        st.markdown("### 🛑 전략 A 백테스트 성과 분석")

        with st.container():
            st.markdown('<div class="control-panel">', unsafe_allow_html=True)
            st.markdown('<div class="control-header">⚙️ 데이터 범위 및 리스크 관리 설정</div>', unsafe_allow_html=True)
            bt_start_label_a = st.selectbox(
                "분석 및 백테스트 시작일",
                ["2018-01-01 (코로나 및 금리인상기 포함)", "2015-01-01 (장기 검증)", "2020-01-01 (최근 트렌드)"],
                index=1,
                key="bt_start_select_a"
            )
            bt_start_a = bt_start_label_a.split(" ")[0]
            st.caption("선택한 시작일 기준으로 전략 A 백테스트 시뮬레이션(NAV, 연도별/월별 수익률, 낙폭, 리밸런싱 기록)이 즉시 재계산됩니다.")
            st.markdown('</div>', unsafe_allow_html=True)

        with st.spinner("전략 A 실시간 백테스트 엔진 구동 중..."):
            try:
                bt_tickers_a = sorted(set(OFFENSIVE_A + DEFENSIVE_A + ["TIP", "QQQ"]))
                daily_px_a = get_daily_price_history_a(bt_tickers_a, start=bt_start_a)
                monthly_px_a = to_monthly_last_a(daily_px_a)
                bt_results_a = run_backtest_strategy_a_full(monthly_px_a)
                bt_ok_a = len(bt_results_a) > 0
            except Exception as e:
                st.error(f"전략 A 백테스트 데이터 로딩 중 오류가 발생했습니다: {e}")
                bt_ok_a = False

        if not bt_ok_a:
            st.warning("백테스트 데이터가 부족하거나 오류가 있습니다. 잠시 후 다시 시도해 주세요.")
        else:
            st.caption(f"시뮬레이션 기간: {bt_results_a['date'].iloc[0].strftime('%Y-%m')} ~ {bt_results_a['date'].iloc[-1].strftime('%Y-%m')}")

            total_days_a = (bt_results_a["date"].iloc[-1] - bt_results_a["date"].iloc[0]).days
            total_years_a = total_days_a / 365.25 if total_days_a > 0 else 1.0
            final_nav_a = bt_results_a["nav"].iloc[-1]

            cagr_a = ((final_nav_a / 100.0) ** (1 / total_years_a) - 1) * 100
            mdd_a = bt_results_a["drawdown"].min()

            bc1, bc2, bc3 = st.columns(3)
            bc1.metric("연환산 복리 수익률 (CAGR)", f"{cagr_a:.2f}%")
            bc2.metric("최대 낙폭 (MDD)", f"{mdd_a:.2f}%", delta_color="inverse")
            bc3.metric("최종 자산 가치 (NAV)", f"{final_nav_a:.1f}", "초기금 100 기준")

            st.markdown("##### 📈 자산 곡선 (NAV) 추이")
            chart_df_a = bt_results_a.copy()
            chart_df_a["date_str"] = chart_df_a["date"].dt.strftime("%Y-%m")

            qqq_ret_series_a = monthly_px_a["QQQ"].pct_change().reindex(bt_results_a["date"])
            chart_df_a["qqq_nav"] = (100 * (1 + qqq_ret_series_a.fillna(0)).cumprod()).values

            nav_color_scale_a = alt.Scale(domain=["전략A", "QQQ"], range=["#50ad6a", "#808080"])
            nav_long_a = chart_df_a.melt(
                id_vars="date_str", value_vars=["nav", "qqq_nav"], var_name="series", value_name="value"
            )
            nav_long_a["series"] = nav_long_a["series"].map({"nav": "전략A", "qqq_nav": "QQQ"})

            nav_chart_a = alt.Chart(nav_long_a).mark_line(size=2.5).encode(
                x=alt.X("date_str:N", sort=None, title="년-월"),
                y=alt.Y("value:Q", title="NAV (기준 100)"),
                color=alt.Color("series:N", scale=nav_color_scale_a, legend=alt.Legend(title=None, orient="bottom")),
                tooltip=[
                    alt.Tooltip("date_str:N", title="년-월"),
                    alt.Tooltip("series:N", title="구분"),
                    alt.Tooltip("value:Q", title="NAV", format=".1f"),
                ],
            ).properties(height=350)
            st.altair_chart(nav_chart_a, use_container_width=True)

            # ------------------------------------------------------------
            # 연도별 수익률 (Annual Returns) — 막대 차트
            # ------------------------------------------------------------
            st.markdown("##### 📊 연도별 수익률 (%)")
            yearly_df_a = bt_results_a.copy()
            yearly_df_a["year"] = yearly_df_a["date"].dt.year
            yearly_returns_a = (
                yearly_df_a.groupby("year")["monthly_return"]
                .apply(lambda x: (np.prod(1 + x / 100.0) - 1) * 100)
                .reset_index(name="annual_return")
            )
            yearly_returns_a["year_str"] = yearly_returns_a["year"].astype(str)
            yearly_returns_a["series"] = "전략A"
            year_sort_order_a = yearly_returns_a["year_str"].tolist()

            qqq_monthly_ret_a = monthly_px_a["QQQ"].pct_change().reindex(bt_results_a["date"]) * 100
            qqq_ret_df_a = pd.DataFrame({
                "date": bt_results_a["date"].values,
                "qqq_return": qqq_monthly_ret_a.values,
            })
            qqq_ret_df_a["year"] = pd.to_datetime(qqq_ret_df_a["date"]).dt.year
            qqq_yearly_a = (
                qqq_ret_df_a.groupby("year")["qqq_return"]
                .apply(lambda x: (np.prod(1 + x / 100.0) - 1) * 100)
                .reset_index(name="annual_return")
            )
            qqq_yearly_a["year_str"] = qqq_yearly_a["year"].astype(str)
            qqq_yearly_a["series"] = "QQQ"

            color_scale_a = alt.Scale(domain=["전략A", "QQQ"], range=["#50ad6a", "#808080"])

            annual_bar_a = alt.Chart(yearly_returns_a).mark_bar(size=28).encode(
                x=alt.X("year_str:N", title="연도", sort=year_sort_order_a),
                y=alt.Y("annual_return:Q", title="수익률 (%)"),
                color=alt.Color("series:N", scale=color_scale_a, legend=alt.Legend(title=None, orient="bottom")),
                tooltip=[
                    alt.Tooltip("year_str:N", title="연도"),
                    alt.Tooltip("annual_return:Q", title="수익률", format="+.2f"),
                ],
            )
            annual_labels_a = alt.Chart(yearly_returns_a).mark_text(
                dy=alt.expr("datum.annual_return >= 0 ? -8 : 14"), fontWeight="bold", fontSize=11, color="#0f172a"
            ).encode(
                x=alt.X("year_str:N", sort=year_sort_order_a),
                y=alt.Y("annual_return:Q"),
                text=alt.Text("annual_return:Q", format="+.1f"),
            )
            qqq_points_a = alt.Chart(qqq_yearly_a).mark_point(
                filled=True, size=110, stroke="white", strokeWidth=1.2
            ).encode(
                x=alt.X("year_str:N", sort=year_sort_order_a),
                y=alt.Y("annual_return:Q"),
                color=alt.Color("series:N", scale=color_scale_a, legend=alt.Legend(title=None, orient="bottom")),
                tooltip=[
                    alt.Tooltip("year_str:N", title="연도"),
                    alt.Tooltip("annual_return:Q", title="QQQ 수익률", format="+.2f"),
                ],
            )
            st.altair_chart(
                (annual_bar_a + annual_labels_a + qqq_points_a).properties(height=320),
                use_container_width=True,
            )

            # ------------------------------------------------------------
            # 월별 수익률 (Monthly Returns) — 히트맵 테이블
            # ------------------------------------------------------------
            st.markdown("##### 🗓️ 월별 수익률 (%)")
            monthly_df_a = bt_results_a.copy()
            monthly_df_a["year"] = monthly_df_a["date"].dt.year
            monthly_df_a["month"] = monthly_df_a["date"].dt.month

            month_labels_a = {1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
                              7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"}
            monthly_df_a["month_label"] = monthly_df_a["month"].map(month_labels_a)
            monthly_df_a["year_label"] = monthly_df_a["year"].astype(str)

            avg_by_month_a = monthly_df_a.groupby(["month", "month_label"])["monthly_return"].mean().reset_index()
            avg_by_month_a["year_label"] = "평균"

            heat_df_a = pd.concat([
                monthly_df_a[["year_label", "month", "month_label", "monthly_return"]],
                avg_by_month_a[["year_label", "month", "month_label", "monthly_return"]],
            ], ignore_index=True)

            year_sort_order_full_a = [str(y) for y in sorted(monthly_df_a["year"].unique())] + ["평균"]
            month_sort_order_a = [month_labels_a[m] for m in range(1, 13)]

            heat_rect_a = alt.Chart(heat_df_a).mark_rect(stroke="white", strokeWidth=1.5).encode(
                x=alt.X("month_label:N", title=None, sort=month_sort_order_a),
                y=alt.Y("year_label:N", title=None, sort=year_sort_order_full_a),
                color=alt.Color(
                    "monthly_return:Q",
                    scale=alt.Scale(
                        type="threshold",
                        domain=[-3.5, -2.5, -1.5, -0.5, 0.5, 1.5, 2.5, 3.5],
                        range=["#cf6265", "#e67f82", "#ecaaab", "#f6d4d5", "#fafbff",
                               "#d7e4da", "#accab2", "#82ae8b", "#599265"],
                    ),
                    legend=alt.Legend(title="수익률 (%)", orient="bottom", gradientLength=220),
                ),
                tooltip=[
                    alt.Tooltip("year_label:N", title="연도"),
                    alt.Tooltip("month_label:N", title="월"),
                    alt.Tooltip("monthly_return:Q", title="수익률", format="+.2f"),
                ],
            )
            heat_text_a = alt.Chart(heat_df_a).mark_text(fontSize=10, fontWeight="bold").encode(
                x=alt.X("month_label:N", sort=month_sort_order_a),
                y=alt.Y("year_label:N", sort=year_sort_order_full_a),
                text=alt.Text("monthly_return:Q", format="+.1f"),
                color=alt.value("#334155"),
            )
            st.altair_chart(
                (heat_rect_a + heat_text_a).properties(height=32 * len(year_sort_order_full_a) + 80),
                use_container_width=True,
            )

            st.markdown("##### 📉 낙폭 (Drawdown) 히스토리")
            dd_chart_a = alt.Chart(chart_df_a).mark_area(color="#fecaca", opacity=0.8).encode(
                x=alt.X("date_str:N", sort=None, title="년-월"),
                y=alt.Y("drawdown:Q", title="MDD (%)"),
                tooltip=["date_str", "drawdown"]
            ).properties(height=200)
            st.altair_chart(dd_chart_a, use_container_width=True)

            st.markdown("##### 🚨 포트폴리오 드로우다운 Top 10")
            dd_vals_a = bt_results_a["drawdown"].values
            dd_dates_a = bt_results_a["date"].values
            n_a = len(dd_vals_a)
            episodes_a = []
            i_ep_a = 0
            while i_ep_a < n_a:
                if dd_vals_a[i_ep_a] < -0.001:
                    start_i_a = i_ep_a
                    j_ep_a = i_ep_a
                    min_val_a = dd_vals_a[i_ep_a]
                    min_idx_a = i_ep_a
                    while j_ep_a < n_a and dd_vals_a[j_ep_a] < -0.001:
                        if dd_vals_a[j_ep_a] < min_val_a:
                            min_val_a = dd_vals_a[j_ep_a]
                            min_idx_a = j_ep_a
                        j_ep_a += 1
                    episodes_a.append({
                        "시작": pd.Timestamp(dd_dates_a[start_i_a]).strftime("%Y/%m"),
                        "종료": pd.Timestamp(dd_dates_a[min_idx_a]).strftime("%Y/%m"),
                        "드로우다운": min_val_a,
                    })
                    i_ep_a = j_ep_a
                else:
                    i_ep_a += 1

            episodes_a.sort(key=lambda x: x["드로우다운"])
            top10_a = episodes_a[:10]
            for idx, ep in enumerate(top10_a):
                ep["순위"] = idx + 1
                ep["드로우다운"] = f"{ep['드로우다운']:.1f}%"
            if top10_a:
                df_dd_top10_a = pd.DataFrame(top10_a)[["순위", "시작", "종료", "드로우다운"]]
                st.dataframe(df_dd_top10_a, use_container_width=True, hide_index=True)
            else:
                st.info("드로우다운 구간이 발견되지 않았습니다.")

            st.markdown("##### 🔻 폭락 시장 포트폴리오 성과")
            STRESS_PERIODS_A = [
                ("코로나 팬데믹", "2020-01-01", "2020-03-31"),
                ("2022 긴축 발작 (금리인상기)", "2022-01-01", "2022-10-31"),
                ("2018년 4분기 조정", "2018-10-01", "2018-12-31"),
            ]
            stress_rows_a = []
            for label_a, s_str_a, e_str_a in STRESS_PERIODS_A:
                s_ts_a, e_ts_a = pd.Timestamp(s_str_a), pd.Timestamp(e_str_a)
                mask_a = (bt_results_a["date"] >= s_ts_a) & (bt_results_a["date"] <= e_ts_a)
                sub_a = bt_results_a[mask_a]
                if len(sub_a) == 0:
                    continue
                port_cum_a = (np.prod(1 + sub_a["monthly_return"].values / 100.0) - 1) * 100
                bench_sub_ret_a = monthly_px_a["QQQ"].pct_change().reindex(sub_a["date"]).fillna(0.0)
                bench_cum_a = (np.prod(1 + bench_sub_ret_a.values) - 1) * 100
                stress_rows_a.append({
                    "스트레스 기간": label_a,
                    "시작": s_ts_a.strftime("%Y/%m"),
                    "종료": e_ts_a.strftime("%Y/%m"),
                    "포트폴리오 수익률": f"{port_cum_a:+.1f}%",
                    "QQQ 수익률": f"{bench_cum_a:+.1f}%",
                })
            if stress_rows_a:
                st.dataframe(pd.DataFrame(stress_rows_a), use_container_width=True, hide_index=True)
            else:
                st.info("선택한 시작일 범위 내 해당하는 폭락장 스트레스 기간 데이터가 없습니다. 시작일을 앞당겨 보세요.")

            st.markdown("##### 📊 주요 지표 비교 (vs QQQ)")

            def _fmt_pct_a(x):
                return f"{x:.1f}%" if x is not None and not (isinstance(x, float) and np.isnan(x)) else "데이터 부족"

            port_ret_arr_a = bt_results_a["monthly_return"].values
            bench_ret_arr_a = qqq_monthly_ret_a.values
            dd_arr_a = bt_results_a["drawdown"].values
            bench_nav_arr_a = chart_df_a["qqq_nav"].values
            bench_running_max_a = np.maximum.accumulate(bench_nav_arr_a)
            bench_dd_arr_a = (bench_nav_arr_a / bench_running_max_a - 1) * 100

            period_ret_a = (final_nav_a / 100.0 - 1) * 100
            bench_final_nav_a = bench_nav_arr_a[-1]
            bench_period_ret_a = (bench_final_nav_a / 100.0 - 1) * 100
            bench_cagr_a = ((bench_final_nav_a / 100.0) ** (1 / total_years_a) - 1) * 100

            last_date2_a = bt_results_a["date"].iloc[-1]
            current_year2_a = last_date2_a.year
            ytd_mask_a = bt_results_a["date"].dt.year == current_year2_a
            port_ytd_a = (np.prod(1 + bt_results_a.loc[ytd_mask_a, "monthly_return"].values / 100.0) - 1) * 100
            bench_ytd_a = (np.prod(1 + (bench_ret_arr_a[ytd_mask_a.values] / 100.0)) - 1) * 100

            win_months_a = int((port_ret_arr_a > 0).sum())
            bench_win_months_a = int((bench_ret_arr_a > 0).sum())
            total_months_a = len(port_ret_arr_a)

            mdd_idx_a = int(np.argmin(dd_arr_a))
            mdd_date_a = bt_results_a["date"].iloc[mdd_idx_a].strftime("%Y-%m")
            bench_mdd_idx_a = int(np.argmin(bench_dd_arr_a))
            bench_mdd_date_a = bt_results_a["date"].iloc[bench_mdd_idx_a].strftime("%Y-%m")

            def _trailing_a(arr, months):
                if len(arr) < months:
                    return None, None
                window = arr[-months:]
                cum = (np.prod(1 + window / 100.0) - 1) * 100
                ann_std = np.std(window, ddof=1) * np.sqrt(12) if len(window) > 1 else None
                return cum, ann_std

            ret_1y_a, std_1y_a = _trailing_a(port_ret_arr_a, 12)
            ret_3y_a, std_3y_a = _trailing_a(port_ret_arr_a, 36)
            ret_5y_a, std_5y_a = _trailing_a(port_ret_arr_a, 60)
            bench_ret_1y_a, bench_std_1y_a = _trailing_a(bench_ret_arr_a, 12)
            bench_ret_3y_a, bench_std_3y_a = _trailing_a(bench_ret_arr_a, 36)
            bench_ret_5y_a, bench_std_5y_a = _trailing_a(bench_ret_arr_a, 60)

            mean_m_a = np.mean(port_ret_arr_a) / 100.0
            std_m_a = np.std(port_ret_arr_a, ddof=1) / 100.0 if total_months_a > 1 else np.nan
            annual_vol_a = std_m_a * np.sqrt(12) * 100 if not np.isnan(std_m_a) else np.nan
            sharpe_a = (mean_m_a * 12) / (std_m_a * np.sqrt(12)) if std_m_a and std_m_a > 0 else np.nan

            downside_a = port_ret_arr_a[port_ret_arr_a < 0] / 100.0
            downside_std_a = np.std(downside_a, ddof=1) if len(downside_a) > 1 else np.nan
            sortino_a = (mean_m_a * 12) / (downside_std_a * np.sqrt(12)) if downside_std_a and downside_std_a > 0 else np.nan

            ulcer_a = np.sqrt(np.mean(dd_arr_a ** 2))
            upi_a = cagr_a / ulcer_a if ulcer_a > 0 else np.nan

            bench_mean_m_a = np.mean(bench_ret_arr_a) / 100.0
            bench_std_m_a = np.std(bench_ret_arr_a, ddof=1) / 100.0 if total_months_a > 1 else np.nan
            bench_annual_vol_a = bench_std_m_a * np.sqrt(12) * 100 if not np.isnan(bench_std_m_a) else np.nan
            bench_sharpe_a = (bench_mean_m_a * 12) / (bench_std_m_a * np.sqrt(12)) if bench_std_m_a and bench_std_m_a > 0 else np.nan

            bench_downside_a = bench_ret_arr_a[bench_ret_arr_a < 0] / 100.0
            bench_downside_std_a = np.std(bench_downside_a, ddof=1) if len(bench_downside_a) > 1 else np.nan
            bench_sortino_a = (bench_mean_m_a * 12) / (bench_downside_std_a * np.sqrt(12)) if bench_downside_std_a and bench_downside_std_a > 0 else np.nan

            bench_ulcer_a = np.sqrt(np.mean(bench_dd_arr_a ** 2))
            bench_upi_a = bench_cagr_a / bench_ulcer_a if bench_ulcer_a > 0 else np.nan

            alloc_list_a = bt_results_a["alloc"].tolist()
            monthly_turnovers_a = []
            prev_alloc_a = {}
            for alloc_d in alloc_list_a:
                all_tk_a = set(prev_alloc_a.keys()) | set(alloc_d.keys())
                diff_a = sum(abs(alloc_d.get(t, 0.0) - prev_alloc_a.get(t, 0.0)) for t in all_tk_a)
                monthly_turnovers_a.append(diff_a / 2.0)
                prev_alloc_a = alloc_d
            avg_turnover_a = np.mean(monthly_turnovers_a) if monthly_turnovers_a else 0.0
            annual_turnover_a = avg_turnover_a * 12

            metrics_rows_a = [
                ("기간 수익률", _fmt_pct_a(period_ret_a), _fmt_pct_a(bench_period_ret_a)),
                ("연환산 수익률 (CAGR)", _fmt_pct_a(cagr_a), _fmt_pct_a(bench_cagr_a)),
                ("이번 달 수익률", _fmt_pct_a(port_ret_arr_a[-1]), _fmt_pct_a(bench_ret_arr_a[-1])),
                ("올해 수익률 (YTD)", _fmt_pct_a(port_ytd_a), _fmt_pct_a(bench_ytd_a)),
                ("월 최고 수익률", _fmt_pct_a(port_ret_arr_a.max()), _fmt_pct_a(bench_ret_arr_a.max())),
                ("월 최저 수익률", _fmt_pct_a(port_ret_arr_a.min()), _fmt_pct_a(bench_ret_arr_a.min())),
                ("수익 월 비중", f"{win_months_a} / {total_months_a}", f"{bench_win_months_a} / {total_months_a}"),
                ("연 변동성", _fmt_pct_a(annual_vol_a), _fmt_pct_a(bench_annual_vol_a)),
                ("최대 낙폭 (MDD)", _fmt_pct_a(mdd_a), _fmt_pct_a(bench_dd_arr_a.min())),
                ("MDD 시점", mdd_date_a, bench_mdd_date_a),
                ("1년 수익률", _fmt_pct_a(ret_1y_a), _fmt_pct_a(bench_ret_1y_a)),
                ("3년 수익률", _fmt_pct_a(ret_3y_a), _fmt_pct_a(bench_ret_3y_a)),
                ("5년 수익률", _fmt_pct_a(ret_5y_a), _fmt_pct_a(bench_ret_5y_a)),
                ("1년 표준편차", _fmt_pct_a(std_1y_a), _fmt_pct_a(bench_std_1y_a)),
                ("3년 표준편차", _fmt_pct_a(std_3y_a), _fmt_pct_a(bench_std_3y_a)),
                ("5년 표준편차", _fmt_pct_a(std_5y_a), _fmt_pct_a(bench_std_5y_a)),
                ("샤프 지수", f"{sharpe_a:.2f}" if not np.isnan(sharpe_a) else "데이터 부족", f"{bench_sharpe_a:.2f}" if not np.isnan(bench_sharpe_a) else "데이터 부족"),
                ("소티노 지수", f"{sortino_a:.2f}" if not np.isnan(sortino_a) else "데이터 부족", f"{bench_sortino_a:.2f}" if not np.isnan(bench_sortino_a) else "데이터 부족"),
                ("UPI 지수", f"{upi_a:.2f}" if not np.isnan(upi_a) else "데이터 부족", f"{bench_upi_a:.2f}" if not np.isnan(bench_upi_a) else "데이터 부족"),
                ("연간 턴오버", f"{annual_turnover_a:.1f}%", "0.0%"),
            ]
            df_metrics_a = pd.DataFrame(metrics_rows_a, columns=["지표", "전략A", "QQQ"])
            st.dataframe(df_metrics_a, use_container_width=True, hide_index=True)
            st.caption(f"※ 기간: {bt_results_a['date'].iloc[0].strftime('%Y-%m')} ~ {bt_results_a['date'].iloc[-1].strftime('%Y-%m')} 야후 파이낸스 실시간 데이터 기준. 1/3/5년 지표는 해당 기간의 월 데이터가 충분할 때만 표시됩니다.")




            st.markdown("##### 🗓️ 월별 세부 리밸런싱 기록")
            display_bt_a = bt_results_a.copy()
            display_bt_a["연월"] = display_bt_a["date"].dt.strftime("%Y-%m")
            display_bt_a["월 수익률"] = display_bt_a["monthly_return"].apply(lambda x: f"{x:+.2f}%")
            display_bt_a["낙폭"] = display_bt_a["drawdown"].apply(lambda x: f"{x:.2f}%")
            display_bt_a["NAV"] = display_bt_a["nav"].apply(lambda x: f"{x:.1f}")

            st.dataframe(
                display_bt_a[["연월", "mode", "월 수익률", "weights_str", "NAV", "낙폭"]].iloc[::-1],
                use_container_width=True, hide_index=True
            )

    with c_b:
        st.header("⚡ 전략 B (공격형)")
        
        with st.expander("📖 전략 B 실행 명세서 (작동원칙)", expanded=False):
            st.markdown("""
            ### ⚡ 전략 B 핵심 구조 (레버리지 집중 투자형 카나리아 로테이션)
            채권 실질금리 모멘텀(TIP)의 방향 전환을 신호로 삼아, 3배 레버리지·인버스 자산군 중 단 1개 종목에 100% 집중 투자하는
            고변동성·고수익 추구형 시스템입니다.

            #### 1단계 — 카나리아 모멘텀 판독 (신호)
            * 매월 말 기준 TIP의 **1-3-6-9-12개월 단순평균 모멘텀 스코어**를 계산합니다.
            $$\\text{TIP 스코어} = \\frac{R_1 + R_3 + R_6 + R_9 + R_{12}}{5}$$
            * **공격 신호**: TIP 스코어 **양수(> 0)**
            * **방어 신호**: TIP 스코어 **음수 또는 0 이하(≤ 0)**

            #### 2단계 — 공격/방어 자산 매수 규칙
            * **공격 신호 (레버리지 자산 3개 중 선택)**
                * 대상 자산: `TYD, UPRO, VNQ`
                * 가중 모멘텀 스코어(최근 수익률에 높은 가중치 부여):
                $$\\text{Weighted Momentum} = \\frac{12 R_1 + 4 R_3 + 2 R_6 + R_{12}}{19}$$
                * 행동: 스코어 **1위 자산**에 **100% 몰빵 투자**합니다. (컷오프 없음)
            * **방어 신호 (인버스/방어 자산 3개 중 선택)**
                * 대상 자산: `DOG, RWM, TBF`
                * 1차 선정: **5개월 단순 수익률**이 가장 높은 자산을 후보로 선정합니다.
                * 예외 조건 (절대 모멘텀 컷오프): 선정된 후보의 **자체 1-3-6-9-12M 단순평균 모멘텀 스코어**가 **0 이하**이면, 해당 비중을 **현금(CASH) 100%**로 대체합니다. 0을 초과하면 해당 자산에 100% 투자합니다.

            #### 3단계 — 리밸런싱 주기
            * 매월 말 종가 기준으로 신호를 재판독하고, 포트폴리오를 전량 재배분합니다.

            > 실제 장기 성과(CAGR, MDD, 연도별/월별 수익률 등)는 아래 **🛑 전략 B 백테스트 성과 분석** 섹션에서 야후 파이낸스 실시간 데이터를 기반으로 항상 최신 상태로 자동 계산됩니다.
            """)

        st.markdown(
            "**1단계: 카나리아 신호 판단** \n"
            "TIP의 단순 모멘텀 스코어가 양수($> 0$)이면 공격, 음수($\\le 0$)이면 방어 모드로 진입합니다."
        )
        col1_b, col2_b = st.columns(2)
        col1_b.metric("TIP 현재가", f"${tip_current:.2f}")
        col2_b.metric("TIP 단순 모멘텀", f"{tip_score_b:.2f}%")
        
        if is_attack_b:
            st.success("⚔️ **현재 모드: 공격 자산 모드** - 레버리지 투자를 적극 실행합니다.")
            df_off_b = df_all[df_all["Ticker"].isin(OFFENSIVE_B)].copy()
            df_off_b = df_off_b.sort_values(by="B_공격스코어", ascending=False)
            
            st.write("**공격 자산 순위 (1-3-6-12M 가중 평균 모멘텀):**")
            st.caption("가중치 공식: $\\frac{12 \\cdot R_1 + 4 \\cdot R_3 + 2 \\cdot R_6 + R_{12}}{19}$")
            st.dataframe(
                df_off_b[["Ticker", "현재가", "1M", "3M", "6M", "12M", "B_공격스코어"]]
                .rename(columns={"B_공격스코어": "가중 모멘텀 스코어"}),
                use_container_width=True, hide_index=True
            )
            
            st.subheader("🎯 최종 포트폴리오 가이드 (100% 집중 투자)")
            for t, _ in alloc_b.items():
                p = data_dict.get(t, {}).get("현재가", 0.0)
                s = data_dict.get(t, {}).get("B_공격스코어", 0.0)
                st.info(f"🏆 **{t}** : 비중 **100%** (현재가: ${p:.2f}, 가중 모멘텀: {s:.2f}%)")
        else:
            st.warning("🛡️ **현재 모드: 방어 자산 모드** - 인버스 자산을 활용하여 하락장에 방어 베팅합니다.")
            df_def_b = df_all[df_all["Ticker"].isin(DEFENSIVE_B)].copy()
            df_def_b = df_def_b.sort_values(by="5M", ascending=False)
            
            st.write("**방어 자산 순위 (5개월 단순 수익률 기준):**")
            st.dataframe(
                df_def_b[["Ticker", "현재가", "5M", "B_단순모멘텀"]]
                .rename(columns={"5M": "5개월 수익률", "B_단순모멘텀": "자체 단순모멘텀"}),
                use_container_width=True, hide_index=True
            )
            
            st.subheader("🎯 최종 포트폴리오 가이드")
            for t, _ in alloc_b.items():
                if t == "CASH (현금)":
                    st.error("🚨 **현금(CASH) 보유 : 비중 100%**")
                else:
                    p = data_dict.get(t, {}).get("현재가", 0.0)
                    s = data_dict.get(t, {}).get("B_단순모멘텀", 0.0)
                    st.info(f"🏆 **{t}** : 비중 **100%** (현재가: ${p:.2f}, 자체 모멘텀: {s:.2f}%)")

        st.markdown("---")
        st.markdown("### 🛑 전략 B 백테스트 성과 분석")

        with st.container():
            st.markdown('<div class="control-panel">', unsafe_allow_html=True)
            st.markdown('<div class="control-header">⚙️ 데이터 범위 및 리스크 관리 설정</div>', unsafe_allow_html=True)
            bt_start_label_b = st.selectbox(
                "분석 및 백테스트 시작일",
                ["2018-01-01 (코로나 및 금리인상기 포함)", "2015-01-01 (장기 검증)", "2020-01-01 (최근 트렌드)"],
                index=1,
                key="bt_start_select_b"
            )
            bt_start_b = bt_start_label_b.split(" ")[0]
            st.caption("선택한 시작일 기준으로 전략 B 백테스트 시뮬레이션(NAV, 연도별/월별 수익률, 낙폭, 리밸런싱 기록)이 즉시 재계산됩니다.")
            st.markdown('</div>', unsafe_allow_html=True)

        with st.spinner("전략 B 실시간 백테스트 엔진 구동 중..."):
            try:
                bt_tickers_b = sorted(set(OFFENSIVE_B + DEFENSIVE_B + ["TIP", "QQQ"]))
                daily_px_b = get_daily_price_history_a(bt_tickers_b, start=bt_start_b)
                monthly_px_b = to_monthly_last_a(daily_px_b)
                bt_results_b = run_backtest_strategy_b_full(monthly_px_b)
                bt_ok_b = len(bt_results_b) > 0
            except Exception as e:
                st.error(f"전략 B 백테스트 데이터 로딩 중 오류가 발생했습니다: {e}")
                bt_ok_b = False

        if not bt_ok_b:
            st.warning("백테스트 데이터가 부족하거나 오류가 있습니다. 잠시 후 다시 시도해 주세요.")
        else:
            st.caption(f"시뮬레이션 기간: {bt_results_b['date'].iloc[0].strftime('%Y-%m')} ~ {bt_results_b['date'].iloc[-1].strftime('%Y-%m')}")

            total_days_b = (bt_results_b["date"].iloc[-1] - bt_results_b["date"].iloc[0]).days
            total_years_b = total_days_b / 365.25 if total_days_b > 0 else 1.0
            final_nav_b = bt_results_b["nav"].iloc[-1]

            cagr_b = ((final_nav_b / 100.0) ** (1 / total_years_b) - 1) * 100
            mdd_b = bt_results_b["drawdown"].min()

            bbc1, bbc2, bbc3 = st.columns(3)
            bbc1.metric("연환산 복리 수익률 (CAGR)", f"{cagr_b:.2f}%")
            bbc2.metric("최대 낙폭 (MDD)", f"{mdd_b:.2f}%", delta_color="inverse")
            bbc3.metric("최종 자산 가치 (NAV)", f"{final_nav_b:.1f}", "초기금 100 기준")

            st.markdown("##### 📈 자산 곡선 (NAV) 추이")
            chart_df_b = bt_results_b.copy()
            chart_df_b["date_str"] = chart_df_b["date"].dt.strftime("%Y-%m")

            qqq_ret_series_b = monthly_px_b["QQQ"].pct_change().reindex(bt_results_b["date"])
            chart_df_b["qqq_nav"] = (100 * (1 + qqq_ret_series_b.fillna(0)).cumprod()).values

            nav_color_scale_b = alt.Scale(domain=["전략B", "QQQ"], range=["#f97316", "#808080"])
            nav_long_b = chart_df_b.melt(
                id_vars="date_str", value_vars=["nav", "qqq_nav"], var_name="series", value_name="value"
            )
            nav_long_b["series"] = nav_long_b["series"].map({"nav": "전략B", "qqq_nav": "QQQ"})

            nav_chart_b = alt.Chart(nav_long_b).mark_line(size=2.5).encode(
                x=alt.X("date_str:N", sort=None, title="년-월"),
                y=alt.Y("value:Q", title="NAV (기준 100)"),
                color=alt.Color("series:N", scale=nav_color_scale_b, legend=alt.Legend(title=None, orient="bottom")),
                tooltip=[
                    alt.Tooltip("date_str:N", title="년-월"),
                    alt.Tooltip("series:N", title="구분"),
                    alt.Tooltip("value:Q", title="NAV", format=".1f"),
                ],
            ).properties(height=350)
            st.altair_chart(nav_chart_b, use_container_width=True)

            # ------------------------------------------------------------
            # 연도별 수익률 (Annual Returns) — 막대 차트
            # ------------------------------------------------------------
            st.markdown("##### 📊 연도별 수익률 (%)")
            yearly_df_b = bt_results_b.copy()
            yearly_df_b["year"] = yearly_df_b["date"].dt.year
            yearly_returns_b = (
                yearly_df_b.groupby("year")["monthly_return"]
                .apply(lambda x: (np.prod(1 + x / 100.0) - 1) * 100)
                .reset_index(name="annual_return")
            )
            yearly_returns_b["year_str"] = yearly_returns_b["year"].astype(str)
            yearly_returns_b["series"] = "전략B"
            year_sort_order_b = yearly_returns_b["year_str"].tolist()

            qqq_monthly_ret_b = monthly_px_b["QQQ"].pct_change().reindex(bt_results_b["date"]) * 100
            qqq_ret_df_b = pd.DataFrame({
                "date": bt_results_b["date"].values,
                "qqq_return": qqq_monthly_ret_b.values,
            })
            qqq_ret_df_b["year"] = pd.to_datetime(qqq_ret_df_b["date"]).dt.year
            qqq_yearly_b = (
                qqq_ret_df_b.groupby("year")["qqq_return"]
                .apply(lambda x: (np.prod(1 + x / 100.0) - 1) * 100)
                .reset_index(name="annual_return")
            )
            qqq_yearly_b["year_str"] = qqq_yearly_b["year"].astype(str)
            qqq_yearly_b["series"] = "QQQ"

            color_scale_b = alt.Scale(domain=["전략B", "QQQ"], range=["#f97316", "#808080"])

            annual_bar_b = alt.Chart(yearly_returns_b).mark_bar(size=28).encode(
                x=alt.X("year_str:N", title="연도", sort=year_sort_order_b),
                y=alt.Y("annual_return:Q", title="수익률 (%)"),
                color=alt.Color("series:N", scale=color_scale_b, legend=alt.Legend(title=None, orient="bottom")),
                tooltip=[
                    alt.Tooltip("year_str:N", title="연도"),
                    alt.Tooltip("annual_return:Q", title="수익률", format="+.2f"),
                ],
            )
            annual_labels_b = alt.Chart(yearly_returns_b).mark_text(
                dy=alt.expr("datum.annual_return >= 0 ? -8 : 14"), fontWeight="bold", fontSize=11, color="#0f172a"
            ).encode(
                x=alt.X("year_str:N", sort=year_sort_order_b),
                y=alt.Y("annual_return:Q"),
                text=alt.Text("annual_return:Q", format="+.1f"),
            )
            qqq_points_b = alt.Chart(qqq_yearly_b).mark_point(
                filled=True, size=110, stroke="white", strokeWidth=1.2
            ).encode(
                x=alt.X("year_str:N", sort=year_sort_order_b),
                y=alt.Y("annual_return:Q"),
                color=alt.Color("series:N", scale=color_scale_b, legend=alt.Legend(title=None, orient="bottom")),
                tooltip=[
                    alt.Tooltip("year_str:N", title="연도"),
                    alt.Tooltip("annual_return:Q", title="QQQ 수익률", format="+.2f"),
                ],
            )
            st.altair_chart(
                (annual_bar_b + annual_labels_b + qqq_points_b).properties(height=320),
                use_container_width=True,
            )

            # ------------------------------------------------------------
            # 월별 수익률 (Monthly Returns) — 히트맵 테이블
            # ------------------------------------------------------------
            st.markdown("##### 🗓️ 월별 수익률 (%)")
            monthly_df_b = bt_results_b.copy()
            monthly_df_b["year"] = monthly_df_b["date"].dt.year
            monthly_df_b["month"] = monthly_df_b["date"].dt.month

            month_labels_b = {1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
                              7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"}
            monthly_df_b["month_label"] = monthly_df_b["month"].map(month_labels_b)
            monthly_df_b["year_label"] = monthly_df_b["year"].astype(str)

            avg_by_month_b = monthly_df_b.groupby(["month", "month_label"])["monthly_return"].mean().reset_index()
            avg_by_month_b["year_label"] = "평균"

            heat_df_b = pd.concat([
                monthly_df_b[["year_label", "month", "month_label", "monthly_return"]],
                avg_by_month_b[["year_label", "month", "month_label", "monthly_return"]],
            ], ignore_index=True)

            year_sort_order_full_b = [str(y) for y in sorted(monthly_df_b["year"].unique())] + ["평균"]
            month_sort_order_b = [month_labels_b[m] for m in range(1, 13)]

            heat_rect_b = alt.Chart(heat_df_b).mark_rect(stroke="white", strokeWidth=1.5).encode(
                x=alt.X("month_label:N", title=None, sort=month_sort_order_b),
                y=alt.Y("year_label:N", title=None, sort=year_sort_order_full_b),
                color=alt.Color(
                    "monthly_return:Q",
                    scale=alt.Scale(
                        type="threshold",
                        domain=[-3.5, -2.5, -1.5, -0.5, 0.5, 1.5, 2.5, 3.5],
                        range=["#cf6265", "#e67f82", "#ecaaab", "#f6d4d5", "#fafbff",
                               "#d7e4da", "#accab2", "#82ae8b", "#599265"],
                    ),
                    legend=alt.Legend(title="수익률 (%)", orient="bottom", gradientLength=220),
                ),
                tooltip=[
                    alt.Tooltip("year_label:N", title="연도"),
                    alt.Tooltip("month_label:N", title="월"),
                    alt.Tooltip("monthly_return:Q", title="수익률", format="+.2f"),
                ],
            )
            heat_text_b = alt.Chart(heat_df_b).mark_text(fontSize=10, fontWeight="bold").encode(
                x=alt.X("month_label:N", sort=month_sort_order_b),
                y=alt.Y("year_label:N", sort=year_sort_order_full_b),
                text=alt.Text("monthly_return:Q", format="+.1f"),
                color=alt.value("#334155"),
            )
            st.altair_chart(
                (heat_rect_b + heat_text_b).properties(height=32 * len(year_sort_order_full_b) + 80),
                use_container_width=True,
            )

            st.markdown("##### 📉 낙폭 (Drawdown) 히스토리")
            dd_chart_b = alt.Chart(chart_df_b).mark_area(color="#fecaca", opacity=0.8).encode(
                x=alt.X("date_str:N", sort=None, title="년-월"),
                y=alt.Y("drawdown:Q", title="MDD (%)"),
                tooltip=["date_str", "drawdown"]
            ).properties(height=200)
            st.altair_chart(dd_chart_b, use_container_width=True)

            st.markdown("##### 🚨 포트폴리오 드로우다운 Top 10")
            dd_vals_b = bt_results_b["drawdown"].values
            dd_dates_b = bt_results_b["date"].values
            n_b = len(dd_vals_b)
            episodes_b = []
            i_ep_b = 0
            while i_ep_b < n_b:
                if dd_vals_b[i_ep_b] < -0.001:
                    start_i_b = i_ep_b
                    j_ep_b = i_ep_b
                    min_val_b = dd_vals_b[i_ep_b]
                    min_idx_b = i_ep_b
                    while j_ep_b < n_b and dd_vals_b[j_ep_b] < -0.001:
                        if dd_vals_b[j_ep_b] < min_val_b:
                            min_val_b = dd_vals_b[j_ep_b]
                            min_idx_b = j_ep_b
                        j_ep_b += 1
                    episodes_b.append({
                        "시작": pd.Timestamp(dd_dates_b[start_i_b]).strftime("%Y/%m"),
                        "종료": pd.Timestamp(dd_dates_b[min_idx_b]).strftime("%Y/%m"),
                        "드로우다운": min_val_b,
                    })
                    i_ep_b = j_ep_b
                else:
                    i_ep_b += 1

            episodes_b.sort(key=lambda x: x["드로우다운"])
            top10_b = episodes_b[:10]
            for idx, ep in enumerate(top10_b):
                ep["순위"] = idx + 1
                ep["드로우다운"] = f"{ep['드로우다운']:.1f}%"
            if top10_b:
                df_dd_top10_b = pd.DataFrame(top10_b)[["순위", "시작", "종료", "드로우다운"]]
                st.dataframe(df_dd_top10_b, use_container_width=True, hide_index=True)
            else:
                st.info("드로우다운 구간이 발견되지 않았습니다.")

            st.markdown("##### 🔻 폭락 시장 포트폴리오 성과")
            STRESS_PERIODS_B = [
                ("코로나 팬데믹", "2020-01-01", "2020-03-31"),
                ("2022 긴축 발작 (금리인상기)", "2022-01-01", "2022-10-31"),
                ("2018년 4분기 조정", "2018-10-01", "2018-12-31"),
            ]
            stress_rows_b = []
            for label_b, s_str_b, e_str_b in STRESS_PERIODS_B:
                s_ts_b, e_ts_b = pd.Timestamp(s_str_b), pd.Timestamp(e_str_b)
                mask_b = (bt_results_b["date"] >= s_ts_b) & (bt_results_b["date"] <= e_ts_b)
                sub_b = bt_results_b[mask_b]
                if len(sub_b) == 0:
                    continue
                port_cum_b = (np.prod(1 + sub_b["monthly_return"].values / 100.0) - 1) * 100
                bench_sub_ret_b = monthly_px_b["QQQ"].pct_change().reindex(sub_b["date"]).fillna(0.0)
                bench_cum_b = (np.prod(1 + bench_sub_ret_b.values) - 1) * 100
                stress_rows_b.append({
                    "스트레스 기간": label_b,
                    "시작": s_ts_b.strftime("%Y/%m"),
                    "종료": e_ts_b.strftime("%Y/%m"),
                    "포트폴리오 수익률": f"{port_cum_b:+.1f}%",
                    "QQQ 수익률": f"{bench_cum_b:+.1f}%",
                })
            if stress_rows_b:
                st.dataframe(pd.DataFrame(stress_rows_b), use_container_width=True, hide_index=True)
            else:
                st.info("선택한 시작일 범위 내 해당하는 폭락장 스트레스 기간 데이터가 없습니다. 시작일을 앞당겨 보세요.")

            st.markdown("##### 📊 주요 지표 비교 (vs QQQ)")

            def _fmt_pct_b(x):
                return f"{x:.1f}%" if x is not None and not (isinstance(x, float) and np.isnan(x)) else "데이터 부족"

            port_ret_arr_b = bt_results_b["monthly_return"].values
            bench_ret_arr_b = qqq_monthly_ret_b.values
            dd_arr_b = bt_results_b["drawdown"].values
            bench_nav_arr_b = chart_df_b["qqq_nav"].values
            bench_running_max_b = np.maximum.accumulate(bench_nav_arr_b)
            bench_dd_arr_b = (bench_nav_arr_b / bench_running_max_b - 1) * 100

            period_ret_b = (final_nav_b / 100.0 - 1) * 100
            bench_final_nav_b = bench_nav_arr_b[-1]
            bench_period_ret_b = (bench_final_nav_b / 100.0 - 1) * 100
            bench_cagr_b = ((bench_final_nav_b / 100.0) ** (1 / total_years_b) - 1) * 100

            last_date2_b = bt_results_b["date"].iloc[-1]
            current_year2_b = last_date2_b.year
            ytd_mask_b = bt_results_b["date"].dt.year == current_year2_b
            port_ytd_b = (np.prod(1 + bt_results_b.loc[ytd_mask_b, "monthly_return"].values / 100.0) - 1) * 100
            bench_ytd_b = (np.prod(1 + (bench_ret_arr_b[ytd_mask_b.values] / 100.0)) - 1) * 100

            win_months_b = int((port_ret_arr_b > 0).sum())
            bench_win_months_b = int((bench_ret_arr_b > 0).sum())
            total_months_b = len(port_ret_arr_b)

            mdd_idx_b = int(np.argmin(dd_arr_b))
            mdd_date_b = bt_results_b["date"].iloc[mdd_idx_b].strftime("%Y-%m")
            bench_mdd_idx_b = int(np.argmin(bench_dd_arr_b))
            bench_mdd_date_b = bt_results_b["date"].iloc[bench_mdd_idx_b].strftime("%Y-%m")

            def _trailing_b(arr, months):
                if len(arr) < months:
                    return None, None
                window = arr[-months:]
                cum = (np.prod(1 + window / 100.0) - 1) * 100
                ann_std = np.std(window, ddof=1) * np.sqrt(12) if len(window) > 1 else None
                return cum, ann_std

            ret_1y_b, std_1y_b = _trailing_b(port_ret_arr_b, 12)
            ret_3y_b, std_3y_b = _trailing_b(port_ret_arr_b, 36)
            ret_5y_b, std_5y_b = _trailing_b(port_ret_arr_b, 60)
            bench_ret_1y_b, bench_std_1y_b = _trailing_b(bench_ret_arr_b, 12)
            bench_ret_3y_b, bench_std_3y_b = _trailing_b(bench_ret_arr_b, 36)
            bench_ret_5y_b, bench_std_5y_b = _trailing_b(bench_ret_arr_b, 60)

            mean_m_b = np.mean(port_ret_arr_b) / 100.0
            std_m_b = np.std(port_ret_arr_b, ddof=1) / 100.0 if total_months_b > 1 else np.nan
            annual_vol_b = std_m_b * np.sqrt(12) * 100 if not np.isnan(std_m_b) else np.nan
            sharpe_b = (mean_m_b * 12) / (std_m_b * np.sqrt(12)) if std_m_b and std_m_b > 0 else np.nan

            downside_b = port_ret_arr_b[port_ret_arr_b < 0] / 100.0
            downside_std_b = np.std(downside_b, ddof=1) if len(downside_b) > 1 else np.nan
            sortino_b = (mean_m_b * 12) / (downside_std_b * np.sqrt(12)) if downside_std_b and downside_std_b > 0 else np.nan

            ulcer_b = np.sqrt(np.mean(dd_arr_b ** 2))
            upi_b = cagr_b / ulcer_b if ulcer_b > 0 else np.nan

            bench_mean_m_b = np.mean(bench_ret_arr_b) / 100.0
            bench_std_m_b = np.std(bench_ret_arr_b, ddof=1) / 100.0 if total_months_b > 1 else np.nan
            bench_annual_vol_b = bench_std_m_b * np.sqrt(12) * 100 if not np.isnan(bench_std_m_b) else np.nan
            bench_sharpe_b = (bench_mean_m_b * 12) / (bench_std_m_b * np.sqrt(12)) if bench_std_m_b and bench_std_m_b > 0 else np.nan

            bench_downside_b = bench_ret_arr_b[bench_ret_arr_b < 0] / 100.0
            bench_downside_std_b = np.std(bench_downside_b, ddof=1) if len(bench_downside_b) > 1 else np.nan
            bench_sortino_b = (bench_mean_m_b * 12) / (bench_downside_std_b * np.sqrt(12)) if bench_downside_std_b and bench_downside_std_b > 0 else np.nan

            bench_ulcer_b = np.sqrt(np.mean(bench_dd_arr_b ** 2))
            bench_upi_b = bench_cagr_b / bench_ulcer_b if bench_ulcer_b > 0 else np.nan

            alloc_list_b = bt_results_b["alloc"].tolist()
            monthly_turnovers_b = []
            prev_alloc_b = {}
            for alloc_d in alloc_list_b:
                all_tk_b = set(prev_alloc_b.keys()) | set(alloc_d.keys())
                diff_b = sum(abs(alloc_d.get(t, 0.0) - prev_alloc_b.get(t, 0.0)) for t in all_tk_b)
                monthly_turnovers_b.append(diff_b / 2.0)
                prev_alloc_b = alloc_d
            avg_turnover_b = np.mean(monthly_turnovers_b) if monthly_turnovers_b else 0.0
            annual_turnover_b = avg_turnover_b * 12

            metrics_rows_b = [
                ("기간 수익률", _fmt_pct_b(period_ret_b), _fmt_pct_b(bench_period_ret_b)),
                ("연환산 수익률 (CAGR)", _fmt_pct_b(cagr_b), _fmt_pct_b(bench_cagr_b)),
                ("이번 달 수익률", _fmt_pct_b(port_ret_arr_b[-1]), _fmt_pct_b(bench_ret_arr_b[-1])),
                ("올해 수익률 (YTD)", _fmt_pct_b(port_ytd_b), _fmt_pct_b(bench_ytd_b)),
                ("월 최고 수익률", _fmt_pct_b(port_ret_arr_b.max()), _fmt_pct_b(bench_ret_arr_b.max())),
                ("월 최저 수익률", _fmt_pct_b(port_ret_arr_b.min()), _fmt_pct_b(bench_ret_arr_b.min())),
                ("수익 월 비중", f"{win_months_b} / {total_months_b}", f"{bench_win_months_b} / {total_months_b}"),
                ("연 변동성", _fmt_pct_b(annual_vol_b), _fmt_pct_b(bench_annual_vol_b)),
                ("최대 낙폭 (MDD)", _fmt_pct_b(mdd_b), _fmt_pct_b(bench_dd_arr_b.min())),
                ("MDD 시점", mdd_date_b, bench_mdd_date_b),
                ("1년 수익률", _fmt_pct_b(ret_1y_b), _fmt_pct_b(bench_ret_1y_b)),
                ("3년 수익률", _fmt_pct_b(ret_3y_b), _fmt_pct_b(bench_ret_3y_b)),
                ("5년 수익률", _fmt_pct_b(ret_5y_b), _fmt_pct_b(bench_ret_5y_b)),
                ("1년 표준편차", _fmt_pct_b(std_1y_b), _fmt_pct_b(bench_std_1y_b)),
                ("3년 표준편차", _fmt_pct_b(std_3y_b), _fmt_pct_b(bench_std_3y_b)),
                ("5년 표준편차", _fmt_pct_b(std_5y_b), _fmt_pct_b(bench_std_5y_b)),
                ("샤프 지수", f"{sharpe_b:.2f}" if not np.isnan(sharpe_b) else "데이터 부족", f"{bench_sharpe_b:.2f}" if not np.isnan(bench_sharpe_b) else "데이터 부족"),
                ("소티노 지수", f"{sortino_b:.2f}" if not np.isnan(sortino_b) else "데이터 부족", f"{bench_sortino_b:.2f}" if not np.isnan(bench_sortino_b) else "데이터 부족"),
                ("UPI 지수", f"{upi_b:.2f}" if not np.isnan(upi_b) else "데이터 부족", f"{bench_upi_b:.2f}" if not np.isnan(bench_upi_b) else "데이터 부족"),
                ("연간 턴오버", f"{annual_turnover_b:.1f}%", "0.0%"),
            ]
            df_metrics_b = pd.DataFrame(metrics_rows_b, columns=["지표", "전략B", "QQQ"])
            st.dataframe(df_metrics_b, use_container_width=True, hide_index=True)
            st.caption(f"※ 기간: {bt_results_b['date'].iloc[0].strftime('%Y-%m')} ~ {bt_results_b['date'].iloc[-1].strftime('%Y-%m')} 야후 파이낸스 실시간 데이터 기준. 1/3/5년 지표는 해당 기간의 월 데이터가 충분할 때만 표시됩니다.")




            st.markdown("##### 🗓️ 월별 세부 리밸런싱 기록")
            display_bt_b = bt_results_b.copy()
            display_bt_b["연월"] = display_bt_b["date"].dt.strftime("%Y-%m")
            display_bt_b["월 수익률"] = display_bt_b["monthly_return"].apply(lambda x: f"{x:+.2f}%")
            display_bt_b["낙폭"] = display_bt_b["drawdown"].apply(lambda x: f"{x:.2f}%")
            display_bt_b["NAV"] = display_bt_b["nav"].apply(lambda x: f"{x:.1f}")

            st.dataframe(
                display_bt_b[["연월", "mode", "월 수익률", "weights_str", "NAV", "낙폭"]].iloc[::-1],
                use_container_width=True, hide_index=True
            )

    with c_c:
        st.header("🔄 전략 C (섹터로테이션)")
        
        with st.expander("📖 전략 C 실행 명세서 (작동원칙)", expanded=False):
            st.markdown("""
            ### 🔄 전략 C 핵심 구조 (S&P 500 배당수익률 기반 섹터 로테이션)
            채권 지표 대신 **S&P 500 실시간 배당수익률**을 카나리아 지표로 사용하여 주식시장의 저평가/과열 국면을 판독하고,
            국면에 맞춰 주도 섹터 또는 원자재 방어자산 중 1개 종목에 집중 투자합니다.

            #### 1단계 — 배당수익률 필터링 (신호)
            * S&P 500(SPY)의 최근 12개월 배당 합계를 현재가로 나눈 **실시간 배당수익률**을 산출합니다.
            * **공격 신호**: 배당수익률 **1.33% 초과** (시장 저평가 국면)
            * **방어 신호**: 배당수익률 **1.33% 이하** (시장 과열 국면)

            #### 2단계 — 공격/방어 자산 매수 규칙
            * **공격 신호 (주도 섹터 자산 중 선택)**
                * 대상 자산: `FDN, LIT, SMH, XLE, IGV, QQQM, XLU`
                * 모멘텀 스코어: `(1M + 3M + 6M + 12M) 수익률 단순평균`
                * 행동: 스코어 **1위 섹터**에 **100% 집중 투자**합니다. (컷오프 없음)
            * **방어 신호 (원자재·방어 자산 중 선택)**
                * 대상 자산: `GLD, PDBC, OILK, SHY, TLT`
                * 모멘텀 스코어: `(1M + 3M + 6M + 9M + 12M) 수익률 단순평균`
                * 행동: 스코어 **1위 자산**에 **100% 대피**합니다.
                * 예외 조건 (절대 모멘텀 컷오프): 1위 자산의 스코어마저 **0 이하**이면 **현금(CASH) 100%**로 대체합니다.

            #### 3단계 — 리밸런싱 주기
            * 매월 말 배당수익률과 모멘텀 스코어를 재판독하여 포트폴리오를 전량 재배분합니다.

            > 실제 장기 성과(CAGR, MDD, 연도별/월별 수익률 등)는 아래 **🛑 전략 C 백테스트 성과 분석** 섹션에서 야후 파이낸스 실시간 데이터를 기반으로 항상 최신 상태로 자동 계산됩니다.
            """)

        st.markdown(
            "**1단계: 카나리아 신호 판단 (S&P 500 배당수익률)** \n"
            "배당수익률이 **1.33%** 초과 시 주식 저평가로 판단하여 공격 모드, 이하일 경우 시장 과열로 판단하여 방어 모드로 진입합니다."
        )
        
        st.markdown(f"""
        <div class="control-panel">
            <div class="control-header">📊 S&P 500 (SPY) 실시간 배당수익률 모니터링</div>
            <div class="control-subheader">
                야후 파이낸스(yfinance) API로부터 소수 및 백분율 단위를 실시간으로 정합 보정하여 산출한 데이터입니다.<br/>
                • <b>실시간 배당수익률: {realtime_dy:.2f}%</b><br/>
                • <b>모드 분류 기준선: 1.33%</b> (초과 시 공격 모드 / 이하 시 방어 모드)
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if is_attack_c:
            st.success(f"🔥 **현재 모드: 공격 자산 모드** (실시간 배당수익률 {realtime_dy:.2f}% > 1.33%) - 시장 저평가 국면으로 주식을 매수합니다.")
            df_off_c = df_all[df_all["Ticker"].isin(OFFENSIVE_C)].copy()
            df_off_c = df_off_c.sort_values(by="A_공격스코어", ascending=False)
            
            st.write("**주도 섹터 후보 순위 (1-3-6-12M 단순 평균 모멘텀):**")
            st.dataframe(
                df_off_c[["Ticker", "현재가", "1M", "3M", "6M", "12M", "A_공격스코어"]]
                .rename(columns={"A_공격스코어": "모멘텀 스코어"}),
                use_container_width=True, hide_index=True
            )
            
            st.subheader("🎯 최종 포트폴리오 가이드 (100% 단일 섹터 투자)")
            for t, _ in alloc_c.items():
                p = data_dict.get(t, {}).get("현재가", 0.0)
                s = data_dict.get(t, {}).get("A_공격스코어", 0.0)
                st.info(f"🏆 **{t}** : 비중 **100%** (현재가: ${p:.2f}, 모멘텀: {s:.2f}%)")
        else:
            st.warning(f"🛡️ **현재 모드: 방어 자산 모드** (실시간 배당수익률 {realtime_dy:.2f}% <= 1.33%) - 시장 과열 국면으로 원자재 자산으로 대피합니다.")
            df_def_c = df_all[df_all["Ticker"].isin(DEFENSIVE_C)].copy()
            df_def_c = df_def_c.sort_values(by="A_방어스코어", ascending=False)
            
            st.write("**원자재 방어 자산 순위 (1-3-6-9-12M 단순 평균 모멘텀):**")
            st.dataframe(
                df_def_c[["Ticker", "현재가", "1M", "3M", "6M", "9M", "12M", "A_방어스코어"]]
                .rename(columns={"A_방어스코어": "모멘텀 스코어"}),
                use_container_width=True, hide_index=True
            )
            
            st.subheader("🎯 최종 포트폴리오 가이드")
            for t, _ in alloc_c.items():
                if t == "CASH (현금)":
                    st.error("🚨 **현금(CASH) 보유 : 비중 100%**")
                else:
                    p = data_dict.get(t, {}).get("현재가", 0.0)
                    s = data_dict.get(t, {}).get("A_방어스코어", 0.0)
                    st.info(f"🏆 **{t}** : 비중 **100%** (현재가: ${p:.2f}, 모멘텀: {s:.2f}%)")

        st.markdown("---")
        st.markdown("### 🛑 전략 C 백테스트 성과 분석")

        with st.container():
            st.markdown('<div class="control-panel">', unsafe_allow_html=True)
            st.markdown('<div class="control-header">⚙️ 데이터 범위 및 리스크 관리 설정</div>', unsafe_allow_html=True)
            bt_start_label_c = st.selectbox(
                "분석 및 백테스트 시작일",
                ["2018-01-01 (코로나 및 금리인상기 포함)", "2015-01-01 (장기 검증)", "2020-01-01 (최근 트렌드)"],
                index=1,
                key="bt_start_select_c"
            )
            bt_start_c = bt_start_label_c.split(" ")[0]
            st.caption("선택한 시작일 기준으로 전략 C 백테스트 시뮬레이션(NAV, 연도별/월별 수익률, 낙폭, 리밸런싱 기록)이 즉시 재계산됩니다.")
            st.markdown('</div>', unsafe_allow_html=True)

        with st.spinner("전략 C 실시간 백테스트 엔진 구동 중..."):
            try:
                bt_tickers_c = sorted(set(OFFENSIVE_C + DEFENSIVE_C + ["SPY", "QQQ"]))
                daily_px_c = get_daily_price_history_a(bt_tickers_c, start=bt_start_c)
                monthly_px_c = to_monthly_last_a(daily_px_c)
                spy_divs_c = get_spy_dividend_history()
                bt_results_c = run_backtest_strategy_c_full(monthly_px_c, spy_divs_c)
                bt_ok_c = len(bt_results_c) > 0
            except Exception as e:
                st.error(f"전략 C 백테스트 데이터 로딩 중 오류가 발생했습니다: {e}")
                bt_ok_c = False

        if not bt_ok_c:
            st.warning("백테스트 데이터가 부족하거나 오류가 있습니다. 잠시 후 다시 시도해 주세요.")
        else:
            st.caption(f"시뮬레이션 기간: {bt_results_c['date'].iloc[0].strftime('%Y-%m')} ~ {bt_results_c['date'].iloc[-1].strftime('%Y-%m')}")

            total_days_c = (bt_results_c["date"].iloc[-1] - bt_results_c["date"].iloc[0]).days
            total_years_c = total_days_c / 365.25 if total_days_c > 0 else 1.0
            final_nav_c = bt_results_c["nav"].iloc[-1]

            cagr_c = ((final_nav_c / 100.0) ** (1 / total_years_c) - 1) * 100
            mdd_c = bt_results_c["drawdown"].min()

            bcc1, bcc2, bcc3 = st.columns(3)
            bcc1.metric("연환산 복리 수익률 (CAGR)", f"{cagr_c:.2f}%")
            bcc2.metric("최대 낙폭 (MDD)", f"{mdd_c:.2f}%", delta_color="inverse")
            bcc3.metric("최종 자산 가치 (NAV)", f"{final_nav_c:.1f}", "초기금 100 기준")

            st.markdown("##### 📈 자산 곡선 (NAV) 추이")
            chart_df_c = bt_results_c.copy()
            chart_df_c["date_str"] = chart_df_c["date"].dt.strftime("%Y-%m")

            qqq_ret_series_c = monthly_px_c["QQQ"].pct_change().reindex(bt_results_c["date"])
            chart_df_c["qqq_nav"] = (100 * (1 + qqq_ret_series_c.fillna(0)).cumprod()).values

            nav_color_scale_c = alt.Scale(domain=["전략C", "QQQ"], range=["#8b5cf6", "#808080"])
            nav_long_c = chart_df_c.melt(
                id_vars="date_str", value_vars=["nav", "qqq_nav"], var_name="series", value_name="value"
            )
            nav_long_c["series"] = nav_long_c["series"].map({"nav": "전략C", "qqq_nav": "QQQ"})

            nav_chart_c = alt.Chart(nav_long_c).mark_line(size=2.5).encode(
                x=alt.X("date_str:N", sort=None, title="년-월"),
                y=alt.Y("value:Q", title="NAV (기준 100)"),
                color=alt.Color("series:N", scale=nav_color_scale_c, legend=alt.Legend(title=None, orient="bottom")),
                tooltip=[
                    alt.Tooltip("date_str:N", title="년-월"),
                    alt.Tooltip("series:N", title="구분"),
                    alt.Tooltip("value:Q", title="NAV", format=".1f"),
                ],
            ).properties(height=350)
            st.altair_chart(nav_chart_c, use_container_width=True)

            # ------------------------------------------------------------
            # 연도별 수익률 (Annual Returns) — 막대 차트
            # ------------------------------------------------------------
            st.markdown("##### 📊 연도별 수익률 (%)")
            yearly_df_c = bt_results_c.copy()
            yearly_df_c["year"] = yearly_df_c["date"].dt.year
            yearly_returns_c = (
                yearly_df_c.groupby("year")["monthly_return"]
                .apply(lambda x: (np.prod(1 + x / 100.0) - 1) * 100)
                .reset_index(name="annual_return")
            )
            yearly_returns_c["year_str"] = yearly_returns_c["year"].astype(str)
            yearly_returns_c["series"] = "전략C"
            year_sort_order_c = yearly_returns_c["year_str"].tolist()

            qqq_monthly_ret_c = monthly_px_c["QQQ"].pct_change().reindex(bt_results_c["date"]) * 100
            qqq_ret_df_c = pd.DataFrame({
                "date": bt_results_c["date"].values,
                "qqq_return": qqq_monthly_ret_c.values,
            })
            qqq_ret_df_c["year"] = pd.to_datetime(qqq_ret_df_c["date"]).dt.year
            qqq_yearly_c = (
                qqq_ret_df_c.groupby("year")["qqq_return"]
                .apply(lambda x: (np.prod(1 + x / 100.0) - 1) * 100)
                .reset_index(name="annual_return")
            )
            qqq_yearly_c["year_str"] = qqq_yearly_c["year"].astype(str)
            qqq_yearly_c["series"] = "QQQ"

            color_scale_c = alt.Scale(domain=["전략C", "QQQ"], range=["#8b5cf6", "#808080"])

            annual_bar_c = alt.Chart(yearly_returns_c).mark_bar(size=28).encode(
                x=alt.X("year_str:N", title="연도", sort=year_sort_order_c),
                y=alt.Y("annual_return:Q", title="수익률 (%)"),
                color=alt.Color("series:N", scale=color_scale_c, legend=alt.Legend(title=None, orient="bottom")),
                tooltip=[
                    alt.Tooltip("year_str:N", title="연도"),
                    alt.Tooltip("annual_return:Q", title="수익률", format="+.2f"),
                ],
            )
            annual_labels_c = alt.Chart(yearly_returns_c).mark_text(
                dy=alt.expr("datum.annual_return >= 0 ? -8 : 14"), fontWeight="bold", fontSize=11, color="#0f172a"
            ).encode(
                x=alt.X("year_str:N", sort=year_sort_order_c),
                y=alt.Y("annual_return:Q"),
                text=alt.Text("annual_return:Q", format="+.1f"),
            )
            qqq_points_c = alt.Chart(qqq_yearly_c).mark_point(
                filled=True, size=110, stroke="white", strokeWidth=1.2
            ).encode(
                x=alt.X("year_str:N", sort=year_sort_order_c),
                y=alt.Y("annual_return:Q"),
                color=alt.Color("series:N", scale=color_scale_c, legend=alt.Legend(title=None, orient="bottom")),
                tooltip=[
                    alt.Tooltip("year_str:N", title="연도"),
                    alt.Tooltip("annual_return:Q", title="QQQ 수익률", format="+.2f"),
                ],
            )
            st.altair_chart(
                (annual_bar_c + annual_labels_c + qqq_points_c).properties(height=320),
                use_container_width=True,
            )

            # ------------------------------------------------------------
            # 월별 수익률 (Monthly Returns) — 히트맵 테이블
            # ------------------------------------------------------------
            st.markdown("##### 🗓️ 월별 수익률 (%)")
            monthly_df_c = bt_results_c.copy()
            monthly_df_c["year"] = monthly_df_c["date"].dt.year
            monthly_df_c["month"] = monthly_df_c["date"].dt.month

            month_labels_c = {1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
                              7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"}
            monthly_df_c["month_label"] = monthly_df_c["month"].map(month_labels_c)
            monthly_df_c["year_label"] = monthly_df_c["year"].astype(str)

            avg_by_month_c = monthly_df_c.groupby(["month", "month_label"])["monthly_return"].mean().reset_index()
            avg_by_month_c["year_label"] = "평균"

            heat_df_c = pd.concat([
                monthly_df_c[["year_label", "month", "month_label", "monthly_return"]],
                avg_by_month_c[["year_label", "month", "month_label", "monthly_return"]],
            ], ignore_index=True)

            year_sort_order_full_c = [str(y) for y in sorted(monthly_df_c["year"].unique())] + ["평균"]
            month_sort_order_c = [month_labels_c[m] for m in range(1, 13)]

            heat_rect_c = alt.Chart(heat_df_c).mark_rect(stroke="white", strokeWidth=1.5).encode(
                x=alt.X("month_label:N", title=None, sort=month_sort_order_c),
                y=alt.Y("year_label:N", title=None, sort=year_sort_order_full_c),
                color=alt.Color(
                    "monthly_return:Q",
                    scale=alt.Scale(
                        type="threshold",
                        domain=[-3.5, -2.5, -1.5, -0.5, 0.5, 1.5, 2.5, 3.5],
                        range=["#cf6265", "#e67f82", "#ecaaab", "#f6d4d5", "#fafbff",
                               "#d7e4da", "#accab2", "#82ae8b", "#599265"],
                    ),
                    legend=alt.Legend(title="수익률 (%)", orient="bottom", gradientLength=220),
                ),
                tooltip=[
                    alt.Tooltip("year_label:N", title="연도"),
                    alt.Tooltip("month_label:N", title="월"),
                    alt.Tooltip("monthly_return:Q", title="수익률", format="+.2f"),
                ],
            )
            heat_text_c = alt.Chart(heat_df_c).mark_text(fontSize=10, fontWeight="bold").encode(
                x=alt.X("month_label:N", sort=month_sort_order_c),
                y=alt.Y("year_label:N", sort=year_sort_order_full_c),
                text=alt.Text("monthly_return:Q", format="+.1f"),
                color=alt.value("#334155"),
            )
            st.altair_chart(
                (heat_rect_c + heat_text_c).properties(height=32 * len(year_sort_order_full_c) + 80),
                use_container_width=True,
            )

            st.markdown("##### 📉 낙폭 (Drawdown) 히스토리")
            dd_chart_c = alt.Chart(chart_df_c).mark_area(color="#fecaca", opacity=0.8).encode(
                x=alt.X("date_str:N", sort=None, title="년-월"),
                y=alt.Y("drawdown:Q", title="MDD (%)"),
                tooltip=["date_str", "drawdown"]
            ).properties(height=200)
            st.altair_chart(dd_chart_c, use_container_width=True)

            st.markdown("##### 🚨 포트폴리오 드로우다운 Top 10")
            dd_vals_c = bt_results_c["drawdown"].values
            dd_dates_c = bt_results_c["date"].values
            n_c = len(dd_vals_c)
            episodes_c = []
            i_ep_c = 0
            while i_ep_c < n_c:
                if dd_vals_c[i_ep_c] < -0.001:
                    start_i_c = i_ep_c
                    j_ep_c = i_ep_c
                    min_val_c = dd_vals_c[i_ep_c]
                    min_idx_c = i_ep_c
                    while j_ep_c < n_c and dd_vals_c[j_ep_c] < -0.001:
                        if dd_vals_c[j_ep_c] < min_val_c:
                            min_val_c = dd_vals_c[j_ep_c]
                            min_idx_c = j_ep_c
                        j_ep_c += 1
                    episodes_c.append({
                        "시작": pd.Timestamp(dd_dates_c[start_i_c]).strftime("%Y/%m"),
                        "종료": pd.Timestamp(dd_dates_c[min_idx_c]).strftime("%Y/%m"),
                        "드로우다운": min_val_c,
                    })
                    i_ep_c = j_ep_c
                else:
                    i_ep_c += 1

            episodes_c.sort(key=lambda x: x["드로우다운"])
            top10_c = episodes_c[:10]
            for idx, ep in enumerate(top10_c):
                ep["순위"] = idx + 1
                ep["드로우다운"] = f"{ep['드로우다운']:.1f}%"
            if top10_c:
                df_dd_top10_c = pd.DataFrame(top10_c)[["순위", "시작", "종료", "드로우다운"]]
                st.dataframe(df_dd_top10_c, use_container_width=True, hide_index=True)
            else:
                st.info("드로우다운 구간이 발견되지 않았습니다.")

            st.markdown("##### 🔻 폭락 시장 포트폴리오 성과")
            STRESS_PERIODS_C = [
                ("코로나 팬데믹", "2020-01-01", "2020-03-31"),
                ("2022 긴축 발작 (금리인상기)", "2022-01-01", "2022-10-31"),
                ("2018년 4분기 조정", "2018-10-01", "2018-12-31"),
            ]
            stress_rows_c = []
            for label_c, s_str_c, e_str_c in STRESS_PERIODS_C:
                s_ts_c, e_ts_c = pd.Timestamp(s_str_c), pd.Timestamp(e_str_c)
                mask_c = (bt_results_c["date"] >= s_ts_c) & (bt_results_c["date"] <= e_ts_c)
                sub_c = bt_results_c[mask_c]
                if len(sub_c) == 0:
                    continue
                port_cum_c = (np.prod(1 + sub_c["monthly_return"].values / 100.0) - 1) * 100
                bench_sub_ret_c = monthly_px_c["QQQ"].pct_change().reindex(sub_c["date"]).fillna(0.0)
                bench_cum_c = (np.prod(1 + bench_sub_ret_c.values) - 1) * 100
                stress_rows_c.append({
                    "스트레스 기간": label_c,
                    "시작": s_ts_c.strftime("%Y/%m"),
                    "종료": e_ts_c.strftime("%Y/%m"),
                    "포트폴리오 수익률": f"{port_cum_c:+.1f}%",
                    "QQQ 수익률": f"{bench_cum_c:+.1f}%",
                })
            if stress_rows_c:
                st.dataframe(pd.DataFrame(stress_rows_c), use_container_width=True, hide_index=True)
            else:
                st.info("선택한 시작일 범위 내 해당하는 폭락장 스트레스 기간 데이터가 없습니다. 시작일을 앞당겨 보세요.")

            st.markdown("##### 📊 주요 지표 비교 (vs QQQ)")

            def _fmt_pct_c(x):
                return f"{x:.1f}%" if x is not None and not (isinstance(x, float) and np.isnan(x)) else "데이터 부족"

            port_ret_arr_c = bt_results_c["monthly_return"].values
            bench_ret_arr_c = qqq_monthly_ret_c.values
            dd_arr_c = bt_results_c["drawdown"].values
            bench_nav_arr_c = chart_df_c["qqq_nav"].values
            bench_running_max_c = np.maximum.accumulate(bench_nav_arr_c)
            bench_dd_arr_c = (bench_nav_arr_c / bench_running_max_c - 1) * 100

            period_ret_c = (final_nav_c / 100.0 - 1) * 100
            bench_final_nav_c = bench_nav_arr_c[-1]
            bench_period_ret_c = (bench_final_nav_c / 100.0 - 1) * 100
            bench_cagr_c = ((bench_final_nav_c / 100.0) ** (1 / total_years_c) - 1) * 100

            last_date2_c = bt_results_c["date"].iloc[-1]
            current_year2_c = last_date2_c.year
            ytd_mask_c = bt_results_c["date"].dt.year == current_year2_c
            port_ytd_c = (np.prod(1 + bt_results_c.loc[ytd_mask_c, "monthly_return"].values / 100.0) - 1) * 100
            bench_ytd_c = (np.prod(1 + (bench_ret_arr_c[ytd_mask_c.values] / 100.0)) - 1) * 100

            win_months_c = int((port_ret_arr_c > 0).sum())
            bench_win_months_c = int((bench_ret_arr_c > 0).sum())
            total_months_c = len(port_ret_arr_c)

            mdd_idx_c = int(np.argmin(dd_arr_c))
            mdd_date_c = bt_results_c["date"].iloc[mdd_idx_c].strftime("%Y-%m")
            bench_mdd_idx_c = int(np.argmin(bench_dd_arr_c))
            bench_mdd_date_c = bt_results_c["date"].iloc[bench_mdd_idx_c].strftime("%Y-%m")

            def _trailing_c(arr, months):
                if len(arr) < months:
                    return None, None
                window = arr[-months:]
                cum = (np.prod(1 + window / 100.0) - 1) * 100
                ann_std = np.std(window, ddof=1) * np.sqrt(12) if len(window) > 1 else None
                return cum, ann_std

            ret_1y_c, std_1y_c = _trailing_c(port_ret_arr_c, 12)
            ret_3y_c, std_3y_c = _trailing_c(port_ret_arr_c, 36)
            ret_5y_c, std_5y_c = _trailing_c(port_ret_arr_c, 60)
            bench_ret_1y_c, bench_std_1y_c = _trailing_c(bench_ret_arr_c, 12)
            bench_ret_3y_c, bench_std_3y_c = _trailing_c(bench_ret_arr_c, 36)
            bench_ret_5y_c, bench_std_5y_c = _trailing_c(bench_ret_arr_c, 60)

            mean_m_c = np.mean(port_ret_arr_c) / 100.0
            std_m_c = np.std(port_ret_arr_c, ddof=1) / 100.0 if total_months_c > 1 else np.nan
            annual_vol_c = std_m_c * np.sqrt(12) * 100 if not np.isnan(std_m_c) else np.nan
            sharpe_c = (mean_m_c * 12) / (std_m_c * np.sqrt(12)) if std_m_c and std_m_c > 0 else np.nan

            downside_c = port_ret_arr_c[port_ret_arr_c < 0] / 100.0
            downside_std_c = np.std(downside_c, ddof=1) if len(downside_c) > 1 else np.nan
            sortino_c = (mean_m_c * 12) / (downside_std_c * np.sqrt(12)) if downside_std_c and downside_std_c > 0 else np.nan

            ulcer_c = np.sqrt(np.mean(dd_arr_c ** 2))
            upi_c = cagr_c / ulcer_c if ulcer_c > 0 else np.nan

            bench_mean_m_c = np.mean(bench_ret_arr_c) / 100.0
            bench_std_m_c = np.std(bench_ret_arr_c, ddof=1) / 100.0 if total_months_c > 1 else np.nan
            bench_annual_vol_c = bench_std_m_c * np.sqrt(12) * 100 if not np.isnan(bench_std_m_c) else np.nan
            bench_sharpe_c = (bench_mean_m_c * 12) / (bench_std_m_c * np.sqrt(12)) if bench_std_m_c and bench_std_m_c > 0 else np.nan

            bench_downside_c = bench_ret_arr_c[bench_ret_arr_c < 0] / 100.0
            bench_downside_std_c = np.std(bench_downside_c, ddof=1) if len(bench_downside_c) > 1 else np.nan
            bench_sortino_c = (bench_mean_m_c * 12) / (bench_downside_std_c * np.sqrt(12)) if bench_downside_std_c and bench_downside_std_c > 0 else np.nan

            bench_ulcer_c = np.sqrt(np.mean(bench_dd_arr_c ** 2))
            bench_upi_c = bench_cagr_c / bench_ulcer_c if bench_ulcer_c > 0 else np.nan

            alloc_list_c = bt_results_c["alloc"].tolist()
            monthly_turnovers_c = []
            prev_alloc_c = {}
            for alloc_d in alloc_list_c:
                all_tk_c = set(prev_alloc_c.keys()) | set(alloc_d.keys())
                diff_c = sum(abs(alloc_d.get(t, 0.0) - prev_alloc_c.get(t, 0.0)) for t in all_tk_c)
                monthly_turnovers_c.append(diff_c / 2.0)
                prev_alloc_c = alloc_d
            avg_turnover_c = np.mean(monthly_turnovers_c) if monthly_turnovers_c else 0.0
            annual_turnover_c = avg_turnover_c * 12

            metrics_rows_c = [
                ("기간 수익률", _fmt_pct_c(period_ret_c), _fmt_pct_c(bench_period_ret_c)),
                ("연환산 수익률 (CAGR)", _fmt_pct_c(cagr_c), _fmt_pct_c(bench_cagr_c)),
                ("이번 달 수익률", _fmt_pct_c(port_ret_arr_c[-1]), _fmt_pct_c(bench_ret_arr_c[-1])),
                ("올해 수익률 (YTD)", _fmt_pct_c(port_ytd_c), _fmt_pct_c(bench_ytd_c)),
                ("월 최고 수익률", _fmt_pct_c(port_ret_arr_c.max()), _fmt_pct_c(bench_ret_arr_c.max())),
                ("월 최저 수익률", _fmt_pct_c(port_ret_arr_c.min()), _fmt_pct_c(bench_ret_arr_c.min())),
                ("수익 월 비중", f"{win_months_c} / {total_months_c}", f"{bench_win_months_c} / {total_months_c}"),
                ("연 변동성", _fmt_pct_c(annual_vol_c), _fmt_pct_c(bench_annual_vol_c)),
                ("최대 낙폭 (MDD)", _fmt_pct_c(mdd_c), _fmt_pct_c(bench_dd_arr_c.min())),
                ("MDD 시점", mdd_date_c, bench_mdd_date_c),
                ("1년 수익률", _fmt_pct_c(ret_1y_c), _fmt_pct_c(bench_ret_1y_c)),
                ("3년 수익률", _fmt_pct_c(ret_3y_c), _fmt_pct_c(bench_ret_3y_c)),
                ("5년 수익률", _fmt_pct_c(ret_5y_c), _fmt_pct_c(bench_ret_5y_c)),
                ("1년 표준편차", _fmt_pct_c(std_1y_c), _fmt_pct_c(bench_std_1y_c)),
                ("3년 표준편차", _fmt_pct_c(std_3y_c), _fmt_pct_c(bench_std_3y_c)),
                ("5년 표준편차", _fmt_pct_c(std_5y_c), _fmt_pct_c(bench_std_5y_c)),
                ("샤프 지수", f"{sharpe_c:.2f}" if not np.isnan(sharpe_c) else "데이터 부족", f"{bench_sharpe_c:.2f}" if not np.isnan(bench_sharpe_c) else "데이터 부족"),
                ("소티노 지수", f"{sortino_c:.2f}" if not np.isnan(sortino_c) else "데이터 부족", f"{bench_sortino_c:.2f}" if not np.isnan(bench_sortino_c) else "데이터 부족"),
                ("UPI 지수", f"{upi_c:.2f}" if not np.isnan(upi_c) else "데이터 부족", f"{bench_upi_c:.2f}" if not np.isnan(bench_upi_c) else "데이터 부족"),
                ("연간 턴오버", f"{annual_turnover_c:.1f}%", "0.0%"),
            ]
            df_metrics_c = pd.DataFrame(metrics_rows_c, columns=["지표", "전략C", "QQQ"])
            st.dataframe(df_metrics_c, use_container_width=True, hide_index=True)
            st.caption(f"※ 기간: {bt_results_c['date'].iloc[0].strftime('%Y-%m')} ~ {bt_results_c['date'].iloc[-1].strftime('%Y-%m')} 야후 파이낸스 실시간 데이터 기준. 1/3/5년 지표는 해당 기간의 월 데이터가 충분할 때만 표시됩니다.")




            st.markdown("##### 🗓️ 월별 세부 리밸런싱 기록")
            display_bt_c = bt_results_c.copy()
            display_bt_c["연월"] = display_bt_c["date"].dt.strftime("%Y-%m")
            display_bt_c["월 수익률"] = display_bt_c["monthly_return"].apply(lambda x: f"{x:+.2f}%")
            display_bt_c["낙폭"] = display_bt_c["drawdown"].apply(lambda x: f"{x:.2f}%")
            display_bt_c["NAV"] = display_bt_c["nav"].apply(lambda x: f"{x:.1f}")

            st.dataframe(
                display_bt_c[["연월", "mode", "월 수익률", "weights_str", "NAV", "낙폭"]].iloc[::-1],
                use_container_width=True, hide_index=True
            )

    with c_rank:
        st.header("🇺🇸 실시간 미국 ETF 랭킹")
        st.markdown(
            "대시보드에 등록된 주요 지수, 주도 섹터, 레버리지 및 배당형 ETF들의 실시간 모멘텀과 "
            "수익률을 역동적으로 추적하여 정렬하는 인텔리전트 멀티-팩터 랭킹 시스템입니다."
        )
        
        sort_by = st.radio(
            "🏆 정렬 기준 선택",
            options=["종합 모멘텀 스코어", "1개월 수익률", "3개월 수익률", "6개월 수익률", "12개월 수익률"],
            horizontal=True,
            key="etf_sort_by_radio"
        )
        
        rank_data = []
        for ticker, metrics in data_dict.items():
            if ticker == "TIP":
                continue
            
            rank_data.append({
                "티커 (Ticker)": ticker,
                "현재가 ($)": f"${metrics['현재가']:.2f}",
                "종합 모멘텀 스코어": metrics["A_공격스코어"],
                "1개월 수익률 (%)": metrics["1M"],
                "3개월 수익률 (%)": metrics["3M"],
                "6개월 수익률 (%)": metrics["6M"],
                "12개월 수익률 (%)": metrics["12M"],
            })
        
        df_ranking = pd.DataFrame(rank_data)
        
        sort_column_map = {
            "종합 모멘텀 스코어": "종합 모멘텀 스코어",
            "1개월 수익률": "1개월 수익률 (%)",
            "3개월 수익률": "3개월 수익률 (%)",
            "6개월 수익률": "6개월 수익률 (%)",
            "12개월 수익률": "12개월 수익률 (%)"
        }
        
        selected_sort_col = sort_column_map[sort_by]
        df_ranking = df_ranking.sort_values(by=selected_sort_col, ascending=False).reset_index(drop=True)
        df_ranking.index += 1
        
        st.markdown(f"### 📊 Top 5 Performers ({sort_by} 기준)")
        df_top5 = df_ranking.head(5).copy()
        
        try:
            import altair as alt
            top_chart = alt.Chart(df_top5).mark_bar(cornerRadiusEnd=6).encode(
                x=alt.X(f"{selected_sort_col}:Q", title=sort_by),
                y=alt.Y("티커 (Ticker):N", sort='-x', title="ETF 티커"),
                color=alt.Color("티커 (Ticker):N", scale=alt.Scale(scheme='tableau10'), legend=None),
                tooltip=["티커 (Ticker)", "현재가 ($)", selected_sort_col]
            ).properties(height=200)
            st.altair_chart(top_chart, use_container_width=True)
        except Exception:
            st.bar_chart(df_top5.set_index("티커 (Ticker)")[selected_sort_col])
        
        st.markdown("### 🏆 실시간 모멘텀 순위표")
        st.dataframe(df_ranking, use_container_width=True)

    with c_calc:
        st.header("🧮 복리의 마법 & 미래 계산기")
        st.markdown(
            "자산배분 백테스트의 실제 연평균 수익률(CAGR)을 기반으로, 매월 적립식 저축 및 정기 생활비 지출이 유발하는 "
            "미래 자산의 실제 성장 경로를 정밀하게 예측합니다. **세율 적용**, **생활비 지출 설정**, 및 **물가상승률 할인**까지 연산하는 실전형 자산 시뮬레이터입니다."
        )

        if "cagr_input" not in st.session_state:
            st.session_state.cagr_input = 38.7

        st.markdown("##### ⚡ 자산배분 전략 실측 CAGR 퀵 프리셋")
        col_pre1, col_pre2, col_pre3, col_pre4 = st.columns(4)
        if col_pre1.button("🏆 2026 혼합 (38.7%)"):
            st.session_state.cagr_input = 38.7
            st.rerun()
        if col_pre2.button("🛡️ 전략 A (27.3%)"):
            st.session_state.cagr_input = 27.3
            st.rerun()
        if col_pre3.button("⚡ 전략 B (36.4%)"):
            st.session_state.cagr_input = 36.4
            st.rerun()
        if col_pre4.button("🔄 전략 C (46.7%)"):
            st.session_state.cagr_input = 46.7
            st.rerun()

        st.markdown("---")
        col_inp1, col_inp2 = st.columns(2)
        with col_inp1:
            calc_init = st.number_input("초기 투자금 (만원 ₩)", min_value=0, value=2000, step=100)
            calc_monthly = st.number_input("매월 저축/적립금 (만원 ₩)", min_value=0, value=100, step=10)
            calc_expense = st.number_input("매월 지출/생활비 (만원 ₩)", min_value=0, value=0, step=10, help="투자수익에서 정기 지출하는 생활비가 있다면 마이너스로 처리됩니다.")
            calc_years = st.slider("시뮬레이션 투자 기간 (년)", min_value=1, max_value=40, value=15)
        with col_inp2:
            calc_cagr = st.number_input("연 목표 수익률 CAGR (%)", min_value=0.0, max_value=100.0, key="cagr_input", step=0.1)
            calc_inflation = st.number_input("연 예상 물가상승률 (%)", min_value=0.0, max_value=20.0, value=3.0, step=0.1)
            calc_expense_start = st.number_input("지출 시작 시점 (년차)", min_value=1, max_value=max(1, calc_years), value=1, step=1, help="생활비 지출을 몇 년차부터 적용할지 연차를 지정합니다.")
            calc_tax_opt = st.selectbox("세율 설정", ["일반과세 (15.4%)", "미국주식양도세 (22.0%)", "비과세 계좌 (0.0% / ISA 및 연금저축)", "사용자 정의"])
        
        if calc_tax_opt == "일반과세 (15.4%)":
            tax_rate = 15.4
        elif calc_tax_opt == "미국주식양도세 (22.0%)":
            tax_rate = 22.0
        elif calc_tax_opt == "비과세 계좌 (0.0% / ISA 및 연금저축)":
            tax_rate = 0.0
        else:
            tax_rate = st.number_input("세율 직접 입력 (%)", min_value=0.0, max_value=50.0, value=15.4, step=0.1)

        records = []
        curr_nominal = calc_init * 10000
        curr_contribution = calc_init * 10000
        monthly_contrib = calc_monthly * 10000
        base_expense = calc_expense * 10000
        r_monthly = (1 + calc_cagr / 100) ** (1/12) - 1 if calc_cagr > 0 else 0.0

        for y in range(1, calc_years + 1):
            current_year_monthly_expense = base_expense * ((1 + calc_inflation / 100) ** (y - 1)) if y >= calc_expense_start else 0.0
            
            for m in range(12):
                net_flow = monthly_contrib - current_year_monthly_expense
                curr_contribution += net_flow
                curr_nominal = (curr_nominal + net_flow) * (1 + r_monthly)
                
                if curr_nominal < 0:
                    curr_nominal = 0.0
            
            effective_contribution = max(0.0, curr_contribution)
            profit = curr_nominal - effective_contribution
            tax_due = profit * (tax_rate / 100) if profit > 0 else 0.0
            curr_after_tax = curr_nominal - tax_due
            
            real_value = curr_after_tax / ((1 + calc_inflation / 100) ** y)
            
            records.append({
                "년차": f"{y}년차",
                "누적 납입원금": round(curr_contribution),
                "세전 일반복리": round(curr_nominal),
                "세후 수령예정액": round(curr_after_tax),
                "세후 실질가치 (물가반영)": round(real_value)
            })

        df_calc = pd.DataFrame(records)

        def format_krw(val):
            sign = "-" if val < 0 else ""
            val = abs(val)
            if val == 0:
                return "0원"
            if val >= 100000000:
                eok = int(val // 100000000)
                man = int((val % 100000000) // 10000)
                if man > 0:
                    return f"{sign}{eok}억 {man:,}만원"
                return f"{sign}{eok}억원"
            else:
                man = int(val // 10000)
                return f"{sign}{man:,}만원"

        last_rec = records[-1]
        st.markdown("### 🏆 시뮬레이션 최종 기대 성과 요약")
        sum_col1, sum_col2, sum_col3 = st.columns(3)
        sum_col1.metric("총 순 원금(저축-지출)", format_krw(last_rec["누적 납입원금"]))
        sum_col2.metric("세후 최종 자산", format_krw(last_rec["세후 수령예정액"]))
        sum_col3.metric("실질구매력 가치", format_krw(last_rec["세후 실질가치 (물가반영)"]))

        st.markdown("### 📈 미래 자산 성장 시뮬레이션")
        df_melt = df_calc.melt(id_vars="년차", value_vars=["누적 납입원금", "세전 일반복리", "세후 수령예정액", "세후 실질가치 (물가반영)"], var_name="구분", value_name="자산액")
        
        try:
            import altair as alt
            line_chart = alt.Chart(df_melt).mark_line(point=True, size=2.5).encode(
                x=alt.X("년차:N", sort=None, title="년차"),
                y=alt.Y("자산액:Q", title="평가액 (₩)"),
                color=alt.Color("구분:N", scale=alt.Scale(range=["#94a3b8", "#ef4444", "#10b981", "#3b82f6"])),
                tooltip=[alt.Tooltip("년차"), alt.Tooltip("구분"), alt.Tooltip("자산액", format=",.0f")]
            ).properties(height=350)
            st.altair_chart(line_chart, use_container_width=True)
        except Exception:
            st.line_chart(df_calc.set_index("년차"))

        st.markdown("### 📊 연도별 세부 자산 성장 상세표")
        df_display = df_calc.copy()
        for col in ["누적 납입원금", "세전 일반복리", "세후 수령예정액", "세후 실질가치 (물가반영)"]:
            df_display[col] = df_display[col].apply(format_krw)
        
        st.dataframe(df_display, use_container_width=True)
