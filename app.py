import streamlit as st
import pandas as pd
from pathlib import Path
import urllib.request
import json

# ── 데이터 로드 ───────────────────────────────────────────────────────────────
DATA_FILE = Path(__file__).parent / "merged_sales.xlsx"

st.title("매출 대시보드")

if not DATA_FILE.exists():
    st.error(
        f"데이터 파일을 찾을 수 없습니다: `{DATA_FILE.name}`\n\n"
        "같은 폴더에 `merged_sales.xlsx`가 있는지 확인해 주세요."
    )
    st.stop()

df = pd.read_excel(DATA_FILE)
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
