import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import koreanize_matplotlib

st.title("HR 퇴직현황 대시보드")

# 1. 데이터 불러오기
df = pd.read_csv("HR Data.csv")

# 2. KPI 3개
total_employees = len(df)
total_attritions = len(df[df["퇴직여부"].isin(["Yes", "퇴직", "Y"])])
overall_rate = (total_attritions / total_employees * 100) if total_employees > 0 else 0

col1, col2, col3 = st.columns(3)

col1.metric(label="전체 직원 수", value=f"{total_employees:,}명")
col2.metric(label="퇴직자 수", value=f"{total_attritions:,}명")
col3.metric(label="전체 퇴직률", value=f"{overall_rate:.1f}%")

st.markdown("---")

# 3. 그래프 2개
# 그래프 1 : 부서별 퇴직자 수
st.subheader("부서별 퇴직자 수")
fig1, ax1 = plt.subplots(figsize=(7, 3))
attrition_df = df[df["퇴직여부"].isin(["Yes", "퇴직", "Y"])]
sns.countplot(data=attrition_df, x="부서", ax=ax1)
ax1.set_xlabel("부서")
ax1.set_ylabel("퇴직자 수(명)")
st.pyplot(fig1)

# 그래프 2 : 출장빈도별 퇴직자 수 (또는 기타 한글 컬럼)
st.subheader("출장빈도별 퇴직자 수")
fig2, ax2 = plt.subplots(figsize=(7, 3))
sns.countplot(data=df, x="출장빈도", hue="퇴직여부", ax=ax2)
ax2.set_xlabel("출장빈도")
ax2.set_ylabel("인원수(명)")
st.pyplot(fig2)