import streamlit as st
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
    background-color: #e2e8f0 !important;
    border: 1px solid #cbd5e1 !important;
    border-radius: 12px !important;
    padding: 5px !important;
    gap: 4px !important;
    box-shadow: inset 0 2px 4px 0 rgba(0, 0, 0, 0.06), 0 4px 6px -1px rgba(0, 0, 0, 0.05) !important;
    margin-bottom: 20px !important;
}

.stTabs [data-baseweb="tab"] {
    background-color: transparent !important;
    border-radius: 8px !important;
    padding: 10px 12px !important;
    font-weight: 800 !important;
    font-size: 0.85rem !important;
    color: #475569 !important;
    border: none !important;
    transition: all 0.2s ease-in-out !important;
    flex: 1 !important;
    text-align: center !important;
}

.stTabs [aria-selected="true"] {
    background-color: #1e293b !important;
    color: #ffffff !important;
    box-shadow: 0 4px 10px -2px rgba(30, 41, 59, 0.3) !important;
}

.control-panel {
    background-color: #f1f5f9 !important;
    border: 1px solid #cbd5e1 !important;
    border-radius: 12px !important;
    padding: 18px !important;
    margin-bottom: 20px !important;
}
.control-header {
    color: #0f172a !important;
    font-weight: 800 !important;
    font-size: 0.98rem !important;
    margin-bottom: 4px !important;
}
.control-subheader {
    color: #475569 !important;
    font-size: 0.8rem !important;
    line-height: 1.45 !important;
}

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
st.caption("야후 파이낸스 실시간 데이터 기반 수시 리밸런싱 가이드 (2026년 전략 고도화 버전)")

# --- 1. 자산군 정의 ---
OFFENSIVE_A = ["QQQ", "FEZ", "GLD", "IBB", "SMH", "EEM", "XLK", "LIT", "XLE", "UBT", "XLV", "QTUM"]
DEFENSIVE_A = ["BIL", "IEF", "AGG", "HYG", "TBF"]

OFFENSIVE_B = ["TYD", "UPRO", "VNQ"]
DEFENSIVE_B = ["DOG", "RWM", "TBF"]

OFFENSIVE_C = ["FDN", "LIT", "SMH", "XLE", "IGV", "QQQM", "XLU"]
DEFENSIVE_C = ["GLD", "PDBC", "OILK", "SHY", "TLT"]

ALL_TICKERS = list(set(["TIP", "SPY"] + OFFENSIVE_A + DEFENSIVE_A + OFFENSIVE_B + DEFENSIVE_B + OFFENSIVE_C + DEFENSIVE_C + ["SCHD", "QQQM", "IGV", "XLU", "JEPI", "TQQQ", "SOXL", "DIA", "IWM", "XLF"]))

# ============================================================
# 데이터 다운로드 및 기초 함수
# ============================================================
@st.cache_data(ttl=3600)
def get_daily_price_history_a(tickers, start="2015-01-01"):
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
def get_spy_dividend_history():
    try:
        divs = yf.Ticker("SPY").dividends
        if divs.index.tz is not None:
            divs.index = divs.index.tz_localize(None)
        return divs
    except Exception:
        return pd.Series(dtype=float)

# ============================================================
# 전략 C: S&P 500 배당수익률 동적 롤링 Z-Score 계산 모듈 (1단계 고도화)
# ============================================================
def calculate_spy_dividend_yield_series(monthly_px, spy_divs):
    """
    매월 말 기준 직전 12개월(365일) 누적 배당금을 당월 종가로 나누어 배당수익률(%) 시계열 생성
    """
    if "SPY" not in monthly_px.columns or spy_divs.empty:
        return pd.Series(dtype=float, index=monthly_px.index)
    
    spy_divs_clean = spy_divs.copy()
    if spy_divs_clean.index.tz is not None:
        spy_divs_clean.index = spy_divs_clean.index.tz_localize(None)
        
    dy_list = []
    for dt, spy_p in monthly_px["SPY"].items():
        if pd.isna(spy_p) or spy_p <= 0:
            dy_list.append(np.nan)
            continue
        dt_naive = dt.tz_localize(None) if dt.tzinfo is not None else dt
        start_dt = dt_naive - pd.Timedelta(days=365)
        sum_div = spy_divs_clean[(spy_divs_clean.index > start_dt) & (spy_divs_clean.index <= dt_naive)].sum()
        dy = (sum_div / spy_p) * 100 if sum_div > 0 else np.nan
        dy_list.append(dy)
        
    return pd.Series(dy_list, index=monthly_px.index)

