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
                        Room(k, v["type"], v["capacity"]) for k, v in room_data.items()
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
        rotation_p = []
        for d in self.days:
            if d != "Fri":
                rotation_p.append((d, self.period_counts[d] - 1))
        patterns.append(rotation_p)

        for _ in range(100):
            p = []
            selected_days = random.sample(self.days, 5)
            for d in selected_days:
                possible = [
                    i
                    for i in range(self.period_counts[d])
                    if not (d == "Tue" and i == 1) and not (d == "Fri" and i == 5)
                ]
                non_last = [i for i in possible if i < (self.period_counts[d] - 1)]
                p.append((d, random.choice(non_last if non_last else possible)))
            patterns.append(p)
        return patterns

    def solve(self, student_requests):
        print("\n" + "=" * 60 + "\n TIMETABLE GENERATOR STARTING\n" + "=" * 60)

        counts = {}
        for subs in student_requests.values():
            for s in subs:
                counts[s] = counts.get(s, 0) + 1

        self.sections = []
        for sub, count in counts.items():
            req_type = self.subject_requirements.get(sub, "General")
            possible_rooms = [r for r in self.rooms if r.type == req_type]
            possible_teachers = [t for t in self.teachers if sub in t.subjects]

            if not possible_rooms or not possible_teachers:
                print(
                    f"[Warning] Missing resources for {sub}. Room/Teacher checks failed."
                )
                continue

            num_sections = max(3, math.ceil(count / 15))
            for i in range(1, num_sections + 1):
                self.sections.append(
                    Section(
                        f"{sub[:3]}-{i}",
                        sub,
                        random.choice(possible_teachers),
                        random.choice(possible_rooms),
                    )
                )

        if not self.sections:
            print("[Error] No sections created. Termination.")
            return

        slot_usage = {}
        teacher_usage = {}
        room_usage = {}

        for sec in self.sections:
            best_pattern = None
            min_cost = float("inf")

            random.shuffle(self.patterns)
            for p in self.patterns:
                cost = 0
                for slot in p:
                    cost += slot_usage.get(slot, 0) * 50
                    if (sec.instructor.name, slot) in teacher_usage:
                        cost += 100000
                    if (sec.room.number, slot) in room_usage:
                        cost += 100000

                if cost < min_cost:
                    min_cost = cost
                    best_pattern = p

            sec.slots = best_pattern
            for slot in best_pattern:
                slot_usage[slot] = slot_usage.get(slot, 0) + 1
                teacher_usage[(sec.instructor.name, slot)] = True
                room_usage[(sec.room.number, slot)] = True

        self._assign_students(student_requests)

    def _assign_students(self, student_requests):
        self.failed_requests = []
        sorted_names = sorted(
            student_requests.keys(),
            key=lambda n: sum(
                1
                for s in student_requests[n]
                if self.subject_requirements.get(s) == "Lab"
            ),
            reverse=True,
        )

        for name in sorted_names:
            self.student_schedules[name] = {
                d: [None] * self.period_counts[d] for d in self.days
            }
            self.student_schedules[name]["Tue"][1] = "TUTOR"
            self.student_schedules[name]["Fri"][5] = "FREE"

            requested = sorted(
                list(student_requests[name]),
                key=lambda s: self.subject_requirements.get(s) != "General",
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
