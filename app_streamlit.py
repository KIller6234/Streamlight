import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# Налаштування сторінки
st.set_page_config(page_title="Дашборд судових справ", layout="wide")

# -------------------------------------------------------------------
# Словник з координатами центрів областей України
# -------------------------------------------------------------------
region_coords = {
    "Вінницька": {"lat": 49.2333, "lon": 28.4667},
    "Волинська": {"lat": 50.75, "lon": 25.3333},
    "Дніпропетровська": {"lat": 48.45, "lon": 34.9833},
    "Донецька": {"lat": 48.0, "lon": 37.8},
    "Житомирська": {"lat": 50.25, "lon": 28.6667},
    "Закарпатська": {"lat": 48.4167, "lon": 22.7},
    "Запорізька": {"lat": 47.8333, "lon": 35.1667},
    "Івано-Франківська": {"lat": 48.9167, "lon": 24.7167},
    "Київська": {"lat": 50.45, "lon": 30.5233},
    "Кіровоградська": {"lat": 48.5, "lon": 32.2667},
    "Луганська": {"lat": 48.5667, "lon": 39.3333},
    "Львівська": {"lat": 49.8333, "lon": 24.0},
    "Миколаївська": {"lat": 46.9667, "lon": 32.0},
    "Одеська": {"lat": 46.4833, "lon": 30.7333},
    "Полтавська": {"lat": 49.5833, "lon": 34.5667},
    "Рівненська": {"lat": 50.6167, "lon": 26.25},
    "Сумська": {"lat": 50.9167, "lon": 34.75},
    "Тернопільська": {"lat": 49.55, "lon": 25.5833},
    "Харківська": {"lat": 49.9833, "lon": 36.2333},
    "Херсонська": {"lat": 46.6333, "lon": 32.6},
    "Хмельницька": {"lat": 49.4167, "lon": 27.0},
    "Черкаська": {"lat": 49.4333, "lon": 32.0667},
    "Чернівецька": {"lat": 48.2833, "lon": 25.9333},
    "Чернігівська": {"lat": 51.5, "lon": 31.3},
    "Київ": {"lat": 50.45, "lon": 30.5233},
    "Севастополь": {"lat": 44.6, "lon": 33.5333},
    "АР Крим": {"lat": 45.0, "lon": 34.0},
}

# -------------------------------------------------------------------
# Демо-дані
# -------------------------------------------------------------------
def load_demo_data():
    import random
    from datetime import datetime, timedelta

    regions = list(region_coords.keys())
    articles = ["124", "122", "185", "186", "187", "190", "191", "263"]
    categories = ["Кримінальні", "Адміністративні", "Цивільні", "Господарські"]

    data = []
    start_date = datetime(2015, 1, 1)
    end_date = datetime(2024, 12, 31)
    delta = end_date - start_date

    for _ in range(3000):
        region = random.choice(regions)
        article = random.choice(articles)
        category = random.choice(categories)
        random_days = random.randint(0, delta.days)
        date = start_date + timedelta(days=random_days)
        data.append([region, article, category, date])

    df = pd.DataFrame(data, columns=["region", "article", "category", "date"])
    return df

# -------------------------------------------------------------------
# Завантаження даних
# -------------------------------------------------------------------
st.title("⚖️ Дашборд судових справ")
st.markdown("Аналіз рішень судів з реєстру судових рішень України")

uploaded_file = st.file_uploader("Завантажте CSV-файл", type=["csv"])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        required_cols = ["region", "article", "category", "date"]
        if not all(col in df.columns for col in required_cols):
            st.error(f"CSV-файл має містити колонки: {', '.join(required_cols)}")
            st.stop()
        df["date"] = pd.to_datetime(df["date"])
        st.success("Файл успішно завантажено!")
    except Exception as e:
        st.error(f"Помилка при читанні файлу: {e}")
        st.stop()
else:
    st.info("Файл не завантажено. Використовується демонстраційний набір даних (3000 синтетичних записів).")
    df = load_demo_data()

# -------------------------------------------------------------------
# Фільтри
# -------------------------------------------------------------------
st.sidebar.header("Фільтри")

regions = sorted(df["region"].unique())
selected_regions = st.sidebar.multiselect("Регіон", regions, default=regions)

articles = sorted(df["article"].unique())
selected_articles = st.sidebar.multiselect("Стаття", articles, default=articles)

min_date = df["date"].min().date()
max_date = df["date"].max().date()
date_range = st.sidebar.date_input(
    "Діапазон дат",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)
if len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = min_date, max_date

