import random
import os
import math
import json
import copy
from tabulate import tabulate
from .models import Room, Instructor, Section


class MasterSystem:
    def __init__(self):
        self.days = ["Mon", "Tue", "Wed", "Thu", "Fri"]
        self.period_counts = {"Mon": 6, "Tue": 7, "Wed": 6, "Thu": 6, "Fri": 6}
        self.subject_requirements = {
            "Chemistry": "Lab",
            "Physics": "Lab",
            "Biology": "Lab",
            "Computer Science": "General",
            "Economics": "General",
            "History": "General",
            "Accounting": "General",
            "Geography": "General",
            "Business Studies": "General",
            "Psychology": "General",
            "Classics": "General",
            "Sociology": "General",
            "Literature": "General",
            "Language": "General",
            "Maths": "General",
            "Further Maths": "General",
            "Design Technology": "DT Room",
            "Mixed Media": "Art",
            "Painting": "Art",
            "Music": "General",
            "Drama": "Drama",
        }
        self.teachers = []
        self.rooms = []
        self.sections = []
        self.student_schedules = {}
        self.failed_requests = []

    def load_resources(self):
        if os.path.exists("rooms.json") and os.path.exists("teachers.json"):
            try:
                with open("rooms.json", "r") as f:
                    room_data = json.load(f)

                    self.rooms = [
                        Room(
                            room_number,
                            data["type"],
                            data["capacity"],
                            data.get("preferred_subjects", []),
                        )
                        for room_number, data in room_data.items()
                    ]

                with open("teachers.json", "r") as f:
                    teacher_data = json.load(f)
                    self.teachers = [Instructor(k, v) for k, v in teacher_data.items()]

                if not self.rooms or not self.teachers:
                    print("[Error] Resource files loaded but contain no data.")
                    return False

                print(
                    f"[System] Resources loaded: {len(self.rooms)} rooms, {len(self.teachers)} teachers."
                )
                return True
            except Exception as e:
                print(f"[Error] Failed to parse JSON: {e}")
                return False
        else:
            print("[Error] rooms.json or teachers.json not found in directory.")
            return False


