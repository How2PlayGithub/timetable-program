class Room:
    def __init__(self, number, r_type, capacity, preferred_subjects=None):
        self.number = number
        self.type = r_type
        self.capacity = capacity
        self.preferred_subjects = preferred_subjects if preferred_subjects else []

    def __str__(self):
        return self.number


class Instructor:
    def __init__(self, name, subjects):
        self.name = name
        self.subjects = subjects

    def __str__(self):
        return self.name


class Section:
    def __init__(self, id, subject, instructor, room):
        self.id = id
        self.subject = subject
        self.instructor = instructor
        self.room = room
        self.slots = []
        self.students = []

    def __str__(self):
        return f"[{self.subject}, {self.room}, {self.instructor}]"
