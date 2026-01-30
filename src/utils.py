import os
from src.models import Section


def rebuild_sections_from_file(file_path, teachers_list, rooms_list):
    if not os.path.exists(file_path):
        return []

    sections = []
    with open(file_path, "r") as f:
        lines = f.readlines()

    current_sec = None
    for line in lines:
        if line.startswith("ID:"):
            parts = [p.strip() for p in line.split("|")]
            sec_id = parts[0].replace("ID:", "").strip()
            subject = parts[1]
            t_name = parts[2]
            r_num = parts[3]

            instructor = next((t for t in teachers_list if t.name == t_name), None)
            room = next((r for r in rooms_list if r.number == r_num), None)

            if instructor is None:
                from src.models import Instructor

                instructor = Instructor(t_name, [subject])

            if room is None:
                from src.models import Room

                room = Room(r_num, "Unknown", 30)

            current_sec = Section(sec_id, subject, instructor, room)
            sections.append(current_sec)

        elif line.startswith("Students:") and current_sec:
            student_list = [
                s.strip() for s in line.replace("Students:", "").split(",") if s.strip()
            ]
            current_sec.students = student_list

    return sections


def import_student_timetables(file_path):
    if not os.path.exists(file_path):
        return {}

    schedules = {}
    current_student = None
    days = ["Mon", "Tue", "Wed", "Thu", "Fri"]

    with open(file_path, "r") as f:
        for line in f:
            if line.startswith("STUDENT:"):
                current_student = line.split(":")[1].strip()
                schedules[current_student] = {d: [None] * 7 for d in days}
            elif current_student and "|" in line and "Period" not in line:
                parts = [p.strip() for p in line.split("|") if p.strip()]
                if parts and parts[0].startswith("P"):
                    p_idx = int(parts[0][1:]) - 1
                    for i, day in enumerate(days):
                        val = parts[i + 1]
                        schedules[current_student][day][p_idx] = (
                            None if val in ["None", "FREE", "-", "---"] else val
                        )
    return schedules


def import_teacher_timetables(file_path):
    if not os.path.exists(file_path):
        return {}

    teachers = {}
    current_teacher = None
    days = ["Mon", "Tue", "Wed", "Thu", "Fri"]

    with open(file_path, "r") as f:
        content = f.read().split("=" * 30)

    for block in content:
        lines = block.strip().split("\n")
        if lines[0].startswith("INSTRUCTOR:"):
            name = lines[0].split(":")[1].strip()
            teachers[name] = {d: [None] * 7 for d in days}

            for line in lines:
                if "|" in line and any(
                    p in line for p in ["P1", "P2", "P3", "P4", "P5", "P6", "P7"]
                ):
                    parts = [p.strip() for p in line.split("|") if p.strip()]
                    p_idx = int(parts[0][1:]) - 1
                    for i, day in enumerate(days):
                        val = parts[i + 1]
                        teachers[name][day][p_idx] = None if val == "---" else val
    return teachers


def import_class_rolls(file_path):
    if not os.path.exists(file_path):
        return {}

    rolls = {}
    current_id = None

    with open(file_path, "r") as f:
        for line in f:
            if line.startswith("ID:"):
                current_id = line.split("|")[0].replace("ID:", "").strip()
            elif line.startswith("Students:") and current_id:
                student_str = line.replace("Students:", "").strip()
                rolls[current_id] = [
                    s.strip() for s in student_str.split(",") if s.strip()
                ]

    return rolls
