# app.py - Complete Flask Application with MongoDB Integration and Missing Routes
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import check_password_hash
from datetime import datetime, timedelta
from functools import wraps
from bson import ObjectId
import os
from dotenv import load_dotenv
from database import users_collection,enrollments_collection, quiz_results_collection, leaderboard_collection
from utils.system_monitor import initialize_system_monitor, get_system_monitor
import csv
import io
from flask import make_response




# Import MongoDB models
from database import (
    UserModel, CourseModel, ModuleModel, EnrollmentModel,
    AssessmentModel, BadgeModel, AnalyticsModel, QuizModel,
    QuizResultModel, LeaderboardModel, mongo_db
)

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')

# ============================================================================
# ADD SYSTEM MONITOR INITIALIZATION HERE #
# ============================================================================

# Initialize system monitor with your MongoDB configuration
system_monitor = initialize_system_monitor(
    mongo_uri=app.config.get('MONGO_URI'),
    db_name='HEADWAY_MAIN'
)


# =====================================================
# UTILITY FUNCTIONS
# =====================================================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated_function


def role_required(roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in to access this page.', 'error')
                return redirect(url_for('login'))

            user = get_current_user()
            if user and user['role'] not in roles:
                flash('Access denied. Insufficient permissions.', 'error')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)

        return decorated_function

    return decorator


def get_current_user():
    """Get current user from session"""
    if 'user_id' in session:
        return UserModel.find_user_by_id(session['user_id'])
    return None


def convert_objectid_to_str(obj):
    """Convert ObjectId to string in MongoDB documents"""
    if isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(value, ObjectId):
                obj[key] = str(value)
            elif isinstance(value, dict):
                convert_objectid_to_str(value)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        convert_objectid_to_str(item)
    return obj


# =====================================================
# AUTHENTICATION ROUTES
# =====================================================

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = UserModel.find_user_by_email(email)
        if user and check_password_hash(user['password'], password):

            # NEW: Check if user is active
            user_status = user.get('status', 'active')
            if user_status != 'active':
                flash('Your account has been deactivated. Please contact the administrator for assistance.', 'error')
                return render_template('auth/login.html')

            # Proceed with normal login
            session['user_id'] = str(user['_id'])
            session['user_email'] = email
            session['user_role'] = user['role']
            session['user_name'] = user['name']

            # Update last login
            UserModel.update_user(user['_id'], {'last_login': datetime.now()})

            flash(f'Welcome back, {user["name"]}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password!', 'error')

    return render_template('auth/login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = request.form.get('role', 'student')

        # Commit 01
        if len(password) < 8 or not any(c.isdigit() for c in password):
            flash("Try a password with at least 8 characters.", 'error')
            return render_template('auth/register.html', form_data=request.form)

        # Check if user already exists
        existing_user = UserModel.find_user_by_email(email)
        if existing_user:
            flash('Email already exists!', 'error')
        else:
            # Create new user
            user_data = {
                'name': name,
                'email': email,
                'password': password,  # Will be hashed in UserModel.create_user
                'role': role,
                'avatar': '/static/images/default.jpg'
            }

            # Add role-specific fields
            if role == 'student':
                user_data.update({
                    'level': 'Beginner',
                    'points': 0,
                    'badges': []
                })
            elif role == 'educator':
                user_data.update({
                    'department': '',
                    'experience': '0 years'
                })

            user_id = UserModel.create_user(user_data)
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))

    return render_template('auth/register.html')


@app.route('/logout')
def logout():
    monitor = get_system_monitor()

    # Get session info before clearing
    session_id = session.get('_permanent', session.get('_id', 'unknown'))
    user = get_current_user()

    if user and session_id in monitor.active_sessions:
        monitor.remove_session(session_id)
        monitor.log_system_event('INFO', 'AUTH',
                                 f'User session ended: {user["email"]}')

    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('index'))

# =====================================================
# DASHBOARD ROUTES
# =====================================================

@app.route('/dashboard')
@login_required
def dashboard():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))

    role = user['role']

    if role == 'student':
        return redirect(url_for('student_dashboard'))
    elif role == 'educator':
        return redirect(url_for('educator_dashboard'))
    elif role == 'admin':
        return redirect(url_for('admin_dashboard'))
    elif role == 'content_manager':
        return redirect(url_for('content_manager_dashboard'))
    elif role == 'system_admin':
        return redirect(url_for('system_admin_dashboard'))

    return render_template('dashboard.html', user=convert_objectid_to_str(user))


# =====================================================
# STUDENT ROUTES
# =====================================================

@app.route('/student/dashboard')
@role_required(['student'])
def student_dashboard():
    user = get_current_user()
    user_id = str(user['_id'])

    # Get student's enrollments
    enrollments = EnrollmentModel.get_user_enrollments(user_id)
    enrolled_courses = []

    for enrollment in enrollments:
        course = CourseModel.find_course_by_id(enrollment['course_id'])
        if course:
            course_data = convert_objectid_to_str(course.copy())
            course_data.update({
                'progress': enrollment['progress'],
                'completed_modules': enrollment.get('completed_modules', []),
                'grade': enrollment.get('grade')
            })
            enrolled_courses.append(course_data)

    # Calculate stats
    total_courses = len(enrolled_courses)
    completed_courses = sum(1 for e in enrollments if e.get('progress', 0) == 100)
    avg_progress = sum(e.get('progress', 0) for e in enrollments) / len(enrollments) if enrollments else 0

    # Recent activity (could be enhanced with actual activity tracking)
    recent_activity = [
        {'action': 'Completed Quiz', 'course': 'Grammar Fundamentals', 'time': '2 hours ago'},
        {'action': 'Started Module', 'course': 'Business English', 'time': '1 day ago'},
        {'action': 'Earned Badge', 'course': 'Grammar Master', 'time': '3 days ago'}
    ]

    # Get badges
    all_badges = BadgeModel.get_all_badges()
    badges_dict = {badge['name'].lower().replace(' ', '_'): badge for badge in all_badges}

    return render_template('student/dashboard.html',
                           user=convert_objectid_to_str(user),
                           enrolled_courses=enrolled_courses,
                           total_courses=total_courses,
                           completed_courses=completed_courses,
                           avg_progress=avg_progress,
                           recent_activity=recent_activity,
                           badges=badges_dict)


@app.route('/student/courses')
@role_required(['student'])
def student_courses():
    user = get_current_user()
    user_id = str(user['_id'])

    # Get all courses
    all_courses = CourseModel.get_all_courses()

    # Get user's enrollments
    enrollments = EnrollmentModel.get_user_enrollments(user_id)
    enrolled_course_ids = {e['course_id'] for e in enrollments}

    # Filter available courses (not enrolled)
    available_courses = []
    for course in all_courses:
        course_id = str(course['_id'])
        if course_id not in enrolled_course_ids and course.get('status') == 'published':
            available_courses.append(convert_objectid_to_str(course))

    return render_template('student/courses.html',
                           user=convert_objectid_to_str(user),
                           available_courses=available_courses)


@app.route('/student/course/<course_id>')
@role_required(['student'])
def student_course_detail(course_id):
    user = get_current_user()
    user_id = str(user['_id'])

    # Get course
    course = CourseModel.find_course_by_id(course_id)
    if not course:
        flash('Course not found!', 'error')
        return redirect(url_for('student_courses'))

    # Get course modules
    modules = ModuleModel.get_modules_by_course(course_id)
    course_modules = []

    for module in modules:
        module_data = convert_objectid_to_str(module.copy())
        module_data['completed'] = user_id in module.get('completed_by', [])
        course_modules.append(module_data)

    # Check if student is enrolled
    enrollment = EnrollmentModel.find_enrollment(user_id, course_id)

    return render_template('student/course_detail.html',
                           user=convert_objectid_to_str(user),
                           course=convert_objectid_to_str(course),
                           modules=course_modules,
                           enrollment=convert_objectid_to_str(enrollment) if enrollment else None)


# =====================================================
# ENROLLMENT ROUTES
# =====================================================

@app.route('/enroll/<course_id>')
@role_required(['student'])
def enroll_course(course_id):
    """Show course enrollment preview page"""
    user = get_current_user()
    user_id = str(user['_id'])

    # Check if course exists
    course = CourseModel.find_course_by_id(course_id)
    if not course:
        flash('Course not found!', 'error')
        return redirect(url_for('student_courses'))

    # Check if already enrolled
    existing_enrollment = EnrollmentModel.find_enrollment(user_id, course_id)
    if existing_enrollment:
        flash('You are already enrolled in this course!', 'warning')
        return redirect(url_for('student_course_detail', course_id=course_id))

    # Get course modules for preview
    modules = ModuleModel.get_modules_by_course(course_id)
    course_modules = [convert_objectid_to_str(module) for module in modules]

    return render_template('student/enroll_preview.html',
                           user=convert_objectid_to_str(user),
                           course=convert_objectid_to_str(course),
                           modules=course_modules)


@app.route('/enroll/<course_id>/confirm', methods=['POST'])
@role_required(['student'])
def confirm_enrollment(course_id):
    """Confirm and process course enrollment"""
    user = get_current_user()
    user_id = str(user['_id'])

    # Check if course exists
    course = CourseModel.find_course_by_id(course_id)
    if not course:
        flash('Course not found!', 'error')
        return redirect(url_for('student_courses'))

    # Check if already enrolled
    existing_enrollment = EnrollmentModel.find_enrollment(user_id, course_id)
    if existing_enrollment:
        flash('You are already enrolled in this course!', 'warning')
        return redirect(url_for('student_course_detail', course_id=course_id))

    # Create enrollment
    enrollment_data = {
        'user_id': user_id,
        'course_id': course_id,
        'progress': 0,
        'completed_modules': [],
        'grade': None
    }

    try:
        enrollment_id = EnrollmentModel.create_enrollment(enrollment_data)

        # Update course enrollment count
        CourseModel.update_course(course_id, {
            'students_enrolled': course.get('students_enrolled', 0) + 1
        })

        # Award points for enrollment
        UserModel.update_user(user['_id'], {
            'points': user.get('points', 0) + 100
        })

        flash(f'Successfully enrolled in {course["title"]}! You earned 100 points.', 'success')
        return redirect(url_for('student_course_detail', course_id=course_id))

    except Exception as e:
        print(f"Error creating enrollment: {e}")
        flash('An error occurred during enrollment. Please try again.', 'error')
        return redirect(url_for('enroll_course', course_id=course_id))


# =====================================================
# ENHANCED STUDENT ROUTES WITH QUIZ FUNCTIONALITY
# =====================================================

@app.route('/student/quiz/<quiz_id>')
@role_required(['student'])
def take_quiz(quiz_id):
    """Take a quiz"""
    user = get_current_user()

    # Get quiz details
    quiz = QuizModel.find_quiz_by_id(quiz_id)
    if not quiz:
        flash('Quiz not found!', 'error')
        return redirect(url_for('student_dashboard'))

    # Get module and course info
    module = ModuleModel.find_module_by_id(quiz['module_id'])
    course = CourseModel.find_course_by_id(module['course_id']) if module else None

    # Check if user is enrolled
    enrollment = EnrollmentModel.find_enrollment(str(user['_id']), str(course['_id'])) if course else None
    if not enrollment:
        flash('You must be enrolled in this course to take the quiz!', 'error')
        return redirect(url_for('student_courses'))

    # Check if quiz already taken
    existing_result = QuizResultModel.find_result(str(user['_id']), quiz_id)
    if existing_result:
        return redirect(url_for('quiz_result', result_id=str(existing_result['_id'])))

    return render_template('student/take_quiz.html',
                           user=convert_objectid_to_str(user),
                           quiz=convert_objectid_to_str(quiz),
                           module=convert_objectid_to_str(module),
                           course=convert_objectid_to_str(course))


@app.route('/student/quiz/<quiz_id>/submit', methods=['POST'])
@role_required(['student'])
def submit_quiz(quiz_id):
    """Submit quiz answers and calculate score"""
    user = get_current_user()
    user_id = str(user['_id'])

    # Get quiz details
    quiz = QuizModel.find_quiz_by_id(quiz_id)
    if not quiz:
        flash('Quiz not found!', 'error')
        return redirect(url_for('student_dashboard'))

    # Get answers from form
    answers = {}
    for key, value in request.form.items():
        if key.startswith('question_'):
            question_index = int(key.split('_')[1])
            # FIX: Convert integer key to string for MongoDB compatibility
            answers[str(question_index)] = int(value)

    # Calculate score
    correct_answers = 0
    total_questions = len(quiz['questions'])
    question_results = []

    for i, question in enumerate(quiz['questions']):
        # FIX: Use string key when accessing answers
        user_answer = answers.get(str(i))
        is_correct = user_answer == question['correct_answer']
        if is_correct:
            correct_answers += 1

        question_results.append({
            'question_index': i,
            'user_answer': user_answer,
            'correct_answer': question['correct_answer'],
            'is_correct': is_correct
        })

    # Calculate percentage score
    score_percentage = (correct_answers / total_questions) * 100 if total_questions > 0 else 0

    # Determine grade
    if score_percentage >= 90:
        grade = 'A+'
    elif score_percentage >= 85:
        grade = 'A'
    elif score_percentage >= 80:
        grade = 'A-'
    elif score_percentage >= 75:
        grade = 'B+'
    elif score_percentage >= 70:
        grade = 'B'
    elif score_percentage >= 65:
        grade = 'B-'
    elif score_percentage >= 60:
        grade = 'C+'
    elif score_percentage >= 55:
        grade = 'C'
    elif score_percentage >= 50:
        grade = 'C-'
    else:
        grade = 'F'

    # Save quiz result
    result_data = {
        'user_id': user_id,
        'quiz_id': quiz_id,
        'module_id': quiz['module_id'],
        'course_id': quiz['course_id'],
        'answers': answers,  # Now contains string keys
        'question_results': question_results,
        'score': correct_answers,
        'total_questions': total_questions,
        'score_percentage': round(score_percentage, 2),
        'grade': grade,
        'time_taken': request.form.get('time_taken', 0),
        'completed_at': datetime.now()
    }

    result_id = QuizResultModel.create_result(result_data)

    # Mark module as completed if passing score
    if score_percentage >= quiz.get('passing_score', 70):
        ModuleModel.mark_module_completed(quiz['module_id'], user_id)

        # Update enrollment progress
        module = ModuleModel.find_module_by_id(quiz['module_id'])
        if module:
            course_id = module['course_id']
            enrollment = EnrollmentModel.find_enrollment(user_id, course_id)

            if enrollment:
                completed_modules = enrollment.get('completed_modules', [])
                if quiz['module_id'] not in completed_modules:
                    completed_modules.append(quiz['module_id'])

                    # Calculate progress
                    total_modules = len(ModuleModel.get_modules_by_course(course_id))
                    progress = int((len(completed_modules) / total_modules) * 100) if total_modules > 0 else 0

                    # Update enrollment
                    EnrollmentModel.update_enrollment_progress(user_id, course_id, {
                        'completed_modules': completed_modules,
                        'progress': progress
                    })

        # Award points
        points_earned = max(10, int(score_percentage / 10) * 5)  # 10-50 points based on score
        UserModel.update_user(user['_id'], {
            'points': user.get('points', 0) + points_earned
        })

        flash(f'Congratulations! You passed with {score_percentage:.1f}% and earned {points_earned} points!', 'success')
    else:
        flash(f'You scored {score_percentage:.1f}%. You need {quiz.get("passing_score", 70)}% to pass. Try again!',
              'warning')

    return redirect(url_for('quiz_result', result_id=result_id))


@app.route('/student/quiz/result/<result_id>')
@role_required(['student'])
def quiz_result(result_id):
    """View quiz result"""
    user = get_current_user()

    # Get quiz result
    result = QuizResultModel.find_result_by_id(result_id)
    if not result or result['user_id'] != str(user['_id']):
        flash('Quiz result not found!', 'error')
        return redirect(url_for('student_dashboard'))

    # Get related data
    quiz = QuizModel.find_quiz_by_id(result['quiz_id'])
    module = ModuleModel.find_module_by_id(result['module_id'])
    course = CourseModel.find_course_by_id(result['course_id'])

    return render_template('student/quiz_result.html',
                           user=convert_objectid_to_str(user),
                           result=convert_objectid_to_str(result),
                           quiz=convert_objectid_to_str(quiz),
                           module=convert_objectid_to_str(module),
                           course=convert_objectid_to_str(course))


@app.route('/student/module/<module_id>')
@role_required(['student'])
def student_module(module_id):
    user = get_current_user()

    # Get module
    module = ModuleModel.find_module_by_id(module_id)
    if not module:
        flash('Module not found!', 'error')
        return redirect(url_for('student_dashboard'))

    # Get course
    course = CourseModel.find_course_by_id(module['course_id'])

    # Get assessment if it's a quiz
    assessment = None
    if module.get('type') == 'quiz':
        assessment = AssessmentModel.get_assessment_by_module(module_id)

    return render_template('student/module.html',
                           user=convert_objectid_to_str(user),
                           module=convert_objectid_to_str(module),
                           course=convert_objectid_to_str(course),
                           assessment=convert_objectid_to_str(assessment) if assessment else None)


@app.route('/student/complete_module/<module_id>')
@role_required(['student'])
def complete_module(module_id):
    user = get_current_user()
    user_id = str(user['_id'])

    # Get module
    module = ModuleModel.find_module_by_id(module_id)
    if not module:
        flash('Module not found!', 'error')
        return redirect(url_for('student_dashboard'))

    # Check if already completed
    if user_id not in module.get('completed_by', []):
        # Mark module as completed
        ModuleModel.mark_module_completed(module_id, user_id)

        # Update enrollment progress
        course_id = module['course_id']
        enrollment = EnrollmentModel.find_enrollment(user_id, course_id)

        if enrollment:
            completed_modules = enrollment.get('completed_modules', [])
            if module_id not in completed_modules:
                completed_modules.append(module_id)

                # Calculate progress
                total_modules = len(ModuleModel.get_modules_by_course(course_id))
                progress = int((len(completed_modules) / total_modules) * 100) if total_modules > 0 else 0

                # Update enrollment
                EnrollmentModel.update_enrollment_progress(user_id, course_id, {
                    'completed_modules': completed_modules,
                    'progress': progress
                })

        # Award points
        UserModel.update_user(user['_id'], {
            'points': user.get('points', 0) + 50
        })

        flash('Module completed! You earned 50 points.', 'success')

    return redirect(url_for('student_course_detail', course_id=module['course_id']))


