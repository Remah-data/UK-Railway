import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import pydeck as pdk
from io import BytesIO
import io
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

# =============================================================
# Page Config
# =============================================================
st.set_page_config(page_title="UK Railway Intelligence Dashboard", layout="wide", page_icon="🚆")

# =============================================================
# Global Styles (Black translucent background + Black text)
# =============================================================
st.markdown(
    """
    <style>
      html, body, [class^="css"], .stApp {
        background: CCF2F4 !important;
        color: red !important;
      }
      .stSidebar, section[data-testid="stSidebar"] > div {
        background: CCF2F4 !important;
        color: red !important;
      }
      h1, h2, h3, label, .stMarkdown, .stText, .stAlert, .stSelectbox label, .stMultiSelect label {
        color: red                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                !important;
      }
      /* Card style */
      .info-card {
        background: rgba(255, 255, 255, 0.9);
        border: 1px solid rgba(0,0,0,0.35);
        border-radius: 16px;
        padding: 18px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.25);
      }
      /* KPI cards */
      .kpi-card {
        background: rgba(255, 255, 255, 0.95);
        border: 2px solid #000000;
        border-radius: 20px;
        padding: 22px;
        text-align: center;
        box-shadow: 0 5px 25px rgba(0,0,0,0.2);
      }
      .kpi-title { font-size: 1rem; opacity: 0.8; color: #333; }
      .kpi-value { font-size: 2rem; font-weight: 800; color: #000; }
      /* Download button */
      .stDownloadButton > button {
        border-radius: 12px;
        border: 1px solid #000000;
        background-color: rgba(255,255,255,0.9);
        color: #000000;
      }
    .card {
        background-color: #ffffff;   /* خلفية بيضاء */
        padding: 15px;
        border-radius: 15px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.15);
        margin-bottom: 20px;
        position: relative;
      }
    .card {
        color: red;
        text-align: center;
      }
    .badge {
        position: absolute;
        top: 8px;
        right: 10px;
        background-color: red;
        color: white;
        padding: 3px 8px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: bold;
      }
    
    # .sidebar .stImage img {
    #     border-radius: 50%;
    #     width: 120px;       
    #     height: 120px;      
    #     object-fit: cover; 
    #   }


    </style>
    """,
    unsafe_allow_html=True,
)


# =============================================================
# Sidebar: Branding + Filters + Options
# =============================================================
st.sidebar.title("🚆 UK Railway Dashboard")
# ----------------- IMAGE ---------------
# st.sidebar.image("uk.PNG",use_column_width=True)


# ------------------ LINK PROFILE -------------
st.sidebar.markdown("Linkedin: http://bit.ly/4lDIiPy")
# ---------------------------------------------
st.sidebar.subheader("Filters")

DATA_PATH = "railway.csv"  # dataset path

try:
    df = pd.read_csv(DATA_PATH)
except Exception as e:
    st.error(f"Couldn't read data from {DATA_PATH}. Error: {e}")
    st.stop()

# =============================================================
# Coordinates dictionary (extend with all stations as needed)
# =============================================================
stations_coords = {
    "London Euston": [51.5281, -0.1337],
    "London Kings Cross": [51.5308, -0.1238],
    "London Paddington": [51.5154, -0.1754],
    "London St Pancras": [51.5315, -0.1263],
    "Manchester Piccadilly": [53.4774, -2.2304],
    "Liverpool Lime Street": [53.4070, -2.9779],
    "Birmingham New Street": [52.4778, -1.8986],
    "York": [53.9576, -1.0930],
    "Reading": [51.4580, -0.9732],
    "Oxford": [51.7548, -1.2683],
    "Edinburgh Waverley": [55.9521, -3.1890],
    "Bristol Temple Meads": [51.4490, -2.5810],
}
coords_df = pd.DataFrame(stations_coords).T.reset_index()
coords_df.columns = ["Station", "Latitude", "Longitude"]

# Merge coordinates
if {"Departure Station"}.issubset(df.columns):
    df = df.merge(coords_df, left_on="Departure Station", right_on="Station", how="left")
    df = df.rename(columns={"Latitude": "Departure_Lat", "Longitude": "Departure_Lon"})
    df = df.drop(columns=["Station"])
