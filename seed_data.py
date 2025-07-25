# enhanced_seed_data.py - Comprehensive seeder with 20 records each for courses, modules, and assessments
from database import *
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import random


def comprehensive_seed_database():
    """Populate MongoDB with 20 records each for courses, modules, and assessments"""
    print("🌱 Starting comprehensive database seeding with 20 records each...")

    # Clear existing data (optional)
    clear_database()

    # Seed data in order
    user_ids = seed_users()
    course_ids = seed_20_courses(user_ids)
    module_ids = seed_20_modules(course_ids)
    quiz_ids = seed_20_assessments(module_ids)
    seed_enrollments(user_ids, course_ids)
    seed_quiz_results(user_ids, quiz_ids, course_ids)
    seed_badges()
    seed_analytics()

    print("✅ Comprehensive database seeding completed with 20 records each!")


def clear_database():
    """Clear all collections"""
    print("🧹 Clearing existing data...")

    collections = [
        users_collection,
        courses_collection,
        modules_collection,
        enrollments_collection,
        assessments_collection,
        quiz_results_collection,
        leaderboard_collection,
        badges_collection,
        analytics_collection
    ]

    for collection in collections:
        collection.delete_many({})

    print("✨ Database cleared")


def seed_users():
    """Seed users with different roles"""
    print("👥 Seeding users...")

    users_data = [
        {
            'name': 'John Student',
            'email': 'student@headway.lk',
            'password': 'student123',
            'role': 'student',
            'level': 'Beginner',
            'points': 0,
            'badges': [],
            'avatar': '/static/images/student.jpg'
        },
        {
            'name': 'Sarah Teacher',
            'email': 'teacher@headway.lk',
            'password': 'teacher123',
            'role': 'educator',
            'department': 'English Language',
            'experience': '5 years',
            'avatar': '/static/images/teacher.jpg'
        },
        {
            'name': 'Michael Brown',
            'email': 'michael@headway.lk',
            'password': 'teacher123',
            'role': 'educator',
            'department': 'Advanced English',
            'experience': '8 years',
            'avatar': '/static/images/teacher2.jpg'
        },
        {
            'name': 'Emma Wilson',
            'email': 'emma@headway.lk',
            'password': 'teacher123',
            'role': 'educator',
            'department': 'Business English',
            'experience': '6 years',
            'avatar': '/static/images/teacher3.jpg'
        },
        {
            'name': 'Admin User',
            'email': 'admin@headway.lk',
            'password': 'admin123',
            'role': 'admin',
            'avatar': '/static/images/admin.jpg'
        },
        {
            'name': 'Content Manager',
            'email': 'content@headway.lk',
            'password': 'content123',
            'role': 'content_manager',
            'avatar': '/static/images/content.jpg'
        },
        {
            'name': 'System Admin',
            'email': 'sysadmin@headway.lk',
            'password': 'sysadmin123',
            'role': 'system_admin',
            'avatar': '/static/images/sysadmin.jpg'
        }
    ]

    user_ids = {}
    for user_data in users_data:
        user_id = UserModel.create_user(user_data)
        user_ids[user_data['email']] = user_id
        print(f"  ✓ Created user: {user_data['name']} ({user_data['role']})")

    return user_ids


