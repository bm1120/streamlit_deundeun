import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import branca.colormap as cm

# 페이지 설정
st.set_page_config(
    page_title="든든전세주택 대시보드",
    layout="wide"
)

# 데이터 로드
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('data/final.csv').copy().sort_values('번호')
        print("\n=== 데이터 로딩 정보 ===")
        print(f"데이터 크기: {df.shape}")
        print("\n=== 데이터 컬럼 목록 ===")
        print(df.columns.tolist())
        print("\n=== 데이터 샘플 ===")
        print(df[['번호', '주소', 'deposit', 'expected_time']].head())
        return df
    except Exception as e:
        print(f"\n=== 데이터 로딩 에러 ===")
        print(f"에러 메시지: {str(e)}")
        st.error(f"데이터 로딩 중 오류가 발생했습니다: {str(e)}")
        return pd.DataFrame()  # 빈 데이터프레임 반환

final = load_data()

# 데이터가 비어있는지 확인
if final.empty:
    st.error("데이터를 불러올 수 없습니다. 'data/final.csv' 파일이 올바른 위치에 있는지 확인해주세요.")
    st.stop()

# 사이드바 컨트롤
with st.sidebar:
    st.header("필터 설정")
    
    max_deposit = st.number_input(
        "최대 보증금(만원)", 
        value=30000,
        step=1000
    )
    
    max_time = st.number_input(
        "최대 통근시간(분)", 
        value=90,
        step=5
    )
    
    color_column = st.selectbox(
        "건물 표시색상",
        options=[
            'deposit', '신청자수', 'deposit_m2'
        ],
        format_func=lambda x: {
            'deposit': '보증금',
            '신청자수': '신청자수',
            'deposit_m2': 'm2당 보증금'
        }[x],
        index=2
    )
    
    map_style = st.selectbox(
        "지도 스타일",
        options=['OpenStreetMap', 'Stamen Terrain', 'Stamen Toner', 'CartoDB positron', 'CartoDB dark_matter'],
        index=0
    )

# 전체 화면에 지도 표시
st.subheader("든든전세주택 위치 지도")

# 데이터 필터링
filtered_data = final[
    (final['deposit'] <= max_deposit) & 
    (final['expected_time'] <= max_time)
]

# 디버깅을 위한 데이터 출력
print("\n=== 필터링된 데이터 정보 ===")
print(f"전체 데이터 수: {len(final)}")
print(f"필터링된 데이터 수: {len(filtered_data)}")
print("\n=== 필터링된 데이터 샘플 ===")
print(filtered_data[['번호', '주소', 'deposit', 'expected_time']].head())
print("\n=== 필터링 조건 ===")
print(f"최대 보증금: {max_deposit}만원")
print(f"최대 통근시간: {max_time}분")

if filtered_data.empty:
    st.warning("필터링 조건에 맞는 데이터가 없습니다. 필터 설정을 조정해주세요.")
else:
    # 필터링된 건물 수 표시
    st.info(f"조건에 맞는 건물: {len(filtered_data)}개")
    
    # 지도 중심점 계산
    lat_center = (filtered_data.x.max() + filtered_data.x.min()) / 2
    lon_center = (filtered_data.y.max() + filtered_data.y.min()) / 2
    
    # 색상 스케일 생성
    if color_column in filtered_data.columns:
        min_val = filtered_data[color_column].min()
        max_val = filtered_data[color_column].max()
        
        # 색상맵 생성 (낮은 값은 파란색, 높은 값은 빨간색)
        colormap = cm.LinearColormap(
            colors=['blue', 'green', 'yellow', 'red'],
            vmin=min_val,
            vmax=max_val
        )
    
    # 지도 생성
    m = folium.Map(
        location=[lat_center, lon_center],
        zoom_start=11,
        tiles=map_style
    )
    
    # 마커 및 색상 범례 추가
    if color_column in filtered_data.columns:
        colormap.caption = {
            'deposit': '보증금 (만원)',
            '신청자수': '신청자수 (명)',
            'deposit_m2': 'm2당 보증금'
        }[color_column]
        colormap.add_to(m)
    
    # 마커 추가
    for idx, row in filtered_data.iterrows():
        # 색상 결정
        if color_column in row and min_val != max_val:
            color_val = row[color_column]
            marker_color = colormap(color_val)
        else:
            marker_color = 'blue'
        
        # 팝업 내용 만들기 - 상세 정보 모두 포함
        popup_html = f"""
        <div style='width:300px; max-height:250px; overflow-y:auto;'>
            <h4 style='margin-top:0; margin-bottom:10px;'>건물 상세 정보</h4>
            <table style='width:100%; border-collapse:collapse;'>
                <tr><td style='width:120px;'><b>번호:</b></td><td>{row['번호']}</td></tr>
                <tr><td style='width:120px;'><b>주소:</b></td><td>{row['주소']}</td></tr>
                <tr><td style='width:120px;'><b>주택유형:</b></td><td>{row['주택유형']}</td></tr>
                <tr><td style='width:120px;'><b>전용면적:</b></td><td>{round(row['m2'] / 3.30579, 1)}평</td></tr>
                <tr><td style='width:120px;'><b>보증금:</b></td><td>{int(row['deposit'])}만원</td></tr>
                <tr><td style='width:120px;'><b>m2당 보증금:</b></td><td>{int(row['deposit_m2'])}만원</td></tr>
                <tr><td style='width:120px;'><b>예상통근시간:</b></td><td>{round(row['expected_time'], 1)}분</td></tr>
                <tr><td style='width:120px;'><b>신청자수:</b></td><td>{row['신청자수']}명</td></tr>
            </table>
            <div style='margin-top:10px;'>
                <a href='https://map.kakao.com/link/roadview/{row['x']},{row['y']}' target='_blank'>
                    카카오맵 로드뷰 보기
                </a>
            </div>
        </div>
        """
        popup = folium.Popup(popup_html, max_width=300)
        
        # 마커 추가
        folium.CircleMarker(
            location=[row['x'], row['y']],
            radius=8,
            popup=popup,
            tooltip=f"번호: {row['번호']} | 보증금: {int(row['deposit'])}만원",
            color='black',
            fill=True,
            fill_color=marker_color,
            fill_opacity=0.7,
            weight=1
        ).add_to(m)
    
    # 지도 표시
    st_folium(m, width="100%", height=700, returned_objects=[])