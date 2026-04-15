import streamlit as st
import pandas as pd
import pymysql
import plotly.express as px


# Database connection

def create_connection():
    try:
        connection = pymysql.connect(
            host="localhost",
            user="root",
            password="Surya@1516",
            database="securecheck",
            cursorclass=pymysql.cursors.DictCursor
        )
        return connection
    except Exception as e:
        st.error(f"Database connection error: {e}")
        return None


# Fetch data from database

def fetch_data(query):
    connection = create_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                cursor.execute(query)
                result = cursor.fetchall()
                return pd.DataFrame(result)
        except Exception as e:
            st.error(f"Query execution error: {e}")
            return pd.DataFrame()
        finally:
            connection.close()
    return pd.DataFrame()


# Streamlit page config

st.set_page_config(page_title="Securecheck Police Dashboard", layout="wide")

st.title("🚨 Securecheck Police Check Post Digital Ledger")
st.markdown("Real-time monitoring and insights for law enforcement 🚓")


# Load main table
st.header("Police Logs Overview 📋")
main_query = "SELECT * FROM police_logs"
data = fetch_data(main_query)

if data.empty:
    st.warning("No data found in police_logs table.")
    st.stop()

st.dataframe(data, use_container_width=True)


 
# Data cleaning for dashboard

if "stop_outcome" in data.columns:
    data["stop_outcome"] = data["stop_outcome"].astype(str)

if "search_conducted" in data.columns:
    data["search_conducted"] = data["search_conducted"].astype(str)

if "drugs_related_stop" in data.columns:
    data["drugs_related_stop"] = data["drugs_related_stop"].astype(str)



# Quick metrics

st.header("📊 Key Metrics")
col1, col2, col3, col4 = st.columns(4)

total_stops = data.shape[0]
arrests = data[data["stop_outcome"].str.contains("arrest", case=False, na=False)].shape[0]
warnings = data[data["stop_outcome"].str.contains("warning", case=False, na=False)].shape[0]
drug_related = data[data["drugs_related_stop"].isin(["1", "True", "true"])].shape[0]

with col1:
    st.metric("Total Police Stops", total_stops)

with col2:
    st.metric("Total Arrests", arrests)

with col3:
    st.metric("Total Warnings", warnings)

with col4:
    st.metric("Drugs Related Stops", drug_related)

# Visual insights

st.header("📈 Visual Insights")
tab1, tab2 = st.tabs(["Stops by Violation", "Driver Gender Distribution"])