def seed_20_courses(user_ids):
    """Seed 20 comprehensive courses"""
    print("📚 Seeding 20 courses...")

    educators = [
        ('Sarah Teacher', user_ids.get('teacher@headway.lk')),
        ('Michael Brown', user_ids.get('michael@headway.lk')),
        ('Emma Wilson', user_ids.get('emma@headway.lk'))
    ]

    courses_data = [
        {
            'title': 'English Grammar Fundamentals',
            'description': 'Master the basics of English grammar with interactive lessons and quizzes covering parts of speech, sentence structure, and essential grammar rules.',
            'level': 'Beginner',
            'duration': '8 weeks',
            'image': '/static/images/grammar-course.jpg',
            'category': 'Grammar'
        },
        {
            'title': 'Business English Communication',
            'description': 'Develop professional English communication skills for the workplace including email writing, presentations, and meeting participation.',
            'level': 'Intermediate',
            'duration': '6 weeks',
            'image': '/static/images/business-course.jpg',
            'category': 'Business English'
        },
        {
            'title': 'IELTS Preparation Course',
            'description': 'Comprehensive preparation for the IELTS academic and general training tests with practice materials and expert strategies.',
            'level': 'Advanced',
            'duration': '12 weeks',
            'image': '/static/images/ielts-course.jpg',
            'category': 'Test Preparation'
        },
        {
            'title': 'English Pronunciation Mastery',
            'description': 'Perfect your English pronunciation with phonetics, stress patterns, and intonation exercises for clear communication.',
            'level': 'Intermediate',
            'duration': '10 weeks',
            'image': '/static/images/pronunciation-course.jpg',
            'category': 'Pronunciation'
        },
        {
            'title': 'Academic Writing Skills',
            'description': 'Learn to write academic essays, research papers, and reports with proper structure, citations, and academic vocabulary.',
            'level': 'Advanced',
            'duration': '14 weeks',
            'image': '/static/images/writing-course.jpg',
            'category': 'Writing'
        },
        {
            'title': 'English Conversation for Beginners',
            'description': 'Build confidence in everyday English conversations with practical dialogues and speaking practice activities.',
            'level': 'Beginner',
            'duration': '6 weeks',
            'image': '/static/images/conversation-course.jpg',
            'category': 'Speaking'
        },
        {
            'title': 'Advanced English Vocabulary',
            'description': 'Expand your vocabulary with advanced words, idioms, phrasal verbs, and expressions for fluent communication.',
            'level': 'Advanced',
            'duration': '8 weeks',
            'image': '/static/images/vocabulary-course.jpg',
            'category': 'Vocabulary'
        },
        {
            'title': 'English Reading Comprehension',
            'description': 'Improve reading skills with various text types, comprehension strategies, and critical analysis techniques.',
            'level': 'Intermediate',
            'duration': '7 weeks',
            'image': '/static/images/reading-course.jpg',
            'category': 'Reading'
        },
        {
            'title': 'TOEFL Test Preparation',
            'description': 'Complete TOEFL preparation covering all four skills with practice tests and proven test-taking strategies.',
            'level': 'Advanced',
            'duration': '10 weeks',
            'image': '/static/images/toefl-course.jpg',
            'category': 'Test Preparation'
        },
        {
            'title': 'English Listening Skills',
            'description': 'Enhance your listening comprehension with authentic audio materials, accents, and listening strategies.',
            'level': 'Intermediate',
            'duration': '6 weeks',
            'image': '/static/images/listening-course.jpg',
            'category': 'Listening'
        },
        {
            'title': 'Creative Writing in English',
            'description': 'Explore creative writing techniques including storytelling, poetry, and descriptive writing in English.',
            'level': 'Intermediate',
            'duration': '9 weeks',
            'image': '/static/images/creative-writing-course.jpg',
            'category': 'Writing'
        },
        {
            'title': 'English for Healthcare Professionals',
            'description': 'Specialized English course for healthcare workers covering medical terminology and patient communication.',
            'level': 'Intermediate',
            'duration': '8 weeks',
            'image': '/static/images/healthcare-english-course.jpg',
            'category': 'Professional English'
        },
        {
            'title': 'British vs American English',
            'description': 'Understand the differences between British and American English in vocabulary, pronunciation, and grammar.',
            'level': 'Intermediate',
            'duration': '5 weeks',
            'image': '/static/images/british-american-course.jpg',
            'category': 'Culture'
        },
        {
            'title': 'English Public Speaking',
            'description': 'Develop confident public speaking skills with techniques for presentations, speeches, and audience engagement.',
            'level': 'Advanced',
            'duration': '7 weeks',
            'image': '/static/images/speaking-course.jpg',
            'category': 'Speaking'
        },
        {
            'title': 'English Literature Appreciation',
            'description': 'Explore classic and contemporary English literature with analysis, interpretation, and discussion.',
            'level': 'Advanced',
            'duration': '12 weeks',
            'image': '/static/images/literature-course.jpg',
            'category': 'Literature'
        },
        {
            'title': 'English for Tourism Industry',
            'description': 'Learn specialized English for tourism professionals including customer service and travel terminology.',
            'level': 'Intermediate',
            'duration': '6 weeks',
            'image': '/static/images/tourism-english-course.jpg',
            'category': 'Professional English'
        },
        {
            'title': 'English Idioms and Expressions',
            'description': 'Master common English idioms, expressions, and colloquial language for natural communication.',
            'level': 'Intermediate',
            'duration': '8 weeks',
            'image': '/static/images/idioms-course.jpg',
            'category': 'Vocabulary'
        },
        {
            'title': 'English Email Writing Mastery',
            'description': 'Perfect your email writing skills for professional and personal communication with proper etiquette.',
            'level': 'Beginner',
            'duration': '4 weeks',
            'image': '/static/images/email-course.jpg',
            'category': 'Writing'
        },
        {
            'title': 'English Job Interview Preparation',
            'description': 'Prepare for English job interviews with practice questions, answers, and professional communication skills.',
            'level': 'Intermediate',
            'duration': '5 weeks',
            'image': '/static/images/interview-course.jpg',
            'category': 'Professional English'
        },
        {
            'title': 'English Grammar for Advanced Learners',
            'description': 'Advanced grammar topics including complex structures, conditional sentences, and sophisticated usage.',
            'level': 'Advanced',
            'duration': '10 weeks',
            'image': '/static/images/advanced-grammar-course.jpg',
            'category': 'Grammar'
        }
    ]

    course_ids = []
    for i, course_data in enumerate(courses_data):
        # Assign instructor randomly
        instructor_name, instructor_id = random.choice(educators)

        course_data.update({
            'instructor': instructor_name,
            'instructor_id': instructor_id,
            'status': random.choice(['published', 'published', 'published', 'draft']),  # 75% published
            'students_enrolled': random.randint(15, 85),
            'rating': round(random.uniform(4.2, 5.0), 1),
            'created_at': datetime.now() - timedelta(days=random.randint(1, 365))
        })

        course_id = CourseModel.create_course(course_data)
        course_ids.append(course_id)
        print(f"  ✓ Created course {i + 1}: {course_data['title']}")

    return course_ids


