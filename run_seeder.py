# run_seeder.py - Simple script to run the database seeder
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from seed_data import comprehensive_seed_database

if __name__ == '__main__':
    print("🚀 Starting database seeding process...")
    try:
        comprehensive_seed_database()
        print("🎉 Database seeding completed successfully!")
        print("\n📋 Summary:")
        print("   ✅ 20 Courses created")
        print("   ✅ 20 Modules created")
        print("   ✅ 20 Assessments created")
        print("   ✅ Sample enrollments and quiz results")
        print("   ✅ User accounts with demo credentials")
        print("\n🔑 Demo Login Credentials:")
        print("   Student: student@headway.lk / student123")
        print("   Teacher: teacher@headway.lk / teacher123")
        print("   Admin: admin@headway.lk / admin123")
        print("   Content Manager: content@headway.lk / content123")
        print("   System Admin: sysadmin@headway.lk / sysadmin123")

    except Exception as e:
        print(f"❌ Error during seeding: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)