# =====================================================
# EDUCATOR ROUTES
# =====================================================

@app.route('/educator/dashboard')
@role_required(['educator'])
def educator_dashboard():
    user = get_current_user()
    user_id = str(user['_id'])

    # Get educator's courses
    educator_courses = CourseModel.get_courses_by_instructor(user_id)
    educator_courses = [convert_objectid_to_str(course) for course in educator_courses]

    # Calculate stats
    total_students = sum(course.get('students_enrolled', 0) for course in educator_courses)
    total_courses = len(educator_courses)
    avg_rating = sum(course.get('rating', 0) for course in educator_courses) / len(
        educator_courses) if educator_courses else 0

    # Recent activity
    recent_activity = [
        {'action': 'New student enrolled', 'course': 'Grammar Fundamentals', 'time': '1 hour ago'},
        {'action': 'Quiz submitted', 'student': 'John Smith', 'time': '3 hours ago'},
        {'action': 'Course updated', 'course': 'Business English', 'time': '1 day ago'}
    ]

    return render_template('educator/dashboard.html',
                           user=convert_objectid_to_str(user),
                           courses=educator_courses,
                           total_students=total_students,
                           total_courses=total_courses,
                           avg_rating=avg_rating,
                           recent_activity=recent_activity)


@app.route('/educator/course/<course_id>')
@role_required(['educator'])
def educator_course_detail(course_id):
    user = get_current_user()

    # Get course
    course = CourseModel.find_course_by_id(course_id)
    if not course or course['instructor_id'] != str(user['_id']):
        flash('Course not found or access denied!', 'error')
        return redirect(url_for('educator_courses'))

    # Get enrolled students
    enrollments = EnrollmentModel.get_course_enrollments(course_id)
    enrolled_students = []

    for enrollment in enrollments:
        student = UserModel.find_user_by_id(enrollment['user_id'])
        if student:
            student_data = convert_objectid_to_str(student.copy())
            student_data.update({
                'progress': enrollment.get('progress', 0),
                'grade': enrollment.get('grade'),
                'enrolled_date': enrollment.get('enrolled_date')
            })
            enrolled_students.append(student_data)

    # Get course modules
    modules = ModuleModel.get_modules_by_course(course_id)
    course_modules = [convert_objectid_to_str(module) for module in modules]

    return render_template('educator/course_detail.html',
                           user=convert_objectid_to_str(user),
                           course=convert_objectid_to_str(course),
                           students=enrolled_students,
                           modules=course_modules)


@app.route('/educator/analytics')
@role_required(['educator'])
def educator_analytics():
    user = get_current_user()
    user_id = str(user['_id'])

    # Get filter parameters
    time_filter = request.args.get('time_filter', 'all_time')
    sort_by = request.args.get('sort_by', 'enrollment_desc')

    # Get educator's courses
    educator_courses = CourseModel.get_courses_by_instructor(user_id)

    # Get analytics for each course
    course_analytics = []
    total_students = 0
    total_courses = len(educator_courses)
    total_revenue = 0  # Placeholder for future implementation

    for course in educator_courses:
        course_id = str(course['_id'])

        # Get course enrollments
        enrollments = EnrollmentModel.get_course_enrollments(course_id)
        course_students = len(enrollments)
        total_students += course_students

        # Calculate completion rate
        completed_students = len([e for e in enrollments if e.get('progress', 0) >= 100])
        completion_rate = (completed_students / course_students * 100) if course_students > 0 else 0

        # Calculate average progress
        avg_progress = sum(e.get('progress', 0) for e in enrollments) / course_students if course_students > 0 else 0

        # Get quiz results for average score
        modules = ModuleModel.get_modules_by_course(course_id)
        all_quiz_results = []
        for module in modules:
            quizzes = QuizModel.get_quizzes_by_module(str(module['_id']))
            for quiz in quizzes:
                quiz_results = QuizResultModel.get_quiz_results(str(quiz['_id']))
                all_quiz_results.extend(quiz_results)

        avg_score = sum(r.get('score_percentage', 0) for r in all_quiz_results) / len(
            all_quiz_results) if all_quiz_results else 0

        # Apply time filter (placeholder - can be enhanced based on enrollment dates)
        filtered_enrollments = enrollments
        if time_filter == 'last_30_days':
            # Filter enrollments from last 30 days
            from datetime import datetime, timedelta
            cutoff_date = datetime.now() - timedelta(days=30)
            filtered_enrollments = [e for e in enrollments if e.get('enrolled_date', datetime.min) >= cutoff_date]
        elif time_filter == 'last_3_months':
            from datetime import datetime, timedelta
            cutoff_date = datetime.now() - timedelta(days=90)
            filtered_enrollments = [e for e in enrollments if e.get('enrolled_date', datetime.min) >= cutoff_date]
        elif time_filter == 'last_6_months':
            from datetime import datetime, timedelta
            cutoff_date = datetime.now() - timedelta(days=180)
            filtered_enrollments = [e for e in enrollments if e.get('enrolled_date', datetime.min) >= cutoff_date]

        analytics = {
            'total_students': len(filtered_enrollments),
            'completion_rate': completion_rate,
            'avg_score': round(avg_score, 1),
            'avg_progress': round(avg_progress, 1),
            'engagement_rate': min(100, max(0, avg_progress + (completion_rate * 0.3))),  # Calculated metric
            'quiz_count': len(all_quiz_results),
            'modules_count': len(modules)
        }

        course_analytics.append({
            'course': convert_objectid_to_str(course),
            'analytics': analytics,
            'enrollments': len(filtered_enrollments)
        })

    # Sort courses based on sort parameter
    if sort_by == 'enrollment_desc':
        course_analytics.sort(key=lambda x: x['enrollments'], reverse=True)
    elif sort_by == 'enrollment_asc':
        course_analytics.sort(key=lambda x: x['enrollments'])
    elif sort_by == 'completion_desc':
        course_analytics.sort(key=lambda x: x['analytics']['completion_rate'], reverse=True)
    elif sort_by == 'completion_asc':
        course_analytics.sort(key=lambda x: x['analytics']['completion_rate'])
    elif sort_by == 'score_desc':
        course_analytics.sort(key=lambda x: x['analytics']['avg_score'], reverse=True)
    elif sort_by == 'score_asc':
        course_analytics.sort(key=lambda x: x['analytics']['avg_score'])

    # Calculate overall statistics
    overall_completion = sum(ca['analytics']['completion_rate'] for ca in course_analytics) / len(
        course_analytics) if course_analytics else 0
    overall_avg_score = sum(ca['analytics']['avg_score'] for ca in course_analytics) / len(
        course_analytics) if course_analytics else 0

    return render_template('educator/analytics.html',
                           user=convert_objectid_to_str(user),
                           course_analytics=course_analytics,
                           total_students=total_students,
                           total_courses=total_courses,
                           overall_completion=round(overall_completion, 1),
                           overall_avg_score=round(overall_avg_score, 1),
                           time_filter=time_filter,
                           sort_by=sort_by)




@app.route('/educator/courses')
@role_required(['educator'])
def educator_courses():
    user = get_current_user()
    user_id = str(user['_id'])

    # Get filter parameters
    search = request.args.get('search', '').strip()
    status_filter = request.args.get('status', '')
    level_filter = request.args.get('level', '')
    sort_by = request.args.get('sort', 'created_desc')

    # Get educator's courses
    educator_courses = CourseModel.get_courses_by_instructor(user_id)

    # Apply filters
    filtered_courses = []
    for course in educator_courses:
        # Search filter (title or description)
        if search and search.lower() not in course.get('title', '').lower() and search.lower() not in course.get(
                'description', '').lower():
            continue

        # Status filter
        if status_filter and course.get('status') != status_filter:
            continue

        # Level filter
        if level_filter and course.get('level') != level_filter:
            continue

        filtered_courses.append(course)

    # Sort courses
    if sort_by == 'created_desc':
        filtered_courses.sort(key=lambda x: x.get('created_at', datetime.min), reverse=True)
    elif sort_by == 'created_asc':
        filtered_courses.sort(key=lambda x: x.get('created_at', datetime.min))
    elif sort_by == 'students_desc':
        filtered_courses.sort(key=lambda x: x.get('students_enrolled', 0), reverse=True)
    elif sort_by == 'rating_desc':
        filtered_courses.sort(key=lambda x: x.get('rating', 0), reverse=True)

    # Convert ObjectId to string
    courses_data = [convert_objectid_to_str(course) for course in filtered_courses]

    return render_template('educator/courses.html',
                           user=convert_objectid_to_str(user),
                           courses=courses_data)


@app.route('/educator/course/create')
@role_required(['educator'])
def educator_create_course():
    """Display course creation form"""
    user = get_current_user()
    return render_template('educator/create_course.html', user=convert_objectid_to_str(user))


@app.route('/educator/course/create', methods=['POST'])
@role_required(['educator'])
def educator_create_course_post():
    """Handle course creation"""
    user = get_current_user()
    user_id = str(user['_id'])

    try:
        # Get form data
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        level = request.form.get('level', 'Beginner')
        duration = request.form.get('duration', '').strip()
        category = request.form.get('category', 'General')

        # Validation
        if not title or not description:
            flash('Title and description are required!', 'error')
            return redirect(url_for('educator_create_course'))

        # Create course data
        course_data = {
            'title': title,
            'description': description,
            'level': level,
            'duration': duration,
            'category': category,
            'instructor': user['name'],
            'instructor_id': user_id,
            'status': 'draft',
            'students_enrolled': 0,
            'rating': 0.0,
            'image': request.form.get('image', '')
        }

        # Create course
        course_id = CourseModel.create_course(course_data)

        flash(f'Course "{title}" created successfully!', 'success')
        return redirect(url_for('educator_course_detail', course_id=course_id))

    except Exception as e:
        print(f"Error creating course: {e}")
        flash('An error occurred while creating the course. Please try again.', 'error')
        return redirect(url_for('educator_create_course'))


@app.route('/educator/course/<course_id>/edit')
@role_required(['educator'])
def educator_edit_course(course_id):
    """Display course edit form"""
    user = get_current_user()

    # Get course and verify ownership
    course = CourseModel.find_course_by_id(course_id)
    if not course or course['instructor_id'] != str(user['_id']):
        flash('Course not found or access denied!', 'error')
        return redirect(url_for('educator_courses'))

    return render_template('educator/edit_course.html',
                           user=convert_objectid_to_str(user),
                           course=convert_objectid_to_str(course))


@app.route('/educator/course/<course_id>/edit', methods=['POST'])
@role_required(['educator'])
def educator_edit_course_post(course_id):
    """Handle course editing"""
    user = get_current_user()

    # Get course and verify ownership
    course = CourseModel.find_course_by_id(course_id)
    if not course or course['instructor_id'] != str(user['_id']):
        flash('Course not found or access denied!', 'error')
        return redirect(url_for('educator_courses'))

    try:
        # Get form data
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        level = request.form.get('level', 'Beginner')
        duration = request.form.get('duration', '').strip()
        category = request.form.get('category', 'General')

        # Validation
        if not title or not description:
            flash('Title and description are required!', 'error')
            return redirect(url_for('educator_edit_course', course_id=course_id))

        # Update course data
        update_data = {
            'title': title,
            'description': description,
            'level': level,
            'duration': duration,
            'category': category,
            'image': request.form.get('image', course.get('image', ''))
        }

        # Update course
        CourseModel.update_course(course_id, update_data)

        flash(f'Course "{title}" updated successfully!', 'success')
        return redirect(url_for('educator_course_detail', course_id=course_id))

    except Exception as e:
        print(f"Error updating course: {e}")
        flash('An error occurred while updating the course. Please try again.', 'error')
        return redirect(url_for('educator_edit_course', course_id=course_id))


@app.route('/educator/course/<course_id>/publish', methods=['POST'])
@role_required(['educator'])
def educator_publish_course(course_id):
    """Publish a course"""
    user = get_current_user()

    # Get course and verify ownership
    course = CourseModel.find_course_by_id(course_id)
    if not course or course['instructor_id'] != str(user['_id']):
        return jsonify({'success': False, 'message': 'Course not found or access denied'}), 403

    try:
        # Check if course has minimum requirements
        modules = ModuleModel.get_modules_by_course(course_id)
        if len(modules) == 0:
            return jsonify({'success': False, 'message': 'Course must have at least one module to be published'}), 400

        # Update course status
        CourseModel.update_course(course_id, {'status': 'published'})

        return jsonify({'success': True, 'message': 'Course published successfully'})

    except Exception as e:
        print(f"Error publishing course: {e}")
        return jsonify({'success': False, 'message': 'An error occurred while publishing the course'}), 500


@app.route('/educator/course/<course_id>/unpublish', methods=['POST'])
@role_required(['educator'])
def educator_unpublish_course(course_id):
    """Unpublish a course"""
    user = get_current_user()

    # Get course and verify ownership
    course = CourseModel.find_course_by_id(course_id)
    if not course or course['instructor_id'] != str(user['_id']):
        return jsonify({'success': False, 'message': 'Course not found or access denied'}), 403

    try:
        # Update course status
        CourseModel.update_course(course_id, {'status': 'draft'})

        return jsonify({'success': True, 'message': 'Course unpublished successfully'})

    except Exception as e:
        print(f"Error unpublishing course: {e}")
        return jsonify({'success': False, 'message': 'An error occurred while unpublishing the course'}), 500


@app.route('/educator/course/<course_id>/duplicate', methods=['POST'])
@role_required(['educator'])
def educator_duplicate_course(course_id):
    """Duplicate a course"""
    user = get_current_user()
    user_id = str(user['_id'])

    # Get course and verify ownership
    course = CourseModel.find_course_by_id(course_id)
    if not course or course['instructor_id'] != str(user['_id']):
        return jsonify({'success': False, 'message': 'Course not found or access denied'}), 403

    try:
        # Create duplicate course data
        duplicate_data = course.copy()
        duplicate_data.pop('_id', None)  # Remove original ID
        duplicate_data['title'] = f"{course['title']} (Copy)"
        duplicate_data['status'] = 'draft'
        duplicate_data['students_enrolled'] = 0
        duplicate_data['rating'] = 0.0
        duplicate_data['created_at'] = datetime.now()
        duplicate_data['updated_at'] = datetime.now()

        # Create duplicate course
        new_course_id = CourseModel.create_course(duplicate_data)

        # Duplicate modules
        original_modules = ModuleModel.get_modules_by_course(course_id)
        for module in original_modules:
            module_data = module.copy()
            module_data.pop('_id', None)  # Remove original ID
            module_data['course_id'] = new_course_id
            module_data['completed_by'] = []
            ModuleModel.create_module(module_data)

        return jsonify({'success': True, 'message': 'Course duplicated successfully'})

    except Exception as e:
        print(f"Error duplicating course: {e}")
        return jsonify({'success': False, 'message': 'An error occurred while duplicating the course'}), 500


@app.route('/educator/course/<course_id>/delete', methods=['DELETE'])
@role_required(['educator'])
def educator_delete_course(course_id):
    """Delete a course"""
    user = get_current_user()

    # Get course and verify ownership
    course = CourseModel.find_course_by_id(course_id)
    if not course or course['instructor_id'] != str(user['_id']):
        return jsonify({'success': False, 'message': 'Course not found or access denied'}), 403

    try:
        # Check if course has enrolled students
        enrollments = EnrollmentModel.get_course_enrollments(course_id)
        if enrollments:
            return jsonify({'success': False, 'message': 'Cannot delete course with enrolled students'}), 400

        # Delete related modules first
        modules = ModuleModel.get_modules_by_course(course_id)
        for module in modules:
            # Delete related quizzes
            quizzes = QuizModel.get_quizzes_by_module(str(module['_id']))
            for quiz in quizzes:
                QuizModel.delete_quiz(str(quiz['_id']))

            # Delete module
            ModuleModel.delete_module(str(module['_id']))

        # Delete course
        CourseModel.delete_course(course_id)

        return jsonify({'success': True, 'message': 'Course deleted successfully'})

    except Exception as e:
        print(f"Error deleting course: {e}")
        return jsonify({'success': False, 'message': 'An error occurred while deleting the course'}), 500


@app.route('/educator/course/<course_id>/analytics')
@role_required(['educator'])
def educator_course_analytics(course_id):
    """View detailed analytics for a specific course"""
    user = get_current_user()

    # Get course and verify ownership
    course = CourseModel.find_course_by_id(course_id)
    if not course or course['instructor_id'] != str(user['_id']):
        flash('Course not found or access denied!', 'error')
        return redirect(url_for('educator_courses'))

    # Get course analytics
    analytics = AnalyticsModel.get_course_analytics(course_id)
    if not analytics:
        # Create default analytics if none exist
        analytics = {
            'completion_rate': 0,
            'avg_score': 0,
            'engagement_rate': 85,  # Default value
            'total_time': '0 hours',
            'total_students': 0
        }

    # Get enrolled students with progress
    enrollments = EnrollmentModel.get_course_enrollments(course_id)
    student_progress = []

    for enrollment in enrollments:
        student = UserModel.find_user_by_id(enrollment['user_id'])
        if student:
            student_data = {
                'name': student['name'],
                'email': student['email'],
                'progress': enrollment.get('progress', 0),
                'grade': enrollment.get('grade'),
                'enrolled_date': enrollment.get('enrolled_date'),
                'last_activity': enrollment.get('last_activity', 'No recent activity')
            }
            student_progress.append(student_data)

    # Update analytics with current data
    if student_progress:
        total_students = len(student_progress)
        completed_students = len([s for s in student_progress if s['progress'] == 100])
        analytics['total_students'] = total_students
        analytics['completion_rate'] = (completed_students / total_students * 100) if total_students > 0 else 0
        analytics['avg_score'] = sum(
            s['progress'] for s in student_progress) / total_students if total_students > 0 else 0

    return render_template('educator/course_analytics.html',
                           user=convert_objectid_to_str(user),
                           course=convert_objectid_to_str(course),
                           analytics=analytics,
                           student_progress=student_progress)


