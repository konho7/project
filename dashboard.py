import pandas as pd

# 1.데이터 불러오기

df1=pd.read_csv("상권별_공실률.csv", encoding="cp949")
df2=pd.read_csv("상권별_순영업소득.csv", encoding="cp949")
df3=pd.read_csv("상권별_임대료.csv", encoding="cp949")

# 2.데이터 전처리

# df2 파일에서 "항목"란에 불필요한 임대수입,기타수입,운영경비 제거 순영업소득만 남기기

df2_slim = df2[df2["항목"] == "순영업소득 (천원/㎡)"]
 
# <df1,2,3> 상권별(1)에서 서울만 남기고 (전국 제외), 상권별(3)이 "소계"가 아닌 개별 상권만 남기기

df2_slim = df2_slim[
    (df2_slim["상권별(1)"] == "서울") &
    (df2_slim["상권별(3)"] != "소계")
]  
df1_slim = df1[
    (df1["상권별(1)"] == "서울") &
    (df1["상권별(3)"] != "소계")
]
df3_slim = df3[
    (df3["상권별(1)"] == "서울") &
    (df3["상권별(3)"] != "소계")
]

# merge를 위해 컬럼명 통일 (상권별(1)=서울 (2)=넓은권역 (3)=개별상권)
df1_slim = df1_slim.rename(columns={"상권별(3)": "상권명"})
df2_slim = df2_slim.rename(columns={"상권별(3)": "상권명"})
df3_slim = df3_slim.rename(columns={"상권별(3)": "상권명"})

# 필요없는 컬럼 정리

df1_final = df1_slim[["상권명", "2024.3/4", "2024.4/4", "2025.1/4", "2025.2/4", "2025.3/4", "2025.4/4", "2026.1/4"]]
df2_final = df2_slim[["상권명", "2024.3/4", "2024.4/4", "2025.1/4", "2025.2/4", "2025.3/4", "2025.4/4", "2026.1/4"]]
df3_final = df3_slim[["상권명", "2024.3/4", "2024.4/4", "2025.1/4", "2025.2/4", "2025.3/4", "2025.4/4", "2026.1/4"]]

# print(df1_final)

# Wide → Long 변환 (melt)
df1_long = df1_final.melt(id_vars="상권명", var_name="분기", value_name="공실률")
df2_long = df2_final.melt(id_vars="상권명", var_name="분기", value_name="순영업소득")
df3_long = df3_final.melt(id_vars="상권명", var_name="분기", value_name="임대료")


# merge (상권명+분기기준)
final = pd.merge(df1_long, df2_long, on=["상권명","분기"] ,how="left")
final = pd.merge(final, df3_long, on=["상권명","분기"], how="left")


#print(final.shape)  # 413행, 컬럼은 상권명·분기·공실률·순영업소득·임대료 5개
#final.head(5)
final.isnull().sum()

print("======================")

# 3.데이터 분석

# 3-1. 공실률 추이
quarters_order = ["2024.3/4","2024.4/4","2025.1/4","2025.2/4","2025.3/4","2025.4/4","2026.1/4"]

공실률_추이 = final.groupby("분기")["공실률"].mean().reindex(quarters_order)
print(공실률_추이)

# 3. 소수점 출력 정리 (신규)
pd.set_option('display.float_format', '{:.2f}'.format)

# 4. 핵심 분석: 상권별 기간 내 변화량 계산 
quarters_order = ["2024.3/4","2024.4/4","2025.1/4","2025.2/4","2025.3/4","2025.4/4","2026.1/4"]
start_q = "2024.3/4"
end_q = "2026.1/4"

pivot_vac = final.pivot(index="상권명", columns="분기", values="공실률")
pivot_rent = final.pivot(index="상권명", columns="분기", values="임대료")
pivot_noi = final.pivot(index="상권명", columns="분기", values="순영업소득")

변화 = pd.DataFrame({
    "공실률_변화": pivot_vac[end_q] - pivot_vac[start_q],
    "임대료_변화율": (pivot_rent[end_q] - pivot_rent[start_q]) / pivot_rent[start_q] * 100,
    "NOI_변화율": (pivot_noi[end_q] - pivot_noi[start_q]) / pivot_noi[start_q] * 100,
}).reset_index()

# 5. 역설 상권 식별
역설상권 = 변화[
    (변화["공실률_변화"] > 0) &
    (변화["임대료_변화율"].abs() < 1) &
    (변화["NOI_변화율"] > 0)
].sort_values("공실률_변화", ascending=False)

print(f"역설 상권 개수: {len(역설상권)}")
print(역설상권)

# ── 핵심 분석 3가지 ──

# ① 전체 공실률 추이 — 공실률이 상승중
공실률_추이 = final.groupby("분기")["공실률"].mean().reindex(quarters_order).round(2)
print("① 전체 평균 공실률 추이")
print(공실률_추이)

# ② 공실률 변화 vs 임대료 변화 상관관계 — 임대료가 안내려감
corr = 변화["공실률_변화"].corr(변화["임대료_변화율"])
print(f"\n② 공실률-임대료 변화 상관계수: {corr:.3f}")

# ③ 역설군(8) vs 일반군(51) NOI 비교 — "왜 안 내려가는가"
역설_리스트 = 역설상권["상권명"].tolist()
변화["그룹"] = 변화["상권명"].apply(lambda x: "역설군" if x in 역설_리스트 else "일반군")
noi_비교 = 변화.groupby("그룹")["NOI_변화율"].mean().round(2)
print("\n③ 그룹별 평균 NOI 변화율")
print(noi_비교)

print("final")