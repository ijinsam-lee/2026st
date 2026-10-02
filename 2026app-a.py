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

/* ── 상단 탭 메뉴: 2줄 구성 ──
   위줄 = 영문 그룹 라벨(STRATEGY / INSIGHTS), 아래줄 = 탭. 탭 사이 틈 없이 색으로만 구분합니다.
   (그룹 라벨·data-grp 속성은 아래 탭 고정용 JS가 만들어 줍니다. 앞 4개 탭 = 전략, 나머지 = 정보) */
.stTabs [data-baseweb="tab-list"] {
    background-color: transparent !important;
    box-shadow: none !important;
    margin-bottom: 20px !important;
}
.stTabs div.tab-grid {
    display: grid !important;
    grid-template-columns: repeat(8, minmax(max-content, 1fr)) !important; /* 탭 개수(8)와 맞춰야 합니다 */
    grid-auto-flow: row !important;
    gap: 0 !important;
    column-gap: 0 !important;
    row-gap: 0 !important;
    width: 100% !important;
    box-sizing: border-box !important;
    padding: 0 !important;
    background-color: transparent !important;
    border: 1px solid #94a3b8 !important;
    border-radius: 0 !important;  /* 모서리 라운드 없음(사각) */
    overflow-x: auto !important;
    overflow-y: hidden !important;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05) !important;
}
.stTabs .tab-grp-label {
    grid-row: 1;
    display: block;
    text-align: center;
    font-size: 0.78rem;
    font-weight: 800;
    letter-spacing: 0.22em;
    line-height: 1.2;
    padding: 6px 0;
    user-select: none;
    pointer-events: none;
    border-bottom: 1px solid #94a3b8;
}
.stTabs .tab-grp-label.s { grid-column: 1 / span 4; background-color: #c3d6f6; color: #1e3a8a; }
.stTabs .tab-grp-label.i { grid-column: 5 / span 4; background-color: #bdeee3; color: #0f766e; border-left: 2px solid #64748b; }

/* 개별 탭: 틈·둥근 모서리 없이 그룹 색으로 이어 붙임 */
.stTabs [data-baseweb="tab"] {
    background-color: transparent !important;
    border-radius: 0 !important;
    margin: 0 !important;
    padding: 10px 12px !important;
    font-weight: 800 !important;
    font-size: 0.85rem !important;
    color: #334155 !important;
    border: none !important;
    white-space: nowrap !important;
    transition: background-color 0.2s ease-in-out !important;
    text-align: center !important;
}
.stTabs [role="tab"][data-grp="s"] { background-color: #e1ebfb !important; }
.stTabs [role="tab"][data-grp="i"] { background-color: #dcf6ef !important; }
/* 탭 사이 얇은 구분선 / 그룹 경계는 굵은 선 */
.stTabs [role="tab"][data-grp="s"]:not([data-first="1"]) { border-left: 1px solid rgba(30, 58, 138, 0.28) !important; }
.stTabs [role="tab"][data-grp="i"]:not([data-first="1"]) { border-left: 1px solid rgba(15, 118, 110, 0.28) !important; }
.stTabs [role="tab"][data-grp="i"][data-first="1"] { border-left: 2px solid #64748b !important; }
/* [선택된 탭] 그룹의 진한 색 + 흰 글씨 */
.stTabs [role="tab"][data-grp="s"][aria-selected="true"] { background-color: #1e3a8a !important; color: #ffffff !important; }
.stTabs [role="tab"][data-grp="i"][aria-selected="true"] { background-color: #0f766e !important; color: #ffffff !important; }
.stTabs [aria-selected="true"] { color: #ffffff !important; box-shadow: none !important; }

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

# ============================================================
# 백테스트 비용·세금 반영 설정 (슬리피지 / 미국주식 양도소득세) — 선택 반영
# ============================================================
def fmt_krw(x):
    """원화를 읽기 쉬운 단위(억원/만원/원)로 표시."""
    x = float(x)
    a = abs(x)
    if a >= 1e8:
        return f"{x / 1e8:,.2f}억원"
    if a >= 1e4:
        return f"{x / 1e4:,.0f}만원"
    return f"{x:,.0f}원"


# 설정 박스를 은은한 노란색으로 강조 (마커 + JS 이중 지정)
st.markdown("""<style>
[data-testid="stExpander"].cost-exp details, [data-testid="stExpander"]:has(.cost-exp-marker) details{
  border:1.5px solid #f2c94c !important;background:#fffdf4 !important;border-radius:12px}
[data-testid="stExpander"].cost-exp summary, [data-testid="stExpander"]:has(.cost-exp-marker) summary{
  background:#fff6d6 !important;font-weight:700;border-radius:10px}
</style>""", unsafe_allow_html=True)

with st.expander("⚙️ 백테스트 비용·세금 반영 설정", expanded=False):
    st.markdown('<span class="cost-exp-marker"></span>', unsafe_allow_html=True)
    COST_CAPITAL = st.number_input(
        "① 초기 투자금 (원)", min_value=100000, max_value=100000000000, value=10000000, step=1000000,
        format="%d", key="cost_capital",
        help="백테스트 시작 시점에 이 금액을 투자했다고 가정하고, 슬리피지와 양도세를 원화로 환산합니다. 자산 계산기의 초기 투자금에도 함께 반영됩니다.")
    st.caption(f"= ₩{COST_CAPITAL:,.0f} ({fmt_krw(COST_CAPITAL)}) · 백테스트 시작일에 전액 투자한 것으로 가정합니다.")
    _cs1, _cs2 = st.columns(2)
    COST_SLIP_ON = _cs1.checkbox("② 슬리피지 반영", value=False, key="cost_slip_on",
                                 help="종목을 사고팔 때마다 체결가 차이로 손해 보는 비용을 월별 수익에서 차감합니다.")
    COST_SLIP_PCT = _cs1.number_input("슬리피지 (매수·매도 각 1회당 %)", min_value=0.0, max_value=5.0, value=1.0, step=0.1,
                                      key="cost_slip_pct", disabled=not COST_SLIP_ON)
    if COST_SLIP_ON:
        _cs1.caption(f"전량 교체 1회 ≈ ₩{COST_CAPITAL * COST_SLIP_PCT / 100 * 2:,.0f} (매도+매수)")
    COST_TAX_ON = _cs2.checkbox("③ 미국주식 양도소득세 반영", value=False, key="cost_tax_on",
                                help="매년 12월 말에 그 해의 순이익에서 기본공제를 뺀 금액에 세율을 곱해 자산에서 차감합니다.")
    COST_TAX_PCT = _cs2.number_input("양도소득세율 (%)", min_value=0.0, max_value=50.0, value=22.0, step=0.5,
                                     key="cost_tax_pct", disabled=not COST_TAX_ON)
    COST_DEDUCT = _cs2.number_input("연 기본공제 (원)", min_value=0, max_value=100000000, value=2500000, step=500000,
                                    format="%d", key="cost_deduct", disabled=not COST_TAX_ON,
                                    help="해외주식 양도차익에서 매년 빼주는 금액(기본 250만원). 0으로 두면 공제 없이 계산합니다.")
    st.caption(
        "• 슬리피지: 리밸런싱으로 바뀐 비중만큼 매수·매도 각각에 부과합니다. 한 종목을 전량 교체하면 매도 1% + 매수 1% = 약 2%가 차감됩니다. "
        "현금 전환·월중 하드스탑 청산 후 재진입도 거래로 계산합니다.\n"
        "• 양도세: 해마다 12월 말 순이익에서 기본공제(기본 250만원)를 뺀 금액에 세율을 부과합니다(손실 해는 0, 이월공제 없음). "
        "환전 비용은 반영하지 않으며, 진행 중인 올해분 세금은 연말에 차감됩니다.\n"
        "• 설정은 혼합전략·전략 A·B·C 백테스트 결과(CAGR·MDD·NAV·월별 표·차트)에 모두 적용됩니다."
    )


def _cost_cfg():
    """현재 상단 설정을 (캐시 키로 쓸 수 있는) 튜플로 반환: (슬리피지 on, %, 세금 on, %, 초기 투자금, 연 공제)."""
    return (bool(COST_SLIP_ON), float(COST_SLIP_PCT), bool(COST_TAX_ON), float(COST_TAX_PCT), float(COST_CAPITAL), float(COST_DEDUCT))


def apply_trading_costs(bt, cfg=None):
    """백테스트 결과(월별 DataFrame)에 슬리피지·양도세를 반영한 새 결과를 돌려줍니다. 둘 다 꺼져 있으면 원본 그대로.
    NAV 100 = 초기 투자금(COST_CAPITAL원)으로 보고 원화 금액(slip_krw, tax_krw)을 함께 기록합니다."""
    slip_on, slip_pct, tax_on, tax_pct, cap, deduct = cfg if cfg is not None else _cost_cfg()
    if bt is None or len(bt) == 0 or not (slip_on or tax_on):
        return bt
    slip = slip_pct / 100.0 if slip_on else 0.0
    tax = tax_pct / 100.0 if tax_on else 0.0
    krw_per_pt = cap / 100.0
    df = bt.reset_index(drop=True).copy()
    nav, peak, year_start_nav = 100.0, 100.0, 100.0
    prev_alloc = {}
    navs, rets, dds, slip_k, tax_k, gain_k, taxable_k = [], [], [], [], [], [], []
    for _, row in df.iterrows():
        gross = float(row["monthly_return"]) / 100.0
        alloc = dict(row["alloc"]) if isinstance(row["alloc"], dict) else {}
        stopped = "월중손절" in str(row["mode"])
        keys = (set(alloc) | set(prev_alloc)) - {"CASH (현금)"}
        traded = sum(abs(alloc.get(k, 0.0) - prev_alloc.get(k, 0.0)) for k in keys) / 100.0
        buy_cost = slip * traded
        stop_cost = slip * sum(w for k, w in alloc.items() if k != "CASH (현금)") / 100.0 if stopped else 0.0
        nav_before = nav
        nav_after_buy = nav_before * (1 - buy_cost)
        nav_mid = nav_after_buy * (1 + gross)
        nav = nav_mid * (1 - stop_cost)
        slip_pts = nav_before * buy_cost + nav_mid * stop_cost
        tax_pts, gain_krw, taxable_krw = 0.0, np.nan, np.nan
        if tax > 0 and pd.Timestamp(row["date"]).month == 12:
            gain_krw = (nav - year_start_nav) * krw_per_pt
            taxable_krw = max(0.0, gain_krw - float(deduct))
            tax_pts = taxable_krw * tax / krw_per_pt
            nav -= tax_pts
            year_start_nav = nav
        peak = max(peak, nav)
        navs.append(nav)
        rets.append((nav / nav_before - 1) * 100.0)
        dds.append((nav / peak - 1) * 100.0)
        slip_k.append(slip_pts * krw_per_pt)
        tax_k.append(tax_pts * krw_per_pt)
        gain_k.append(gain_krw)
        taxable_k.append(taxable_krw)
        prev_alloc = {} if stopped else alloc  # 월중 손절 후에는 현금 상태에서 다시 진입
    df["nav"], df["monthly_return"], df["drawdown"] = navs, rets, dds
    df["slip_krw"], df["tax_krw"], df["gain_krw"], df["taxable_krw"] = slip_k, tax_k, gain_k, taxable_k
    return df


def cost_status_caption(bt):
    """현재 비용·세금 반영 상태를 원화 카드와 연도별 표로 표시."""
    if not (COST_SLIP_ON or COST_TAX_ON) or "slip_krw" not in bt:
        st.caption("💸 거래비용·세금 미반영 (맨 위 '⚙️ 백테스트 비용·세금 반영 설정'에서 선택)")
        return
    slip_sum = float(bt["slip_krw"].sum())
    tax_sum = float(bt["tax_krw"].sum())
    final_krw = float(bt["nav"].iloc[-1]) / 100.0 * COST_CAPITAL
    cards = []
    if COST_SLIP_ON:
        cards.append((f"슬리피지 누적 ({COST_SLIP_PCT:g}%/회)", fmt_krw(slip_sum), f"₩{slip_sum:,.0f}", "neg"))
    if COST_TAX_ON:
        cards.append((f"양도세 누적 ({COST_TAX_PCT:g}%)", fmt_krw(tax_sum), f"₩{tax_sum:,.0f} · 연 공제 {fmt_krw(COST_DEDUCT)}", "neg"))
    cards.append(("세후 최종 자산", fmt_krw(final_krw), f"₩{final_krw:,.0f} · 초기 투자금 {fmt_krw(COST_CAPITAL)}", "neutral"))
    st.caption(f"✅ 비용·세금 반영 중 · 초기 투자금 ₩{COST_CAPITAL:,.0f} 기준")
    hl_cards(cards)
    d = bt.copy()
    d["연도"] = pd.to_datetime(d["date"]).dt.year
    rows = []
    for yr, g in d.groupby("연도"):
        gain = g["gain_krw"].max()
        taxable = g["taxable_krw"].max()
        rows.append({
            "연도": int(yr),
            "연말 자산(세후)": f"₩{g['nav'].iloc[-1] / 100.0 * COST_CAPITAL:,.0f}",
            "순이익(세전)": f"₩{gain:,.0f}" if pd.notna(gain) else "연말 전",
            "과세표준(공제후)": f"₩{taxable:,.0f}" if pd.notna(taxable) else "-",
            "양도세": f"₩{g['tax_krw'].sum():,.0f}",
            "슬리피지": f"₩{g['slip_krw'].sum():,.0f}",
        })
    with st.expander("💴 연도별 비용·세금 내역 (원)", expanded=False):
        st.dataframe(pd.DataFrame(rows).iloc[::-1], use_container_width=True, hide_index=True)

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
#     3개 전략(각 33.33%)을 합산했을 때 특정 티커의 최종 비중이 상한(기본 35%)을 넘으면
#     초과분을 현금(CASH)으로 자동 전환하여 강제 분산시킵니다.
#   - 2단계 개선: 월중 하드스탑(Intra-month Stop-loss)
#     일별 가격으로 월중 누적 손실을 감시하다가, 포트폴리오가 월초(전월 말 종가) 대비 임계치
#     (기본 -7%)까지 하락하면 그 시점 이후 월말까지 전량 현금화한 것으로 간주해 추가 손실을 차단합니다.
# ============================================================
@st.cache_data(ttl=3600)
def run_backtest_strategy_mix_improved_full(
    monthly_px, spy_divs, daily_px=None,
    apply_cap=False, weight_cap=35.0,
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
                    stop_note = f" 🛑월중손절({stop_triggered.index[0].strftime('%m/%d')})"
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

def compute_historical_portfolio_at_month_end(prices_dict, spy_divs, target_date, OFFENSIVE_A, DEFENSIVE_A, OFFENSIVE_B, DEFENSIVE_B, OFFENSIVE_C, DEFENSIVE_C, return_parts=False):
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
        if return_parts:
            _cash = {"CASH (현금)": 100.0}
            return {"CASH (현금)": 100.0}, False, False, False, 1.32, {"A": dict(_cash), "B": dict(_cash), "C": dict(_cash)}
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
    if return_parts:
        return clean_portfolio, is_attack_a_hist, is_attack_b_hist, is_attack_c_hist, dy_val, {
            "A": dict(alloc_a_hist), "B": dict(alloc_b_hist), "C": dict(alloc_c_hist),
        }
    return clean_portfolio, is_attack_a_hist, is_attack_b_hist, is_attack_c_hist, dy_val

# ============================================================
# 자산 계산기 퀵 프리셋용: 각 전략 탭의 '초기 설정'과 같은 조건의 실측 CAGR
#   - 초기 설정 = 백테스트 시작일 2015-01-01 (장기 검증), 혼합전략 안전장치(비중 상한·하드스탑) 미적용
#   - 각 전략 탭과 동일한 종목·엔진·CAGR 계산식(일수 ÷ 365.25)을 사용하므로 탭에 표시되는 값과 일치합니다.
# ============================================================
PRESET_START = "2015-01-01"
PRESET_FALLBACK_CAGR = {"mix": 38.7, "A": 27.3, "B": 36.4, "C": 46.7}  # 데이터 로딩 실패 시에만 사용


def _cagr_from_bt(bt):
    days = (bt["date"].iloc[-1] - bt["date"].iloc[0]).days
    years = days / 365.25 if days > 0 else 1.0
    return ((bt["nav"].iloc[-1] / 100.0) ** (1 / years) - 1) * 100


@st.cache_data(ttl=3600)
def get_preset_cagrs(start=PRESET_START, cost_cfg=None):
    out = {}
    try:
        spy_divs = get_spy_dividend_history()
    except Exception:
        spy_divs = pd.Series(dtype=float)
    specs = {
        "A": (sorted(set(OFFENSIVE_A + DEFENSIVE_A + ["TIP", "QQQ"])), lambda m: run_backtest_strategy_a_full(m)),
        "B": (sorted(set(OFFENSIVE_B + DEFENSIVE_B + ["TIP", "QQQ"])), lambda m: run_backtest_strategy_b_full(m)),
        "C": (sorted(set(OFFENSIVE_C + DEFENSIVE_C + ["SPY", "QQQ"])), lambda m: run_backtest_strategy_c_full(m, spy_divs)),
        "mix": (
            sorted(set(OFFENSIVE_A + DEFENSIVE_A + OFFENSIVE_B + DEFENSIVE_B + OFFENSIVE_C + DEFENSIVE_C + ["TIP", "SPY", "QQQ"])),
            lambda m: run_backtest_strategy_mix_full(m, spy_divs),
        ),
    }
    for key, (tickers, runner) in specs.items():
        try:
            daily = get_daily_price_history_a(tickers, start=start)
            bt = runner(to_monthly_last_a(daily))
            if cost_cfg is not None and len(bt) > 0:
                bt = apply_trading_costs(bt, cost_cfg)  # 상단 슬리피지·세금 설정 반영
            out[key] = round(float(_cagr_from_bt(bt)), 2) if len(bt) > 0 else None
        except Exception:
            out[key] = None
    return out


# ============================================================
# 월중 하드스탑 실시간 모니터 (이번 달 일별 수익률 추적)
#   - 직전 월말에 확정된 혼합 포트폴리오를 이번 달 보유 포트폴리오로 보고,
#     직전 월말 종가 대비 일별 누적 수익률을 백테스트와 같은 방식(비중 × 종목 누적수익률 합)으로 계산합니다.
# ============================================================
def now_us_eastern():
    """미국 동부 시간 기준 현재 시각 (한국 시간과 날짜가 달라 월말 판정이 어긋나는 문제 방지)."""
    try:
        return pd.Timestamp.now(tz="America/New_York").tz_localize(None)
    except Exception:
        return pd.Timestamp(datetime.datetime.utcnow() - datetime.timedelta(hours=4))


@st.cache_data(ttl=300)
def get_intramonth_daily_prices(tickers, start):
    """보유 종목의 일별 종가 (5분 캐시). tickers는 tuple."""
    tickers = list(tickers)
    if not tickers:
        return pd.DataFrame()
    try:
        df = yf.download(tickers, start=start, interval="1d", progress=False, auto_adjust=True)
    except Exception:
        return pd.DataFrame()
    if df is None or len(df) == 0:
        return pd.DataFrame()
    if isinstance(df.columns, pd.MultiIndex):
        close = df["Close"] if "Close" in df.columns.levels[0] else df
    else:
        close = df[["Close"]].rename(columns={"Close": tickers[0]}) if "Close" in df.columns else df
    if isinstance(close, pd.Series):
        close = close.to_frame(tickers[0])
    if getattr(close.index, "tz", None) is not None:
        close.index = close.index.tz_localize(None)
    return close.dropna(how="all")


def render_intramonth_stop_monitor(hist_prices, spy_divs_hist, strategy="mix"):
    """strategy: "mix"(혼합전략) 또는 "A" / "B" / "C"(개별 전략, 전략 자산의 100% 기준)."""
    is_mix = strategy == "mix"
    label = "혼합" if is_mix else f"전략 {strategy}"
    if is_mix:
        st.markdown("### 🛑 월중 하드스탑 모니터 (이번 달 일별 수익률)")
    else:
        st.markdown(f"### 📈 전략 {strategy} 이번 달 일별 수익률")
    st.caption("⚠️ 이 일별 표는 슬리피지·거래비용·세금·환전 비용이 반영되지 않았으며 백테스트 비용·세금 설정과 무관합니다. 실제 체결 가격과 계좌 수익률은 이 값과 다를 수 있습니다.")

    if is_mix:
        stop_pct = float(st.session_state.get("mix_stop_pct", -7.0))
        cap_on = bool(st.session_state.get("apply_cap_mix", False))
        cap_pct = float(st.session_state.get("mix_cap_pct", 35.0))
    else:
        stop_pct = None  # 개별 전략은 월중 하드스탑을 운용하지 않음
        cap_on = False
        cap_pct = 100.0

    if not hist_prices or "SPY" not in hist_prices:
        st.warning("일별 가격 데이터를 불러오지 못해 이번 달 일별 수익률을 표시할 수 없습니다.")
        return

    # 1) 직전 완료 월말(= 이번 달 포트폴리오를 확정한 날) 찾기
    spy_idx = hist_prices["SPY"].index
    if getattr(spy_idx, "tz", None) is not None:
        spy_idx = spy_idx.tz_localize(None)
    # 월 판정은 미국 동부 시간 기준 (한국 시간 새벽에는 미국이 아직 전날 장중)
    now = now_us_eastern()
    month_ends = pd.Series(spy_idx, index=spy_idx).groupby([spy_idx.year, spy_idx.month]).max().tolist()
    completed = [pd.Timestamp(d) for d in month_ends if not (d.year == now.year and d.month == now.month)]
    if not completed:
        st.info("직전 월말 데이터가 없습니다.")
        return

    if st.button("🔄 최신 가격으로 새로고침", key=f"intramonth_refresh_{strategy}"):
        get_intramonth_daily_prices.clear()

    base_date = completed[-1]
    view_end = None      # 지난달 표시 모드일 때 마지막 날짜
    period_word = "이번 달"
    # 새 달 첫 거래일 데이터가 아직 없으면 → 지난달 일별 흐름을 대신 표시
    spy_fresh = get_intramonth_daily_prices(("SPY",), (base_date - pd.Timedelta(days=10)).strftime("%Y-%m-%d"))
    spy_dates = spy_fresh.index if not spy_fresh.empty else spy_idx
    if not (spy_dates > base_date).any() and len(completed) >= 2:
        view_end = base_date
        base_date = completed[-2]
        period_word = f"지난달({view_end.month}월)"
        st.info(
            f"{view_end.strftime('%Y-%m-%d')} 이후 새 달 거래일 데이터가 아직 없어 "
            f"{view_end.month}월 한 달의 일별 흐름을 표시합니다. 새 달 첫 거래일 장 마감 뒤 자동으로 이번 달로 바뀝니다."
        )

    # 2) 그 월말 기준 혼합 포트폴리오 (월말 리밸런싱 역사와 같은 계산)
    held_mix, _, _, _, _, parts = compute_historical_portfolio_at_month_end(
        hist_prices, spy_divs_hist, base_date,
        OFFENSIVE_A, DEFENSIVE_A, OFFENSIVE_B, DEFENSIVE_B, OFFENSIVE_C, DEFENSIVE_C,
        return_parts=True,
    )
    held = held_mix if is_mix else parts.get(strategy, {"CASH (현금)": 100.0})
    held = {t: w for t, w in held.items() if w > 0.01}
    pre_cap = dict(held)  # 상한 적용 전 합산 비중 (전략별 분해용)

    # 비중 상한이 켜져 있으면 백테스트와 동일하게 초과분을 현금으로
    cap_note = ""
    if cap_on:
        excess = 0.0
        capped = {}
        for t, w in held.items():
            if t == "CASH (현금)":
                continue
            if w > cap_pct:
                capped[t] = cap_pct
                excess += w - cap_pct
            else:
                capped[t] = w
        capped["CASH (현금)"] = held.get("CASH (현금)", 0.0) + excess
        held = {t: w for t, w in capped.items() if w > 0.01}
        if excess > 0.01:
            cap_note = f" · 비중 상한 {cap_pct:.0f}% 적용(초과분 {excess:.1f}%p 현금)"

    risky = [t for t in held if t != "CASH (현금)"]
    st.caption(
        f"보유 기준: {base_date.strftime('%Y-%m-%d')} 월말 확정 {label} 포트폴리오{cap_note} · "
        f"기준가: 같은 날 종가 · "
        f"{f'하드스탑 임계치 {stop_pct:.1f}% (백테스트 설정값과 연동) · ' if is_mix else ''}가격은 5분마다 갱신"
    )

    if not risky:
        st.info(f"{period_word} {label} 포트폴리오는 전량 현금 보유라 월중 손실 위험이 없습니다.")
        return

    start = (base_date - pd.Timedelta(days=10)).strftime("%Y-%m-%d")
    px = get_intramonth_daily_prices(tuple(sorted(risky)), start)
    missing = [t for t in risky if t not in px.columns]
    if px.empty or missing:
        # 실패 시 1시간 캐시된 일별 데이터로 대체
        px = pd.DataFrame({t: hist_prices[t] for t in risky if t in hist_prices})
        if getattr(px.index, "tz", None) is not None:
            px.index = px.index.tz_localize(None)
    px = px.sort_index().ffill()

    base_px = px[px.index <= base_date]
    month_px = px[px.index > base_date]
    if view_end is not None:
        month_px = month_px[month_px.index <= view_end]
    if base_px.empty:
        st.warning("기준일 종가를 찾지 못했습니다.")
        return
    if month_px.empty:
        st.info(f"{base_date.strftime('%Y-%m-%d')} 이후 아직 거래일 데이터가 없습니다. 첫 거래일 장 마감 뒤 다시 확인하세요.")
        return
    base_row = base_px.iloc[-1]

    # 3) 일별 누적 수익률 = Σ 비중 × (종가 / 기준가 − 1)  (백테스트 하드스탑과 동일)
    cum = pd.Series(0.0, index=month_px.index)
    contrib_rows = []
    rets = {}
    for t in risky:
        w = held[t] / 100.0
        b = base_row.get(t, np.nan)
        if t not in month_px.columns or pd.isna(b) or b == 0:
            continue
        t_ret = (month_px[t] / b - 1.0).fillna(0.0)
        rets[t] = t_ret
        cum = cum + w * t_ret
        last_px = month_px[t].dropna().iloc[-1] if month_px[t].notna().any() else np.nan
        contrib_rows.append({
            "자산 (Ticker)": t,
            "비중 (%)": round(held[t], 2),
            "월초 기준가 ($)": round(float(b), 2),
            "최근 종가 ($)": round(float(last_px), 2) if pd.notna(last_px) else None,
            "월초 대비 (%)": round(float(t_ret.iloc[-1] * 100), 2),
            "포트폴리오 기여 (%p)": round(float(w * t_ret.iloc[-1] * 100), 2),
        })
    if "CASH (현금)" in held:
        contrib_rows.append({
            "자산 (Ticker)": "CASH (현금)", "비중 (%)": round(held["CASH (현금)"], 2),
            "월초 기준가 ($)": None, "최근 종가 ($)": None,
            "월초 대비 (%)": 0.0, "포트폴리오 기여 (%p)": 0.0,
        })

    # 혼합전략: 전략 A·B·C별 기여로 분해 (각 전략 비중 × 1/3, 상한 적용 시 티커별 비례 축소)
    part_cum = {}
    if is_mix:
        for X in ("A", "B", "C"):
            c_x = pd.Series(0.0, index=month_px.index)
            for t, w_raw in parts.get(X, {}).items():
                if t == "CASH (현금)" or t not in rets:
                    continue
                scale = held.get(t, 0.0) / pre_cap[t] if (cap_on and pre_cap.get(t, 0.0) > 0) else 1.0
                c_x = c_x + (w_raw / 100.0) * (1.0 / 3.0) * scale * rets[t]
            part_cum[X] = c_x
        cum = part_cum["A"] + part_cum["B"] + part_cum["C"]  # 합계 = A + B + C

    cum_pct = cum * 100.0
    nav = 1.0 + cum
    daily_pct = (nav / nav.shift(1).fillna(1.0) - 1.0) * 100.0
    part_cum_pct, part_daily_pct = {}, {}
    if is_mix:
        prev_nav = nav.shift(1).fillna(1.0)
        for X, c_x in part_cum.items():
            part_cum_pct[X] = c_x * 100.0
            # 일간 기여 = 전략 누적 증가분 ÷ 전일 포트폴리오 가치 → 세 전략 합이 일간 합계와 정확히 일치
            part_daily_pct[X] = (c_x - c_x.shift(1).fillna(0.0)) / prev_nav * 100.0

    last_cum = float(cum_pct.iloc[-1])
    last_daily = float(daily_pct.iloc[-1])
    worst_cum = float(cum_pct.min())
    if is_mix:
        room = last_cum - stop_pct
        hit = cum_pct[cum_pct <= stop_pct]
    cards = [
        ("월초 대비 누적 (이번 달 복리)", last_cum, "전월 말 종가 대비"),
        (f"최근일 ({cum_pct.index[-1].strftime('%m/%d')}) 일간 수익률", last_daily, "전일 대비"),
        ("이번 달 최저 누적", worst_cum, "월중 가장 낮았던 누적"),
    ]
    if is_mix:
        cards.append(("하드스탑까지 여유", f"{room:+.2f}%p", f"임계치 {stop_pct:.1f}%", "neg" if room <= 2.0 else "pos"))
    hl_cards(cards)
    if is_mix:
        st.caption(
            f"월초 대비 누적 {last_cum:+.2f}% = "
            f"A {part_cum_pct['A'].iloc[-1]:+.2f}%p + B {part_cum_pct['B'].iloc[-1]:+.2f}%p + C {part_cum_pct['C'].iloc[-1]:+.2f}%p  ·  "
            f"최근일 {last_daily:+.2f}% = "
            f"A {part_daily_pct['A'].iloc[-1]:+.2f}%p + B {part_daily_pct['B'].iloc[-1]:+.2f}%p + C {part_daily_pct['C'].iloc[-1]:+.2f}%p"
        )

    if not is_mix:
        pass
    elif len(hit) > 0:
        st.error(
            f"🛑 하드스탑 발동: {hit.index[0].strftime('%Y-%m-%d')} 종가 기준 누적 {hit.iloc[0]:.2f}%로 "
            f"임계치 {stop_pct:.1f}%에 도달했습니다. 규칙상 전량 현금화 후 월말 리밸런싱까지 대기합니다."
        )
    elif room <= 2.0:
        st.warning(f"⚠️ 주의: 하드스탑 임계치({stop_pct:.1f}%)까지 {room:.2f}%p 남았습니다.")
    else:
        st.success(f"✅ 정상: 하드스탑 임계치({stop_pct:.1f}%)까지 {room:.2f}%p 여유가 있습니다.")

    df_days = pd.DataFrame({
        "날짜": cum_pct.index,
        "일간 수익률 (%)": daily_pct.values,
        "월초 대비 누적 (%)": cum_pct.values,
    })
    try:
        base = alt.Chart(df_days).encode(x=alt.X("날짜:T", title=None, axis=alt.Axis(format="%m/%d")))
        if is_mix:
            df_long = pd.concat([
                pd.DataFrame({"날짜": cum_pct.index, "전략": f"전략 {X}", "일간 기여 (%p)": part_daily_pct[X].values})
                for X in ("A", "B", "C")
            ])
            bars = alt.Chart(df_long).mark_bar(opacity=0.6).encode(
                x=alt.X("날짜:T", title=None, axis=alt.Axis(format="%m/%d")),
                y=alt.Y("sum(일간 기여 (%p)):Q", title="수익률 (%)"),
                color=alt.Color("전략:N", scale=alt.Scale(domain=["전략 A", "전략 B", "전략 C"], range=["#3b82f6", "#f59e0b", "#10b981"]),
                                legend=alt.Legend(orient="top", title=None)),
                tooltip=[alt.Tooltip("날짜:T", format="%Y-%m-%d"), "전략:N", alt.Tooltip("일간 기여 (%p):Q", format=".2f")],
            )
        else:
            bars = base.mark_bar(opacity=0.45).encode(
                y=alt.Y("일간 수익률 (%):Q", title="수익률 (%)"),
                color=alt.condition("datum['일간 수익률 (%)'] >= 0", alt.value("#16a34a"), alt.value("#dc2626")),
                tooltip=[alt.Tooltip("날짜:T", format="%Y-%m-%d"), alt.Tooltip("일간 수익률 (%):Q", format=".2f")],
            )
        line = base.mark_line(point=True, color="#1e293b").encode(
            y="월초 대비 누적 (%):Q",
            tooltip=[alt.Tooltip("날짜:T", format="%Y-%m-%d"), alt.Tooltip("월초 대비 누적 (%):Q", format=".2f")],
        )
        zero = alt.Chart(pd.DataFrame({"y": [0.0]})).mark_rule(color="#94a3b8").encode(y="y:Q")
        layers = bars + line + zero
        if is_mix:
            rule = alt.Chart(pd.DataFrame({"y": [stop_pct]})).mark_rule(color="#dc2626", strokeDash=[6, 4]).encode(y="y:Q")
            layers = layers + rule
        st.altair_chart(layers.properties(height=260), use_container_width=True)
        if is_mix:
            st.caption(f"막대 = 일간 수익률의 전략별 기여(A·B·C 누적 막대, 합계 = 일간 합계), 선 = 월초 대비 누적 합계, 빨간 점선 = 하드스탑 임계치 {stop_pct:.1f}%")
        else:
            st.caption("막대 = 일간 수익률, 선 = 월초 대비 누적 수익률")
    except Exception:
        st.line_chart(df_days.set_index("날짜")["월초 대비 누적 (%)"])

    if is_mix:
        # 괄호 안 = 전략 A·B·C의 기여도(%p). 세 값을 더하면 합계와 정확히 같음
        def _fmt_combo(total, a, b, c):
            total, a, b, c = [0.0 if abs(v) < 0.005 else v for v in (total, a, b, c)]  # "-0.00" 방지
            s_ = f"{a:.2f}"
            for v in (b, c):
                s_ += f"+{v:.2f}" if v >= 0 else f"{v:.2f}"
            return f"{total:.2f} ({s_})"

        df_days_view = pd.DataFrame({
            "날짜": cum_pct.index,
            "일간 수익률 (%) (A+B+C)": [
                _fmt_combo(daily_pct.iloc[i], part_daily_pct["A"].iloc[i], part_daily_pct["B"].iloc[i], part_daily_pct["C"].iloc[i])
                for i in range(len(cum_pct))
            ],
            "월초 대비 누적 (%) (A+B+C)": [
                _fmt_combo(cum_pct.iloc[i], part_cum_pct["A"].iloc[i], part_cum_pct["B"].iloc[i], part_cum_pct["C"].iloc[i])
                for i in range(len(cum_pct))
            ],
            "하드스탑까지 여유 (%p)": (cum_pct - stop_pct).round(2).values,
        }).sort_values("날짜", ascending=False)
    else:
        df_days_view = df_days.sort_values("날짜", ascending=False).copy()
    df_days_view["날짜"] = df_days_view["날짜"].dt.strftime("%Y-%m-%d")
    st.dataframe(
        df_days_view.round(2), use_container_width=True, hide_index=True,
        height=(len(df_days_view) + 1) * 35 + 3,
    )
    if is_mix:
        st.caption(
            "※ 괄호 안은 전략 A·B·C가 혼합 포트폴리오 수익률에 기여한 값(%p)이며, 세 값을 더하면 앞의 합계와 같습니다"
            "(표시값은 소수 둘째 자리 반올림이라 0.01 차이가 날 수 있음). "
            "각 전략의 단독 수익률은 전략 A·B·C 탭에서 확인할 수 있습니다."
        )

    st.markdown("**종목별 월초 대비 수익률과 기여도**")
    df_contrib = pd.DataFrame(contrib_rows).sort_values("포트폴리오 기여 (%p)")
    st.dataframe(df_contrib, use_container_width=True, hide_index=True,
                 height=(len(df_contrib) + 1) * 35 + 3)
    if is_mix:
        st.caption("※ 일별 종가 기준입니다. 장중에는 최근일 값이 실시간 가격으로 계속 바뀌며, 규칙상 판정은 종가로 합니다. 월중 리밸런싱이 없는 매수 후 보유 가정이며, 슬리피지·거래비용·세금은 반영되지 않았습니다.")
    else:
        st.caption("※ 일별 종가 기준입니다. 장중에는 최근일 값이 실시간 가격으로 계속 바뀝니다. 월중 리밸런싱이 없는 매수 후 보유 가정이며, 슬리피지·거래비용·세금은 반영되지 않았습니다.")


import html as _html

# 티커 -> (짧은 한글명, 간략 설명). 표에서 티커 옆에 한글명을 보여주고, 마우스를 올리면 설명이 나옵니다.
TICKER_INFO = {
    "TIP": ("물가연동채", "iShares TIPS Bond · 원금이 물가상승률에 연동되는 미국 물가연동국채(TIPS)"),
    "SPY": ("S&P500", "SPDR S&P 500 · 미국 대형주 500개 지수 추종"),
    "QQQ": ("나스닥100", "Invesco QQQ · 나스닥 상위 100개 비금융 대형주(기술주 중심) 추종"),
    "QQQM": ("나스닥100", "Invesco NASDAQ 100 · QQQ와 같은 지수를 추종하며 보수가 더 낮은 ETF"),
    "FEZ": ("유로존50", "SPDR EURO STOXX 50 · 유로존 대형주 50개 추종"),
    "GLD": ("금", "SPDR Gold Shares · 금 현물 가격 추종"),
    "IBB": ("바이오", "iShares Biotechnology · 미국 바이오테크 기업 지수 추종"),
    "SMH": ("반도체", "VanEck Semiconductor · 미국 반도체 대형주 추종"),
    "EEM": ("신흥국", "iShares MSCI Emerging Markets · 신흥국 주식 시장 추종"),
    "XLK": ("기술주", "Technology Select Sector SPDR · S&P500 내 정보기술 섹터"),
    "LIT": ("리튬·배터리", "Global X Lithium & Battery Tech · 리튬 채굴·2차전지 관련 기업"),
    "XLE": ("에너지", "Energy Select Sector SPDR · S&P500 내 에너지 섹터(석유·가스)"),
    "UBT": ("장기국채 2배", "ProShares Ultra 20+ Year Treasury · 미국 20년 이상 장기국채 일간 2배 레버리지"),
    "XLV": ("헬스케어", "Health Care Select Sector SPDR · S&P500 내 헬스케어 섹터"),
    "QTUM": ("양자컴퓨팅", "Defiance Quantum ETF · 양자컴퓨팅·머신러닝 관련 기업"),
    "BIL": ("초단기국채", "SPDR 1-3 Month T-Bill · 만기 1~3개월 미국 단기국채, 현금에 가까운 자산"),
    "IEF": ("중기국채", "iShares 7-10 Year Treasury · 만기 7~10년 미국 중기국채"),
    "AGG": ("종합채권", "iShares Core US Aggregate Bond · 미국 국채·회사채·MBS 등 종합 채권"),
    "HYG": ("하이일드채", "iShares iBoxx High Yield Corporate Bond · 신용등급이 낮은 고수익 회사채"),
    "TBF": ("장기국채 인버스", "ProShares Short 20+ Year Treasury · 20년 이상 장기국채와 반대로 움직이는 -1배 인버스. 금리 상승 시 이익"),
    "TYD": ("중기국채 3배", "Direxion 7-10 Year Treasury Bull 3X · 만기 7~10년 미국 국채 일간 3배 레버리지"),
    "UPRO": ("S&P500 3배", "ProShares UltraPro S&P500 · S&P500 일간 3배 레버리지"),
    "VNQ": ("미국 리츠", "Vanguard Real Estate · 미국 상장 부동산투자회사(리츠)"),
    "DOG": ("다우 인버스", "ProShares Short Dow30 · 다우존스30 지수와 반대로 움직이는 -1배 인버스"),
    "RWM": ("러셀2000 인버스", "ProShares Short Russell2000 · 미국 소형주(러셀2000)와 반대로 움직이는 -1배 인버스"),
    "FDN": ("인터넷", "First Trust Dow Jones Internet · 미국 인터넷 기업"),
    "IGV": ("소프트웨어", "iShares Expanded Tech-Software · 미국 소프트웨어 기업"),
    "XLU": ("유틸리티", "Utilities Select Sector SPDR · S&P500 내 전력·가스 등 유틸리티 섹터"),
    "PDBC": ("원자재", "Invesco Optimum Yield Diversified Commodity · 에너지·금속·농산물 등 다변화 원자재 선물"),
    "OILK": ("원유", "ProShares K-1 Free Crude Oil Strategy · 원유 선물 추종(K-1 세무서류 없음)"),
    "SHY": ("단기국채", "iShares 1-3 Year Treasury · 만기 1~3년 미국 단기국채"),
    "TLT": ("장기국채", "iShares 20+ Year Treasury · 만기 20년 이상 미국 장기국채"),
    "SCHD": ("배당성장", "Schwab US Dividend Equity · 배당 지속성이 높은 미국 배당성장주"),
    "JEPI": ("커버드콜", "JPMorgan Equity Premium Income · S&P500 주식 + 옵션 매도로 월 배당을 높인 ETF"),
    "TQQQ": ("나스닥100 3배", "ProShares UltraPro QQQ · 나스닥100 일간 3배 레버리지"),
    "SOXL": ("반도체 3배", "Direxion Semiconductor Bull 3X · 반도체 지수 일간 3배 레버리지"),
    "DIA": ("다우30", "SPDR Dow Jones Industrial Average · 다우존스 산업평균 30개 종목 추종"),
    "IWM": ("러셀2000", "iShares Russell 2000 · 미국 소형주 2000개 추종"),
    "XLF": ("금융", "Financial Select Sector SPDR · S&P500 내 금융 섹터"),
}


def ticker_cell_html(t, show_name=True):
    """티커 + (한글명) + 마우스 오버/터치 설명(data-tip)."""
    info = TICKER_INFO.get(str(t))
    if not info:
        return _html.escape(str(t))
    short, desc = info
    tip = _html.escape(f"{t} · {short}\n{desc}", quote=True).replace("\n", "&#10;")
    name = f'<span class="tk-name">({_html.escape(short)})</span>' if show_name else ""
    return f'<span class="tk gl" data-tip="{tip}">{_html.escape(str(t))}</span>{name}'


# ===================== 용어 설명 (마우스 오버 / 폰 터치) =====================
import re as _re
from streamlit.delta_generator import DeltaGenerator as _DG

GL_TICKERS_IN_TEXT = True  # 본문 속 티커에도 설명을 붙이려면 True, 끄려면 False

_GL_DEFS = [
    (("^TNX", "TNX"), "미국 10년물 국채 금리. 주식 가치평가와 기업 차입금리의 기준이 되는 무위험 수익률 지표"),
    (("^TYX", "TYX"), "미국 30년물 국채 금리. 초장기 인플레이션·경제성장 기대를 반영하는 장기금리 지표"),
    (("USDKRW=X",), "달러/원 환율. 해외 ETF 환전 매수와 환노출 성과에 직접 영향"),
    (("DX-Y.NYB",), "달러 인덱스. 유로·엔·파운드 등 주요 6개 통화 대비 달러의 상대 가치"),
    (("CL=F",), "WTI 원유 선물 가격. 국제 유가와 생산자 물가 압력을 나타냄"),
    (("^VIX", "VIX"), "변동성 지수(공포 지수). S&P500 옵션 가격으로 산출한 시장의 기대 변동성"),
    (("SPY 배당수익률", "배당수익률"), "S&P500의 주가 대비 배당금 비율. 전략 C에서 과열·저평가를 판단하는 카나리아 지표(1.33% 기준선)"),
    (("카나리아 신호", "카나리아"), "탄광의 카나리아처럼 하락 위험을 미리 알려주는 선행 경고 지표 (TIP 이동평균·모멘텀, S&P500 배당수익률)"),
    (("모멘텀 스코어",), "과거 1·3·6·12개월 수익률로 계산한 추세 강도. 최근 기간에 가중치를 주기도 함"),
    (("NAV",), "순자산가치. 시작 시점을 100으로 두고 누적 복리 수익을 반영한 자산 곡선 값"),
    (("CAGR",), "연평균 복리 수익률. 전체 기간 성과를 매년 일정 비율로 복리 성장한 것으로 환산한 값"),
    (("MDD",), "최대 낙폭. 직전 고점 대비 가장 크게 떨어진 하락률 = 감내해야 할 최대 손실 위험"),
    (("샤프 지수",), "변동성(위험) 한 단위당 얻은 초과수익. 높을수록 위험 대비 효율이 좋음"),
    (("소티노 지수",), "손실이 난 '하방 변동성'만 위험으로 보고 계산한 위험조정 수익 지표"),
    (("UPI 지수",), "Ulcer Performance Index. 낙폭의 깊이와 지속기간을 반영한 위험 대비 수익률"),
    (("연간 턴오버", "턴오버"), "1년 동안 포트폴리오 자산이 교체된 비중의 합(회전율). 높을수록 거래비용·슬리피지 증가"),
    (("비중 상한",), "여러 전략이 같은 자산을 고를 때 한 자산에 쏠리지 않게 정한 한도(예: 35%). 초과분은 현금 전환"),
    (("월중 하드스탑", "하드스탑"), "월말 리밸런싱을 기다리지 않고, 월중 누적 손실이 기준(예: -7%)에 닿으면 즉시 전량 현금화하는 규칙"),
    (("연 변동성",), "수익률의 표준편차를 연 단위로 환산한 값. 클수록 등락이 심함"),
    (("표준편차",), "수익률이 평균에서 흩어진 정도. 클수록 변동이 큼"),
    (("YTD",), "Year-To-Date. 올해 1월 1일부터 현재까지의 누적 수익률"),
    (("슬리피지",), "주문 예상가와 실제 체결가의 차이로 생기는 숨은 거래비용"),
    (("대공황",), "1929년 미국 증시 폭락으로 시작된 세계적 경제 불황. S&P500이 1929~1932년 약 80%대 하락"),
    (("블랙먼데이",), "1987년 10월 19일 미국 증시가 하루에 약 20% 폭락한 사건. 프로그램 매매와 공포 매도가 겹침"),
    (("닷컴버블",), "1990년대 후반 인터넷 기업 주가 거품이 2000년 3월부터 꺼진 폭락. 나스닥이 2002년까지 약 78% 하락"),
    (("글로벌 금융위기", "금융위기"), "2007~2009년 미국 서브프라임 모기지 부실에서 시작된 세계 금융 위기. S&P500이 약 57% 하락"),
    (("긴축 발작",), "2022년 연준의 급격한 금리 인상으로 주식·채권이 동반 하락한 시기"),
    (("전고점 회복",), "하락 뒤 주가가 직전 최고점을 다시 넘는 데 걸린 시간. 길수록 '물린 기간'이 깁니다"),
]
GLOSSARY = {}
for _keys, _d in _GL_DEFS:
    for _k in _keys:
        GLOSSARY[_k] = _d
if GL_TICKERS_IN_TEXT:
    for _t, (_s, _d) in TICKER_INFO.items():
        GLOSSARY.setdefault(_t, f"{_t} ({_s}) — {_d}".replace("|", "/"))
_GL_RE = _re.compile(
    r"(?<![A-Za-z0-9_^])(?:" + "|".join(_re.escape(k) for k in sorted(GLOSSARY, key=len, reverse=True)) + r")(?![A-Za-z0-9_])"
)
_GL_SPLIT = _re.compile(r"(</?[A-Za-z][^>]*>|`[^`]*`)")


def glossify(text):
    """글 속 용어를 <span class="gl" data-tip=...>로 감쌉니다 (태그·코드·스타일 블록 안은 건드리지 않음)."""
    if "<style" in text or "```" in text:
        return text
    out, skip = [], False
    for part in _GL_SPLIT.split(text):
        if part.startswith("<") or part.startswith("`"):
            if _re.search(r'class="[^"]*\bgl\b', part):
                skip = True
            elif part == "</span>" and skip:
                skip = False
            out.append(part)
        elif skip:
            out.append(part)
        else:
            out.append(_GL_RE.sub(
                lambda m: f'<span class="gl" data-tip="{_html.escape(GLOSSARY[m.group(0)], quote=True)}">{m.group(0)}</span>', part))
    return "".join(out)


def _gl_patch(owner, name, handler):
    cur = getattr(owner, name)
    orig = getattr(cur, "_gl_orig", cur)  # 재실행해도 겹겹이 감싸지지 않도록 원본 기준으로 교체

    def f(*args, **k):
        i = 1 if args and isinstance(args[0], _DG) else 0
        return handler(orig, args, k, i)
    f._gl_orig = orig
    setattr(owner, name, f)


def _h_text(orig, args, k, i):
    if len(args) > i and isinstance(args[i], str):
        new = glossify(args[i])
        if new != args[i]:
            args = args[:i] + (new,) + args[i + 1:]
            k["unsafe_allow_html"] = True
    return orig(*args, **k)


def _h_metric(orig, args, k, i):
    """st.metric 라벨에 용어가 있으면 ⓘ 도움말 아이콘(터치 가능)을 자동으로 붙입니다."""
    if "help" not in k and i < len(args) <= i + 4 and isinstance(args[i], str):
        seen = []
        for m in _GL_RE.finditer(args[i]):
            if m.group(0) not in seen:
                seen.append(m.group(0))
        if seen:
            k["help"] = "\n\n".join(f"**{x}** — {GLOSSARY[x]}" for x in seen)
    return orig(*args, **k)


for _o in (st, _DG):
    for _n, _h in (("markdown", _h_text), ("caption", _h_text), ("metric", _h_metric)):
        _gl_patch(_o, _n, _h)

st.markdown("<style>.gl{border-bottom:1px dotted #64748b;cursor:help;-webkit-tap-highlight-color:transparent}</style>",
            unsafe_allow_html=True)


# ===================== 핵심 수치 강조 (비중 칩 · 일별/월별 복리 수익 카드) =====================
st.markdown("""<style>
.hl-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:8px;margin:0.3rem 0 0.7rem}
.hl-card{border-radius:12px;padding:9px 12px;border:1px solid #bfdbfe;background:#f5f9ff;color:#2563eb}
.hl-card.pos{border-color:#a7f3d0;background:#f3fcf8;color:#059669}
.hl-card.neg{border-color:#fecaca;background:#fff6f6;color:#dc2626}
.hl-card .hl-l{font-size:0.78rem;font-weight:700;color:#334155;word-break:keep-all}
.hl-card .hl-v{font-size:1.4rem;font-weight:700;line-height:1.25}
.hl-card .hl-s{font-size:0.72rem;color:#64748b;word-break:keep-all}
.al-wrap{display:flex;flex-wrap:wrap;gap:8px;margin:0.3rem 0 0.6rem}
.al-chip{flex:1 1 140px;border-radius:12px;padding:10px 12px;background:#fff;border:1px solid #e2e8f0;border-left:5px solid #3b82f6;box-shadow:0 1px 2px rgba(15,23,42,.05)}
.al-chip .al-t{font-size:1.05rem;font-weight:700;color:#0f172a}
.al-chip .al-n{font-size:0.78rem;color:#64748b;margin-left:4px}
.al-chip .al-w{font-size:1.45rem;font-weight:700;line-height:1.2;color:#0f172a}
</style>""", unsafe_allow_html=True)


def hl_cards(items):
    """items: [(라벨, 숫자 또는 문자열, 부가설명, 'auto'|'pos'|'neg'|'neutral'), ...] -> 큼직한 강조 카드."""
    html = ""
    for label, val, sub, *rest in items:
        tone = rest[0] if rest else "auto"
        if isinstance(val, (int, float, np.floating)):
            if tone == "auto":
                tone = "pos" if val > 0 else ("neg" if val < 0 else "neutral")
            val = f"{val:.2f}%" if label.startswith("연환산") else f"{val:+.2f}%"
        cls = {"pos": " pos", "neg": " neg"}.get(tone, "")
        html += (f'<div class="hl-card{cls}"><div class="hl-l">{_html.escape(label)}</div>'
                 f'<div class="hl-v">{_html.escape(str(val))}</div><div class="hl-s">{_html.escape(sub)}</div></div>')
    st.markdown(f'<div class="hl-grid">{html}</div>', unsafe_allow_html=True)


def monthly_compound_cards(bt):
    """월별 수익률 위에 이번 달 / 올해(YTD) / 최근 12개월 복리 수익을 크게 표시."""
    try:
        r = bt["monthly_return"].astype(float).values / 100.0
        d = pd.to_datetime(bt["date"])
        last = d.iloc[-1]
        ytd = (np.prod(1 + r[(d.dt.year == last.year).values]) - 1) * 100
        items = [(f"이번 달 ({last.strftime('%Y-%m')})", r[-1] * 100, "월 수익률"),
                 ("올해 복리 수익 (YTD)", ytd, "월 수익률을 연초부터 복리로 누적")]
        if len(r) >= 12:
            items.append(("최근 12개월 복리", (np.prod(1 + r[-12:]) - 1) * 100, "최근 1년 복리 누적"))
        hl_cards(items)
    except Exception:
        pass


def render_alloc_chips(df, ticker_col="자산군 (Ticker)", weight_col="배분 비중 (%)",
                       colors=("#3b82f6", "#ef4444", "#10b981", "#f59e0b", "#8b5cf6", "#ec4899", "#06b6d4", "#f97316")):
    """포트폴리오 자산군과 비중을 도넛 색과 같은 색의 큰 칩으로 강조."""
    chips = ""
    for i, (_, r) in enumerate(df.iterrows()):
        try:
            w = f"{float(r[weight_col]):,.2f}%"
        except Exception:
            w = str(r[weight_col])
        chips += (f'<div class="al-chip" style="border-left-color:{colors[i % len(colors)]}">'
                  f'<div><span class="al-t">{ticker_cell_html(r[ticker_col], show_name=False)}</span></div>'
                  f'<div class="al-w">{_html.escape(w)}</div></div>')
    st.markdown(f'<div class="al-wrap">{chips}</div>', unsafe_allow_html=True)


# ===================== 장기 낙폭 (SPY·QQQ 등) 헬퍼 =====================
LONG_EVENTS = [
    ("대공황", "1929 대공황", "1929-09-01", "1932-12-31"),
    ("오일쇼크", "1973-74 오일쇼크 약세장", "1973-01-01", "1974-12-31"),
    ("블랙먼데이", "1987 블랙먼데이", "1987-08-01", "1987-12-31"),
    ("LTCM", "1998 LTCM·러시아 위기", "1998-07-01", "1998-10-31"),
    ("닷컴", "2000 닷컴버블 붕괴", "2000-03-01", "2002-12-31"),
    ("금융위기", "2007-09 글로벌 금융위기", "2007-10-01", "2009-04-30"),
    ("유럽위기", "2011 美 신용등급 강등·유럽 재정위기", "2011-04-01", "2011-10-31"),
    ("중국쇼크", "2015-16 중국 쇼크·유가 급락", "2015-05-01", "2016-02-29"),
    ("2018 Q4", "2018 4분기 긴축·무역분쟁", "2018-09-01", "2018-12-31"),
    ("코로나", "2020 코로나 팬데믹", "2020-02-01", "2020-04-30"),
    ("2022 긴축", "2022 긴축 발작 (금리 인상기)", "2022-01-01", "2022-12-31"),
    ("엔캐리", "2024 엔캐리 청산·AI 주가 조정", "2024-07-01", "2024-08-31"),
    ("관세쇼크", "2025 美 관세 쇼크", "2025-02-01", "2025-05-31"),
]


@st.cache_data(ttl=6 * 3600, show_spinner=False)
def get_long_history(symbols, start):
    """일별 종가(배당·분할 반영) 장기 시계열. symbols는 tuple. {심볼: Series}"""
    out = {}
    for sym in symbols:
        try:
            df = yf.download(sym, start=start, interval="1d", progress=False, auto_adjust=True)
        except Exception:
            continue
        if df is None or len(df) == 0:
            continue
        close = df["Close"] if "Close" in df.columns else df.iloc[:, 0]
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]
        close = close.dropna()
        if getattr(close.index, "tz", None) is not None:
            close.index = close.index.tz_localize(None)
        close = close[close > 0].astype(float)
        if len(close) > 50:
            out[sym] = close
    return out


def _fmt_dur(days):
    if days is None:
        return "-"
    if days >= 365:
        return f"{days / 365.25:.1f}년"
    if days >= 45:
        return f"{days / 30.44:.0f}개월"
    return f"{int(days)}일"


def dd_episodes(px, min_depth=-2.0):
    """고점 → 저점 → (전고점 회복) 낙폭 구간 목록.
    가장 깊은 낙폭을 찾은 뒤, 그 '앞 구간'·'저점~회복 사이 구간'·'회복 이후 구간'을 다시 따로 탐색합니다.
    그래서 전고점을 오래 못 넘은 기간 안에 있던 별도 폭락(예: 닷컴 회복 구간 중 금융위기)도 독립 구간으로 잡힙니다."""
    vals, idx = px.values, px.index
    n = len(vals)
    out, stack = [], [(0, n)]
    while stack:
        lo, hi = stack.pop()
        if hi - lo < 3:
            continue
        seg = vals[lo:hi]
        dd = seg / np.maximum.accumulate(seg) - 1
        k = int(np.argmin(dd))
        if dd[k] * 100 > min_depth:
            continue
        t = lo + k
        pk = lo + int(np.argmax(seg[:k + 1]))
        hit = np.nonzero(vals[t + 1:] >= vals[pk])[0]
        r = (t + 1 + int(hit[0])) if len(hit) else None
        out.append({"peak": idx[pk], "trough": idx[t], "recovery": (idx[r] if r is not None else None),
                    "depth": float(dd[k] * 100)})
        stack.append((lo, pk + 1))                           # 고점 이전 구간
        stack.append((t, (r + 1) if r is not None else n))   # 저점 ~ 회복 사이 구간
        if r is not None and r < hi - 1:
            stack.append((r, hi))                            # 회복 이후 구간
    return out


def event_stats(px, start, end):
    """이슈 기간 안에서의 고점→저점 낙폭, 전고점 회복, 저점 후 1년 수익률. 데이터가 없으면 None."""
    s0, e0 = pd.Timestamp(start), pd.Timestamp(end)
    w = px[(px.index >= s0) & (px.index <= e0)]
    if len(w) < 5 or (w.index[0] - s0).days > 45:
        return None
    dd = w / w.cummax() - 1
    t = dd.idxmin()
    depth = float(dd.min() * 100)
    if depth > -3:
        return None
    p = w.loc[:t].idxmax()
    after = px.loc[t:]
    rec = after[after >= px.loc[p]]
    j = px.index.get_loc(t)
    rebound = float((px.iloc[j + 252] / px.iloc[j] - 1) * 100) if j + 252 < len(px) else None
    return {"peak": p, "trough": t, "depth": depth,
            "recovery": (rec.index[0] if len(rec) else None), "rebound": rebound}


NDX_INFO = {
    "ADBE": ("어도비", "Adobe · 포토샵·PDF 등 크리에이티브·문서 소프트웨어"),
    "AMD": ("AMD", "Advanced Micro Devices · CPU·GPU·AI 가속기 반도체"),
    "ABNB": ("에어비앤비", "Airbnb · 숙박 공유 플랫폼"),
    "ALNY": ("알닐람", "Alnylam Pharmaceuticals · RNA 간섭(RNAi) 치료제 바이오텍"),
    "GOOGL": ("알파벳A", "Alphabet Class A · 구글·유튜브·클라우드 모회사(의결권 주식)"),
    "GOOG": ("알파벳C", "Alphabet Class C · 같은 회사의 무의결권 주식"),
    "AMZN": ("아마존", "Amazon · 전자상거래와 AWS 클라우드"),
    "AEP": ("아메리칸일렉트릭", "American Electric Power · 미국 전력 유틸리티"),
    "AMGN": ("암젠", "Amgen · 바이오 제약"),
    "ADI": ("아날로그디바이시스", "Analog Devices · 아날로그·혼합신호 반도체"),
    "AAPL": ("애플", "Apple · 아이폰·맥·서비스"),
    "AMAT": ("어플라이드머티리얼즈", "Applied Materials · 반도체 제조 장비"),
    "APP": ("앱러빈", "AppLovin · 모바일 광고·앱 수익화 소프트웨어"),
    "ARM": ("암홀딩스", "Arm Holdings · CPU 설계 기술(IP) 라이선스"),
    "ASML": ("ASML", "ASML Holding · 극자외선(EUV) 노광장비 (네덜란드)"),
    "ALAB": ("아스테라랩스", "Astera Labs · AI 서버용 연결(커넥티비티) 반도체"),
    "ADSK": ("오토데스크", "Autodesk · 설계·건축용 소프트웨어(AutoCAD)"),
    "ADP": ("ADP", "Automatic Data Processing · 급여·인사 관리 서비스"),
    "AXON": ("액손", "Axon Enterprise · 테이저·바디캠 등 공공안전 기술"),
    "BKR": ("베이커휴즈", "Baker Hughes · 에너지 장비·서비스"),
    "BKNG": ("부킹홀딩스", "Booking Holdings · 온라인 여행 예약(Booking.com)"),
    "AVGO": ("브로드컴", "Broadcom · 네트워크·AI 반도체와 인프라 소프트웨어"),
    "CDNS": ("케이던스", "Cadence Design Systems · 반도체 설계 자동화(EDA) 소프트웨어"),
    "CTAS": ("신타스", "Cintas · 유니폼·시설 관리 서비스"),
    "CSCO": ("시스코", "Cisco · 네트워크 장비·보안"),
    "CCEP": ("코카콜라유로퍼시픽", "Coca-Cola Europacific Partners · 유럽·호주 코카콜라 병입·판매"),
    "CMCSA": ("컴캐스트", "Comcast · 케이블·방송·NBC유니버설"),
    "CEG": ("컨스텔레이션에너지", "Constellation Energy · 원자력 중심 발전"),
    "CPRT": ("코파트", "Copart · 온라인 중고차·사고차 경매"),
    "CRWV": ("코어위브", "CoreWeave · AI 전용 GPU 클라우드"),
    "COST": ("코스트코", "Costco · 회원제 창고형 할인점"),
    "CRWD": ("크라우드스트라이크", "CrowdStrike · 클라우드 사이버보안"),
    "CSX": ("CSX", "CSX Corporation · 미국 동부 철도 운송"),
    "DDOG": ("데이터독", "Datadog · 클라우드 모니터링 소프트웨어"),
    "DXCM": ("덱스콤", "DexCom · 연속혈당측정기"),
    "FANG": ("다이아몬드백", "Diamondback Energy · 셰일 원유·가스 생산"),
    "DASH": ("도어대시", "DoorDash · 음식 배달 플랫폼"),
    "EXC": ("엑셀론", "Exelon · 미국 전력 유틸리티"),
    "FAST": ("패스널", "Fastenal · 산업용 체결 부품·공구 유통"),
    "FER": ("페로비알", "Ferrovial · 고속도로·공항 등 인프라 운영"),
    "FTNT": ("포티넷", "Fortinet · 네트워크 보안 장비"),
    "GEHC": ("GE헬스케어", "GE HealthCare · 의료영상·진단 장비"),
    "GILD": ("길리어드", "Gilead Sciences · 항바이러스 등 바이오 제약"),
    "HONA": ("허니웰항공우주", "Honeywell Aerospace · 허니웰에서 분리된 항공우주 사업"),
    "HON": ("허니웰", "Honeywell · 산업 자동화·빌딩 기술"),
    "IDXX": ("아이덱스", "Idexx Laboratories · 동물 진단 장비"),
    "INTC": ("인텔", "Intel · CPU와 파운드리(위탁생산)"),
    "INTU": ("인튜이트", "Intuit · 터보택스·퀵북스 소프트웨어"),
    "ISRG": ("인튜이티브서지컬", "Intuitive Surgical · 다빈치 수술 로봇"),
    "KDP": ("큐리그닥터페퍼", "Keurig Dr Pepper · 음료와 커피 머신"),
    "KLAC": ("KLA", "KLA Corporation · 반도체 검사·계측 장비"),
    "KHC": ("크래프트하인즈", "Kraft Heinz · 가공식품"),
    "LRCX": ("램리서치", "Lam Research · 반도체 식각·증착 장비"),
    "LIN": ("린데", "Linde · 산업용 가스"),
    "LITE": ("루멘텀", "Lumentum · 광통신·레이저 부품"),
    "MAR": ("메리어트", "Marriott International · 호텔 체인"),
    "MRVL": ("마벨", "Marvell Technology · 데이터센터·네트워크 반도체"),
    "MELI": ("메르카도리브레", "Mercado Libre · 중남미 전자상거래·핀테크"),
    "META": ("메타", "Meta Platforms · 페이스북·인스타그램"),
    "MCHP": ("마이크로칩", "Microchip Technology · 마이크로컨트롤러 반도체"),
    "MU": ("마이크론", "Micron Technology · 메모리 반도체(D램·낸드)"),
    "MSFT": ("마이크로소프트", "Microsoft · 윈도우·오피스·애저 클라우드"),
    "MSTR": ("스트래티지", "MicroStrategy · 비트코인을 대량 보유한 소프트웨어 기업"),
    "MDLZ": ("몬덜리즈", "Mondelez International · 오레오 등 과자·스낵"),
    "MPWR": ("모놀리식파워", "Monolithic Power Systems · 전력관리 반도체"),
    "MNST": ("몬스터베버리지", "Monster Beverage · 에너지 음료"),
    "NBIS": ("네비우스", "Nebius Group · AI 클라우드 인프라 (네덜란드)"),
    "NFLX": ("넷플릭스", "Netflix · 동영상 스트리밍"),
    "NVDA": ("엔비디아", "Nvidia · AI·그래픽 GPU"),
    "NXPI": ("NXP", "NXP Semiconductors · 차량용 반도체 (네덜란드)"),
    "ORLY": ("오라일리", "O'Reilly Automotive · 자동차 부품 소매"),
    "ODFL": ("올드도미니언", "Old Dominion Freight Line · 화물 운송"),
    "PCAR": ("팩카", "Paccar · 트럭 제조(켄워스·피터빌트)"),
    "PLTR": ("팔란티어", "Palantir Technologies · 데이터 분석·AI 플랫폼"),
    "PANW": ("팔로알토", "Palo Alto Networks · 사이버보안 플랫폼"),
    "PAYX": ("페이첵스", "Paychex · 중소기업 급여·인사 서비스"),
    "PYPL": ("페이팔", "PayPal · 온라인 결제"),
    "PDD": ("PDD", "PDD Holdings · 테무·핀둬둬 운영 (중국 전자상거래)"),
    "PEP": ("펩시코", "PepsiCo · 음료와 스낵"),
    "QCOM": ("퀄컴", "Qualcomm · 모바일 칩과 통신 특허"),
    "REGN": ("리제네론", "Regeneron Pharmaceuticals · 바이오 제약"),
    "RKLB": ("로켓랩", "Rocket Lab · 소형 로켓 발사·우주 부품"),
    "ROP": ("로퍼", "Roper Technologies · 산업·소프트웨어 지주회사"),
    "ROST": ("로스스토어", "Ross Stores · 할인 의류 소매"),
    "SNDK": ("샌디스크", "Sandisk · 낸드 플래시·SSD"),
    "STX": ("시게이트", "Seagate Technology · 하드디스크 드라이브"),
    "SHOP": ("쇼피파이", "Shopify · 온라인 쇼핑몰 구축 플랫폼"),
    "SPCX": ("스페이스X", "SpaceX · 로켓 발사와 스타링크 위성 인터넷"),
    "SBUX": ("스타벅스", "Starbucks · 커피 체인"),
    "SNPS": ("시높시스", "Synopsys · 반도체 설계 자동화(EDA) 소프트웨어"),
    "TMUS": ("티모바일", "T-Mobile US · 미국 이동통신"),
    "TTWO": ("테이크투", "Take-Two Interactive · GTA 등 게임 퍼블리셔"),
    "TER": ("테라다인", "Teradyne · 반도체 테스트 장비·로봇"),
    "TSLA": ("테슬라", "Tesla · 전기차·에너지 저장장치"),
    "TXN": ("텍사스인스트루먼트", "Texas Instruments · 아날로그 반도체"),
    "TRI": ("톰슨로이터", "Thomson Reuters · 뉴스·법률 정보 서비스"),
    "VRTX": ("버텍스", "Vertex Pharmaceuticals · 낭포성 섬유증 등 바이오 제약"),
    "WMT": ("월마트", "Walmart · 대형 할인점"),
    "WBD": ("워너브라더스", "Warner Bros. Discovery · 미디어·HBO 스트리밍"),
    "WDC": ("웨스턴디지털", "Western Digital · 하드디스크 드라이브"),
    "WDAY": ("워크데이", "Workday · 인사·재무 클라우드 소프트웨어"),
    "XEL": ("엑셀에너지", "Xcel Energy · 미국 중서부 전력 유틸리티"),
}
for _k, _v in NDX_INFO.items():
    TICKER_INFO.setdefault(_k, _v)  # 용어 사전(GLOSSARY) 생성 이후에 추가하므로 본문 자동 밑줄에는 영향 없음
NDX_FALLBACK = list(NDX_INFO)  # 위키피디아 자동 갱신 실패 시 쓰는 내장 구성 종목 목록


@st.cache_data(ttl=24 * 3600, show_spinner=False)
def get_ndx_tickers():
    """나스닥100 구성 종목: 위키피디아 표에서 자동 갱신하고, 실패하면 내장 목록을 사용합니다."""
    try:
        import requests
        from io import StringIO
        r = requests.get("https://en.wikipedia.org/wiki/List_of_NASDAQ-100_companies",
                         headers={"User-Agent": "Mozilla/5.0 (asset-allocation-dashboard)"}, timeout=10)
        r.raise_for_status()
        for t in pd.read_html(StringIO(r.text)):
            if "Ticker" in [str(c) for c in t.columns]:
                tick = [str(x).strip().replace(".", "-") for x in t["Ticker"].dropna().tolist()]
                tick = [x for x in tick if x and x.replace("-", "").isalnum()]
                if 90 <= len(tick) <= 110:
                    return list(dict.fromkeys(tick)), "auto"
    except Exception:
        pass
    return list(NDX_FALLBACK), "fallback"


def render_gl_table(df):
    """지표 표: 첫 열(지표명)의 용어에 설명을 붙인 HTML 표 (스크롤 없이 전체 표시)."""
    head = "".join(f"<th>{_html.escape(str(c))}</th>" for c in df.columns)
    body = ""
    for _, row in df.iterrows():
        cells = ""
        for j, c in enumerate(df.columns):
            sv = str(row[c])
            if j == 0:
                cells += f'<td class="l">{glossify(_html.escape(sv))}</td>'
            else:
                neg = sv.startswith("-") and len(sv) > 1 and sv[1].isdigit()
                cells += f'<td class="{"neg" if neg else ""}">{_html.escape(sv)}</td>'
        body += f"<tr>{cells}</tr>"
    st.markdown(f'{_TBL_CSS}<table class="dtbl"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>', unsafe_allow_html=True)


_TBL_CSS = (
    "<style>"
    ".dtbl{width:100%;border-collapse:collapse;font-size:0.85rem;margin:0.3rem 0 0.6rem}"
    ".dtbl th{background:#e2e8f0;color:#334155;padding:7px 5px;text-align:center;border:1px solid #cbd5e1;word-break:keep-all}"
    ".dtbl td{padding:6px 5px;text-align:right;border:1px solid #e2e8f0;white-space:nowrap}"
    ".dtbl td.l{text-align:left}"
    ".dtbl td.t{text-align:left;white-space:normal;word-break:keep-all;overflow-wrap:anywhere}"
    ".dtbl tr:nth-child(even) td{background:#f8fafc}"
    ".dtbl td.neg{color:#dc2626}"
    ".dtbl .tk{border-bottom:1px dotted #64748b;cursor:help;font-weight:600}"
    ".dtbl .tk-name{color:#64748b;font-size:0.82em;margin-left:2px;white-space:normal;word-break:keep-all}"
    "@media (max-width:640px){.dtbl{font-size:0.62rem}.dtbl th,.dtbl td{padding:4px 2px}}"
    "</style>"
)


def render_html_table(df, ticker_cols=(), text_cols=()):
    """DataFrame을 스크롤 없이 전체가 보이는 HTML 표로 표시. 티커 열은 한글명+마우스 오버 설명을 붙입니다."""
    head = "".join(f"<th>{_html.escape(str(c))}</th>" for c in df.columns)
    body = ""
    for _, row in df.iterrows():
        cells = ""
        for c in df.columns:
            v = row[c]
            if c in ticker_cols:
                cells += f'<td class="l">{ticker_cell_html(v)}</td>'
            elif c in text_cols:
                cells += f'<td class="t">{_html.escape(str(v))}</td>'
            elif isinstance(v, float):
                d = 2 if any(k in str(c) for k in ("스코어", "모멘텀", "현재가", "비중")) else 1
                cells += f'<td class="{"neg" if v < 0 else ""}">{v:,.{d}f}</td>'
            else:
                sv = str(v)
                neg = sv.startswith("-") and len(sv) > 1 and sv[1].isdigit()
                cells += f'<td class="{"neg" if neg else ""}">{_html.escape(sv)}</td>'
        body += f"<tr>{cells}</tr>"
    st.markdown(f'{_TBL_CSS}<table class="dtbl"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>', unsafe_allow_html=True)


def render_alloc_table(df):
    """비중 분배 현황: 자산마다 2줄(수치 줄 + 참여 전략·선택 기준 줄)로 폰에서도 한눈에 보이는 표."""
    num_cols = ["자산군", "현재가 ($)", "배분 비중 (%)", "1M", "3M", "6M", "12M"]
    head = "".join(f"<th>{_html.escape(c)}</th>" for c in num_cols)
    body = ""
    for _, r in df.iterrows():
        cells = f'<td class="l">{ticker_cell_html(r["자산군"])}</td>'
        cells += f'<td>{_html.escape(str(r["현재가 ($)"]))}</td>'
        cells += f'<td class="wt">{float(r["배분 비중 (%)"]):,.2f}%</td>'
        for c in ("1M", "3M", "6M", "12M"):
            sv = str(r[c])
            neg = sv.startswith("-") and len(sv) > 1 and sv[1].isdigit()
            cells += f'<td class="{"neg" if neg else ""}">{_html.escape(sv)}</td>'
        detail = (
            f'<b>참여 전략</b> {_html.escape(str(r["참여 전략 (신호)"]))}<br>'
            f'<b>선택 기준·값</b> {_html.escape(str(r["선택 기준 · 값"]))}'
        )
        body += f'<tr class="main">{cells}</tr><tr class="detail"><td colspan="{len(num_cols)}" class="t">{detail}</td></tr>'
    st.markdown(
        _TBL_CSS
        + "<style>.dtbl td.wt{background:#fefce8 !important;font-size:1.08em;font-weight:700;color:#0f172a}"
        + ".dtbl td.l .tk{font-size:1.08em;color:#0f172a}.dtbl td.l .tk-name{display:block;margin-left:0}"
        + ".dtbl tr.detail td{background:#f1f5f9;color:#334155;font-size:0.92em;line-height:1.45}"
        + ".dtbl tr.main td{border-bottom:none}.dtbl tr.detail td{border-top:none}</style>"
        + f'<table class="dtbl"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>',
        unsafe_allow_html=True,
    )


def render_drawdown_with_benchmark(chart_df, strategy_name):
    """낙폭 히스토리: 전략(진한 빨강) 위에 벤치마크 QQQ(연한 회색)를 겹쳐 표시."""
    import altair as alt
    dd_df = pd.DataFrame({
        "date_str": chart_df["date_str"].values,
        strategy_name: chart_df["drawdown"].values,
    })
    if "qqq_nav" in chart_df.columns:
        q_nav = pd.Series(chart_df["qqq_nav"].values, dtype=float)
        dd_df["QQQ"] = ((q_nav / q_nav.cummax() - 1.0) * 100.0).values
    # 표시 구간 선택 (슬라이더로 원하는 기간만 확대해서 보기)
    _all_dates = dd_df["date_str"].tolist()
    if len(_all_dates) > 2:
        _lo, _hi = st.select_slider(
            "🔍 표시 구간 (양쪽 손잡이를 움직이면 해당 기간만 확대됩니다)",
            options=_all_dates, value=(_all_dates[0], _all_dates[-1]),
            key=f"dd_zoom_{strategy_name}",
        )
        _i0, _i1 = _all_dates.index(_lo), _all_dates.index(_hi)
        dd_df = dd_df.iloc[_i0:_i1 + 1].reset_index(drop=True)
    long_df = dd_df.melt(id_vars="date_str", var_name="series", value_name="drawdown")
    long_df["drawdown"] = long_df["drawdown"].round(2)

    domain = [strategy_name, "QQQ"]
    color_scale = alt.Scale(domain=domain, range=["#dc2626", "#9ca3af"])
    x_enc = alt.X("date_str:N", sort=None, title="년-월", axis=alt.Axis(labelOverlap=True))
    y_enc = alt.Y("drawdown:Q", title="MDD (%)")
    tip = [alt.Tooltip("date_str:N", title="년-월"), alt.Tooltip("series:N", title="구분"),
           alt.Tooltip("drawdown:Q", title="낙폭 (%)", format=".2f")]
    color_enc = alt.Color("series:N", scale=color_scale, sort=domain,
                          legend=alt.Legend(orient="top", title=None))

    # 뒤: QQQ 연한 회색 / 앞: 전략 진한 빨강 (면 + 테두리선)
    qqq_layer = alt.Chart(long_df[long_df["series"] == "QQQ"]).mark_area(
        opacity=0.35, line={"color": "#9ca3af", "strokeWidth": 1}
    ).encode(x=x_enc, y=y_enc, color=color_enc, tooltip=tip)
    strat_layer = alt.Chart(long_df[long_df["series"] == strategy_name]).mark_area(
        opacity=0.6, line={"color": "#991b1b", "strokeWidth": 1.5}
    ).encode(x=x_enc, y=y_enc, color=color_enc, tooltip=tip)

    st.altair_chart((qqq_layer + strat_layer).properties(height=220), use_container_width=True)

    if "QQQ" in dd_df.columns:
        st.caption(
            f"빨강 = {strategy_name} (선택 구간 MDD {dd_df[strategy_name].min():.2f}%), "
            f"연회색 = 벤치마크 QQQ (선택 구간 MDD {dd_df['QQQ'].min():.2f}%)"
        )


def render_strategy_report():
    """혼합전략 탭 최하단: 종합평가서 + 개선 작업 보고서 (문제 -> 개선안 -> 백테스트 -> 판정 -> 최종 결과 -> 지적 대응)."""
    st.markdown("## 📑 전략 종합평가 및 개선 작업 보고서")
    st.caption("검증 기준: 야후 파이낸스 실데이터 2014-01 ~ 2026-09 · 백테스트 시작일 2015/2018/2020 3구간 교차 확인 (아래 표는 2018~ 기준) · 2026-10-01 정리")
    st.info(
        "**한 줄 결론** — 종합평가서가 지적한 개선안(전략 C Z-Score, 전략 B 평활화·변동성 타깃팅, VIX 레버리지 축소 등)을 "
        "모두 실제 데이터로 백테스트해 봤고, **기존 전략보다 성과를 개선한 항목은 없었습니다.** "
        "그래서 전략 로직은 기존 그대로 유지하고, 큰 폭락 대비용 안전장치(월중 하드스탑·비중 상한)만 선택형으로 남겼습니다."
    )

    with st.expander("① 종합평가서 요약 — 강점과 지적된 한계", expanded=False):
        st.markdown("""
**강점**

- 물가연동국채(TIP)로 실질금리 변화를 추적하고, 시장 배당수익률 밸류에이션 필터와 결합해 거시 국면 전환을 선제 감지
- 하락장에서는 모멘텀 제로 플로어(Zero-Floor) 규칙으로 최대 100% 현금 대피 가능

**지적된 구조적 한계**

- 명목 비중은 33.33%씩이지만 3배 레버리지에 단일 집중하는 전략 B가 전체 위험의 65~75% 이상을 지배
- 하위 전략 간 유니버스 중복으로 특정 ETF에 쏠림 발생 (예: 2019년 5월 SMH 41.66%)
- S&P 500 배당수익률이 구조적으로 낮아져(1% 내외) 전략 C의 고정 기준선(1.33%)이 강세장에서도 방어 신호만 내는 '신호 동결' 우려
""")

    with st.expander("② 분석 결과 — 확인된 문제와 개선 방향", expanded=False):
        st.markdown("""
| 항목 | 코드·데이터로 확인한 내용 | 제안된 개선 |
|---|---|---|
| 전략 C 신호 | 기준선 1.33%가 4곳에 하드코딩. 현재 배당수익률 0.99% | 36개월 롤링 Z-Score |
| 전략 B 집중 | 점수 공식에서 최근 1개월이 63.16% | 가중 완화 + 변동성 타깃팅 |
| 종목 쏠림 | 혼합 합산 시 한 종목에 비중 집중 가능 | 단일자산 상한 35% |
| 공포 구간 | 3배 ETF 변동성 잠식 우려 | VIX 28 초과 시 레버리지 절반 |
| **추가 발견** | 배당 조정가를 써서 과거 배당수익률이 과대 계산됨 | 비조정 종가로 정정 (CAGR 2~4%p 하락) |
""")
        st.caption("진행 방식: 모든 개선을 적용/미적용 토글과 전·후 비교표로 구현해 실제 데이터로 검증한 뒤, 효과 없는 항목은 제거했습니다.")

    with st.expander("③ 개선안 적용 백테스트 결과 (2018~)", expanded=False):
        st.markdown("""
**전략 C — 배당수익률 신호**

| 방식 | CAGR | MDD | 샤프 | 공격 비율 |
|---|---|---|---|---|
| **① 기존 (고정 1.33%)** | **52.6%** | **-17.2%** | **1.68** | 65% |
| ② 고정 + 비조정가 | 49.3% | -17.2% | 1.61 | 56% |
| ③ Z-Score 36개월 | 42.8% | -23.4% | 1.54 | 34% |

2015~ 구간도 동일(CAGR 44.7% → 33.6%, MDD -17.2% → -31.0%). 2020~에서만 Z가 소폭 우세(51.1% vs 50.1%).

**전략 B — 모멘텀 가중·변동성 타깃팅**

| 방식 | CAGR | MDD | 샤프 |
|---|---|---|---|
| **① 기존 12-4-2-1** | **42.4%** | **-22.7%** | **1.34** |
| ② 완화 4-3-2-1 | 33.2% | -37.7% | 1.06 |
| ③ 변동성 타깃 35% | 30.6% | -15.8% | 1.29 |
| ④ 둘 다 | 24.3% | -31.7% | 0.98 |

**혼합전략 — MDD 안전장치**

| 방식 | CAGR | MDD | 샤프 | 발동 |
|---|---|---|---|---|
| ① 없음 | 43.9% | -13.0% | 2.10 | - |
| ② 상한 35% | 39.6% | -12.0% | 2.06 | 66개월 |
| ③ VIX 28 | 41.7% | -13.0% | 2.10 | 7개월 |
| ④ 상한 25% | 30.1% | -8.9% | 2.07 | 92개월 |
| ⑤ 하드스탑 -7% | 40.1% | -9.6% | 1.87 | 6개월 |
| ⑥ 상한 25% + 하드스탑 | 25.3% | -9.8% | 1.59 | 6개월 |
""")

    with st.expander("④ 판정 — 의미 없었던 것과 적용한 것", expanded=False):
        st.markdown("""
| 항목 | 판정 | 근거 |
|---|---|---|
| 전략 C Z-Score | ❌ 제거 | CAGR·MDD 모두 열위 |
| 전략 B 가중 완화 | ❌ 제거 | 수익·MDD 모두 악화 |
| 전략 B 변동성 타깃팅 | ❌ 제거 | MDD만 감소, CAGR 12%p 하락, 샤프 개선 없음 |
| VIX 28 레버리지 축소 | ❌ 제거 | 7개월만 발동, MDD 변화 없음 |
| 상관관계 필터 | ❌ 미구현 | 필요 없다고 판단 |
| 월중 하드스탑 (-7%) | ✅ 유지 | 큰 폭락 대비 보험. 2018~ MDD -13.0% → -9.6% |
| 비중 상한 (입력칸) | ✅ 유지 | MDD를 줄이는 선택 장치 (CAGR도 함께 감소) |
| 전략 C 기준선 1.33% | ✅ 기존 유지 | 바꿔서 확실히 나아지는 값이 없음 |
""")

    with st.expander("⑤ 최종 결과 — 지금의 전략", expanded=True):
        st.markdown("""
전략 A·B·C의 로직은 **원본 그대로**이며, 제거 후 엔진의 NAV가 원본과 정확히 일치함을 3개 구간 × 4개 엔진 모두 확인했습니다.

| 전략 | 2015~ CAGR / MDD | 2018~ CAGR / MDD | 2020~ CAGR / MDD |
|---|---|---|---|
| A | 25.1% / -15.7% | 29.8% / -15.7% | 24.2% / -15.7% |
| B | 37.8% / -22.7% | 42.4% / -22.7% | 37.1% / -18.8% |
| C | 44.7% / -17.2% | 52.6% / -17.2% | 50.1% / -17.1% |
| **혼합** | **37.7% / -13.0%** | **43.9% / -13.0%** | **39.4% / -9.6%** |

혼합전략 샤프 지수는 2.03 / 2.10 / 2.21로, 개별 전략(1.3~1.7)보다 높습니다. 안전장치는 체크박스로 켜고 끄며, 기본값은 꺼짐입니다.
""")

    with st.expander("⑥ 이런 지적을 받는다면 — 이미 검증했습니다", expanded=False):
        st.markdown("""
| 지적 | 검증 결과 |
|---|---|
| "배당수익률이 낮아져 전략 C 기준선 1.33%는 상시 방어 아닌가?" | 36개월 Z-Score로 바꿔 검증 → CAGR 52.6%→42.8%, MDD -17.2%→-23.4%로 오히려 악화. 기준선 1.2~1.5%가 안정 구간이며 1.3%는 뾰족한 최적값이라 과최적화 가능성은 인지 |
| "3배 레버리지 전략 B가 위험을 지배한다" | 변동성 타깃팅 검증 → MDD -22.7%→-15.8%로 줄지만 CAGR 42.4%→30.6%, 샤프 1.34→1.29. 위험만 줄이는 수단이라 제거. 혼합 시 MDD는 -13.0%로 분산 효과 확인 |
| "최근 1개월 비중 63%는 휩소가 많다" | 4-3-2-1 완화 검증 → CAGR 33.2%, MDD -37.7%로 악화 |
| "특정 ETF 쏠림이 위험하다" | 비중 상한 35%/25% 검증 → MDD -12.0%/-8.9%로 감소하나 CAGR 39.6%/30.1%로 하락, 샤프는 약 2.1로 동일. 선택 장치로 제공 |
| "공포 구간에 3배 ETF 비중을 줄여야 한다 (VIX 28)" | 검증 → 7개월만 발동하고 MDD 변화 없음 |
| "닷컴·금융위기급 폭락에 대비가 없다" | 월중 하드스탑(-7%) 보유. 2018~·2020~ MDD -13.0%→-9.6% (CAGR 3~4%p 비용). 2015~ 구간에서는 -14.0%로 악화될 수 있음 |
| "백테스트가 과최적화 아닌가?" | 인정: 전 구간 표본 내 성과. 3개 시작일로 교차 확인했고, 한 점이 아닌 안정 구간을 기준으로 판단 |
""")

    with st.expander("⑦ 개선 작업 진행 내용", expanded=False):
        st.markdown("""
| 단계 | 내용 | 상태 |
|---|---|---|
| 1 | 전략 C 배당수익률 Z-Score 구현 → 실데이터 검증 → 효과 없어 제거 | ✅ 완료 |
| 2 | 전략 B 가중 완화·변동성 타깃팅 구현 → 검증 → 제거 | ✅ 완료 |
| 3 | 혼합 안전장치 검증 → VIX 제거, 비중 상한·하드스탑 유지 | ✅ 완료 |
| 4 | 정리 후 4개 엔진이 원본과 일치하는지 최종 검증 | ✅ 완료 |
| 5 | 화면 개선: 시작일 2015 기본, 탭 상단 고정, 월별 비중 33.3% 표기, 합계(A+B+C) 열, 비중 분배 표, 낙폭 확대 슬라이더, 하드스탑 실시간 모니터 | ✅ 완료 |
| 6 | 자산 계산기: 전략별 실측 CAGR 퀵 프리셋 연동, 초기값 설정 | ✅ 완료 |
| 7 | 이 보고서를 혼합전략 최하단에 배치 | ✅ 완료 |
""")

    with st.expander("⑧ 한계와 유의사항", expanded=False):
        st.markdown("""
- 모든 결과는 표본 내(in-sample) 성과이며 CAGR이 매우 높아 과최적화·생존편향 가능성이 있습니다.
- 현금 수익률 0%, 월간 데이터 기준입니다. 거래비용·세금은 기본 미반영이며, 맨 위 '⚙️ 백테스트 비용·세금 반영 설정'에서 선택할 수 있습니다.
- 하드스탑은 최근 6~7회만 발동한 표본이라 2000·2008년급 붕괴에서의 효과는 검증되지 않았습니다.
- 위 수치는 2026-10-01 시점의 검증값이며 새 데이터가 쌓이면 달라질 수 있습니다.
- 현재 SPY 배당수익률은 0.99%로, 전략 C는 고정 기준선 방식에서 방어 신호가 이어지고 있습니다.
""")


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
    
    tab_2026, tab_a, tab_b, tab_c, tab_rank, tab_ndx, tab_mdd, tab_calc = st.tabs([
        "🏆 2026 혼합전략", 
        "🛡️ 전략 A", 
        "⚡ 전략 B", 
        "🔄 전략 C",
        "🇺🇸 미국 ETF 랭킹",
        "🏢 나스닥100 랭킹",
        "📉 장기 낙폭",
        "🧮 자산 계산기"
    ])


    # 용어 설명 팝업: 마우스는 올리면, 폰은 탭하면 표시 (다른 곳을 탭하면 닫힘)
    components.html("""
<script>
(function () {
  var win = window.parent, doc = win.document;
  try { if (win.__glOff) { win.__glOff(); } } catch (e) {}
  var pop = doc.getElementById('gl-pop');
  if (!pop) {
    pop = doc.createElement('div'); pop.id = 'gl-pop';
    pop.style.cssText = 'position:fixed;z-index:100000;display:none;background:#1e293b;color:#f8fafc;padding:8px 10px;border-radius:8px;font-size:13px;line-height:1.5;font-weight:400;white-space:pre-line;word-break:keep-all;box-shadow:0 6px 18px rgba(15,23,42,.35);pointer-events:none;';
    doc.body.appendChild(pop);
  }
  var cur = null, ptype = 'mouse';
  function tgt(e) { return e.target && e.target.closest ? e.target.closest('.gl') : null; }
  function show(el) {
    var t = el.getAttribute('data-tip'); if (!t) { return; }
    pop.textContent = t; pop.style.display = 'block';
    pop.style.maxWidth = Math.min(280, win.innerWidth - 16) + 'px';
    var r = el.getBoundingClientRect(), w = pop.offsetWidth, h = pop.offsetHeight;
    var x = Math.max(8, Math.min(r.left, win.innerWidth - w - 8));
    var y = r.bottom + 6; if (y + h > win.innerHeight - 8) { y = Math.max(8, r.top - h - 6); }
    pop.style.left = x + 'px'; pop.style.top = y + 'px'; cur = el;
  }
  function hide() { pop.style.display = 'none'; cur = null; }
  function onDown(e) { ptype = e.pointerType || 'mouse'; if (!tgt(e)) { hide(); } }
  function onOver(e) { if (ptype !== 'mouse') { return; } var el = tgt(e); if (el) { show(el); } }
  function onOut(e) { if (ptype !== 'mouse') { return; } if (tgt(e)) { hide(); } }
  function onClick(e) { if (ptype === 'mouse') { return; } var el = tgt(e); if (!el) { return; } if (cur === el) { hide(); } else { show(el); } }
  doc.addEventListener('pointerdown', onDown, true);
  doc.addEventListener('mouseover', onOver, true);
  doc.addEventListener('mouseout', onOut, true);
  doc.addEventListener('click', onClick, true);
  win.addEventListener('scroll', hide, true);
  var mt = null;
  function markCost() {
    doc.querySelectorAll('[data-testid="stExpander"]').forEach(function (e) {
      var sm = e.querySelector('summary');
      if (sm && sm.textContent.indexOf('백테스트 비용·세금') >= 0) { e.classList.add('cost-exp'); }
    });
  }
  markCost();
  var mo = new win.MutationObserver(function () { if (mt) { win.clearTimeout(mt); } mt = win.setTimeout(markCost, 200); });
  mo.observe(doc.body, { childList: true, subtree: true });
  win.__glOff = function () {
    doc.removeEventListener('pointerdown', onDown, true); doc.removeEventListener('mouseover', onOver, true);
    doc.removeEventListener('mouseout', onOut, true); doc.removeEventListener('click', onClick, true);
    win.removeEventListener('scroll', hide, true);
    mo.disconnect();
  };
})();
</script>
""", height=0)

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
    var N_STRAT = 4;  // 앞 4개 탭(혼합전략·A·B·C)이 '전략' 그룹, 나머지는 '정보' 그룹
    var tabs = tl.querySelectorAll('[role="tab"]');
    for (var i = 0; i < tabs.length; i++) {
      var g = i < N_STRAT ? 's' : 'i';
      var f = (i === 0 || i === N_STRAT) ? '1' : '0';
      if (tabs[i].getAttribute('data-grp') !== g) { tabs[i].setAttribute('data-grp', g); }
      if (tabs[i].getAttribute('data-first') !== f) { tabs[i].setAttribute('data-first', f); }
    }
    if (tabs.length > N_STRAT) {
      var ge = tabs[0].parentElement;  // 모든 탭을 직접 담고 있는 가장 가까운 공통 부모
      while (ge && !ge.contains(tabs[tabs.length - 1])) { ge = ge.parentElement; }
      if (ge) {
        if (!ge.classList.contains('tab-grid')) { ge.classList.add('tab-grid'); }
        doc.querySelectorAll('.tab-grp-label').forEach(function (e) { if (e.parentElement !== ge) { e.remove(); } });  // 이전 버전이 남긴 라벨 정리
        if (ge.querySelectorAll(':scope > .tab-grp-label').length !== 2) {
          ge.querySelectorAll(':scope > .tab-grp-label').forEach(function (e) { e.remove(); });
          var lbI = doc.createElement('div'); lbI.className = 'tab-grp-label i'; lbI.textContent = 'INSIGHTS';
          var lbS = doc.createElement('div'); lbS.className = 'tab-grp-label s'; lbS.textContent = 'STRATEGY';
          ge.insertBefore(lbI, ge.firstChild);
          ge.insertBefore(lbS, ge.firstChild);
        }
      }
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
    with tab_ndx:
        c_ndx = st.container()
    with tab_mdd:
        c_mdd = st.container()
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

        with st.expander("📖 2026 혼합전략 명세서", expanded=False):
            st.markdown(r"""
## 개요

2026 혼합전략은 성격이 다른 3개 동적 자산배분 전략(A 안정형, B 레버리지 공격형, C 섹터로테이션)을 각 33.33% 동일 비중으로 합친 월간 리밸런싱 전략입니다. 벤치마크는 QQQ입니다.

| 구성 요소 | 카나리아(국면 판단) | 공격 시 | 방어 시 |
| --- | --- | --- | --- |
| 전략 A (안정형) | TIP 현재가 vs 11개월 이동평균 | 모멘텀 상위 4종목 × 25% | 모멘텀 1위 100% 또는 현금 |
| 전략 B (공격형) | TIP 1·3·6·9·12개월 평균 모멘텀 부호 | 가중 모멘텀 1위 100% | 5개월 수익률 1위 100% 또는 현금 |
| 전략 C (섹터로테이션) | SPY 12개월 배당수익률 > 1.33% | 모멘텀 1위 섹터 100% | 모멘텀 1위 100% 또는 현금 |

선택 적용 리스크 장치로 단일 자산 비중 상한(기본 35%)과 월중 하드스탑(기본 -7%)이 있습니다. 둘 다 백테스트 설정 패널의 체크박스로 켜고 끄며, 기본 상태는 꺼짐입니다.

## 투자 유니버스와 데이터

| 전략 | 공격 자산군 | 방어 자산군 |
| --- | --- | --- |
| A | QQQ, FEZ, GLD, IBB, SMH, EEM, XLK, LIT, XLE, UBT, XLV, QTUM (12개) | BIL, IEF, AGG, HYG, TBF (5개) |
| B | TYD, UPRO, VNQ (3개) | DOG, RWM, TBF (3개) |
| C | FDN, LIT, SMH, XLE, IGV, QQQM, XLU (7개) | GLD, PDBC, OILK, SHY, TLT (5개) |

전략 간 겹치는 티커가 있습니다. SMH·LIT·XLE는 A공격과 C공격, GLD는 A공격과 C방어, TBF는 A방어와 B방어에 함께 들어 있습니다. 합산 비중이 한 종목에 쏠리는 원인이 바로 이 중복입니다.

- **출처**: yfinance(야후 파이낸스) 일별 종가, `auto_adjust=True`(배당·분할 반영 수정주가). 캐시 유효시간 1시간.
- **월간 변환**: 일별 종가를 월말 마지막 값으로 리샘플링합니다.
- **배당 데이터**: SPY 배당 이력을 전략 C 카나리아에 씁니다.
- **시작일**: 2015-01-01(기본), 2018-01-01, 2020-01-01 중 선택. 첫 12개월은 모멘텀 계산용 워밍업이라 성과 기록에서 빠집니다.

## 전략 A: 대형 우량 자산 안정형

매월 말 TIP 종가가 최근 11개월(당월 포함) 종가 평균보다 높으면 공격, 같거나 낮으면 방어입니다.

**모멘텀 정의**: R_n = (당월 말 종가 ÷ n개월 전 월말 종가 − 1) × 100. 모든 전략이 이 정의를 씁니다.

1. **공격 스코어**: 공격 자산 12개에 4구간 평균을 적용합니다. R_1과 R_12가 모두 있어야 후보가 됩니다.
2. **공격 배분**: 점수 상위 4종목에 각 25%. 후보가 없으면 현금 100%.
3. **방어 스코어**: 방어 자산 5개에 9개월 구간을 더한 5구간 평균을 씁니다.
4. **방어 배분**: 점수 1위 자산에 100%. 단, 1위 점수가 0 이하면 현금 100%.
""")
            st.latex(r"Score_{A,\text{공격}} = \frac{R_1 + R_3 + R_6 + R_{12}}{4} \qquad Score_{A,\text{방어}} = \frac{R_1 + R_3 + R_6 + R_9 + R_{12}}{5}")
            st.markdown(r"""
## 전략 B: 레버리지 공격형

TIP의 5구간 평균 모멘텀이 0보다 크면 공격, 0 이하면 방어입니다. 어느 쪽이든 1종목에 100% 집중합니다. TIP 모멘텀 5개 중 하나라도 계산되지 않는 달은 기록에서 빠집니다.

1. **공격 스코어**: TYD·UPRO·VNQ에 최근 수익률 비중이 큰 가중 모멘텀을 적용합니다. R_12가 있어야 후보가 됩니다.
2. **공격 배분**: 점수 1위에 100%. 후보가 없으면 현금 100%.
3. **방어 선정**: DOG·RWM·TBF 중 최근 5개월 수익률(R_5)이 가장 높은 자산을 고릅니다.
4. **방어 필터**: 선정 자산의 5구간 평균 모멘텀이 0보다 크면 100% 투자, 아니면 현금 100%.

방어 시 순위(R_5)와 진입 필터(5구간 평균)가 서로 다른 지표라는 점이 A·C와 다릅니다.
""")
            st.latex(r"Canary_B = \frac{R_1 + R_3 + R_6 + R_9 + R_{12}}{5}\,(TIP) > 0 \qquad Score_{B,\text{공격}} = \frac{12R_1 + 4R_3 + 2R_6 + R_{12}}{19}")
            st.markdown(r"""
## 전략 C: 배당 기반 섹터 로테이션

SPY의 최근 365일 배당 합계를 월말 SPY 종가로 나눈 배당수익률이 1.33%를 넘으면 공격, 이하면 방어입니다. 배당 합계가 0이거나 가격이 없는 달은 기록에서 빠집니다.

1. **공격 스코어**: 섹터 ETF 7개에 전략 A와 같은 4구간 평균을 적용합니다. R_12가 있어야 후보가 됩니다.
2. **공격 배분**: 점수 1위 섹터에 100%. 후보가 없으면 현금 100%.
3. **방어 스코어**: 원자재·채권 5개에 5구간 평균(R_1·R_3·R_6·R_9·R_12)을 적용합니다.
4. **방어 배분**: 점수 1위에 100%. 1위 점수가 0 이하면 현금 100%.

실시간 화면의 배당수익률은 `get_sp500_dividend_yield()`가 최근 배당 이력과 현재가로 따로 계산하며, 백테스트와 같은 1.33% 기준을 씁니다.
""")
            st.latex(r"DY = \frac{\sum Div_{SPY}(\text{최근 365일})}{P_{SPY}(\text{월말})} \times 100 > 1.33\%")
            st.markdown(r"""
## 혼합전략 결합과 월간 흐름

세 전략은 서로 독립적으로 신호를 내고, 혼합전략은 각 전략 비중에 1/3을 곱해 티커별로 더합니다. 예를 들어 A가 QQQ·SMH·XLK·GLD에 25%씩, B가 UPRO 100%, C가 SMH 100%면 합산은 SMH 41.67%, UPRO 33.33%, QQQ·XLK·GLD 각 8.33%입니다.
""")
            st.graphviz_chart("""
digraph G {
    rankdir=TB; nodesep=0.35; ranksep=0.45;
    node [shape=box, style="rounded", fontname="sans-serif", fontsize=11, color="#94a3b8"];
    edge [color="#94a3b8", arrowsize=0.7];
    A [label="전략 A · 안정형\\nTIP vs 11개월 평균\\n공격: 상위 4종목 × 25%\\n방어: 채권 1위 또는 현금"];
    B [label="전략 B · 레버리지\\nTIP 5구간 모멘텀 양수 여부\\n공격: 가중 모멘텀 1위 100%\\n방어: 인버스 1위 또는 현금"];
    C [label="전략 C · 섹터로테이션\\nSPY 배당수익률 1.33% 초과\\n공격: 모멘텀 1위 섹터 100%\\n방어: 원자재·채권 또는 현금"];
    M [label="동일 비중 합산\\n전략별 비중 × 1/3을 티커별로 더함"];
    CAP [label="비중 상한 (선택)\\n단일 티커 35% 초과분 → 현금", style="rounded,dashed"];
    STOP [label="월중 하드스탑 (선택)\\n월초 대비 −7% 도달일에 청산\\n이후 월말까지 현금", style="rounded,dashed"];
    R [label="다음 달 수익 확정\\n다음 월말 종가 기준 수익률\\nNAV·드로다운 기록 후 반복", style="rounded,filled", fillcolor="#dbeafe", color="#2563eb"];
    {rank=same; A; B; C;}
    {rank=same; CAP; STOP; R;}
    A -> M; B -> M; C -> M;
    M -> CAP; CAP -> STOP; STOP -> R;
}
""")
            st.caption("점선 상자는 체크박스로 켜는 선택 장치이며 기본값은 꺼짐입니다. 꺼져 있으면 그대로 통과하고, 합산 비중이 그대로 다음 달 수익률에 적용됩니다.")
            st.markdown(r"""
## 리스크 관리 장치

두 장치는 `run_backtest_strategy_mix_improved_full()`에 구현되어 있고, 하나라도 켜면 개선판 엔진으로 계산합니다. 도입 근거는 2019년 5월 무역전쟁 급락 때 SMH 41.66%, UPRO 33.33%로 비중이 겹치며 MDD -13.0%가 났던 사례입니다.

| 항목 | 비중 상한 (Cap) | 월중 하드스탑 |
| --- | --- | --- |
| 기본값 | 35% | -7.0% |
| 입력 범위 | 10 – 50%, 1%p 단위 | -20.0 – -1.0%, 0.5%p 단위 |
| 기본 적용 여부 | 꺼짐 (체크박스) | 꺼짐 (체크박스) |
| 판단 시점 | 월말 리밸런싱 시 | 다음 달 매 영업일 종가 |
| 발동 조건 | 합산 후 단일 티커 비중 > 상한 | 월초 대비 누적 수익률 ≤ 임계치 |
| 처리 | 초과분을 현금으로 전환 (재배분 없음) | 첫 도달일 수익률로 그달 확정, 이후 월말까지 현금 |
| 모드 표시 | 📐Cap적용 | 🛑월중손절(발동일 MM/DD) |

**비중 상한이 실제로 걸리는 경우**: 한 전략이 100%를 넣어도 합산 비중은 33.33%라 35% 상한에 걸리지 않습니다. 두 전략 이상이 같은 티커를 고를 때만 발동합니다. 예를 들어 A가 SMH 25%, C가 SMH 100%를 고르면 합산 41.67%이고, 초과분 6.67%p가 현금이 됩니다.

**하드스탑 계산 방식**: 전월 말 종가를 기준가로 삼아, 보유 종목별 일별 누적 수익률에 비중을 곱해 더합니다. 월중 리밸런싱이 없는 매수 후 보유 경로입니다. 하드스탑만 켜고 발동하지 않은 달도 일별 경로의 월말 값으로 수익률을 다시 계산합니다.

## 백테스트 방법론과 성과 지표

월말 종가로 신호와 비중을 정하고, 같은 종가에 체결했다고 보고 다음 달 월간 수익률을 적용합니다. NAV는 100에서 시작하며, 수익은 실현되는 달(다음 월말)에 기록합니다.

- **현금 수익률**: 0%로 가정합니다.
- **거래비용·세금·슬리피지**: 기본은 반영하지 않으며, 맨 위 설정에서 슬리피지(기본 1%/회)와 양도세(22%, 연 1회)를 선택 반영할 수 있습니다.
- **혼합 결합**: 세 전략이 모두 기록을 가진 날짜만 씁니다(교집합).
- **드로다운**: 월말 NAV의 직전 고점 대비 하락률입니다. 월중 낙폭은 잡히지 않습니다.

| 지표 | 계산 방식 |
| --- | --- |
| 기간 수익률 | 최종 NAV ÷ 100 − 1 |
| 연환산 수익률 (CAGR) | (최종 NAV ÷ 100)^(1 ÷ 연수) − 1, 연수 = 일수 ÷ 365.25 |
| 이번 달 수익률 | 마지막 달 월간 수익률 |
| 올해 수익률 (YTD) | 마지막 기록 연도의 월간 수익률 복리 누적 |
| 월 최고 / 월 최저 수익률 | 월간 수익률의 최댓값 / 최솟값 |
| 수익 월 비중 | 수익률 > 0인 달 수 / 전체 달 수 |
| 연 변동성 | 월간 수익률 표준편차 × √12 |
| 최대 낙폭 (MDD) / MDD 시점 | 드로다운 최솟값과 그 달 |
| 1년·3년·5년 수익률 | 최근 12·36·60개월 복리 누적. 데이터가 모자라면 "데이터 부족" |
| 1년·3년·5년 표준편차 | 같은 구간 월간 표준편차 × √12 |
| 샤프 지수 | (월평균 수익률 × 12) ÷ 연 변동성. 무위험수익률 0 |
| 소티노 지수 | (월평균 수익률 × 12) ÷ (음수 월 수익률 표준편차 × √12) |
| UPI 지수 | CAGR ÷ 궤양지수, 궤양지수 = √(드로다운² 평균) |
| 연간 턴오버 | 월별 (Σ 비중 변화의 절댓값 ÷ 2)의 평균 × 12. QQQ는 0% |

## 앱 화면 구성과 파라미터

| 파라미터 | 기본값 | 선택 범위 | 위치 |
| --- | --- | --- | --- |
| 백테스트 시작일 | 2015-01-01 | 2015 / 2018 / 2020년 1월 1일 | 설정 패널 |
| 비중 상한 | 35% | 10 – 50% | 설정 패널 |
| 월중 하드스탑 | -7.0% | -20.0 – -1.0% | 설정 패널 |
| 비중 상한 적용 | 꺼짐 | 체크박스 | 설정 패널 |
| 월중 하드스탑 적용 | 꺼짐 | 체크박스 | 설정 패널 |

실시간 비중 분배 현황에는 두 리스크 장치가 적용되지 않습니다. 장치는 백테스트 결과에만 반영됩니다.

## 한계와 유의사항

백테스트 수치는 비용이 없고 월말 종가에 바로 체결된다는 가정 위의 값이라, 실제 운용 성과보다 높게 나올 수 있습니다.

- **비용 미반영**: 전략 B·C는 매달 100% 교체될 수 있어 턴오버가 큽니다. 거래비용과 세금을 빼면 수익률이 낮아집니다. (맨 위 설정에서 반영해 확인할 수 있습니다.)
- **동일 종가 체결**: 신호를 계산한 종가에 체결한다고 봅니다. 실제로는 다음 날 시가 등에 체결되므로 차이가 생깁니다.
- **배당수익률 편향 가능성**: 전략 C 백테스트는 배당을 반영해 낮아진 수정주가로 나눕니다. 과거 배당수익률이 실제보다 높게 계산돼 공격 신호가 더 자주 나올 수 있습니다.
- **현금 수익률 0%**: 현금 비중이 큰 방어 구간과 상한 초과분의 이자 수익이 빠져 있습니다.
- **실시간 비중과 백테스트 차이**: 실시간 비중 분배에는 비중 상한이 적용되지 않습니다. 상한을 운용 규칙으로 쓰려면 매매 시 따로 확인해야 합니다.
- **하드스탑 가정**: 임계치에 닿은 날 종가에 전량 매도된다고 봅니다. 장중 급락이나 갭하락은 반영하지 못합니다.
- **짧은 이력 자산**: QTUM, QQQM, OILK 등은 상장 기간이 짧습니다. 데이터가 없는 달에는 후보에서 빠지므로 초기 구간의 선택 폭이 좁습니다.
- **데이터 의존성**: yfinance 응답이 바뀌거나 비면 결과가 달라지거나 표시되지 않을 수 있습니다.

이 명세서는 코드 동작을 정리한 문서이며 투자 권유가 아닙니다.
""")

        st.markdown("### 🚦 실시간 카나리아 신호 요약")
        c_sig1, c_sig2, c_sig3 = st.columns(3)
        c_sig1.metric("전략A (TIP 비율)", f"{tip_ratio:.3f}", "공격" if is_attack_a else "방어", delta_color="inverse" if not is_attack_a else "normal")
        c_sig2.metric("전략B (TIP 모멘텀)", f"{tip_score_b:.2f}%", "공격" if is_attack_b else "방어", delta_color="inverse" if not is_attack_b else "normal")
        c_sig3.metric("전략C (배당수익률)", f"{realtime_dy:.2f}%", "공격" if is_attack_c else "방어", delta_color="inverse" if not is_attack_c else "normal")

        st.markdown("### 📊 포트폴리오 비중 분배 현황")
        render_alloc_chips(df_mix)
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
                            labelFontSize=13.5,
                            labelFontWeight="bold",
                            symbolType="circle",
                            symbolSize=160,
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
        
        render_alloc_table(df_mix_view)
        st.caption("※ 자산군에 마우스를 올리거나(폰은 터치) ETF 설명이 표시됩니다. 선택 기준·값: 각 전략이 해당 자산을 고른 이유와 스코어입니다. 1M·3M·6M·12M은 해당 자산의 기간별 수익률입니다. 배분 비중은 전체 자산 대비 %입니다.")

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

        st.markdown("---")
        render_intramonth_stop_monitor(hist_prices, spy_divs_hist)

        if hist_prices and "SPY" in hist_prices:
            st.markdown("---")
            st.markdown("### 📅 월말 기준 리밸런싱 포트폴리오 역사 (최근 1년)")
            st.caption("매월 최종 영업일 마감 데이터를 기준으로 실시간 모멘텀과 시그널을 연산하여, 익월 1일 아침 리밸런싱 시 적용되는 혼합 포트폴리오 구성 비중입니다.")
            
            spy_series = hist_prices["SPY"]
            df_spy_dates = spy_series.to_frame()
            df_spy_dates['year'] = df_spy_dates.index.year
            df_spy_dates['month'] = df_spy_dates.index.month
            
            month_ends = df_spy_dates.groupby(['year', 'month']).apply(lambda x: x.index[-1]).tolist()
            
            now = now_us_eastern()  # 미국 동부 시간 기준 (한국 새벽에 미국 장중인 월말을 '완료'로 잘못 판정하지 않도록)
            completed_month_ends = [d for d in month_ends if not (d.year == now.year and d.month == now.month)]
            completed_12_months = completed_month_ends[-12:]
            completed_12_months.reverse()
            
            col_h1, col_h2 = st.columns(2)
            for idx, date in enumerate(completed_12_months):
                target_col = col_h1 if idx < 6 else col_h2  # 모바일에서 세로로 쌓여도 최신순 유지
                
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
            mix_cap = _mc1.number_input("비중 상한 (%)", min_value=10.0, max_value=50.0, value=35.0, step=1.0, key="mix_cap_pct")
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
                bt_results_mix = apply_trading_costs(bt_results_mix)
                bt_ok_mix = len(bt_results_mix) > 0
            except Exception as e:
                st.error(f"2026 혼합전략 백테스트 데이터 로딩 중 오류가 발생했습니다: {e}")
                bt_ok_mix = False

        if not bt_ok_mix:
            st.warning("백테스트 데이터가 부족하거나 오류가 있습니다. 잠시 후 다시 시도해 주세요.")
        else:
            st.caption(f"시뮬레이션 기간: {bt_results_mix['date'].iloc[0].strftime('%Y-%m')} ~ {bt_results_mix['date'].iloc[-1].strftime('%Y-%m')}")
            cost_status_caption(bt_results_mix)
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

            hl_cards([
                ("연환산 복리 수익률 (CAGR)", cagr_mix, "연평균 복리 수익률"),
                ("최대 낙폭 (MDD)", f"{mdd_mix:.2f}%", "직전 고점 대비 최대 하락", "neg"),
                ("최종 자산 가치 (NAV)", f"{final_nav_mix:.1f}", "초기금 100 기준", "neutral"),
            ])

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

            annual_bar_mix = alt.Chart(yearly_returns_mix).mark_bar().encode(
                x=alt.X("year_str:N", title="연도", sort=year_sort_order_mix, scale=alt.Scale(paddingInner=0.5, paddingOuter=0.2)),
                y=alt.Y("annual_return:Q", title="수익률 (%)"),
                color=alt.Color("series:N", scale=color_scale_mix, legend=alt.Legend(title=None, orient="bottom")),
                tooltip=[
                    alt.Tooltip("year_str:N", title="연도"),
                    alt.Tooltip("annual_return:Q", title="수익률", format="+.2f"),
                ],
            )
            annual_labels_mix = alt.Chart(yearly_returns_mix).mark_text(
                dy=alt.expr("datum.annual_return >= 0 ? -8 : 14"), fontWeight="bold", fontSize=10, color="#0f172a"
            ).encode(
                x=alt.X("year_str:N", sort=year_sort_order_mix, scale=alt.Scale(paddingInner=0.5, paddingOuter=0.2)),
                y=alt.Y("annual_return:Q"),
                text=alt.Text("annual_return:Q", format=".1f"),
            )
            qqq_points_mix = alt.Chart(qqq_yearly_mix).mark_point(
                filled=True, size=110, stroke="white", strokeWidth=1.2
            ).encode(
                x=alt.X("year_str:N", sort=year_sort_order_mix, scale=alt.Scale(paddingInner=0.5, paddingOuter=0.2)),
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
            monthly_compound_cards(bt_results_mix)
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
            render_drawdown_with_benchmark(chart_df_mix, "2026 혼합전략")

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
            render_gl_table(df_metrics_mix)
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
                    apply_cap=cap is not None, weight_cap=cap if cap is not None else 35.0,
                    apply_stop_loss=stop is not None, stop_loss_pct=stop if stop is not None else -7.0,
                )

            _mix_cases = {
                "① 안전장치 없음": {},
                f"② 상한 {mix_cap:.0f}%만": {"cap": mix_cap},
                f"③ 하드스탑 {mix_stop:.1f}%만": {"stop": mix_stop},
                "④ 상한 + 하드스탑": {"cap": mix_cap, "stop": mix_stop},
            }
            _mix_res = {k: apply_trading_costs(_run_mix(**v)) for k, v in _mix_cases.items()}
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

        st.markdown("---")
        render_strategy_report()

    with c_a:
        st.header("🛡️ 전략 A (안정형)")

        with st.expander("📖 전략 A 명세서", expanded=False):
            st.markdown(r"""
## 개요

전략 A는 TIP(물가연동채)로 국면을 판단해, 공격 국면에는 모멘텀 상위 4종목에 25%씩 분산하고 방어 국면에는 채권 1종목 또는 현금으로 대피하는 월간 로테이션 전략입니다. 2026 혼합전략에서 33.33%를 맡는 안정형 축입니다.

| 항목 | 내용 |
| --- | --- |
| 카나리아 | TIP 월말 종가 vs 최근 11개월(당월 포함) 월말 종가 평균 |
| 공격 조건 | TIP 종가 > 11개월 평균 (신호 비율 > 1.0) |
| 공격 시 | 공격 자산 12개 중 모멘텀 상위 4종목 × 25% |
| 방어 시 | 방어 자산 5개 중 모멘텀 1위 100%, 1위 점수 ≤ 0이면 현금 100% |
| 리밸런싱 | 매월 말 종가 기준 전량 재배분, 월중 매매 없음 |
| 월중 하드스탑 | 사용하지 않음 |

## 자산군

| 구분 | 티커 |
| --- | --- |
| 공격 (12개) | QQQ, FEZ, GLD, IBB, SMH, EEM, XLK, LIT, XLE, UBT, XLV, QTUM |
| 방어 (5개) | BIL, IEF, AGG, HYG, TBF |

## 운용 규칙

**모멘텀 정의**: R_n = (당월 말 종가 ÷ n개월 전 월말 종가 − 1) × 100.

1. **국면 판단**: 매월 말 TIP 종가를 최근 11개월 평균과 비교해 공격 또는 방어를 정합니다.
2. **공격 스코어**: 공격 자산 12개에 4구간 평균 모멘텀을 계산합니다. R_1과 R_12가 모두 있어야 후보가 됩니다.
3. **공격 배분**: 점수 상위 4종목에 각 25%. 절대 모멘텀 컷오프 없이 순위로만 고르며, 후보가 없으면 현금 100%.
4. **방어 스코어**: 방어 자산 5개에 9개월 구간을 더한 5구간 평균을 계산합니다.
5. **방어 배분**: 점수 1위 자산에 100%. 1위 점수가 0 이하면 현금 100%.
""")
            st.latex(r"Score_{\text{공격}} = \frac{R_1 + R_3 + R_6 + R_{12}}{4} \qquad Score_{\text{방어}} = \frac{R_1 + R_3 + R_6 + R_9 + R_{12}}{5}")
            st.markdown(r"""
## 혼합전략 안에서의 역할

전략 A 비중은 혼합 포트폴리오의 33.33%이므로, 공격 시 종목당 8.33%, 방어 시 1종목 33.33%가 됩니다. SMH·LIT·XLE는 전략 C 공격 자산과, GLD는 전략 C 방어 자산과, TBF는 전략 B 방어 자산과 겹칩니다. 같은 종목이 동시에 선택되면 혼합 포트폴리오에서 비중이 합쳐집니다.

## 화면 구성

1. 카나리아 신호: TIP 현재가, 11개월 평균, 신호 비율과 현재 모드
2. 자산 순위표와 최종 포트폴리오 가이드
3. 이번 달 일별 수익률: 직전 월말 확정 포트폴리오의 일간·월초 대비 누적 수익률과 종목별 기여도
4. 백테스트 성과 분석: 시작일 선택(2015-01-01 기본, 2018, 2020), 자산 곡선, 연도별·월별 수익률, 낙폭, 드로다운 Top 10, 폭락 시장 성과, 주요 지표 비교(vs QQQ), 월별 리밸런싱 기록

신호 화면은 실시간 현재가로 계산한 참고값입니다. 실제 매매 판단은 월말 종가로 합니다.

## 백테스트 가정과 한계

- 월말 종가로 신호를 계산하고 같은 종가에 체결했다고 봅니다. 현금 수익률은 0%입니다.
- 슬리피지·세금은 기본 미반영이며 맨 위 설정에서 선택 반영할 수 있습니다. 환전 비용은 반영하지 않았습니다.
- 첫 12개월은 모멘텀 계산용 워밍업이라 성과 기록에서 빠집니다.
- QTUM처럼 상장 기간이 짧은 자산은 데이터가 없는 달에 후보에서 빠집니다.
- 공격 시 순위만으로 4종목을 고르므로, 공격 국면 중 하락장에서는 손실을 그대로 받습니다.
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
            render_html_table(
                df_off_a[["Ticker", "현재가", "1M", "3M", "6M", "12M", "A_공격스코어"]]
                .rename(columns={"A_공격스코어": "모멘텀 스코어"}),
                ticker_cols=("Ticker",)
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
            render_html_table(
                df_def_a[["Ticker", "현재가", "1M", "3M", "6M", "9M", "12M", "A_방어스코어"]]
                .rename(columns={"A_방어스코어": "모멘텀 스코어"}),
                ticker_cols=("Ticker",)
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
        render_intramonth_stop_monitor(hist_prices, spy_divs_hist, strategy="A")

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
                bt_results_a = apply_trading_costs(bt_results_a)
                bt_ok_a = len(bt_results_a) > 0
            except Exception as e:
                st.error(f"전략 A 백테스트 데이터 로딩 중 오류가 발생했습니다: {e}")
                bt_ok_a = False

        if not bt_ok_a:
            st.warning("백테스트 데이터가 부족하거나 오류가 있습니다. 잠시 후 다시 시도해 주세요.")
        else:
            st.caption(f"시뮬레이션 기간: {bt_results_a['date'].iloc[0].strftime('%Y-%m')} ~ {bt_results_a['date'].iloc[-1].strftime('%Y-%m')}")
            cost_status_caption(bt_results_a)

            total_days_a = (bt_results_a["date"].iloc[-1] - bt_results_a["date"].iloc[0]).days
            total_years_a = total_days_a / 365.25 if total_days_a > 0 else 1.0
            final_nav_a = bt_results_a["nav"].iloc[-1]

            cagr_a = ((final_nav_a / 100.0) ** (1 / total_years_a) - 1) * 100
            mdd_a = bt_results_a["drawdown"].min()

            hl_cards([
                ("연환산 복리 수익률 (CAGR)", cagr_a, "연평균 복리 수익률"),
                ("최대 낙폭 (MDD)", f"{mdd_a:.2f}%", "직전 고점 대비 최대 하락", "neg"),
                ("최종 자산 가치 (NAV)", f"{final_nav_a:.1f}", "초기금 100 기준", "neutral"),
            ])

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

            annual_bar_a = alt.Chart(yearly_returns_a).mark_bar().encode(
                x=alt.X("year_str:N", title="연도", sort=year_sort_order_a, scale=alt.Scale(paddingInner=0.5, paddingOuter=0.2)),
                y=alt.Y("annual_return:Q", title="수익률 (%)"),
                color=alt.Color("series:N", scale=color_scale_a, legend=alt.Legend(title=None, orient="bottom")),
                tooltip=[
                    alt.Tooltip("year_str:N", title="연도"),
                    alt.Tooltip("annual_return:Q", title="수익률", format="+.2f"),
                ],
            )
            annual_labels_a = alt.Chart(yearly_returns_a).mark_text(
                dy=alt.expr("datum.annual_return >= 0 ? -8 : 14"), fontWeight="bold", fontSize=10, color="#0f172a"
            ).encode(
                x=alt.X("year_str:N", sort=year_sort_order_a, scale=alt.Scale(paddingInner=0.5, paddingOuter=0.2)),
                y=alt.Y("annual_return:Q"),
                text=alt.Text("annual_return:Q", format=".1f"),
            )
            qqq_points_a = alt.Chart(qqq_yearly_a).mark_point(
                filled=True, size=110, stroke="white", strokeWidth=1.2
            ).encode(
                x=alt.X("year_str:N", sort=year_sort_order_a, scale=alt.Scale(paddingInner=0.5, paddingOuter=0.2)),
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
            monthly_compound_cards(bt_results_a)
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
            render_drawdown_with_benchmark(chart_df_a, "전략A")

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
                st.caption("※ 드로우다운은 시작월 직전 고점부터 종료월(최저점)까지의 하락률입니다.")
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
            render_gl_table(df_metrics_a)
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
        
        with st.expander("📖 전략 B 명세서", expanded=False):
            st.markdown(r"""
## 개요

전략 B는 TIP 모멘텀의 방향으로 국면을 판단해, 3배 레버리지·리츠 또는 인버스 자산 중 1종목에 100% 집중하는 월간 로테이션 전략입니다. 2026 혼합전략에서 33.33%를 맡는 고수익·고변동 축입니다.

| 항목 | 내용 |
| --- | --- |
| 카나리아 | TIP 5구간(1·3·6·9·12개월) 평균 모멘텀 |
| 공격 조건 | TIP 스코어 > 0 |
| 공격 시 | 공격 자산 3개 중 가중 모멘텀 1위 100% |
| 방어 시 | 방어 자산 3개 중 5개월 수익률 1위, 그 자산의 5구간 평균 ≤ 0이면 현금 100% |
| 리밸런싱 | 매월 말 종가 기준 전량 재배분, 월중 매매 없음 |
| 월중 하드스탑 | 사용하지 않음 |

## 자산군

| 구분 | 티커 |
| --- | --- |
| 공격 (3개) | TYD(미국채 3X), UPRO(S&P500 3X), VNQ(리츠) |
| 방어 (3개) | DOG(다우 인버스), RWM(러셀2000 인버스), TBF(미국채 장기 인버스) |

## 운용 규칙

**모멘텀 정의**: R_n = (당월 말 종가 ÷ n개월 전 월말 종가 − 1) × 100.

1. **국면 판단**: 매월 말 TIP 5구간 평균 모멘텀이 0보다 크면 공격, 0 이하면 방어입니다. 5개 구간 중 하나라도 계산되지 않는 달은 건너뜁니다.
2. **공격 스코어**: 공격 자산 3개에 최근 수익률 비중이 큰 가중 모멘텀을 계산합니다. R_12가 있어야 후보가 됩니다.
3. **공격 배분**: 점수 1위에 100%. 컷오프 없음, 후보가 없으면 현금 100%.
4. **방어 선정**: 방어 자산 3개 중 최근 5개월 수익률(R_5)이 가장 높은 자산을 고릅니다.
5. **방어 필터**: 선정 자산의 5구간 평균 모멘텀이 0보다 크면 100% 투자, 아니면 현금 100%.

방어 시 순위(R_5)와 진입 필터(5구간 평균)가 서로 다른 지표라는 점이 전략 A·C와 다릅니다.
""")
            st.latex(r"Canary_B = \frac{R_1 + R_3 + R_6 + R_9 + R_{12}}{5}\,(TIP) \qquad Score_{\text{공격}} = \frac{12R_1 + 4R_3 + 2R_6 + R_{12}}{19}")
            st.markdown(r"""
## 혼합전략 안에서의 역할

전략 B 비중은 혼합 포트폴리오의 33.33%이므로, 선택된 1종목이 전체의 33.33%가 됩니다. TBF는 전략 A 방어 자산과 겹쳐, 두 전략이 함께 방어일 때 TBF 비중이 최대 66.67%까지 커질 수 있습니다. 혼합전략의 비중 상한(기본 35%)은 이런 중복을 제한하는 장치입니다.

## 화면 구성

1. 카나리아 신호: TIP 5구간 모멘텀과 현재 모드
2. 자산 순위표와 최종 포트폴리오 가이드
3. 이번 달 일별 수익률: 직전 월말 확정 포트폴리오의 일간·월초 대비 누적 수익률과 종목별 기여도
4. 백테스트 성과 분석: 시작일 선택(2015-01-01 기본, 2018, 2020), 자산 곡선, 연도별·월별 수익률, 낙폭, 드로다운 Top 10, 폭락 시장 성과, 주요 지표 비교(vs QQQ), 월별 리밸런싱 기록

신호 화면은 실시간 현재가로 계산한 참고값입니다. 실제 매매 판단은 월말 종가로 합니다.

## 백테스트 가정과 한계

- 월말 종가로 신호를 계산하고 같은 종가에 체결했다고 봅니다. 현금 수익률은 0%입니다.
- 슬리피지·세금은 기본 미반영이며 맨 위 설정에서 선택 반영할 수 있습니다. 환전 비용은 반영하지 않았습니다. 1종목 전량 교체가 잦아 비용 영향이 큽니다.
- 3배 레버리지 ETF는 변동성 손실(음의 복리)이 있어, 횡보·급변 구간에서 기초지수 3배보다 성과가 나빠질 수 있습니다.
- 1종목 집중이라 월중 급락을 그대로 받습니다. 개별 전략에는 월중 하드스탑이 없습니다.
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
            render_html_table(
                df_off_b[["Ticker", "현재가", "1M", "3M", "6M", "12M", "B_공격스코어"]]
                .rename(columns={"B_공격스코어": "가중 모멘텀 스코어"}),
                ticker_cols=("Ticker",)
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
            render_html_table(
                df_def_b[["Ticker", "현재가", "5M", "B_단순모멘텀"]]
                .rename(columns={"5M": "5개월 수익률", "B_단순모멘텀": "자체 단순모멘텀"}),
                ticker_cols=("Ticker",)
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
        render_intramonth_stop_monitor(hist_prices, spy_divs_hist, strategy="B")

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
                bt_results_b = apply_trading_costs(bt_results_b)
                bt_ok_b = len(bt_results_b) > 0
            except Exception as e:
                st.error(f"전략 B 백테스트 데이터 로딩 중 오류가 발생했습니다: {e}")
                bt_ok_b = False

        if not bt_ok_b:
            st.warning("백테스트 데이터가 부족하거나 오류가 있습니다. 잠시 후 다시 시도해 주세요.")
        else:
            st.caption(f"시뮬레이션 기간: {bt_results_b['date'].iloc[0].strftime('%Y-%m')} ~ {bt_results_b['date'].iloc[-1].strftime('%Y-%m')}")
            cost_status_caption(bt_results_b)

            total_days_b = (bt_results_b["date"].iloc[-1] - bt_results_b["date"].iloc[0]).days
            total_years_b = total_days_b / 365.25 if total_days_b > 0 else 1.0
            final_nav_b = bt_results_b["nav"].iloc[-1]

            cagr_b = ((final_nav_b / 100.0) ** (1 / total_years_b) - 1) * 100
            mdd_b = bt_results_b["drawdown"].min()

            hl_cards([
                ("연환산 복리 수익률 (CAGR)", cagr_b, "연평균 복리 수익률"),
                ("최대 낙폭 (MDD)", f"{mdd_b:.2f}%", "직전 고점 대비 최대 하락", "neg"),
                ("최종 자산 가치 (NAV)", f"{final_nav_b:.1f}", "초기금 100 기준", "neutral"),
            ])

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

            annual_bar_b = alt.Chart(yearly_returns_b).mark_bar().encode(
                x=alt.X("year_str:N", title="연도", sort=year_sort_order_b, scale=alt.Scale(paddingInner=0.5, paddingOuter=0.2)),
                y=alt.Y("annual_return:Q", title="수익률 (%)"),
                color=alt.Color("series:N", scale=color_scale_b, legend=alt.Legend(title=None, orient="bottom")),
                tooltip=[
                    alt.Tooltip("year_str:N", title="연도"),
                    alt.Tooltip("annual_return:Q", title="수익률", format="+.2f"),
                ],
            )
            annual_labels_b = alt.Chart(yearly_returns_b).mark_text(
                dy=alt.expr("datum.annual_return >= 0 ? -8 : 14"), fontWeight="bold", fontSize=10, color="#0f172a"
            ).encode(
                x=alt.X("year_str:N", sort=year_sort_order_b, scale=alt.Scale(paddingInner=0.5, paddingOuter=0.2)),
                y=alt.Y("annual_return:Q"),
                text=alt.Text("annual_return:Q", format=".1f"),
            )
            qqq_points_b = alt.Chart(qqq_yearly_b).mark_point(
                filled=True, size=110, stroke="white", strokeWidth=1.2
            ).encode(
                x=alt.X("year_str:N", sort=year_sort_order_b, scale=alt.Scale(paddingInner=0.5, paddingOuter=0.2)),
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
            monthly_compound_cards(bt_results_b)
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
            render_drawdown_with_benchmark(chart_df_b, "전략B")

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
                st.caption("※ 드로우다운은 시작월 직전 고점부터 종료월(최저점)까지의 하락률입니다.")
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
            render_gl_table(df_metrics_b)
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
        
        with st.expander("📖 전략 C 명세서", expanded=False):
            st.markdown(r"""
## 개요

전략 C는 S&P 500(SPY) 배당수익률로 주식시장의 저평가·과열을 판단해, 주도 섹터 1개 또는 원자재·채권 1개에 100% 투자하는 월간 섹터 로테이션 전략입니다. 2026 혼합전략에서 33.33%를 맡습니다.

| 항목 | 내용 |
| --- | --- |
| 카나리아 | SPY 최근 365일 배당 합계 ÷ 월말 SPY 종가 |
| 공격 조건 | 배당수익률 > 1.33% (저평가 국면) |
| 공격 시 | 섹터 ETF 7개 중 모멘텀 1위 100% |
| 방어 시 | 원자재·채권 5개 중 모멘텀 1위 100%, 1위 점수 ≤ 0이면 현금 100% |
| 리밸런싱 | 매월 말 종가 기준 전량 재배분, 월중 매매 없음 |
| 월중 하드스탑 | 사용하지 않음 |

## 자산군

| 구분 | 티커 |
| --- | --- |
| 공격 (7개) | FDN, LIT, SMH, XLE, IGV, QQQM, XLU |
| 방어 (5개) | GLD, PDBC, OILK, SHY, TLT |

## 운용 규칙

**모멘텀 정의**: R_n = (당월 말 종가 ÷ n개월 전 월말 종가 − 1) × 100.

1. **국면 판단**: 매월 말 배당수익률이 1.33%를 넘으면 공격, 이하면 방어입니다. 배당 합계가 0이거나 가격이 없는 달은 건너뜁니다.
2. **공격 스코어**: 섹터 ETF 7개에 4구간 평균 모멘텀을 계산합니다. R_12가 있어야 후보가 됩니다.
3. **공격 배분**: 점수 1위 섹터에 100%. 컷오프 없음, 후보가 없으면 현금 100%.
4. **방어 스코어**: 원자재·채권 5개에 5구간 평균 모멘텀을 계산합니다.
5. **방어 배분**: 점수 1위에 100%. 1위 점수가 0 이하면 현금 100%.
""")
            st.latex(r"DY = \frac{\sum Div_{SPY}(\text{최근 365일})}{P_{SPY}(\text{월말})} \times 100 \qquad Score_{\text{공격}} = \frac{R_1 + R_3 + R_6 + R_{12}}{4} \qquad Score_{\text{방어}} = \frac{R_1 + R_3 + R_6 + R_9 + R_{12}}{5}")
            st.markdown(r"""
## 혼합전략 안에서의 역할

전략 C 비중은 혼합 포트폴리오의 33.33%이므로, 선택된 1종목이 전체의 33.33%가 됩니다. SMH·LIT·XLE는 전략 A 공격 자산과, GLD는 전략 A 공격 자산과 겹칩니다. 예를 들어 A가 SMH 25%, C가 SMH 100%를 고르면 혼합 비중은 41.67%가 되며, 혼합전략의 비중 상한(기본 35%)이 켜져 있으면 초과분이 현금이 됩니다.

## 화면 구성

1. 카나리아 신호: 실시간 배당수익률과 현재 모드
2. 자산 순위표와 최종 포트폴리오 가이드
3. 이번 달 일별 수익률: 직전 월말 확정 포트폴리오의 일간·월초 대비 누적 수익률과 종목별 기여도
4. 백테스트 성과 분석: 시작일 선택(2015-01-01 기본, 2018, 2020), 자산 곡선, 연도별·월별 수익률, 낙폭, 드로다운 Top 10, 폭락 시장 성과, 주요 지표 비교(vs QQQ), 월별 리밸런싱 기록

실시간 배당수익률은 최근 배당 이력과 현재가로 따로 계산한 참고값입니다. 실제 매매 판단은 월말 종가로 합니다.

## 백테스트 가정과 한계

- 월말 종가로 신호를 계산하고 같은 종가에 체결했다고 봅니다. 현금 수익률은 0%입니다.
- 슬리피지·세금은 기본 미반영이며 맨 위 설정에서 선택 반영할 수 있습니다. 환전 비용은 반영하지 않았습니다.
- 백테스트는 배당이 반영된 수정주가로 배당수익률을 나눕니다. 과거 배당수익률이 실제보다 높게 계산돼 공격 신호가 더 자주 나올 수 있습니다.
- 1.33% 기준은 고정값입니다. 금리·배당 성향이 바뀌면 기준의 의미도 달라질 수 있습니다.
- QQQM·OILK 등은 상장 기간이 짧아 초기 구간에는 후보에서 빠집니다.
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
            render_html_table(
                df_off_c[["Ticker", "현재가", "1M", "3M", "6M", "12M", "A_공격스코어"]]
                .rename(columns={"A_공격스코어": "모멘텀 스코어"}),
                ticker_cols=("Ticker",)
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
            render_html_table(
                df_def_c[["Ticker", "현재가", "1M", "3M", "6M", "9M", "12M", "A_방어스코어"]]
                .rename(columns={"A_방어스코어": "모멘텀 스코어"}),
                ticker_cols=("Ticker",)
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
        render_intramonth_stop_monitor(hist_prices, spy_divs_hist, strategy="C")

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
                bt_results_c = apply_trading_costs(bt_results_c)
                bt_ok_c = len(bt_results_c) > 0
            except Exception as e:
                st.error(f"전략 C 백테스트 데이터 로딩 중 오류가 발생했습니다: {e}")
                bt_ok_c = False

        if not bt_ok_c:
            st.warning("백테스트 데이터가 부족하거나 오류가 있습니다. 잠시 후 다시 시도해 주세요.")
        else:
            st.caption(f"시뮬레이션 기간: {bt_results_c['date'].iloc[0].strftime('%Y-%m')} ~ {bt_results_c['date'].iloc[-1].strftime('%Y-%m')}")
            cost_status_caption(bt_results_c)

            total_days_c = (bt_results_c["date"].iloc[-1] - bt_results_c["date"].iloc[0]).days
            total_years_c = total_days_c / 365.25 if total_days_c > 0 else 1.0
            final_nav_c = bt_results_c["nav"].iloc[-1]

            cagr_c = ((final_nav_c / 100.0) ** (1 / total_years_c) - 1) * 100
            mdd_c = bt_results_c["drawdown"].min()

            hl_cards([
                ("연환산 복리 수익률 (CAGR)", cagr_c, "연평균 복리 수익률"),
                ("최대 낙폭 (MDD)", f"{mdd_c:.2f}%", "직전 고점 대비 최대 하락", "neg"),
                ("최종 자산 가치 (NAV)", f"{final_nav_c:.1f}", "초기금 100 기준", "neutral"),
            ])

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

            annual_bar_c = alt.Chart(yearly_returns_c).mark_bar().encode(
                x=alt.X("year_str:N", title="연도", sort=year_sort_order_c, scale=alt.Scale(paddingInner=0.5, paddingOuter=0.2)),
                y=alt.Y("annual_return:Q", title="수익률 (%)"),
                color=alt.Color("series:N", scale=color_scale_c, legend=alt.Legend(title=None, orient="bottom")),
                tooltip=[
                    alt.Tooltip("year_str:N", title="연도"),
                    alt.Tooltip("annual_return:Q", title="수익률", format="+.2f"),
                ],
            )
            annual_labels_c = alt.Chart(yearly_returns_c).mark_text(
                dy=alt.expr("datum.annual_return >= 0 ? -8 : 14"), fontWeight="bold", fontSize=10, color="#0f172a"
            ).encode(
                x=alt.X("year_str:N", sort=year_sort_order_c, scale=alt.Scale(paddingInner=0.5, paddingOuter=0.2)),
                y=alt.Y("annual_return:Q"),
                text=alt.Text("annual_return:Q", format=".1f"),
            )
            qqq_points_c = alt.Chart(qqq_yearly_c).mark_point(
                filled=True, size=110, stroke="white", strokeWidth=1.2
            ).encode(
                x=alt.X("year_str:N", sort=year_sort_order_c, scale=alt.Scale(paddingInner=0.5, paddingOuter=0.2)),
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
            monthly_compound_cards(bt_results_c)
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
            render_drawdown_with_benchmark(chart_df_c, "전략C")

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
                st.caption("※ 드로우다운은 시작월 직전 고점부터 종료월(최저점)까지의 하락률입니다.")
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
            render_gl_table(df_metrics_c)
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
        
        st.markdown(f"### 📊 Top 10 Performers ({sort_by} 기준)")
        df_top5 = df_ranking.head(10).copy()
        
        try:
            import altair as alt
            top_chart = alt.Chart(df_top5).mark_bar(cornerRadiusEnd=6).encode(
                x=alt.X(f"{selected_sort_col}:Q", title=sort_by),
                y=alt.Y("티커 (Ticker):N", sort='-x', title="ETF 티커"),
                color=alt.Color("티커 (Ticker):N", scale=alt.Scale(scheme='tableau10'), legend=None),
                tooltip=["티커 (Ticker)", "현재가 ($)", selected_sort_col]
            ).properties(height=340)
            st.altair_chart(top_chart, use_container_width=True)
        except Exception:
            st.bar_chart(df_top5.set_index("티커 (Ticker)")[selected_sort_col])
        
        st.markdown("### 🏆 실시간 모멘텀 순위표")
        _rk = df_ranking.copy()
        _rk.insert(0, "순위", _rk.index)
        render_html_table(_rk, ticker_cols=("티커 (Ticker)",))
        st.caption("※ 티커 옆 괄호는 ETF의 한글 명칭이며, 티커에 마우스를 올리면 간략 설명이 표시됩니다. 점수·수익률 단위는 %입니다.")

    with c_ndx:
        st.header("🏢 실시간 미국 나스닥100 랭킹")
        st.markdown(
            "나스닥100 구성 종목들의 실시간 모멘텀과 수익률을 역동적으로 추적하여 정렬하는 "
            "멀티-팩터 랭킹입니다. 상위 20개만 표시합니다."
        )

        ndx_sort_by = st.radio(
            "🏆 정렬 기준 선택",
            options=["종합 모멘텀 스코어", "1개월 수익률", "3개월 수익률", "6개월 수익률", "12개월 수익률"],
            horizontal=True,
            key="ndx_sort_by_radio"
        )

        _ndx_list, _ndx_src = get_ndx_tickers()
        with st.spinner("나스닥100 구성 종목 데이터를 집계 중..."):
            _ndx_raw = get_all_financial_data_v2(_ndx_list)

        if _ndx_raw is None or _ndx_raw.empty:
            st.warning("나스닥100 종목 데이터를 불러오지 못했습니다. 잠시 후 새로고침해 주세요.")
        else:
            ndx_rows = []
            for _, _r in _ndx_raw.iterrows():
                ndx_rows.append({
                    "티커 (Ticker)": _r["Ticker"],
                    "현재가 ($)": f"${_r['현재가']:.2f}",
                    "종합 모멘텀 스코어": _r["A_공격스코어"],
                    "1개월 수익률 (%)": _r["1M"],
                    "3개월 수익률 (%)": _r["3M"],
                    "6개월 수익률 (%)": _r["6M"],
                    "12개월 수익률 (%)": _r["12M"],
                })
            df_ndx = pd.DataFrame(ndx_rows)
            _ndx_sort_map = {
                "종합 모멘텀 스코어": "종합 모멘텀 스코어",
                "1개월 수익률": "1개월 수익률 (%)",
                "3개월 수익률": "3개월 수익률 (%)",
                "6개월 수익률": "6개월 수익률 (%)",
                "12개월 수익률": "12개월 수익률 (%)",
            }
            _ndx_col = _ndx_sort_map[ndx_sort_by]
            df_ndx = df_ndx.sort_values(by=_ndx_col, ascending=False).reset_index(drop=True)
            df_ndx.index += 1

            st.markdown(f"### 📊 Top 10 Performers ({ndx_sort_by} 기준)")
            df_ndx_top5 = df_ndx.head(10).copy()
            try:
                import altair as alt
                ndx_chart = alt.Chart(df_ndx_top5).mark_bar(cornerRadiusEnd=6).encode(
                    x=alt.X(f"{_ndx_col}:Q", title=ndx_sort_by),
                    y=alt.Y("티커 (Ticker):N", sort='-x', title="종목 티커"),
                    color=alt.Color("티커 (Ticker):N", scale=alt.Scale(scheme='tableau10'), legend=None),
                    tooltip=["티커 (Ticker)", "현재가 ($)", _ndx_col]
                ).properties(height=340)
                st.altair_chart(ndx_chart, use_container_width=True)
            except Exception:
                st.bar_chart(df_ndx_top5.set_index("티커 (Ticker)")[_ndx_col])

            st.markdown("### 🏆 실시간 모멘텀 순위표 (상위 20)")
            _ndx_rk = df_ndx.head(20).copy()
            _ndx_rk.insert(0, "순위", _ndx_rk.index)
            render_html_table(_ndx_rk, ticker_cols=("티커 (Ticker)",))
            st.caption(
                f"※ 나스닥100 구성 종목 {len(_ndx_list)}개 중 데이터가 확보된 {len(df_ndx)}개를 비교해 상위 20개만 표시합니다 "
                "(상장 12개월 미만 종목은 제외). 티커 옆 괄호는 한글 회사명이며, 티커에 마우스를 올리거나(폰은 터치) 간략 설명이 표시됩니다. "
                "점수·수익률 단위는 %이고, 점수 산식은 ETF 랭킹과 같습니다."
                + (" 구성 종목은 하루 한 번 위키피디아 표에서 자동 갱신합니다." if _ndx_src == "auto" else " 구성 종목은 내장 목록(2026-10 기준)을 사용 중입니다.")
            )

    with c_mdd:
        import altair as alt
        st.header("📉 SPY·QQQ 장기 낙폭 (경각심용)")
        st.caption("내 전략은 2015년 이전 백테스트가 어려워, 닷컴버블·금융위기 같은 대형 폭락을 SPY·QQQ로 대신 확인하는 참고 화면입니다. 전략 성과와는 무관하며 일별 종가 기준입니다.")

        _LONG_MODES = {
            "ETF 30년 (배당 포함)": ("1996-01-01", [("SPY", "SPY"), ("QQQ", "QQQ")]),
            "지수 초장기 (대공황 포함 · 배당 제외)": ("1927-12-30", [("S&P500", "^GSPC"), ("나스닥100", "^NDX")]),
        }
        _mode_names = list(_LONG_MODES)
        long_mode = st.radio("데이터 범위", _mode_names, horizontal=True, key="long_mode")
        _mi = _mode_names.index(long_mode)
        _start, _series = _LONG_MODES[long_mode]
        with st.spinner("장기 가격 데이터를 불러오는 중..."):
            _hist = get_long_history(tuple(sym for _, sym in _series), _start)
        long_px = {n: _hist[sym] for n, sym in _series if sym in _hist}

        if not long_px:
            st.warning("장기 가격 데이터를 불러오지 못했습니다. 잠시 후 새로고침해 주세요.")
        else:
            if _mi == 0:
                st.caption("SPY는 1993년, QQQ는 1999년 3월 상장이라 QQQ는 약 27년치입니다. 1929 대공황·1987 블랙먼데이는 ETF가 없어 '지수 초장기'에서 확인하세요.")
            else:
                st.caption("S&P500(1927~)·나스닥100(1985~) 지수의 가격 기준이라 배당이 빠져 ETF보다 낙폭이 조금 더 깊게 나옵니다. 대공황·1987년·오일쇼크를 볼 수 있습니다.")

            # ---- 요약 카드 ----
            _cards_mdd, _cards_cur = [], []
            for n, px in long_px.items():
                dd_s = px / px.cummax() - 1
                t = dd_s.idxmin()
                pk = px.loc[:t].idxmax()
                mdd = float(dd_s.min() * 100)
                _cards_mdd.append((f"{n} 최대 낙폭 (MDD)", f"{mdd:.2f}%",
                                   f"{pk:%Y-%m} → {t:%Y-%m} · 초기 투자금이면 약 {fmt_krw(COST_CAPITAL * abs(mdd) / 100)} 평가손실", "neg"))
                cur = float(dd_s.iloc[-1] * 100)
                _cards_cur.append((f"{n} 현재 낙폭", f"{cur:.2f}%",
                                   f"역대 고점 {px.idxmax():%Y-%m-%d} 대비", "neg" if cur <= -10 else "neutral"))
            hl_cards(_cards_mdd + _cards_cur)

            # ---- 낙폭 히스토리 ----
            st.markdown("##### 📉 낙폭 (Drawdown) 히스토리")
            frames = []
            for n, px in long_px.items():
                d = ((px / px.cummax() - 1) * 100).resample("W").min().dropna()
                frames.append(pd.DataFrame({"date": d.index, "series": n, "drawdown": d.values.round(2)}))
            long_df = pd.concat(frames, ignore_index=True)
            _y_all = list(range(int(long_df["date"].dt.year.min()), int(long_df["date"].dt.year.max()) + 1))
            if len(_y_all) > 2:
                _y0, _y1 = st.select_slider("🔍 표시 구간 (년)", options=_y_all, value=(_y_all[0], _y_all[-1]), key=f"long_zoom_{_mi}")
            else:
                _y0, _y1 = _y_all[0], _y_all[-1]
            view_df = long_df[(long_df["date"].dt.year >= _y0) & (long_df["date"].dt.year <= _y1)]

            _names = list(long_px)
            _palette = ["#2563eb", "#dc2626"][:len(_names)]
            x_enc = alt.X("date:T", title=None, axis=alt.Axis(format="%Y", labelOverlap=True))
            y_enc = alt.Y("drawdown:Q", title="낙폭 (%)")
            color_enc = alt.Color("series:N", scale=alt.Scale(domain=_names, range=_palette), sort=_names,
                                  legend=alt.Legend(orient="top", title=None))
            tip = [alt.Tooltip("date:T", title="주", format="%Y-%m-%d"), alt.Tooltip("series:N", title="구분"),
                   alt.Tooltip("drawdown:Q", title="낙폭 (%)", format=".2f")]
            layers = [alt.Chart(view_df).mark_area(opacity=0.33, line={"strokeWidth": 1.2}).encode(x=x_enc, y=y_enc, color=color_enc, tooltip=tip)]

            ev_rows = []
            for short, full, a, b in LONG_EVENTS:
                for n, px in long_px.items():
                    es = event_stats(px, a, b)
                    if es:
                        ev_rows.append({"date": es["trough"], "label": short})
                        break
            ev_df = pd.DataFrame(ev_rows)
            if len(ev_df):
                ev_df = ev_df[(ev_df["date"].dt.year >= _y0) & (ev_df["date"].dt.year <= _y1)].reset_index(drop=True)
            if len(ev_df):
                layers.append(alt.Chart(ev_df).mark_rule(color="#64748b", strokeDash=[3, 3]).encode(x="date:T"))
                for k in range(3):
                    sub = ev_df[ev_df.index % 3 == k]
                    if len(sub):
                        layers.append(alt.Chart(sub).mark_text(align="left", dx=3, fontSize=10, color="#475569").encode(
                            x="date:T", y=alt.value(10 + 12 * k), text="label:N"))
            st.altair_chart(alt.layer(*layers).properties(height=270), use_container_width=True)
            _rng_txt = " · ".join(f"{n} {view_df[view_df['series'] == n]['drawdown'].min():.1f}%" for n in _names if (view_df['series'] == n).any())
            st.caption(f"점선 = 주요 이슈의 저점 시기. 선택 구간 최대 낙폭: {_rng_txt} (주간 기준 표시, 계산은 일별 종가)")

            # ---- 드로우다운 Top 10 ----
            st.markdown("##### 🚨 포트폴리오 드로우다운 Top 10")
            _pick = st.radio("자산", _names, horizontal=True, key=f"long_top10_{_mi}") if len(_names) > 1 else _names[0]
            eps = sorted(dd_episodes(long_px[_pick]), key=lambda e: e["depth"])[:10]
            top_rows = []
            for i, e in enumerate(eps, 1):
                issue = next((short for short, full, a, b in LONG_EVENTS
                              if pd.Timestamp(a) <= e["trough"] <= pd.Timestamp(b)), "-")
                top_rows.append({
                    "순위": i, "고점일": f"{e['peak']:%Y-%m-%d}", "저점일": f"{e['trough']:%Y-%m-%d}",
                    "최대 낙폭": f"{e['depth']:.1f}%", "하락 기간": _fmt_dur((e["trough"] - e["peak"]).days),
                    "전고점 회복": (f"{_fmt_dur((e['recovery'] - e['trough']).days)} 후" if e["recovery"] is not None else "미회복"),
                    "주요 이슈": issue,
                })
            if top_rows:
                st.dataframe(pd.DataFrame(top_rows), use_container_width=True, hide_index=True)
                st.caption("※ 고점 → 저점 → 전고점 회복까지를 한 구간으로 봅니다. 전고점을 오래 못 넘은 기간 안의 별도 폭락(예: 닷컴 회복 중 금융위기)도 각각 독립 구간으로 집계합니다. '전고점 회복'은 저점에서 그 구간의 고점을 다시 넘기까지 걸린 시간입니다.")

            # ---- 폭락 시장 성과 ----
            st.markdown("##### 🔻 폭락 시장 성과 (대형 이슈별)")
            crash_rows = []
            for short, full, a, b in LONG_EVENTS:
                for n, px in long_px.items():
                    es = event_stats(px, a, b)
                    if not es:
                        continue
                    crash_rows.append({
                        "이슈": full, "자산": n, "고점일": f"{es['peak']:%Y-%m-%d}", "저점일": f"{es['trough']:%Y-%m-%d}",
                        "최대 낙폭": f"{es['depth']:.1f}%", "고점→저점": _fmt_dur((es["trough"] - es["peak"]).days),
                        "전고점 회복": (f"{_fmt_dur((es['recovery'] - es['trough']).days)} 후 ({es['recovery']:%Y-%m})"
                                      if es["recovery"] is not None else "미회복"),
                        "저점 후 1년": (f"{es['rebound']:+.0f}%" if es["rebound"] is not None else "-"),
                    })
            if crash_rows:
                st.dataframe(pd.DataFrame(crash_rows), use_container_width=True, hide_index=True)
                st.caption("※ 낙폭은 각 이슈 기간 안의 고점→저점 기준이라, 전체 기간의 최대 낙폭(역대 고점 기준)과 다를 수 있습니다. 데이터가 없는 시기는 표시하지 않습니다.")
            else:
                st.info("표시할 폭락 구간 데이터가 없습니다.")

    with c_calc:
        st.header("🧮 복리의 마법 & 미래 계산기")
        st.markdown(
            "자산배분 백테스트의 실제 연평균 수익률(CAGR)을 기반으로, 매월 적립식 저축 및 정기 생활비 지출이 유발하는 "
            "미래 자산의 실제 성장 경로를 정밀하게 예측합니다. **세율 적용**, **생활비 지출 설정**, 및 **물가상승률 할인**까지 연산하는 실전형 자산 시뮬레이터입니다."
        )

        _cost_on = bool(COST_SLIP_ON or COST_TAX_ON)
        _preset_cagr = get_preset_cagrs(PRESET_START, _cost_cfg() if _cost_on else None)

        def _pv(k):
            v = _preset_cagr.get(k)
            return float(v) if v is not None else float(PRESET_FALLBACK_CAGR[k])

        if "cagr_input" not in st.session_state:
            st.session_state.cagr_input = 25.0  # 계산기 초기값 (퀵 프리셋 버튼으로 전략별 실측값 선택 가능)

        # 상단 설정이 바뀌면, 직전에 눌러 둔 프리셋 값(직접 고치지 않은 경우)을 새 값으로 갱신
        _sel = st.session_state.get("_preset_sel")
        if _sel and abs(st.session_state.cagr_input - st.session_state.get("_preset_val", -999.0)) < 0.005 \
                and abs(_pv(_sel) - st.session_state["_preset_val"]) >= 0.005:
            st.session_state.cagr_input = _pv(_sel)
            st.session_state["_preset_val"] = _pv(_sel)

        def _apply_preset(k):
            st.session_state.cagr_input = _pv(k)
            st.session_state["_preset_sel"] = k
            st.session_state["_preset_val"] = _pv(k)

        st.markdown("##### ⚡ 자산배분 전략 실측 CAGR 퀵 프리셋")
        col_pre1, col_pre2, col_pre3, col_pre4 = st.columns(4)
        col_pre1.button(f"🏆 2026 혼합 ({_pv('mix'):.2f}%)", key="preset_btn_mix", on_click=_apply_preset, args=("mix",))
        col_pre2.button(f"🛡️ 전략 A ({_pv('A'):.2f}%)", key="preset_btn_A", on_click=_apply_preset, args=("A",))
        col_pre3.button(f"⚡ 전략 B ({_pv('B'):.2f}%)", key="preset_btn_B", on_click=_apply_preset, args=("B",))
        col_pre4.button(f"🔄 전략 C ({_pv('C'):.2f}%)", key="preset_btn_C", on_click=_apply_preset, args=("C",))
        if all(_preset_cagr.get(k) is not None for k in ["mix", "A", "B", "C"]):
            st.caption(f"※ 각 전략 탭의 초기 설정(백테스트 시작일 {PRESET_START}, 안전장치 미적용) 기준 실측 CAGR이며, 전략 탭의 '연환산 복리 수익률(CAGR)'과 같은 값입니다.")
            if _cost_on:
                _bits = []
                if COST_SLIP_ON:
                    _bits.append(f"슬리피지 {COST_SLIP_PCT:g}%/회")
                if COST_TAX_ON:
                    _bits.append(f"양도세 {COST_TAX_PCT:g}% (연 공제 {fmt_krw(COST_DEDUCT)})")
                st.caption(f"💸 상단 '백테스트 비용·세금 반영 설정'이 적용된 값입니다 · " + " · ".join(_bits) + f" · 초기 투자금 {fmt_krw(COST_CAPITAL)}")
        else:
            st.caption("※ 일부 전략의 실측 CAGR을 불러오지 못해 기존 참고값을 표시 중입니다. 잠시 후 새로고침해 주세요.")

        st.markdown("---")
        if st.session_state.get("_calc_init_sync") != COST_CAPITAL:  # 상단 '초기 투자금'이 바뀌면 계산기에도 반영
            st.session_state["calc_init_input"] = int(round(COST_CAPITAL / 10000))
            st.session_state["_calc_init_sync"] = COST_CAPITAL
        _TAX_DONE = "양도세 반영 완료 (0.0% · 프리셋 CAGR에 포함)"
        if st.session_state.get("_calc_tax_prev") != COST_TAX_ON:  # 양도세 반영을 켜면 이중 과세 방지로 세율 0% 선택
            st.session_state["calc_tax_sel"] = _TAX_DONE if COST_TAX_ON else "미국주식양도세 (22.0%)"
            st.session_state["_calc_tax_prev"] = COST_TAX_ON
        col_inp1, col_inp2 = st.columns(2)
        with col_inp1:
            calc_init = st.number_input("초기 투자금 (만원 ₩)", min_value=0, step=100, key="calc_init_input",
                                        help="상단 '백테스트 비용·세금 반영 설정'의 초기 투자금과 연동됩니다. 여기서 직접 바꿀 수도 있습니다.")
            calc_monthly = st.number_input("매월 저축/적립금 (만원 ₩)", min_value=0, value=0, step=10)
            calc_expense = st.number_input("매월 지출/생활비 (만원 ₩)", min_value=0, value=0, step=10, help="투자수익에서 정기 지출하는 생활비가 있다면 마이너스로 처리됩니다.")
            calc_years = st.slider("시뮬레이션 투자 기간 (년)", min_value=1, max_value=40, value=20)
        with col_inp2:
            calc_cagr = st.number_input("연 목표 수익률 CAGR (%)", min_value=0.0, max_value=100.0, key="cagr_input", step=0.1, format="%.2f")
            calc_inflation = st.number_input("연 예상 물가상승률 (%)", min_value=0.0, max_value=20.0, value=3.0, step=0.1)
            calc_expense_start = st.number_input("지출 시작 시점 (년차)", min_value=1, max_value=max(1, calc_years), value=1, step=1, help="생활비 지출을 몇 년차부터 적용할지 연차를 지정합니다.")
            calc_tax_opt = st.selectbox("세율 설정", ["일반과세 (15.4%)", "미국주식양도세 (22.0%)", "비과세 계좌 (0.0% / ISA 및 연금저축)", "사용자 정의", _TAX_DONE], key="calc_tax_sel")
        
        if calc_tax_opt == "일반과세 (15.4%)":
            tax_rate = 15.4
        elif calc_tax_opt == "미국주식양도세 (22.0%)":
            tax_rate = 22.0
        elif calc_tax_opt in ("비과세 계좌 (0.0% / ISA 및 연금저축)", _TAX_DONE):
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
        
        _hdr = "".join(f"<th>{c}</th>" for c in df_display.columns)
        _body = ""
        _last = len(df_display) - 1
        for _ri, (_, _row) in enumerate(df_display.iterrows()):
            _cls = ' class="last"' if _ri == _last else ""
            _body += f"<tr{_cls}>" + "".join(f"<td>{v}</td>" for v in _row.values) + "</tr>"
        st.markdown(
            "<style>"
            ".growth-tbl{width:100%;border-collapse:collapse;font-size:0.9rem;margin-bottom:0.5rem}"
            ".growth-tbl th{background:#e2e8f0;color:#334155;padding:8px 6px;text-align:center;border:1px solid #cbd5e1;word-break:keep-all}"
            ".growth-tbl td{padding:7px 6px;text-align:right;border:1px solid #e2e8f0;white-space:nowrap}"
            ".growth-tbl td:first-child{text-align:center}"
            ".growth-tbl tr:nth-child(even) td{background:#f8fafc}"
            ".growth-tbl tr.last td{background:#e8f1fa;font-weight:700}"
            "@media (max-width:640px){.growth-tbl{font-size:0.62rem}.growth-tbl th{font-size:0.6rem}.growth-tbl th,.growth-tbl td{padding:5px 2px}}"
            "</style>"
            f'<table class="growth-tbl"><thead><tr>{_hdr}</tr></thead><tbody>{_body}</tbody></table>',
            unsafe_allow_html=True,
        )
