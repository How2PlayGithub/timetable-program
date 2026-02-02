import sys
import os
import random
from tabulate import tabulate
from src.scheduler import Scheduler
from src.utils import (
    import_student_timetables,
    import_teacher_timetables,
    rebuild_sections_from_file,
)

OUTPUT_DIR = "./output"
OUTPUT_FILES = [
    os.path.join(OUTPUT_DIR, "roll_calls.txt"),
    os.path.join(OUTPUT_DIR, "student_timetables.txt"),
    os.path.join(OUTPUT_DIR, "teacher_timetables.txt"),
]


def ensure_output_dir():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)


def delete_output_files():
    ensure_output_dir()
    deleted_any = False
    for path in OUTPUT_FILES:
        if os.path.exists(path):
            os.remove(path)
            deleted_any = True
    if deleted_any:
        print("[System] Old output files deleted.")
    else:
        print("[System] No old output files found to delete.")


def options():
    while True:
        print("\n" + "═" * 40)
        print("      ACG SCHOOL MANAGEMENT SYSTEM      ")
        print("═" * 40)
        print(" 1. Generate & Save New Timetables (RESET output first)")
        print(" 2. View Student Timetable")
        print(" 3. View Teacher Timetable")
        print(" 4. View Class Roll & Details")
        print(" 5. IMPORT Data from Existing Files")
        print(" 6. Student Class Search")
        print(" 7. Exit")
        print("═" * 40)

        choice = input("Select an option (1-7): ").strip()

        if choice == "1":
            delete_output_files()

            school = Scheduler()
            if not school.load_resources():
                print("[Error] Could not load rooms/teachers JSON.")
                continue

            run(school)
            print("[Success] New files generated and saved.")

        elif choice == "2":
            school = Scheduler()
            if not school.load_resources():
                print("[Error] Could not load rooms/teachers JSON.")
                continue

            school.student_schedules = import_student_timetables(
                os.path.join(OUTPUT_DIR, "student_timetables.txt")
            )

            name = input("Enter Student Name: ").strip()
            matches = [
                k for k in school.student_schedules.keys() if k.lower() == name.lower()
            ]

            if matches:
                school.print_timetable(matches[0])
            else:
                print(f"No schedule for {name}")

        elif choice == "3":
            school = Scheduler()
            if not school.load_resources():
                print("[Error] Could not load rooms/teachers JSON.")
                continue

            school.teacher_grids = import_teacher_timetables(
                os.path.join(OUTPUT_DIR, "teacher_timetables.txt")
            )

            school.sections = rebuild_sections_from_file(
                os.path.join(OUTPUT_DIR, "roll_calls.txt"),
                school.teachers,
                school.rooms,
            )

            t_name_input = input("Enter Teacher Name: ").strip()

            match = next(
                (
                    name
                    for name in school.teacher_grids.keys()
                    if name.lower().replace(".", "")
                    == t_name_input.lower().replace(".", "")
                ),
                None,
            )

            if match:
                school.print_teacher_timetable(match)
            else:
                print(f"[Error] No classes found for teacher: {t_name_input}")

        elif choice == "4":
            school = Scheduler()
            if not school.load_resources():
                print("[Error] Could not load rooms/teachers JSON.")
                continue

            school.sections = rebuild_sections_from_file(
                os.path.join(OUTPUT_DIR, "roll_calls.txt"),
                school.teachers,
                school.rooms,
            )

            class_id = input("Enter Class ID (e.g., Mat-1): ").strip()
            section = next((s for s in school.sections if s.id == class_id), None)

            if section:
                print(f"\nROLL FOR {section.subject} ({section.id})")

                instr_name = (
                    section.instructor.name if section.instructor else "Unknown Teacher"
                )
                room_num = section.room.number if section.room else "Unknown Room"

                print(f"Teacher: {instr_name} | Room: {room_num}")
                print("-" * 30)
                for i, s in enumerate(sorted(section.students), 1):
                    print(f"{i}. {s}")
            else:
                print("[Error] Class ID not found.")

        elif choice == "5":
            school = Scheduler()
            if not school.load_resources():
                continue

            print("\n[System] Importing all data...")

            school.sections = rebuild_sections_from_file(
                os.path.join(OUTPUT_DIR, "roll_calls.txt"),
                school.teachers,
                school.rooms,
            )

            school.student_schedules = import_student_timetables(
                os.path.join(OUTPUT_DIR, "student_timetables.txt")
            )

            school.teacher_grids = import_teacher_timetables(
                os.path.join(OUTPUT_DIR, "teacher_timetables.txt")
            )

            print(
                f"[Success] Imported {len(school.sections)} sections and {len(school.teacher_grids)} teacher schedules."
            )

        elif choice == "6":
            school = Scheduler()
            if not school.load_resources():
                print("[Error] Could not load rooms/teachers JSON.")
                continue

            school.sections = rebuild_sections_from_file(
                os.path.join(OUTPUT_DIR, "roll_calls.txt"),
                school.teachers,
                school.rooms,
            )

            search_system(school)

        elif choice == "7":
            print("Goodbye!")
            sys.exit()