class Scheduler(MasterSystem):
    def __init__(self):
        super().__init__()
        self.patterns = self._generate_all_patterns()

    def _generate_all_patterns(self):
        patterns = []
        for _ in range(500):
            extended_p = []
            for d in self.days:
                if d == "Fri":
                    continue
                last_p = self.period_counts[d] - 1
                extended_p.append((d, last_p))
            patterns.append(extended_p)

            standard_p = []
            for d in self.days:
                last_p = self.period_counts[d] - 1
                possible = [i for i in range(last_p) if not (d == "Tue" and i == 1)]
                standard_p.append((d, random.choice(possible)))
            patterns.append(standard_p)

        return patterns

    def solve(self, student_requests, max_attempts=200):
        print("\n" + "=" * 60 + "\n TIMETABLE GENERATOR STARTING\n" + "=" * 60)

        self.student_schedules = {}
        self.failed_requests = []
        self.sections = []

        counts = {}
        for subs in student_requests.values():
            for s in subs:
                counts[s] = counts.get(s, 0) + 1

        total_students = len(student_requests)

        divisor = 8 if total_students <= 120 else 12

        section_plan = {
            sub: max(2, math.ceil(count / divisor)) for sub, count in counts.items()
        }

        best = None

        for attempt in range(1, max_attempts + 1):
            self.patterns = self._generate_all_patterns()

            self.sections = []
            teacher_load = {}

            for sub, count in counts.items():
                possible_teachers = [t for t in self.teachers if sub in t.subjects]
                if not possible_teachers:
                    continue

                preferred_rooms = [r for r in self.rooms if sub in r.preferred_subjects]
                if preferred_rooms:
                    selected_rooms_pool = preferred_rooms
                else:
                    req_type = self.subject_requirements.get(sub, "General")
                    selected_rooms_pool = [r for r in self.rooms if r.type == req_type]

                if not selected_rooms_pool:
                    continue

                num_sections = section_plan.get(sub, 2)

                for i in range(1, num_sections + 1):
                    possible_teachers_sorted = sorted(
                        possible_teachers,
                        key=lambda t: teacher_load.get((t.name, sub), 0),
                    )
                    selected_teacher = possible_teachers_sorted[0]
                    teacher_load[(selected_teacher.name, sub)] = (
                        teacher_load.get((selected_teacher.name, sub), 0) + 1
                    )

                    selected_room = random.choice(selected_rooms_pool)

                    sub_parts = sub.split()
                    prefix = (
                        (sub_parts[0][:3] + sub_parts[1][:2])
                        if len(sub_parts) > 1
                        else sub[:5]
                    )
                    section_id = f"{prefix}-{i}"

                    self.sections.append(
                        Section(section_id, sub, selected_teacher, selected_room)
                    )

            if not self.sections:
                print("[Error] No sections created. Termination.")
                return

            slot_usage = {}
            teacher_usage = {}
            room_usage = {}
            pattern_usage = {}

            from collections import defaultdict

            sub_to_sections = defaultdict(list)
            for sec in self.sections:
                sub_to_sections[sec.subject].append(sec)

            for subject, sections in sub_to_sections.items():
                for sec in sections:
                    best_pattern = None
                    min_cost = float("inf")

                    random.shuffle(self.patterns)
                    for p in self.patterns:
                        cost = 0
                        p_key = tuple(p)
                        reuse = pattern_usage.get(p_key, 0)

                        is_extended = any(d == "Mon" and s == 5 for d, s in p)

                        for slot in p:
                            cost += slot_usage.get(slot, 0) * 1000

                            if (sec.instructor.name, slot) in teacher_usage:
                                cost += 100000
                            if (sec.room.number, slot) in room_usage:
                                cost += 100000

                        cost += reuse * 2500
                        if len(sections) == 1:
                            cost += reuse * 9000

                        if len(sections) == 1 and is_extended:
                            cost += 5000

                        if cost < min_cost:
                            min_cost = cost
                            best_pattern = p

                    sec.slots = best_pattern

                    for slot in best_pattern:
                        slot_usage[slot] = slot_usage.get(slot, 0) + 1
                        teacher_usage[(sec.instructor.name, slot)] = True
                        room_usage[(sec.room.number, slot)] = True

                    b_key = tuple(best_pattern)
                    pattern_usage[b_key] = pattern_usage.get(b_key, 0) + 1

            self._assign_students(student_requests)

            failed = len(self.failed_requests)
            if failed == 0:
                if attempt > 1:
                    print(
                        f"[System] Solved with 100% success on attempt {attempt}/{max_attempts}."
                    )
                return

            if best is None or failed < best["failed_count"]:
                best = {
                    "failed_count": failed,
                    "failed_requests": copy.deepcopy(self.failed_requests),
                    "student_schedules": copy.deepcopy(self.student_schedules),
                    "sections": copy.deepcopy(self.sections),
                    "section_plan": copy.deepcopy(section_plan),
                }

            bottleneck_counts = {}
            for fr in self.failed_requests:
                sub = fr.get("failed_at")
                bottleneck_counts[sub] = bottleneck_counts.get(sub, 0) + 1

            worst = sorted(bottleneck_counts.items(), key=lambda x: x[1], reverse=True)[
                :3
            ]
            for sub, _cnt in worst:
                if sub in counts:
                    current = section_plan.get(sub, 2)
                    cap = max(6, math.ceil(counts[sub] / 3) + 6)
                    if current < cap:
                        section_plan[sub] = current + 1

        if best:
            self.failed_requests = best["failed_requests"]
            self.student_schedules = best["student_schedules"]
            self.sections = best["sections"]
            print(
                f"[Warning] Could not reach 100% after {max_attempts} attempts. "
                f"Best attempt still has {best['failed_count']} failures."
            )

    def _assign_students(self, student_requests):
        self.failed_requests = []

        for sec in self.sections:
            sec.students = []

        all_subjects = set()
        for subs in student_requests.values():
            for s in subs:
                all_subjects.add(s)

        subject_difficulty = {}
        for sub in all_subjects:
            sections_available = [s for s in self.sections if s.subject == sub]
            count = len(sections_available)
            subject_difficulty[sub] = 100 / count if count > 0 else 999

        sorted_names = sorted(student_requests.keys())

        for name in sorted_names:
            self.student_schedules[name] = {
                d: [None] * self.period_counts[d] for d in self.days
            }
            self.student_schedules[name]["Tue"][1] = "TUTOR"
            self.student_schedules[name]["Fri"][5] = "FREE"

            requested = sorted(
                list(student_requests[name]),
                key=lambda s: subject_difficulty.get(s, 0),
                reverse=True,
            )

            success, failed_sub = self._backtrack(name, requested, 0)

            if not success:
                self.student_schedules[name] = None
                self.failed_requests.append(
                    {"name": name, "failed_at": failed_sub, "all_requested": requested}
                )

    def _backtrack(self, name, subjects, idx):
        if idx == len(subjects):
            return True, None

        sub = subjects[idx]
        potential = [s for s in self.sections if s.subject == sub]
        random.shuffle(potential)

        for sec in potential:
            if len(sec.students) < sec.room.capacity:
                if all(
                    self.student_schedules[name][d][p] is None for d, p in sec.slots
                ):
                    sec_has_mon_p6 = any(d == "Mon" and p == 5 for d, p in sec.slots)
                    sec_has_other_last = any(
                        d != "Mon" and d != "Fri" and p == (self.period_counts[d] - 1)
                        for d, p in sec.slots
                    )
                    is_mon_p6_taken = self.student_schedules[name]["Mon"][5] is not None

                    if sec_has_other_last and not sec_has_mon_p6:
                        continue
                    if (
                        sec_has_mon_p6
                        and is_mon_p6_taken
                        and not self.student_schedules[name]["Mon"][5].startswith(sub)
                    ):
                        continue

                    for d, p in sec.slots:
                        self.student_schedules[name][d][
                            p
                        ] = f"{sub} ({sec.room.number})"

                    sec.students.append(name)

                    success, deeper_fail = self._backtrack(name, subjects, idx + 1)
                    if success:
                        return True, None

                    sec.students.remove(name)
                    for d, p in sec.slots:
                        self.student_schedules[name][d][p] = None

        return False, sub

    def print_timetable(self, name):
        if name not in self.student_schedules or not self.student_schedules[name]:
            print(f"No schedule for {name}")
            return

        print(f"\n--- TIMETABLE: {name.upper()} ---")

        headers = ["Period"] + self.days

        table_data = []
        for p in range(7):
            row = [f"P{p+1}"]
            for d in self.days:
                if p < self.period_counts[d]:
                    row.append(self.student_schedules[name][d][p] or "FREE")
                else:
                    row.append("-")
            table_data.append(row)

        print(tabulate(table_data, headers=headers, tablefmt="fancy_grid"))

    def print_teacher_timetable(self, teacher_name):
        sched = {d: [None] * self.period_counts[d] for d in self.days}

        teacher_sections = [
            s for s in self.sections if s.instructor.name == teacher_name
        ]

        if not teacher_sections:
            print(f"[Error] No classes found for teacher: {teacher_name}")
            return

        for sec in teacher_sections:
            for d, p in sec.slots:
                sched[d][
                    p
                ] = f"{sec.subject}\n({sec.room.number})\nSt: {len(sec.students)}"

        print(f"\n--- TEACHER TIMETABLE: {teacher_name.upper()} ---")
        headers = ["Period"] + self.days
        table_data = []

        for p in range(7):
            row = [f"P{p+1}"]
            for d in self.days:
                if p < self.period_counts[d]:
                    row.append(sched[d][p] or "---")
                else:
                    row.append("-")
            table_data.append(row)

        print(tabulate(table_data, headers=headers, tablefmt="fancy_grid"))

    def save_all_data(self):
        with open("./output/roll_calls.txt", "w") as f:
            for sec in sorted(self.sections, key=lambda x: x.subject):
                f.write(
                    f"\nID: {sec.id} | {sec.subject} | {sec.instructor.name} | {sec.room.number}\n"
                )
                f.write(f"Students: {', '.join(sorted(sec.students))}\n")

        with open("./output/student_timetables.txt", "w") as f:
            for name in sorted(self.student_schedules.keys()):
                if not self.student_schedules[name]:
                    continue
                f.write(f"\nSTUDENT: {name}\n")
                headers = ["Period"] + self.days
                table_data = []
                for p in range(7):
                    line = [f"P{p+1}"]
                    for d in self.days:
                        line.append(
                            str(
                                self.student_schedules[name][d][p]
                                if p < self.period_counts[d]
                                else "-"
                            )
                        )
                    table_data.append(line)
                f.write(tabulate(table_data, headers=headers, tablefmt="grid") + "\n")

        with open("./output/teacher_timetables.txt", "w") as f:
            for teacher in sorted(self.teachers, key=lambda t: t.name):
                f.write(f"\n{'='*30}\nINSTRUCTOR: {teacher.name}\n{'='*30}\n")

                teacher_sched = {d: [None] * self.period_counts[d] for d in self.days}
                teacher_sections = [
                    s for s in self.sections if s.instructor.name == teacher.name
                ]

                for sec in teacher_sections:
                    for d, p in sec.slots:
                        teacher_sched[d][
                            p
                        ] = f"{sec.subject}\n({sec.room.number})\nStudents: {len(sec.students)}"

                headers = ["Period"] + self.days
                table_data = []
                for p in range(7):
                    row = [f"P{p+1}"]
                    for d in self.days:
                        if p < self.period_counts[d]:
                            row.append(teacher_sched[d][p] or "---")
                        else:
                            row.append("-")
                    table_data.append(row)

                f.write(tabulate(table_data, headers=headers, tablefmt="grid") + "\n\n")

        print(
            "[System] Reports generated: roll_calls.txt, teacher_timetables.txt, and student_timetables.txt"
        )