if {"Arrival Destination"}.issubset(df.columns):
    df = df.merge(coords_df, left_on="Arrival Destination", right_on="Station", how="left")
    df = df.rename(columns={"Latitude": "Arrival_Lat", "Longitude": "Arrival_Lon"})
    df = df.drop(columns=["Station"])

# =============================================================
# Sidebar filters
# =============================================================
purchase_type = st.sidebar.multiselect("Purchase Type", df["Purchase Type"].unique() if "Purchase Type" in df.columns else [])
ticket_class = st.sidebar.multiselect("Ticket Class", df["Ticket Class"].unique() if "Ticket Class" in df.columns else [])
departure_sel = st.sidebar.multiselect("Departure Station", df["Departure Station"].unique() if "Departure Station" in df.columns else [])
arrival_sel = st.sidebar.multiselect("Arrival Destination", df["Arrival Destination"].unique() if "Arrival Destination" in df.columns else [])

st.sidebar.subheader("Map Options")
map_style = st.sidebar.selectbox("Style", ["Dark", "Street", "Satellite"], index=0)
show_points = st.sidebar.checkbox("Show Points", value=True)
show_routes = st.sidebar.checkbox("Show Routes", value=True)

# =============================================================
# Header with Cards
# =============================================================

st.title("UK Railways Analysis Dashboard")

# Header Section
# -------------------

col1, col2, col3 = st.columns(3)

with col1:
    with st.expander("📌 About Me"):
        st.write("I am an ambitious Data Analyst with experience in analyzing data and using analytical tools to provide insights that help improve operations and support\n Skills: [Data Analysis - Statistics - Excel & Python - Data Visualization ]")
                              

with col2:
    with st.expander("📂 About the Project"):
        st.write("This project aims to analyze UK railway ticket sales data, focusing on revenue, travel patterns, and delays.The analysis includes:Studying revenue by departure and arrival stations.Analyzing ticket price distribution by class (first class, second class, etc.).Understanding the proportion of delayed journeys versus on-time journeys.Presenting data visually using bar charts, boxplots, pie charts, and professional dashboard cards.This analysis helps identify key passenger trends and supports operational improvements and service efficiency.")

        
with col3:
    with st.expander("⬇ Project Report"):
        with open("RailwayUK.pdf", "rb") as file:
            st.download_button(
                label="Download Report",
                data=file,
                file_name="RailwayUK.pdf",
                mime="application/pdf")


# =============================================================
# Apply Filters
# =============================================================
filtered = df.copy()
if purchase_type:
    filtered = filtered[filtered["Purchase Type"].isin(purchase_type)]
if ticket_class:
    filtered = filtered[filtered["Ticket Class"].isin(ticket_class)]
if departure_sel:
    filtered = filtered[filtered["Departure Station"].isin(departure_sel)]
if arrival_sel:
    filtered = filtered[filtered["Arrival Destination"].isin(arrival_sel)]

# =============================================================
# KPI Section with Attractive Cards
# =============================================================
st.header("Key Performance Indicators")
k1, k2, k3 = st.columns(3)

price_col = "Price" if "Price" in filtered.columns else None
status_col = "Journey Status" if "Journey Status" in filtered.columns else None

total_revenue = filtered[price_col].sum() if price_col else 0
avg_price = filtered[price_col].mean() if price_col else 0
delayed_cnt = (filtered[status_col] == "Delayed").sum() if status_col else 0
total_trips = len(filtered)
delayed_pct = (delayed_cnt / total_trips * 100) if total_trips else 0

with k1:
    st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Total Revenue</div><div class='kpi-value'>£{total_revenue:,.0f}</div></div>", unsafe_allow_html=True)
with k2:
    st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Average Ticket Price</div><div class='kpi-value'>£{avg_price:,.2f}</div></div>", unsafe_allow_html=True)
with k3:
    st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Delayed Journeys</div><div class='kpi-value'>{delayed_pct:.2f}%</div></div>", unsafe_allow_html=True)

# =============================================================
# Data Analysis & Visualizations
# =============================================================
st.header("Visualizations")
# --- الصف الأول: Bar chart + Boxplot
col1, col2 = st.columns(2)

