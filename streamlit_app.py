import streamlit as st
import pandas as pd
import plotly.express as px


@st.cache_data
def load_data(path: str = "car_apps_reviews.csv") -> pd.DataFrame:
    df = pd.read_csv(path)
    df["review_date"] = pd.to_datetime(df.get("review_date", df.get("at")), errors="coerce")
    return df


def main():
    st.set_page_config(page_title="Car Apps Reviews Analytics", layout="wide")
    st.title("Car Apps Reviews — Analytics")

    df = load_data()

    st.sidebar.header("Filters")
    apps = st.sidebar.multiselect("Select apps", options=sorted(df["app_name"].dropna().unique()),
                                  default=sorted(df["app_name"].dropna().unique()))
    min_date = df["review_date"].min().date() if not df["review_date"].isna().all() else None
    max_date = df["review_date"].max().date() if not df["review_date"].isna().all() else None
    date_range = st.sidebar.date_input("Date range", value=[min_date, max_date])

    # Apply filters
    df_filtered = df.copy()
    if apps:
        df_filtered = df_filtered[df_filtered["app_name"].isin(apps)]
    if len(date_range) == 2 and all(date_range):
        start = pd.to_datetime(date_range[0])
        end = pd.to_datetime(date_range[1])
        df_filtered = df_filtered[df_filtered["review_date"].between(start, end)]

    # Summary metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Total reviews", int(df_filtered.shape[0]))
    if not df_filtered["review_date"].isna().all():
        col2.metric("Date range", f"{df_filtered['review_date'].min().date()} — {df_filtered['review_date'].max().date()}")
    else:
        col2.metric("Date range", "N/A")
    col3.metric("Average rating", round(df_filtered["rating"].mean(), 2) if not df_filtered["rating"].isna().all() else "N/A")

    st.markdown("---")

    # Number of reviews per app (bar)
    st.subheader("Number of Reviews per App")
    counts = df_filtered["app_name"].value_counts().rename_axis("app_name").reset_index(name="counts")
    fig_counts = px.bar(counts, x="app_name", y="counts", labels={"app_name": "App", "counts": "Number of Reviews"})
    st.plotly_chart(fig_counts, use_container_width=True)

    # Monthly average rating per app (line)
    st.subheader("Monthly Average Rating per App")
    monthly = (
        df_filtered.dropna(subset=["review_date"]) 
        .groupby([pd.Grouper(key="review_date", freq="M"), "app_name"]) ["rating"]
        .mean()
        .reset_index()
    )
    if monthly.empty:
        st.info("No review_date data available for the selected filters.")
    else:
        fig_line = px.line(monthly, x="review_date", y="rating", color="app_name", markers=True,
                           labels={"review_date": "Month", "rating": "Average Rating", "app_name": "App"})
        st.plotly_chart(fig_line, use_container_width=True)

    st.subheader("Rating Distribution")
    fig_hist = px.histogram(df_filtered, x="rating", nbins=5, labels={"rating": "Rating"})
    st.plotly_chart(fig_hist, use_container_width=True)

    st.subheader("Sample of Reviews")
    st.dataframe(df_filtered.sort_values("review_date", ascending=False).reset_index(drop=True).head(200))

    csv = df_filtered.to_csv(index=False).encode("utf-8")
    st.download_button("Download filtered CSV", data=csv, file_name="filtered_reviews.csv", mime="text/csv")


if __name__ == "__main__":
    main()
