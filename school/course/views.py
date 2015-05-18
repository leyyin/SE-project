from flask.ext.login import login_required, current_user
from flask import Blueprint, render_template, flash, redirect, url_for, request
from school.decorators import role_required
from school.config import FLASH_SUCCESS, FLASH_ERROR
from school.models import *
from school.user import User
from .forms import TeacherAddCourseForm
from datetime import date

course = Blueprint('course', __name__)


@course.route('/see_courses', methods=['GET', 'POST'])
@course.route('/see_courses/<int:semester_id>', methods=['GET', 'POST'])
@login_required
def see_courses(semester_id=None):
    if current_user.is_student():

        period = current_user.get_default_period()
        degree = period.degree
        semesters = User.get_semesters_for_period(period)

        if semester_id is None:  # use default, all semesters, enrolled with contract
            semester = None
            courses_enrolled = current_user.get_courses_enrolled(degree)
        else:  # has semester from url
            semester = Semester.get_by_id(semester_id)
            has_contract = current_user.has_contract_signed(semester, degree)
            courses_enrolled = []
            if has_contract:  # only display signed contracts for that semester
                courses_enrolled = current_user.get_courses_enrolled_semester(semester, degree)

        return render_template("course/see_courses.html",
                               semesters=semesters,
                               courses_enrolled=courses_enrolled,
                               selected_semester=semester)
    elif current_user.is_admin():

        departments = Department.query.order_by("name").all()

        seen_depts = set()
        depts = []
        courses_depts = []

        for department in departments:
            if department.name not in seen_depts:
                seen_depts.add(department.name)
                depts.append(department.name)
            for degree in department.degrees:
                for course in degree.courses:
                    dico = dict()
                    dico["course"] = course.name
                    dico["department"] = department.name
                    courses_depts.append(dico)

        return render_template("course/see_courses.html", total=courses_depts, depts=depts)

    elif current_user.is_teacher():

        courses = []
        for teach in current_user.teaches.all():  # TODO get only approved courses
            courses.append(teach.course)

        return render_template("course/see_courses.html", courses=courses)

    elif current_user.is_chief_department():

        name_dp = "Math/Computer Science"
        department = Department.query.filter_by(name=name_dp).first()

        courses_depts = []

        for degree in department.degrees:
            for course in degree.courses:
                dico = dict()
                dico["course"] = course.name
                dico["department"] = department.name
                courses_depts.append(dico)

        return render_template("course/see_courses.html", total=courses_depts, dp=department)


@course.route('/upload_course_results', methods=['GET', 'POST'])
@login_required
def upload_course_results():
    le_semestre = ""
    le_cours = ""
    semesters = []
    the_semester = Semester.query.all()
    for semester in the_semester:
        semesters.append(semester)

    allcourses = [teach.course for teach in current_user.teaches.all()]

    if request.method == 'POST':
        val = request.form['course']
        sem = request.form['semester']
        students = []
        grades = []

        le_cours = Course.query.filter_by(id=int(val)).first()
        le_semestre = Semester.query.filter_by(id=sem).first()

        studentsenrolled = Enrollment.query.filter_by(course_id=int(val), semester_id=int(sem)).all()
        for student in studentsenrolled:
            students.append(User.query.filter_by(id=student.student_id).first())
            grades.append(student.grade)

        return render_template("course/upload_course_results.html",
                               allcourses=allcourses,
                               thecourse=le_cours,
                               students=students,
                               semesters=semesters,
                               le_semestre=le_semestre,
                               grades=grades)
    else:
        return render_template("course/upload_course_results.html", allcourses=allcourses,
                               le_semestre=le_semestre,
                               semesters=semesters,
                               thecourse=le_cours)


