# database.py - MongoDB Configuration and Models (Complete Updated Version)
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
from werkzeug.security import generate_password_hash
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class MongoDB:
    def __init__(self):
        # MongoDB connection string
        self.connection_string = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
        self.database_name = os.getenv('DATABASE_NAME', 'headway_elearning')

        # Initialize connection
        self.client = None
        self.db = None
        self.connect()

    def connect(self):
        """Establish MongoDB connection"""
        try:
            self.client = MongoClient(self.connection_string)
            self.db = self.client[self.database_name]

            # Test connection
            self.client.admin.command('ping')
            print(f"✅ Connected to MongoDB: {self.database_name}")

        except Exception as e:
            print(f"❌ MongoDB connection failed: {e}")
            raise e

    def close_connection(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            print("🔌 MongoDB connection closed")


# Initialize MongoDB instance
mongo_db = MongoDB()

# Collection references
users_collection = mongo_db.db.users
courses_collection = mongo_db.db.courses
modules_collection = mongo_db.db.modules
enrollments_collection = mongo_db.db.enrollments
assessments_collection = mongo_db.db.assessments
badges_collection = mongo_db.db.badges
analytics_collection = mongo_db.db.analytics
quiz_results_collection = mongo_db.db.quiz_results
leaderboard_collection = mongo_db.db.leaderboards


class UserModel:
    @staticmethod
    def create_user(user_data):
        """Create a new user"""
        user_data['created_at'] = datetime.now()
        user_data['updated_at'] = datetime.now()

        # Hash password
        if 'password' in user_data:
            user_data['password'] = generate_password_hash(user_data['password'])

        result = users_collection.insert_one(user_data)
        return str(result.inserted_id)

    @staticmethod
    def find_user_by_email(email):
        """Find user by email"""
        return users_collection.find_one({'email': email})

    @staticmethod
    def find_user_by_id(user_id):
        """Find user by ID"""
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
        return users_collection.find_one({'_id': user_id})

    @staticmethod
    def get_all_users():
        """Get all users"""
        return list(users_collection.find())

    @staticmethod
    def get_users_by_role(role):
        """Get all users with a specific role"""
        return list(users_collection.find({'role': role}))

    @staticmethod
    def update_user(user_id, update_data):
        """Update user"""
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)

        update_data['updated_at'] = datetime.now()
        return users_collection.update_one(
            {'_id': user_id},
            {'$set': update_data}
        )

    @staticmethod
    def delete_user(user_id):
        """Delete user"""
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
        return users_collection.delete_one({'_id': user_id})


class CourseModel:
    @staticmethod
    def create_course(course_data):
        """Create a new course"""
        course_data['created_at'] = datetime.now()
        course_data['updated_at'] = datetime.now()
        course_data['students_enrolled'] = 0
        course_data['rating'] = 0.0

        result = courses_collection.insert_one(course_data)
        return str(result.inserted_id)

    @staticmethod
    def get_all_courses():
        """Get all courses"""
        return list(courses_collection.find())

    @staticmethod
    def find_course_by_id(course_id):
        """Find course by ID"""
        if isinstance(course_id, str):
            course_id = ObjectId(course_id)
        return courses_collection.find_one({'_id': course_id})

    @staticmethod
    def get_courses_by_instructor(instructor_id):
        """Get courses by instructor"""
        return list(courses_collection.find({'instructor_id': instructor_id}))

    @staticmethod
    def update_course(course_id, update_data):
        """Update course"""
        if isinstance(course_id, str):
            course_id = ObjectId(course_id)

        update_data['updated_at'] = datetime.now()
        return courses_collection.update_one(
            {'_id': course_id},
            {'$set': update_data}
        )

    @staticmethod
    def delete_course(course_id):
        """Delete course"""
        if isinstance(course_id, str):
            course_id = ObjectId(course_id)
        return courses_collection.delete_one({'_id': course_id})


