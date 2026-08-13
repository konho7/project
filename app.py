import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

# ────────────────────────────────
# 기본 설정
# ────────────────────────────────
st.set_page_config(page_title="골목상권 임대료 경직성 분석", layout="wide")
plt.rcParams["font.family"] = "Malgun Gothic"   # Mac이면 'AppleGothic'으로 변경
plt.rcParams["axes.unicode_minus"] = False

quarters_order = ["2024.3/4", "2024.4/4", "2025.1/4", "2025.2/4",
                   "2025.3/4", "2025.4/4", "2026.1/4"]
start_q, end_q = quarters_order[0], quarters_order[-1]


# ────────────────────────────────
# 데이터 불러오기 및 전처리
# ────────────────────────────────
@st.cache_data
def load_data():
    df1 = pd.read_csv("상권별_공실률.csv", encoding="cp949")
    df2 = pd.read_csv("상권별_순영업소득.csv", encoding="cp949")
    df3 = pd.read_csv("상권별_임대료.csv", encoding="cp949")

    df2 = df2[df2["항목"] == "순영업소득 (천원/㎡)"]

    def clean(df, 값이름):
        df = df[(df["상권별(1)"] == "서울") & (df["상권별(3)"] != "소계")]
        df = df.rename(columns={"상권별(3)": "상권명"})
        df = df[["상권명"] + quarters_order]
        return df.melt(id_vars="상권명", var_name="분기", value_name=값이름)

    df1_long = clean(df1, "공실률")
    df2_long = clean(df2, "순영업소득")
    df3_long = clean(df3, "임대료")

    final = pd.merge(df1_long, df2_long, on=["상권명", "분기"], how="left")
    final = pd.merge(final, df3_long, on=["상권명", "분기"], how="left")

    pivot_vac = final.pivot(index="상권명", columns="분기", values="공실률")
    pivot_rent = final.pivot(index="상권명", columns="분기", values="임대료")
    pivot_noi = final.pivot(index="상권명", columns="분기", values="순영업소득")

    변화 = pd.DataFrame({
        "공실률_변화": pivot_vac[end_q] - pivot_vac[start_q],
        "임대료_변화율": (pivot_rent[end_q] - pivot_rent[start_q]) / pivot_rent[start_q] * 100,
        "NOI_변화율": (pivot_noi[end_q] - pivot_noi[start_q]) / pivot_noi[start_q] * 100,
    }).reset_index()

    역설상권 = 변화[
        (변화["공실률_변화"] > 0) &
        (변화["임대료_변화율"].abs() < 1) &
        (변화["NOI_변화율"] > 0)
    ].sort_values("공실률_변화", ascending=False)

    변화["그룹"] = 변화["상권명"].apply(lambda x: "역설군" if x in 역설상권["상권명"].values else "일반군")

    return final, 변화, 역설상권


final, 변화, 역설상권 = load_data()
역설_리스트 = 역설상권["상권명"].tolist()


# ────────────────────────────────
# 사이드바
# ────────────────────────────────
st.sidebar.header("상권 조회")

선택_상권 = st.sidebar.selectbox(
    "상권을 선택하세요",
    options=sorted(final["상권명"].unique()),
    index=sorted(final["상권명"].unique()).index("독산/시흥") if "독산/시흥" in final["상권명"].unique() else 0
)

st.sidebar.markdown("---")
st.sidebar.caption("데이터 출처: 한국부동산원 상업용부동산 임대동향조사")
st.sidebar.caption(f"분석 기간: {start_q} ~ {end_q}")


# ────────────────────────────────
# 타이틀
# ────────────────────────────────
st.title("공실은 늘어도 임대료는 그대로다")
st.caption("서울 59개 상권 공실률-임대료 경직성 분석")


# ────────────────────────────────
# KPI 지표
# ────────────────────────────────
공실증가_수 = (변화["공실률_변화"] > 0).sum()
경직_수 = 변화[(변화["공실률_변화"] > 0) & (변화["임대료_변화율"] >= -1)].shape[0]

col1, col2, col3, col4 = st.columns(4)
col1.metric("분석 대상 상권", "59개")
col2.metric("공실률 증가 상권", f"{공실증가_수}개")
col3.metric("공실 늘어도 임대료 안 내림", f"{경직_수}개")
col4.metric("역설 상권 (공실↑ 임대료 그대로 NOI↑)", f"{len(역설상권)}개")