with col1:
    with st.container():
        total_revenue = df["Price"].sum()
       # st.markdown(f'<div class="card"><span class="badge">£{total_revenue:,.0f}</span><h3>💰 Revenue by Departure Station</h3>', unsafe_allow_html=True)
        revenue_by_station = df.groupby("Departure Station")["Price"].sum().sort_values(ascending=False).head(10)
        fig, ax = plt.subplots(figsize=(6,4))
        revenue_by_station.plot(kind="bar", color="red", ax=ax)
        ax.set_ylabel("Revenue (£)", color="black")
        ax.tick_params(axis='x', colors='black', rotation=45)
        ax.tick_params(axis='y', colors='black')
        st.pyplot(fig)
        st.markdown('</div>', unsafe_allow_html=True)

with col2:
    with st.container():
        record_count = len(df)
        #st.markdown(f'<div class="card"><span class="badge">{record_count:,} Records</span><h3>🎫 Ticket Price Distribution by Class</h3>', unsafe_allow_html=True)
        fig, ax = plt.subplots(figsize=(6,4))
        df.boxplot(column="Price", by="Ticket Class", grid=False, ax=ax, color="red")
        ax.set_xlabel("Ticket Class", color="black")
        ax.set_ylabel("Price (£)", color="black")
        plt.suptitle("")
        ax.tick_params(axis='x', colors='black')
        ax.tick_params(axis='y', colors='black')
        st.pyplot(fig)
        st.markdown('</div>', unsafe_allow_html=True)



      # --- الصف الثاني: Pie + Arrival Station Revenue
col3, col4 = st.columns(2)

with col3:
    with st.container():
        journey_count = df["Journey Status"].nunique()
        #st.markdown(f'<div class="card"><span class="badge">{journey_count} Types</span><h3>🚦 Journey Status Distribution</h3>', unsafe_allow_html=True)
        status_counts = df["Journey Status"].value_counts()
        fig, ax = plt.subplots()
        ax.pie(status_counts, labels=status_counts.index, autopct="%1.1f%%", 
               colors=["red","darkred","lightcoral"], textprops={'color':'black'})
        st.pyplot(fig)
        st.markdown('</div>', unsafe_allow_html=True)

with col4:
    with st.container():
        # رسم جديد: Top 10 Arrival Stations by Revenue
        top_arrivals = df.groupby("Arrival Destination")["Price"].sum().sort_values(ascending=False).head(10)
        total_revenue_arrival = top_arrivals.sum()
        #st.markdown(f'<div class="card"><span class="badge">£{total_revenue_arrival:,.0f}</span><h3>🚉 Top 10 Arrival Stations by Revenue</h3>', unsafe_allow_html=True)
        fig, ax = plt.subplots(figsize=(6,4))
        top_arrivals.plot(kind="bar", color="red", ax=ax)
        ax.set_ylabel("Revenue (£)", color="black")
        ax.tick_params(axis='x', colors='black', rotation=45)
        ax.tick_params(axis='y', colors='black')
        st.pyplot(fig)
        st.markdown('</div>', unsafe_allow_html=True)


# =============================================================
# Map Visualization
# =============================================================
st.header("🗺 Geographical Map with Routes")

map_data = df[["Departure_Lat", "Departure_Lon"]].dropna()
map_data = map_data.rename(columns={"Departure_Lat": "lat", "Departure_Lon": "lon"})
st.map(map_data, zoom=5)

# -------------------------------------------------

route_data = df.dropna(subset=["Departure_Lat","Departure_Lon","Arrival_Lat","Arrival_Lon"])

layer_points = pdk.Layer(
    "ScatterplotLayer",
    data=route_data,
    get_position=["Departure_Lon","Departure_Lat"],
    get_color=[255,0,0],
    get_radius=20000,
)

layer_routes = pdk.Layer(
    "LineLayer",
    data=route_data,
    get_source_position=["Departure_Lon","Departure_Lat"],
    get_target_position=["Arrival_Lon","Arrival_Lat"],
    get_color=[255,0,0],
    get_width=2,
)

view_state = pdk.ViewState(latitude=54, longitude=-2, zoom=5)
st.pydeck_chart(pdk.Deck(layers=[layer_points, layer_routes], initial_view_state=view_state))

# =============================================================
# Summary Section
# =============================================================
st.header("Summary")
st.write("""This dashboard provides detailed insights into UK railway operations, including purchase types, ticket classes, routes, and geospatial flows. KPIs are displayed in modern cards, visualizations are clear, and data export is available for further use.""")