@course.route('/upload_course_results/<int:user_id>,<int:course_id>,<int:grade>,<int:semester_id>')
@login_required
@role_required(teacher=True, cd=True)
def save_grade(user_id, course_id, grade, semester_id):
    enrollment_instance = Enrollment.query.filter_by(student_id=user_id, course_id=course_id,
                                                     semester_id=semester_id).first()

    enrollment_instance.grade = grade
    db.session.add(enrollment_instance)
    db.session.commit()

    flash("Grade updated", FLASH_SUCCESS)
    return redirect(url_for("course.upload_course_results"))


@course.route('/contract/', methods=["GET"])
@course.route('/contract/<int:semester_id>', methods=["GET", "POST"])
@login_required
@role_required(student=True)
def contract(semester_id=None):
    # all the semesters for the default degree
    period = current_user.get_default_period()
    degree = period.degree
    group = current_user.get_group(period)
    semesters = User.get_semesters_for_period(period)
    year, sem_nr = User.get_current_year_semester(semesters)

    if semester_id is None:  # use default semester
        semester = semesters[0]
    else:  # has semester from url
        semester = Semester.get_by_id(semester_id)

    has_contract = current_user.has_contract_signed(semester, degree)
    courses_enrolled = current_user.get_courses_enrolled_semester(semester, degree)

    print(year, sem_nr)
    return render_template("course/contract.html",
                           semesters=semesters,
                           semester_sel=semester,
                           semester_nr=sem_nr,
                           year=year,
                           group=group,
                           degree=degree,
                           has_contract=has_contract,
                           courses_enrolled=courses_enrolled)

@course.route('/remove_optional_course/<int:course_id>', methods=["GET"])
@login_required
@role_required(teacher=True, cd=True)
def remove_optional_course(course_id):
    found_course = Course.get_by_id(course_id)
    year = date.today().year

    if current_user.is_teacher():
        optional_teaches = Teaches.get_optional_courses(current_user, year)
        for teaches in optional_teaches:
            if found_course.id == teaches.course.id:  # found course remove it
                # update database
                db.session.delete(found_course)
                db.session.delete(teaches)
                db.session.commit()

                flash("Removed optional course", FLASH_SUCCESS)
                return redirect(url_for("course.establish_courses"))

        flash("Can not remove that optional course", FLASH_ERROR)
        return redirect(url_for("course.establish_courses"))

    flash("TODO", FLASH_ERROR)
    return redirect(url_for("course.establish_courses"))

@course.route('/establish_courses', methods=["GET", "POST"])
@login_required
@role_required(teacher=True, cd=True)
def establish_courses():
    if current_user.is_teacher():
        if not current_user.is_lecturer():
            flash("You are not a lecturer, so you can't add optional courses", FLASH_ERROR)
            return redirect(url_for("user.index"))

        year = date.today().year
        semesters = Semester.get_semesters_year(year)
        department = current_user.get_department_teacher()
        degrees = department.degrees
        optional_teaches = Teaches.get_optional_courses(current_user, year)
        can_add = (len(optional_teaches) < 2)  # only 2 optional course per year

        # build form
        add_form = TeacherAddCourseForm()
        if can_add:
            add_form.semester_id.choices = [(s.id, s.name) for s in semesters]
            add_form.degree_id.choices = [(d.id, d.name) for d in degrees]
            if add_form.validate_on_submit():
                # add optional course to database
                add_course = Course(is_approved=False, is_optional=True, category=0)
                add_form.populate_obj(add_course)  # should set name, degree_id

                # add mark in teaches
                add_teaches = Teaches(teacher=current_user, course=add_course, semester_id=add_form.semester_id.data)

                db.session.add_all([add_course, add_teaches])
                db.session.commit()

                # update view
                flash("Optional course added", FLASH_SUCCESS)
                add_form.name.data = ""
                optional_teaches = Teaches.get_optional_courses(current_user, year)
                can_add = (len(optional_teaches) < 2)

        return render_template("course/establish_courses.html",
                               add_form=add_form,
                               can_add=can_add,
                               optional_teaches=optional_teaches)

    # cd
    department = current_user.get_department_cd()

    return render_template("course/establish_courses.html")
