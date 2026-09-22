
import streamlit as st
import sqlite3
import pandas as pd
import io
import hashlib
from datetime import date

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="School ERP",
    page_icon="🎓",
    layout="wide"
)


# =========================================================
# DATABASE
# =========================================================

DB_FILE = "school.db"


def get_connection():
    return sqlite3.connect(DB_FILE)


def init_database():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT UNIQUE,
            name TEXT,
            father_name TEXT,
            mobile TEXT,
            email TEXT,
            course TEXT,
            college TEXT,
            dob TEXT,
            admission_date TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT,
            total_fee REAL,
            paid_fee REAL,
            pending_fee REAL,
            payment_date TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT,
            attendance_date TEXT,
            status TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS exams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT,
            subject TEXT,
            marks REAL,
            total_marks REAL,
            percentage REAL,
            grade TEXT
        )
    """)

    # Default login
    default_password = hashlib.sha256(
        "admin123".encode()
    ).hexdigest()

    cursor.execute(
        "SELECT * FROM users WHERE username=?",
        ("admin",)
    )

    if cursor.fetchone() is None:

        cursor.execute(
            "INSERT INTO users(username,password) VALUES (?,?)",
            ("admin", default_password)
        )

    conn.commit()
    conn.close()


init_database()


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def hash_password(password):

    return hashlib.sha256(
        password.encode()
    ).hexdigest()


def check_login(username, password):

    conn = get_connection()

    df = pd.read_sql_query(
        "SELECT * FROM users WHERE username=?",
        conn,
        params=(username,)
    )

    conn.close()

    if len(df) == 0:
        return False

    return df.iloc[0]["password"] == hash_password(password)


def calculate_grade(percentage):

    if percentage >= 90:
        return "A+"
    elif percentage >= 80:
        return "A"
    elif percentage >= 70:
        return "B"
    elif percentage >= 60:
        return "C"
    elif percentage >= 50:
        return "D"
    elif percentage >= 33:
        return "E"
    else:
        return "F"


def load_students():

    conn = get_connection()

    df = pd.read_sql_query(
        "SELECT * FROM students ORDER BY id DESC",
        conn
    )

    conn.close()

    return df


def load_fees():

    conn = get_connection()

    df = pd.read_sql_query(
        "SELECT * FROM fees ORDER BY id DESC",
        conn
    )

    conn.close()

    return df


def load_attendance():

    conn = get_connection()

    df = pd.read_sql_query(
        "SELECT * FROM attendance ORDER BY id DESC",
        conn
    )

    conn.close()

    return df


def load_exams():

    conn = get_connection()

    df = pd.read_sql_query(
        "SELECT * FROM exams ORDER BY id DESC",
        conn
    )

    conn.close()

    return df


# =========================================================
# LOGIN
# =========================================================

if "logged_in" not in st.session_state:

    st.session_state.logged_in = False


if not st.session_state.logged_in:

    st.title("🎓 School ERP Login")

    st.write("Login to Student Management System")

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:

        username = st.text_input(
            "Username"
        )

        password = st.text_input(
            "Password",
            type="password"
        )

        if st.button(
            "🔐 Login",
            type="primary",
            use_container_width=True
        ):

            if check_login(
                username,
                password
            ):

                st.session_state.logged_in = True

                st.rerun()

            else:

                st.error(
                    "Invalid username or password"
                )

    st.info(
        "Default Login: admin / admin123"
    )

    st.stop()


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title("🎓 SCHOOL ERP")

st.sidebar.success(
    "Logged in as Admin"
)

menu = st.sidebar.radio(
    "MAIN MENU",
    [
        "Dashboard",
        "Students",
        "Fees",
        "Attendance",
        "Exams & Results",
        "Reports",
        "Logout"
    ]
)


# =========================================================
# DASHBOARD
# =========================================================

if menu == "Dashboard":

    st.title("📊 Dashboard")

    students = load_students()
    fees = load_fees()
    attendance = load_attendance()
    exams = load_exams()

    total_students = len(students)

    total_fee = fees["total_fee"].sum() if len(fees) else 0

    paid_fee = fees["paid_fee"].sum() if len(fees) else 0

    pending_fee = fees["pending_fee"].sum() if len(fees) else 0

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "👨‍🎓 Students",
            total_students
        )

    with col2:
        st.metric(
            "💰 Total Fees",
            f"₹{total_fee:,.2f}"
        )

    with col3:
        st.metric(
            "✅ Paid",
            f"₹{paid_fee:,.2f}"
        )

    with col4:
        st.metric(
            "⏳ Pending",
            f"₹{pending_fee:,.2f}"
        )

    st.divider()

    st.subheader("📋 Recent Students")

    if len(students):

        st.dataframe(
            students.head(10),
            use_container_width=True
        )

    else:

        st.info(
            "No students available."
        )


# =========================================================
# STUDENTS
# =========================================================

elif menu == "Students":

    st.title("👨‍🎓 Student Management")

    student_menu = st.selectbox(
        "Select Action",
        [
            "Add Student",
            "Search Student",
            "Update Student",
            "Delete Student",
            "All Students"
        ]
    )

    # -----------------------------------------------------
    # ADD
    # -----------------------------------------------------

    if student_menu == "Add Student":

        st.subheader("➕ Add Student")

        col1, col2 = st.columns(2)

        with col1:

            student_id = st.text_input(
                "Student ID *"
            )

            name = st.text_input(
                "Student Name *"
            )

            father_name = st.text_input(
                "Father Name"
            )

            mobile = st.text_input(
                "Mobile"
            )

            email = st.text_input(
                "Email"
            )

        with col2:

            course = st.text_input(
                "Course"
            )

            college = st.text_input(
                "College / School"
            )

            dob = st.date_input(
                "Date of Birth",
                date(2000, 1, 1)
            )

            admission_date = st.date_input(
                "Admission Date",
                date.today()
            )

        if st.button(
            "💾 Save Student",
            type="primary"
        ):

            if not student_id.strip():

                st.error(
                    "Student ID is required."
                )

            elif not name.strip():

                st.error(
                    "Student Name is required."
                )

            else:

                try:

                    conn = get_connection()

                    conn.execute(
                        """
                        INSERT INTO students
                        (
                            student_id,
                            name,
                            father_name,
                            mobile,
                            email,
                            course,
                            college,
                            dob,
                            admission_date
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            student_id,
                            name,
                            father_name,
                            mobile,
                            email,
                            course,
                            college,
                            str(dob),
                            str(admission_date)
                        )
                    )

                    conn.commit()
                    conn.close()

                    st.success(
                        "✅ Student added successfully!"
                    )

                except sqlite3.IntegrityError:

                    st.error(
                        "Student ID already exists."
                    )

    # -----------------------------------------------------
    # SEARCH
    # -----------------------------------------------------

    elif student_menu == "Search Student":

        st.subheader("🔍 Search Student")

        search = st.text_input(
            "Student ID or Name"
        )

        if search:

            students = load_students()

            result = students[
                students["student_id"]
                .astype(str)
                .str.contains(
                    search,
                    case=False,
                    na=False
                )
                |
                students["name"]
                .astype(str)
                .str.contains(
                    search,
                    case=False,
                    na=False
                )
            ]

            if len(result):

                st.success(
                    f"{len(result)} student(s) found."
                )

                st.dataframe(
                    result,
                    use_container_width=True
                )

            else:

                st.warning(
                    "No student found."
                )

    # -----------------------------------------------------
    # UPDATE
    # -----------------------------------------------------

    elif student_menu == "Update Student":

        st.subheader("✏️ Update Student")

        students = load_students()

        if len(students):

            selected_id = st.selectbox(
                "Select Student",
                students["student_id"].tolist()
            )

            student = students[
                students["student_id"]
                == selected_id
            ].iloc[0]

            col1, col2 = st.columns(2)

            with col1:

                new_name = st.text_input(
                    "Name",
                    student["name"]
                )

                new_father = st.text_input(
                    "Father Name",
                    student["father_name"]
                )

                new_mobile = st.text_input(
                    "Mobile",
                    student["mobile"]
                )

                new_email = st.text_input(
                    "Email",
                    student["email"]
                )

            with col2:

                new_course = st.text_input(
                    "Course",
                    student["course"]
                )

                new_college = st.text_input(
                    "College",
                    student["college"]
                )

            if st.button(
                "🔄 Update Student",
                type="primary"
            ):

                conn = get_connection()

                conn.execute(
                    """
                    UPDATE students
                    SET name=?,
                        father_name=?,
                        mobile=?,
                        email=?,
                        course=?,
                        college=?
                    WHERE student_id=?
                    """,
                    (
                        new_name,
                        new_father,
                        new_mobile,
                        new_email,
                        new_course,
                        new_college,
                        selected_id
                    )
                )

                conn.commit()
                conn.close()

                st.success(
                    "✅ Student updated!"
                )

        else:

            st.info(
                "No students available."
            )

    # -----------------------------------------------------
    # DELETE
    # -----------------------------------------------------

    elif student_menu == "Delete Student":

        st.subheader("🗑️ Delete Student")

        students = load_students()

        if len(students):

            selected_id = st.selectbox(
                "Select Student",
                students["student_id"].tolist()
            )

            confirm = st.checkbox(
                "I confirm that I want to delete this student."
            )

            if st.button(
                "🗑️ Delete",
                type="primary"
            ):

                if not confirm:

                    st.warning(
                        "Please confirm deletion."
                    )

                else:

                    conn = get_connection()

                    conn.execute(
                        "DELETE FROM students WHERE student_id=?",
                        (selected_id,)
                    )

                    conn.commit()
                    conn.close()

                    st.success(
                        "Student deleted successfully."
                    )

        else:

            st.info(
                "No students available."
            )

    # -----------------------------------------------------
    # ALL
    # -----------------------------------------------------

    elif student_menu == "All Students":

        st.subheader("👨‍🎓 All Students")

        students = load_students()

        if len(students):

            st.dataframe(
                students,
                use_container_width=True,
                height=500
            )

        else:

            st.info(
                "No students available."
            )


