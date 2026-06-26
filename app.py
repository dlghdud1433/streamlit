import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import urllib.request
import json

# ── 데이터 로드 (파일 없으면 더미 생성) ──────────────────────────────────────
DATA_FILE = Path(__file__).parent / "merged_sales.xlsx"

def make_dummy() -> pd.DataFrame:
    rng = np.random.default_rng(7)
    products_a = ["노트북", "스마트폰", "태블릿", "이어폰", "충전기", "마우스", "키보드"]
    products_b = ["갤럭시탭", "아이패드", "에어팟", "맥북", "모니터", "웹캠", "스피커"]
    dates_a = pd.date_range("2024-03-01", "2024-05-31")
    dates_b = pd.date_range("2024-04-01", "2024-06-30")
    rows = [
        {"날짜": dates_a[i], "지점": "A",
         "상품": products_a[rng.integers(len(products_a))],
         "금액": int(rng.integers(15_000, 850_000))}
        for i in rng.integers(len(dates_a), size=20)
    ] + [
        {"날짜": dates_b[i], "지점": "B",
         "상품": products_b[rng.integers(len(products_b))],
         "금액": int(rng.integers(20_000, 1_200_000))}
        for i in rng.integers(len(dates_b), size=20)
    ]
    return pd.DataFrame(rows).sort_values("날짜").reset_index(drop=True)

if DATA_FILE.exists():
    df = pd.read_excel(DATA_FILE)
else:
    df = make_dummy()

df["날짜"] = pd.to_datetime(df["날짜"])
df["금액"] = df["금액"].astype(int)

# ── 사이드바 필터 ─────────────────────────────────────────────────────────────
branches = sorted(df["지점"].unique().tolist())

with st.sidebar:
    st.header("필터")

    date_min = df["날짜"].min().date()
    date_max = df["날짜"].max().date()
    date_range = st.date_input(
        "날짜 범위",
        value=(date_min, date_max),
        min_value=date_min,
        max_value=date_max,
    )

    selected = st.multiselect(
        "지점 선택",
        options=branches,
        default=branches,
    )

# date_input이 단일 날짜만 선택된 경우 방어
if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date = end_date = date_range[0] if date_range else date_min

filtered = df[
    (df["날짜"].dt.date >= start_date)
    & (df["날짜"].dt.date <= end_date)
    & (df["지점"].isin(selected) if selected else False)
]

# ── 레이아웃 ──────────────────────────────────────────────────────────────────
total = filtered["금액"].sum()
st.metric(label="전체 매출 합계", value=f"₩ {total:,}")

st.divider()

# ── 월별 매출 추이 선그래프 ───────────────────────────────────────────────────
st.subheader("월별 매출 추이")

monthly = (
    filtered.assign(월=filtered["날짜"].dt.to_period("M").astype(str))
    .groupby(["월", "지점"])["금액"]
    .sum()
    .reset_index()
    .pivot(index="월", columns="지점", values="금액")
    .fillna(0)
    .sort_index()
)

st.line_chart(monthly)

# ── 상품별 매출 표 ────────────────────────────────────────────────────────────
st.subheader("상품별 매출")

product_sales = (
    filtered.groupby("상품")["금액"]
    .agg(판매건수="count", 매출합계="sum")
    .sort_values("매출합계", ascending=False)
    .reset_index()
)
product_sales["매출합계"] = product_sales["매출합계"].map(lambda x: f"₩ {x:,}")

st.dataframe(product_sales, use_container_width=True, hide_index=True)

st.divider()

# ── 서울 날씨 (Open-Meteo) ────────────────────────────────────────────────────
st.subheader("서울 오늘 날씨")

@st.cache_data(ttl=600)
def fetch_weather():
    url = (
        "https://api.open-meteo.com/v1/forecast"
        "?latitude=37.5665&longitude=126.9780"
        "&current=temperature_2m,weathercode"
        "&hourly=temperature_2m"
        "&timezone=Asia%2FSeoul"
        "&forecast_days=1"
    )
    with urllib.request.urlopen(url, timeout=8) as res:
        return json.loads(res.read())

try:
    data = fetch_weather()

    current_temp = data["current"]["temperature_2m"]
    current_time = data["current"]["time"].replace("T", " ")
    st.metric(label=f"현재 기온 ({current_time} 기준)", value=f"{current_temp} °C")

    hourly_df = pd.DataFrame({
        "시각": pd.to_datetime(data["hourly"]["time"]).strftime("%H:%M"),
        "기온 (°C)": data["hourly"]["temperature_2m"],
    }).set_index("시각")

    st.line_chart(hourly_df)

except Exception as e:
    st.warning(f"날씨 데이터를 불러오지 못했습니다. ({e})")
