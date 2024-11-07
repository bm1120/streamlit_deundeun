import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from streamlit_plotly_events import plotly_events
import requests
import numpy as np

kakao_api_key = st.secrets["api_keys"]["kakao"]

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
    
    # 회사 위치 설정
    st.header("회사 위치 설정")
    
    # 회사 주소 입력
    company_address = st.text_input(
        "회사 주소",
        value="서울특별시 강남구 테헤란로 427"  # 기본값 설정
    )
    
    # 주소 -> 좌표 변환 함수
    @st.cache_data
    def get_coordinates(address):
        url = f"https://dapi.kakao.com/v2/local/search/address.json"
        headers = {"Authorization": f"KakaoAK {kakao_api_key}"}
        params = {"query": address}
        
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            result = response.json()
            if result["documents"]:
                x = float(result["documents"][0]["y"])  # 위도
                y = float(result["documents"][0]["x"])  # 경도
                return x, y
        return None, None
    
    # 좌표 계산
    company_x, company_y = get_coordinates(company_address)
    
    if company_x and company_y:
        st.success("회사 위치가 확인되었습니다.")
        
        # 대중교통 시간 계산 함수
        @st.cache_data
        def calculate_transit_time(origin_x, origin_y, dest_x, dest_y):
            url = "https://apis-navi.kakaomobility.com/v1/directions"
            headers = {"Authorization": f"KakaoAK {kakao_api_key}"}
            params = {
                "origin": f"{origin_y},{origin_x}",
                "destination": f"{dest_y},{dest_x}",
                "priority": "TIME",
                "car_fuel": "GASOLINE",
                "car_hipass": False,
                "alternatives": False,
                "road_details": False
            }
            
            try:
                response = requests.get(url, headers=headers, params=params)
                if response.status_code == 200:
                    result = response.json()
                    # 이동 시간을 분 단위로 반환
                    return result['routes'][0]['summary']['duration'] / 60
                return None
            except:
                return None

        # 모든 건물에 대해 새로운 예상 시간 계산
        @st.cache_data
        def update_transit_times(df, comp_x, comp_y):
            df = df.copy()
            df['expected_time'] = df.apply(
                lambda row: calculate_transit_time(
                    comp_x, comp_y, 
                    row['x'], row['y']
                ), axis=1
            )
            return df
        
        # 데이터 업데이트
        final = update_transit_times(final, company_x, company_y)
        
        # 회사 위치 지도에 표시
        fig.add_trace(go.Scattermapbox(
            lat=[company_x],
            lon=[company_y],
            mode='markers+text',
            marker=dict(
                size=25,
                symbol='star',
                color='red'
            ),
            text=['회사'],
            name='회사 위치'
        ))
        
    else:
        st.error("회사 주소를 확인할 수 없습니다. 정확한 주소를 입력해주세요.")

# 메인 레이아웃
col1, col2 = st.columns([6, 4])

with col1:
    st.subheader("지도")
    
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
        height=700
    )
    
    # plotly_chart 대신 plotly_events 사용
    selected_point = plotly_events(fig, click_event=True, override_height=700)

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
