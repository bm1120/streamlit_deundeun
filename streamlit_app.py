import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 데이터 로드
@st.cache_data
def load_data():
    return pd.read_csv('data/final.csv').copy().sort_values('번호')

final = load_data()

# 사이드바 컨트롤
st.sidebar.title('필터 옵션')

max_deposit = st.sidebar.number_input(
    "최대 보증금(만원)", 
    value=30000,
    step=1000
)

max_time = st.sidebar.number_input(
    "최대 통근시간(분)", 
    value=90,
    step=5
)

color_column = st.sidebar.selectbox(
    "건물 표시색상",
    options=['deposit', 'distanceM_near_station', '신청자수', 'deposit_m2'],
    format_func=lambda x: {
        'deposit': '보증금',
        'distanceM_near_station': '인접역까지 거리',
        '신청자수': '신청자수',
        'deposit_m2': 'm2당 보증금'
    }[x]
)

map_style = st.sidebar.radio(
    "지도 스타일",
    options=['open-street-map', 'carto-positron', 'carto-darkmatter', 'stamen-terrain']
)

# 메인 레이아웃
col1, col2 = st.columns([6, 4])

with col1:
    st.title('지도')
    
    # 데이터 필터링
    filtered_data = final[
        (final['deposit'] <= max_deposit) & 
        (final['expected_time'] <= max_time)
    ]
    
    # 지도 생성
    fig = go.Figure()
    
    fig.add_trace(go.Scattermapbox(
        lat=filtered_data.x,
        lon=filtered_data.y,
        mode='markers+text',
        marker=dict(
            size=20,
            color=filtered_data[color_column],
            colorscale='Viridis_r',
            showscale=True
        ),
        text=filtered_data['번호'].astype(str),
        hovertext=filtered_data.apply(
            lambda row: (
                f"<b>번호: {row['번호']}</b><br>"
                f"주소: {row['주소']}<br><br>"
                f"가장 가까운 역: {row['near_station']}"
            ), axis=1
        ),
        hoverinfo='text'
    ))
    
    fig.update_layout(
        mapbox=dict(
            style=map_style,
            zoom=9,
            center=dict(lat=filtered_data.x.mean(), lon=filtered_data.y.mean())
        ),
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        height=700
    )
    
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.title('평면구조도')
    
    # 선택된 마커 정보 표시
    selected_point = st.session_state.get('selected_point', None)
    if selected_point:
        row = final[final['번호'] == selected_point].iloc[0]
        
        # 이미지 표시
        image_url = f"이미지URL_{row['번호']:03d}"  # 실제 이미지 URL로 수정 필요
        if image_url:
            st.image(image_url)
        
        # 상세 정보 표시
        st.write(f"번호: {row['번호']}")
        st.write(f"주소: {row['주소']}")
        st.write(f"주택유형: {row['주택유형']}")
        st.write(f"전용면적: {round(row['m2'] / 3.30579, 1)}평")
        st.write(f"보증금: {int(row['deposit'])}만원")
        st.write(f"가장 가까운 역까지 거리: {row['near_station']}까지 {int(row['distanceM_near_station'])}m")
        st.write(f"회사까지 예상 소요 시간: {round(row['expected_time'], 1)}분")
        st.write(f"신청자수: {row['신청자수']}명")
        st.markdown(f"[로드뷰 보기](https://map.kakao.com/link/roadview/{row['x']},{row['y']})")