class ModuleModel:
    @staticmethod
    def create_module(module_data):
        """Create a new module"""
        module_data['created_at'] = datetime.now()
        module_data['completed_by'] = []

        result = modules_collection.insert_one(module_data)
        return str(result.inserted_id)

    @staticmethod
    def get_modules_by_course(course_id):
        """Get modules by course ID"""
        return list(modules_collection.find({'course_id': course_id}).sort('order', 1))

    @staticmethod
    def find_module_by_id(module_id):
        """Find module by ID"""
        if isinstance(module_id, str):
            module_id = ObjectId(module_id)
        return modules_collection.find_one({'_id': module_id})

    @staticmethod
    def mark_module_completed(module_id, user_id):
        """Mark module as completed by user"""
        if isinstance(module_id, str):
            module_id = ObjectId(module_id)

        return modules_collection.update_one(
            {'_id': module_id},
            {'$addToSet': {'completed_by': user_id}}
        )

    @staticmethod
    def delete_module(module_id):
        """Delete module"""
        if isinstance(module_id, str):
            module_id = ObjectId(module_id)
        return modules_collection.delete_one({'_id': module_id})

    @staticmethod
    def update_module(module_id, update_data):
        """Update module"""
        if isinstance(module_id, str):
            module_id = ObjectId(module_id)

        update_data['updated_at'] = datetime.now()
        return modules_collection.update_one(
            {'_id': module_id},
            {'$set': update_data}
        )


class EnrollmentModel:
    @staticmethod
    def create_enrollment(enrollment_data):
        """Create a new enrollment"""
        enrollment_data['enrolled_date'] = datetime.now()
        enrollment_data['progress'] = 0
        enrollment_data['status'] = 'active'
        enrollment_data['completed_modules'] = []
        enrollment_data['grade'] = None

        result = enrollments_collection.insert_one(enrollment_data)
        return str(result.inserted_id)

    @staticmethod
    def get_user_enrollments(user_id):
        """Get all enrollments for a user"""
        return list(enrollments_collection.find({'user_id': user_id}))

    @staticmethod
    def get_course_enrollments(course_id):
        """Get all enrollments for a course"""
        return list(enrollments_collection.find({'course_id': course_id}))

    @staticmethod
    def find_enrollment(user_id, course_id):
        """Find specific enrollment"""
        return enrollments_collection.find_one({
            'user_id': user_id,
            'course_id': course_id
        })

    @staticmethod
    def update_enrollment_progress(user_id, course_id, progress_data):
        """Update enrollment progress"""
        return enrollments_collection.update_one(
            {'user_id': user_id, 'course_id': course_id},
            {'$set': progress_data}
        )


class AssessmentModel:
    @staticmethod
    def create_assessment(assessment_data):
        """Create a new assessment"""
        assessment_data['created_at'] = datetime.now()

        result = assessments_collection.insert_one(assessment_data)
        return str(result.inserted_id)

    @staticmethod
    def get_assessment_by_module(module_id):
        """Get assessment by module ID"""
        return assessments_collection.find_one({'module_id': module_id})

    @staticmethod
    def find_assessment_by_id(assessment_id):
        """Find assessment by ID"""
        if isinstance(assessment_id, str):
            assessment_id = ObjectId(assessment_id)
        return assessments_collection.find_one({'_id': assessment_id})

    @staticmethod
    def get_assessments_by_module(module_id):
        """Get assessments by module ID"""
        return list(assessments_collection.find({'module_id': module_id}))

    @staticmethod
    def delete_assessment(assessment_id):
        """Delete assessment"""
        if isinstance(assessment_id, str):
            assessment_id = ObjectId(assessment_id)
        return assessments_collection.delete_one({'_id': assessment_id})