def get_dynamic_zscore_at_index(dy_series, idx_pos, window=36, min_periods=12):
    """
    최근 36개월 롤링 윈도우 기반 Z-Score 산출
    Z_DY = (DY_t - Mean_36) / Std_36
    """
    if idx_pos < 0 or pd.isna(dy_series.iloc[idx_pos]):
        return np.nan, np.nan, np.nan
    
    start_pos = max(0, idx_pos - window + 1)
    sub = dy_series.iloc[start_pos:idx_pos + 1].dropna()
    
    if len(sub) < min_periods:
        return np.nan, np.nan, np.nan
        
    curr_dy = dy_series.iloc[idx_pos]
    mean_dy = sub.mean()
    std_dy = sub.std(ddof=1)
    
    if pd.isna(std_dy) or std_dy < 1e-6:
        z_score = 0.0
    else:
        z_score = (curr_dy - mean_dy) / std_dy
        
    return z_score, curr_dy, mean_dy

# ============================================================
# 전략 A 실시간 백테스트 엔진
# ============================================================
@st.cache_data(ttl=3600)
def run_backtest_strategy_a_full(monthly_px):
    records = []
    nav = 100.0
    peak = 100.0
    monthly_returns = monthly_px.pct_change().shift(-1)

    for i in range(11, len(monthly_px) - 1):
        tip_window = monthly_px["TIP"].iloc[i - 10:i + 1]
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
# 전략 B 실시간 백테스트 엔진
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
# 전략 C 실시간 백테스트 엔진 (동적 Z-Score 체계 적용)
# ============================================================
@st.cache_data(ttl=3600)
def run_backtest_strategy_c_full(monthly_px, spy_divs, z_threshold=-0.5):
    records = []
    nav = 100.0
    peak = 100.0
    monthly_returns = monthly_px.pct_change().shift(-1)
    dy_series = calculate_spy_dividend_yield_series(monthly_px, spy_divs)

    for i in range(11, len(monthly_px) - 1):
        if "SPY" not in monthly_px.columns:
            break
        
        # 36개월 롤링 동적 Z-Score 산출
        z_val, dy_curr, _ = get_dynamic_zscore_at_index(dy_series, i, window=36, min_periods=12)
        if pd.isna(z_val):
            # 워밍업 초기에는 절대 기준선(1.33%) 폴백
            is_attack = dy_curr > 1.33 if pd.notna(dy_curr) else False
        else:
            is_attack = z_val > z_threshold

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
            "mode": f"공격 (Offensive, Z:{z_val:.2f})" if is_attack else f"방어 (Defensive, Z:{z_val:.2f})",
            "nav": nav,
            "monthly_return": port_ret * 100,
            "drawdown": dd,
            "weights_str": ", ".join([f"{t} {w}%" for t, w in alloc.items() if w > 0]),
            "alloc": dict(alloc),
        })

    return pd.DataFrame(records)