# =========================================================
# FEES
# =========================================================

elif menu == "Fees":

    st.title("💰 Fees Management")

    fee_menu = st.selectbox(
        "Select Action",
        [
            "Add Fee Payment",
            "Fee Records"
        ]
    )

    students = load_students()

    if fee_menu == "Add Fee Payment":

        if len(students) == 0:

            st.warning(
                "Please add a student first."
            )

        else:

            selected_id = st.selectbox(
                "Student",
                students["student_id"].tolist()
            )

            total_fee = st.number_input(
                "Total Fee",
                min_value=0.0,
                value=0.0
            )

            paid_fee = st.number_input(
                "Paid Fee",
                min_value=0.0,
                value=0.0
            )

            payment_date = st.date_input(
                "Payment Date",
                date.today()
            )

            pending_fee = total_fee - paid_fee

            st.metric(
                "Pending Fee",
                f"₹{pending_fee:,.2f}"
            )

            if st.button(
                "💾 Save Fee",
                type="primary"
            ):

                if paid_fee > total_fee:

                    st.error(
                        "Paid fee cannot exceed total fee."
                    )

                else:

                    conn = get_connection()

                    conn.execute(
                        """
                        INSERT INTO fees
                        (
                            student_id,
                            total_fee,
                            paid_fee,
                            pending_fee,
                            payment_date
                        )
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            selected_id,
                            total_fee,
                            paid_fee,
                            pending_fee,
                            str(payment_date)
                        )
                    )

                    conn.commit()
                    conn.close()

                    st.success(
                        "✅ Fee payment saved."
                    )

    else:

        fees = load_fees()

        if len(fees):

            st.dataframe(
                fees,
                use_container_width=True
            )

        else:

            st.info(
                "No fee records available."
            )


# =========================================================
# ATTENDANCE
# =========================================================

elif menu == "Attendance":

    st.title("📅 Attendance Management")

    students = load_students()

    if len(students) == 0:

        st.warning(
            "Please add students first."
        )

    else:

        selected_id = st.selectbox(
            "Student",
            students["student_id"].tolist()
        )

        attendance_date = st.date_input(
            "Date",
            date.today()
        )

        status = st.selectbox(
            "Status",
            [
                "Present",
                "Absent"
            ]
        )

        if st.button(
            "💾 Save Attendance",
            type="primary"
        ):

            conn = get_connection()

            conn.execute(
                """
                INSERT INTO attendance
                (
                    student_id,
                    attendance_date,
                    status
                )
                VALUES (?, ?, ?)
                """,
                (
                    selected_id,
                    str(attendance_date),
                    status
                )
            )

            conn.commit()
            conn.close()

            st.success(
                "✅ Attendance saved."
            )

        st.divider()

        attendance = load_attendance()

        if len(attendance):

            st.dataframe(
                attendance,
                use_container_width=True
            )


# =========================================================
# EXAMS
# =========================================================

elif menu == "Exams & Results":

    st.title("📝 Exams & Results")

    students = load_students()

    if len(students) == 0:

        st.warning(
            "Please add students first."
        )

    else:

        selected_id = st.selectbox(
            "Student",
            students["student_id"].tolist()
        )

        subject = st.text_input(
            "Subject"
        )

        marks = st.number_input(
            "Obtained Marks",
            min_value=0.0,
            value=0.0
        )

        total_marks = st.number_input(
            "Total Marks",
            min_value=1.0,
            value=100.0
        )

        percentage = (
            marks / total_marks
        ) * 100

        grade = calculate_grade(
            percentage
        )

        st.info(
            f"Percentage: {percentage:.2f}% | Grade: {grade}"
        )

        if st.button(
            "💾 Save Result",
            type="primary"
        ):

            if marks > total_marks:

                st.error(
                    "Marks cannot exceed total marks."
                )

            elif not subject.strip():

                st.error(
                    "Subject is required."
                )

            else:

                conn = get_connection()

                conn.execute(
                    """
                    INSERT INTO exams
                    (
                        student_id,
                        subject,
                        marks,
                        total_marks,
                        percentage,
                        grade
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        selected_id,
                        subject,
                        marks,
                        total_marks,
                        percentage,
                        grade
                    )
                )

                conn.commit()
                conn.close()

                st.success(
                    "✅ Result saved."
                )

        st.divider()

        exams = load_exams()

        if len(exams):

            st.dataframe(
                exams,
                use_container_width=True
            )

        else:

            st.info(
                "No exam records available."
            )