@app.route('/educator/analytics/export')
@role_required(['educator'])
def educator_export_analytics():
    """Export all educator analytics as CSV"""
    user = get_current_user()
    user_id = str(user['_id'])

    try:
        # Get educator's courses
        educator_courses = CourseModel.get_courses_by_instructor(user_id)

        # Create CSV data
        csv_data = []
        csv_data.append([
            'Course Title', 'Level', 'Status', 'Total Students', 'Completion Rate (%)',
            'Average Score (%)', 'Average Progress (%)', 'Total Modules', 'Quiz Count',
            'Created Date', 'Last Updated'
        ])

        for course in educator_courses:
            course_id = str(course['_id'])

            # Get course statistics
            enrollments = EnrollmentModel.get_course_enrollments(course_id)
            course_students = len(enrollments)
            completed_students = len([e for e in enrollments if e.get('progress', 0) >= 100])
            completion_rate = (completed_students / course_students * 100) if course_students > 0 else 0
            avg_progress = sum(
                e.get('progress', 0) for e in enrollments) / course_students if course_students > 0 else 0

            # Get modules and quizzes
            modules = ModuleModel.get_modules_by_course(course_id)
            all_quiz_results = []
            for module in modules:
                quizzes = QuizModel.get_quizzes_by_module(str(module['_id']))
                for quiz in quizzes:
                    quiz_results = QuizResultModel.get_quiz_results(str(quiz['_id']))
                    all_quiz_results.extend(quiz_results)

            avg_score = sum(r.get('score_percentage', 0) for r in all_quiz_results) / len(
                all_quiz_results) if all_quiz_results else 0

            csv_data.append([
                course.get('title', 'N/A'),
                course.get('level', 'N/A'),
                course.get('status', 'N/A'),
                course_students,
                round(completion_rate, 2),
                round(avg_score, 2),
                round(avg_progress, 2),
                len(modules),
                len(all_quiz_results),
                course.get('created_at', 'Unknown'),
                course.get('updated_at', 'Unknown')
            ])

        # Create CSV response
        import io
        import csv
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerows(csv_data)

        # Create response
        from flask import Response
        response = Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename=educator_analytics_report.csv'}
        )

        return response

    except Exception as e:
        print(f"Error exporting analytics: {e}")
        flash('An error occurred while exporting analytics.', 'error')
        return redirect(url_for('educator_analytics'))

# Optional: Export analytics route
@app.route('/educator/course/<course_id>/analytics/export')
@role_required(['educator'])
def educator_export_course_analytics(course_id):
    """Export individual course analytics as CSV"""
    user = get_current_user()

    # Get course and verify ownership
    course = CourseModel.find_course_by_id(course_id)
    if not course or course['instructor_id'] != str(user['_id']):
        flash('Course not found or access denied!', 'error')
        return redirect(url_for('educator_courses'))

    try:
        # Get enrolled students with detailed progress
        enrollments = EnrollmentModel.get_course_enrollments(course_id)

        # Create detailed CSV data
        csv_data = []
        csv_data.append([
            'Student Name', 'Email', 'Progress (%)', 'Grade', 'Enrolled Date',
            'Last Activity', 'Modules Completed', 'Quiz Attempts', 'Average Quiz Score (%)'
        ])

        for enrollment in enrollments:
            student = UserModel.find_user_by_id(enrollment['user_id'])
            if student:
                # Get student quiz results
                modules = ModuleModel.get_modules_by_course(course_id)
                student_quiz_results = []
                for module in modules:
                    quizzes = QuizModel.get_quizzes_by_module(str(module['_id']))
                    for quiz in quizzes:
                        results = QuizResultModel.find_result(enrollment['user_id'], str(quiz['_id']))
                        if results:
                            student_quiz_results.append(results)

                avg_quiz_score = sum(r.get('score_percentage', 0) for r in student_quiz_results) / len(
                    student_quiz_results) if student_quiz_results else 0

                csv_data.append([
                    student['name'],
                    student['email'],
                    enrollment.get('progress', 0),
                    enrollment.get('grade', 'N/A'),
                    enrollment.get('enrolled_date', 'Unknown'),
                    enrollment.get('last_activity', 'No recent activity'),
                    len(enrollment.get('completed_modules', [])),
                    len(student_quiz_results),
                    round(avg_quiz_score, 2)
                ])

        # Create CSV response
        import io
        import csv
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerows(csv_data)

        # Create response
        from flask import Response
        response = Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename={course["title"]}_detailed_analytics.csv'}
        )

        return response

    except Exception as e:
        print(f"Error exporting course analytics: {e}")
        flash('An error occurred while exporting course analytics.', 'error')
        return redirect(url_for('educator_analytics'))


# API endpoint for dynamic filtering (AJAX)
@app.route('/api/educator/analytics/filter')
@role_required(['educator'])
def api_educator_analytics_filter():
    """API endpoint for filtering analytics data"""
    user = get_current_user()
    user_id = str(user['_id'])

    time_filter = request.args.get('time_filter', 'all_time')
    sort_by = request.args.get('sort_by', 'enrollment_desc')

    try:
        # Get educator's courses
        educator_courses = CourseModel.get_courses_by_instructor(user_id)

        # Get analytics for each course (similar to main analytics route)
        course_analytics = []
        for course in educator_courses:
            course_id = str(course['_id'])
            enrollments = EnrollmentModel.get_course_enrollments(course_id)

            # Apply time filter
            filtered_enrollments = enrollments
            if time_filter == 'last_30_days':
                from datetime import datetime, timedelta
                cutoff_date = datetime.now() - timedelta(days=30)
                filtered_enrollments = [e for e in enrollments if e.get('enrolled_date', datetime.min) >= cutoff_date]
            elif time_filter == 'last_3_months':
                from datetime import datetime, timedelta
                cutoff_date = datetime.now() - timedelta(days=90)
                filtered_enrollments = [e for e in enrollments if e.get('enrolled_date', datetime.min) >= cutoff_date]
            elif time_filter == 'last_6_months':
                from datetime import datetime, timedelta
                cutoff_date = datetime.now() - timedelta(days=180)
                filtered_enrollments = [e for e in enrollments if e.get('enrolled_date', datetime.min) >= cutoff_date]

            # Calculate metrics
            course_students = len(filtered_enrollments)
            completed_students = len([e for e in filtered_enrollments if e.get('progress', 0) >= 100])
            completion_rate = (completed_students / course_students * 100) if course_students > 0 else 0
            avg_progress = sum(
                e.get('progress', 0) for e in filtered_enrollments) / course_students if course_students > 0 else 0

            course_analytics.append({
                'course_id': course_id,
                'course_title': course['title'],
                'total_students': course_students,
                'completion_rate': round(completion_rate, 1),
                'avg_progress': round(avg_progress, 1)
            })

        # Sort based on sort_by parameter
        if sort_by == 'enrollment_desc':
            course_analytics.sort(key=lambda x: x['total_students'], reverse=True)
        elif sort_by == 'enrollment_asc':
            course_analytics.sort(key=lambda x: x['total_students'])
        elif sort_by == 'completion_desc':
            course_analytics.sort(key=lambda x: x['completion_rate'], reverse=True)
        elif sort_by == 'completion_asc':
            course_analytics.sort(key=lambda x: x['completion_rate'])

        return jsonify({
            'success': True,
            'data': course_analytics
        })

    except Exception as e:
        print(f"Error filtering analytics: {e}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while filtering analytics data'
        }), 500

@app.route('/educator/course/<course_id>/module/create', methods=['POST'])
@role_required(['educator'])
def educator_create_module(course_id):
    """Create a new module for a course"""
    user = get_current_user()

    # Get course and verify ownership
    course = CourseModel.find_course_by_id(course_id)
    if not course or course['instructor_id'] != str(user['_id']):
        return jsonify({'success': False, 'message': 'Course not found or access denied'}), 403

    try:
        # Get JSON data from request
        data = request.get_json()

        # Validation
        title = data.get('title', '').strip()
        if not title:
            return jsonify({'success': False, 'message': 'Module title is required'}), 400

        # Get next order number
        existing_modules = ModuleModel.get_modules_by_course(course_id)
        next_order = len(existing_modules) + 1

        # Create module data
        module_data = {
            'title': title,
            'course_id': course_id,
            'type': data.get('type', 'lesson'),
            'content': data.get('content', ''),
            'duration': data.get('duration', ''),
            'order': next_order
        }

        # Create module
        module_id = ModuleModel.create_module(module_data)

        return jsonify({'success': True, 'message': 'Module created successfully', 'module_id': module_id})

    except Exception as e:
        print(f"Error creating module: {e}")
        return jsonify({'success': False, 'message': 'An error occurred while creating the module'}), 500


@app.route('/educator/module/<module_id>/edit')
@role_required(['educator'])
def educator_edit_module(module_id):
    """Display module edit form"""
    user = get_current_user()

    # Get module
    module = ModuleModel.find_module_by_id(module_id)
    if not module:
        flash('Module not found!', 'error')
        return redirect(url_for('educator_courses'))

    # Get course and verify ownership
    course = CourseModel.find_course_by_id(module['course_id'])
    if not course or course['instructor_id'] != str(user['_id']):
        flash('Course not found or access denied!', 'error')
        return redirect(url_for('educator_courses'))

    return render_template('educator/edit_module.html',
                           user=convert_objectid_to_str(user),
                           course=convert_objectid_to_str(course),
                           module=convert_objectid_to_str(module))


@app.route('/educator/module/<module_id>/edit', methods=['POST'])
@role_required(['educator'])
def educator_edit_module_post(module_id):
    """Handle module editing"""
    user = get_current_user()

    # Get module
    module = ModuleModel.find_module_by_id(module_id)
    if not module:
        return jsonify({'success': False, 'message': 'Module not found'}), 404

    # Get course and verify ownership
    course = CourseModel.find_course_by_id(module['course_id'])
    if not course or course['instructor_id'] != str(user['_id']):
        return jsonify({'success': False, 'message': 'Access denied'}), 403

    try:
        # Get form data
        data = request.get_json() if request.is_json else request.form

        title = data.get('title', '').strip()
        if not title:
            return jsonify({'success': False, 'message': 'Module title is required'}), 400

        # Update module data
        update_data = {
            'title': title,
            'type': data.get('type', module.get('type', 'lesson')),
            'content': data.get('content', ''),
            'duration': data.get('duration', ''),
            'updated_at': datetime.now()
        }

        # Update module
        ModuleModel.update_module(module_id, update_data)

        if request.is_json:
            return jsonify({'success': True, 'message': 'Module updated successfully'})
        else:
            flash('Module updated successfully!', 'success')
            return redirect(url_for('educator_course_detail', course_id=course['_id']))

    except Exception as e:
        print(f"Error updating module: {e}")
        if request.is_json:
            return jsonify({'success': False, 'message': 'An error occurred while updating the module'}), 500
        else:
            flash('An error occurred while updating the module.', 'error')
            return redirect(url_for('educator_edit_module', module_id=module_id))

@app.route('/educator/course/<course_id>/export')
@role_required(['educator'])
def educator_export_course_reports(course_id):
    """Export course reports as CSV"""
    user = get_current_user()

    # Get course and verify ownership
    course = CourseModel.find_course_by_id(course_id)
    if not course or course['instructor_id'] != str(user['_id']):
        flash('Course not found or access denied!', 'error')
        return redirect(url_for('educator_courses'))

    try:
        # Get enrolled students with progress
        enrollments = EnrollmentModel.get_course_enrollments(course_id)

        # Create CSV data
        csv_data = []
        csv_data.append(['Student Name', 'Email', 'Progress (%)', 'Grade', 'Enrolled Date', 'Modules Completed'])

        for enrollment in enrollments:
            student = UserModel.find_user_by_id(enrollment['user_id'])
            if student:
                csv_data.append([
                    student['name'],
                    student['email'],
                    enrollment.get('progress', 0),
                    enrollment.get('grade', 'N/A'),
                    enrollment.get('enrolled_date', 'Unknown'),
                    len(enrollment.get('completed_modules', []))
                ])

        # Create CSV response
        import io
        import csv
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerows(csv_data)

        # Create response
        from flask import Response
        response = Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename={course["title"]}_report.csv'}
        )

        return response

    except Exception as e:
        print(f"Error exporting reports: {e}")
        flash('An error occurred while exporting reports.', 'error')
        return redirect(url_for('educator_course_detail', course_id=course_id))


@app.route('/educator/student/<student_id>/details')
@role_required(['educator'])
def educator_student_details(student_id):
    """View student details (placeholder for future implementation)"""
    flash('Student details view will be implemented in a future update.', 'info')
    return redirect(url_for('educator_courses'))


@app.route('/educator/edit-module/<module_id>')
@role_required(['educator'])
def educator_edit_module_page(module_id):  # RENAMED FUNCTION
    """Show edit module page"""
    user = get_current_user()

    # Get module
    module = ModuleModel.find_module_by_id(module_id)
    if not module:
        flash('Module not found!', 'error')
        return redirect(url_for('educator_courses'))

    # Get course and verify ownership
    course = CourseModel.find_course_by_id(module['course_id'])
    if not course or course['instructor_id'] != str(user['_id']):
        flash('Course not found or access denied!', 'error')
        return redirect(url_for('educator_courses'))

    return render_template('educator/edit_module.html',
                           user=convert_objectid_to_str(user),
                           course=convert_objectid_to_str(course),
                           module=convert_objectid_to_str(module))


@app.route('/educator/edit-module/<module_id>', methods=['POST'])
@role_required(['educator'])
def educator_edit_module_submit(module_id):  # RENAMED FUNCTION
    """Update module"""
    user = get_current_user()

    # Get module
    module = ModuleModel.find_module_by_id(module_id)
    if not module:
        if request.is_json:
            return jsonify({'success': False, 'message': 'Module not found'}), 404
        else:
            flash('Module not found!', 'error')
            return redirect(url_for('educator_courses'))

    # Get course and verify ownership
    course = CourseModel.find_course_by_id(module['course_id'])
    if not course or course['instructor_id'] != str(user['_id']):
        if request.is_json:
            return jsonify({'success': False, 'message': 'Access denied'}), 403
        else:
            flash('Course not found or access denied!', 'error')
            return redirect(url_for('educator_courses'))

    try:
        # Get form data
        update_data = {
            'title': request.form.get('title', '').strip(),
            'content': request.form.get('content', '').strip(),
            'type': request.form.get('type', 'lesson'),
            'duration': request.form.get('duration', '').strip(),
            'order': int(request.form.get('order', module.get('order', 1))),
            'prerequisites': request.form.get('prerequisites', '').strip(),
            'objectives': request.form.get('objectives', '').strip(),
            'video_url': request.form.get('video_url', '').strip(),
            'resources': request.form.get('resources', '').strip(),
            'updated_at': datetime.now()
        }

        # Validate required fields
        if not update_data['title'] or not update_data['content']:
            message = 'Title and content are required'
            if request.is_json:
                return jsonify({'success': False, 'message': message}), 400
            else:
                flash(message, 'error')
                return redirect(url_for('educator_edit_module_page', module_id=module_id))

        # Check if saving as draft
        if request.form.get('save_as_draft'):
            update_data['status'] = 'draft'

        # Update module
        ModuleModel.update_module(module_id, update_data)

        message = 'Module updated successfully!'
        if request.is_json:
            return jsonify({'success': True, 'message': message})
        else:
            flash(message, 'success')
            return redirect(url_for('educator_course_detail', course_id=course['_id']))

    except Exception as e:
        print(f"Error updating module: {e}")
        message = 'An error occurred while updating the module'
        if request.is_json:
            return jsonify({'success': False, 'message': message}), 500
        else:
            flash(message, 'error')
            return redirect(url_for('educator_edit_module_page', module_id=module_id))


@app.route('/educator/module/<module_id>/analytics')
@role_required(['educator'])
def educator_module_analytics_page(module_id):  # RENAMED FUNCTION
    """View module analytics"""
    user = get_current_user()

    # Get module
    module = ModuleModel.find_module_by_id(module_id)
    if not module:
        flash('Module not found!', 'error')
        return redirect(url_for('educator_courses'))

    # Get course and verify ownership
    course = CourseModel.find_course_by_id(module['course_id'])
    if not course or course['instructor_id'] != str(user['_id']):
        flash('Course not found or access denied!', 'error')
        return redirect(url_for('educator_courses'))

    # Get module completion stats
    total_students = len(EnrollmentModel.get_course_enrollments(str(course['_id'])))
    completed_students = len(module.get('completed_by', []))
    completion_rate = (completed_students / total_students * 100) if total_students > 0 else 0

    # Get quiz results if module has quizzes
    quiz_results = []
    try:
        # Try to get assessments, handle if not implemented
        if hasattr(AssessmentModel, 'get_assessments_by_module'):
            assessments = AssessmentModel.get_assessments_by_module(module_id)
            for quiz in assessments:
                if hasattr(QuizResultModel, 'get_quiz_results'):
                    results = QuizResultModel.get_quiz_results(str(quiz['_id']))
                    quiz_results.extend(results)
    except Exception as e:
        print(f"Quiz functionality not available: {e}")
        quiz_results = []

    analytics_data = {
        'total_students': total_students,
        'completed_students': completed_students,
        'completion_rate': completion_rate,
        'quiz_results': quiz_results,
        'avg_quiz_score': sum(r.get('score_percentage', 0) for r in quiz_results) / len(
            quiz_results) if quiz_results else 0
    }

    return render_template('educator/module_analytics.html',
                           user=convert_objectid_to_str(user),
                           course=convert_objectid_to_str(course),
                           module=convert_objectid_to_str(module),
                           analytics=analytics_data)