# ============================================================
# 2026 혼합전략 백테스트 엔진 (기본형)
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
        weights_str = f"A[{bt_a.loc[d, 'weights_str']}] + B[{bt_b.loc[d, 'weights_str']}] + C[{bt_c.loc[d, 'weights_str']}]"

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
# ============================================================
@st.cache_data(ttl=3600)
def run_backtest_strategy_mix_improved_full(
    monthly_px, spy_divs, daily_px=None,
    apply_cap=False, weight_cap=25.0,
    apply_vix_dampening=False, vix_threshold=25.0,
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
    has_vix = "^VIX" in monthly_px.columns
    offensive_b_set = set(OFFENSIVE_B)
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
        decision_pos = pos - 1 if pos > 0 else None
        decision_date = monthly_idx[decision_pos] if decision_pos is not None else None

        vol_note = ""
        if apply_vix_dampening and has_vix and decision_pos is not None:
            vix_val = monthly_px["^VIX"].iloc[decision_pos]
            if pd.notna(vix_val) and vix_val > vix_threshold:
                new_alloc_b = {}
                changed = False
                for t, w in alloc_b.items():
                    if t in offensive_b_set:
                        new_alloc_b[t] = new_alloc_b.get(t, 0.0) + w * 0.5
                        new_alloc_b["CASH (현금)"] = new_alloc_b.get("CASH (현금)", 0.0) + w * 0.5
                        changed = True
                    else:
                        new_alloc_b[t] = new_alloc_b.get(t, 0.0) + w
                if changed:
                    alloc_b = new_alloc_b
                    vol_note = " ⚡VIX완화"

        combined_alloc = {}
        for src in (alloc_a, alloc_b, alloc_c):
            for t, w in src.items():
                combined_alloc[t] = combined_alloc.get(t, 0.0) + (w / 100.0) * (1.0 / 3.0) * 100.0

        cap_note = ""
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

        port_ret = 0.0
        if decision_pos is not None:
            for t, w in final_alloc.items():
                if t != "CASH (현금)" and t in monthly_returns.columns:
                    r = monthly_returns[t].iloc[decision_pos]
                    if pd.notna(r):
                        port_ret += (w / 100.0) * r

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
                    port_ret = cum_val.iloc[-1]

        nav *= (1 + port_ret)
        peak = max(peak, nav)
        dd = (nav / peak - 1) * 100

        mode_a_short = bt_a.loc[d, "mode"].split(" ")[0]
        mode_b_short = bt_b.loc[d, "mode"].split(" ")[0]
        mode_c_short = bt_c.loc[d, "mode"].split(" ")[0]
        mode_str = f"A:{mode_a_short} / B:{mode_b_short} / C:{mode_c_short}{vol_note}{cap_note}{stop_note}"
        weights_str = ", ".join([f"{t} {w:.1f}%" for t, w in final_alloc.items() if w > 0.01])

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

# 관심매크로 지표 정의 및 심볼 매핑
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

@st.cache_data(ttl=60)
def get_macro_market_pulse():
    macro_data = []
    for name, symbol in MACRO_TICKERS.items():
        price_val = "-"
        delta_val = "0.00"
        delta_pct_val = "0.00%"
        raw_delta_val = 0.0
        
        try:
            ticker = yf.Ticker(symbol)
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
    return 1380.0

@st.cache_data(ttl=3600)
def get_sp500_dividend_and_zscore():
    """
    실시간 SPY 배당수익률 및 과거 36개월 롤링 Z-Score 계산
    """
    dy_curr = 1.32
    z_score = 0.0
    mean_36 = 1.32
    std_36 = 0.15
    
    try:
        spy = yf.Ticker("SPY")
        divs = spy.dividends
        if not divs.empty:
            if divs.index.tz is not None:
                divs.index = divs.index.tz_localize(None)
                
            # 과거 4년 월간 종가 가져오기
            hist_monthly = spy.history(period="5y", interval="1mo")
            if not hist_monthly.empty and "Close" in hist_monthly.columns:
                m_closes = hist_monthly["Close"].dropna()
                dy_hist = []
                for dt, px in m_closes.items():
                    dt_naive = dt.tz_localize(None) if dt.tzinfo is not None else dt
                    start_dt = dt_naive - pd.Timedelta(days=365)
                    sum_d = divs[(divs.index > start_dt) & (divs.index <= dt_naive)].sum()
                    if px > 0 and sum_d > 0:
                        dy_hist.append((sum_d / px) * 100)
                
                if len(dy_hist) >= 12:
                    sub = dy_hist[-36:]
                    mean_36 = np.mean(sub)
                    std_36 = np.std(sub, ddof=1) if len(sub) > 1 else 0.15
                    dy_curr = dy_hist[-1]
                    z_score = (dy_curr - mean_36) / std_36 if std_36 > 1e-6 else 0.0
                    return dy_curr, z_score, mean_36, std_36
    except Exception:
        pass
    return dy_curr, z_score, mean_36, std_36

@st.cache_data(ttl=3600) 
def get_all_financial_data_v2(tickers):
    data_list = []
    now = datetime.datetime.now()
    start_date = (now - datetime.timedelta(days=450)).strftime('%Y-%m-%d')
    
    try:
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
                
                current_price = float(closes.iloc[-1])
                p1 = float(closes.iloc[-2]) if len(closes) >= 2 else current_price
                p3 = float(closes.iloc[-4]) if len(closes) >= 4 else current_price
                p5 = float(closes.iloc[-6]) if len(closes) >= 6 else current_price
                p6 = float(closes.iloc[-7]) if len(closes) >= 7 else current_price
                p9 = float(closes.iloc[-10]) if len(closes) >= 10 else current_price
                p12 = float(closes.iloc[-13]) if len(closes) >= 13 else float(closes.iloc[0])
                
                r1 = ((current_price - p1) / p1) * 100
                r3 = ((current_price - p3) / p3) * 100
                r5 = ((current_price - p5) / p5) * 100
                r6 = ((current_price - p6) / p6) * 100
                r9 = ((current_price - p9) / p9) * 100
                r12 = ((current_price - p12) / p12) * 100
                
                score_a_off = (r1 + r3 + r6 + r12) / 4
                score_a_def = (r1 + r3 + r6 + r9 + r12) / 5
                score_b_off = (r1 * 12 + r3 * 4 + r6 * 2 + r12 * 1) / 19
                score_b_def_simple = (r1 + r3 + r6 + r9 + r12) / 5
                
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
    start_date = (now - datetime.timedelta(days=1500)).strftime('%Y-%m-%d')
    
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
        return {"CASH (현금)": 100.0}, False, False, False, 1.32, 0.0

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

    # 3. 전략 C 배분 (동적 Z-Score 체계 적용)
    dy_val = 1.32
    z_score_val = 0.0
    if not spy_divs.empty and "SPY" in monthly_prices:
        spy_sub_series = prices_dict["SPY"][prices_dict["SPY"].index <= target_date]
        df_spy = spy_sub_series.to_frame()
        df_spy['year'] = df_spy.index.year
        df_spy['month'] = df_spy.index.month
        spy_last_idx = df_spy.groupby(['year', 'month']).apply(lambda x: x.index[-1])
        
        spy_divs_clean = spy_divs.copy()
        if spy_divs_clean.index.tz is not None:
            spy_divs_clean.index = spy_divs_clean.index.tz_localize(None)
            
        hist_dy_vals = []
        for d_idx in spy_last_idx:
            p_val = spy_sub_series.loc[d_idx]
            d_naive = d_idx.tz_localize(None) if d_idx.tzinfo is not None else d_idx
            s_dt = d_naive - pd.Timedelta(days=365)
            s_div = spy_divs_clean[(spy_divs_clean.index > s_dt) & (spy_divs_clean.index <= d_naive)].sum()
            if p_val > 0 and s_div > 0:
                hist_dy_vals.append((s_div / p_val) * 100)
                
        if hist_dy_vals:
            dy_val = hist_dy_vals[-1]
            sub_36 = hist_dy_vals[-36:]
            if len(sub_36) >= 12:
                m_36 = np.mean(sub_36)
                s_36 = np.std(sub_36, ddof=1) if len(sub_36) > 1 else 0.15
                z_score_val = (dy_val - m_36) / s_36 if s_36 > 1e-6 else 0.0

    # 동적 Z-Score 기준선 (-0.5 초과 시 공격)
    is_attack_c_hist = z_score_val > -0.5

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
    return clean_portfolio, is_attack_a_hist, is_attack_b_hist, is_attack_c_hist, dy_val, z_score_val

with st.spinner("야후 파이낸스 실시간 데이터를 통합 집계 중..."):
    df_all = get_all_financial_data_v2(ALL_TICKERS)

if df_all.empty or "TIP" not in df_all["Ticker"].values:
    st.error("핵심 데이터 로딩에 실패했습니다. 페이지를 새로고침해 주세요.")
else:
    data_dict = df_all.set_index("Ticker").to_dict(orient="index")
    
    with st.spinner("과거 포트폴리오 데이터를 로딩 및 연산 중..."):
        hist_prices, spy_divs_hist = get_historical_simulation_data(ALL_TICKERS)
    
    # TIP 데이터 추출
    tip_data = data_dict.get("TIP", {})
    tip_closes = tip_data.get("raw_closes", [])
    tip_current = tip_data.get("현재가", 0.0)
    
    tip_last11 = tip_closes[-11:] if len(tip_closes) >= 11 else tip_closes
    tip_ma11 = sum(tip_last11) / len(tip_last11) if tip_last11 else 1.0
    tip_ratio = tip_current / tip_ma11 if tip_ma11 > 0 else 1.0
    is_attack_a = tip_ratio > 1.0

    # 전략 B 카나리아 신호
    tip_score_b = (tip_data.get("1M", 0.0) + tip_data.get("3M", 0.0) + tip_data.get("6M", 0.0) + tip_data.get("9M", 0.0) + tip_data.get("12M", 0.0)) / 5
    is_attack_b = tip_score_b > 0

    # 전략 C: 동적 Z-Score 카나리아 신호 (1단계 고도화 반영)
    realtime_dy, realtime_z, mean_dy_36, std_dy_36 = get_sp500_dividend_and_zscore()
    is_attack_c = realtime_z > -0.5
    
    tab_2026, tab_a, tab_b, tab_c, tab_rank, tab_calc = st.tabs([
        "🏆 2026 혼합전략", 
        "🛡️ 전략 A", 
        "⚡ 전략 B", 
        "🔄 전략 C (고도화)",
        "🇺🇸 미국 ETF 랭킹",
        "🧮 자산 계산기"
    ])

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

    # [전략 C 할당 산출 - 동적 Z-Score 기반]
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

    with c_2026:
        st.header("🏆 2026년 혼합 전략")
        st.markdown(
            "안정 지향의 **전략 A**, 고수익 레버리지의 **전략 B**, 동적 밸류에이션 로테이션 **전략 C**를 "
            "각각 **$33.33\%$씩 동일 비중**으로 혼합하여 시장 전반의 변동성을 제어하는 2026년 추천 전략 모델입니다."
        )

        with st.expander("📖 2026 동적 자산배분 혼합 전략 명세서 (작동원칙)", expanded=False):
            st.markdown("""
            ### 🎯 혼합전략 개요
            본 전략은 시장의 거시경제 지표와 자산별 모멘텀을 실시간으로 추적하여 작동합니다.
            성격이 서로 다른 3가지 동적 자산배분 전략을 각각 **33.33%의 동일 비중**으로 혼합합니다.

            ---
            #### 🛡️ 전략 A: 대형 우량 자산 안정형 (33.33%)
            * **카나리아**: TIP 현재가 vs 11개월 이동평균(11MA) — 현재가 > 11MA면 공격, 이하면 방어
            * **공격 자산군 (12개)**: `QQQ, FEZ, GLD, IBB, SMH, EEM, XLK, LIT, XLE, UBT, XLV, QTUM`
            * **방어 자산군 (5개)**: `BIL, IEF, AGG, HYG, TBF`
            * **운용 가이드**: 공격 시 모멘텀 상위 4종목에 각 25%씩 균등 분배. 방어 시 1위 자산에 100% 투자(음수면 현금 100%).

            #### ⚡ 전략 B: 레버리지 공격형 (33.33%)
            * **카나리아**: TIP 1·3·6·9·12개월 단순평균 모멘텀 — 양수(> 0)면 공격, 이하면 방어
            * **공격 자산군 (3개)**: `TYD(미국채 3X), UPRO(S&P500 3X), VNQ(리츠)`
            * **방어 자산군 (3개)**: `DOG, RWM, TBF`
            * **운용 가이드**: 공격 시 1·3·6·12개월 가중평균 모멘텀 1위 자산 100% 몰빵. 방어 시 5개월 수익률 1위 자산(음수면 현금 100%).

            #### 🔄 전략 C: 배당 기반 섹터 로테이션 [고도화 반영] (33.33%)
            * **카나리아**: **S&P 500 최근 36개월 롤링 배당수익률 Z-Score ($Z_{\\text{DY}}$)**
              $$Z_{\\text{DY}} = \\frac{\\text{DY}_t - \\mu_{36}}{\\sigma_{36}}$$
              * **공격 신호**: $Z_{\\text{DY}} > -0.5$ (역사적 추세 대비 정상 및 저평가 국면)
              * **방어 신호**: $Z_{\\text{DY}} \\le -0.5$ (역사적 추세 대비 극단적 과열 국면)
            * **공격 자산군 (7개)**: `FDN, LIT, SMH, XLE, IGV, QQQM, XLU`
            * **방어 자산군 (5개)**: `GLD, PDBC, OILK, SHY, TLT`
            * **운용 가이드**: 공격 시 단순평균 모멘텀 1위 섹터 100% 투자. 방어 시 1위 방어자산 100% 투자(음수면 현금 100%).
            """)

        st.markdown("### 🚦 실시간 카나리아 신호 요약")
        c_sig1, c_sig2, c_sig3 = st.columns(3)
        c_sig1.metric("전략A (TIP 비율)", f"{tip_ratio:.3f}", "공격" if is_attack_a else "방어", delta_color="inverse" if not is_attack_a else "normal")
        c_sig2.metric("전략B (TIP 모멘텀)", f"{tip_score_b:.2f}%", "공격" if is_attack_b else "방어", delta_color="inverse" if not is_attack_b else "normal")
        c_sig3.metric("전략C (동적 Z-Score)", f"{realtime_z:+.2f}", f"공격 (DY {realtime_dy:.2f}%)" if is_attack_c else f"방어 (DY {realtime_dy:.2f}%)", delta_color="inverse" if not is_attack_c else "normal")

        st.markdown("### 📊 포트폴리오 비중 분배 현황")
        chart_col, table_col = st.columns([5, 5])
        
        with chart_col:
            try:
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
                st.bar_chart(df_mix.set_index("자산군 (Ticker)")["배분 비중 (%)"])
        
        with table_col:
            st.dataframe(df_mix, use_container_width=True, hide_index=True)

        st.markdown("### 💰 실시간 리밸런싱 목표 수량 계산기")
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
            st.caption("매월 최종 영업일 마감 데이터를 기준으로 실시간 모멘텀과 시그널을 연산한 포트폴리오 구성 비중입니다.")
            
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
                
                hist_portfolio, hist_sig_a, hist_sig_b, hist_sig_c, dy_c, z_c = compute_historical_portfolio_at_month_end(
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
                            st.caption("전략C (동적Z)")
                            st.markdown(f"**{sig_text_c}**<br/><small>(Z: {z_c:+.2f} / DY: {dy_c:.2f}%)</small>", unsafe_allow_html=True)
                        
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
                index=0,
                key="bt_start_select_mix"
            )
            bt_start_mix = bt_start_label_mix.split(" ")[0]
            st.markdown("**🛡️️ MDD 개선 로직 (옵션 설정)**")
            apply_cap_mix = st.checkbox("1단계: 단일 자산군 비중 상한(Cap 25%) 적용", value=False, key="apply_cap_mix")
            apply_vix_mix = st.checkbox("2단계: 전략 B 변동성 동적 조절 (VIX > 25 시 레버리지 절반 축소)", value=False, key="apply_vix_mix")
            apply_stop_mix = st.checkbox("3단계: 월중 하드스탑 (월중 낙폭 -7% 도달 시 전량 현금화)", value=False, key="apply_stop_mix")
            st.markdown('</div>', unsafe_allow_html=True)

        use_improved_mix = apply_cap_mix or apply_vix_mix or apply_stop_mix

        with st.spinner("2026 혼합전략 실시간 백테스트 엔진 구동 중... (전략 C 동적 Z-Score 연동)"):
            try:
                bt_tickers_mix = sorted(set(
                    OFFENSIVE_A + DEFENSIVE_A + OFFENSIVE_B + DEFENSIVE_B + OFFENSIVE_C + DEFENSIVE_C
                    + ["TIP", "SPY", "QQQ", "^VIX"]
                ))
                daily_px_mix = get_daily_price_history_a(bt_tickers_mix, start=bt_start_mix)
                monthly_px_mix = to_monthly_last_a(daily_px_mix)
                spy_divs_mix = get_spy_dividend_history()
                if use_improved_mix:
                    bt_results_mix = run_backtest_strategy_mix_improved_full(
                        monthly_px_mix, spy_divs_mix, daily_px=daily_px_mix,
                        apply_cap=apply_cap_mix, weight_cap=25.0,
                        apply_vix_dampening=apply_vix_mix, vix_threshold=25.0,
                        apply_stop_loss=apply_stop_mix, stop_loss_pct=-7.0,
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

            # 월별 세부 리밸런싱 기록
            st.markdown("##### 🗓️️ 월별 세부 리밸런싱 기록")
            display_bt_mix = bt_results_mix.copy()
            display_bt_mix["연월"] = display_bt_mix["date"].dt.strftime("%Y-%m")
            display_bt_mix["월 수익률"] = display_bt_mix["monthly_return"].apply(lambda x: f"{x:+.2f}%")
            display_bt_mix["낙폭"] = display_bt_mix["drawdown"].apply(lambda x: f"{x:.2f}%")
            display_bt_mix["NAV"] = display_bt_mix["nav"].apply(lambda x: f"{x:.1f}")

            st.dataframe(
                display_bt_mix[["연월", "mode", "월 수익률", "weights_str", "NAV", "낙폭"]].iloc[::-1],
                use_container_width=True, hide_index=True
            )

    with c_a:
        st.header("🛡️ 전략 A (안정형)")
        st.markdown("**1단계: 카나리아 신호 판단** \n"
                    "신호 비율($TIP 현재가 / TIP_{11MA}$)이 $1.0$을 초과하면 공격 모드, 이하이면 방어 모드로 진입합니다.")
        col1, col2, col3 = st.columns(3)
        col1.metric("TIP 현재가", f"${tip_current:.2f}")
        col2.metric("TIP 11M 이평", f"${tip_ma11:.2f}")
        col3.metric("신호 비율 (현재/이평)", f"{tip_ratio:.3f}")
        
        if is_attack_a:
            st.success("🔥 **현재 모드: 공격 자산 모드** - 시장의 위험 신호가 낮습니다.")
            df_off_a = df_all[df_all["Ticker"].isin(OFFENSIVE_A)].copy().sort_values(by="A_공격스코어", ascending=False)
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
            df_def_a = df_all[df_all["Ticker"].isin(DEFENSIVE_A)].copy().sort_values(by="A_방어스코어", ascending=False)
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

    with c_b:
        st.header("⚡ 전략 B (공격형)")
        st.markdown("**1단계: 카나리아 신호 판단** \n"
                    "TIP의 단순 모멘텀 스코어가 양수($> 0$)이면 공격, 음수($\\le 0$)이면 방어 모드로 진입합니다.")
        col1_b, col2_b = st.columns(2)
        col1_b.metric("TIP 현재가", f"${tip_current:.2f}")
        col2_b.metric("TIP 단순 모멘텀", f"{tip_score_b:.2f}%")
        
        if is_attack_b:
            st.success("⚔️ **현재 모드: 공격 자산 모드** - 레버리지 투자를 적극 실행합니다.")
            df_off_b = df_all[df_all["Ticker"].isin(OFFENSIVE_B)].copy().sort_values(by="B_공격스코어", ascending=False)
            st.write("**공격 자산 순위 (1-3-6-12M 가중 평균 모멘텀):**")
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
            df_def_b = df_all[df_all["Ticker"].isin(DEFENSIVE_B)].copy().sort_values(by="5M", ascending=False)
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

    # ============================================================
    # 탭 C: 전략 C (섹터로테이션) - 동적 Z-Score 고도화 화면
    # ============================================================
    with c_c:
        st.header("🔄 전략 C (동적 배당 Z-Score 섹터 로테이션)")
        
        with st.expander("📖 전략 C 고도화 실행 명세서 (작동원칙)", expanded=False):
            st.markdown("""
            ### 🔄 전략 C 핵심 구조 (S&P 500 동적 배당수익률 Z-Score 시스템)
            빅테크 중심의 지수 개편과 자사주 매입 증가로 배당수익률의 절대 레벨이 구조적으로 낮아진 문제를 해결하기 위해,
            **과거 고정 기준선(1.33%)을 폐기하고 최근 36개월 롤링 Z-Score($Z_{\\text{DY}}$)**를 카나리아 지표로 도입했습니다.

            #### 1단계 — 동적 롤링 Z-Score 카나리아 판독 (신호)
            * S&P 500(SPY)의 최근 12개월 누적 배당수익률 시계열을 기준으로 최근 36개월 평균과 표준편차를 실시간 계산합니다.
            $$Z_{\\text{DY}} = \\frac{\\text{DY}_t - \\mu_{36}(\\text{DY})}{\\sigma_{36}(\\text{DY})}$$
            * **공격 신호**: $Z_{\\text{DY}} > -0.5$ (역사적 추세 대비 정상 및 저평가 국면)
            * **방어 신호**: $Z_{\\text{DY}} \\le -0.5$ (역사적 추세 대비 극단적 과열 국면)

            #### 2단계 — 공격/방어 자산 매수 규칙
            * **공격 신호 (주도 섹터 자산 7개)**: `FDN, LIT, SMH, XLE, IGV, QQQM, XLU`
              * $1\\cdot 3\\cdot 6\\cdot 12\\text{M}$ 단순평균 모멘텀 1위 섹터에 **100% 집중 투자**
            * **방어 신호 (원자재·방어 자산 5개)**: `GLD, PDBC, OILK, SHY, TLT`
              * $1\\cdot 3\\cdot 6\\cdot 9\\cdot 12\\text{M}$ 단순평균 모멘텀 1위 자산에 **100% 투자**
              * (단, 1위 자산의 모멘텀 스코어가 $\\le 0$인 경우 **현금 100% 대피**)
            """)

        st.markdown(
            "**1단계: 동적 카나리아 신호 판단 (S&P 500 36개월 배당 Z-Score)** \n"
            "최근 36개월 배당수익률의 롤링 표준화 점수인 $Z_{\\text{DY}}$가 **$-0.5$ 초과** 시 공격 모드, **$-0.5$ 이하** 시 시장 과열로 방어 모드로 진입합니다."
        )
        
        st.markdown(f"""
        <div class="control-panel">
            <div class="control-header">📊 S&P 500 (SPY) 동적 롤링 밸류에이션 모니터링</div>
            <div class="control-subheader">
                최근 36개월 롤링 평균 및 표준편차를 동적 반영하여 '신호 동결' 왜곡을 방지한 고도화 지표입니다.<br/>
                • <b>실시간 S&P 500 배당수익률: {realtime_dy:.2f}%</b> (36개월 롤링 평균: {mean_dy_36:.2f}%, 표준편차: {std_dy_36:.2f}%)<br/>
                • <b>동적 표준화 점수 (Z-Score): {realtime_z:+.2f}</b><br/>
                • <b>신호 판정 기준선: Z > -0.50</b> (현재: {"🟢 공격 국면 (정상/저평가)" if is_attack_c else "🛡️ 방어 국면 (극단적 과열 경보)"})
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        col_c1, col_c2, col_c3 = st.columns(3)
        col_c1.metric("실시간 SPY 배당수익률", f"{realtime_dy:.2f}%")
        col_c2.metric("36M 롤링 Z-Score", f"{realtime_z:+.2f}", "기준선: > -0.5")
        col_c3.metric("최종 카나리아 판정", "공격 (Offensive)" if is_attack_c else "방어 (Defensive)", delta_color="normal" if is_attack_c else "inverse")
        
        if is_attack_c:
            st.success(f"🔥 **현재 모드: 주도 섹터 공격 모드** ($Z={realtime_z:+.2f} > -0.5$) - 거시 밸류에이션이 정상 범위에 있어 주도 섹터를 적극 매수합니다.")
            df_off_c = df_all[df_all["Ticker"].isin(OFFENSIVE_C)].copy().sort_values(by="A_공격스코어", ascending=False)
            
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
            st.warning(f"🛡️ **현재 모드: 원자재 방어 자산 모드** ($Z={realtime_z:+.2f} \\le -0.5$) - 시장 밸류에이션 과열로 원자재/채권 자산으로 대피합니다.")
            df_def_c = df_all[df_all["Ticker"].isin(DEFENSIVE_C)].copy().sort_values(by="A_방어스코어", ascending=False)
            
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
        st.markdown("### 🛑 전략 C 백테스트 성과 분석 (동적 Z-Score 엔진)")

        with st.container():
            st.markdown('<div class="control-panel">', unsafe_allow_html=True)
            st.markdown('<div class="control-header">⚙️ 데이터 범위 및 Z-Score 임계치 설정</div>', unsafe_allow_html=True)
            col_z1, col_z2 = st.columns(2)
            with col_z1:
                bt_start_label_c = st.selectbox(
                    "분석 및 백테스트 시작일",
                    ["2018-01-01 (코로나 및 금리인상기 포함)", "2015-01-01 (장기 검증)", "2020-01-01 (최근 트렌드)"],
                    index=0,
                    key="bt_start_select_c"
                )
                bt_start_c = bt_start_label_c.split(" ")[0]
            with col_z2:
                z_thresh_input = st.number_input(
                    "Z-Score 공격/방어 임계치",
                    value=-0.50,
                    step=0.10,
                    format="%.2f",
                    help="Z-Score가 이 값 초과 시 공격 모드, 이하 시 방어 모드로 진입합니다. (기본 권고: -0.5)"
                )
            st.caption("선택한 조건 기준으로 전략 C 백테스트 시뮬레이션이 즉시 재계산됩니다.")
            st.markdown('</div>', unsafe_allow_html=True)

        with st.spinner("전략 C 실시간 백테스트 엔진 구동 중..."):
            try:
                bt_tickers_c = sorted(set(OFFENSIVE_C + DEFENSIVE_C + ["SPY", "QQQ"]))
                daily_px_c = get_daily_price_history_a(bt_tickers_c, start=bt_start_c)
                monthly_px_c = to_monthly_last_a(daily_px_c)
                spy_divs_c = get_spy_dividend_history()
                bt_results_c = run_backtest_strategy_c_full(monthly_px_c, spy_divs_c, z_threshold=z_thresh_input)
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
            calc_expense = st.number_input("매월 지출/생활비 (만원 ₩)", min_value=0, value=0, step=10)
            calc_years = st.slider("시뮬레이션 투자 기간 (년)", min_value=1, max_value=40, value=15)
        with col_inp2:
            calc_cagr = st.number_input("연 목표 수익률 CAGR (%)", min_value=0.0, max_value=100.0, key="cagr_input", step=0.1)
            calc_inflation = st.number_input("연 예상 물가상승률 (%)", min_value=0.0, max_value=20.0, value=3.0, step=0.1)
            calc_expense_start = st.number_input("지출 시작 시점 (년차)", min_value=1, max_value=max(1, calc_years), value=1, step=1)
            calc_tax_opt = st.selectbox("세율 설정", ["일반과세 (15.4%)", "미국주식양도세 (22.0%)", "비과세 계좌 (0.0% / ISA 및 연금저축)", "사용자 정의"])
        
        tax_rate = 15.4 if calc_tax_opt == "일반과세 (15.4%)" else 22.0 if calc_tax_opt == "미국주식양도세 (22.0%)" else 0.0

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
                return f"{sign}{eok}억 {man:,}만원" if man > 0 else f"{sign}{eok}억원"
            else:
                man = int(val // 10000)
                return f"{sign}{man:,}만원"

        last_rec = records[-1]
        st.markdown("### 🏆 시뮬레이션 최종 기대 성과 요약")
        sum_col1, sum_col2, sum_col3 = st.columns(3)
        sum_col1.metric("총 순 원금(저축-지출)", format_krw(last_rec["누적 납입원금"]))
        sum_col2.metric("세후 최종 자산", format_krw(last_rec["세후 수령예정액"]))
        sum_col3.metric("실질구매력 가치", format_krw(last_rec["세후 실질가치 (물가반영)"]))
