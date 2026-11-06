import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import openpyxl
from io import BytesIO

from database import create_database, add_student, get_students, update_student, delete_student

st.set_page_config(
    page_title="Student Analytics | Insight Studio",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# CONFIGURATION
# =========================================================

SUBJECTS = [
    "Mathematics_Marks",
    "Science_Marks",
    "English_Marks",
    "Computer_Science_Marks"
]

LABELS = {
    "Mathematics_Marks": "Mathematics",
    "Science_Marks": "Science",
    "English_Marks": "English",
    "Computer_Science_Marks": "Computer Science"
}

BANDS = ["Excellent", "Average", "Needs Improvement"]

BAND_COLORS = {
    "Excellent": "#35D9FF",
    "Average": "#9B87FF",
    "Needs Improvement": "#FFB454"
}

CHART_COLORS = ["#35D9FF", "#8B7CFF", "#32D6A0", "#FFB454"]

# =========================================================
# DATA LOADING — CSV + SQLITE DATABASE
# =========================================================

@st.cache_data
def load_csv_data():
    data = pd.read_csv("student_performance_final.csv")

    required = [
        "Student_ID",
        "Attendance_Percentage",
        "Study_Hours_Per_Day",
        *SUBJECTS
    ]

    missing = [col for col in required if col not in data.columns]

    if missing:
        raise ValueError("Missing columns: " + ", ".join(missing))

    for col in required[1:]:
        data[col] = pd.to_numeric(data[col], errors="coerce")

    data = data.dropna(subset=required).copy()
    return data


def prepare_student_data(data):
    data = data.copy()

    for col in ["Attendance_Percentage", "Study_Hours_Per_Day", *SUBJECTS]:
        data[col] = pd.to_numeric(data[col], errors="coerce")

    data = data.dropna(
        subset=["Student_ID", "Attendance_Percentage", "Study_Hours_Per_Day", *SUBJECTS]
    ).copy()

    if data.empty:
        data["Average_Marks"] = pd.Series(dtype=float)
        data["Performance_Category"] = pd.Series(dtype=str)
        return data

    data["Average_Marks"] = data[SUBJECTS].mean(axis=1)

    data["Performance_Category"] = np.select(
        [
            data["Average_Marks"] >= 75,
            data["Average_Marks"] >= 50
        ],
        ["Excellent", "Average"],
        default="Needs Improvement"
    )

    return data


try:
    create_database()
    csv_df = load_csv_data()

    # Read records entered through the website from SQLite.
    db_records = get_students()

    if db_records is None or db_records.empty:
        db_df = pd.DataFrame(columns=[
            "Student_ID", "Attendance_Percentage", "Study_Hours_Per_Day",
            *SUBJECTS
        ])
    else:
        db_df = db_records.rename(columns={
            "student_id": "Student_ID",
            "attendance": "Attendance_Percentage",
            "study_hours": "Study_Hours_Per_Day",
            "mathematics": "Mathematics_Marks",
            "science": "Science_Marks",
            "english": "English_Marks",
            "computer_science": "Computer_Science_Marks"
        })[
            ["Student_ID", "Attendance_Percentage", "Study_Hours_Per_Day", *SUBJECTS]
        ]

    # Combine the original sample CSV with newly entered database records.
    df = pd.concat([csv_df, db_df], ignore_index=True)
    df = prepare_student_data(df)

    if df.empty:
        st.error("No valid student records found in the CSV or database.")
        st.stop()

except Exception as e:
    st.error(
        "Data could not be loaded. Check student_performance_final.csv "
        "and database.py."
    )
    st.exception(e)
    st.stop()

# =========================================================
# THEME SELECTOR
# =========================================================

THEMES = {
    "Hybrid Premium": {
        "bg": "#0D1321",
        "panel": "#151E30",
        "panel2": "#1D2940",
        "text": "#F4F7FC",
        "muted": "#A4B1C7",
        "border": "#33425A",
        "accent": "#67DDF5",
        "accent2": "#A895FF",
        "hero1": "#172B46",
        "hero2": "#24516A",
        "sidebar": "#101827",
        "grid": "#33425A",
        "chart_text": "#E5EDF8",
        "glass": True,
        "light": False
    },

    "Glassmorphism": {
        "bg": "#0B1020",
        "panel": "#171D32",
        "panel2": "#202844",
        "text": "#F3F6FF",
        "muted": "#A7B3D0",
        "border": "#465171",
        "accent": "#72E4FF",
        "accent2": "#B49AFF",
        "hero1": "#242B50",
        "hero2": "#174B67",
        "sidebar": "#10172B",
        "grid": "#465171",
        "chart_text": "#E5ECFF",
        "glass": True,
        "light": False
    },

    "Futuristic Dark": {
        "bg": "#070B14",
        "panel": "#101827",
        "panel2": "#151F32",
        "text": "#EDF5FF",
        "muted": "#94A8C5",
        "border": "#283953",
        "accent": "#35D9FF",
        "accent2": "#9B87FF",
        "hero1": "#101D38",
        "hero2": "#123A52",
        "sidebar": "#0A1220",
        "grid": "#263750",
        "chart_text": "#DDEAFF",
        "glass": False,
        "light": False
    },

    "Light": {
        "bg": "#F2F5FA",
        "panel": "#FFFFFF",
        "panel2": "#EAF0F8",
        "text": "#18263B",
        "muted": "#667891",
        "border": "#D8E1ED",
        "accent": "#146DDF",
        "accent2": "#7657DC",
        "hero1": "#18375D",
        "hero2": "#246A91",
        "sidebar": "#11243D",
        "grid": "#DCE4EF",
        "chart_text": "#26364D",
        "glass": False,
        "light": True
    },

    "Minimal Premium": {
        "bg": "#F6F8FC",
        "panel": "#FFFFFF",
        "panel2": "#EEF2F8",
        "text": "#17243A",
        "muted": "#68778D",
        "border": "#DFE5EF",
        "accent": "#315EFB",
        "accent2": "#7188FF",
        "hero1": "#FFFFFF",
        "hero2": "#E8EEFF",
        "sidebar": "#FFFFFF",
        "grid": "#E3E8F0",
        "chart_text": "#26364D",
        "glass": False,
        "light": True
    }
}

theme = st.sidebar.selectbox(
    "Appearance",
    list(THEMES.keys())
)

T = THEMES[theme]
glass_mode = T["glass"]
light_mode = T["light"]

# =========================================================
# GLOBAL CSS
# =========================================================

st.markdown(
    f"""
    <style>
    @import url(
        'https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap'
    );

    :root {{
        --bg: {T["bg"]};
        --panel: {T["panel"]};
        --panel2: {T["panel2"]};
        --text: {T["text"]};
        --muted: {T["muted"]};
        --border: {T["border"]};
        --accent: {T["accent"]};
        --accent2: {T["accent2"]};
        --grid: {T["grid"]};
    }}

    html, body, [class*="css"] {{
        font-family: 'DM Sans', sans-serif;
    }}

    .stApp {{
        background:
            radial-gradient(
                ellipse at 5% 5%,
                {T["hero2"]}25 0%,
                transparent 38%
            ),
            radial-gradient(
                ellipse at 95% 35%,
                {T["accent2"]}12 0%,
                transparent 32%
            ),
            var(--bg);
        color: var(--text);
    }}

    .block-container {{
        max-width: 1500px;
        padding-top: 1.8rem;
        padding-bottom: 3rem;
    }}

    [data-testid="stHeader"] {{
        background: transparent;
    }}

    [data-testid="stSidebar"] {{
        background: {T["sidebar"]};
        border-right: 1px solid {T["border"]};
        {"backdrop-filter: blur(18px);" if glass_mode else ""}
    }}

    [data-testid="stSidebar"] * {{
        color: {"#17243A" if light_mode else "#EAF1FF"};
    }}

    [data-testid="stSidebar"] [data-baseweb="select"] > div {{
        background: {"#F1F4FA" if light_mode else "#1A2540"};
        border: 1px solid {T["border"]};
        border-radius: 11px;
    }}

    h1, h2, h3 {{
        font-family: 'Manrope', sans-serif !important;
        color: var(--text);
        letter-spacing: -0.035em;
    }}

    p, label {{
        color: var(--text);
    }}

    .brand {{
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 10px 2px 18px;
    }}

    .brandmark {{
        width: 44px;
        height: 44px;
        flex-shrink: 0;
        border-radius: 15px;
        display: grid;
        place-items: center;
        background: linear-gradient(
            135deg, var(--accent), var(--accent2)
        );
        color: #10172B;
        font-weight: 900;
        box-shadow: 0 0 25px {T["accent"]}25;
    }}

    .brandname {{
        font-size: 12px;
        font-weight: 800;
        letter-spacing: 1.1px;
        color: {"#17243A" if light_mode else "#F2F7FF"};
    }}

    .brandtag {{
        font-size: 9px;
        letter-spacing: 1.3px;
        color: {"#68778D" if light_mode else "#A7B7D5"};
        margin-top: 4px;
    }}

    .hero {{
        position: relative;
        overflow: hidden;
        padding: 32px;
        border-radius: 24px;
        margin-bottom: 26px;
        background: {"linear-gradient(125deg, #FFFFFF, #E8EEFF)" if theme == "Minimal Premium" else f"linear-gradient(120deg, {T['hero1']}, {T['hero2']}, {T['panel2']})"};
        border: 1px solid {T["border"] if theme == "Minimal Premium" else T["accent"] + "40"};
        box-shadow: 0 18px 55px #00000012;
        {"backdrop-filter: blur(18px);" if glass_mode else ""}
    }}

    .hero:after {{
        content: "";
        position: absolute;
        width: 190px;
        height: 190px;
        right: -45px;
        top: -65px;
        border-radius: 50%;
        border: 1px solid {T["accent"]}35;
        box-shadow:
            0 0 0 22px {T["accent"]}0D,
            0 0 0 44px {T["accent"]}08,
            0 0 0 66px {T["accent"]}05;
        pointer-events: none;
    }}

    .eyebrow {{
        color: {T["accent"]};
        font-size: 10px;
        letter-spacing: 2px;
        font-weight: 800;
        margin-bottom: 11px;
    }}

    .hero h1 {{
        color: {"#17243A" if theme == "Minimal Premium" else "#FFFFFF"} !important;
        font-size: clamp(25px, 3vw, 36px) !important;
        font-weight: 800 !important;
        margin: 0 0 12px !important;
        line-height: 1.25 !important;
    }}

    .hero p {{
        color: {"#52627A" if theme == "Minimal Premium" else "#D1DEF5"} !important;
        font-size: 13px;
        line-height: 1.8;
        max-width: 780px;
        margin: 0;
    }}

    .pills {{
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
        margin-top: 20px;
    }}

    .pill {{
        border: 1px solid {T["border"] if theme == "Minimal Premium" else T["accent"] + "50"};
        background: {"#FFFFFF" if theme == "Minimal Premium" else "#FFFFFF12"};
        color: {"#315EFB" if theme == "Minimal Premium" else "#E6F9FF"};
        border-radius: 30px;
        padding: 7px 11px;
        font-size: 9px;
        letter-spacing: 0.5px;
        {"backdrop-filter: blur(10px);" if glass_mode else ""}
    }}

    .kpi {{
        background: {"linear-gradient(145deg, " + T["panel"] + "E8, " + T["panel2"] + "B8)" if glass_mode else T["panel"]};
        border: 1px solid var(--border);
        border-radius: 19px;
        padding: 19px;
        min-height: 135px;
        box-shadow: 0 10px 30px #0000000C;
        {"backdrop-filter: blur(16px);" if glass_mode else ""}
        transition: border-color 0.2s ease,
                    transform 0.2s ease,
                    box-shadow 0.2s ease;
    }}

    .kpi:hover {{
        border-color: var(--accent);
        transform: translateY(-3px);
        box-shadow: 0 14px 35px #00000016;
    }}

    .kpihead {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 8px;
        color: var(--muted);
        font-size: 10px;
        font-weight: 800;
        letter-spacing: 0.7px;
    }}

    .kpiicon {{
        font-size: 21px;
    }}

    .kpivalue {{
        color: var(--accent);
        font-family: 'Manrope', sans-serif;
        font-size: clamp(23px, 2.2vw, 31px);
        font-weight: 800;
        margin-top: 14px;
        overflow-wrap: anywhere;
    }}

    .kpinote {{
        color: var(--muted);
        font-size: 10px;
        margin-top: 8px;
    }}

    .kicker {{
        color: var(--accent);
        font-size: 10px;
        letter-spacing: 1.8px;
        font-weight: 800;
        margin: 5px 0 8px;
    }}

    .stitle {{
        color: var(--text);
        font-family: 'Manrope', sans-serif;
        font-size: 20px;
        font-weight: 800;
        margin: 0 0 5px;
    }}

    .sdesc {{
        color: var(--muted);
        font-size: 12px;
        line-height: 1.7;
        margin: 0 0 16px;
    }}

    .insight {{
        background: {"linear-gradient(140deg, " + T["panel"] + "E8, " + T["panel2"] + "B5)" if glass_mode else T["panel"]};
        border: 1px solid var(--border);
        border-left: 3px solid var(--accent);
        padding: 15px;
        border-radius: 15px;
        min-height: 84px;
        box-shadow: 0 7px 24px #0000000C;
        {"backdrop-filter: blur(14px);" if glass_mode else ""}
    }}

    .ilabel {{
        color: var(--muted);
        font-size: 9px;
        letter-spacing: 1.1px;
        font-weight: 800;
    }}

    .ivalue {{
        color: var(--text);
        font-size: 14px;
        font-weight: 700;
        margin-top: 8px;
    }}

    .note {{
        background: linear-gradient(135deg, var(--panel2), var(--panel));
        border: 1px solid var(--border);
        border-radius: 15px;
        padding: 14px 16px;
        color: var(--muted);
        font-size: 11px;
        line-height: 1.8;
        box-shadow: 0 6px 22px #0000000A;
        {"backdrop-filter: blur(12px);" if glass_mode else ""}
    }}

    div[data-testid="stMetric"] {{
        background: var(--panel);
        border: 1px solid var(--border);
        padding: 15px;
        border-radius: 15px;
        box-shadow: 0 7px 20px #00000008;
    }}

    div[data-testid="stMetricLabel"] {{
        color: var(--muted);
    }}

    div[data-testid="stMetricValue"] {{
        color: var(--accent);
    }}

    div[data-testid="stDataFrame"] {{
        border: 1px solid var(--border);
        border-radius: 14px;
        overflow: hidden;
    }}

    .stButton button,
    .stDownloadButton button {{
        border-radius: 11px;
        font-weight: 700;
        border: 1px solid var(--border);
        transition: all 0.2s ease;
    }}

    .stButton button:hover,
    .stDownloadButton button:hover {{
        border-color: var(--accent);
        color: var(--accent);
        box-shadow: 0 5px 18px {T["accent"]}18;
    }}

    .stTabs [data-baseweb="tab-list"] {{
        gap: 7px;
        background: var(--panel2);
        border: 1px solid var(--border);
        padding: 5px;
        border-radius: 14px;
        {"backdrop-filter: blur(12px);" if glass_mode else ""}
    }}

    .stTabs [data-baseweb="tab"] {{
        border-radius: 9px;
        padding: 9px 14px;
        color: var(--text);
    }}

    .stTabs [aria-selected="true"] {{
        background: var(--panel);
        border-radius: 9px;
    }}

    [data-testid="stTextInput"] input,
    [data-testid="stNumberInput"] input {{
        background: var(--panel);
        color: var(--text);
        border-color: var(--border);
        border-radius: 10px;
    }}

    [data-testid="stSelectbox"] [data-baseweb="select"] > div {{
        background: var(--panel);
        border-color: var(--border);
        border-radius: 10px;
    }}

    [data-testid="stSlider"] {{
        color: var(--text);
    }}

    hr {{
        border-color: var(--border);
    }}

    footer {{
        visibility: hidden;
    }}

    @media (max-width: 768px) {{
        .block-container {{
            padding-top: 1rem;
        }}

        .hero {{
            padding: 23px 19px;
            border-radius: 18px;
        }}

        .kpi {{
            padding: 14px;
        }}
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:
    st.markdown(
        """
        <div class="brand">
            <div class="brandmark">SA</div>
            <div>
                <div class="brandname">STUDENT ANALYTICS</div>
                <div class="brandtag">INSIGHT STUDIO · 2026</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("---")
    st.markdown("### WORKSPACE")

    page = st.radio(
        "Navigate",
        [
            "Overview",
            "Add Student",
            "Manage Students",
            "CSV Import",
            "Excel Import",
            "Student Explorer",
            "Deep Analytics",
            "Project Notes"
        ],
        label_visibility="collapsed"
    )

    st.markdown("---")
    st.markdown("### DATA SNAPSHOT")
    st.markdown(f"**{len(df):,}** student records")
    st.caption("CSV sample + saved SQLite records")
    st.caption("Python-powered academic insights")
    st.markdown("---")
    st.caption(f"STUDENT ANALYTICS · {theme.upper()}")

# =========================================================
# SHARED METRICS
# =========================================================

subject_means = df[SUBJECTS].mean().sort_values()
avg_marks = df["Average_Marks"].mean()
avg_att = df["Attendance_Percentage"].mean()
avg_study = df["Study_Hours_Per_Day"].mean()

counts = (
    df["Performance_Category"]
    .value_counts()
    .reindex(BANDS, fill_value=0)
)

# =========================================================
# HELPER FUNCTIONS
# =========================================================

def hero(kicker, title, copy, pills):
    pill_html = "".join(
        f'<span class="pill">{p}</span>'
        for p in pills
    )

    st.markdown(
        f"""
        <div class="hero">
            <div class="eyebrow">{kicker}</div>
            <h1>{title}</h1>
            <p>{copy}</p>
            <div class="pills">{pill_html}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def section(title, desc, kicker="INSIGHT OVERVIEW"):
    st.markdown(
        f"""
        <div class="kicker">{kicker}</div>
        <div class="stitle">{title}</div>
        <div class="sdesc">{desc}</div>
        """,
        unsafe_allow_html=True
    )


def kpi(icon, label, value, note):
    st.markdown(
        f"""
        <div class="kpi">
            <div class="kpihead">
                <span>{label}</span>
                <span class="kpiicon">{icon}</span>
            </div>
            <div class="kpivalue">{value}</div>
            <div class="kpinote">{note}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def insight(label, value):
    st.markdown(
        f"""
        <div class="insight">
            <div class="ilabel">{label}</div>
            <div class="ivalue">{value}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def style_ax(ax, grid_axis="y"):
    ax.set_facecolor(T["panel"])
    ax.tick_params(colors=T["muted"], labelsize=9)

    ax.xaxis.label.set_color(T["muted"])
    ax.yaxis.label.set_color(T["muted"])
    ax.title.set_color(T["text"])

    for spine in ax.spines.values():
        spine.set_visible(False)

    ax.grid(
        axis=grid_axis,
        color=T["grid"],
        alpha=0.75,
        linewidth=0.7
    )

    ax.set_axisbelow(True)


def finish_chart(fig, ax):
    fig.patch.set_facecolor(T["panel"])
    ax.set_facecolor(T["panel"])
    fig.tight_layout()


def dataframe_to_excel(dataframe):
    """Convert a DataFrame to an in-memory .xlsx file."""
    output = BytesIO()
    dataframe.to_excel(output, index=False, engine="openpyxl")
    output.seek(0)
    return output.getvalue()

# =========================================================
# ADD STUDENT
# =========================================================

if page == "Add Student":

    hero(
        "DYNAMIC DATA ENTRY",
        "Add a student record.",
        "Enter a student's attendance, study time and subject marks. "
        "The record will be saved in the SQLite database and included "
        "in the dashboard automatically.",
        ["SQLITE DATABASE", "PERMANENT LOCAL SAVE", "LIVE DASHBOARD DATA"]
    )

    section(
        "Student information",
        "Student ID must be unique. Marks and attendance should be between 0 and 100.",
        "NEW RECORD"
    )

    with st.form("add_student_form", clear_on_submit=True):
        student_id = st.text_input(
            "Student ID",
            placeholder="e.g. STU201"
        ).strip()

        c1, c2 = st.columns(2)

        with c1:
            attendance = st.number_input(
                "Attendance (%)", min_value=0.0, max_value=100.0,
                value=75.0, step=0.5
            )
            study_hours = st.number_input(
                "Study hours per day", min_value=0.0, max_value=24.0,
                value=2.0, step=0.5
            )
            mathematics = st.number_input(
                "Mathematics marks", min_value=0.0, max_value=100.0,
                value=60.0, step=1.0
            )
            science = st.number_input(
                "Science marks", min_value=0.0, max_value=100.0,
                value=60.0, step=1.0
            )

        with c2:
            english = st.number_input(
                "English marks", min_value=0.0, max_value=100.0,
                value=60.0, step=1.0
            )
            computer_science = st.number_input(
                "Computer Science marks", min_value=0.0, max_value=100.0,
                value=60.0, step=1.0
            )

            average_preview = (
                mathematics + science + english + computer_science
            ) / 4
            st.metric("Preview average marks", f"{average_preview:.1f}/100")

        submitted = st.form_submit_button(
            "Save Student Record",
            width="stretch",
            type="primary"
        )

    if submitted:
        if not student_id:
            st.error("Please enter a Student ID.")
        elif student_id in df["Student_ID"].astype(str).values:
            st.error(
                "This Student ID already exists in the current dataset. "
                "Please use a different ID."
            )
        else:
            saved = add_student(
                student_id,
                attendance,
                study_hours,
                mathematics,
                science,
                english,
                computer_science
            )

            if saved:
                st.success(
                    f"Student {student_id} saved successfully! "
                    "The dashboard will include this record."
                )
                st.rerun()
            else:
                st.error(
                    "This Student ID already exists in the database. "
                    "Please use a unique ID."
                )

    st.info(
        "Note: Records added here are stored in students.db. "
        "They remain available when you restart the local app, "
        "as long as the database file is kept."
    )


# =========================================================
# MANAGE STUDENTS
# =========================================================

elif page == "Manage Students":

    hero(
        "RECORD MANAGEMENT",
        "Manage saved student records.",
        "Review records added through this website. You can update "
        "their marks and attendance or remove a saved record.",
        ["VIEW", "EDIT", "DELETE"]
    )

    saved_records = get_students()

    if saved_records.empty:
        st.info("No manually added student records yet. Use Add Student to create one.")
    else:
        section(
            "Saved database records",
            "Only records stored in the SQLite database are editable here. "
            "The original CSV sample records remain unchanged.",
            "DATABASE RECORDS"
        )

        display_records = saved_records.rename(columns={
            "student_id": "Student ID",
            "attendance": "Attendance (%)",
            "study_hours": "Study hours/day",
            "mathematics": "Mathematics",
            "science": "Science",
            "english": "English",
            "computer_science": "Computer Science"
        })

        st.dataframe(
            display_records,
            width="stretch",
            hide_index=True
        )

        student_options = saved_records["student_id"].astype(str).tolist()
        selected_student = st.selectbox(
            "Choose a Student ID to edit or delete",
            student_options
        )

        selected_row = saved_records[
            saved_records["student_id"].astype(str) == selected_student
        ].iloc[0]

        st.markdown("#### Update student details")

        with st.form("update_student_form"):
            c1, c2 = st.columns(2)

            with c1:
                new_attendance = st.number_input(
                    "Attendance (%)",
                    min_value=0.0, max_value=100.0,
                    value=float(selected_row["attendance"]), step=0.5,
                    key="edit_attendance"
                )
                new_study_hours = st.number_input(
                    "Study hours per day",
                    min_value=0.0, max_value=24.0,
                    value=float(selected_row["study_hours"]), step=0.5,
                    key="edit_study_hours"
                )
                new_mathematics = st.number_input(
                    "Mathematics marks",
                    min_value=0.0, max_value=100.0,
                    value=float(selected_row["mathematics"]), step=1.0,
                    key="edit_mathematics"
                )
                new_science = st.number_input(
                    "Science marks",
                    min_value=0.0, max_value=100.0,
                    value=float(selected_row["science"]), step=1.0,
                    key="edit_science"
                )

            with c2:
                new_english = st.number_input(
                    "English marks",
                    min_value=0.0, max_value=100.0,
                    value=float(selected_row["english"]), step=1.0,
                    key="edit_english"
                )
                new_computer_science = st.number_input(
                    "Computer Science marks",
                    min_value=0.0, max_value=100.0,
                    value=float(selected_row["computer_science"]), step=1.0,
                    key="edit_computer_science"
                )

            update_submitted = st.form_submit_button(
                "Update Student",
                width="stretch",
                type="primary"
            )

        if update_submitted:
            updated = update_student(
                selected_student,
                new_attendance,
                new_study_hours,
                new_mathematics,
                new_science,
                new_english,
                new_computer_science
            )

            if updated:
                st.success(f"Student {selected_student} updated successfully.")
                st.rerun()
            else:
                st.error("Student record could not be updated.")

        st.divider()
        st.warning(
            f"Delete permanently removes {selected_student} from the SQLite database."
        )

        confirm_delete = st.checkbox(
            f"I confirm that I want to delete {selected_student}",
            key="confirm_delete_student"
        )

        if st.button(
            "Delete Selected Student",
            disabled=not confirm_delete,
            type="secondary"
        ):
            deleted = delete_student(selected_student)

            if deleted:
                st.success(f"Student {selected_student} deleted.")
                st.rerun()
            else:
                st.error("Student record could not be deleted.")


# =========================================================
# CSV IMPORT
# =========================================================

elif page == "CSV Import":

    hero(
        "BULK DATA IMPORT",
        "Import student records from CSV.",
        "Upload a CSV file to add multiple student records to the SQLite database. "
        "Existing Student IDs are skipped to prevent duplicate records.",
        ["CSV UPLOAD", "DATA VALIDATION", "DUPLICATE CHECK"]
    )

    section(
        "1. Download the CSV template",
        "Use these exact column names in your file. Marks and attendance must be 0–100; study hours must be 0–24.",
        "IMPORT GUIDE"
    )

    import_columns = [
        "Student_ID",
        "Attendance_Percentage",
        "Study_Hours_Per_Day",
        *SUBJECTS
    ]

    template_df = pd.DataFrame(columns=import_columns)

    st.download_button(
        "Download CSV template",
        template_df.to_csv(index=False).encode("utf-8"),
        "student_import_template.csv",
        "text/csv",
        width="content"
    )

    st.divider()

    section(
        "2. Upload your completed CSV",
        "The app will check the required columns, empty values, numeric values, valid ranges and duplicate Student IDs before saving.",
        "UPLOAD FILE"
    )

    uploaded_file = st.file_uploader(
        "Choose a student CSV file",
        type=["csv"],
        key="student_csv_uploader"
    )

    if uploaded_file is not None:
        try:
            import_df = pd.read_csv(
                uploaded_file,
                dtype={"Student_ID": str}
            )

            missing_columns = [
                col for col in import_columns
                if col not in import_df.columns
            ]

            if missing_columns:
                st.error(
                    "Missing required columns: "
                    + ", ".join(missing_columns)
                )
            elif import_df.empty:
                st.warning("The uploaded CSV file contains no student records.")
            else:
                import_df = import_df[import_columns].copy()
                import_df["Student_ID"] = (
                    import_df["Student_ID"].astype("string").str.strip()
                )

                numeric_columns = [
                    "Attendance_Percentage",
                    "Study_Hours_Per_Day",
                    *SUBJECTS
                ]

                for col in numeric_columns:
                    import_df[col] = pd.to_numeric(
                        import_df[col],
                        errors="coerce"
                    )

                invalid_rows = import_df[
                    import_df["Student_ID"].isna()
                    | (import_df["Student_ID"] == "")
                    | import_df[numeric_columns].isna().any(axis=1)
                ]

                out_of_range = (
                    (import_df["Attendance_Percentage"] < 0)
                    | (import_df["Attendance_Percentage"] > 100)
                    | (import_df["Study_Hours_Per_Day"] < 0)
                    | (import_df["Study_Hours_Per_Day"] > 24)
                )

                for col in SUBJECTS:
                    out_of_range = (
                        out_of_range
                        | (import_df[col] < 0)
                        | (import_df[col] > 100)
                    )

                duplicate_in_file = import_df[
                    "Student_ID"
                ].duplicated(keep="first")

                if not invalid_rows.empty:
                    st.error(
                        f"{len(invalid_rows)} row(s) contain a blank Student ID "
                        "or missing/non-numeric values. Correct the CSV and upload it again."
                    )
                elif out_of_range.any():
                    st.error(
                        "Some values are outside the allowed ranges. "
                        "Attendance and subject marks must be 0–100; study hours must be 0–24."
                    )
                elif duplicate_in_file.any():
                    duplicate_ids = import_df.loc[
                        duplicate_in_file, "Student_ID"
                    ].tolist()
                    st.error(
                        "Duplicate Student IDs found inside the uploaded file: "
                        + ", ".join(duplicate_ids[:10])
                    )
                else:
                    existing_ids = set(
                        df["Student_ID"].astype(str).str.strip()
                    )
                    already_exists = import_df["Student_ID"].isin(existing_ids)
                    new_records = import_df.loc[~already_exists].copy()
                    duplicate_count = int(already_exists.sum())

                    st.write("**Import preview**")
                    st.dataframe(
                        new_records,
                        width="stretch",
                        hide_index=True
                    )

                    m1, m2, m3 = st.columns(3)
                    m1.metric("Rows in file", len(import_df))
                    m2.metric("New records", len(new_records))
                    m3.metric("Already existing IDs", duplicate_count)

                    if new_records.empty:
                        st.info(
                            "There are no new records to import. "
                            "All Student IDs already exist in the current dataset."
                        )
                    elif st.button(
                        "Import valid student records",
                        type="primary",
                        width="stretch",
                        key="confirm_csv_import"
                    ):
                        imported_count = 0
                        failed_count = 0

                        for _, row in new_records.iterrows():
                            saved = add_student(
                                str(row["Student_ID"]),
                                float(row["Attendance_Percentage"]),
                                float(row["Study_Hours_Per_Day"]),
                                float(row["Mathematics_Marks"]),
                                float(row["Science_Marks"]),
                                float(row["English_Marks"]),
                                float(row["Computer_Science_Marks"])
                            )

                            if saved:
                                imported_count += 1
                            else:
                                failed_count += 1

                        if imported_count:
                            st.success(
                                f"Successfully imported {imported_count} student record(s)."
                            )
                        if failed_count:
                            st.warning(
                                f"{failed_count} record(s) could not be saved, "
                                "possibly because their IDs already exist in the database."
                            )
                        st.rerun()

        except Exception as e:
            st.error("The CSV file could not be read. Please check its format.")
            st.exception(e)



# =========================================================
# EXCEL IMPORT
# =========================================================

elif page == "Excel Import":

    hero(
        "BULK DATA IMPORT",
        "Import student records from Excel.",
        "Upload an Excel workbook to add multiple student records to the SQLite database. "
        "Existing Student IDs are skipped to prevent duplicate records.",
        ["EXCEL UPLOAD", "DATA VALIDATION", "DUPLICATE CHECK"]
    )

    section(
        "1. Download the Excel template",
        "Use these exact column names. Attendance and marks must be 0–100; study hours must be 0–24.",
        "IMPORT GUIDE"
    )

    import_columns = [
        "Student_ID",
        "Attendance_Percentage",
        "Study_Hours_Per_Day",
        *SUBJECTS
    ]

    template_df = pd.DataFrame(columns=import_columns)

    st.download_button(
        "Download Excel template",
        dataframe_to_excel(template_df),
        "student_import_template.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        width="content"
    )

    st.divider()

    section(
        "2. Upload your completed Excel file",
        "The app checks required columns, empty values, numeric values, valid ranges and duplicate Student IDs.",
        "UPLOAD FILE"
    )

    uploaded_excel = st.file_uploader(
        "Choose an Excel workbook",
        type=["xlsx"],
        key="student_excel_uploader"
    )

    if uploaded_excel is not None:
        try:
            import_df = pd.read_excel(
                uploaded_excel,
                engine="openpyxl",
                dtype={"Student_ID": str}
            )

            missing_columns = [
                col for col in import_columns
                if col not in import_df.columns
            ]

            if missing_columns:
                st.error(
                    "Missing required columns: "
                    + ", ".join(missing_columns)
                )
            elif import_df.empty:
                st.warning("The uploaded Excel file contains no student records.")
            else:
                import_df = import_df[import_columns].copy()
                import_df["Student_ID"] = (
                    import_df["Student_ID"].astype("string").str.strip()
                )

                numeric_columns = [
                    "Attendance_Percentage",
                    "Study_Hours_Per_Day",
                    *SUBJECTS
                ]

                for col in numeric_columns:
                    import_df[col] = pd.to_numeric(
                        import_df[col],
                        errors="coerce"
                    )

                invalid_rows = import_df[
                    import_df["Student_ID"].isna()
                    | (import_df["Student_ID"] == "")
                    | import_df[numeric_columns].isna().any(axis=1)
                ]

                out_of_range = (
                    (import_df["Attendance_Percentage"] < 0)
                    | (import_df["Attendance_Percentage"] > 100)
                    | (import_df["Study_Hours_Per_Day"] < 0)
                    | (import_df["Study_Hours_Per_Day"] > 24)
                )

                for col in SUBJECTS:
                    out_of_range = (
                        out_of_range
                        | (import_df[col] < 0)
                        | (import_df[col] > 100)
                    )

                duplicate_in_file = import_df["Student_ID"].duplicated(
                    keep="first"
                )

                if not invalid_rows.empty:
                    st.error(
                        f"{len(invalid_rows)} row(s) contain a blank Student ID "
                        "or missing/non-numeric values. Correct the Excel file and upload it again."
                    )
                elif out_of_range.any():
                    st.error(
                        "Some values are outside the allowed ranges. "
                        "Attendance and subject marks must be 0–100; study hours must be 0–24."
                    )
                elif duplicate_in_file.any():
                    duplicate_ids = import_df.loc[
                        duplicate_in_file, "Student_ID"
                    ].tolist()
                    st.error(
                        "Duplicate Student IDs found inside the uploaded file: "
                        + ", ".join(duplicate_ids[:10])
                    )
                else:
                    existing_ids = set(
                        df["Student_ID"].astype(str).str.strip()
                    )
                    already_exists = import_df["Student_ID"].isin(existing_ids)
                    new_records = import_df.loc[~already_exists].copy()
                    duplicate_count = int(already_exists.sum())

                    st.write("**Import preview**")
                    st.dataframe(
                        new_records,
                        width="stretch",
                        hide_index=True
                    )

                    m1, m2, m3 = st.columns(3)
                    m1.metric("Rows in file", len(import_df))
                    m2.metric("New records", len(new_records))
                    m3.metric("Already existing IDs", duplicate_count)

                    if new_records.empty:
                        st.info(
                            "There are no new records to import. "
                            "All Student IDs already exist in the current dataset."
                        )
                    elif st.button(
                        "Import valid student records",
                        type="primary",
                        width="stretch",
                        key="confirm_excel_import"
                    ):
                        imported_count = 0
                        failed_count = 0

                        for _, row in new_records.iterrows():
                            saved = add_student(
                                str(row["Student_ID"]),
                                float(row["Attendance_Percentage"]),
                                float(row["Study_Hours_Per_Day"]),
                                float(row["Mathematics_Marks"]),
                                float(row["Science_Marks"]),
                                float(row["English_Marks"]),
                                float(row["Computer_Science_Marks"])
                            )

                            if saved:
                                imported_count += 1
                            else:
                                failed_count += 1

                        if imported_count:
                            st.success(
                                f"Successfully imported {imported_count} student record(s)."
                            )
                        if failed_count:
                            st.warning(
                                f"{failed_count} record(s) could not be saved, "
                                "possibly because their IDs already exist in the database."
                            )
                        st.rerun()

        except Exception as e:
            st.error("The Excel file could not be read. Please check that it is a valid .xlsx workbook.")
            st.exception(e)


# =========================================================
# OVERVIEW
# =========================================================

if page == "Overview":

    hero(
        "ACADEMIC INTELLIGENCE PLATFORM",
        "See the story behind the scores.",
        "A focused view of academic performance, attendance and "
        "study patterns — designed to make student data easier "
        "to explore and explain.",
        [
            f"{len(df):,} SAMPLE RECORDS",
            "4 SUBJECT AREAS",
            "INTERACTIVE ANALYTICS"
        ]
    )

    section(
        "At a glance",
        "A quick read of the dataset's key performance indicators."
    )

    cols = st.columns(4)

    with cols[0]:
        kpi(
            "👥", "STUDENT RECORDS", f"{len(df):,}",
            "Records included in this sample"
        )

    with cols[1]:
        kpi(
            "◷", "MEAN ATTENDANCE", f"{avg_att:.1f}%",
            "Average attendance percentage"
        )

    with cols[2]:
        kpi(
            "▤", "MEAN SCORE", f"{avg_marks:.1f}",
            "Average across four subjects"
        )

    with cols[3]:
        kpi(
            "✦", "EXCELLENT BAND", f"{counts['Excellent']:,}",
            "Average score of 75 or higher"
        )

    st.write("")

    left, right = st.columns([1.25, 1])

    with left:
        section(
            "Subject scorecard",
            "Mean marks by subject on a common 0–100 scale.",
            "SUBJECT COMPARISON"
        )

        fig, ax = plt.subplots(figsize=(8, 3.5))
        vals = subject_means.values
        labels = [LABELS[x] for x in subject_means.index]

        bars = ax.barh(
            labels,
            vals,
            color=CHART_COLORS,
            height=0.56
        )

        ax.set_xlim(0, 110)
        ax.set_xlabel("Mean marks · out of 100")

        style_ax(ax, "x")
        ax.grid(axis="y", visible=False)

        for bar, val in zip(bars, vals):
            ax.text(
                val + 1.3,
                bar.get_y() + bar.get_height() / 2,
                f"{val:.1f}",
                va="center",
                color=T["chart_text"],
                fontsize=9,
                fontweight="bold"
            )

        finish_chart(fig, ax)
        st.pyplot(fig, width="stretch")
        plt.close(fig)

    with right:
        section(
            "Performance mix",
            "Share of records in each score band.",
            "CATEGORY BREAKDOWN"
        )

        fig, ax = plt.subplots(figsize=(6, 3.5))
        vals = counts.values
        names = counts.index.tolist()

        wedges, _, _ = ax.pie(
            vals,
            labels=None,
            autopct="%1.0f%%",
            startangle=90,
            colors=[BAND_COLORS[x] for x in names],
            pctdistance=0.78,
            wedgeprops={
                "width": 0.34,
                "edgecolor": T["panel"],
                "linewidth": 3
            },
            textprops={
                "color": T["chart_text"],
                "fontsize": 9,
                "weight": "bold"
            }
        )

        ax.text(
            0, 0.06, f"{len(df):,}",
            ha="center", va="center",
            color=T["chart_text"], fontsize=22,
            fontweight="bold"
        )

        ax.text(
            0, -0.18, "STUDENTS",
            ha="center", va="center",
            color=T["muted"], fontsize=8
        )

        ax.legend(
            wedges,
            [
                f"{name} · {value}"
                for name, value in zip(names, vals)
            ],
            loc="lower center",
            bbox_to_anchor=(0.5, -0.18),
            frameon=False,
            labelcolor=T["muted"],
            fontsize=8
        )

        finish_chart(fig, ax)
        st.pyplot(fig, width="stretch")
        plt.close(fig)

    st.write("")

    section(
        "Attendance and academic scores",
        "Each dot represents one sample student. "
        "This view shows spread, not cause and effect.",
        "RELATIONSHIP EXPLORER"
    )

    fig, ax = plt.subplots(figsize=(11, 3.8))

    sns.scatterplot(
        data=df,
        x="Attendance_Percentage",
        y="Average_Marks",
        hue="Performance_Category",
        hue_order=BANDS,
        palette=BAND_COLORS,
        alpha=0.78,
        s=45,
        edgecolor="none",
        ax=ax
    )

    ax.set_xlabel("Attendance (%)")
    ax.set_ylabel("Average marks")
    ax.set_xlim(0, 105)
    ax.set_ylim(0, 105)

    style_ax(ax, "both")

    leg = ax.legend(
        title="Score band",
        frameon=False,
        fontsize=8,
        title_fontsize=8
    )

    if leg:
        for tx in leg.get_texts():
            tx.set_color(T["muted"])
        leg.get_title().set_color(T["muted"])

    finish_chart(fig, ax)
    st.pyplot(fig, width="stretch")
    plt.close(fig)

    best = subject_means.idxmax()
    low = subject_means.idxmin()

    a, b, c = st.columns(3)

    with a:
        insight(
            "HIGHEST SUBJECT MEAN",
            f"{LABELS[best]} · {subject_means[best]:.1f}"
        )

    with b:
        insight(
            "LOWEST SUBJECT MEAN",
            f"{LABELS[low]} · {subject_means[low]:.1f}"
        )

    with c:
        insight(
            "MEAN STUDY TIME",
            f"{avg_study:.2f} hours per day"
        )

    st.markdown(
        """
        <div class="note">
            DATA NOTE · This project uses randomly generated synthetic
            records for learning and demonstration. Results are not
            findings about a real student population. Correlation does
            not imply causation.
        </div>
        """,
        unsafe_allow_html=True
    )

# =========================================================
# STUDENT EXPLORER
# =========================================================

elif page == "Student Explorer":

    hero(
        "RECORDS & DISCOVERY",
        "Explore the student dataset.",
        "Search individual records, narrow the view by performance "
        "band and export filtered results.",
        [
            f"{len(df):,} RECORDS",
            "SEARCHABLE TABLE",
            "CSV EXPORT"
        ]
    )

    section(
        "Find a record",
        "Use the controls below to focus on the records you need.",
        "STUDENT EXPLORER"
    )

    c1, c2, c3 = st.columns([1.2, 1, 1])

    with c1:
        search = st.text_input(
            "Student ID",
            placeholder="e.g. S001"
        )

    with c2:
        band = st.selectbox(
            "Performance band",
            ["All bands"] + BANDS
        )

    with c3:
        min_att = st.slider(
            "Minimum attendance (%)",
            0, 100, 0
        )

    view = df.copy()

    if search:
        view = view[
            view["Student_ID"]
            .astype(str)
            .str.contains(search, case=False, na=False)
        ]

    if band != "All bands":
        view = view[view["Performance_Category"] == band]

    view = view[view["Attendance_Percentage"] >= min_att]

    m1, m2, m3 = st.columns(3)

    m1.metric("Matching records", f"{len(view):,}")

    m2.metric(
        "Mean marks",
        f"{view['Average_Marks'].mean():.1f}" if len(view) else "—"
    )

    m3.metric(
        "Mean attendance",
        f"{view['Attendance_Percentage'].mean():.1f}%"
        if len(view) else "—"
    )

    st.dataframe(
        view,
        width="stretch",
        hide_index=True
    )

    download_col1, download_col2 = st.columns(2)

    with download_col1:
        st.download_button(
            "Download filtered student report",
            view.to_csv(index=False).encode("utf-8"),
            "student_performance_filtered.csv",
            "text/csv",
            disabled=view.empty,
            width="stretch"
        )

    with download_col2:
        st.download_button(
            "Download complete student dataset",
            df.to_csv(index=False).encode("utf-8"),
            "student_performance_complete.csv",
            "text/csv",
            width="stretch"
        )


    st.write("")
    excel_col1, excel_col2 = st.columns(2)

    with excel_col1:
        st.download_button(
            "Download filtered Excel report",
            dataframe_to_excel(view),
            "student_performance_filtered.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            disabled=view.empty,
            width="stretch"
        )

    with excel_col2:
        st.download_button(
            "Download complete Excel dataset",
            dataframe_to_excel(df),
            "student_performance_complete.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            width="stretch"
        )

# =========================================================
# DEEP ANALYTICS
# =========================================================

elif page == "Deep Analytics":

    hero(
        "PATTERN & RELATIONSHIP LAB",
        "Go beyond the averages.",
        "Explore numeric relationships, inspect study-time "
        "patterns and understand attendance distribution.",
        ["CORRELATION", "DISTRIBUTION", "STUDY HABITS"]
    )

    tab1, tab2, tab3 = st.tabs(
        ["Correlation map", "Study habits", "Attendance profile"]
    )

    with tab1:
        section(
            "Correlation matrix",
            "Values range from −1 to +1. Values near zero "
            "indicate a weak linear relationship.",
            "RELATIONSHIP ANALYSIS"
        )

        corr = df.select_dtypes(include="number").corr()

        fig, ax = plt.subplots(figsize=(10, 6))

        sns.heatmap(
            corr,
            annot=True,
            fmt=".2f",
            cmap="coolwarm",
            center=0,
            vmin=-1,
            vmax=1,
            linewidths=0.7,
            linecolor=T["panel"],
            annot_kws={"size": 8},
            cbar_kws={"shrink": 0.8},
            ax=ax
        )

        ax.tick_params(colors=T["muted"], labelsize=8)
        ax.set_facecolor(T["panel"])

        plt.xticks(rotation=35, ha="right")
        plt.yticks(rotation=0)

        finish_chart(fig, ax)
        st.pyplot(fig, width="stretch")
        plt.close(fig)

    with tab2:
        section(
            "Study time and average marks",
            "The fitted line summarizes this sample; "
            "it is not a prediction model.",
            "STUDY HABITS"
        )

        fig, ax = plt.subplots(figsize=(10, 4.5))

        sns.regplot(
            data=df,
            x="Study_Hours_Per_Day",
            y="Average_Marks",
            scatter_kws={
                "alpha": 0.48,
                "s": 34,
                "color": T["accent"]
            },
            line_kws={
                "color": "#32D6A0",
                "linewidth": 2.2
            },
            ax=ax
        )

        ax.set_xlabel("Study hours per day")
        ax.set_ylabel("Average marks")

        style_ax(ax)
        finish_chart(fig, ax)

        st.pyplot(fig, width="stretch")
        plt.close(fig)

        study_corr = df["Study_Hours_Per_Day"].corr(
            df["Average_Marks"]
        )

        st.metric(
            "Pearson correlation · study time vs marks",
            f"{study_corr:.3f}" if pd.notna(study_corr) else "N/A"
        )

        st.markdown(
            """
            <div class="note">
                INTERPRETATION · A correlation close to zero indicates
                little linear association in this generated sample.
                It does not mean study time is unimportant in real
                educational settings.
            </div>
            """,
            unsafe_allow_html=True
        )

    with tab3:
        section(
            "Attendance distribution",
            "A histogram shows how attendance values are "
            "spread across the sample.",
            "ATTENDANCE PROFILE"
        )

        fig, ax = plt.subplots(figsize=(10, 4.2))

        sns.histplot(
            df["Attendance_Percentage"],
            bins=12,
            kde=True,
            color=T["accent"],
            edgecolor=T["panel"],
            ax=ax
        )

        ax.axvline(
            avg_att,
            color="#32D6A0",
            linestyle="--",
            linewidth=2,
            label=f"Mean · {avg_att:.1f}%"
        )

        ax.set_xlabel("Attendance percentage")
        ax.set_ylabel("Number of records")

        style_ax(ax)
        ax.legend(frameon=False, labelcolor=T["muted"])

        finish_chart(fig, ax)
        st.pyplot(fig, width="stretch")
        plt.close(fig)

        attendance_corr = df["Attendance_Percentage"].corr(
            df["Average_Marks"]
        )

        st.metric(
            "Attendance correlation with average marks",
            (
                f"{attendance_corr:.3f}"
                if pd.notna(attendance_corr)
                else "N/A"
            )
        )

# =========================================================
# PROJECT NOTES
# =========================================================

else:

    hero(
        "ABOUT THIS PROJECT",
        "A learning project with a data-first approach.",
        "A Python-based demonstration of data preparation, "
        "exploratory analysis and interactive reporting.",
        ["PYTHON", "PANDAS", "SEABORN", "STREAMLIT"]
    )

    section(
        "From raw records to readable insights",
        "The application loads a CSV, validates fields, "
        "calculates average marks, assigns performance bands "
        "and presents exploratory charts.",
        "PROJECT BRIEF"
    )

    st.markdown(
        """
        <div class="note">
            <b>PROJECT PURPOSE</b><br>
            Demonstrate a beginner-friendly data analytics workflow:
            data loading, validation, transformation, visualization,
            interactive reporting and local student-record management
            with SQLite.
        </div>
        """,
        unsafe_allow_html=True
    )

    st.write("")

    tech = st.columns(4)

    for col, name, desc in zip(
        tech,
        [
            "Python & Pandas",
            "Matplotlib",
            "Seaborn",
            "Streamlit"
        ],
        [
            "Data handling",
            "Chart rendering",
            "Statistical visuals",
            "Interactive web app"
        ]
    ):
        with col:
            st.markdown(
                f"""
                <div class="insight">
                    <div class="ilabel">TECHNOLOGY</div>
                    <div class="ivalue">{name}</div>
                    <div style="
                        color:{T['muted']};
                        font-size:10px;
                        margin-top:5px
                    ">{desc}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

    st.write("")

    section(
        "Analysis workflow",
        "The steps followed in this project.",
        "METHOD"
    )

    st.markdown(
        """
        1. **Load** — read the CSV dataset with Pandas.
        2. **Validate** — check required columns and incomplete rows.
        3. **Transform** — calculate average marks and performance categories.
        4. **Explore** — compare subjects and inspect distributions and correlations.
        5. **Communicate** — present findings through an interactive dashboard.
        """
    )

    st.warning(
        "DATASET LIMITATION · Records are synthetic and randomly "
        "generated for educational demonstration. They are not real "
        "student records, and this dashboard is not a grading or "
        "prediction system."
    )

# =========================================================
# FOOTER
# =========================================================

st.markdown("---")

st.markdown(
    f"""
    <div style="
        display:flex;
        justify-content:space-between;
        gap:12px;
        flex-wrap:wrap;
        color:{T['muted']};
        font-size:10px;
        padding:4px 2px 12px;
    ">
        <span>
            <b style="color:{T['text']}">STUDENT ANALYTICS</b>
            · INSIGHT STUDIO
        </span>
        <span>
            Python · Pandas · Matplotlib · Seaborn · Streamlit
        </span>
        <span>SYNTHETIC DATA · EDUCATIONAL USE</span>
    </div>
    """,
    unsafe_allow_html=True
)
