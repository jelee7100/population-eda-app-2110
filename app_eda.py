import streamlit as st
import pyrebase
import time
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ---------------------
# Firebase 설정
# ---------------------
firebase_config = {
    "apiKey": "AIzaSyCswFmrOGU3FyLYxwbNPTp7hvQxLfTPIZw",
    "authDomain": "sw-projects-49798.firebaseapp.com",
    "databaseURL": "https://sw-projects-49798-default-rtdb.firebaseio.com",
    "projectId": "sw-projects-49798",
    "storageBucket": "sw-projects-49798.firebasestorage.app",
    "messagingSenderId": "812186368395",
    "appId": "1:812186368395:web:be2f7291ce54396209d78e"
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
firestore = firebase.database()
storage = firebase.storage()

# ---------------------
# 세션 상태 초기화
# ---------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.id_token = ""
    st.session_state.user_name = ""
    st.session_state.user_gender = "선택 안함"
    st.session_state.user_phone = ""
    st.session_state.profile_image_url = ""

# ---------------------
# 홈 페이지 클래스
# ---------------------
class Home:
    def __init__(self, login_page, register_page, findpw_page):
        st.title("🏠 Home")
        if st.session_state.get("logged_in"):
            st.success(f"{st.session_state.get('user_email')}님 환영합니다.")

        # 데이터셋 출처 및 소개 (population_trends.csv로 수정)
        st.markdown("""
                ---
                **Population Trends 데이터셋**  
                - 제공처: 사용자 업로드 데이터  
                - 설명: 2008–2023년 대한민국 전국 및 지역별 인구, 출생아수, 사망자수를 기록한 데이터  
                - 주요 변수:  
                  - `연도`: 연도 (2008~2023)  
                  - `지역`: 전국 및 17개 지역 (서울, 부산, 세종 등)  
                  - `인구`: 해당 연도의 인구수  
                  - `출생아수(명)`: 연간 출생아수  
                  - `사망자수(명)`: 연간 사망자수  
                """)
        
# ---------------------
# 로그인 페이지 클래스
# ---------------------
class Login:
    def __init__(self):
        st.title("🔐 로그인")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.id_token = user['idToken']

                user_info = firestore.child("users").child(email.replace(".", "_")).get().val()
                if user_info:
                    st.session_state.user_name = user_info.get("name", "")
                    st.session_state.user_gender = user_info.get("gender", "선택 안함")
                    st.session_state.user_phone = user_info.get("phone", "")
                    st.session_state.profile_image_url = user_info.get("profile_image_url", "")

                st.success("로그인 성공!")
                time.sleep(1)
                st.rerun()
            except Exception:
                st.error("로그인 실패")

# ---------------------
# 회원가입 페이지 클래스
# ---------------------
class Register:
    def __init__(self, login_page_url):
        st.title("📝 회원가입")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        name = st.text_input("성명")
        gender = st.selectbox("성별", ["선택 안함", "남성", "여성"])
        phone = st.text_input("휴대전화번호")

        if st.button("회원가입"):
            try:
                auth.create_user_with_email_and_password(email, password)
                firestore.child("users").child(email.replace(".", "_")).set({
                    "email": email,
                    "name": name,
                    "gender": gender,
                    "phone": phone,
                    "role": "user",
                    "profile_image_url": ""
                })
                st.success("회원가입 성공! 로그인 페이지로 이동합니다.")
                time.sleep(1)
                st.switch_page(login_page_url)
            except Exception:
                st.error("회원가입 실패")

# ---------------------
# 비밀번호 찾기 페이지 클래스
# ---------------------
class FindPassword:
    def __init__(self):
        st.title("🔎 비밀번호 찾기")
        email = st.text_input("이메일")
        if st.button("비밀번호 재설정 메일 전송"):
            try:
                auth.send_password_reset_email(email)
                st.success("비밀번호 재설정 이메일을 전송했습니다.")
                time.sleep(1)
                st.rerun()
            except:
                st.error("이메일 전송 실패")

# ---------------------
# 사용자 정보 수정 페이지 클래스
# ---------------------
class UserInfo:
    def __init__(self):
        st.title("👤 사용자 정보")

        email = st.session_state.get("user_email", "")
        new_email = st.text_input("이메일", value=email)
        name = st.text_input("성명", value=st.session_state.get("user_name", ""))
        gender = st.selectbox(
            "성별",
            ["선택 안함", "남성", "여성"],
            index=["선택 안함", "남성", "여성"].index(st.session_state.get("user_gender", "선택 안함"))
        )
        phone = st.text_input("휴대전화번호", value=st.session_state.get("user_phone", ""))

        uploaded_file = st.file_uploader("프로필 이미지 업로드", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            file_path = f"profiles/{email.replace('.', '_')}.jpg"
            storage.child(file_path).put(uploaded_file, st.session_state.id_token)
            image_url = storage.child(file_path).get_url(st.session_state.id_token)
            st.session_state.profile_image_url = image_url
            st.image(image_url, width=150)
        elif st.session_state.get("profile_image_url"):
            st.image(st.session_state.profile_image_url, width=150)

        if st.button("수정"):
            st.session_state.user_email = new_email
            st.session_state.user_name = name
            st.session_state.user_gender = gender
            st.session_state.user_phone = phone

            firestore.child("users").child(new_email.replace(".", "_")).update({
                "email": new_email,
                "name": name,
                "gender": gender,
                "phone": phone,
                "profile_image_url": st.session_state.get("profile_image_url", "")
            })

            st.success("사용자 정보가 저장되었습니다.")
            time.sleep(1)
            st.rerun()

# ---------------------
# 로그아웃 페이지 클래스
# ---------------------
class Logout:
    def __init__(self):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.session_state.id_token = ""
        st.session_state.user_name = ""
        st.session_state.user_gender = "선택 안함"
        st.session_state.user_phone = ""
        st.session_state.profile_image_url = ""
        st.success("로그아웃 되었습니다.")
        time.sleep(1)
        st.rerun()

# ---------------------
# EDA 페이지 클래스
# ---------------------
class EDA:
    def __init__(self):
        st.title("📊 Population Trends EDA")
        uploaded = st.file_uploader("population_trends.csv 파일을 업로드하세요", type="csv")
        if not uploaded:
            st.info("population_trends.csv 파일을 업로드 해주세요.")
            return

        # Read and preprocess data
        df = pd.read_csv(uploaded)
        df.loc[df['지역'] == '세종', ['인구', '출생아수(명)', '사망자수(명)']] = df.loc[df['지역'] == '세종', ['인구', '출생아수(명)', '사망자수(명)']].replace('-', 0)
        df['인구'] = pd.to_numeric(df['인구'], errors='coerce')
        df['출생아수(명)'] = pd.to_numeric(df['출생아수(명)'], errors='coerce')
        df['사망자수(명)'] = pd.to_numeric(df['사망자수(명)'], errors='coerce')

        # Map Korean region names to English for visualizations
        region_mapping = {
            '서울': 'Seoul', '부산': 'Busan', '대구': 'Daegu', '인천': 'Incheon',
            '광주': 'Gwangju', '대전': 'Daejeon', '울산': 'Ulsan', '세종': 'Sejong',
            '경기': 'Gyeonggi', '강원': 'Gangwon', '충북': 'Chungbuk', '충남': 'Chungnam',
            '전북': 'Jeonbuk', '전남': 'Jeonnam', '경북': 'Gyeongbuk', '경남': 'Gyeongnam',
            '제주': 'Jeju'
        }
        df['Region'] = df['지역'].map(region_mapping)

        tabs = st.tabs(["기초 통계", "연도별 추이", "지역별 분석", "변화량 분석", "시각화"])

        # 1. 기초 통계
        with tabs[0]:
            st.header("기초 통계")
            st.subheader("1) 데이터 구조 (`df.info()`)")
            buffer = io.StringIO()
            df.info(buf=buffer)
            st.text(buffer.getvalue())

            st.subheader("2) 기초 통계량 (`df.describe()`)")
            st.dataframe(df.describe(), use_container_width=True)

            st.subheader("3) 데이터셋 설명")
            st.markdown(f"""
            - **population_trends.csv**: 2008–2023년 대한민국 전국 및 지역별 인구, 출생, 사망 기록  
            - 총 관측치: {df.shape[0]}개  
            - 주요 변수:
              - **연도**: 연도 (2008~2023)  
              - **지역**: 전국 및 17개 지역 (서울, 부산, 세종 등)  
              - **인구**: 해당 연도의 인구수  
              - **출생아수(명)**: 연간 출생아수  
              - **사망자수(명)**: 연간 사망자수
            - **전처리**: 세종 지역의 결측치('-')는 0으로 치환, 인구 및 출생/사망 열은 숫자형으로 변환
            """)

        # 2. 연도별 추이
        with tabs[1]:
            st.header("연도별 추이")
            df_national = df[df['지역'] == '전국'][['연도', '인구', '출생아수(명)', '사망자수(명)']].copy()
            df_recent = df_national[df_national['연도'].isin([2021, 2022, 2023])]
            df_recent['net_change'] = df_recent['출생아수(명)'] - df_recent['사망자수(명)']
            X = df_recent['연도'].values.reshape(-1, 1)
            y = df_recent['net_change'].values
            model = LinearRegression()
            model.fit(X, y)
            future_years = np.arange(2024, 2036).reshape(-1, 1)
            predicted_net_change = model.predict(future_years)
            last_population = df_national[df_national['연도'] == 2023]['인구'].values[0]
            predicted_population = last_population
            for change in predicted_net_change:
                predicted_population += change
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.plot(df_national['연도'], df_national['인구'], marker='o', label='Historical Population')
            ax.scatter(2035, predicted_population, color='red', s=100, label='Predicted Population (2035)')
            ax.set_title('Population Trend')
            ax.set_xlabel('Year')
            ax.set_ylabel('Population')
            ax.grid(True)
            ax.legend()
            st.pyplot(fig)
            st.write(f"2035년 예측 인구: {int(predicted_population):,}")
            st.markdown("""
            **해석**:
            - 전국 인구는 2019년에 약 5,184만 명으로 정점을 찍은 후 감소 추세입니다.
            - 출생률 감소와 사망률 증가로 인해 2035년 인구는 약 {int(predicted_population):,} 명으로 예측됩니다.
            - 선형 회귀 모델은 최근 3년(2021~2023)의 자연 인구 변화(출생-사망)를 기반으로 예측했습니다.
            """)

        # 3. 지역별 분석
        with tabs[2]:
            st.header("지역별 분석")
            df_regions = df[df['지역'] != '전국']
            df_last_5_years = df_regions[df_regions['연도'].isin([2019, 2023])][['연도', '지역', '인구', 'Region']]
            df_pivot = df_last_5_years.pivot(index='지역', columns='연도', values='인구').reset_index()
            df_pivot['change'] = (df_pivot[2023] - df_pivot[2019]) / 1000
            df_pivot['percent_change'] = ((df_pivot[2023] - df_pivot[2019]) / df_pivot[2019]) * 100
            df_pivot['Region'] = df_pivot['지역'].map(region_mapping)
            df_pivot = df_pivot.sort_values(by='change', ascending=False)
            sns.set_style("whitegrid")
            plt.figure(figsize=(10, 8))
            ax1 = sns.barplot(x='change', y='Region', data=df_pivot, palette='viridis')
            ax1.set_title('Population Change (2019-2023)')
            ax1.set_xlabel('Population Change (Thousands)')
            ax1.set_ylabel('Region')
            for index, value in enumerate(df_pivot['change']):
                ax1.text(value, index, f'{value:.1f}', va='center', ha='left' if value >= 0 else 'right', color='black')
            st.pyplot(plt)
            plt.clf()
            df_pivot = df_pivot.sort_values(by='percent_change', ascending=False)
            plt.figure(figsize=(10, 8))
            ax2 = sns.barplot(x='percent_change', y='Region', data=df_pivot, palette='magma')
            ax2.set_title('Population Percentage Change (2019-2023)')
            ax2.set_xlabel('Percentage Change (%)')
            ax2.set_ylabel('Region')
            for index, value in enumerate(df_pivot['percent_change']):
                ax2.text(value, index, f'{value:.1f}%', va='center', ha='left' if value >= 0 else 'right', color='black')
            st.pyplot(plt)
            st.markdown("""
            **해석**:
            - **인구 변화량(천명)**: 경기와 세종은 도시화와 신도시 개발로 큰 인구 증가를 보였으며, 서울과 부산은 교외로의 이동과 낮은 출생률로 감소했습니다.
            - **변화율(%)**: 세종은 낮은 초기 인구로 인해 높은 증가율을 기록했고, 전북과 광주는 고령화와 지역 이탈로 큰 감소율을 보였습니다.
            - 지역별 인구 변화는 지역 계획 및 자원 배분에 중요한 시사점을 제공합니다.
            """)

        # 4. 변화량 분석
        with tabs[3]:
            st.header("변화량 분석")
            df_regions = df[df['지역'] != '전국'][['연도', '지역', '인구']]
            df_pivot = df_regions.pivot(index='연도', columns='지역', values='인구')
            df_diff = df_pivot.diff().reset_index()
            df_melt = df_diff.melt(id_vars=['연도'], var_name='지역', value_name='인구_증감')
            df_melt = df_melt.dropna().sort_values(by='인구_증감', ascending=False).head(100)
            df_melt['인구_증감_표시'] = df_melt['인구_증감'].apply(lambda x: f"{x:,.0f}")
            def color_gradient(val):
                if pd.isna(val):
                    return ''
                val = float(val.replace(',', '')) if isinstance(val, str) else val
                if val > 0:
                    intensity = min(val / df_melt['인구_증감'].max(), 1)
                    r, g, b = 0, 0, int(255 * intensity)
                else:
                    intensity = min(abs(val) / abs(df_melt['인구_증감'].min()), 1)
                    r, g, b = int(255 * intensity), 0, 0
                return f'background-color: rgb({r},{g},{b})'
            styled_df = df_melt[['연도', '지역', '인구_증감_표시']].style.applymap(
                color_gradient, subset=['인구_증감_표시']
            ).set_caption("연도별 인구 증감 상위 100개 사례")
            st.dataframe(styled_df, use_container_width=True)
            st.markdown("""
            **해석**:
            - 연도별 인구 증감 상위 100개 사례를 표시하며, 양수는 파랑 계열, 음수는 빨강 계열로 강조됩니다.
            - 경기 지역은 대규모 인구 증가 사례가 많고, 서울은 감소 사례가 두드러집니다.
            - 이는 도시화와 교외로의 인구 이동 패턴을 반영합니다.
            """)

        # 5. 시각화
        with tabs[4]:
            st.header("시각화")
            df_regions = df[df['지역'] != '전국'][['연도', '지역', '인구', 'Region']]
            pivot_table = df_regions.pivot_table(index='연도', columns='Region', values='인구', fill_value=0)
            sns.set_style("whitegrid")
            plt.figure(figsize=(12, 6))
            palette = sns.color_palette("tab20", n_colors=len(pivot_table.columns))
            pivot_table.plot(kind='area', stacked=True, color=palette, alpha=0.8)
            plt.title('Population by Region Over Time')
            plt.xlabel('Year')
            plt.ylabel('Population')
            plt.legend(title='Region', bbox_to_anchor=(1.05, 1), loc='upper left')
            plt.tight_layout()
            st.pyplot(plt)
            st.subheader("피벗 테이블 (지역별 연도별 인구)")
            st.dataframe(pivot_table, use_container_width=True)
            st.markdown("""
            **해석**:
            - 누적 영역 그래프는 2008~2023년 지역별 인구 변화를 시각화합니다.
            - 경기와 서울이 전체 인구의 큰 비중을 차지하며, 세종은 2008~2011년 인구가 0으로 시작했습니다.
            - tab20 팔레트를 사용하여 17개 지역을 명확히 구분했습니다.
            """)

# ---------------------
# 페이지 객체 생성
# ---------------------
Page_Login    = st.Page(Login,    title="Login",    icon="🔐", url_path="login")
Page_Register = st.Page(lambda: Register(Page_Login.url_path), title="Register", icon="📝", url_path="register")
Page_FindPW   = st.Page(FindPassword, title="Find PW", icon="🔎", url_path="find-password")
Page_Home     = st.Page(lambda: Home(Page_Login, Page_Register, Page_FindPW), title="Home", icon="🏠", url_path="home", default=True)
Page_User     = st.Page(UserInfo, title="My Info", icon="👤", url_path="user-info")
Page_Logout   = st.Page(Logout,   title="Logout",  icon="🔓", url_path="logout")
Page_EDA      = st.Page(EDA,      title="EDA",     icon="📊", url_path="eda")

# ---------------------
# 네비게이션 실행
# ---------------------
if st.session_state.logged_in:
    pages = [Page_Home, Page_User, Page_Logout, Page_EDA]
else:
    pages = [Page_Home, Page_Login, Page_Register, Page_FindPW]

selected_page = st.navigation(pages)
selected_page.run()