class QuizModel:
    @staticmethod
    def create_quiz(quiz_data):
        """Create a new quiz"""
        quiz_data['created_at'] = datetime.now()
        result = assessments_collection.insert_one(quiz_data)
        return str(result.inserted_id)

    @staticmethod
    def find_quiz_by_id(quiz_id):
        """Find quiz by ID"""
        if isinstance(quiz_id, str):
            quiz_id = ObjectId(quiz_id)
        return assessments_collection.find_one({'_id': quiz_id})

    @staticmethod
    def get_module_quiz(module_id):
        """Get quiz for a specific module"""
        return assessments_collection.find_one({'module_id': module_id})

    @staticmethod
    def get_quizzes_by_module(module_id):
        """Get all quizzes by module ID"""
        return list(assessments_collection.find({'module_id': module_id}))

    @staticmethod
    def delete_quiz(quiz_id):
        """Delete quiz"""
        if isinstance(quiz_id, str):
            quiz_id = ObjectId(quiz_id)
        return assessments_collection.delete_one({'_id': quiz_id})

    @staticmethod
    def update_quiz(quiz_id, update_data):
        """Update quiz"""
        if isinstance(quiz_id, str):
            quiz_id = ObjectId(quiz_id)

        update_data['updated_at'] = datetime.now()
        return assessments_collection.update_one(
            {'_id': quiz_id},
            {'$set': update_data}
        )


class QuizResultModel:
    @staticmethod
    def create_result(result_data):
        """Create a new quiz result"""
        result_data['created_at'] = datetime.now()
        result = quiz_results_collection.insert_one(result_data)

        # Update leaderboard
        LeaderboardModel.update_leaderboard(result_data)

        return str(result.inserted_id)

    @staticmethod
    def find_result_by_id(result_id):
        """Find quiz result by ID"""
        if isinstance(result_id, str):
            result_id = ObjectId(result_id)
        return quiz_results_collection.find_one({'_id': result_id})

    @staticmethod
    def find_result(user_id, quiz_id):
        """Find quiz result by user and quiz"""
        return quiz_results_collection.find_one({
            'user_id': user_id,
            'quiz_id': quiz_id
        })

    @staticmethod
    def get_user_results(user_id):
        """Get all quiz results for a user"""
        return list(quiz_results_collection.find({'user_id': user_id}))

    @staticmethod
    def get_quiz_results(quiz_id):
        """Get all results for a specific quiz"""
        return list(quiz_results_collection.find({'quiz_id': quiz_id}))

    @staticmethod
    def get_course_results(course_id):
        """Get all quiz results for a course"""
        return list(quiz_results_collection.find({'course_id': course_id}))

    @staticmethod
    def update_result(result_id, update_data):
        """Update quiz result"""
        if isinstance(result_id, str):
            result_id = ObjectId(result_id)

        return quiz_results_collection.update_one(
            {'_id': result_id},
            {'$set': update_data}
        )


class LeaderboardModel:
    @staticmethod
    def update_leaderboard(quiz_result):
        """Update leaderboard based on quiz result"""
        user_id = quiz_result['user_id']
        course_id = quiz_result['course_id']
        score = quiz_result['score_percentage']

        # Find existing leaderboard entry
        existing_entry = leaderboard_collection.find_one({
            'user_id': user_id,
            'course_id': course_id
        })

        if existing_entry:
            # Update existing entry
            new_total_score = existing_entry['total_score'] + score
            new_quiz_count = existing_entry['quiz_count'] + 1
            new_avg_score = new_total_score / new_quiz_count
            new_best_score = max(existing_entry['best_score'], score)

            leaderboard_collection.update_one(
                {'_id': existing_entry['_id']},
                {
                    '$set': {
                        'total_score': new_total_score,
                        'quiz_count': new_quiz_count,
                        'average_score': round(new_avg_score, 2),
                        'best_score': new_best_score,
                        'last_activity': datetime.now()
                    }
                }
            )
        else:
            # Create new leaderboard entry
            leaderboard_data = {
                'user_id': user_id,
                'course_id': course_id,
                'total_score': score,
                'quiz_count': 1,
                'average_score': score,
                'best_score': score,
                'last_activity': datetime.now(),
                'created_at': datetime.now()
            }
            leaderboard_collection.insert_one(leaderboard_data)

    @staticmethod
    def get_course_leaderboard(course_id, limit=50):
        """Get leaderboard for a specific course"""
        return list(leaderboard_collection.find({'course_id': course_id})
                    .sort('average_score', -1)
                    .limit(limit))

    @staticmethod
    def get_user_ranking(user_id, course_id):
        """Get user's ranking in a specific course"""
        # Get all users in course ordered by average score
        all_users = list(leaderboard_collection.find({'course_id': course_id})
                         .sort('average_score', -1))

        for index, entry in enumerate(all_users):
            if entry['user_id'] == user_id:
                return index + 1

        return None

    @staticmethod
    def get_top_performers(course_id, limit=10):
        """Get top performers for a specific course"""
        return LeaderboardModel.get_course_leaderboard(course_id, limit)