def seed_20_modules(course_ids):
    """Seed 20 modules distributed across courses"""
    print("📖 Seeding 20 modules...")

    modules_data = [
        # Grammar course modules
        {
            'course_index': 0,
            'title': 'Parts of Speech Overview',
            'content': 'Introduction to nouns, verbs, adjectives, adverbs, pronouns, prepositions, conjunctions, and interjections.',
            'type': 'lesson',
            'order': 1,
            'duration': '45 minutes'
        },
        {
            'course_index': 0,
            'title': 'Grammar Fundamentals Quiz',
            'content': 'Test your understanding of basic parts of speech and their functions.',
            'type': 'quiz',
            'order': 2,
            'duration': '20 minutes'
        },
        # Business English modules
        {
            'course_index': 1,
            'title': 'Professional Email Writing',
            'content': 'Learn the structure and tone of professional emails including greetings, body, and closings.',
            'type': 'lesson',
            'order': 1,
            'duration': '40 minutes'
        },
        {
            'course_index': 1,
            'title': 'Business Communication Assessment',
            'content': 'Evaluate your professional communication skills through practical scenarios.',
            'type': 'quiz',
            'order': 2,
            'duration': '25 minutes'
        },
        # IELTS modules
        {
            'course_index': 2,
            'title': 'IELTS Writing Task 1 Strategies',
            'content': 'Learn how to describe charts, graphs, diagrams, and processes for IELTS Writing Task 1.',
            'type': 'lesson',
            'order': 1,
            'duration': '60 minutes'
        },
        {
            'course_index': 2,
            'title': 'IELTS Practice Test',
            'content': 'Complete IELTS-style questions to assess your preparation level.',
            'type': 'quiz',
            'order': 2,
            'duration': '30 minutes'
        },
        # Pronunciation modules
        {
            'course_index': 3,
            'title': 'English Phonetic Sounds',
            'content': 'Master the 44 phonetic sounds of English with audio examples and practice exercises.',
            'type': 'lesson',
            'order': 1,
            'duration': '50 minutes'
        },
        {
            'course_index': 3,
            'title': 'Pronunciation Skills Check',
            'content': 'Test your ability to identify and produce correct English sounds.',
            'type': 'quiz',
            'order': 2,
            'duration': '25 minutes'
        },
        # Academic Writing modules
        {
            'course_index': 4,
            'title': 'Essay Structure and Organization',
            'content': 'Learn how to structure academic essays with introduction, body paragraphs, and conclusion.',
            'type': 'lesson',
            'order': 1,
            'duration': '55 minutes'
        },
        {
            'course_index': 4,
            'title': 'Academic Writing Skills Test',
            'content': 'Assess your understanding of academic writing principles and techniques.',
            'type': 'quiz',
            'order': 2,
            'duration': '35 minutes'
        },
        # Conversation modules
        {
            'course_index': 5,
            'title': 'Basic Conversation Starters',
            'content': 'Learn common phrases and questions for starting conversations in English.',
            'type': 'lesson',
            'order': 1,
            'duration': '35 minutes'
        },
        {
            'course_index': 5,
            'title': 'Conversation Skills Assessment',
            'content': 'Practice conversation scenarios and test your speaking confidence.',
            'type': 'quiz',
            'order': 2,
            'duration': '20 minutes'
        },
        # Vocabulary modules
        {
            'course_index': 6,
            'title': 'Advanced Vocabulary Building',
            'content': 'Learn strategies for expanding vocabulary and understanding word relationships.',
            'type': 'lesson',
            'order': 1,
            'duration': '45 minutes'
        },
        {
            'course_index': 6,
            'title': 'Advanced Vocabulary Quiz',
            'content': 'Test your knowledge of advanced English vocabulary and usage.',
            'type': 'quiz',
            'order': 2,
            'duration': '30 minutes'
        },
        # Reading modules
        {
            'course_index': 7,
            'title': 'Reading Comprehension Strategies',
            'content': 'Learn effective techniques for understanding and analyzing different types of texts.',
            'type': 'lesson',
            'order': 1,
            'duration': '40 minutes'
        },
        {
            'course_index': 7,
            'title': 'Reading Skills Evaluation',
            'content': 'Test your reading comprehension with various text types and question formats.',
            'type': 'quiz',
            'order': 2,
            'duration': '35 minutes'
        },
        # TOEFL modules
        {
            'course_index': 8,
            'title': 'TOEFL Test Format and Strategies',
            'content': 'Understanding the TOEFL test structure and effective test-taking strategies.',
            'type': 'lesson',
            'order': 1,
            'duration': '50 minutes'
        },
        {
            'course_index': 8,
            'title': 'TOEFL Practice Assessment',
            'content': 'Practice with authentic TOEFL-style questions across all four skills.',
            'type': 'quiz',
            'order': 2,
            'duration': '40 minutes'
        },
        # Listening modules
        {
            'course_index': 9,
            'title': 'Active Listening Techniques',
            'content': 'Develop skills for effective listening comprehension in various contexts.',
            'type': 'lesson',
            'order': 1,
            'duration': '35 minutes'
        },
        {
            'course_index': 9,
            'title': 'Listening Comprehension Test',
            'content': 'Evaluate your listening skills with audio materials and comprehension questions.',
            'type': 'quiz',
            'order': 2,
            'duration': '25 minutes'
        }
    ]

    module_ids = []
    for module_data in modules_data:
        if module_data['course_index'] < len(course_ids):
            course_id = course_ids[module_data['course_index']]

            module_info = {
                'course_id': course_id,
                'title': module_data['title'],
                'content': module_data['content'],
                'type': module_data['type'],
                'order': module_data['order'],
                'duration': module_data['duration'],
                'created_at': datetime.now() - timedelta(days=random.randint(1, 90))
            }

            module_id = ModuleModel.create_module(module_info)
            module_ids.append(module_id)
            print(f"  ✓ Created module {len(module_ids)}: {module_data['title']}")

    return module_ids


