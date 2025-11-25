"""
Name: Olivia Pusczko
Date: November 25, 2025
Description: This program is an interactive Streamlit application designed to explore Boston's public tree dataset. Users can view the most common tree species in each neighborhood, visualize trees on an interactive map by parks, and analyze trees by their DBH/diameter range. The app includes different charts like bar graphs and pie charts, along with a map using PyDeck for geographical visualization.
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import pydeck as pdk


#LOAD DATA
@st.cache_data
def load_data(path):
    df = pd.read_csv(path, low_memory=False)
    df.columns = [c.lower() for c in df.columns]
    for col in ['dbh', 'point_x', 'point_y']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    return df


#FUNCTIONS
def filter_trees_by_dbh(df, min_dbh=0, max_dbh=100):
    return df[(df['dbh'] >= min_dbh) & (df['dbh'] <= max_dbh)]

def neighborhood_tree_counts(df, neighborhood):
    nb_data = df[df['neighborhood'] == neighborhood]
    return nb_data['spp_com'].value_counts(), len(nb_data)


#Updated display_bar_chart to show only top 30 species
def display_bar_chart(series_counts, title, top_n=30):
    #Display bar chart of counts for top 30 species
    top_series = series_counts.head(top_n)

    #Assign a unique color to each species
    colors = plt.cm.tab20.colors
    color_list = [colors[i % len(colors)] for i in range(len(top_series))]

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.bar(top_series.index, top_series.values, color=color_list)
    ax.set_xticklabels(top_series.index, rotation=45, ha='right')
    ax.set_ylabel("Number of Trees")
    ax.set_title(title)
    st.pyplot(fig)

    # Display top 10 species below chart
    st.subheader("Top 10 Species by Count")
    top_10 = top_series.head(10)
    for species, count in top_10.items():
        st.write(f"{species}: {count}")


def build_pydeck_map(df_points):
    # Drop rows with missing or invalid coordinates
    df_points = df_points.dropna(subset=['point_x', 'point_y'])
    df_points = df_points[
        df_points['point_x'].between(-180, 180) & df_points['point_y'].between(-90, 90)
        ]

    if df_points.empty:
        st.info("No valid coordinate data to display.")
        return

    # Ensure numeric types
    df_points['point_x'] = pd.to_numeric(df_points['point_x'], errors='coerce')
    df_points['point_y'] = pd.to_numeric(df_points['point_y'], errors='coerce')
    df_points['dbh'] = pd.to_numeric(df_points['dbh'].fillna(5))
    df_points['spp_com'] = df_points['spp_com'].fillna("Unknown").astype(str)

    # Determine top 10 species
    top_species = df_points['spp_com'].value_counts().head(10).index.tolist()
    colors = [
        [255, 0, 0], [0, 0, 255], [0, 128, 0], [255, 165, 0], [128, 0, 128],
        [165, 42, 42], [255, 192, 203], [0, 255, 255], [255, 255, 0], [0, 0, 0]
    ]
    color_map = {s: colors[i] for i, s in enumerate(top_species)}

    # Assign color to each row (gray for species not in top 10)
    df_points['color'] = df_points['spp_com'].map(lambda s: color_map.get(s, [169, 169, 169]))

    # PyDeck Scatterplot Layer
    layer = pdk.Layer(
        "ScatterplotLayer",
        data=df_points,
        get_position=["point_x", "point_y"],  # [longitude, latitude]
        get_fill_color="color",
        get_radius=10,
        pickable=True,
        auto_highlight=True
    )

    # Center map on Boston (or mean coordinates if available)
    if not df_points.empty:
        center_lat = df_points['point_y'].mean()
        center_lon = df_points['point_x'].mean()
    else:
        center_lat, center_lon = 42.3601, -71.0589  # default Boston

    view = pdk.ViewState(
        latitude=center_lat,
        longitude=center_lon,
        zoom=15,
        pitch=30
    )

    # Tooltip
    tooltip = {
        "html": "<b>Species:</b> {spp_com} <br/> <b>DBH:</b> {dbh} <br/> <b>Park:</b> {park} <br/> <b>Neighborhood:</b> {neighborhood}",
        "style": {"color": "white"}
    }

    # Render PyDeck map
    st.pydeck_chart(pdk.Deck(
        layers=[layer],
        initial_view_state=view,
        tooltip=tooltip,
        map_style="light"
    ))

    # Legend for top 10 species
    st.subheader("Legend: Top 10 Species")
    cols = st.columns(2)
    for i, species in enumerate(top_species):
        color = color_map[species]
        hex_color = f'#{color[0]:02x}{color[1]:02x}{color[2]:02x}'
        with cols[i % 2]:
            st.markdown(
                f"<div style='background:{hex_color};width:20px;height:20px;display:inline-block;margin-right:5px'></div>{species}",
                unsafe_allow_html=True
            )
def plot_pie(series_counts, title):
    fig, ax = plt.subplots(figsize=(6,6))
    ax.pie(series_counts.values, labels=series_counts.index, autopct='%1.1f%%', startangle=140)
    ax.set_title(title)
    st.pyplot(fig)


#MAIN APP
def main():
    df = load_data("bprd_trees.csv")

    st.title("Boston Trees Explorer")
    page = st.sidebar.radio("Select a View:", ["Trees by Neighborhood", "Map of Trees in Parks", "Tree Diameter Filter"])

    #Page 1: Neighborhood
    if page == "Trees by Neighborhood":
        st.header("Trees by Neighborhood")
        neighborhoods = sorted(df['neighborhood'].dropna().unique())
        selected_nb = st.selectbox("Select a neighborhood:", neighborhoods)  # [ST1]

        counts, total = neighborhood_tree_counts(df, selected_nb)
        st.write(f"Total trees in {selected_nb}: {total}")

        # Bar chart of top 30 species #[CHART1]
        display_bar_chart(counts, f"Top 30 Tree Species in {selected_nb}", top_n=30)

    # Page 2: Parks Map
    elif page == "Map of Trees in Parks":
        st.header("Map of Trees in Parks")
        parks = sorted(df['park'].dropna().unique())
        selected_park = st.selectbox("Choose a park:", parks)
        park_data = df[df['park']==selected_park]
        st.write(f"Total trees in {selected_park}: {len(park_data)}")
        build_pydeck_map(park_data)

    # Page 3: Diameter Filter
    elif page == "Tree Diameter Filter":
        st.header("Filter Trees by Diameter")
        min_dbh = int(df['dbh'].min())
        max_dbh = int(df['dbh'].max())
        selected_range = st.slider("Select diameter range (in inches):", min_value=min_dbh, max_value=max_dbh, value=(min_dbh,max_dbh))
        filtered = filter_trees_by_dbh(df, selected_range[0], selected_range[1])
        st.write(f"Total trees in selected range: {len(filtered)}")
        counts = filtered['spp_com'].value_counts()
        if not counts.empty:
            plot_pie(counts, f"Species Distribution for DBH {selected_range[0]}–{selected_range[1]}")
        else:
            st.write("No trees found in this diameter range.")

    st.write("---")
    st.caption("Created for CS230 by Olivia Pusczko — Boston Trees Explorer")

if __name__ == "__main__":
    main()