@app.route('/educator/module/<module_id>/duplicate', methods=['POST'])
@role_required(['educator'])
def educator_duplicate_module_action(module_id):  # RENAMED FUNCTION
    """Duplicate a module"""
    user = get_current_user()

    # Get module
    module = ModuleModel.find_module_by_id(module_id)
    if not module:
        return jsonify({'success': False, 'message': 'Module not found'}), 404

    # Get course and verify ownership
    course = CourseModel.find_course_by_id(module['course_id'])
    if not course or course['instructor_id'] != str(user['_id']):
        return jsonify({'success': False, 'message': 'Access denied'}), 403

    try:
        # Create duplicate module data
        duplicate_data = module.copy()
        duplicate_data.pop('_id', None)  # Remove original ID
        duplicate_data['title'] = f"{module['title']} (Copy)"
        duplicate_data['created_at'] = datetime.now()
        duplicate_data['completed_by'] = []

        # Get next order number
        existing_modules = ModuleModel.get_modules_by_course(module['course_id'])
        duplicate_data['order'] = len(existing_modules) + 1

        # Create duplicate module
        new_module_id = ModuleModel.create_module(duplicate_data)

        return jsonify({'success': True, 'message': 'Module duplicated successfully'})

    except Exception as e:
        print(f"Error duplicating module: {e}")
        return jsonify({'success': False, 'message': 'An error occurred while duplicating the module'}), 500


@app.route('/educator/module/<module_id>/delete', methods=['DELETE'])
@role_required(['educator'])
def educator_delete_module_action(module_id):  # RENAMED FUNCTION
    """Delete a module"""
    user = get_current_user()

    # Get module
    module = ModuleModel.find_module_by_id(module_id)
    if not module:
        return jsonify({'success': False, 'message': 'Module not found'}), 404

    # Get course and verify ownership
    course = CourseModel.find_course_by_id(module['course_id'])
    if not course or course['instructor_id'] != str(user['_id']):
        return jsonify({'success': False, 'message': 'Access denied'}), 403

    try:
        # Check if module has students who completed it
        if module.get('completed_by') and len(module['completed_by']) > 0:
            return jsonify(
                {'success': False, 'message': 'Cannot delete module that has been completed by students'}), 400

        # Delete related assessments first
        try:
            if hasattr(AssessmentModel, 'get_assessments_by_module'):
                assessments = AssessmentModel.get_assessments_by_module(module_id)
                for assessment in assessments:
                    if hasattr(AssessmentModel, 'delete_assessment'):
                        AssessmentModel.delete_assessment(str(assessment['_id']))
        except Exception as e:
            print(f"Assessment cleanup error (non-critical): {e}")

        # Delete module
        ModuleModel.delete_module(module_id)

        return jsonify({'success': True, 'message': 'Module deleted successfully'})

    except Exception as e:
        print(f"Error deleting module: {e}")
        return jsonify({'success': False, 'message': 'An error occurred while deleting the module'}), 500


@app.route('/educator/add-module', methods=['POST'])
@role_required(['educator'])
def educator_add_module_action():  # RENAMED FUNCTION
    """Add new module to course"""
    user = get_current_user()

    try:
        course_id = request.form.get('course_id')

        # Verify course ownership
        course = CourseModel.find_course_by_id(course_id)
        if not course or course['instructor_id'] != str(user['_id']):
            return jsonify({'success': False, 'message': 'Access denied'}), 403

        # Get existing modules to determine order
        existing_modules = ModuleModel.get_modules_by_course(course_id)
        next_order = len(existing_modules) + 1

        # Create module data
        module_data = {
            'course_id': course_id,
            'title': request.form.get('title', '').strip(),
            'content': request.form.get('content', '').strip(),
            'type': request.form.get('type', 'lesson'),
            'duration': request.form.get('duration', '').strip(),
            'order': next_order,
            'created_at': datetime.now(),
            'completed_by': []
        }

        # Validate required fields
        if not module_data['title'] or not module_data['content']:
            return jsonify({'success': False, 'message': 'Title and content are required'}), 400

        # Create module
        module_id = ModuleModel.create_module(module_data)

        return jsonify({'success': True, 'message': 'Module added successfully', 'module_id': module_id})

    except Exception as e:
        print(f"Error adding module: {e}")
        return jsonify({'success': False, 'message': 'An error occurred while adding the module'}), 500


@app.route('/educator/module/<module_id>/analytics/export')
@role_required(['educator'])
def educator_export_module_analytics_csv(module_id):  # RENAMED FUNCTION
    """Export module analytics as CSV"""
    user = get_current_user()

    # Get module
    module = ModuleModel.find_module_by_id(module_id)
    if not module:
        flash('Module not found!', 'error')
        return redirect(url_for('educator_courses'))

    # Get course and verify ownership
    course = CourseModel.find_course_by_id(module['course_id'])
    if not course or course['instructor_id'] != str(user['_id']):
        flash('Course not found or access denied!', 'error')
        return redirect(url_for('educator_courses'))

    try:
        # Get module analytics data
        total_students = len(EnrollmentModel.get_course_enrollments(str(course['_id'])))
        completed_students = len(module.get('completed_by', []))
        completion_rate = (completed_students / total_students * 100) if total_students > 0 else 0

        # Get quiz results
        quiz_results = []
        try:
            if hasattr(AssessmentModel, 'get_assessments_by_module'):
                assessments = AssessmentModel.get_assessments_by_module(module_id)
                for assessment in assessments:
                    if hasattr(QuizResultModel, 'get_quiz_results'):
                        results = QuizResultModel.get_quiz_results(str(assessment['_id']))
                        quiz_results.extend(results)
        except Exception as e:
            print(f"Quiz results error (non-critical): {e}")
            quiz_results = []

        # Create CSV data
        csv_data = []
        csv_data.append([
            'Module Title', 'Module Type', 'Total Students', 'Completed Students',
            'Completion Rate (%)', 'Quiz Attempts', 'Average Quiz Score (%)',
            'Duration', 'Created Date'
        ])

        avg_quiz_score = sum(r.get('score_percentage', 0) for r in quiz_results) / len(
            quiz_results) if quiz_results else 0

        csv_data.append([
            module.get('title', 'N/A'),
            module.get('type', 'N/A'),
            total_students,
            completed_students,
            round(completion_rate, 2),
            len(quiz_results),
            round(avg_quiz_score, 2),
            module.get('duration', 'N/A'),
            module.get('created_at', 'Unknown')
        ])

        # Create CSV response
        import io
        import csv
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerows(csv_data)

        # Create response
        from flask import Response
        response = Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename=module_analytics_{module_id}.csv'}
        )

        return response

    except Exception as e:
        print(f"Error exporting module analytics: {e}")
        flash('An error occurred while exporting module analytics.', 'error')
        return redirect(url_for('educator_module_analytics_page', module_id=module_id))



# =====================================================
# EDUCATOR LEADERBOARD ROUTES
# =====================================================

@app.route('/educator/course/<course_id>/leaderboard')
@role_required(['educator'])
def course_leaderboard(course_id):
    """View course leaderboard"""
    user = get_current_user()

    # Get course and verify ownership
    course = CourseModel.find_course_by_id(course_id)
    if not course or course['instructor_id'] != str(user['_id']):
        flash('Course not found or access denied!', 'error')
        return redirect(url_for('educator_courses'))

    # Get leaderboard data
    leaderboard_data = LeaderboardModel.get_course_leaderboard(course_id)

    return render_template('educator/leaderboard.html',
                           user=convert_objectid_to_str(user),
                           course=convert_objectid_to_str(course),
                           leaderboard=leaderboard_data)


@app.route('/educator/course/<course_id>/quiz/<quiz_id>/results')
@role_required(['educator'])
def quiz_results_overview(course_id, quiz_id):
    """View all quiz results for a specific quiz"""
    user = get_current_user()

    # Get course and verify ownership
    course = CourseModel.find_course_by_id(course_id)
    if not course or course['instructor_id'] != str(user['_id']):
        flash('Course not found or access denied!', 'error')
        return redirect(url_for('educator_courses'))

    # Get quiz details
    quiz = QuizModel.find_quiz_by_id(quiz_id)
    if not quiz:
        flash('Quiz not found!', 'error')
        return redirect(url_for('educator_course_detail', course_id=course_id))

    # Get all results for this quiz
    results = QuizResultModel.get_quiz_results(quiz_id)

    # Get user details for each result
    enhanced_results = []
    for result in results:
        student = UserModel.find_user_by_id(result['user_id'])
        if student:
            result_data = convert_objectid_to_str(result.copy())
            result_data['student'] = convert_objectid_to_str(student)
            enhanced_results.append(result_data)

    # Sort by score descending
    enhanced_results.sort(key=lambda x: x['score_percentage'], reverse=True)

    return render_template('educator/quiz_results.html',
                           user=convert_objectid_to_str(user),
                           course=convert_objectid_to_str(course),
                           quiz=convert_objectid_to_str(quiz),
                           results=enhanced_results)


# =====================================================
# ADMIN ROUTES
# =====================================================

@app.route('/admin/dashboard')
@role_required(['admin'])
def admin_dashboard():
    user = get_current_user()

    # Get or update system stats
    stats = AnalyticsModel.get_system_analytics()
    if not stats:
        stats = AnalyticsModel.update_system_stats()

    # Recent system activity
    recent_activity = [
        {'action': 'New user registered', 'details': 'student@example.com', 'time': '30 minutes ago'},
        {'action': 'Course published', 'details': 'Advanced Grammar', 'time': '2 hours ago'},
        {'action': 'System backup completed', 'details': 'Scheduled backup', 'time': '6 hours ago'}
    ]

    return render_template('admin/dashboard.html',
                           user=convert_objectid_to_str(user),
                           stats=stats,
                           recent_activity=recent_activity)


@app.route('/admin/users')
@role_required(['admin'])
def admin_users():
    user = get_current_user()

    # Get filter parameters
    search = request.args.get('search', '').strip()
    role_filter = request.args.get('role', '')
    status_filter = request.args.get('status', '')

    # Get all users
    all_users = UserModel.get_all_users()
    users_data = []

    for user_data in all_users:
        user_info = convert_objectid_to_str(user_data.copy())

        # Add enrollment count for students
        if user_data.get('role') == 'student':
            enrollments = EnrollmentModel.get_user_enrollments(str(user_data['_id']))
            user_info['enrolled_courses'] = len(enrollments)

        # Ensure status field exists (default to 'active' for existing users)
        user_info['status'] = user_data.get('status', 'active')

        users_data.append(user_info)

    # Apply filters
    filtered_users = users_data

    # Search filter (name or email)
    if search:
        filtered_users = [
            u for u in filtered_users
            if search.lower() in u['name'].lower() or search.lower() in u['email'].lower()
        ]

    # Role filter
    if role_filter:
        filtered_users = [u for u in filtered_users if u['role'] == role_filter]

    # Status filter
    if status_filter:
        filtered_users = [u for u in filtered_users if u['status'] == status_filter]

    return render_template('admin/users.html',
                           user=convert_objectid_to_str(user),
                           all_users=filtered_users,
                           search=search,
                           role_filter=role_filter,
                           status_filter=status_filter)


# Add new user
@app.route('/admin/user/add', methods=['POST'])
@role_required(['admin'])
def admin_add_user():
    current_admin = get_current_user()

    try:
        # Get form data
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        role = request.form.get('role', 'student')

        # Validation
        if not name or not email or not password:
            flash('Name, email, and password are required!', 'error')
            return redirect(url_for('admin_users'))

        if len(password) < 6:
            flash('Password must be at least 6 characters long!', 'error')
            return redirect(url_for('admin_users'))

        # Check if user already exists
        existing_user = UserModel.find_user_by_email(email)
        if existing_user:
            flash('A user with this email already exists!', 'error')
            return redirect(url_for('admin_users'))

        # Create user data
        user_data = {
            'name': name,
            'email': email,
            'password': password,  # Will be hashed in UserModel.create_user
            'role': role,
            'avatar': '/static/images/default.jpg',
            'status': 'active',  # NEW: Set default status to active
            'created_by': str(current_admin['_id'])
        }

        # Add role-specific fields
        if role == 'student':
            user_data.update({
                'level': 'Beginner',
                'points': 0,
                'badges': []
            })
        elif role == 'educator':
            user_data.update({
                'department': request.form.get('department', ''),
                'experience': request.form.get('experience', '0 years')
            })
        elif role == 'content_manager':
            user_data.update({
                'content_manager_permissions': ['course_creation', 'content_management', 'module_management'],
                'assigned_to_content_manager_at': datetime.now()
            })
        elif role == 'admin':
            user_data.update({
                'admin_permissions': ['user_management', 'course_management', 'analytics'],
                'upgraded_to_admin_at': datetime.now()
            })

        # Create user
        user_id = UserModel.create_user(user_data)
        flash(f'User "{name}" has been created successfully with active status!', 'success')

        # Log the action
        print(f"AUDIT: {current_admin['name']} created new user: {name} ({email}) with role: {role} and status: active")

    except Exception as e:
        print(f"Error creating user: {e}")
        flash('An error occurred while creating the user. Please try again.', 'error')

    return redirect(url_for('admin_users'))

