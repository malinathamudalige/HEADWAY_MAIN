# database.py - MongoDB Configuration and Models
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
        self.database_name = os.getenv('DATABASE_NAME', 'HEADWAY_MAIN')

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

    # Add to ModuleModel class:
    @staticmethod
    def delete_module(module_id):
        """Delete module"""
        if isinstance(module_id, str):
            module_id = ObjectId(module_id)
        return modules_collection.delete_one({'_id': module_id})

    # Add to QuizModel class:
    @staticmethod
    def get_quizzes_by_module(module_id):
        """Get quizzes by module ID"""
        return list(assessments_collection.find({'module_id': module_id}))

    @staticmethod
    def delete_quiz(quiz_id):
        """Delete quiz"""
        if isinstance(quiz_id, str):
            quiz_id = ObjectId(quiz_id)
        return assessments_collection.delete_one({'_id': quiz_id})

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
    def get_user_course_results(user_id, course_id):
        """Get user's quiz results for a specific course"""
        return list(quiz_results_collection.find({
            'user_id': user_id,
            'course_id': course_id
        }))


class LeaderboardModel:
    @staticmethod
    def update_leaderboard(quiz_result_data):
        """Update leaderboard with new quiz result"""
        user_id = quiz_result_data['user_id']
        course_id = quiz_result_data['course_id']
        score_percentage = quiz_result_data['score_percentage']

        # Find existing leaderboard entry
        existing_entry = leaderboard_collection.find_one({
            'user_id': user_id,
            'course_id': course_id
        })

        if existing_entry:
            # Update existing entry
            new_total_score = existing_entry['total_score'] + score_percentage
            new_quiz_count = existing_entry['quiz_count'] + 1
            new_average_score = new_total_score / new_quiz_count

            # Update best score if this one is higher
            new_best_score = max(existing_entry['best_score'], score_percentage)

            leaderboard_collection.update_one(
                {'_id': existing_entry['_id']},
                {'$set': {
                    'total_score': new_total_score,
                    'quiz_count': new_quiz_count,
                    'average_score': round(new_average_score, 2),
                    'best_score': new_best_score,
                    'last_quiz_date': datetime.now(),
                    'updated_at': datetime.now()
                }}
            )
        else:
            # Create new leaderboard entry
            leaderboard_data = {
                'user_id': user_id,
                'course_id': course_id,
                'total_score': score_percentage,
                'quiz_count': 1,
                'average_score': score_percentage,
                'best_score': score_percentage,
                'last_quiz_date': datetime.now(),
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
            leaderboard_collection.insert_one(leaderboard_data)

    @staticmethod
    def get_course_leaderboard(course_id, limit=50):
        """Get leaderboard for a specific course"""
        pipeline = [
            {'$match': {'course_id': course_id}},
            {'$sort': {'average_score': -1, 'best_score': -1}},
            {'$limit': limit}
        ]

        leaderboard_data = list(leaderboard_collection.aggregate(pipeline))

        # Enhance with user details
        enhanced_leaderboard = []
        for entry in leaderboard_data:
            user = UserModel.find_user_by_id(entry['user_id'])
            if user:
                entry['user'] = {
                    'name': user['name'],
                    'email': user['email'],
                    'avatar': user.get('avatar'),
                    'level': user.get('level', 'Beginner')
                }
                enhanced_leaderboard.append(entry)

        # Add rank
        for i, entry in enumerate(enhanced_leaderboard):
            entry['rank'] = i + 1

        return enhanced_leaderboard

    @staticmethod
    def get_user_course_ranking(user_id, course_id):
        """Get user's ranking in a specific course"""
        pipeline = [
            {'$match': {'course_id': course_id}},
            {'$sort': {'average_score': -1, 'best_score': -1}},
            {'$group': {
                '_id': None,
                'users': {'$push': {
                    'user_id': '$user_id',
                    'average_score': '$average_score'
                }}
            }}
        ]

        result = list(leaderboard_collection.aggregate(pipeline))
        if result and result[0]['users']:
            users = result[0]['users']
            for i, user_data in enumerate(users):
                if user_data['user_id'] == user_id:
                    return {
                        'rank': i + 1,
                        'total_participants': len(users),
                        'average_score': user_data['average_score']
                    }

        return None

    @staticmethod
    def get_top_performers(course_id, limit=10):
        """Get top performers for a course"""
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

        analytics_data = {
            'type': 'system_stats',
            'total_users': total_users,
            'total_courses': total_courses,
            'total_enrollments': total_enrollments,
            'completion_rate': round(completion_rate, 1),
            'avg_engagement': 4.2,  # This would be calculated from user activity
            'last_updated': datetime.now()
        }

        analytics_collection.update_one(
            {'type': 'system_stats'},
            {'$set': analytics_data},
            upsert=True
        )

        return analytics_data