def seed_20_assessments(module_ids):
    """Seed 20 comprehensive quiz assessments"""
    print("📊 Seeding 20 assessments...")

    # Sample question pools for different topics
    question_pools = {
        'grammar': [
            {
                "question": "What part of speech is the word 'beautiful'?",
                "options": ["Noun", "Verb", "Adjective", "Adverb"],
                "correct_answer": 2,
                "explanation": "Beautiful is an adjective as it describes or modifies a noun."
            },
            {
                "question": "Identify the verb in: 'She runs quickly to school.'",
                "options": ["She", "runs", "quickly", "school"],
                "correct_answer": 1,
                "explanation": "Runs is the action word (verb) in this sentence."
            },
            {
                "question": "Which sentence uses correct subject-verb agreement?",
                "options": ["The dogs runs fast", "The dog run fast", "The dogs run fast", "The dog are running"],
                "correct_answer": 2,
                "explanation": "Dogs (plural subject) requires run (plural verb)."
            },
            {
                "question": "What is the past tense of 'go'?",
                "options": ["goed", "went", "gone", "going"],
                "correct_answer": 1,
                "explanation": "Went is the irregular past tense form of go."
            },
            {
                "question": "Choose the correct article: '_____ apple a day keeps the doctor away.'",
                "options": ["A", "An", "The", "No article needed"],
                "correct_answer": 1,
                "explanation": "An is used before words that begin with a vowel sound."
            }
        ],
        'business': [
            {
                "question": "What is the most formal way to start a business email?",
                "options": ["Hi there", "Dear Sir/Madam", "Hey", "Hello"],
                "correct_answer": 1,
                "explanation": "Dear Sir/Madam is the most formal greeting in business correspondence."
            },
            {
                "question": "Which phrase is best for ending a formal business letter?",
                "options": ["Bye", "Yours sincerely", "See you later", "Cheers"],
                "correct_answer": 1,
                "explanation": "Yours sincerely is the appropriate formal closing for business letters."
            },
            {
                "question": "What does 'FYI' stand for in business communication?",
                "options": ["For Your Information", "Find Your Interest", "Follow Your Instinct", "Fix Your Issue"],
                "correct_answer": 0,
                "explanation": "FYI is a common abbreviation meaning For Your Information."
            },
            {
                "question": "Which is the most professional way to ask for a meeting?",
                "options": ["Let's meet up", "I would like to schedule a meeting", "Wanna meet?", "Meet me tomorrow"],
                "correct_answer": 1,
                "explanation": "This is the most formal and professional way to request a meeting."
            },
            {
                "question": "What does 'CC' mean in email?",
                "options": ["Carbon Copy", "Clear Copy", "Complete Copy", "Correct Copy"],
                "correct_answer": 0,
                "explanation": "CC stands for Carbon Copy, used to send copies to additional recipients."
            }
        ],
        'ielts': [
            {
                "question": "In IELTS Writing Task 1, what should you write about?",
                "options": ["Your opinion", "A graph or chart description", "A story", "Your personal experience"],
                "correct_answer": 1,
                "explanation": "IELTS Writing Task 1 requires describing visual information like graphs, charts, or diagrams."
            },
            {
                "question": "How long is the IELTS Speaking test?",
                "options": ["5-10 minutes", "11-14 minutes", "15-20 minutes", "25-30 minutes"],
                "correct_answer": 1,
                "explanation": "The IELTS Speaking test typically lasts 11-14 minutes."
            },
            {
                "question": "What is the highest band score in IELTS?",
                "options": ["8", "9", "10", "100"],
                "correct_answer": 1,
                "explanation": "The IELTS band scores range from 0 to 9, with 9 being the highest."
            },
            {
                "question": "What is the minimum word count for IELTS Writing Task 2?",
                "options": ["150 words", "200 words", "250 words", "300 words"],
                "correct_answer": 2,
                "explanation": "IELTS Writing Task 2 requires a minimum of 250 words."
            },
            {
                "question": "Which section comes first in the IELTS test?",
                "options": ["Speaking", "Writing", "Reading", "Listening"],
                "correct_answer": 3,
                "explanation": "The IELTS test typically starts with the Listening section."
            }
        ],
        'general': [
            {
                "question": "Which of the following is a synonym for 'happy'?",
                "options": ["Sad", "Joyful", "Angry", "Tired"],
                "correct_answer": 1,
                "explanation": "Joyful is a synonym for happy, meaning feeling pleasure or contentment."
            },
            {
                "question": "What does the idiom 'break a leg' mean?",
                "options": ["To injure yourself", "Good luck", "To run fast", "To dance"],
                "correct_answer": 1,
                "explanation": "Break a leg is an idiom meaning good luck, commonly used in theater."
            },
            {
                "question": "Which sentence is grammatically correct?",
                "options": ["I have went to the store", "I have gone to the store", "I have go to the store",
                            "I have going to the store"],
                "correct_answer": 1,
                "explanation": "I have gone is the correct present perfect form using the past participle."
            },
            {
                "question": "What is the opposite of 'hot'?",
                "options": ["Warm", "Cool", "Cold", "Freezing"],
                "correct_answer": 2,
                "explanation": "Cold is the direct opposite of hot in terms of temperature."
            },
            {
                "question": "Which word means 'very large'?",
                "options": ["Tiny", "Small", "Huge", "Medium"],
                "correct_answer": 2,
                "explanation": "Huge means very large or enormous in size."
            }
        ]
    }

    assessment_topics = [
        ('grammar', 'Grammar Fundamentals Quiz', 20, 70),
        ('business', 'Business Communication Assessment', 25, 75),
        ('ielts', 'IELTS Practice Test', 30, 70),
        ('general', 'Pronunciation Skills Check', 25, 70),
        ('general', 'Academic Writing Skills Test', 35, 75),
        ('general', 'Conversation Skills Assessment', 20, 65),
        ('general', 'Advanced Vocabulary Quiz', 30, 70),
        ('general', 'Reading Skills Evaluation', 35, 70),
        ('general', 'TOEFL Practice Assessment', 40, 75),
        ('general', 'Listening Comprehension Test', 25, 65),
        ('grammar', 'Advanced Grammar Assessment', 30, 80),
        ('business', 'Professional English Evaluation', 25, 70),
        ('ielts', 'IELTS Writing Practice', 45, 70),
        ('general', 'Phonetics and Pronunciation Quiz', 20, 65),
        ('general', 'Essay Writing Assessment', 40, 75),
        ('general', 'Speaking Confidence Test', 15, 60),
        ('general', 'Vocabulary Mastery Quiz', 25, 70),
        ('general', 'Comprehension Skills Test', 30, 70),
        ('general', 'English Proficiency Assessment', 50, 80),
        ('general', 'Communication Skills Evaluation', 30, 70)
    ]

    quiz_ids = []
    for i, (topic, title, time_limit, passing_score) in enumerate(assessment_topics):
        if i < len(module_ids):
            module_id = module_ids[i]

            # Get module to determine course_id
            module = ModuleModel.find_module_by_id(module_id)
            if module:
                # Select questions from the appropriate pool
                question_pool = question_pools.get(topic, question_pools['general'])

                # Generate 5-10 questions for each quiz
                num_questions = random.randint(5, min(10, len(question_pool)))
                selected_questions = random.sample(question_pool, num_questions)

                quiz_data = {
                    'module_id': module_id,
                    'course_id': module['course_id'],
                    'title': title,
                    'questions': selected_questions,
                    'time_limit': time_limit,
                    'passing_score': passing_score,
                    'total_questions': len(selected_questions),
                    'total_points': len(selected_questions) * 10,
                    'instructions': f'Answer all {len(selected_questions)} questions to the best of your ability. You have {time_limit} minutes to complete this quiz.',
                    'quiz_type': 'multiple_choice',
                    'created_at': datetime.now() - timedelta(days=random.randint(1, 60))
                }

                quiz_id = QuizModel.create_quiz(quiz_data)
                quiz_ids.append(quiz_id)
                print(f"  ✓ Created assessment {i + 1}: {title} with {len(selected_questions)} questions")

    return quiz_ids