# View user details
@app.route('/admin/user/<user_id>/view')
@role_required(['admin'])
def admin_view_user(user_id):
    user = UserModel.find_user_by_id(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Get additional user statistics
    user_stats = {}
    if user.get('role') == 'student':
        enrollments = EnrollmentModel.get_user_enrollments(user_id)
        user_stats = {
            'total_enrollments': len(enrollments),
            'completed_courses': len([e for e in enrollments if e.get('progress', 0) == 100]),
            'average_progress': sum(e.get('progress', 0) for e in enrollments) / len(enrollments) if enrollments else 0
        }
    elif user.get('role') == 'educator':
        courses = CourseModel.get_courses_by_instructor(user_id)
        user_stats = {
            'total_courses': len(courses),
            'total_students': sum(course.get('students_enrolled', 0) for course in courses)
        }

    user_data = convert_objectid_to_str(user.copy())
    user_data['stats'] = user_stats

    return jsonify(user_data)


# Edit user
@app.route('/admin/user/<user_id>/edit', methods=['POST'])
@role_required(['admin'])
def admin_edit_user(user_id):
    current_admin = get_current_user()

    # Get the target user
    target_user = UserModel.find_user_by_id(user_id)
    if not target_user:
        flash('User not found!', 'error')
        return redirect(url_for('admin_users'))

    try:
        # Get form data
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()

        # Validation
        if not name or not email:
            flash('Name and email are required!', 'error')
            return redirect(url_for('admin_users'))

        # Check if email is already taken by another user
        existing_user = UserModel.find_user_by_email(email)
        if existing_user and str(existing_user['_id']) != user_id:
            flash('This email is already taken by another user!', 'error')
            return redirect(url_for('admin_users'))

        # Prepare update data
        update_data = {
            'name': name,
            'email': email,
            'updated_by': str(current_admin['_id'])
        }

        # Add role-specific fields if provided
        role = target_user.get('role')
        if role == 'educator':
            department = request.form.get('department', '')
            experience = request.form.get('experience', '')
            if department:
                update_data['department'] = department
            if experience:
                update_data['experience'] = experience

        # Update password if provided
        new_password = request.form.get('password', '').strip()
        if new_password:
            if len(new_password) < 6:
                flash('Password must be at least 6 characters long!', 'error')
                return redirect(url_for('admin_users'))
            from werkzeug.security import generate_password_hash
            update_data['password'] = generate_password_hash(new_password)

        # Update user
        UserModel.update_user(user_id, update_data)
        flash(f'User "{name}" has been updated successfully!', 'success')

        # Log the action
        print(f"AUDIT: {current_admin['name']} updated user: {target_user['name']} ({target_user['email']})")

    except Exception as e:
        print(f"Error updating user: {e}")
        flash('An error occurred while updating the user. Please try again.', 'error')

    return redirect(url_for('admin_users'))


# Delete user
@app.route('/admin/user/<user_id>/delete', methods=['POST'])
@role_required(['admin'])
def admin_delete_user(user_id):
    current_admin = get_current_user()

    # Get the target user
    target_user = UserModel.find_user_by_id(user_id)
    if not target_user:
        flash('User not found!', 'error')
        return redirect(url_for('admin_users'))

    # Prevent admin from deleting themselves
    if str(target_user['_id']) == str(current_admin['_id']):
        flash('You cannot delete your own account!', 'error')
        return redirect(url_for('admin_users'))

    # Prevent deleting system admin
    if target_user.get('role') == 'system_admin':
        flash('System Administrator accounts cannot be deleted!', 'error')
        return redirect(url_for('admin_users'))

    try:
        user_name = target_user['name']
        user_email = target_user['email']

        # Delete related data first
        if target_user.get('role') == 'student':
            # Delete enrollments
            enrollments_collection.delete_many({'user_id': user_id})
            # Delete quiz results
            quiz_results_collection.delete_many({'user_id': user_id})
            # Delete leaderboard entries
            leaderboard_collection.delete_many({'user_id': user_id})
        elif target_user.get('role') == 'educator':
            # Check if educator has courses
            courses = CourseModel.get_courses_by_instructor(user_id)
            if courses:
                flash(
                    f'Cannot delete educator "{user_name}" - they have {len(courses)} course(s) assigned. Please reassign courses first.',
                    'error')
                return redirect(url_for('admin_users'))

        # Delete the user
        result = UserModel.delete_user(user_id)

        if result.deleted_count > 0:
            flash(f'User "{user_name}" has been deleted successfully!', 'success')
            # Log the action
            print(f"AUDIT: {current_admin['name']} deleted user: {user_name} ({user_email})")
        else:
            flash('Failed to delete user. Please try again.', 'error')

    except Exception as e:
        print(f"Error deleting user: {e}")
        flash('An error occurred while deleting the user. Please try again.', 'error')

    return redirect(url_for('admin_users'))


# Get user data for editing (AJAX endpoint)
@app.route('/admin/user/<user_id>/data')
@role_required(['admin'])
def admin_get_user_data(user_id):
    user = UserModel.find_user_by_id(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    user_data = convert_objectid_to_str(user.copy())
    # Remove sensitive data
    user_data.pop('password', None)

    return jsonify(user_data)


@app.route('/admin/courses')
@role_required(['admin'])
def admin_courses():
    user = get_current_user()

    # Get filter parameters
    search = request.args.get('search', '').strip()
    status_filter = request.args.get('status', '')
    category_filter = request.args.get('category', '')
    level_filter = request.args.get('level', '')
    instructor_filter = request.args.get('instructor', '')
    sort_by = request.args.get('sort', 'created_desc')

    # Get all courses
    all_courses = CourseModel.get_all_courses()

    # Apply filters
    filtered_courses = []
    for course in all_courses:
        # Search filter (title, description, instructor)
        if search:
            search_lower = search.lower()
            instructor_name = course.get('instructor', '').lower()
            if (search_lower not in course.get('title', '').lower() and
                    search_lower not in course.get('description', '').lower() and
                    search_lower not in instructor_name):
                continue

        # Status filter
        if status_filter and course.get('status') != status_filter:
            continue

        # Category filter
        if category_filter and course.get('category') != category_filter:
            continue

        # Level filter
        if level_filter and course.get('level') != level_filter:
            continue

        # Instructor filter
        if instructor_filter:
            instructor = UserModel.find_user_by_id(course.get('instructor_id', ''))
            if not instructor or instructor_filter not in instructor.get('name', '').lower():
                continue

        filtered_courses.append(course)

    # Sort courses
    if sort_by == 'created_desc':
        filtered_courses.sort(key=lambda x: x.get('created_at', datetime.min), reverse=True)
    elif sort_by == 'created_asc':
        filtered_courses.sort(key=lambda x: x.get('created_at', datetime.min))
    elif sort_by == 'students_desc':
        filtered_courses.sort(key=lambda x: x.get('students_enrolled', 0), reverse=True)
    elif sort_by == 'rating_desc':
        filtered_courses.sort(key=lambda x: x.get('rating', 0), reverse=True)
    elif sort_by == 'title_asc':
        filtered_courses.sort(key=lambda x: x.get('title', '').lower())

    # Convert to serializable format and add instructor names
    courses_data = []
    for course in filtered_courses:
        course_data = convert_objectid_to_str(course.copy())

        # Get instructor name
        instructor = UserModel.find_user_by_id(course.get('instructor_id', ''))
        course_data['instructor_name'] = instructor.get('name', 'Unknown') if instructor else 'Unknown'

        # Get enrollment count
        enrollments = EnrollmentModel.get_course_enrollments(str(course['_id']))
        course_data['students_enrolled'] = len(enrollments)

        # Get modules count
        modules = ModuleModel.get_modules_by_course(str(course['_id']))
        course_data['modules_count'] = len(modules)

        courses_data.append(course_data)

    # Calculate statistics
    total_courses = len(courses_data)
    published_courses = sum(1 for course in courses_data if course.get('status') == 'published')
    draft_courses = sum(1 for course in courses_data if course.get('status') == 'draft')
    archived_courses = sum(1 for course in courses_data if course.get('status') == 'archived')

    # Get unique instructors for filter dropdown
    all_instructors = UserModel.get_users_by_role('educator')
    instructor_options = [{'id': str(inst['_id']), 'name': inst['name']} for inst in all_instructors]

    return render_template('admin/courses.html',
                           user=convert_objectid_to_str(user),
                           courses=courses_data,
                           total_courses=total_courses,
                           published_courses=published_courses,
                           draft_courses=draft_courses,
                           archived_courses=archived_courses,
                           instructor_options=instructor_options,
                           # Filter values for form persistence
                           search=search,
                           status_filter=status_filter,
                           category_filter=category_filter,
                           level_filter=level_filter,
                           instructor_filter=instructor_filter,
                           sort_by=sort_by)


@app.route('/admin/courses/export')
@role_required(['admin'])
def admin_export_courses():
    """Export courses data as CSV"""
    user = get_current_user()

    # Get all courses with same filtering as main page
    search = request.args.get('search', '').strip()
    status_filter = request.args.get('status', '')
    category_filter = request.args.get('category', '')
    level_filter = request.args.get('level', '')
    instructor_filter = request.args.get('instructor', '')

    all_courses = CourseModel.get_all_courses()

    # Apply same filters as main page
    filtered_courses = []
    for course in all_courses:
        # Search filter
        if search:
            search_lower = search.lower()
            instructor_name = course.get('instructor', '').lower()
            if (search_lower not in course.get('title', '').lower() and
                    search_lower not in course.get('description', '').lower() and
                    search_lower not in instructor_name):
                continue

        # Status filter
        if status_filter and course.get('status') != status_filter:
            continue

        # Category filter
        if category_filter and course.get('category') != category_filter:
            continue

        # Level filter
        if level_filter and course.get('level') != level_filter:
            continue

        # Instructor filter
        if instructor_filter:
            instructor = UserModel.find_user_by_id(course.get('instructor_id', ''))
            if not instructor or instructor_filter not in instructor.get('name', '').lower():
                continue

        filtered_courses.append(course)

    # Create CSV content
    output = io.StringIO()
    writer = csv.writer(output)

    # Write headers
    writer.writerow([
        'Course ID', 'Title', 'Instructor', 'Status', 'Level', 'Category',
        'Students Enrolled', 'Modules', 'Rating', 'Created Date', 'Updated Date'
    ])

    # Write data
    for course in filtered_courses:
        instructor = UserModel.find_user_by_id(course.get('instructor_id', ''))
        instructor_name = instructor.get('name', 'Unknown') if instructor else 'Unknown'

        enrollments = EnrollmentModel.get_course_enrollments(str(course['_id']))
        modules = ModuleModel.get_modules_by_course(str(course['_id']))

        writer.writerow([
            str(course['_id']),
            course.get('title', ''),
            instructor_name,
            course.get('status', ''),
            course.get('level', ''),
            course.get('category', ''),
            len(enrollments),
            len(modules),
            course.get('rating', 0),
            course.get('created_at', '').strftime('%Y-%m-%d %H:%M:%S') if course.get('created_at') else '',
            course.get('updated_at', '').strftime('%Y-%m-%d %H:%M:%S') if course.get('updated_at') else ''
        ])

    # Create response
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers[
        'Content-Disposition'] = f'attachment; filename=courses_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'

    return response


@app.route('/admin/course/create')
@role_required(['admin'])
def admin_create_course():
    """Show create course form"""
    user = get_current_user()

    # Get all educators for instructor dropdown
    educators = UserModel.get_users_by_role('educator')

    return render_template('admin/create_course.html',
                           user=convert_objectid_to_str(user),
                           educators=[convert_objectid_to_str(edu) for edu in educators])


@app.route('/admin/course/create', methods=['POST'])
@role_required(['admin'])
def admin_create_course_submit():
    """Handle course creation"""
    user = get_current_user()

    try:
        # Get form data
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        instructor_id = request.form.get('instructor_id', '').strip()
        level = request.form.get('level', '')
        category = request.form.get('category', '').strip()
        duration = request.form.get('duration', '').strip()
        prerequisites = request.form.get('prerequisites', '').strip()
        objectives = request.form.get('objectives', '').strip()

        # Validation
        if not title or not description or not instructor_id:
            flash('Title, description, and instructor are required!', 'error')
            return redirect(url_for('admin_create_course'))

        # Verify instructor exists
        instructor = UserModel.find_user_by_id(instructor_id)
        if not instructor or instructor.get('role') != 'educator':
            flash('Invalid instructor selected!', 'error')
            return redirect(url_for('admin_create_course'))

        # Create course data
        course_data = {
            'title': title,
            'description': description,
            'instructor_id': instructor_id,
            'instructor': instructor.get('name'),
            'level': level,
            'category': category,
            'duration': duration,
            'prerequisites': prerequisites,
            'objectives': objectives,
            'status': 'draft',
            'rating': 0,
            'students_enrolled': 0,
            'created_by': str(user['_id']),
            'created_by_admin': True
        }

        # Create course
        course_id = CourseModel.create_course(course_data)

        flash(f'Course "{title}" created successfully!', 'success')
        return redirect(url_for('admin_courses'))

    except Exception as e:
        print(f"Error creating course: {e}")
        flash('An error occurred while creating the course. Please try again.', 'error')
        return redirect(url_for('admin_create_course'))


@app.route('/admin/course/<course_id>/view')
@role_required(['admin'])
def admin_view_course(course_id):
    """View course details"""
    user = get_current_user()

    course = CourseModel.find_course_by_id(course_id)
    if not course:
        return jsonify({'error': 'Course not found'}), 404

    # Get additional course data
    instructor = UserModel.find_user_by_id(course.get('instructor_id', ''))
    enrollments = EnrollmentModel.get_course_enrollments(course_id)
    modules = ModuleModel.get_modules_by_course(course_id)

    course_data = convert_objectid_to_str(course.copy())
    course_data['instructor_name'] = instructor.get('name', 'Unknown') if instructor else 'Unknown'
    course_data['instructor_email'] = instructor.get('email', '') if instructor else ''
    course_data['students_enrolled'] = len(enrollments)
    course_data['modules_count'] = len(modules)
    course_data['completion_rate'] = sum(e.get('progress', 0) for e in enrollments) / len(
        enrollments) if enrollments else 0

    return jsonify(course_data)


@app.route('/admin/course/<course_id>/edit')
@role_required(['admin'])
def admin_edit_course(course_id):
    """Show edit course form"""
    user = get_current_user()

    course = CourseModel.find_course_by_id(course_id)
    if not course:
        flash('Course not found!', 'error')
        return redirect(url_for('admin_courses'))

    # Get all educators for instructor dropdown
    educators = UserModel.get_users_by_role('educator')

    return render_template('admin/edit_course.html',
                           user=convert_objectid_to_str(user),
                           course=convert_objectid_to_str(course),
                           educators=[convert_objectid_to_str(edu) for edu in educators])


@app.route('/admin/course/<course_id>/edit', methods=['POST'])
@role_required(['admin'])
def admin_edit_course_submit(course_id):
    """Handle course editing"""
    user = get_current_user()

    course = CourseModel.find_course_by_id(course_id)
    if not course:
        flash('Course not found!', 'error')
        return redirect(url_for('admin_courses'))

    try:
        # Get form data
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        instructor_id = request.form.get('instructor_id', '').strip()
        level = request.form.get('level', '')
        category = request.form.get('category', '').strip()
        duration = request.form.get('duration', '').strip()
        prerequisites = request.form.get('prerequisites', '').strip()
        objectives = request.form.get('objectives', '').strip()
        status = request.form.get('status', course.get('status', 'draft'))

        # Validation
        if not title or not description or not instructor_id:
            flash('Title, description, and instructor are required!', 'error')
            return redirect(url_for('admin_edit_course', course_id=course_id))

        # Verify instructor exists
        instructor = UserModel.find_user_by_id(instructor_id)
        if not instructor or instructor.get('role') != 'educator':
            flash('Invalid instructor selected!', 'error')
            return redirect(url_for('admin_edit_course', course_id=course_id))

        # Update course data
        update_data = {
            'title': title,
            'description': description,
            'instructor_id': instructor_id,
            'instructor': instructor.get('name'),
            'level': level,
            'category': category,
            'duration': duration,
            'prerequisites': prerequisites,
            'objectives': objectives,
            'status': status,
            'updated_by': str(user['_id']),
            'updated_at': datetime.now()
        }

        # Update course
        CourseModel.update_course(course_id, update_data)

        flash(f'Course "{title}" updated successfully!', 'success')
        return redirect(url_for('admin_courses'))

    except Exception as e:
        print(f"Error updating course: {e}")
        flash('An error occurred while updating the course. Please try again.', 'error')
        return redirect(url_for('admin_edit_course', course_id=course_id))


@app.route('/admin/course/<course_id>/delete', methods=['POST'])
@role_required(['admin'])
def admin_delete_course(course_id):
    """Delete a course"""
    user = get_current_user()

    course = CourseModel.find_course_by_id(course_id)
    if not course:
        return jsonify({'success': False, 'message': 'Course not found'}), 404

    try:
        # Check if course has enrollments
        enrollments = EnrollmentModel.get_course_enrollments(course_id)
        if enrollments:
            return jsonify({
                'success': False,
                'message': f'Cannot delete course with {len(enrollments)} active enrollments. Please remove all enrollments first.'
            }), 400

        # Delete related data first
        modules = ModuleModel.get_modules_by_course(course_id)
        for module in modules:
            # Delete quizzes for each module
            quizzes = QuizModel.get_quizzes_by_module(str(module['_id']))
            for quiz in quizzes:
                QuizModel.delete_quiz(str(quiz['_id']))

            # Delete module
            ModuleModel.delete_module(str(module['_id']))

        # Delete course
        CourseModel.delete_course(course_id)

        return jsonify({
            'success': True,
            'message': f'Course "{course.get("title", "")}" deleted successfully'
        })

    except Exception as e:
        print(f"Error deleting course: {e}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while deleting the course'
        }), 500


@app.route('/admin/course/<course_id>/toggle-status', methods=['POST'])
@role_required(['admin'])
def admin_toggle_course_status(course_id):
    """Toggle course status (publish/unpublish/archive)"""
    user = get_current_user()

    course = CourseModel.find_course_by_id(course_id)
    if not course:
        return jsonify({'success': False, 'message': 'Course not found'}), 404

    try:
        current_status = course.get('status', 'draft')

        # Determine new status
        if current_status == 'draft':
            new_status = 'published'
        elif current_status == 'published':
            new_status = 'archived'
        else:  # archived
            new_status = 'draft'

        # Update status
        CourseModel.update_course(course_id, {
            'status': new_status,
            'updated_by': str(user['_id']),
            'updated_at': datetime.now()
        })

        return jsonify({
            'success': True,
            'message': f'Course status changed to {new_status}',
            'new_status': new_status
        })

    except Exception as e:
        print(f"Error toggling course status: {e}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while updating course status'
        }), 500


@app.route('/admin/courses/bulk-action', methods=['POST'])
@role_required(['admin'])
def admin_bulk_course_action():
    """Handle bulk actions on courses"""
    user = get_current_user()

    action = request.form.get('action')
    course_ids = request.form.getlist('course_ids')

    if not action or not course_ids:
        return jsonify({'success': False, 'message': 'Invalid request'}), 400

    try:
        success_count = 0
        error_count = 0

        for course_id in course_ids:
            try:
                course = CourseModel.find_course_by_id(course_id)
                if not course:
                    error_count += 1
                    continue

                if action == 'publish':
                    CourseModel.update_course(course_id, {
                        'status': 'published',
                        'updated_by': str(user['_id']),
                        'updated_at': datetime.now()
                    })
                elif action == 'unpublish':
                    CourseModel.update_course(course_id, {
                        'status': 'draft',
                        'updated_by': str(user['_id']),
                        'updated_at': datetime.now()
                    })
                elif action == 'archive':
                    CourseModel.update_course(course_id, {
                        'status': 'archived',
                        'updated_by': str(user['_id']),
                        'updated_at': datetime.now()
                    })
                elif action == 'delete':
                    # Check for enrollments
                    enrollments = EnrollmentModel.get_course_enrollments(course_id)
                    if enrollments:
                        error_count += 1
                        continue

                    # Delete course and related data
                    modules = ModuleModel.get_modules_by_course(course_id)
                    for module in modules:
                        quizzes = QuizModel.get_quizzes_by_module(str(module['_id']))
                        for quiz in quizzes:
                            QuizModel.delete_quiz(str(quiz['_id']))
                        ModuleModel.delete_module(str(module['_id']))

                    CourseModel.delete_course(course_id)

                success_count += 1

            except Exception as e:
                print(f"Error processing course {course_id}: {e}")
                error_count += 1

        message = f'Bulk action completed: {success_count} successful'
        if error_count > 0:
            message += f', {error_count} failed'

        return jsonify({
            'success': True,
            'message': message,
            'success_count': success_count,
            'error_count': error_count
        })

    except Exception as e:
        print(f"Error in bulk action: {e}")
        return jsonify({
            'success': False,
            'message': 'An error occurred during bulk operation'
        }), 500


@app.route('/admin/analytics')
@role_required(['admin'])
def admin_analytics():
    user = get_current_user()

    # Get system stats
    stats = AnalyticsModel.get_system_analytics()
    if not stats:
        stats = AnalyticsModel.update_system_stats()

    # Get all courses for performance data
    all_courses = CourseModel.get_all_courses()
    course_performance = {}
    courses_dict = {}

    for course in all_courses:
        course_id = str(course['_id'])
        courses_dict[course_id] = course

        analytics = AnalyticsModel.get_course_analytics(course_id)
        if analytics:
            course_performance[course_id] = analytics

    return render_template('admin/analytics.html',
                           user=convert_objectid_to_str(user),
                           stats=stats,
                           course_performance=course_performance,
                           courses=courses_dict)



"""Modification: User Change Role by Admin"""

