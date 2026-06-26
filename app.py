import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="2026 북중미 월드컵", page_icon="⚽", layout="wide")

# ── 팀 & 강도 데이터 ──────────────────────────────────────────────────────────
GROUPS = {
    "A": ["미국", "잉글랜드", "이란", "세네갈"],
    "B": ["캐나다", "독일", "모로코", "세르비아"],
    "C": ["멕시코", "스페인", "일본", "폴란드"],
    "D": ["아르헨티나", "프랑스", "호주", "에콰도르"],
    "E": ["브라질", "콜롬비아", "나이지리아", "크로아티아"],
    "F": ["네덜란드", "한국", "포르투갈", "스위스"],
    "G": ["벨기에", "덴마크", "카메룬", "코스타리카"],
    "H": ["이탈리아", "우루과이", "사우디아라비아", "튀니지"],
    "I": ["카타르", "튀르키예", "이집트", "자메이카"],
    "J": ["칠레", "웨일스", "알제리", "뉴질랜드"],
    "K": ["페루", "체코", "코트디부아르", "파나마"],
    "L": ["베네수엘라", "오스트리아", "가나", "온두라스"],
}

STRENGTH = {
    "미국": 7, "잉글랜드": 8, "이란": 5, "세네갈": 6,
    "캐나다": 6, "독일": 8, "모로코": 7, "세르비아": 6,
    "멕시코": 7, "스페인": 9, "일본": 7, "폴란드": 6,
    "아르헨티나": 10, "프랑스": 9, "호주": 5, "에콰도르": 6,
    "브라질": 9, "콜롬비아": 7, "나이지리아": 6, "크로아티아": 7,
    "네덜란드": 8, "한국": 7, "포르투갈": 8, "스위스": 7,
    "벨기에": 7, "덴마크": 7, "카메룬": 5, "코스타리카": 5,
    "이탈리아": 8, "우루과이": 7, "사우디아라비아": 5, "튀니지": 5,
    "카타르": 5, "튀르키예": 6, "이집트": 6, "자메이카": 4,
    "칠레": 6, "웨일스": 6, "알제리": 6, "뉴질랜드": 4,
    "페루": 6, "체코": 6, "코트디부아르": 6, "파나마": 4,
    "베네수엘라": 6, "오스트리아": 7, "가나": 5, "온두라스": 4,
}

# ── 경기 결과 시뮬레이션 ──────────────────────────────────────────────────────
@st.cache_data
def build_matches() -> pd.DataFrame:
    rng = np.random.default_rng(42)
    dates = pd.date_range("2026-06-11", periods=3, freq="4D")
    rows = []
    for group, teams in GROUPS.items():
        pairs = [(teams[i], teams[j])
                 for i in range(len(teams)) for j in range(i + 1, len(teams))]
        for idx, (home, away) in enumerate(pairs):
            lam_h = max(0.3, STRENGTH[home] / 5 + rng.normal(0, 0.4))
            lam_a = max(0.3, STRENGTH[away] / 5 + rng.normal(0, 0.4))
            gh, ga = int(rng.poisson(lam_h)), int(rng.poisson(lam_a))
            rows.append({
                "조": group,
                "경기일": dates[idx // 2],
                "홈팀": home, "홈득점": gh,
                "원정팀": away, "원정득점": ga,
            })
    return pd.DataFrame(rows)


def standings(df: pd.DataFrame, group: str) -> pd.DataFrame:
    gdf = df[df["조"] == group]
    result = []
    for team in GROUPS[group]:
        h = gdf[gdf["홈팀"] == team]
        a = gdf[gdf["원정팀"] == team]
        gf = int(h["홈득점"].sum() + a["원정득점"].sum())
        ga = int(h["원정득점"].sum() + a["홈득점"].sum())
        w = int((h["홈득점"] > h["원정득점"]).sum() +
                (a["원정득점"] > a["홈득점"]).sum())
        d = int((h["홈득점"] == h["원정득점"]).sum() +
                (a["원정득점"] == a["홈득점"]).sum())
        l = int((h["홈득점"] < h["원정득점"]).sum() +
                (a["원정득점"] < a["홈득점"]).sum())
        result.append({"팀": team, "경기": w+d+l, "승": w, "무": d, "패": l,
                       "득점": gf, "실점": ga, "득실차": gf-ga, "승점": w*3+d})
    return (pd.DataFrame(result)
            .sort_values(["승점", "득실차", "득점"], ascending=False)
            .reset_index(drop=True))


# ── 레이아웃 ──────────────────────────────────────────────────────────────────
df = build_matches()

st.title("⚽ 2026 북중미 월드컵 — 조별리그 대시보드")
st.caption("시뮬레이션 데이터 기반 · 실제 결과와 다를 수 있습니다")

# 사이드바 조 선택
with st.sidebar:
    st.header("조 선택")
    sel = st.radio("조", list(GROUPS.keys()), format_func=lambda x: f"{x}조")

# 상단 요약 지표
total_goals = int(df["홈득점"].sum() + df["원정득점"].sum())
total_matches = len(df)
c1, c2, c3 = st.columns(3)
c1.metric("총 경기 수", f"{total_matches}경기")
c2.metric("총 득점", f"{total_goals}골")
c3.metric("경기당 평균 골", f"{total_goals / total_matches:.2f}")

st.divider()

# 조별 순위표
st.subheader(f"{sel}조 순위")

tb = standings(df, sel)

def row_color(row):
    if row.name < 2:
        return ["background-color:#d4edda"] * len(row)   # 16강 직행
    if row.name == 2:
        return ["background-color:#fff3cd"] * len(row)   # 와일드카드 경쟁
    return [""] * len(row)

st.dataframe(tb.style.apply(row_color, axis=1), use_container_width=True, hide_index=True)
st.caption("🟢 16강 직행 (1·2위)　🟡 와일드카드 경쟁 (3위)")

st.divider()

# 경기 결과
st.subheader(f"{sel}조 경기 결과")

match_view = (
    df[df["조"] == sel]
    .assign(경기일=lambda d: d["경기일"].dt.strftime("%m/%d"),
            결과=lambda d: d["홈득점"].astype(str) + " : " + d["원정득점"].astype(str))
    [["경기일", "홈팀", "결과", "원정팀"]]
    .sort_values("경기일")
    .reset_index(drop=True)
)
st.dataframe(match_view, use_container_width=True, hide_index=True)

st.divider()

# 조별 총 득점 비교
st.subheader("조별 총 득점 비교")

goals_by_group = (
    df.groupby("조")
    .apply(lambda g: int(g["홈득점"].sum() + g["원정득점"].sum()), include_groups=False)
    .rename("총득점")
    .reset_index()
    .set_index("조")
)
st.bar_chart(goals_by_group)
