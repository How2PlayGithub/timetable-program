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
    current_p_idx = None

    with open(file_path, "r") as f:
        for line in f:
            raw_line = line.strip()

            if "INSTRUCTOR:" in raw_line:
                current_teacher = raw_line.split(":")[1].strip()
                teachers[current_teacher] = {d: [""] * 7 for d in days}
                current_p_idx = None
                continue

            if current_teacher and "|" in raw_line:
                if "Period" in raw_line or "+" in raw_line or "=" in raw_line:
                    continue

                pipe_content = raw_line.strip("|")
                parts = [p.strip() for p in pipe_content.split("|")]

                if not parts:
                    continue

                if parts[0].startswith("P"):
                    try:
                        current_p_idx = int(parts[0][1:]) - 1
                        for i, day in enumerate(days):
                            if i + 1 < len(parts):
                                val = parts[i + 1]
                                if val and val not in ["---", "-", "FREE", "None"]:
                                    teachers[current_teacher][day][current_p_idx] = val
                                else:
                                    teachers[current_teacher][day][current_p_idx] = ""
                    except (ValueError, IndexError):
                        current_p_idx = None

                elif current_p_idx is not None:
                    for i, day in enumerate(days):
                        if i + 1 < len(parts):
                            val = parts[i + 1]
                            if val and val not in ["---", "-", "FREE", "None"]:
                                existing = teachers[current_teacher][day][current_p_idx]
                                if existing:
                                    teachers[current_teacher][day][current_p_idx] = (
                                        existing + "\n" + val
                                    )
                                else:
                                    teachers[current_teacher][day][current_p_idx] = val
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