@app.route('/admin/user/<user_id>/change-role', methods=['POST'])
@role_required(['admin'])
def admin_change_user_role(user_id):
    """Change user role (between educator, admin, and content_manager)"""
    current_admin = get_current_user()

    # Get the target user
    target_user = UserModel.find_user_by_id(user_id)
    if not target_user:
        flash('User not found!', 'error')
        return redirect(url_for('admin_users'))

    # Debug: Print initial state
    print(f"DEBUG: Target user before change: {target_user['name']}, Role: {target_user.get('role')}")

    # Prevent admin from changing their own role
    if str(target_user['_id']) == str(current_admin['_id']):
        flash('You cannot change your own role!', 'error')
        return redirect(url_for('admin_users'))

    current_role = target_user.get('role')
    new_role = request.form.get('new_role')

    # Debug: Print role change attempt
    print(f"DEBUG: Attempting to change {target_user['name']} from {current_role} to {new_role}")

    # Validate role change - now allow educator, admin, and content_manager
    allowed_roles = ['educator', 'admin', 'content_manager']
    if current_role not in allowed_roles or new_role not in allowed_roles:
        flash('Role changes are only allowed between Educator, Admin, and Content Manager roles!', 'error')
        return redirect(url_for('admin_users'))

    if current_role == new_role:
        flash(f'User is already a {new_role.replace("_", " ").title()}!', 'warning')
        return redirect(url_for('admin_users'))

    try:
        # Base update data
        update_data = {
            'role': new_role,
            'role_changed_by': str(current_admin['_id']),
            'role_changed_at': datetime.now()
        }

        # Handle role-specific fields based on the new role
        if new_role == 'admin':
            # Upgrading to admin (from educator or content_manager)
            update_data.update({
                'admin_permissions': ['user_management', 'course_management', 'analytics'],
                'upgraded_to_admin_at': datetime.now()
            })
            print(f"DEBUG: Upgrading {target_user['name']} to admin with data: {update_data}")
            result = UserModel.update_user(user_id, update_data)
            print(f"DEBUG: Update result: {result.modified_count} documents modified")

            # Remove content_manager specific fields if upgrading from content_manager
            if current_role == 'content_manager':
                users_collection.update_one(
                    {'_id': ObjectId(user_id)},
                    {'$unset': {
                        'content_manager_permissions': '',
                        'assigned_to_content_manager_at': ''
                    }}
                )
                print(f"DEBUG: Removed content_manager fields")

        elif new_role == 'content_manager':
            # Assigning to content_manager (from educator or downgrading from admin)
            update_data.update({
                'content_manager_permissions': ['course_creation', 'content_management', 'module_management'],
                'assigned_to_content_manager_at': datetime.now()
            })
            print(f"DEBUG: Assigning {target_user['name']} to content_manager with data: {update_data}")
            result = UserModel.update_user(user_id, update_data)
            print(f"DEBUG: Update result: {result.modified_count} documents modified")

            # Remove admin specific fields if downgrading from admin
            if current_role == 'admin':
                users_collection.update_one(
                    {'_id': ObjectId(user_id)},
                    {'$unset': {
                        'admin_permissions': '',
                        'upgraded_to_admin_at': ''
                    }}
                )
                print(f"DEBUG: Removed admin fields")

        elif new_role == 'educator':
            # Downgrading to educator (from admin or content_manager)
            print(f"DEBUG: Downgrading {target_user['name']} to educator")
            result = UserModel.update_user(user_id, update_data)
            print(f"DEBUG: Role update result: {result.modified_count} documents modified")

            # Remove role-specific fields based on current role
            fields_to_unset = {}
            if current_role == 'admin':
                fields_to_unset.update({
                    'admin_permissions': '',
                    'upgraded_to_admin_at': ''
                })
            elif current_role == 'content_manager':
                fields_to_unset.update({
                    'content_manager_permissions': '',
                    'assigned_to_content_manager_at': ''
                })

            if fields_to_unset:
                unset_result = users_collection.update_one(
                    {'_id': ObjectId(user_id)},
                    {'$unset': fields_to_unset}
                )
                print(f"DEBUG: Unset result: {unset_result.modified_count} documents modified")

        # Verify the change was applied
        updated_user = UserModel.find_user_by_id(user_id)
        if updated_user:
            print(f"DEBUG: User after update: {updated_user['name']}, Role: {updated_user.get('role')}")
            if updated_user.get('role') == new_role:
                # Determine action type
                action_map = {
                    ('educator', 'admin'): 'upgraded',
                    ('content_manager', 'admin'): 'upgraded',
                    ('admin', 'educator'): 'downgraded',
                    ('content_manager', 'educator'): 'downgraded',
                    ('educator', 'content_manager'): 'assigned as',
                    ('admin', 'content_manager'): 'reassigned as'
                }

                action_key = (current_role, new_role)
                action = action_map.get(action_key, 'changed to')

                role_display = new_role.replace('_', ' ').title()
                flash(f'Successfully {action} {target_user["name"]} {role_display}!', 'success')
                print(f"SUCCESS: Role change completed for {target_user['name']}")
            else:
                flash('Role change may not have been applied correctly. Please check and try again.', 'warning')
                print(f"WARNING: Role change verification failed")
        else:
            flash('Could not verify role change. Please check the user.', 'warning')

        # Log the action for audit trail
        print(f"AUDIT: {current_admin['name']} changed {target_user['name']} from {current_role} to {new_role}")

    except Exception as e:
        print(f"ERROR: Exception during role change: {str(e)}")
        import traceback
        traceback.print_exc()
        flash('An error occurred while changing the user role. Please try again.', 'error')

    return redirect(url_for('admin_users'))


# =====================================================
# CONTENT MANAGER ROUTES
# =====================================================

@app.route('/content-manager/dashboard')
@role_required(['content_manager'])
def content_manager_dashboard():
    user = get_current_user()

    # Get content statistics
    all_courses = CourseModel.get_all_courses()
    total_courses = len(all_courses)
    published_courses = sum(1 for course in all_courses if course.get('status') == 'published')

    # Get total modules across all courses
    total_modules = 0
    for course in all_courses:
        course_modules = ModuleModel.get_modules_by_course(str(course['_id']))
        total_modules += len(course_modules)

    recent_activity = [
        {'action': 'Module created', 'details': 'Advanced Writing Skills', 'time': '1 hour ago'},
        {'action': 'Course updated', 'details': 'IELTS Preparation', 'time': '4 hours ago'},
        {'action': 'Content reviewed', 'details': 'Grammar Fundamentals', 'time': '1 day ago'}
    ]

    return render_template('content_manager/dashboard.html',
                           user=convert_objectid_to_str(user),
                           total_courses=total_courses,
                           total_modules=total_modules,
                           published_courses=published_courses,
                           recent_activity=recent_activity)


@app.route('/admin/user/<user_id>/toggle-status', methods=['POST'])
@role_required(['admin'])
def admin_toggle_user_status(user_id):
    """Toggle user status between active and inactive"""
    current_admin = get_current_user()

    # Get the target user
    target_user = UserModel.find_user_by_id(user_id)
    if not target_user:
        return jsonify({'success': False, 'message': 'User not found!'}), 404

    # Prevent admin from deactivating themselves
    if str(target_user['_id']) == str(current_admin['_id']):
        return jsonify({'success': False, 'message': 'You cannot deactivate your own account!'}), 400

    # Prevent deactivating system admin
    if target_user.get('role') == 'system_admin':
        return jsonify({'success': False, 'message': 'System Administrator accounts cannot be deactivated!'}), 400

    try:
        # Get current status (default to 'active' if not set)
        current_status = target_user.get('status', 'active')
        new_status = 'inactive' if current_status == 'active' else 'active'

        # Update user status
        update_data = {
            'status': new_status,
            'status_changed_by': str(current_admin['_id']),
            'status_changed_at': datetime.now()
        }

        # Add status change reason
        if new_status == 'inactive':
            update_data['deactivated_at'] = datetime.now()
            update_data['deactivated_by'] = str(current_admin['_id'])
        else:
            update_data['reactivated_at'] = datetime.now()
            update_data['reactivated_by'] = str(current_admin['_id'])
            # Remove deactivation fields when reactivating
            users_collection.update_one(
                {'_id': ObjectId(user_id)},
                {'$unset': {
                    'deactivated_at': '',
                    'deactivated_by': ''
                }}
            )

        result = UserModel.update_user(user_id, update_data)

        if result.modified_count > 0:
            action = 'deactivated' if new_status == 'inactive' else 'reactivated'
            message = f'User "{target_user["name"]}" has been {action} successfully!'

            # Log the action
            print(f"AUDIT: {current_admin['name']} {action} user: {target_user['name']} ({target_user['email']})")

            return jsonify({
                'success': True,
                'message': message,
                'new_status': new_status,
                'user_name': target_user['name']
            })
        else:
            return jsonify({'success': False, 'message': 'Failed to update user status!'}), 500

    except Exception as e:
        print(f"Error toggling user status: {e}")
        return jsonify({'success': False, 'message': 'An error occurred while updating user status.'}), 500


@app.route('/content-manager/create-course', methods=['GET', 'POST'])
@role_required(['content_manager'])
def create_course():
    user = get_current_user()

    if request.method == 'POST':
        # Get all educators for instructor assignment
        educators = UserModel.get_all_users()
        default_educator = next((u for u in educators if u.get('role') == 'educator'), None)

        course_data = {
            'title': request.form['title'],
            'description': request.form['description'],
            'instructor': request.form['instructor'],
            'instructor_id': default_educator['_id'] if default_educator else None,
            'level': request.form['level'],
            'duration': request.form['duration'],
            'image': '/static/images/default-course.jpg',
            'status': 'draft'
        }

        course_id = CourseModel.create_course(course_data)
        flash('Course created successfully!', 'success')
        return redirect(url_for('content_manager_courses'))

    return render_template('content_manager/create_course.html',
                           user=convert_objectid_to_str(user))

@app.route('/content-manager/course/create')
@role_required(['content_manager'])
def content_manager_create_course():
    """Content manager create course page"""
    user = get_current_user()
    return render_template('content_manager/create_course.html',
                           user=convert_objectid_to_str(user))


@app.route('/content-manager/course/create', methods=['POST'])
@role_required(['content_manager'])
def content_manager_create_course_post():
    """Handle course creation by content manager"""
    user = get_current_user()

    try:
        # Get form data
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        level = request.form.get('level', 'Beginner')
        duration = request.form.get('duration', '').strip()
        category = request.form.get('category', 'General')
        instructor = request.form.get('instructor', '').strip()

        # Validation
        if not title or not description:
            flash('Title and description are required!', 'error')
            return redirect(url_for('content_manager_create_course'))

        if not instructor:
            flash('Instructor selection is required!', 'error')
            return redirect(url_for('content_manager_create_course'))

        # Find instructor by name (you might want to improve this)
        instructor_user = UserModel.find_user_by_email(instructor)
        if not instructor_user:
            # Try to find by name
            all_educators = [u for u in UserModel.get_all_users() if u.get('role') == 'educator']
            instructor_user = next((u for u in all_educators if u['name'] == instructor), None)

        if not instructor_user:
            flash('Selected instructor not found!', 'error')
            return redirect(url_for('content_manager_create_course'))

        # Create course data
        course_data = {
            'title': title,
            'description': description,
            'level': level,
            'duration': duration,
            'category': category,
            'instructor': instructor_user['name'],
            'instructor_id': str(instructor_user['_id']),
            'status': 'draft',
            'students_enrolled': 0,
            'rating': 0.0,
            'image': request.form.get('image', ''),
            'created_by': str(user['_id']),  # Track who created it
            'created_by_role': 'content_manager'
        }

        # Create course
        course_id = CourseModel.create_course(course_data)

        flash(f'Course "{title}" created successfully and assigned to {instructor_user["name"]}!', 'success')
        return redirect(url_for('content_manager_courses'))

    except Exception as e:
        print(f"Error creating course: {e}")
        flash('An error occurred while creating the course. Please try again.', 'error')
        return redirect(url_for('content_manager_create_course'))


@app.route('/content-manager/course/<course_id>')
@role_required(['content_manager'])
def content_manager_course_detail(course_id):
    """Content manager course detail page"""
    user = get_current_user()

    # Get course
    course = CourseModel.find_course_by_id(course_id)
    if not course:
        flash('Course not found!', 'error')
        return redirect(url_for('content_manager_courses'))

    # Get course modules
    modules = ModuleModel.get_modules_by_course(course_id)
    course_modules = [convert_objectid_to_str(module) for module in modules]

    # Get enrolled students
    enrollments = EnrollmentModel.get_course_enrollments(course_id)
    enrolled_students = []

    for enrollment in enrollments:
        student = UserModel.find_user_by_id(enrollment['user_id'])
        if student:
            student_data = convert_objectid_to_str(student.copy())
            student_data.update({
                'progress': enrollment.get('progress', 0),
                'grade': enrollment.get('grade'),
                'enrolled_date': enrollment.get('enrolled_date')
            })
            enrolled_students.append(student_data)

    return render_template('content_manager/course_detail.html',
                           user=convert_objectid_to_str(user),
                           course=convert_objectid_to_str(course),
                           modules=course_modules,
                           students=enrolled_students)


@app.route('/content-manager/course/<course_id>/edit')
@role_required(['content_manager'])
def content_manager_edit_course(course_id):
    """Content manager edit course page"""
    user = get_current_user()

    # Get course
    course = CourseModel.find_course_by_id(course_id)
    if not course:
        flash('Course not found!', 'error')
        return redirect(url_for('content_manager_courses'))

    # Get all educators for instructor assignment
    all_users = UserModel.get_all_users()
    educators = [convert_objectid_to_str(u) for u in all_users if u.get('role') == 'educator']

    return render_template('content_manager/edit_course.html',
                           user=convert_objectid_to_str(user),
                           course=convert_objectid_to_str(course),
                           educators=educators)


@app.route('/content-manager/course/<course_id>/edit', methods=['POST'])
@role_required(['content_manager'])
def content_manager_edit_course_post(course_id):
    """Handle course editing by content manager"""
    user = get_current_user()

    # Get course
    course = CourseModel.find_course_by_id(course_id)
    if not course:
        flash('Course not found!', 'error')
        return redirect(url_for('content_manager_courses'))

    try:
        # Get form data
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        level = request.form.get('level', 'Beginner')
        duration = request.form.get('duration', '').strip()
        category = request.form.get('category', 'General')
        instructor = request.form.get('instructor', '').strip()
        status = request.form.get('status', course.get('status', 'draft'))

        # Validation
        if not title or not description:
            flash('Title and description are required!', 'error')
            return redirect(url_for('content_manager_edit_course', course_id=course_id))

        # Update course data
        update_data = {
            'title': title,
            'description': description,
            'level': level,
            'duration': duration,
            'category': category,
            'status': status,
            'image': request.form.get('image', course.get('image', ''))
        }

        # Update instructor if changed
        if instructor and instructor != course.get('instructor'):
            instructor_user = UserModel.find_user_by_email(instructor)
            if not instructor_user:
                # Try to find by name
                all_educators = [u for u in UserModel.get_all_users() if u.get('role') == 'educator']
                instructor_user = next((u for u in all_educators if u['name'] == instructor), None)

            if instructor_user:
                update_data['instructor'] = instructor_user['name']
                update_data['instructor_id'] = str(instructor_user['_id'])

        # Update course
        CourseModel.update_course(course_id, update_data)

        flash(f'Course "{title}" updated successfully!', 'success')
        return redirect(url_for('content_manager_course_detail', course_id=course_id))

    except Exception as e:
        print(f"Error updating course: {e}")
        flash('An error occurred while updating the course. Please try again.', 'error')
        return redirect(url_for('content_manager_edit_course', course_id=course_id))


@app.route('/content-manager/course/<course_id>/publish', methods=['POST'])
@role_required(['content_manager'])
def content_manager_publish_course(course_id):
    """Publish/unpublish a course"""
    user = get_current_user()

    # Get course
    course = CourseModel.find_course_by_id(course_id)
    if not course:
        return jsonify({'success': False, 'message': 'Course not found'}), 404

    try:
        current_status = course.get('status', 'draft')
        new_status = 'published' if current_status != 'published' else 'draft'

        # Update course status
        CourseModel.update_course(course_id, {'status': new_status})

        action = 'published' if new_status == 'published' else 'unpublished'
        return jsonify({'success': True, 'message': f'Course {action} successfully', 'new_status': new_status})

    except Exception as e:
        print(f"Error updating course status: {e}")
        return jsonify({'success': False, 'message': 'An error occurred while updating the course status'}), 500


@app.route('/content-manager/course/<course_id>/delete', methods=['DELETE'])
@role_required(['content_manager'])
def content_manager_delete_course(course_id):
    """Delete a course"""
    user = get_current_user()

    # Get course
    course = CourseModel.find_course_by_id(course_id)
    if not course:
        return jsonify({'success': False, 'message': 'Course not found'}), 404

    try:
        # Check if course has enrolled students
        enrollments = EnrollmentModel.get_course_enrollments(course_id)
        if enrollments:
            return jsonify({'success': False, 'message': 'Cannot delete course with enrolled students'}), 400

        # Delete related modules first
        modules = ModuleModel.get_modules_by_course(course_id)
        for module in modules:
            # Delete related quizzes
            quizzes = QuizModel.get_quizzes_by_module(str(module['_id']))
            for quiz in quizzes:
                QuizModel.delete_quiz(str(quiz['_id']))

            # Delete module
            ModuleModel.delete_module(str(module['_id']))

        # Delete course
        CourseModel.delete_course(course_id)

        return jsonify({'success': True, 'message': 'Course deleted successfully'})

    except Exception as e:
        print(f"Error deleting course: {e}")
        return jsonify({'success': False, 'message': 'An error occurred while deleting the course'}), 500


@app.route('/content-manager/analytics')
@role_required(['content_manager'])
def content_manager_analytics():
    """Content manager analytics page"""
    user = get_current_user()

    # Get content statistics
    all_courses = CourseModel.get_all_courses()
    total_courses = len(all_courses)
    published_courses = sum(1 for course in all_courses if course.get('status') == 'published')
    draft_courses = sum(1 for course in all_courses if course.get('status') == 'draft')

    # Get total modules and enrollments
    total_modules = 0
    total_enrollments = 0

    for course in all_courses:
        course_modules = ModuleModel.get_modules_by_course(str(course['_id']))
        total_modules += len(course_modules)

        course_enrollments = EnrollmentModel.get_course_enrollments(str(course['_id']))
        total_enrollments += len(course_enrollments)

    analytics_data = {
        'total_courses': total_courses,
        'published_courses': published_courses,
        'draft_courses': draft_courses,
        'total_modules': total_modules,
        'total_enrollments': total_enrollments,
        'avg_enrollment_per_course': total_enrollments / total_courses if total_courses > 0 else 0
    }

    return render_template('content_manager/analytics.html',
                           user=convert_objectid_to_str(user),
                           analytics=analytics_data,
                           courses=all_courses)


@app.route('/content-manager/courses')
@role_required(['content_manager'])
def content_manager_courses():
    """Enhanced content manager courses page with filtering"""
    user = get_current_user()

    # Get filter parameters
    search = request.args.get('search', '').strip()
    status_filter = request.args.get('status', '')
    category_filter = request.args.get('category', '')
    level_filter = request.args.get('level', '')
    instructor_filter = request.args.get('instructor', '')

    # Get all courses for content management
    all_courses = CourseModel.get_all_courses()

    # Apply filters
    filtered_courses = []
    for course in all_courses:
        # Search filter (title, description, instructor)
        if search:
            search_lower = search.lower()
            if (search_lower not in course.get('title', '').lower() and
                    search_lower not in course.get('description', '').lower() and
                    search_lower not in course.get('instructor', '').lower()):
                continue

        # Status filter
        if status_filter and course.get('status') != status_filter:
            continue

        # Category filter
        if category_filter and course.get('category') != category_filter:
            continue

        # Level filter
        if level_filter and course.get('level') != level_filter:
            continue

        # Instructor filter
        if instructor_filter and course.get('instructor') != instructor_filter:
            continue

        filtered_courses.append(course)

    # Convert to serializable format
    courses_data = [convert_objectid_to_str(course) for course in filtered_courses]

    # Calculate statistics
    total_courses = len(courses_data)
    published_courses = sum(1 for course in courses_data if course.get('status') == 'published')
    draft_courses = sum(1 for course in courses_data if course.get('status') == 'draft')

    return render_template('content_manager/courses.html',
                           user=convert_objectid_to_str(user),
                           courses=courses_data,
                           total_courses=total_courses,
                           published_courses=published_courses,
                           draft_courses=draft_courses)


