from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os

def main():
<<<<<<< HEAD
    # Database connection - Update with your credentials
    DATABASE_URL = "postgresql://nuraiaripbay:050921@localhost:5432/caregiver_platform"
=======
    # You can update your credentials here
    DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/caregiver_platform"
>>>>>>> 5c2d7286488f87a11aeaafed19c20ef22e1aec10
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    print("=== CSCI 341 Assignment 3 - Caregiver Platform ===\n")
    
    try:
        # 3.Updating SQL Statements
        print("3. Update SQL Statements")
        print("3.1 Updating Arman Armanov's phone number")
        update_phone = text("""
            UPDATE "user" 
            SET phone_number = '+77773414141' 
            WHERE given_name = 'Arman' AND surname = 'Armanov'
        """)
        session.execute(update_phone)
        session.commit()
        print("Phone number updated successfully")
        
        print("\n3.2 Updating caregiver hourly rates")
        update_rates = text("""
            UPDATE caregiver 
            SET hourly_rate = 
                CASE 
                    WHEN hourly_rate < 10 THEN hourly_rate + 0.3
                    ELSE hourly_rate * 1.10
                END
        """)
        session.execute(update_rates)
        session.commit()
        print("Hourly rates updated successfully")
        
        # 4.Deleting SQL Statements
        print("\n4. Delete SQL Statements")
        print("4.1 Deleting jobs posted by Amina Aminova")
        delete_jobs = text("""
            DELETE FROM job 
            WHERE member_user_id IN (
                SELECT member_user_id FROM member 
                WHERE member_user_id IN (
                    SELECT user_id FROM "user" 
                    WHERE given_name = 'Amina' AND surname = 'Aminova'
                )
            )
        """)
        result = session.execute(delete_jobs)
        session.commit()
        print(f"Deleted {result.rowcount} job(s) posted by Amina Aminova")
        
        
        print("\n4.2 Deleting all members who live on Kabanbay Batyr street")
        
        # 2.Deleting appointments referencing these members
        delete_appointments = text("""
            DELETE FROM appointment 
            WHERE member_user_id IN (
                SELECT member_user_id FROM address 
                WHERE street = 'Kabanbay Batyr'
            )
        """)
        session.execute(delete_appointments)
        
        # 3.Deleting job applications for jobs posted by these members
        delete_job_apps = text("""
            DELETE FROM job_application 
            WHERE job_id IN (
                SELECT job_id FROM job 
                WHERE member_user_id IN (
                    SELECT member_user_id FROM address 
                    WHERE street = 'Kabanbay Batyr'
                )
            )
        """)
        session.execute(delete_job_apps)
        
        # 4. Deleting jobs posted by these members
        delete_jobs = text("""
            DELETE FROM job 
            WHERE member_user_id IN (
                SELECT member_user_id FROM address 
                WHERE street = 'Kabanbay Batyr'
            )
        """)
        session.execute(delete_jobs)
        
        # 5. Deleting users who live on this street
        delete_members = text("""
            DELETE FROM "user" 
            WHERE user_id IN (
                SELECT member_user_id FROM address 
                WHERE street = 'Kabanbay Batyr'
            )
        """)
        result = session.execute(delete_members)
        session.commit()
        print(f"Deleted {result.rowcount} member(s) living on Kabanbay Batyr street")
        
        
        # 5.Simple queries
        print("\n5. SIMPLE QUERIES")
        
        print("\n5.1 Caregiver and member names for accepted appointments:")
        query_5_1 = text("""
            SELECT 
                u_c.given_name as caregiver_name, 
                u_c.surname as caregiver_surname,
                u_m.given_name as member_name, 
                u_m.surname as member_surname
            FROM appointment a
            JOIN caregiver c ON a.caregiver_user_id = c.caregiver_user_id
            JOIN "user" u_c ON c.caregiver_user_id = u_c.user_id
            JOIN member m ON a.member_user_id = m.member_user_id
            JOIN "user" u_m ON m.member_user_id = u_m.user_id
            WHERE a.status = 'accepted'
        """)
        result_5_1 = session.execute(query_5_1)
        for row in result_5_1:
            print(f"Caregiver: {row.caregiver_name} {row.caregiver_surname}, Member: {row.member_name} {row.member_surname}")
        
        
        print("\n5.2 Job IDs that contain 'soft-spoken' in their other requirements:")
        query_5_2 = text("""
            SELECT job_id FROM job 
            WHERE other_requirements ILIKE '%soft-spoken%'
        """)
        result_5_2 = session.execute(query_5_2)
        for row in result_5_2:
            print(f"Job ID: {row.job_id}")
        
        
        print("\n5.3 Work hours of all babysitter positions:")
        query_5_3 = text("""
            SELECT a.work_hours 
            FROM appointment a
            JOIN caregiver c ON a.caregiver_user_id = c.caregiver_user_id
            WHERE c.caregiving_type = 'Babysitter'
        """)
        result_5_3 = session.execute(query_5_3)
        for row in result_5_3:
            print(f"Hours: {row.work_hours}")
        
        
        print("\n5.4 Members looking for Elderly Care in Astana with 'No pets' rule:")
        query_5_4 = text("""
            SELECT u.given_name, u.surname 
            FROM "user" u
            JOIN member m ON u.user_id = m.member_user_id
            WHERE u.city = 'Astana' 
            AND m.house_rules ILIKE '%no pets%'
            AND m.member_user_id IN (
                SELECT member_user_id FROM job 
                WHERE required_caregiving_type = 'Elderly Care'
            )
        """)
        result_5_4 = session.execute(query_5_4)
        for row in result_5_4:
            print(f"Member: {row.given_name} {row.surname}")
        
        
        # 6.Complex queries
        print("\n6. COMPLEX QUERIES")
        
        print("\n6.1 Count the number of applicants for each job:")
        query_6_1 = text("""
            SELECT j.job_id, COUNT(ja.caregiver_user_id) as applicant_count
            FROM job j
            LEFT JOIN job_application ja ON j.job_id = ja.job_id
            GROUP BY j.job_id
            ORDER BY j.job_id
        """)
        result_6_1 = session.execute(query_6_1)
        for row in result_6_1:
            print(f"Job ID: {row.job_id}, Applicants: {row.applicant_count}")
        
        
        print("\n6.2 Total hours spent by caregivers for all accepted appointments:")
        query_6_2 = text("""
            SELECT SUM(work_hours) as total_hours
            FROM appointment
            WHERE status = 'accepted'
        """)
        result_6_2 = session.execute(query_6_2)
        total_hours = result_6_2.scalar()
        print(f"Total Hours: {total_hours}")
        
        
        print("\n6.3 Average pay of caregivers based on accepted appointments:")
        query_6_3 = text("""
            SELECT AVG(c.hourly_rate * a.work_hours) as avg_pay
            FROM appointment a
            JOIN caregiver c ON a.caregiver_user_id = c.caregiver_user_id
            WHERE a.status = 'accepted'
        """)
        result_6_3 = session.execute(query_6_3)
        avg_pay = result_6_3.scalar()
        print(f"Average Pay: ${avg_pay:.2f}")
        
        
        print("\n6.4 Caregivers who earn above average based on accepted appointments:")
        query_6_4 = text("""
            SELECT u.given_name, u.surname, c.hourly_rate * a.work_hours as total_earnings
            FROM appointment a
            JOIN caregiver c ON a.caregiver_user_id = c.caregiver_user_id
            JOIN "user" u ON c.caregiver_user_id = u.user_id
            WHERE a.status = 'accepted'
            AND c.hourly_rate * a.work_hours > (
                SELECT AVG(c2.hourly_rate * a2.work_hours)
                FROM appointment a2
                JOIN caregiver c2 ON a2.caregiver_user_id = c2.caregiver_user_id
                WHERE a2.status = 'accepted'
            )
        """)
        result_6_4 = session.execute(query_6_4)
        for row in result_6_4:
            print(f"Caregiver: {row.given_name} {row.surname}, Earnings: ${row.total_earnings:.2f}")
        
        
        # 7. Query with derived attribute
        print("\n7. QUERY WITH DERIVED ATTRIBUTE")
        query_7 = text("""
            SELECT 
                u.given_name, 
                u.surname,
                a.work_hours,
                c.hourly_rate,
                (c.hourly_rate * a.work_hours) as total_cost
            FROM appointment a
            JOIN caregiver c ON a.caregiver_user_id = c.caregiver_user_id
            JOIN "user" u ON c.caregiver_user_id = u.user_id
            WHERE a.status = 'accepted'
        """)
        result_7 = session.execute(query_7)
        total_overall_cost = 0
        print("Total cost for each accepted appointment:")
        for row in result_7:
            print(f"{row.given_name} {row.surname}: {row.work_hours}h × ${row.hourly_rate}/h = ${row.total_cost:.2f}")
            total_overall_cost += float(row.total_cost)
        print(f"Overall Total Cost: ${total_overall_cost:.2f}")
        
        
        # 8.View operation
        print("\n8. VIEW OPERATION")
        print("Creating view: job_application_view")
        
        create_view = text("""
            CREATE OR REPLACE VIEW job_application_view AS
            SELECT 
                j.job_id,
                u_m.given_name as member_name,
                u_m.surname as member_surname,
                u_c.given_name as caregiver_name,
                u_c.surname as caregiver_surname,
                j.required_caregiving_type,
                ja.date_applied
            FROM job_application ja
            JOIN job j ON ja.job_id = j.job_id
            JOIN member m ON j.member_user_id = m.member_user_id
            JOIN "user" u_m ON m.member_user_id = u_m.user_id
            JOIN caregiver c ON ja.caregiver_user_id = c.caregiver_user_id
            JOIN "user" u_c ON c.caregiver_user_id = u_c.user_id
        """)
        session.execute(create_view)
        session.commit()
        
        query_view = text("SELECT * FROM job_application_view ORDER BY job_id")
        result_view = session.execute(query_view)
        
        print("Job Applications View Results:")
        for row in result_view:
            print(f"Job {row.job_id}: {row.member_name} {row.member_surname} <- {row.caregiver_name} {row.caregiver_surname} ({row.required_caregiving_type}) - Applied: {row.date_applied}")
        
        print("\nAll queries executed successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    main()