# ────────────────────────────────
# 선택 상권 개별 추이
# ────────────────────────────────
st.subheader(f"[{선택_상권}] 지표 추이")

if 선택_상권 in 역설_리스트:
    st.warning(f"{선택_상권}은(는) 역설 상권 8개에 해당합니다 — 공실 증가에도 임대료를 유지하며 순소득이 늘었습니다.")

상권_data = final[final["상권명"] == 선택_상권].set_index("분기").reindex(quarters_order)

fig1, axes1 = plt.subplots(1, 3, figsize=(14, 3.5))

axes1[0].plot(quarters_order, 상권_data["공실률"], color="firebrick", marker="o")
axes1[0].set_title("공실률 (%)")
axes1[0].tick_params(axis="x", rotation=45)

axes1[1].plot(quarters_order, 상권_data["임대료"], color="firebrick", marker="o")
axes1[1].set_title("임대료")
axes1[1].tick_params(axis="x", rotation=45)

axes1[2].plot(quarters_order, 상권_data["순영업소득"], color="firebrick", marker="o")
axes1[2].set_title("임대인 순소득 (NOI)")
axes1[2].tick_params(axis="x", rotation=45)

for ax in axes1:
    ax.grid(axis="y", linestyle=":", alpha=0.5)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

plt.tight_layout()
st.pyplot(fig1)


# ────────────────────────────────
# 전체 핵심 분석
# ────────────────────────────────
st.subheader("전체 상권 핵심 분석")

공실률_추이 = final.groupby("분기")["공실률"].mean().reindex(quarters_order)

공실증가 = 변화[변화["공실률_변화"] > 0].copy()
공실증가["임대료_하락여부"] = ["하락" if x < -1 else "하락하지 않음" for x in 공실증가["임대료_변화율"]]
n_하락 = (공실증가["임대료_하락여부"] == "하락").sum()
n_안하락 = (공실증가["임대료_하락여부"] == "하락하지 않음").sum()

임대료유지 = 변화[변화["임대료_변화율"].abs() < 1].copy()
임대료유지["공실_방향"] = ["공실 증가" if x > 0 else "공실 감소·유지" for x in 임대료유지["공실률_변화"]]
noi_공실별 = 임대료유지.groupby("공실_방향")["NOI_변화율"].mean()

fig2, axes2 = plt.subplots(1, 3, figsize=(14, 4))

axes2[0].plot(quarters_order, 공실률_추이.values, color="#2C3E50", marker="o", linewidth=2)
axes2[0].set_title("1. 서울시 전체 상권 평균 공실률", loc="left", fontweight="bold")
axes2[0].set_ylabel("평균 공실률 (%)")
axes2[0].tick_params(axis="x", rotation=45)

bars = axes2[1].bar(
    [f"임대료 하락\n({n_하락}개)", f"하락하지 않음\n({n_안하락}개)"],
    [n_하락, n_안하락], color=["lightgray", "firebrick"], width=0.4
)
axes2[1].set_title("2. 공실 증가 상권의 임대료 반응", loc="left", fontweight="bold")
axes2[1].set_ylabel("상권 수 (개)")
axes2[1].yaxis.set_major_locator(MaxNLocator(integer=True))
axes2[1].bar_label(bars, fmt="%d개", padding=3, fontweight="bold")

axes2[2].bar(noi_공실별.index, noi_공실별.values, color=["lightgray", "firebrick"], width=0.5)
axes2[2].axhline(0, color="#333333", linewidth=1.0)
axes2[2].set_title("3. 임대료 그대로인 상권, 공실 증감별 순소득", loc="left", fontweight="bold")
axes2[2].set_ylabel("임대인 순소득 변화율 (%)")
for i, v in enumerate(noi_공실별.values):
    axes2[2].text(i, v + 1.5, f"{v:+.1f}%", ha="center", fontweight="bold")

for ax in axes2:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

plt.tight_layout()
st.pyplot(fig2)


# ────────────────────────────────
# 역설 상권 목록
# ────────────────────────────────
st.subheader("역설 상권 8개 상세")
st.dataframe(
    역설상권[["상권명", "공실률_변화", "임대료_변화율", "NOI_변화율"]]
    .rename(columns={
        "공실률_변화": "공실률 변화(%p)",
        "임대료_변화율": "임대료 변화율(%)",
        "NOI_변화율": "순소득 변화율(%)"
    })
    .set_index("상권명")
    .style.format("{:.2f}"),
    use_container_width=True
)