@app.route('/content-manager/course/<course_id>/duplicate', methods=['POST'])
@role_required(['content_manager'])
def content_manager_duplicate_course(course_id):
    """Duplicate a course"""
    user = get_current_user()

    # Get course
    course = CourseModel.find_course_by_id(course_id)
    if not course:
        return jsonify({'success': False, 'message': 'Course not found'}), 404

    try:
        # Create duplicate course data
        duplicate_data = course.copy()
        duplicate_data.pop('_id', None)  # Remove original ID
        duplicate_data['title'] = f"{course['title']} (Copy)"
        duplicate_data['status'] = 'draft'
        duplicate_data['students_enrolled'] = 0
        duplicate_data['rating'] = 0.0
        duplicate_data['created_at'] = datetime.now()
        duplicate_data['updated_at'] = datetime.now()
        duplicate_data['created_by'] = str(user['_id'])
        duplicate_data['created_by_role'] = 'content_manager'

        # Create duplicate course
        new_course_id = CourseModel.create_course(duplicate_data)

        # Duplicate modules
        original_modules = ModuleModel.get_modules_by_course(course_id)
        for module in original_modules:
            module_data = module.copy()
            module_data.pop('_id', None)  # Remove original ID
            module_data['course_id'] = new_course_id
            module_data['completed_by'] = []
            ModuleModel.create_module(module_data)

        return jsonify({'success': True, 'message': 'Course duplicated successfully'})

    except Exception as e:
        print(f"Error duplicating course: {e}")
        return jsonify({'success': False, 'message': 'An error occurred while duplicating the course'}), 500


@app.route('/content-manager/course/<course_id>/export')
@role_required(['content_manager'])
def content_manager_export_course(course_id):
    """Export individual course data"""
    user = get_current_user()

    # Get course
    course = CourseModel.find_course_by_id(course_id)
    if not course:
        flash('Course not found!', 'error')
        return redirect(url_for('content_manager_courses'))

    try:
        # Get course modules
        modules = ModuleModel.get_modules_by_course(course_id)

        # Get enrolled students
        enrollments = EnrollmentModel.get_course_enrollments(course_id)

        # Create CSV data
        csv_data = []
        csv_data.append(['Course Information'])
        csv_data.append(['Title', course['title']])
        csv_data.append(['Instructor', course['instructor']])
        csv_data.append(['Level', course['level']])
        csv_data.append(['Status', course['status']])
        csv_data.append(['Students Enrolled', len(enrollments)])
        csv_data.append(['Modules', len(modules)])
        csv_data.append([''])  # Empty row

        csv_data.append(['Modules'])
        csv_data.append(['Order', 'Title', 'Type', 'Duration'])
        for module in modules:
            csv_data.append([
                module.get('order', 0),
                module.get('title', ''),
                module.get('type', ''),
                module.get('duration', '')
            ])

        csv_data.append([''])  # Empty row
        csv_data.append(['Enrolled Students'])
        csv_data.append(['Student Name', 'Email', 'Progress', 'Grade', 'Enrolled Date'])

        for enrollment in enrollments:
            student = UserModel.find_user_by_id(enrollment['user_id'])
            if student:
                csv_data.append([
                    student['name'],
                    student['email'],
                    f"{enrollment.get('progress', 0)}%",
                    enrollment.get('grade', 'N/A'),
                    enrollment.get('enrolled_date', 'Unknown')
                ])

        # Create CSV response
        import io
        import csv
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerows(csv_data)

        # Create response
        from flask import Response
        response = Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename={course["title"]}_export.csv'}
        )

        return response

    except Exception as e:
        print(f"Error exporting course: {e}")
        flash('An error occurred while exporting the course.', 'error')
        return redirect(url_for('content_manager_courses'))


@app.route('/content-manager/bulk-approve', methods=['POST'])
@role_required(['content_manager'])
def content_manager_bulk_approve():
    """Bulk approve courses under review"""
    user = get_current_user()

    try:
        # Get all courses under review
        all_courses = CourseModel.get_all_courses()
        review_courses = [course for course in all_courses if course.get('status') == 'review']

        count = 0
        for course in review_courses:
            CourseModel.update_course(str(course['_id']), {'status': 'published'})
            count += 1

        return jsonify({'success': True, 'message': f'{count} courses approved successfully', 'count': count})

    except Exception as e:
        print(f"Error in bulk approval: {e}")
        return jsonify({'success': False, 'message': 'An error occurred during bulk approval'}), 500


@app.route('/content-manager/bulk-publish', methods=['POST'])
@role_required(['content_manager'])
def content_manager_bulk_publish():
    """Bulk publish approved draft courses"""
    user = get_current_user()

    try:
        # Get all draft courses that are ready for publishing
        all_courses = CourseModel.get_all_courses()
        draft_courses = [course for course in all_courses if course.get('status') == 'draft']

        count = 0
        for course in draft_courses:
            # Check if course has modules (basic publishing requirement)
            modules = ModuleModel.get_modules_by_course(str(course['_id']))
            if modules:  # Only publish if it has content
                CourseModel.update_course(str(course['_id']), {'status': 'published'})
                count += 1

        return jsonify({'success': True, 'message': f'{count} courses published successfully', 'count': count})

    except Exception as e:
        print(f"Error in bulk publishing: {e}")
        return jsonify({'success': False, 'message': 'An error occurred during bulk publishing'}), 500


@app.route('/content-manager/export-all-courses')
@role_required(['content_manager'])
def content_manager_export_all_courses():
    """Export all courses data"""
    user = get_current_user()

    try:
        # Get all courses
        all_courses = CourseModel.get_all_courses()

        # Create comprehensive CSV data
        csv_data = []
        csv_data.append(
            ['Course ID', 'Title', 'Instructor', 'Level', 'Category', 'Status', 'Students Enrolled', 'Rating',
             'Modules Count', 'Created Date'])

        for course in all_courses:
            modules = ModuleModel.get_modules_by_course(str(course['_id']))
            enrollments = EnrollmentModel.get_course_enrollments(str(course['_id']))

            csv_data.append([
                str(course['_id']),
                course.get('title', ''),
                course.get('instructor', ''),
                course.get('level', ''),
                course.get('category', ''),
                course.get('status', ''),
                len(enrollments),
                course.get('rating', 0),
                len(modules),
                course.get('created_at', '').strftime('%Y-%m-%d') if course.get('created_at') else 'Unknown'
            ])

        # Create CSV response
        import io
        import csv
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerows(csv_data)

        # Create response
        from flask import Response
        response = Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=all_courses_export.csv'}
        )

        return response

    except Exception as e:
        print(f"Error exporting all courses: {e}")
        flash('An error occurred while exporting courses.', 'error')
        return redirect(url_for('content_manager_courses'))


@app.route('/content-manager/course/<course_id>/publish', methods=['POST'])
@role_required(['content_manager'])
def content_manager_update_course_status(course_id):
    """Update course status (enhanced version)"""
    user = get_current_user()

    # Get course
    course = CourseModel.find_course_by_id(course_id)
    if not course:
        return jsonify({'success': False, 'message': 'Course not found'}), 404

    try:
        # Get the new status from request
        data = request.get_json()
        new_status = data.get('status') if data else request.form.get('status')

        if not new_status:
            # Toggle logic (original functionality)
            current_status = course.get('status', 'draft')
            new_status = 'published' if current_status != 'published' else 'draft'

        # Validate status transition
        valid_statuses = ['draft', 'review', 'published', 'archived']
        if new_status not in valid_statuses:
            return jsonify({'success': False, 'message': 'Invalid status'}), 400

        # Update course status
        CourseModel.update_course(course_id, {'status': new_status})

        action = f'Status changed to {new_status}'
        return jsonify({'success': True, 'message': f'Course {action} successfully', 'new_status': new_status})

    except Exception as e:
        print(f"Error updating course status: {e}")
        return jsonify({'success': False, 'message': 'An error occurred while updating the course status'}), 500

@app.route('/content-manager/module/<module_id>/edit', methods=['GET'])
@role_required(['content_manager'])
def content_manager_edit_module(module_id):
    """Display module edit form (Content Manager)"""
    user = get_current_user()

    # Get module
    module = ModuleModel.find_module_by_id(module_id)
    if not module:
        flash('Module not found!', 'error')
        return redirect(url_for('content_manager_courses'))

    # Get course
    course = CourseModel.find_course_by_id(module['course_id'])
    if not course:
        flash('Course not found!', 'error')
        return redirect(url_for('content_manager_courses'))

    return render_template('content_manager/edit_module.html',
                           user=convert_objectid_to_str(user),
                           course=convert_objectid_to_str(course),
                           module=convert_objectid_to_str(module))


@app.route('/content-manager/module/<module_id>/edit', methods=['POST'])
@role_required(['content_manager'])
def content_manager_edit_module_post(module_id):
    """Handle module editing (Content Manager)"""
    user = get_current_user()

    # Get module
    module = ModuleModel.find_module_by_id(module_id)
    if not module:
        return jsonify({'success': False, 'message': 'Module not found'}), 404

    # Get course
    course = CourseModel.find_course_by_id(module['course_id'])
    if not course:
        return jsonify({'success': False, 'message': 'Course not found'}), 404

    try:
        # Get form data
        data = request.get_json() if request.is_json else request.form

        title = data.get('title', '').strip()
        if not title:
            if request.is_json:
                return jsonify({'success': False, 'message': 'Module title is required'}), 400
            else:
                flash('Module title is required!', 'error')
                return redirect(url_for('content_manager_edit_module', module_id=module_id))

        # Update module data
        update_data = {
            'title': title,
            'type': data.get('type', module.get('type', 'lesson')),
            'content': data.get('content', ''),
            'duration': data.get('duration', ''),
            'prerequisites': data.get('prerequisites', ''),
            'objectives': data.get('objectives', ''),
            'video_url': data.get('video_url', ''),
            'resources': data.get('resources', ''),
            'status': data.get('status', module.get('status', 'draft')),
            'updated_at': datetime.now(),
            'updated_by': str(user['_id']),
            'updated_by_role': 'content_manager'
        }

        # Update module
        result = ModuleModel.update_module(module_id, update_data)

        if request.is_json:
            return jsonify({'success': True, 'message': 'Module updated successfully'})
        else:
            flash('Module updated successfully!', 'success')
            return redirect(url_for('content_manager_course_detail', course_id=course['_id']))

    except Exception as e:
        print(f"Error updating module: {e}")
        import traceback
        traceback.print_exc()

        if request.is_json:
            return jsonify({'success': False, 'message': 'An error occurred while updating the module'}), 500
        else:
            flash('An error occurred while updating the module. Please try again.', 'error')
            return redirect(url_for('content_manager_edit_module', module_id=module_id))


@app.route('/content-manager/module/<module_id>/delete', methods=['DELETE'])
@role_required(['content_manager'])
def content_manager_delete_module(module_id):
    """Delete a module (Content Manager)"""
    user = get_current_user()

    # Get module first to verify it exists
    module = ModuleModel.find_module_by_id(module_id)
    if not module:
        return jsonify({'success': False, 'message': 'Module not found'}), 404

    try:
        print(f"DEBUG: Attempting to delete module {module_id}")

        # Delete related quizzes first
        try:
            quizzes = QuizModel.get_quizzes_by_module(module_id)
            for quiz in quizzes:
                QuizModel.delete_quiz(str(quiz['_id']))
                print(f"DEBUG: Deleted quiz {quiz['_id']}")
        except Exception as e:
            print(f"DEBUG: Error deleting quizzes: {e}")

        # Delete module
        result = ModuleModel.delete_module(module_id)
        print(f"DEBUG: Module delete result: {result}")

        if result and result.deleted_count > 0:
            return jsonify({'success': True, 'message': 'Module deleted successfully'})
        else:
            return jsonify({'success': False, 'message': 'Module not found or already deleted'}), 404

    except Exception as e:
        print(f"ERROR: Exception in delete_module: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'An error occurred while deleting the module: {str(e)}'}), 500

@app.route('/content-manager/course/<course_id>/module/create', methods=['POST'])
@role_required(['content_manager'])
def content_manager_create_module(course_id):
    """Create a new module for a course (Content Manager)"""
    user = get_current_user()

    # Get course
    course = CourseModel.find_course_by_id(course_id)
    if not course:
        return jsonify({'success': False, 'message': 'Course not found'}), 404

    try:
        # Get JSON data from request
        data = request.get_json()

        # Debug logging
        print(f"DEBUG: Received data: {data}")
        print(f"DEBUG: Course ID: {course_id}")
        print(f"DEBUG: User: {user['name'] if user else 'No user'}")

        # Validation
        title = data.get('title', '').strip()
        if not title:
            return jsonify({'success': False, 'message': 'Module title is required'}), 400

        # Get next order number
        existing_modules = ModuleModel.get_modules_by_course(course_id)
        next_order = len(existing_modules) + 1

        # Create module data
        module_data = {
            'title': title,
            'course_id': course_id,
            'type': data.get('type', 'lesson'),
            'content': data.get('content', ''),
            'duration': data.get('duration', ''),
            'order': next_order,
            'created_by': str(user['_id']),
            'created_by_role': 'content_manager',
            'status': 'draft'
        }

        print(f"DEBUG: Creating module with data: {module_data}")

        # Create module
        module_id = ModuleModel.create_module(module_data)

        print(f"DEBUG: Module created with ID: {module_id}")

        return jsonify({
            'success': True,
            'message': 'Module created successfully',
            'module_id': module_id
        })

    except Exception as e:
        print(f"ERROR: Exception in create_module: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'An error occurred while creating the module: {str(e)}'
        }), 500




# =====================================================
# SYSTEM ADMIN ROUTES
# =====================================================

@app.route('/system-admin/dashboard')
@role_required(['system_admin'])
def system_admin_dashboard():
    user = get_current_user()
    monitor = get_system_monitor()

    # Get real system metrics
    system_metrics = monitor.get_system_metrics()

    # Get recent system logs (last 10 for dashboard)
    recent_logs = monitor.get_recent_logs(10)

    # Log dashboard access
    monitor.log_system_event('INFO', 'SYSTEM_ADMIN',
                             f'Dashboard accessed by {user["name"]} ({user["email"]})')

    return render_template('system_admin/dashboard.html',
                           user=convert_objectid_to_str(user),
                           metrics=system_metrics,
                           logs=recent_logs)


@app.route('/system-admin/logs')
@role_required(['system_admin'])
def system_admin_logs():
    user = get_current_user()
    monitor = get_system_monitor()

    # Get filter parameters
    level_filter = request.args.get('level', 'all')
    module_filter = request.args.get('module', 'all')
    limit = int(request.args.get('limit', 100))

    # Get all logs
    all_logs = monitor.get_recent_logs(1000)  # Get more logs for filtering

    # Apply filters
    filtered_logs = all_logs
    if level_filter != 'all':
        filtered_logs = [log for log in filtered_logs if log['level'].lower() == level_filter.lower()]

    if module_filter != 'all':
        filtered_logs = [log for log in filtered_logs if log['module'].lower() == module_filter.lower()]

    # Limit results
    filtered_logs = filtered_logs[-limit:]

    # Get unique modules and levels for filter options
    unique_modules = list(set([log['module'] for log in all_logs]))
    unique_levels = list(set([log['level'] for log in all_logs]))

    # Calculate log statistics
    log_stats = {
        'total': len(all_logs),
        'info': len([log for log in all_logs if log['level'] == 'INFO']),
        'warning': len([log for log in all_logs if log['level'] == 'WARNING']),
        'error': len([log for log in all_logs if log['level'] == 'ERROR'])
    }

    # Log access
    monitor.log_system_event('INFO', 'SYSTEM_ADMIN',
                             f'Logs viewed by {user["name"]} ({user["email"]})')

    return render_template('system_admin/logs.html',
                           user=convert_objectid_to_str(user),
                           logs=filtered_logs,
                           log_stats=log_stats,
                           unique_modules=unique_modules,
                           unique_levels=unique_levels,
                           current_filters={
                               'level': level_filter,
                               'module': module_filter,
                               'limit': limit
                           })


@app.route('/system-admin/api/metrics')
@role_required(['system_admin'])
def api_system_metrics():
    """API endpoint for real-time metrics"""
    monitor = get_system_monitor()
    metrics = monitor.get_system_metrics()
    return jsonify(metrics)


@app.route('/system-admin/api/logs')
@role_required(['system_admin'])
def api_system_logs():
    """API endpoint for real-time logs"""
    monitor = get_system_monitor()
    limit = int(request.args.get('limit', 20))
    logs = monitor.get_recent_logs(limit)
    return jsonify(logs)


@app.route('/system-admin/actions/restart', methods=['POST'])
@role_required(['system_admin'])
def system_restart_services():
    """Restart system services (placeholder for actual implementation)"""
    user = get_current_user()
    monitor = get_system_monitor()

    # Log the action
    monitor.log_system_event('WARNING', 'SYSTEM_ADMIN',
                             f'Service restart initiated by {user["name"]} ({user["email"]})')

    # In a real implementation, you would restart actual services here
    # For now, we'll just log the action

    return jsonify({
        'success': True,
        'message': 'Service restart initiated successfully'
    })


@app.route('/system-admin/actions/backup', methods=['POST'])
@role_required(['system_admin'])
def system_backup():
    """Initiate system backup"""
    user = get_current_user()
    monitor = get_system_monitor()

    # Log the action
    monitor.log_system_event('INFO', 'SYSTEM_ADMIN',
                             f'Backup initiated by {user["name"]} ({user["email"]})')

    try:
        # In a real implementation, you would trigger actual backup process
        # For demonstration, we'll just create a backup entry
        backup_time = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"system_backup_{backup_time}"

        # Log successful backup
        monitor.log_system_event('INFO', 'BACKUP',
                                 f'Backup {backup_name} completed successfully')

        return jsonify({
            'success': True,
            'message': f'Backup {backup_name} completed successfully',
            'backup_name': backup_name
        })
    except Exception as e:
        monitor.log_system_event('ERROR', 'BACKUP', f'Backup failed: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'Backup failed: {str(e)}'
        }), 500


