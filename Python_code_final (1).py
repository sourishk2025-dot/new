import mysql.connector
import pandas as pd
import matplotlib.pyplot as plt
from sqlalchemy import create_engine

# ✅ SQLAlchemy engine for plotting with pandas
engine = create_engine("mysql+mysqlconnector://root:Nithin%4007@localhost/student_db")


# ======================= DB CONNECTION =======================
def connect_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Nithin@07",
        database="student_db"
    )


# ======================= TABLE CREATION =======================
def create_tables():
    con = connect_db()
    cur = con.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS college_students (
            ID INT PRIMARY KEY,
            name VARCHAR(100),
            sem_marks INT,
            attendance_percentage FLOAT,
            cgpa DECIMAL(4,2),
            weighted_cgpa DECIMAL(4,2),
            grade VARCHAR(3)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS student_marks (
            ID INT PRIMARY KEY,
            name VARCHAR(100),
            python FLOAT,
            basic_engineering FLOAT,
            chemistry FLOAT,
            physics FLOAT,
            computational FLOAT,
            FOREIGN KEY (ID) REFERENCES college_students(ID) ON DELETE CASCADE
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS top_performers (
            subject VARCHAR(50),
            ID INT,
            name VARCHAR(100),
            marks FLOAT
        )
    """)

    con.commit()
    cur.close()
    con.close()


# ======================= GRADE & CGPA =======================
def assign_grade(cgpa):
    if cgpa >= 9: return "S"
    elif cgpa >= 8: return "A"
    elif cgpa >= 7: return "B"
    elif cgpa >= 6: return "C"
    elif cgpa >= 5: return "D"
    else: return "F"


def compute_cgpa(marks):
    credit_map = {
        "python": 3,
        "basic_engineering": 3,
        "chemistry": 4,
        "physics": 4,
        "computational": 3
    }

    cgpa = sum(marks.values()) / len(marks) / 10
    total = sum((marks[s] / 10) * credit_map[s] for s in marks)
    weighted_cgpa = total / sum(credit_map.values())
    grade = assign_grade(weighted_cgpa)
    return cgpa, weighted_cgpa, grade


# ======================= MANUAL MARKS INPUT =======================
def input_marks(): #used during update marks fn and save marks fn
    print("\nEnter marks (out of 100) for:")
    subjects = ["python", "basic_engineering", "chemistry", "physics", "computational"]
    marks = {}
    for s in subjects:
        marks[s] = float(input(f"{s.title()}: "))
    return marks


# ======================= SAVE MARKS =======================
def save_marks(ID, name, marks):
    con = connect_db()
    cur = con.cursor()

    cur.execute("""
        INSERT INTO student_marks (ID, name, python, basic_engineering, chemistry, physics, computational)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            name=VALUES(name),
            python=VALUES(python),
            basic_engineering=VALUES(basic_engineering),
            chemistry=VALUES(chemistry),
            physics=VALUES(physics),
            computational=VALUES(computational)
    """, (ID, name, marks["python"], marks["basic_engineering"], marks["chemistry"],
          marks["physics"], marks["computational"]))
    con.commit()  # ✅ Immediate commit

    cur.close()
    con.close()

    


# ======================= ADD STUDENT =======================
def add_student(ID, name, semester, attendance):
    con = connect_db()
    cur = con.cursor()

    # Check existence
    cur.execute("SELECT * FROM college_students WHERE ID=%s", (ID,))
    if cur.fetchone():
        print("⚠ Student already exists.")
        con.close()
        return 



    # Insert student and commit immediately
    cur.execute("""
        INSERT INTO college_students (ID, name, sem_marks, attendance_percentage)
        VALUES (%s, %s, %s, %s)
    """, (ID, name, semester, attendance))
    con.commit()

    # Enter marks
    print(f"\nEnter marks for {name}:")
    marks = input_marks()

    # Save marks
    save_marks(ID, name, marks)

    # Compute CGPA & grade
    cgpa, weighted_cgpa, grade = compute_cgpa(marks)
    cur.execute("""
        UPDATE college_students
        SET cgpa=%s, weighted_cgpa=%s, grade=%s
        WHERE ID=%s
    """, (cgpa, weighted_cgpa, grade, ID))
    con.commit()

    cur.close()
    con.close()
    print("✅ Student added successfully with marks and CGPA/grade!")


# ======================= IMPORT CSV =======================
def import_students_and_marks(students_csv, marks_csv):
    con = connect_db()
    cur = con.cursor()

    # --- Students ---
    df_students = pd.read_csv(students_csv)
    for _, row in df_students.iterrows():
        ID = int(row["ID"])
        name = row["name"]
        semester = int(row.get("semester") or input(f"Enter semester for {name}: "))
        attendance = float(row.get("attendance_percentage") or input(f"Enter attendance % for {name}: "))

        cur.execute("SELECT * FROM college_students WHERE ID=%s", (ID,))
        if not cur.fetchone():
            cur.execute("""
                INSERT INTO college_students (ID, name, sem_marks, attendance_percentage)
                VALUES (%s, %s, %s, %s)
            """, (ID, name, semester, attendance))
        else:
            cur.execute("""
                UPDATE college_students
                SET name=%s, sem_marks=%s, attendance_percentage=%s
                WHERE ID=%s
            """, (name, semester, attendance, ID))
        con.commit()  # ✅ commit each student

    # --- Marks ---
    df_marks = pd.read_csv(marks_csv)
    for _, row in df_marks.iterrows():
        ID = int(row["ID"])
        name = row["name"]
        marks = {
            "python": float(row["python"]),
            "basic_engineering": float(row["basic_engineering"]),
            "chemistry": float(row["chemistry"]),
            "physics": float(row["physics"]),
            "computational": float(row["computational"])
        }

        # Ensure student exists
        cur.execute("SELECT ID FROM college_students WHERE ID=%s", (ID,))
        if not cur.fetchone():
            print(f"⚠ Student ID {ID} not found. Skipping marks.")
            continue

        # Save marks
        save_marks(ID, name, marks)

        # Update CGPA & grade
        cgpa, weighted_cgpa, grade = compute_cgpa(marks)
        cur.execute("""
            UPDATE college_students
            SET cgpa=%s, weighted_cgpa=%s, grade=%s
            WHERE ID=%s
        """, (cgpa, weighted_cgpa, grade, ID))
        con.commit()  # ✅ commit each student

    cur.close()
    con.close()
    print("✅ Students and marks imported successfully!")


# ======================= UPDATE STUDENT INFO =======================
def update_student_info(ID):
    con = connect_db()
    cur = con.cursor()
    cur.execute("SELECT name, sem_marks, attendance_percentage FROM college_students WHERE ID=%s", (ID,))
    result = cur.fetchone()

    if not result:
        print("❌ Student not found.")
        con.close()
        return

    name, sem_marks, attendance = result
    print(f"\nCurrent Info → Name: {name}, Semester: {sem_marks}, Attendance: {attendance}%")

    new_name = input(f"New Name (press Enter to keep '{name}'): ").strip() or name

    while True:
        new_sem = input(f"New Semester (press Enter to keep '{sem_marks}'): ").strip()
        if new_sem == "":
            new_sem = sem_marks
            break
        try:
            new_sem = int(new_sem)
            if new_sem <= 0:
                print("⚠ Semester must be positive.")
                continue
            break
        except ValueError:
            print("⚠ Invalid input. Enter an integer.")

    while True:
        new_att = input(f"New Attendance % (press Enter to keep '{attendance}'): ").strip()
        if new_att == "":
            new_att = attendance
            break
        try:
            new_att = float(new_att)
            if not (0 <= new_att <= 100):
                print("⚠ Attendance must be between 0 and 100.")
                continue
            break
        except ValueError:
            print("⚠ Invalid input. Enter a number.")

    cur.execute("""
        UPDATE college_students
        SET name=%s, sem_marks=%s, attendance_percentage=%s
        WHERE ID=%s
    """, (new_name, new_sem, new_att, ID))
    cur.execute("UPDATE student_marks SET name=%s WHERE ID=%s", (new_name, ID))

    con.commit()
    cur.close()
    con.close()
    print("✅ Student info updated successfully!")


# ======================= UPDATE MARKS =======================
def update_marks(ID):
    con = connect_db()
    cur = con.cursor()
    cur.execute("SELECT name, python, basic_engineering, chemistry, physics, computational FROM student_marks WHERE ID=%s", (ID,))
    result = cur.fetchone()

    if not result:
        print("❌ No marks found for this student. Please add first.")
        con.close()
        return

    name = result[0]
    subjects = ["python", "basic_engineering", "chemistry", "physics", "computational"]
    current_marks = dict(zip(subjects, result[1:]))

    print(f"\nCurrent marks for {name}:")
    for s, v in current_marks.items():
        print(f"  {s.title()}: {v}")

    print("\nEnter new marks (press Enter to keep existing):")
    new_marks = {}
    for s in subjects:
        val = input(f"{s.title()} (current {current_marks[s]}): ")
        new_marks[s] = float(val) if val.strip() != "" else current_marks[s]

    save_marks(ID, name, new_marks)

    cgpa, weighted_cgpa, grade = compute_cgpa(new_marks)
    cur.execute("""
        UPDATE college_students
        SET cgpa=%s, weighted_cgpa=%s, grade=%s
        WHERE ID=%s
    """, (cgpa, weighted_cgpa, grade, ID))
    con.commit()

    cur.close()
    con.close()
    print("✅ Marks updated successfully with recalculated CGPA and grade!")


# ======================= DELETE STUDENT =======================
def delete_student(ID):
    con = connect_db()
    cur = con.cursor()
    cur.execute("DELETE FROM college_students WHERE ID=%s", (ID,))
    con.commit()
    cur.close()
    con.close()
    print("✅ Student deleted!")


# ======================= VIEW FUNCTIONS =======================
def view_students():
    con = connect_db()
    cur = con.cursor()
    cur.execute("""
        SELECT 
            s.ID, s.name, s.sem_marks, s.attendance_percentage,
            s.cgpa, s.weighted_cgpa, s.grade,
            m.python, m.basic_engineering, m.chemistry, m.physics, m.computational
        FROM college_students s
        LEFT JOIN student_marks m ON s.ID = m.ID
        ORDER BY s.ID
    """)
    rows = cur.fetchall()
    print("\n=============== STUDENT RECORDS ===============")
    for r in rows:
        print(f"ID:{r[0]} | Name:{r[1]} | Sem:{r[2]} | Att:{r[3]}% | "
              f"CGPA:{r[4]} | WCGPA:{r[5]} | Grade:{r[6]} | "
              f"Marks -> Py:{r[7]}, Eng:{r[8]}, Chem:{r[9]}, Phy:{r[10]}, Comp:{r[11]}")
    print("===============================================\n")
    cur.close()
    con.close()


def view_student_by_id(ID):
    con = connect_db()
    cur = con.cursor()
    cur.execute("""
        SELECT 
            s.ID, s.name, s.sem_marks, s.attendance_percentage,
            s.cgpa, s.weighted_cgpa, s.grade,
            m.python, m.basic_engineering, m.chemistry, m.physics, m.computational
        FROM college_students s
        LEFT JOIN student_marks m ON s.ID = m.ID
        WHERE s.ID = %s
    """, (ID,))
    result = cur.fetchone()

    if not result:
        print("❌ No record found for this ID.")
    else:
        print("\n=============== STUDENT DETAILS ===============")
        print(f"ID: {result[0]}\nName: {result[1]}\nSemester: {result[2]}\nAttendance: {result[3]}%")
        print(f"CGPA: {result[4]} | Weighted CGPA: {result[5]} | Grade: {result[6]}")
        print(f"Marks → Python: {result[7]}, Basic Engg: {result[8]}, Chem: {result[9]}, "
              f"Physics: {result[10]}, Comp: {result[11]}")
        print("===============================================")
    cur.close()
    con.close()


# ======================= TOP PERFORMERS =======================
def store_and_display_top_performers():
    con = connect_db()
    cur = con.cursor()
    subjects = ["python", "basic_engineering", "chemistry", "physics", "computational"]
    cur.execute("DELETE FROM top_performers")
    con.commit()

    print("\n=============== TOP 3 PERFORMERS ===============")
    for sub in subjects:
        cur.execute(f"""
            SELECT ID, name, {sub} FROM student_marks
            ORDER BY {sub} DESC
            LIMIT 3
        """)
        top = cur.fetchall()
        for t in top:
            cur.execute("""
                INSERT INTO top_performers (subject, ID, name, marks)
                VALUES (%s, %s, %s, %s)
            """, (sub, t[0], t[1], t[2]))
        con.commit()
        print(f"\nTop 3 in {sub.title()}:")
        for t in top:
            print(f"ID:{t[0]} | Name:{t[1]} | Marks:{t[2]}")
    print("================================================\n")
    cur.close()
    con.close()


# ======================= LOW ATTENDANCE =======================
def warn_low_attendance():
    con = connect_db()
    cur = con.cursor()
    cur.execute("""
        SELECT ID, name, attendance_percentage
        FROM college_students
        WHERE attendance_percentage < 75
        ORDER BY attendance_percentage ASC
    """)
    rows = cur.fetchall()
    if not rows:
        print("\n✅ All students have attendance >= 75%\n")
    else:
        print("\n=============== LOW ATTENDANCE STUDENTS ===============")
        for r in rows:
            print(f"ID: {r[0]} | Name: {r[1]} | Attendance: {r[2]}%")
        print("=======================================================\n")
    cur.close()
    con.close()


# ======================= PLOTTING =======================
def plot_cgpa_distribution():
    df = pd.read_sql("SELECT cgpa FROM college_students", engine)
    plt.figure(figsize=(8, 5))
    plt.hist(df['cgpa'].dropna(), bins=10, color='skyblue', edgecolor='black')
    plt.title("CGPA Distribution of Students")
    plt.xlabel("CGPA")
    plt.ylabel("Number of Students")
    plt.show()


def plot_attendance_analysis():
    df = pd.read_sql("SELECT name, attendance_percentage FROM college_students", engine)
    plt.figure(figsize=(10, 6))
    plt.bar(df['name'], df['attendance_percentage'], color='orange')
    plt.axhline(y=75, color='r', linestyle='--', label="Minimum Attendance")
    plt.xticks(rotation=45)
    plt.ylabel("Attendance %")
    plt.title("Student Attendance")
    plt.legend()
    plt.show()


def plot_top_performers(subject):
    df = pd.read_sql(f"SELECT name, {subject} FROM student_marks ORDER BY {subject} DESC LIMIT 3", engine)
    plt.figure(figsize=(6, 4))
    plt.bar(df['name'], df[subject], color='green')
    plt.title(f"Top 3 Performers in {subject.title()}")
    plt.ylabel("Marks")
    plt.show()


# ======================= MENU =======================
def menu():
    create_tables()
    while True:
        print("""
======== STUDENT MANAGEMENT ========
1. Import CSV Files
2. Add Student (with Marks) 
3. View All Students
4. Update Marks
5. Delete Student
6. Update Student Info
7. View Student by ID
8. Low Attendance Warning 
9. Top 3 Performers in Each Subject
10.To Plot CGPA Distribution
11.To Plot Attendance Analysis
12.To Plot Top 3 Performers
13.Exit
""")
        ch = input("Enter Your Choice: ")

        if ch == '1':
            students_csv = input("Enter CSV path for college_students: ")
            marks_csv = input("Enter CSV path for student_marks: ")
            create_tables()
            import_students_and_marks(students_csv, marks_csv)
        elif ch == '2':
            ID = int(input("ID: "))
            name = input("Name: ")
            semester = int(input("Semester: "))
            attendance = float(input("Attendance %: "))
            add_student(ID, name, semester, attendance)
        elif ch == '3':
            view_students()
        elif ch == '4':
            update_marks(int(input("Enter Student ID to update marks: ")))
        elif ch == '5':
            delete_student(int(input("Enter Student ID to delete: ")))
        elif ch == '6':
            update_student_info(int(input("Enter Student ID to update info: ")))
        elif ch == '7':
            view_student_by_id(int(input("Enter Student ID to view details: ")))
        elif ch == '8':
            warn_low_attendance()
        elif ch == '9':
            store_and_display_top_performers()
        elif ch == '10':
            plot_cgpa_distribution()
        elif ch == '11':
            plot_attendance_analysis()
        elif ch == '12':
            subject = input("Enter subject (python/basic_engineering/chemistry/physics/computational): ").strip().lower()
            if subject in ["python", "basic_engineering", "chemistry", "physics", "computational"]:
                plot_top_performers(subject)
            else:
                print("❌ Invalid subject.")
        elif ch == '13':
            print("👋 Bye! Exiting program.")
            break
        else:
            print("❌ Invalid choice, please try again.")


# ======================= MAIN =======================
if __name__ == "__main__":
    menu()
