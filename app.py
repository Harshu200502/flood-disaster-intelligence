import streamlit as st
from datetime import date
from weather_data import get_weather_data

st.set_page_config(
    page_title="FloodLens AI",
    page_icon="🌧️",
    layout="wide",
)

st.title("🌧️ FloodLens AI")
st.caption("Flood Disaster Intelligence and Live Weather Connector")

st.info(
    "Weather information is model-based. It is not verified flood "
    "observations and must not be treated as confirmation of flooding."
)

# --------------------------------------------------
# FLOOD SCENARIO
# --------------------------------------------------

st.sidebar.header("Flood Scenario")

with st.sidebar.form("flood_scenario_form"):
    location = st.text_input(
        "Location",
        value="Chennai, Tamil Nadu",
        help="Enter a city and state, for example Chennai, Tamil Nadu.",
    )

    event_date = st.date_input(
        "Scenario date",
        value=date.today(),
    )

    rainfall_mm = st.number_input(
        "Scenario rainfall (mm)",
        min_value=0.0,
        max_value=2000.0,
        value=0.0,
        step=5.0,
    )

    river_level_m = st.number_input(
        "River level (m, if known)",
        min_value=0.0,
        max_value=100.0,
        value=0.0,
        step=0.1,
    )

    scenario_submitted = st.form_submit_button(
        "Save Flood Scenario",
        type="primary",
    )

if scenario_submitted:
    st.session_state["scenario"] = {
        "location": location.strip(),
        "event_date": event_date.isoformat(),
        "rainfall_mm": rainfall_mm,
        "river_level_m": river_level_m,
    }
    st.session_state.pop("live_weather", None)
    st.session_state.pop("weather_error", None)
    st.success("Flood scenario saved.")

scenario = st.session_state.get("scenario")

if scenario:
    st.subheader("Selected Flood Scenario")
    st.write(f"**Location:** {scenario['location']}")
    st.write(f"**Scenario date:** {scenario['event_date']}")
    st.write(f"**Scenario rainfall:** {scenario['rainfall_mm']} mm")
    st.write(f"**River level:** {scenario['river_level_m']} m")

# --------------------------------------------------
# LIVE WEATHER
# --------------------------------------------------

st.divider()
st.header("Live Weather")

st.write(
    "Fetch current weather-model estimates for the location "
    "saved in your flood scenario."
)

if st.button("Fetch Live Weather", type="secondary"):
    selected_location = (
        scenario["location"] if scenario else location.strip()
    )

    if not selected_location:
        st.session_state["weather_error"] = (
            "Please enter a location and save the flood scenario first."
        )
        st.session_state.pop("live_weather", None)
    else:
        with st.spinner(
            f"Fetching weather for {selected_location}..."
        ):
            try:
                weather = get_weather_data(selected_location)
                st.session_state["live_weather"] = weather
                st.session_state.pop("weather_error", None)
            except Exception as exc:
                st.session_state["weather_error"] = str(exc)
                st.session_state.pop("live_weather", None)

if st.session_state.get("weather_error"):
    st.error(
        "Could not fetch live weather: "
        + st.session_state["weather_error"]
    )

weather = st.session_state.get("live_weather")

if weather:
    st.success(
        f"Weather retrieved for {weather['location']}"
    )

    st.caption(
        f"Model time: {weather['model_time']} | "
        f"Source: {weather['source']}"
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Temperature",
        f"{weather['temperature_c']} °C"
        if weather.get("temperature_c") is not None
        else "Unavailable",
    )

    col2.metric(
        "Humidity",
        f"{weather['relative_humidity_percent']}%"
        if weather.get("relative_humidity_percent") is not None
        else "Unavailable",
    )

    col3.metric(
        "Current precipitation",
        f"{weather['current_precipitation_mm']} mm"
        if weather.get("current_precipitation_mm") is not None
        else "Unavailable",
    )

    rainfall_24h = weather.get(
        "estimated_precipitation_last_24h_mm"
    )

    col4.metric(
        "Estimated rainfall (24h)",
        f"{rainfall_24h} mm"
        if rainfall_24h is not None
        else "Unavailable",
    )

    st.caption(weather["limitations"])

    with st.expander("Weather data details"):
        st.json(weather)

# --------------------------------------------------
# IMPORTANT LIMITATIONS
# --------------------------------------------------

st.divider()
st.subheader("Important Limitations")

st.markdown(
    """
    - Live weather values are weather-model estimates, not necessarily
      local rain-gauge measurements.
    - Current weather is not historical weather for the selected
      scenario date.
    - Rainfall alone does not confirm a flood.
    - This simplified version does not calculate a validated flood-risk
      score or generate an AI flood report.
    """
)