# -------------------------------------------------------------------
# Застосування фільтрів
# -------------------------------------------------------------------
filtered_df = df[
    (df["region"].isin(selected_regions)) &
    (df["article"].isin(selected_articles)) &
    (df["date"].dt.date >= start_date) &
    (df["date"].dt.date <= end_date)
]

# -------------------------------------------------------------------
# Ключові показники
# -------------------------------------------------------------------
st.subheader("Загальна інформація")
col1, col2, col3 = st.columns(3)
col1.metric("Всього справ", f"{len(filtered_df):,}")
col2.metric("Унікальних регіонів", filtered_df["region"].nunique())
col3.metric("Унікальних статей", filtered_df["article"].nunique())

# -------------------------------------------------------------------
# Карта розподілу по регіонах (оновлено)
# -------------------------------------------------------------------
st.subheader("🗺️ Розподіл справ по регіонах")
if not filtered_df.empty:
    region_counts = filtered_df["region"].value_counts().reset_index()
    region_counts.columns = ["region", "count"]
    region_counts["lat"] = region_counts["region"].map(lambda r: region_coords.get(r, {}).get("lat"))
    region_counts["lon"] = region_counts["region"].map(lambda r: region_coords.get(r, {}).get("lon"))
    region_counts = region_counts.dropna(subset=["lat", "lon"])

    if not region_counts.empty:
        # Замість scatter_mapbox використовуємо scatter_map (новіший метод)
        fig_map = px.scatter_map(
            region_counts,
            lat="lat",
            lon="lon",
            size="count",
            hover_name="region",
            hover_data={"count": True},
            size_max=50,
            zoom=5.5,
            title="Кількість справ по регіонах"
        )
        fig_map.update_layout(map_style="open-street-map")
        st.plotly_chart(fig_map, width='stretch')
    else:
        st.warning("Для обраних регіонів немає координат для відображення на карті.")
else:
    st.warning("Немає даних для відображення карти.")

# -------------------------------------------------------------------
# Діаграма категорій
# -------------------------------------------------------------------
st.subheader("📊 Кількість справ за категоріями")
if not filtered_df.empty:
    cat_counts = filtered_df["category"].value_counts().reset_index()
    cat_counts.columns = ["Категорія", "Кількість"]
    fig_cat = px.bar(cat_counts, x="Категорія", y="Кількість", title="Кількість справ за категоріями")
    st.plotly_chart(fig_cat, width='stretch')
else:
    st.warning("Немає даних, що відповідають вибраним фільтрам.")

# -------------------------------------------------------------------
# Аналіз тенденцій по роках
# -------------------------------------------------------------------
st.subheader("📈 Тенденції по роках")
if not filtered_df.empty:
    filtered_df["year"] = filtered_df["date"].dt.year

    trend_type = st.radio(
        "Аналізувати за:",
        ["Категоріями", "Статтями"],
        horizontal=True
    )

    if trend_type == "Категоріями":
        yearly_counts = filtered_df.groupby(["year", "category"]).size().reset_index(name="count")
        fig_trend = px.line(
            yearly_counts,
            x="year",
            y="count",
            color="category",
            title="Кількість справ по роках (за категоріями)",
            markers=True
        )
        st.plotly_chart(fig_trend, width='stretch')
    else:
        available_articles = sorted(filtered_df["article"].unique())
        selected_articles_trend = st.multiselect(
            "Виберіть статті для аналізу",
            available_articles,
            default=available_articles[:5] if len(available_articles) > 5 else available_articles
        )
        if selected_articles_trend:
            trend_df = filtered_df[filtered_df["article"].isin(selected_articles_trend)]
            yearly_counts = trend_df.groupby(["year", "article"]).size().reset_index(name="count")
            fig_trend = px.line(
                yearly_counts,
                x="year",
                y="count",
                color="article",
                title="Кількість справ по роках (за статтями)",
                markers=True
            )
            st.plotly_chart(fig_trend, width='stretch')
        else:
            st.warning("Виберіть хоча б одну статтю для аналізу.")
else:
    st.warning("Немає даних для відображення тренду.")

# -------------------------------------------------------------------
# Завантаження відфільтрованих даних
# -------------------------------------------------------------------
st.subheader("📥 Експорт даних")
if not filtered_df.empty:
    csv = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Завантажити відфільтровані дані (CSV)",
        data=csv,
        file_name="suddovi_spravy_filtr.csv",
        mime="text/csv",
    )
else:
    st.info("Немає даних для експорту.")

# -------------------------------------------------------------------
# Попередній перегляд
# -------------------------------------------------------------------
st.subheader("📄 Відфільтровані дані")
st.dataframe(filtered_df, width='stretch')