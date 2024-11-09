import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from streamlit_plotly_events import plotly_events

# 페이지 설정
st.set_page_config(
    page_title="든든전세주택 대시보드",
    layout="wide"
)

# 데이터 로드
@st.cache_data
def load_data():
    return pd.read_csv('data/final.csv').copy().sort_values('번호')

final = load_data()

# 세션 스테이트 초기화
if 'selected_number' not in st.session_state:
    st.session_state.selected_number = None

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
            'deposit', 'distanceM_near_station', 
            '신청자수', 'deposit_m2'
        ],
        format_func=lambda x: {
            'deposit': '보증금',
            'distanceM_near_station': '인접역까지 거리',
            '신청자수': '신청자수',
            'deposit_m2': 'm2당 보증금'
        }[x],
        index=3
    )
    
    map_style = st.radio(
        "지도 스타일",
        options=['open-street-map', 'carto-positron', 
                'carto-darkmatter', 'stamen-terrain']
    )

# 메인 레이아웃 비율 조정
col1, col2 = st.columns([7, 3], gap="small")

with col1:
    st.subheader("지도")
    
    # 데이터 필터링
    filtered_data = final[
        (final['deposit'] <= max_deposit) & 
        (final['expected_time'] <= max_time)
    ]
    
    # 지도 생성
    fig = go.Figure()
    
    # 건물 마커 추가
    fig.add_trace(go.Scattermapbox(
        lat=filtered_data.x,
        lon=filtered_data.y,
        mode='markers+text',
        marker=go.scattermapbox.Marker(
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
    
    # 지도 레이아웃 설정
    fig.update_layout(
        mapbox=dict(
            style=map_style,
            zoom=9,
            center=dict(
                lat=filtered_data.x.mean(), 
                lon=filtered_data.y.mean()
            )
        ),
        margin={"r":0,"t":0,"l":0,"b":0},
        height=400,
        width=1000,
        autosize=False
    )
    
    # plotly_events 설정
    selected_point = plotly_events(
        fig, 
        click_event=True,
        override_width="100%"
    )

with col2:
    st.subheader("평면구조도")
    
    # 클릭된 포인트가 있으면 해당 정보 표시
    if selected_point:
        # 클릭된 포인트의 인덱스로 데이터 접근
        point_idx = selected_point[0]['pointIndex']
        selected_row = filtered_data.iloc[point_idx]
        
        # 이미지 표시
        image_urls = {f'{num:03d}': img_url 
                     for idx, num, img_url in final.filter(regex='번호|img').itertuples()}
        if image_url := image_urls.get(f'{int(selected_row["번호"]):03d}'):
            st.image(image_url)
        
        # 건물 상세 정보
        st.write(f"번호: {selected_row['번호']}")
        st.write(f"주소: {selected_row['주소']}")
        st.write(f"주택유형: {selected_row['주택유형']}")
        st.write(f"전용면적: {round(selected_row['m2'] / 3.30579, 1)}평")
        st.write(f"보증금: {int(selected_row['deposit'])}만원")
        st.write(f"가장 가까운 역까지 거리: {selected_row['near_station']}까지 {int(selected_row['distanceM_near_station'])}m")
        st.write(f"회사까지 예상 소요 시간: {round(selected_row['expected_time'], 1)}분")
        st.write(f"신청자수: {selected_row['신청자수']}명")
        st.markdown(f"[로드뷰 보기](https://map.kakao.com/link/roadview/{selected_row['x']},{selected_row['y']})")
    else:
        st.write("지도에서 건물을 선택해주세요.")