with tab1:
    if "violation" in data.columns:
        violation_data = data["violation"].value_counts().reset_index()
        violation_data.columns = ["violation", "count"]
        fig = px.bar(
            violation_data,
            x="violation",
            y="count",
            title="Stops by Violation Type",
            color="violation"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No data available for violation chart.")

with tab2:
    if "driver_gender" in data.columns:
        gender_data = data["driver_gender"].value_counts().reset_index()
        gender_data.columns = ["Gender", "count"]
        fig = px.bar(
            gender_data,
            x="Gender",
            y="count",
            title="Driver Gender Distribution",
            color="Gender"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No data available for gender chart.")


# Advanced insights
st.header("🧩 Advanced Insights")

selected_query = st.selectbox(
    "Select a query to run",
    [
        "Top 10 Vehicles involved in drug-related stops",
        "Most frequently searched vehicles",
        "Driver age group with highest arrest rate",
        "Gender distribution of drivers stopped in each country",
        "Race + gender combination with highest search rate",
        "Time of day with most traffic stops",
        "Average stop duration for different violations",
        "Night-time stops more likely to lead to arrests?",
        "Violations associated with searches or arrests",
        "Common violations among younger drivers (<25)",
        "Violations that rarely result in search or arrest",
        "Countries with highest drug-related stops",
        "Arrest rate by country and violation",
        "Countries with the most stops involving a search",
        "Yearly breakdown of stops & arrests by country",
        "Driver violation trends by age & race",
        "Time period analysis (Year, Month, Hour)",
        "Violations with high search & arrest rates",
        "Driver demographics by country",
        "Top 5 violations with highest arrest rates"
    ]
)

query_map = {
    "Top 10 Vehicles involved in drug-related stops": """
        SELECT vehicle_number, COUNT(*) AS drug_cases
        FROM police_logs
        WHERE drugs_related_stop IN (1, '1', 'True', 'true')
        GROUP BY vehicle_number
        ORDER BY drug_cases DESC
        LIMIT 10;
    """,

    "Most frequently searched vehicles": """
        SELECT vehicle_number, COUNT(*) AS searches
        FROM police_logs
        WHERE search_conducted IN (1, '1', 'True', 'true')
        GROUP BY vehicle_number
        ORDER BY searches DESC;
    """,

    "Driver age group with highest arrest rate": """
        SELECT driver_age,
               AVG(CASE WHEN stop_outcome LIKE '%Arrest%' THEN 1 ELSE 0 END) * 100 AS arrest_rate
        FROM police_logs
        WHERE driver_age IS NOT NULL
        GROUP BY driver_age
        ORDER BY arrest_rate DESC;
    """,

    "Gender distribution of drivers stopped in each country": """
        SELECT country_name, driver_gender, COUNT(*) AS total
        FROM police_logs
        GROUP BY country_name, driver_gender;
    """,

    "Race + gender combination with highest search rate": """
        SELECT driver_race,
               driver_gender,
               AVG(CASE WHEN search_conducted IN (1, '1', 'True', 'true') THEN 1 ELSE 0 END) * 100 AS search_rate
        FROM police_logs
        GROUP BY driver_race, driver_gender
        ORDER BY search_rate DESC;
    """,

    "Time of day with most traffic stops": """
        SELECT HOUR(stop_time) AS hour, COUNT(*) AS total
        FROM police_logs
        GROUP BY HOUR(stop_time)
        ORDER BY total DESC;
    """,

    "Average stop duration for different violations": """
        SELECT violation,
               AVG(
                   CASE
                       WHEN stop_duration = '<5 min' THEN 3
                       WHEN stop_duration = '6-15 min' THEN 10
                       WHEN stop_duration = '16-30 min' THEN 20
                       WHEN stop_duration = '30+ min' THEN 35
                       ELSE NULL
                   END
               ) AS avg_minutes
        FROM police_logs
        GROUP BY violation;
    """,

    "Night-time stops more likely to lead to arrests?": """
        SELECT
            CASE
                WHEN HOUR(stop_time) BETWEEN 20 AND 23 OR HOUR(stop_time) BETWEEN 0 AND 4 THEN 'Night'
                ELSE 'Day'
            END AS period,
            AVG(CASE WHEN stop_outcome LIKE '%Arrest%' THEN 1 ELSE 0 END) * 100 AS arrest_rate
        FROM police_logs
        GROUP BY period;
    """,

    "Violations associated with searches or arrests": """
        SELECT violation,
               AVG(CASE WHEN search_conducted IN (1, '1', 'True', 'true') THEN 1 ELSE 0 END) * 100 AS search_rate,
               AVG(CASE WHEN stop_outcome LIKE '%Arrest%' THEN 1 ELSE 0 END) * 100 AS arrest_rate
        FROM police_logs
        GROUP BY violation;
    """,

    "Common violations among younger drivers (<25)": """
        SELECT violation, COUNT(*) AS total
        FROM police_logs
        WHERE driver_age < 25
        GROUP BY violation
        ORDER BY total DESC;
    """,

    "Violations that rarely result in search or arrest": """
        SELECT violation,
               AVG(CASE WHEN search_conducted IN (1, '1', 'True', 'true') THEN 1 ELSE 0 END) * 100 AS search_rate,
               AVG(CASE WHEN stop_outcome LIKE '%Arrest%' THEN 1 ELSE 0 END) * 100 AS arrest_rate
        FROM police_logs
        GROUP BY violation
        HAVING search_rate < 5 AND arrest_rate < 2;
    """,

    "Countries with highest drug-related stops": """
        SELECT country_name,
               SUM(CASE WHEN drugs_related_stop IN (1, '1', 'True', 'true') THEN 1 ELSE 0 END) AS total
        FROM police_logs
        GROUP BY country_name
        ORDER BY total DESC;
    """,

    "Arrest rate by country and violation": """
        SELECT country_name,
               violation,
               AVG(CASE WHEN stop_outcome LIKE '%Arrest%' THEN 1 ELSE 0 END) * 100 AS arrest_rate
        FROM police_logs
        GROUP BY country_name, violation
        ORDER BY arrest_rate DESC;
    """,

    "Countries with the most stops involving a search": """
        SELECT country_name,
               SUM(CASE WHEN search_conducted IN (1, '1', 'True', 'true') THEN 1 ELSE 0 END) AS searches
        FROM police_logs
        GROUP BY country_name
        ORDER BY searches DESC;
    """,

    "Yearly breakdown of stops & arrests by country": """
        SELECT country_name,
               YEAR(stop_date) AS year,
               COUNT(*) AS stops,
               SUM(CASE WHEN stop_outcome LIKE '%Arrest%' THEN 1 ELSE 0 END) AS arrests
        FROM police_logs
        GROUP BY country_name, YEAR(stop_date)
        ORDER BY year, country_name;
    """,

    "Driver violation trends by age & race": """
        SELECT driver_age, driver_race, violation, COUNT(*) AS total
        FROM police_logs
        GROUP BY driver_age, driver_race, violation
        ORDER BY total DESC;
    """,

    "Time period analysis (Year, Month, Hour)": """
        SELECT YEAR(stop_date) AS year,
               MONTH(stop_date) AS month,
               HOUR(stop_time) AS hour,
               COUNT(*) AS total
        FROM police_logs
        GROUP BY YEAR(stop_date), MONTH(stop_date), HOUR(stop_time)
        ORDER BY year, month, hour;
    """,

    "Violations with high search & arrest rates": """
        SELECT violation,
               AVG(CASE WHEN search_conducted IN (1, '1', 'True', 'true') THEN 1 ELSE 0 END) * 100 AS search_rate,
               AVG(CASE WHEN stop_outcome LIKE '%Arrest%' THEN 1 ELSE 0 END) * 100 AS arrest_rate
        FROM police_logs
        GROUP BY violation
        ORDER BY arrest_rate DESC;
    """,

    "Driver demographics by country": """
        SELECT country_name, driver_age, driver_gender, driver_race, COUNT(*) AS total
        FROM police_logs
        GROUP BY country_name, driver_age, driver_gender, driver_race
        ORDER BY total DESC;
    """,

    "Top 5 violations with highest arrest rates": """
        SELECT violation,
               AVG(CASE WHEN stop_outcome LIKE '%Arrest%' THEN 1 ELSE 0 END) * 100 AS arrest_rate
        FROM police_logs
        GROUP BY violation
        ORDER BY arrest_rate DESC
        LIMIT 5;
    """
}

if st.button("Run SQL Query"):
    result = fetch_data(query_map[selected_query])
    if not result.empty:
        st.dataframe(result, use_container_width=True)
    else:
        st.warning("No results found for the selected query.")


# Prediction section
st.markdown("---")
st.markdown("Built with ❤️ for Law Enforcement by SecureCheck")

st.header("📝 Add New Police Log & Predict Outcome and Violation")
st.markdown("Fill in the details below to get a prediction based on similar existing records.")

stop_duration_options = (
    sorted(data["stop_duration"].dropna().astype(str).unique().tolist())
    if "stop_duration" in data.columns
    else ["<5 min", "6-15 min", "16-30 min", "30+ min"]
)

with st.form("new_log_form"):
    stop_date = st.date_input("Stop Date")
    stop_time = st.time_input("Stop Time")
    country_name = st.text_input("Country Name")
    driver_gender = st.selectbox("Driver Gender", ["Male", "Female"])
    driver_age = st.number_input("Driver Age", min_value=16, max_value=100, value=27)
    driver_race = st.text_input("Driver Race")
    search_conducted = st.selectbox("Was a search conducted?", ["0", "1"])
    search_type = st.text_input("Search Type")
    drugs_related_stop = st.selectbox("Was it drug related?", ["0", "1"])
    stop_duration = st.selectbox("Stop Duration", stop_duration_options)
    vehicle_number = st.text_input("Vehicle Number")

    submitted = st.form_submit_button("Predict Stop Outcome & Violation")

    if submitted:
        filtered_data = data[
            (data["driver_gender"].astype(str) == driver_gender) &
            (pd.to_numeric(data["driver_age"], errors="coerce") == driver_age) &
            (data["search_conducted"].astype(str) == search_conducted) &
            (data["stop_duration"].astype(str) == stop_duration) &
            (data["drugs_related_stop"].astype(str) == drugs_related_stop)
        ]

        if not filtered_data.empty:
            predicted_outcome = filtered_data["stop_outcome"].mode().iloc[0]
            predicted_violation = filtered_data["violation"].mode().iloc[0]
        else:
            predicted_outcome = "Warning"
            predicted_violation = "Speeding"

        search_text = "A search was conducted" if search_conducted == "1" else "No search was conducted"
        drug_text = "was drug-related" if drugs_related_stop == "1" else "was not drug-related"

        st.success("Prediction generated successfully.")
        st.markdown(f"""
        ### 🚔 Prediction Summary

        - **Predicted Violation:** {predicted_violation}
        - **Predicted Stop Outcome:** {predicted_outcome}

        A **{driver_age}** year old **{driver_gender}** driver in **{country_name}**  
        was stopped at **{stop_time.strftime('%I:%M %p')}** on **{stop_date}**.  
        {search_text}, and the stop {drug_text}.  
        **Stop duration:** {stop_duration}  
        **Vehicle number:** {vehicle_number}
        """)