@app.route('/system-admin/actions/cleanup', methods=['POST'])
@role_required(['system_admin'])
def system_cleanup():
    """Cleanup inactive sessions and temporary data"""
    user = get_current_user()
    monitor = get_system_monitor()

    # Cleanup inactive sessions
    cleaned_sessions = monitor.cleanup_inactive_sessions(30)  # 30 minutes timeout

    # Log the action
    monitor.log_system_event('INFO', 'SYSTEM_ADMIN',
                             f'System cleanup performed by {user["name"]}: {cleaned_sessions} inactive sessions removed')

    return jsonify({
        'success': True,
        'message': f'System cleanup completed. {cleaned_sessions} inactive sessions removed.',
        'cleaned_sessions': cleaned_sessions
    })


@app.route('/system-admin/database')
@role_required(['system_admin'])
def system_admin_database():
    """Database administration page"""
    user = get_current_user()
    monitor = get_system_monitor()

    # Get database statistics
    db_stats = monitor.get_database_stats()

    # Get collection statistics
    try:
        client = MongoClient(app.config.get('MONGO_URI'))
        db = client['headway_elearning']

        collection_stats = {}
        for collection_name in db.list_collection_names():
            collection = db[collection_name]
            stats = db.command("collStats", collection_name)
            collection_stats[collection_name] = {
                'count': stats.get('count', 0),
                'size': f"{stats.get('size', 0) / 1024:.1f} KB",
                'avg_obj_size': f"{stats.get('avgObjSize', 0):.1f} bytes" if stats.get('avgObjSize') else "0 bytes"
            }
    except Exception as e:
        collection_stats = {}
        monitor.log_system_event('ERROR', 'DATABASE', f'Failed to get collection stats: {str(e)}')

    # Log access
    monitor.log_system_event('INFO', 'SYSTEM_ADMIN',
                             f'Database admin accessed by {user["name"]} ({user["email"]})')

    return render_template('system_admin/database.html',
                           user=convert_objectid_to_str(user),
                           db_stats=db_stats,
                           collection_stats=collection_stats)

@app.before_request
def track_user_activity():
    """Track user sessions and activity"""
    if 'user_id' in session:
        monitor = get_system_monitor()
        session_id = session.get('_permanent_id', 'unknown')
        user_id = session['user_id']
        ip_address = request.remote_addr

        # Track or update session
        if session_id not in monitor.active_sessions:
            monitor.track_session(session_id, user_id, ip_address)
        else:
            monitor.update_session_activity(session_id)

@app.route('/system-admin/api/collections')
@role_required(['system_admin'])
def api_collections():
    """API endpoint for collection statistics"""
    monitor = get_system_monitor()

    try:
        client = MongoClient(app.config.get('MONGO_URI'))
        db = client['headway_elearning']

        collection_stats = {}
        for collection_name in db.list_collection_names():
            collection = db[collection_name]
            stats = db.command("collStats", collection_name)
            collection_stats[collection_name] = {
                'count': stats.get('count', 0),
                'size': f"{stats.get('size', 0) / 1024:.1f} KB",
                'avg_obj_size': f"{stats.get('avgObjSize', 0):.1f} bytes" if stats.get('avgObjSize') else "0 bytes"
            }

        return jsonify(collection_stats)
    except Exception as e:
        monitor.log_system_event('ERROR', 'DATABASE', f'Failed to get collection stats: {str(e)}')
        return jsonify({'error': 'Failed to retrieve collection statistics'}), 500


@app.route('/system-admin/api/collection/<collection_name>/details')
@role_required(['system_admin'])
def api_collection_details(collection_name):
    """API endpoint for detailed collection information"""
    monitor = get_system_monitor()

    try:
        client = MongoClient(app.config.get('MONGO_URI'))
        db = client['headway_elearning']

        if collection_name not in db.list_collection_names():
            return jsonify({'error': 'Collection not found'}), 404

        collection = db[collection_name]
        stats = db.command("collStats", collection_name)

        # Get indexes
        indexes = []
        for index in collection.list_indexes():
            indexes.append({
                'name': index['name'],
                'keys': dict(index['key']),
                'unique': index.get('unique', False)
            })

        details = {
            'name': collection_name,
            'count': stats.get('count', 0),
            'size': f"{stats.get('size', 0) / (1024 ** 2):.2f} MB",
            'avgObjSize': f"{stats.get('avgObjSize', 0):.1f} bytes" if stats.get('avgObjSize') else "0 bytes",
            'storageSize': f"{stats.get('storageSize', 0) / (1024 ** 2):.2f} MB",
            'indexes': indexes,
            'indexSizes': stats.get('indexSizes', {}),
            'totalIndexSize': f"{stats.get('totalIndexSize', 0) / 1024:.1f} KB"
        }

        return jsonify(details)
    except Exception as e:
        monitor.log_system_event('ERROR', 'DATABASE',
                                 f'Failed to get collection details for {collection_name}: {str(e)}')
        return jsonify({'error': 'Failed to retrieve collection details'}), 500


@app.route('/system-admin/api/collection/<collection_name>/optimize', methods=['POST'])
@role_required(['system_admin'])
def api_optimize_collection(collection_name):
    """API endpoint to optimize a specific collection"""
    user = get_current_user()
    monitor = get_system_monitor()

    try:
        client = MongoClient(app.config.get('MONGO_URI'))
        db = client['headway_elearning']

        if collection_name not in db.list_collection_names():
            return jsonify({'success': False, 'message': 'Collection not found'}), 404

        collection = db[collection_name]

        # Reindex the collection
        collection.reindex()

        monitor.log_system_event('INFO', 'DATABASE',
                                 f'Collection {collection_name} optimized by {user["name"]}')

        return jsonify({
            'success': True,
            'message': f'Collection {collection_name} optimized successfully'
        })
    except Exception as e:
        monitor.log_system_event('ERROR', 'DATABASE',
                                 f'Failed to optimize collection {collection_name}: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'Failed to optimize collection: {str(e)}'
        }), 500


@app.route('/system-admin/database/backup', methods=['POST'])
@role_required(['system_admin'])
def database_backup():
    """Initiate database backup"""
    user = get_current_user()
    monitor = get_system_monitor()

    try:
        # In a real implementation, you would use mongodump or similar
        # For now, we'll simulate the backup process
        backup_time = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"headway_backup_{backup_time}"

        # Create backup directory if it doesn't exist
        backup_dir = 'backups'
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)

        # Simulate backup process (in real implementation, use subprocess to call mongodump)
        # subprocess.run([
        #     'mongodump',
        #     '--uri', app.config.get('MONGO_URI'),
        #     '--out', f'{backup_dir}/{backup_name}'
        # ], check=True)

        monitor.log_system_event('INFO', 'BACKUP',
                                 f'Database backup {backup_name} initiated by {user["name"]}')

        return jsonify({
            'success': True,
            'message': f'Database backup {backup_name} initiated successfully',
            'backup_name': backup_name
        })
    except Exception as e:
        monitor.log_system_event('ERROR', 'BACKUP', f'Database backup failed: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'Database backup failed: {str(e)}'
        }), 500


@app.route('/system-admin/database/optimize', methods=['POST'])
@role_required(['system_admin'])
def database_optimize():
    """Optimize entire database"""
    user = get_current_user()
    monitor = get_system_monitor()

    try:
        client = MongoClient(app.config.get('MONGO_URI'))
        db = client['headway_elearning']

        optimized_collections = []

        # Optimize each collection
        for collection_name in db.list_collection_names():
            collection = db[collection_name]
            collection.reindex()
            optimized_collections.append(collection_name)

        monitor.log_system_event('INFO', 'DATABASE',
                                 f'Database optimized by {user["name"]}: {len(optimized_collections)} collections processed')

        return jsonify({
            'success': True,
            'message': f'Database optimized successfully. {len(optimized_collections)} collections processed.',
            'optimized_collections': optimized_collections
        })
    except Exception as e:
        monitor.log_system_event('ERROR', 'DATABASE', f'Database optimization failed: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'Database optimization failed: {str(e)}'
        }), 500


@app.route('/system-admin/database/maintenance', methods=['POST'])
@role_required(['system_admin'])
def database_maintenance():
    """Run database maintenance tasks"""
    user = get_current_user()
    monitor = get_system_monitor()

    try:
        client = MongoClient(app.config.get('MONGO_URI'))
        db = client['headway_elearning']

        maintenance_tasks = []

        # Task 1: Clean up expired sessions
        cleaned_sessions = monitor.cleanup_inactive_sessions(60)  # 1 hour timeout
        if cleaned_sessions > 0:
            maintenance_tasks.append(f"Cleaned {cleaned_sessions} inactive sessions")

        # Task 2: Validate collections
        for collection_name in db.list_collection_names():
            try:
                result = db.validate_collection(collection_name)
                if result.get('valid', False):
                    maintenance_tasks.append(f"Validated collection: {collection_name}")
                else:
                    maintenance_tasks.append(f"Issues found in collection: {collection_name}")
            except:
                maintenance_tasks.append(f"Could not validate collection: {collection_name}")

        # Task 3: Update database statistics
        stats = db.command("dbstats")
        maintenance_tasks.append("Updated database statistics")

        monitor.log_system_event('INFO', 'DATABASE',
                                 f'Database maintenance completed by {user["name"]}: {len(maintenance_tasks)} tasks')

        return jsonify({
            'success': True,
            'message': f'Database maintenance completed successfully. {len(maintenance_tasks)} tasks performed.',
            'tasks': maintenance_tasks
        })
    except Exception as e:
        monitor.log_system_event('ERROR', 'DATABASE', f'Database maintenance failed: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'Database maintenance failed: {str(e)}'
        }), 500


@app.route('/system-admin/logs/export')
@role_required(['system_admin'])
def export_logs():
    """Export system logs as CSV"""
    user = get_current_user()
    monitor = get_system_monitor()

    # Get filter parameters
    level_filter = request.args.get('level', 'all')
    module_filter = request.args.get('module', 'all')
    limit = int(request.args.get('limit', 1000))
    format_type = request.args.get('format', 'csv')

    # Get logs
    all_logs = monitor.get_recent_logs(limit)

    # Apply filters
    filtered_logs = all_logs
    if level_filter != 'all':
        filtered_logs = [log for log in filtered_logs if log['level'].lower() == level_filter.lower()]

    if module_filter != 'all':
        filtered_logs = [log for log in filtered_logs if log['module'].lower() == module_filter.lower()]

    if format_type == 'csv':
        # Create CSV output
        output = io.StringIO()
        fieldnames = ['timestamp', 'level', 'module', 'message', 'ip']
        writer = csv.DictWriter(output, fieldnames=fieldnames)

        writer.writeheader()
        for log in filtered_logs:
            writer.writerow(log)

        # Create response
        csv_output = output.getvalue()
        output.close()

        response = make_response(csv_output)
        response.headers['Content-Type'] = 'text/csv'
        response.headers[
            'Content-Disposition'] = f'attachment; filename=system_logs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'

        monitor.log_system_event('INFO', 'SYSTEM_ADMIN',
                                 f'Logs exported by {user["name"]}: {len(filtered_logs)} records')

        return response

    return jsonify({'error': 'Unsupported export format'}), 400


@app.route('/system-admin/logs/clear', methods=['POST'])
@role_required(['system_admin'])
def clear_logs():
    """Clear system logs"""
    user = get_current_user()
    monitor = get_system_monitor()

    try:
        # Clear in-memory logs
        monitor.system_logs.clear()

        # Clear log files
        log_file = 'logs/system.log'
        if os.path.exists(log_file):
            open(log_file, 'w').close()

        monitor.log_system_event('WARNING', 'SYSTEM_ADMIN',
                                 f'System logs cleared by {user["name"]}')

        return jsonify({
            'success': True,
            'message': 'System logs cleared successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to clear logs: {str(e)}'
        }), 500


@app.route('/system-admin/performance')
@role_required(['system_admin'])
def system_admin_performance():
    """System performance monitoring page"""
    user = get_current_user()
    monitor = get_system_monitor()

    # Get performance metrics
    metrics = monitor.get_system_metrics()

    # Get performance history (simulated for now)
    performance_history = {
        'cpu': [12, 15, 18, 14, 16, 13, 11, 17, 19, 15],
        'memory': [68, 70, 72, 69, 71, 68, 67, 73, 75, 70],
        'disk': [45, 45, 46, 45, 47, 46, 45, 48, 47, 46],
        'timestamps': [
            (datetime.now() - timedelta(minutes=i * 10)).strftime('%H:%M')
            for i in range(9, -1, -1)
        ]
    }

    # Log access
    monitor.log_system_event('INFO', 'SYSTEM_ADMIN',
                             f'Performance monitoring accessed by {user["name"]} ({user["email"]})')

    return render_template('system_admin/performance.html',
                           user=convert_objectid_to_str(user),
                           metrics=metrics,
                           performance_history=performance_history)


@app.route('/system-admin/api/performance-history')
@role_required(['system_admin'])
def api_performance_history():
    """API endpoint for performance history data"""
    # In a real implementation, you would store and retrieve historical data
    # For now, we'll generate sample data

    hours = int(request.args.get('hours', 24))

    data = []
    now = datetime.now()

    for i in range(hours):
        timestamp = now - timedelta(hours=i)
        data.append({
            'timestamp': timestamp.isoformat(),
            'cpu': 10 + (i % 20),  # Simulate CPU usage
            'memory': 60 + (i % 15),  # Simulate memory usage
            'disk': 40 + (i % 10),  # Simulate disk usage
            'active_sessions': 5 + (i % 8)  # Simulate session count
        })

    return jsonify(data[::-1])  # Reverse to get chronological order


@app.route('/system-admin/settings')
@role_required(['system_admin'])
def system_admin_settings():
    """System settings management page"""
    user = get_current_user()
    monitor = get_system_monitor()

    # Get current system settings
    settings = {
        'log_level': 'INFO',
        'session_timeout': 30,
        'max_log_entries': 1000,
        'auto_backup': True,
        'backup_frequency': 'daily',
        'monitoring_interval': 30,
        'alert_email': 'admin@headway.lk',
        'maintenance_mode': False
    }

    # Log access
    monitor.log_system_event('INFO', 'SYSTEM_ADMIN',
                             f'System settings accessed by {user["name"]} ({user["email"]})')

    return render_template('system_admin/settings.html',
                           user=convert_objectid_to_str(user),
                           settings=settings)


@app.route('/system-admin/settings/update', methods=['POST'])
@role_required(['system_admin'])
def update_system_settings():
    """Update system settings"""
    user = get_current_user()
    monitor = get_system_monitor()

    try:
        # Get form data
        settings = {
            'log_level': request.form.get('log_level', 'INFO'),
            'session_timeout': int(request.form.get('session_timeout', 30)),
            'max_log_entries': int(request.form.get('max_log_entries', 1000)),
            'auto_backup': 'auto_backup' in request.form,
            'backup_frequency': request.form.get('backup_frequency', 'daily'),
            'monitoring_interval': int(request.form.get('monitoring_interval', 30)),
            'alert_email': request.form.get('alert_email', ''),
            'maintenance_mode': 'maintenance_mode' in request.form
        }

        # In a real implementation, you would save these settings to database or config file
        # For now, we'll just log the changes

        monitor.log_system_event('INFO', 'SYSTEM_ADMIN',
                                 f'System settings updated by {user["name"]}: {settings}')

        flash('System settings updated successfully!', 'success')
        return redirect(url_for('system_admin_settings'))

    except Exception as e:
        monitor.log_system_event('ERROR', 'SYSTEM_ADMIN',
                                 f'Failed to update system settings: {str(e)}')
        flash('Failed to update system settings. Please try again.', 'error')
        return redirect(url_for('system_admin_settings'))


# =====================================================
# API ROUTES (for AJAX calls)
# =====================================================

@app.route('/api/user-stats')
@login_required
def api_user_stats():
    user = get_current_user()

    if user['role'] == 'student':
        user_id = str(user['_id'])
        enrollments = EnrollmentModel.get_user_enrollments(user_id)

        completed_modules = sum(len(e.get('completed_modules', [])) for e in enrollments)

        stats = {
            'total_courses': len(enrollments),
            'completed_modules': completed_modules,
            'points': user.get('points', 0),
            'badges': len(user.get('badges', []))
        }
        return jsonify(stats)

    return jsonify({'error': 'Invalid user role'}), 400


@app.route('/api/course-progress/<course_id>')
@login_required
def api_course_progress(course_id):
    user = get_current_user()

    if user['role'] == 'student':
        user_id = str(user['_id'])
        enrollment = EnrollmentModel.find_enrollment(user_id, course_id)

        if enrollment:
            total_modules = len(ModuleModel.get_modules_by_course(course_id))
            return jsonify({
                'progress': enrollment.get('progress', 0),
                'completed_modules': len(enrollment.get('completed_modules', [])),
                'total_modules': total_modules
            })

    return jsonify({'error': 'Enrollment not found'}), 404


# =====================================================
# ERROR HANDLERS
# =====================================================

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    return render_template('errors/500.html'), 500


@app.errorhandler(403)
def forbidden_error(error):
    return render_template('errors/403.html'), 403


# =====================================================
# CONTEXT PROCESSORS
# =====================================================

@app.context_processor
def inject_user():
    return dict(current_user=get_current_user())


# =====================================================
# APPLICATION CLEANUP
# =====================================================

@app.teardown_appcontext
def close_db(error):
    """Close database connection when app context tears down"""
    pass  # MongoDB connection is handled globally


# =====================================================
# MAIN EXECUTION
# =====================================================

if __name__ == '__main__':
    try:
        app.run(debug=True, host='0.0.0.0', port=5000)
    except Exception as e:
        print(f"❌ Error starting application: {e}")
    finally:
        mongo_db.close_connection()