class BadgeModel:
    @staticmethod
    def create_badge(badge_data):
        """Create a new badge"""
        result = badges_collection.insert_one(badge_data)
        return str(result.inserted_id)

    @staticmethod
    def get_all_badges():
        """Get all badges"""
        return list(badges_collection.find())

    @staticmethod
    def find_badge_by_name(badge_name):
        """Find badge by name"""
        return badges_collection.find_one({'name': badge_name})

    @staticmethod
    def find_badge_by_id(badge_id):
        """Find badge by ID"""
        if isinstance(badge_id, str):
            badge_id = ObjectId(badge_id)
        return badges_collection.find_one({'_id': badge_id})

    @staticmethod
    def update_badge(badge_id, update_data):
        """Update badge"""
        if isinstance(badge_id, str):
            badge_id = ObjectId(badge_id)

        return badges_collection.update_one(
            {'_id': badge_id},
            {'$set': update_data}
        )

    @staticmethod
    def delete_badge(badge_id):
        """Delete badge"""
        if isinstance(badge_id, str):
            badge_id = ObjectId(badge_id)
        return badges_collection.delete_one({'_id': badge_id})


class AnalyticsModel:
    @staticmethod
    def create_analytics_record(analytics_data):
        """Create analytics record"""
        analytics_data['timestamp'] = datetime.now()

        result = analytics_collection.insert_one(analytics_data)
        return str(result.inserted_id)

    @staticmethod
    def get_system_analytics():
        """Get system-wide analytics"""
        return analytics_collection.find_one({'type': 'system_stats'})

    @staticmethod
    def get_course_analytics(course_id):
        """Get course-specific analytics"""
        return analytics_collection.find_one({
            'type': 'course_performance',
            'course_id': course_id
        })

    @staticmethod
    def update_system_stats():
        """Update system statistics"""
        total_users = users_collection.count_documents({})
        total_courses = courses_collection.count_documents({})
        total_enrollments = enrollments_collection.count_documents({})

        # Calculate completion rate
        completed_enrollments = enrollments_collection.count_documents({'progress': 100})
        completion_rate = (completed_enrollments / total_enrollments * 100) if total_enrollments > 0 else 0

        # Calculate average engagement (example metric)
        total_quiz_results = quiz_results_collection.count_documents({})
        avg_engagement = min(total_quiz_results / total_users * 10, 5.0) if total_users > 0 else 0

        analytics_data = {
            'type': 'system_stats',
            'total_users': total_users,
            'total_courses': total_courses,
            'total_enrollments': total_enrollments,
            'completion_rate': round(completion_rate, 1),
            'avg_engagement': round(avg_engagement, 1),
            'total_quiz_results': total_quiz_results,
            'last_updated': datetime.now()
        }

        analytics_collection.update_one(
            {'type': 'system_stats'},
            {'$set': analytics_data},
            upsert=True
        )

        return analytics_data

    @staticmethod
    def update_course_analytics(course_id):
        """Update analytics for a specific course"""
        # Get course enrollments
        enrollments = EnrollmentModel.get_course_enrollments(course_id)
        total_enrollments = len(enrollments)

        if total_enrollments == 0:
            return None

        # Calculate completion rate
        completed = sum(1 for e in enrollments if e.get('progress', 0) == 100)
        completion_rate = (completed / total_enrollments * 100)

        # Calculate average progress
        avg_progress = sum(e.get('progress', 0) for e in enrollments) / total_enrollments

        # Get quiz results for this course
        quiz_results = QuizResultModel.get_course_results(course_id)
        avg_score = sum(r.get('score_percentage', 0) for r in quiz_results) / len(quiz_results) if quiz_results else 0

        analytics_data = {
            'type': 'course_performance',
            'course_id': course_id,
            'total_enrollments': total_enrollments,
            'completion_rate': round(completion_rate, 1),
            'avg_progress': round(avg_progress, 1),
            'avg_score': round(avg_score, 1),
            'total_quiz_attempts': len(quiz_results),
            'last_updated': datetime.now()
        }

        analytics_collection.update_one(
            {'type': 'course_performance', 'course_id': course_id},
            {'$set': analytics_data},
            upsert=True
        )

        return analytics_data

    @staticmethod
    def get_user_analytics(user_id):
        """Get analytics for a specific user"""
        # Get user enrollments
        enrollments = EnrollmentModel.get_user_enrollments(user_id)

        # Get user quiz results
        quiz_results = QuizResultModel.get_user_results(user_id)

        # Calculate user statistics
        total_courses = len(enrollments)
        completed_courses = sum(1 for e in enrollments if e.get('progress', 0) == 100)
        avg_progress = sum(e.get('progress', 0) for e in enrollments) / total_courses if total_courses > 0 else 0
        avg_quiz_score = sum(r.get('score_percentage', 0) for r in quiz_results) / len(
            quiz_results) if quiz_results else 0

        return {
            'user_id': user_id,
            'total_courses': total_courses,
            'completed_courses': completed_courses,
            'avg_progress': round(avg_progress, 1),
            'total_quizzes': len(quiz_results),
            'avg_quiz_score': round(avg_quiz_score, 1),
            'last_updated': datetime.now()
        }


