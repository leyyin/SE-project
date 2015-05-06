from school.extensions import db
from sqlalchemy import Column, Integer, String, SmallInteger
from flask.ext.login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class Role:
    STUDENT = 1
    TEACHER = 2
    CHIEF_DEPARTMENT = 3
    ADMIN = 4

    @staticmethod
    def get_roles():
        return [Role.STUDENT, Role.TEACHER, Role.CHIEF_DEPARTMENT, Role.ADMIN]


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True)
    realname = Column(String(128), nullable=True)
    email = Column(String(64), unique=True)
    password_hash = Column(String(160), nullable=False)
    role_id = Column(SmallInteger, default=Role.STUDENT)
    enrolled = db.relationship("Enrollment", lazy="dynamic", cascade="save-update, merge, delete, delete-orphan")
    teaches = db.relationship("Teaches", lazy="dynamic", cascade="save-update, merge, delete, delete-orphan")

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)

        # invalid role detected
        if self.role_id is not None and self.role_id not in Role.get_roles():
            print("ERROR: INVALID role_id: ", self.role_id)
            self.role_id = Role.STUDENT

    def __repr__(self):
        return '<User id={0}, username={1}, realname={2}, email={3}, role={4}>'.format(str(self.id),
                                                                                       str(self.username),
                                                                                       str(self.realname,
                                                                                       str(self.email)),
                                                                                       self.role_to_str())

    @classmethod
    def get_by_id(cls, user_id):
        return cls.query.filter_by(id=user_id).first_or_404()

    def role_to_str(self):
        if self.role_id == Role.STUDENT:
            return "student"
        elif self.role_id == Role.TEACHER:
            return "teacher"
        elif self.role_id == Role.CHIEF_DEPARTMENT:
            return "chief_department"
        elif self.role_id == Role.ADMIN:
            return "admin"

    def is_student(self):
        return self.role_id == Role.STUDENT

    def is_teacher(self):
        return self.role_id == Role.TEACHER

    def is_chief_department(self):
        return self.role_id == Role.CHIEF_DEPARTMENT

    def is_admin(self):
        return self.role_id == Role.ADMIN

    @property
    def password(self):
        return self.password_hash

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def get_realname(self):
        return self.realname

    def get_username(self):
        return self.username

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)