# =========================================================
# REPORTS
# =========================================================

elif menu == "Reports":

    st.title("📄 Reports & Downloads")

    students = load_students()

    if len(students) == 0:

        st.info(
            "No student data available."
        )

    else:

        csv_data = students.to_csv(
            index=False
        ).encode("utf-8")

        excel_buffer = io.BytesIO()

        students.to_excel(
            excel_buffer,
            index=False,
            engine="openpyxl"
        )

        excel_buffer.seek(0)

        col1, col2 = st.columns(2)

        with col1:

            st.download_button(
                "📄 Download CSV",
                csv_data,
                "students.csv",
                "text/csv"
            )

        with col2:

            st.download_button(
                "📊 Download Excel",
                excel_buffer,
                "students.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        st.divider()

        def create_pdf():

            buffer = io.BytesIO()

            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=25,
                leftMargin=25,
                topMargin=25,
                bottomMargin=25
            )

            styles = getSampleStyleSheet()

            title = styles["Title"]
            title.alignment = TA_CENTER

            elements = []

            elements.append(
                Paragraph(
                    "SCHOOL ERP - STUDENT REPORT",
                    title
                )
            )

            elements.append(
                Spacer(1, 20)
            )

            table_data = [
                [
                    "Student ID",
                    "Name",
                    "Course",
                    "College"
                ]
            ]

            for _, row in students.iterrows():

                table_data.append(
                    [
                        str(row["student_id"]),
                        str(row["name"]),
                        str(row["course"]),
                        str(row["college"])
                    ]
                )

            table = Table(
                table_data,
                repeatRows=1
            )

            table.setStyle(
                TableStyle(
                    [
                        (
                            "BACKGROUND",
                            (0, 0),
                            (-1, 0),
                            colors.grey
                        ),
                        (
                            "TEXTCOLOR",
                            (0, 0),
                            (-1, 0),
                            colors.white
                        ),
                        (
                            "GRID",
                            (0, 0),
                            (-1, -1),
                            0.5,
                            colors.black
                        ),
                        (
                            "ALIGN",
                            (0, 0),
                            (-1, -1),
                            "CENTER"
                        ),
                        (
                            "FONTSIZE",
                            (0, 0),
                            (-1, -1),
                            8
                        )
                    ]
                )
            )

            elements.append(table)

            doc.build(elements)

            buffer.seek(0)

            return buffer

        pdf_file = create_pdf()

        st.download_button(
            "📄 Download PDF",
            pdf_file,
            "student_report.pdf",
            "application/pdf"
        )


# =========================================================
# LOGOUT
# =========================================================

elif menu == "Logout":

    st.session_state.logged_in = False

    st.rerun()