def seed_enrollments(user_ids, course_ids):
    """Seed student enrollments"""
    print("📝 Seeding enrollments...")

    student_id = user_ids.get('student@headway.lk')
    if not student_id:
        print("  ⚠️ No student found, skipping enrollments")
        return

    # Enroll student in first 5 courses with varying progress
    for i in range(min(5, len(course_ids))):
        enrollment_data = {
            'user_id': student_id,
            'course_id': course_ids[i],
            'progress': random.randint(20, 95),
            'completed_modules': [],
            'grade': random.choice(['A', 'A-', 'B+', 'B', 'B-', None])
        }

        EnrollmentModel.create_enrollment(enrollment_data)
        print(f"  ✓ Created enrollment {i + 1}")


def seed_quiz_results(user_ids, quiz_ids, course_ids):
    """Seed quiz results"""
    print("🎯 Seeding quiz results...")

    student_id = user_ids.get('student@headway.lk')
    if not student_id or not quiz_ids:
        print("  ⚠️ No student or quizzes found, skipping quiz results")
        return

    # Create results for first 10 quizzes
    for i in range(min(10, len(quiz_ids))):
        quiz_id = quiz_ids[i]
        quiz = QuizModel.find_quiz_by_id(quiz_id)

        if quiz:
            # Generate realistic score
            correct_answers = random.randint(3, len(quiz['questions']))
            total_questions = len(quiz['questions'])
            score_percentage = (correct_answers / total_questions) * 100

            # Generate question results
            question_results = []
            for j in range(total_questions):
                is_correct = j < correct_answers
                question_results.append({
                    'question_index': j,
                    'user_answer': quiz['questions'][j]['correct_answer'] if is_correct else random.randint(0, 3),
                    'correct_answer': quiz['questions'][j]['correct_answer'],
                    'is_correct': is_correct
                })

            # Determine grade
            if score_percentage >= 95:
                grade = 'A+'
            elif score_percentage >= 90:
                grade = 'A'
            elif score_percentage >= 85:
                grade = 'A-'
            elif score_percentage >= 80:
                grade = 'B+'
            elif score_percentage >= 75:
                grade = 'B'
            elif score_percentage >= 70:
                grade = 'B-'
            elif score_percentage >= 65:
                grade = 'C+'
            elif score_percentage >= 60:
                grade = 'C'
            else:
                grade = 'F'

            result_data = {
                'user_id': student_id,
                'quiz_id': quiz_id,
                'module_id': quiz['module_id'],
                'course_id': quiz['course_id'],
                # FIX: Convert integer keys to strings
                'answers': {str(j): result['user_answer'] for j, result in enumerate(question_results)},
                'question_results': question_results,
                'score': correct_answers,
                'total_questions': total_questions,
                'score_percentage': round(score_percentage, 2),
                'grade': grade,
                'time_taken': random.randint(300, quiz.get('time_limit', 20) * 60),
                'completed_at': datetime.now() - timedelta(days=random.randint(1, 30))
            }

            QuizResultModel.create_result(result_data)
            print(f"  ✓ Created quiz result {i + 1}: {score_percentage:.1f}%")


