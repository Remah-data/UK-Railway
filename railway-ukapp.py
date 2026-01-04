import streamlit as st
import pandas as pd
import plotly.express as px

# ===================== Page Config =====================
st.set_page_config(
    page_title="UK Railway Dashboard",
    layout="wide"
)

# ===================== Load Data =====================
df = pd.read_csv("railway.csv")
df["Date of Purchase"] = pd.to_datetime(df["Date of Purchase"], errors="coerce")

# ===================== Station Coordinates =====================
stations_coords = {
    "London Paddington": [51.5154, -0.1754],
    "Liverpool Lime Street": [53.4070, -2.9779],
    "London Kings Cross": [51.5308, -0.1238],
    "Manchester Piccadilly": [53.4774, -2.2304],
    "Birmingham New Street": [52.4778, -1.8986],
    "Edinburgh Waverley": [55.9521, -3.1890],
    "Bristol Temple Meads": [51.4490, -2.5810],
    "London Euston": [51.5281, -0.1337],
}

coords_df = pd.DataFrame(stations_coords).T.reset_index()
coords_df.columns = ["Station", "Lat", "Lon"]

df = df.merge(coords_df, left_on="Departure Station", right_on="Station", how="left")
df.rename(columns={"Lat": "Departure_Lat", "Lon": "Departure_Lon"}, inplace=True)
df.drop(columns=["Station"], inplace=True)

df = df.merge(coords_df, left_on="Arrival Destination", right_on="Station", how="left")
df.rename(columns={"Lat": "Arrival_Lat", "Lon": "Arrival_Lon"}, inplace=True)
df.drop(columns=["Station"], inplace=True)

# ===================== Sidebar Filters =====================


purchase = st.sidebar.multiselect(
    "Purchase Type",
    df["Purchase Type"].dropna().unique()
)

ticket = st.sidebar.multiselect(
    "Ticket Class",
    df["Ticket Class"].dropna().unique()
)

status = st.sidebar.multiselect(
    "Journey Status",
    df["Journey Status"].dropna().unique()
)

date_range = st.sidebar.date_input(
    "Date Range",
    [df["Date of Purchase"].min(), df["Date of Purchase"].max()]
)

filtered = df.copy()

if purchase:
    filtered = filtered[filtered["Purchase Type"].isin(purchase)]
if ticket:
    filtered = filtered[filtered["Ticket Class"].isin(ticket)]
if status:
    filtered = filtered[filtered["Journey Status"].isin(status)]

filtered = filtered[
    (filtered["Date of Purchase"] >= pd.to_datetime(date_range[0])) &
    (filtered["Date of Purchase"] <= pd.to_datetime(date_range[1]))
]

# ===================== Title =====================
st.title("UK Railway Dashboard")

# ===================== KPIs =====================
k1, k2, k3, k4 = st.columns(4)

k1.metric("Total Revenue", f"£{filtered['Price'].sum():,.0f}")
k2.metric("Average Ticket Price", f"£{filtered['Price'].mean():,.2f}")
k3.metric(
    "Delayed Rate",
    f"{(filtered['Journey Status'] == 'Delayed').mean() * 100:.1f}%"
)
k4.metric(
    "On-Time Performance",
    f"{(filtered['Journey Status'] == 'On Time').mean() * 100:.1f}%"
)

st.divider()

# ===================== Charts =====================
c1, c2 = st.columns(2)

# ---- Top Routes
with c1:
    top_routes = (
        filtered.groupby(["Departure Station", "Arrival Destination"])["Price"]
        .sum()
        .reset_index()
        .nlargest(8, "Price")
    )
    fig = px.bar(
        top_routes,
        x="Price",
        y="Departure Station",
        color="Arrival Destination",
        orientation="h",
        title="Top 8 Most Profitable Routes"
    )
    st.plotly_chart(fig, use_container_width=True)

# ---- Ticket Price Distribution
with c2:
    fig = px.violin(
        filtered,
        x="Ticket Class",
        y="Price",
        color="Ticket Class",
        box=True,
        points=False,
        title="Ticket Price Distribution"
    )
    st.plotly_chart(fig, use_container_width=True)

# ===================== Extra Charts  =====================
c3, c4 = st.columns(2)

# ---- Delay Rate by Station
with c3:
    delay_station = (
        filtered.assign(Delayed=filtered["Journey Status"] == "Delayed")
        .groupby("Departure Station")["Delayed"]
        .mean()
        .reset_index()
    )
    fig = px.bar(
        delay_station,
        x="Departure Station",
        y="Delayed",
        title="Delay Rate by Departure Station"
    )
    st.plotly_chart(fig, use_container_width=True)

# ---- Monthly Revenue
with c4:
    monthly = (
        filtered
        .groupby(filtered["Date of Purchase"].dt.to_period("M"))["Price"]
        .sum()
        .reset_index()
    )
    monthly["Date of Purchase"] = monthly["Date of Purchase"].astype(str)

    fig = px.line(
        monthly,
        x="Date of Purchase",
        y="Price",
        markers=True,
        title="Monthly Revenue Trend"
    )
    st.plotly_chart(fig, use_container_width=True)

# ===================== Interactive Map (Plotly – Stable) =====================
st.subheader("🗺 Railway Routes Map")

map_df = filtered.dropna(
    subset=["Departure_Lat", "Departure_Lon", "Arrival_Lat", "Arrival_Lon"]
)

if not map_df.empty:

    fig = px.scatter_mapbox(
        map_df,
        lat="Departure_Lat",
        lon="Departure_Lon",
        hover_name="Departure Station",
        hover_data=[
            "Arrival Destination",
            "Price",
            "Ticket Class",
            "Journey Status"
        ],
        zoom=4,
        height=550
    )

   # Map
    for _, row in map_df.iterrows():
        fig.add_scattermapbox(
            lat=[row["Departure_Lat"], row["Arrival_Lat"]],
            lon=[row["Departure_Lon"], row["Arrival_Lon"]],
            mode="lines",
            line=dict(width=2),
            showlegend=False
        )

    fig.update_layout(
        mapbox_style="open-street-map",
        margin=dict(r=0, l=0, t=0, b=0)
    )

    st.plotly_chart(fig, use_container_width=True)

else:
    st.warning("No geographic data available for selected filters.")