def search_system(school):
    print("\n" + "─" * 30)
    print("      STUDENT CLASS SEARCH      ")
    print("─" * 30)

    name = input("Enter Student Name (e.g., Student_1): ").strip()
    found_classes = [sec for sec in school.sections if name in sec.students]

    if found_classes:
        print(
            f"\n[Results] {name} is enrolled in the following {len(found_classes)} classes:"
        )
        print("-" * 50)
        for sec in found_classes:
            teacher_name = sec.instructor.name if sec.instructor else "Unknown Teacher"
            print(
                f"Class ID: {sec.id:<10} | Subject: {sec.subject:<15} | Teacher: {teacher_name}"
            )
        print("-" * 50)
        print("\nTip: Use Option 4 with these IDs to view the full class roll.")
    else:
        print(f"\n[!] No classes found for '{name}'.")


def run(school):
    ensure_output_dir()

    NUM_STUDENTS = int(input("Enter the number of students: "))

    topic_weights = {
        "Maths": 5.0,
        "Physics": 5.0,
        "Chemistry": 5.0,
        "Biology": 5.0,
        "Economics": 3.0,
        "Business Studies": 1.0,
        "Language": 3.0,
        "Psychology": 3.5,
        "Further Maths": 5.0,
        "Computer Science": 1.5,
        "History": 1.5,
        "Literature": 4.5,
        "Geography": 1.5,
        "Sociology": 1.0,
        "Accounting": 1.5,
        "Design Technology": 1.0,
        "Mixed Media": 1.0,
        "Painting": 1.0,
        "Music": 1.0,
        "Drama": 1.0,
        "Classics": 1.5,
    }

    topics, weights = list(topic_weights.keys()), list(topic_weights.values())
    student_data = {}

    MIN_SUBJECTS = 3
    MAX_SUBJECTS = 5

    for i in range(1, NUM_STUDENTS + 1):
        target = random.randint(MIN_SUBJECTS, MAX_SUBJECTS)

        pool = random.choices(topics, weights=weights, k=80)
        unique = []
        for item in pool:
            if item not in unique:
                unique.append(item)
            if len(unique) == target:
                break

        if len(unique) < target:
            remaining = [t for t in topics if t not in unique]
            random.shuffle(remaining)
            unique.extend(remaining[: (target - len(unique))])

        student_data[f"Student_{i}"] = unique

    school.solve(student_data)

    if NUM_STUDENTS >= 1:
        school.print_timetable("Student_1")

    school.save_all_data()

    if school.failed_requests:
        print("\n" + "!" * 20 + " FAILED REQUESTS SUMMARY " + "!" * 20)
        failure_table = []
        for fail in school.failed_requests:
            failure_table.append(
                [fail["name"], fail["failed_at"], ", ".join(fail["all_requested"])]
            )

        print(
            tabulate(
                failure_table,
                headers=["Student Name", "Failing Subject", "Full Request"],
                tablefmt="simple",
            )
        )

    success = (
        ((NUM_STUDENTS - len(school.failed_requests)) / NUM_STUDENTS) * 100
        if NUM_STUDENTS
        else 0
    )
    print(f"\nFinal Success Rate: {success:.2f}%")


if __name__ == "__main__":
    options()