def seed_badges():
    """Seed achievement badges"""
    print("🏆 Seeding badges...")

    badges_data = [
        {
            'name': 'First Steps',
            'description': 'Complete your first lesson',
            'icon': '🌟',
            'color': 'bg-blue-100',
            'requirements': {'lessons_completed': 1}
        },
        {
            'name': 'Quiz Master',
            'description': 'Score 90% or higher on a quiz',
            'icon': '🧠',
            'color': 'bg-purple-100',
            'requirements': {'quiz_score': 90}
        },
        {
            'name': 'Dedicated Learner',
            'description': 'Complete 5 lessons',
            'icon': '📚',
            'color': 'bg-green-100',
            'requirements': {'lessons_completed': 5}
        },
        {
            'name': 'Grammar Expert',
            'description': 'Complete the Grammar Fundamentals course',
            'icon': '✍️',
            'color': 'bg-yellow-100',
            'requirements': {'course_completed': 'English Grammar Fundamentals'}
        }
    ]

    for badge_data in badges_data:
        BadgeModel.create_badge(badge_data)
        print(f"  ✓ Created badge: {badge_data['name']}")


def seed_analytics():
    """Seed analytics data"""
    print("📈 Seeding analytics...")

    AnalyticsModel.update_system_stats()
    print("  ✓ Created system analytics")


if __name__ == '__main__':
    try:
        comprehensive_seed_database()
    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        import traceback

        traceback.print_exc()
    finally:
        mongo_db.close_connection()