# Additional utility functions
def convert_objectid_to_str(data):
    """Convert ObjectId to string in a document or list of documents"""
    if isinstance(data, list):
        return [convert_objectid_to_str(item) for item in data]
    elif isinstance(data, dict):
        converted = {}
        for key, value in data.items():
            if isinstance(value, ObjectId):
                converted[key] = str(value)
            elif isinstance(value, dict):
                converted[key] = convert_objectid_to_str(value)
            elif isinstance(value, list):
                converted[key] = convert_objectid_to_str(value)
            else:
                converted[key] = value
        return converted
    else:
        return data


def create_indexes():
    """Create database indexes for better performance"""
    try:
        # User indexes
        users_collection.create_index("email", unique=True)
        users_collection.create_index("role")

        # Course indexes
        courses_collection.create_index("instructor_id")
        courses_collection.create_index("status")
        courses_collection.create_index("level")
        courses_collection.create_index("category")
        courses_collection.create_index("created_at")

        # Module indexes
        modules_collection.create_index("course_id")
        modules_collection.create_index([("course_id", 1), ("order", 1)])

        # Enrollment indexes
        enrollments_collection.create_index([("user_id", 1), ("course_id", 1)], unique=True)
        enrollments_collection.create_index("user_id")
        enrollments_collection.create_index("course_id")

        # Quiz result indexes
        quiz_results_collection.create_index("user_id")
        quiz_results_collection.create_index("quiz_id")
        quiz_results_collection.create_index("course_id")
        quiz_results_collection.create_index([("user_id", 1), ("quiz_id", 1)])

        # Leaderboard indexes
        leaderboard_collection.create_index([("course_id", 1), ("average_score", -1)])
        leaderboard_collection.create_index([("user_id", 1), ("course_id", 1)], unique=True)

        # Analytics indexes
        analytics_collection.create_index("type")
        analytics_collection.create_index([("type", 1), ("course_id", 1)])

        print("✅ Database indexes created successfully")

    except Exception as e:
        print(f"⚠️ Warning: Could not create some indexes: {e}")


# Initialize indexes when module is imported
if __name__ == "__main__":
    create_indexes()