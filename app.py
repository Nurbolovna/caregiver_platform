"""
Main Flask application for the Online Caregivers Platform.
Implements CRUD operations for all database tables.
"""
from flask import Flask, render_template, request, redirect, url_for, flash
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, date, time
import os
import traceback

# Try to load .env file if python-dotenv is installed
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, skip

from config import DATABASE_URL

# Debug: Display actual connection string (password masked)
if DATABASE_URL:
    if '@' in DATABASE_URL:
        parts = DATABASE_URL.split('@')
        if '://' in parts[0] and ':' in parts[0].split('://')[1]:
            protocol_user = parts[0].split('://')
            user_pass = protocol_user[1].split(':')
            print(f"Using DATABASE_URL: {protocol_user[0]}://{user_pass[0]}:****@{parts[1]}")
from models import Base, User, Caregiver, Member, Address, Job, JobApplication, Appointment
from flask import abort

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Create database engine and session with error handling
try:
    engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
    Session = sessionmaker(bind=engine)
    
    # Test connection
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    # Mask password in log output
    if DATABASE_URL and '@' in DATABASE_URL:
        db_info = DATABASE_URL.split('@')[1]
        print(f"✓ Database connection successful: {db_info}")
    else:
        print(f"✓ Database connection successful")
except Exception as e:
    print(f"✗ Database connection error: {e}")
    if DATABASE_URL:
        # Mask password in error output
        if '@' in DATABASE_URL:
            parts = DATABASE_URL.split('@')
            if '://' in parts[0] and ':' in parts[0].split('://')[1]:
                protocol_user = parts[0].split('://')
                user_pass = protocol_user[1].split(':')
                masked_url = f"{protocol_user[0]}://{user_pass[0]}:****@{parts[1]}"
                print(f"  DATABASE_URL: {masked_url}")
            else:
                print(f"  DATABASE_URL: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'configured'}")
        else:
            print(f"  DATABASE_URL: configured")
    else:
        print(f"  DATABASE_URL: not set")
    
    # Provide helpful troubleshooting
    print("\nTroubleshooting:")
    print("  1. Check if database service is running: brew services list | grep postgresql")
    print("  2. Check if database user exists: psql -U nazerke -l")
    print("  3. Check if port is correct (should be 5433)")
    print("  4. Check if password is correct")
    print("  5. If using environment variable, check: echo $DATABASE_URL")
    # Don't raise here - let Flask handle it with error handler


def get_session():
    """Create a new database session"""
    try:
        return Session()
    except Exception as e:
        raise SQLAlchemyError(f"Failed to create database session: {e}")


def first_or_404(query):
    """Helper function to get first result or return 404"""
    result = query.first()
    if result is None:
        abort(404)
    return result


# ==================== HOME PAGE ====================
@app.route('/')
def index():
    """Home page with links to all entities"""
    return render_template('index.html')


# ==================== USER ROUTES ====================
@app.route('/users')
def user_list():
    """List all users"""
    session = get_session()
    try:
        users = session.query(User).all()
        return render_template('user_list.html', users=users)
    except SQLAlchemyError as e:
        flash(f'Database error: {str(e)}', 'error')
        return render_template('user_list.html', users=[])
    except Exception as e:
        flash(f'Error loading users: {str(e)}', 'error')
        return render_template('user_list.html', users=[])
    finally:
        session.close()


@app.route('/users/create', methods=['GET', 'POST'])
def user_create():
    """Create a new user"""
    if request.method == 'POST':
        session = get_session()
        try:
            try:
                user = User(
                    email=request.form['email'],
                    given_name=request.form['given_name'],
                    surname=request.form['surname'],
                    city=request.form.get('city', ''),
                    phone_number=request.form.get('phone_number', ''),
                    profile_description=request.form.get('profile_description', ''),
                    password=request.form['password']
                )
                session.add(user)
                session.commit()
                flash('User created successfully!', 'success')
                return redirect(url_for('user_list'))
            except ValueError as e:
                session.rollback()
                flash(f'Invalid input: {str(e)}', 'error')
            except KeyError as e:
                session.rollback()
                flash(f'Missing required field: {str(e)}', 'error')
            except SQLAlchemyError as e:
                session.rollback()
                error_msg = str(e.orig) if hasattr(e, 'orig') else str(e)
                if 'duplicate' in error_msg.lower() or 'unique' in error_msg.lower():
                    flash('This email address is already registered. Please use a different email.', 'error')
                else:
                    flash(f'Database error: {error_msg}', 'error')
            except Exception as e:
                session.rollback()
                flash(f'Error creating user: {str(e)}', 'error')
        finally:
            session.close()
    
    return render_template('user_form.html', user=None)


@app.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
def user_edit(user_id):
    """Edit an existing user"""
    session = get_session()
    try:
        user = first_or_404(session.query(User).filter_by(user_id=user_id))
        
        if request.method == 'POST':
            user.email = request.form['email']
            user.given_name = request.form['given_name']
            user.surname = request.form['surname']
            user.city = request.form.get('city', '')
            user.phone_number = request.form.get('phone_number', '')
            user.profile_description = request.form.get('profile_description', '')
            user.password = request.form['password']
            session.commit()
            flash('User updated successfully!', 'success')
            return redirect(url_for('user_list'))
        
        return render_template('user_form.html', user=user)
    finally:
        session.close()


@app.route('/users/<int:user_id>/delete', methods=['POST'])
def user_delete(user_id):
    """Delete a user"""
    session = get_session()
    try:
        user = first_or_404(session.query(User).filter_by(user_id=user_id))
        session.delete(user)
        session.commit()
        flash('User deleted successfully!', 'success')
    except Exception as e:
        session.rollback()
        flash(f'Error deleting user: {str(e)}', 'error')
    finally:
        session.close()
    return redirect(url_for('user_list'))


# ==================== CAREGIVER ROUTES ====================
@app.route('/caregivers')
def caregiver_list():
    """List all caregivers with user information"""
    session = get_session()
    try:
        caregivers = session.query(Caregiver).join(User).all()
        return render_template('caregiver_list.html', caregivers=caregivers)
    finally:
        session.close()


@app.route('/caregivers/create', methods=['GET', 'POST'])
def caregiver_create():
    """Create a new caregiver"""
    session = get_session()
    try:
        if request.method == 'POST':
            try:
                gender_value = request.form.get('gender', '').strip()
                gender_value = gender_value if gender_value in ('M', 'F', 'O') else None
                
                caregiving_type = request.form.get('caregiving_type', '').strip()
                if not caregiving_type or caregiving_type not in ('Babysitter', 'Elderly Care', 'Playmate'):
                    flash('Invalid caregiving type. Must be one of: Babysitter, Elderly Care, Playmate', 'error')
                    users = session.query(User).all()
                    return render_template('caregiver_form.html', caregiver=None, users=users)
                
                hourly_rate = None
                if request.form.get('hourly_rate'):
                    try:
                        hourly_rate = float(request.form['hourly_rate'])
                        if hourly_rate < 0:
                            raise ValueError("Hourly rate cannot be negative")
                    except ValueError as e:
                        flash(f'Invalid hourly rate: {str(e)}', 'error')
                        users = session.query(User).all()
                        return render_template('caregiver_form.html', caregiver=None, users=users)
                
                caregiver = Caregiver(
                    caregiver_user_id=int(request.form['caregiver_user_id']),
                    photo=request.form.get('photo', '') or None,
                    gender=gender_value,
                    caregiving_type=caregiving_type,
                    hourly_rate=hourly_rate
                )
                session.add(caregiver)
                session.commit()
                flash('Caregiver created successfully!', 'success')
                return redirect(url_for('caregiver_list'))
            except ValueError as e:
                session.rollback()
                flash(f'Invalid input: {str(e)}', 'error')
                users = session.query(User).all()
                return render_template('caregiver_form.html', caregiver=None, users=users)
            except KeyError as e:
                session.rollback()
                flash(f'Missing required field: {str(e)}', 'error')
                users = session.query(User).all()
                return render_template('caregiver_form.html', caregiver=None, users=users)
            except SQLAlchemyError as e:
                session.rollback()
                error_msg = str(e.orig) if hasattr(e, 'orig') else str(e)
                if 'duplicate' in error_msg.lower() or 'unique' in error_msg.lower():
                    flash('This caregiver already exists. Please choose a different user.', 'error')
                elif 'check' in error_msg.lower() or 'constraint' in error_msg.lower():
                    flash('Invalid data: One or more fields violate database constraints. Please check your input.', 'error')
                elif 'foreign key' in error_msg.lower():
                    flash('Invalid user ID. The selected user does not exist.', 'error')
                else:
                    flash(f'Database error: {error_msg}', 'error')
                users = session.query(User).all()
                return render_template('caregiver_form.html', caregiver=None, users=users)
            except Exception as e:
                session.rollback()
                flash(f'Error creating caregiver: {str(e)}', 'error')
                users = session.query(User).all()
                return render_template('caregiver_form.html', caregiver=None, users=users)
        
        users = session.query(User).all()
        return render_template('caregiver_form.html', caregiver=None, users=users)
    finally:
        session.close()


@app.route('/caregivers/<int:caregiver_user_id>/edit', methods=['GET', 'POST'])
def caregiver_edit(caregiver_user_id):
    """Edit an existing caregiver"""
    session = get_session()
    try:
        caregiver = first_or_404(session.query(Caregiver).filter_by(caregiver_user_id=caregiver_user_id))
        
        if request.method == 'POST':
            caregiver.photo = request.form.get('photo', '') or None
            gender_value = request.form.get('gender', '').strip()
            caregiver.gender = gender_value if gender_value in ('M', 'F', 'O') else None
            
            caregiving_type = request.form.get('caregiving_type', '').strip()
            if not caregiving_type or caregiving_type not in ('Babysitter', 'Elderly Care', 'Playmate'):
                flash('Invalid caregiving type. Must be one of: Babysitter, Elderly Care, Playmate', 'error')
                users = session.query(User).all()
                return render_template('caregiver_form.html', caregiver=caregiver, users=users)
            caregiver.caregiving_type = caregiving_type
            
            caregiver.hourly_rate = float(request.form['hourly_rate']) if request.form.get('hourly_rate') else None
            session.commit()
            flash('Caregiver updated successfully!', 'success')
            return redirect(url_for('caregiver_list'))
        
        users = session.query(User).all()
        return render_template('caregiver_form.html', caregiver=caregiver, users=users)
    finally:
        session.close()


@app.route('/caregivers/<int:caregiver_user_id>/delete', methods=['POST'])
def caregiver_delete(caregiver_user_id):
    """Delete a caregiver"""
    session = get_session()
    try:
        caregiver = first_or_404(session.query(Caregiver).filter_by(caregiver_user_id=caregiver_user_id))
        session.delete(caregiver)
        session.commit()
        flash('Caregiver deleted successfully!', 'success')
    except Exception as e:
        session.rollback()
        flash(f'Error deleting caregiver: {str(e)}', 'error')
    finally:
        session.close()
    return redirect(url_for('caregiver_list'))


# ==================== MEMBER ROUTES ====================
@app.route('/members')
def member_list():
    """List all members with user information"""
    session = get_session()
    try:
        members = session.query(Member).join(User).all()
        return render_template('member_list.html', members=members)
    finally:
        session.close()


@app.route('/members/create', methods=['GET', 'POST'])
def member_create():
    """Create a new member"""
    session = get_session()
    try:
        if request.method == 'POST':
            try:
                member = Member(
                    member_user_id=int(request.form['member_user_id']),
                    house_rules=request.form.get('house_rules', ''),
                    dependent_description=request.form.get('dependent_description', '')
                )
                session.add(member)
                session.commit()
                flash('Member created successfully!', 'success')
                return redirect(url_for('member_list'))
            except ValueError as e:
                session.rollback()
                flash(f'Invalid input: {str(e)}', 'error')
                users = session.query(User).all()
                return render_template('member_form.html', member=None, users=users)
            except KeyError as e:
                session.rollback()
                flash(f'Missing required field: {str(e)}', 'error')
                users = session.query(User).all()
                return render_template('member_form.html', member=None, users=users)
            except SQLAlchemyError as e:
                session.rollback()
                error_msg = str(e.orig) if hasattr(e, 'orig') else str(e)
                if 'duplicate' in error_msg.lower() or 'unique' in error_msg.lower():
                    flash('This member already exists. Please choose a different user.', 'error')
                elif 'foreign key' in error_msg.lower():
                    flash('Invalid user ID. The selected user does not exist.', 'error')
                else:
                    flash(f'Database error: {error_msg}', 'error')
                users = session.query(User).all()
                return render_template('member_form.html', member=None, users=users)
            except Exception as e:
                session.rollback()
                flash(f'Error creating member: {str(e)}', 'error')
                users = session.query(User).all()
                return render_template('member_form.html', member=None, users=users)
        
        users = session.query(User).all()
        return render_template('member_form.html', member=None, users=users)
    finally:
        session.close()


@app.route('/members/<int:member_user_id>/edit', methods=['GET', 'POST'])
def member_edit(member_user_id):
    """Edit an existing member"""
    session = get_session()
    try:
        member = first_or_404(session.query(Member).filter_by(member_user_id=member_user_id))
        
        if request.method == 'POST':
            member.house_rules = request.form.get('house_rules', '')
            member.dependent_description = request.form.get('dependent_description', '')
            session.commit()
            flash('Member updated successfully!', 'success')
            return redirect(url_for('member_list'))
        
        users = session.query(User).all()
        return render_template('member_form.html', member=member, users=users)
    finally:
        session.close()


@app.route('/members/<int:member_user_id>/delete', methods=['POST'])
def member_delete(member_user_id):
    """Delete a member"""
    session = get_session()
    try:
        member = first_or_404(session.query(Member).filter_by(member_user_id=member_user_id))
        session.delete(member)
        session.commit()
        flash('Member deleted successfully!', 'success')
    except Exception as e:
        session.rollback()
        flash(f'Error deleting member: {str(e)}', 'error')
    finally:
        session.close()
    return redirect(url_for('member_list'))


# ==================== ADDRESS ROUTES ====================
@app.route('/addresses')
def address_list():
    """List all addresses with member information"""
    session = get_session()
    try:
        addresses = session.query(Address).join(Member).join(User).all()
        return render_template('address_list.html', addresses=addresses)
    finally:
        session.close()


@app.route('/addresses/create', methods=['GET', 'POST'])
def address_create():
    """Create a new address"""
    session = get_session()
    try:
        if request.method == 'POST':
            try:
                address = Address(
                    member_user_id=int(request.form['member_user_id']),
                    house_number=request.form.get('house_number', ''),
                    street=request.form.get('street', ''),
                    town=request.form.get('town', '')
                )
                session.add(address)
                session.commit()
                flash('Address created successfully!', 'success')
                return redirect(url_for('address_list'))
            except ValueError as e:
                session.rollback()
                flash(f'Invalid input: {str(e)}', 'error')
                members = session.query(Member).join(User).all()
                return render_template('address_form.html', address=None, members=members)
            except KeyError as e:
                session.rollback()
                flash(f'Missing required field: {str(e)}', 'error')
                members = session.query(Member).join(User).all()
                return render_template('address_form.html', address=None, members=members)
            except SQLAlchemyError as e:
                session.rollback()
                error_msg = str(e.orig) if hasattr(e, 'orig') else str(e)
                if 'duplicate' in error_msg.lower() or 'unique' in error_msg.lower():
                    flash('This address already exists for this member.', 'error')
                elif 'foreign key' in error_msg.lower():
                    flash('Invalid member ID. The selected member does not exist.', 'error')
                else:
                    flash(f'Database error: {error_msg}', 'error')
                members = session.query(Member).join(User).all()
                return render_template('address_form.html', address=None, members=members)
            except Exception as e:
                session.rollback()
                flash(f'Error creating address: {str(e)}', 'error')
                members = session.query(Member).join(User).all()
                return render_template('address_form.html', address=None, members=members)
        
        members = session.query(Member).join(User).all()
        return render_template('address_form.html', address=None, members=members)
    finally:
        session.close()


@app.route('/addresses/<int:member_user_id>/edit', methods=['GET', 'POST'])
def address_edit(member_user_id):
    """Edit an existing address"""
    session = get_session()
    try:
        address = first_or_404(session.query(Address).filter_by(member_user_id=member_user_id))
        
        if request.method == 'POST':
            address.house_number = request.form.get('house_number', '')
            address.street = request.form.get('street', '')
            address.town = request.form.get('town', '')
            session.commit()
            flash('Address updated successfully!', 'success')
            return redirect(url_for('address_list'))
        
        members = session.query(Member).join(User).all()
        return render_template('address_form.html', address=address, members=members)
    finally:
        session.close()


@app.route('/addresses/<int:member_user_id>/delete', methods=['POST'])
def address_delete(member_user_id):
    """Delete an address"""
    session = get_session()
    try:
        address = first_or_404(session.query(Address).filter_by(member_user_id=member_user_id))
        session.delete(address)
        session.commit()
        flash('Address deleted successfully!', 'success')
    except Exception as e:
        session.rollback()
        flash(f'Error deleting address: {str(e)}', 'error')
    finally:
        session.close()
    return redirect(url_for('address_list'))


# ==================== JOB ROUTES ====================
@app.route('/jobs')
def job_list():
    """List all jobs with member information"""
    session = get_session()
    try:
        jobs = session.query(Job).join(Member).join(User).all()
        return render_template('job_list.html', jobs=jobs)
    finally:
        session.close()


@app.route('/jobs/create', methods=['GET', 'POST'])
def job_create():
    """Create a new job"""
    session = get_session()
    try:
        if request.method == 'POST':
            try:
                date_posted = None
                date_posted_str = request.form.get('date_posted', '')
                if date_posted_str:
                    try:
                        date_posted = datetime.strptime(date_posted_str, '%Y-%m-%d').date()
                    except ValueError:
                        flash('Invalid date format. Please use YYYY-MM-DD format.', 'error')
                        members = session.query(Member).join(User).all()
                        return render_template('job_form.html', job=None, members=members)
                
                required_caregiving_type = request.form.get('required_caregiving_type', '').strip()
                if not required_caregiving_type or required_caregiving_type not in ('Babysitter', 'Elderly Care', 'Playmate'):
                    flash('Invalid caregiving type. Must be one of: Babysitter, Elderly Care, Playmate', 'error')
                    members = session.query(Member).join(User).all()
                    return render_template('job_form.html', job=None, members=members)
                
                job = Job(
                    member_user_id=int(request.form['member_user_id']),
                    required_caregiving_type=required_caregiving_type,
                    other_requirements=request.form.get('other_requirements', ''),
                    date_posted=date_posted
                )
                session.add(job)
                session.commit()
                flash('Job created successfully!', 'success')
                return redirect(url_for('job_list'))
            except ValueError as e:
                session.rollback()
                flash(f'Invalid input: {str(e)}', 'error')
                members = session.query(Member).join(User).all()
                return render_template('job_form.html', job=None, members=members)
            except KeyError as e:
                session.rollback()
                flash(f'Missing required field: {str(e)}', 'error')
                members = session.query(Member).join(User).all()
                return render_template('job_form.html', job=None, members=members)
            except SQLAlchemyError as e:
                session.rollback()
                error_msg = str(e.orig) if hasattr(e, 'orig') else str(e)
                if 'check' in error_msg.lower() or 'constraint' in error_msg.lower():
                    flash('Invalid data: One or more fields violate database constraints. Please check your input.', 'error')
                elif 'foreign key' in error_msg.lower():
                    flash('Invalid member ID. The selected member does not exist.', 'error')
                else:
                    flash(f'Database error: {error_msg}', 'error')
                members = session.query(Member).join(User).all()
                return render_template('job_form.html', job=None, members=members)
            except Exception as e:
                session.rollback()
                flash(f'Error creating job: {str(e)}', 'error')
                members = session.query(Member).join(User).all()
                return render_template('job_form.html', job=None, members=members)
        
        members = session.query(Member).join(User).all()
        return render_template('job_form.html', job=None, members=members)
    finally:
        session.close()


@app.route('/jobs/<int:job_id>/edit', methods=['GET', 'POST'])
def job_edit(job_id):
    """Edit an existing job"""
    session = get_session()
    try:
        job = first_or_404(session.query(Job).filter_by(job_id=job_id))
        
        if request.method == 'POST':
            job.member_user_id = int(request.form['member_user_id'])
            
            required_caregiving_type = request.form.get('required_caregiving_type', '').strip()
            if not required_caregiving_type or required_caregiving_type not in ('Babysitter', 'Elderly Care', 'Playmate'):
                flash('Invalid caregiving type. Must be one of: Babysitter, Elderly Care, Playmate', 'error')
                members = session.query(Member).join(User).all()
                return render_template('job_form.html', job=job, members=members)
            job.required_caregiving_type = required_caregiving_type
            
            job.other_requirements = request.form.get('other_requirements', '')
            date_posted_str = request.form.get('date_posted', '')
            job.date_posted = datetime.strptime(date_posted_str, '%Y-%m-%d').date() if date_posted_str else None
            session.commit()
            flash('Job updated successfully!', 'success')
            return redirect(url_for('job_list'))
        
        members = session.query(Member).join(User).all()
        return render_template('job_form.html', job=job, members=members)
    finally:
        session.close()


@app.route('/jobs/<int:job_id>/delete', methods=['POST'])
def job_delete(job_id):
    """Delete a job"""
    session = get_session()
    try:
        job = first_or_404(session.query(Job).filter_by(job_id=job_id))
        session.delete(job)
        session.commit()
        flash('Job deleted successfully!', 'success')
    except Exception as e:
        session.rollback()
        flash(f'Error deleting job: {str(e)}', 'error')
    finally:
        session.close()
    return redirect(url_for('job_list'))


# ==================== JOB APPLICATION ROUTES ====================
@app.route('/job-applications')
def job_application_list():
    """List all job applications with caregiver and job information"""
    session = get_session()
    try:
        applications = session.query(JobApplication).join(Caregiver).join(User).join(Job).all()
        return render_template('job_application_list.html', applications=applications)
    finally:
        session.close()


@app.route('/job-applications/create', methods=['GET', 'POST'])
def job_application_create():
    """Create a new job application"""
    session = get_session()
    try:
        if request.method == 'POST':
            try:
                date_applied = None
                date_applied_str = request.form.get('date_applied', '')
                if date_applied_str:
                    try:
                        date_applied = datetime.strptime(date_applied_str, '%Y-%m-%d').date()
                    except ValueError:
                        flash('Invalid date format. Please use YYYY-MM-DD format.', 'error')
                        caregivers = session.query(Caregiver).join(User).all()
                        jobs = session.query(Job).all()
                        return render_template('job_application_form.html', application=None, caregivers=caregivers, jobs=jobs)
                
                application = JobApplication(
                    caregiver_user_id=int(request.form['caregiver_user_id']),
                    job_id=int(request.form['job_id']),
                    date_applied=date_applied
                )
                session.add(application)
                session.commit()
                flash('Job application created successfully!', 'success')
                return redirect(url_for('job_application_list'))
            except ValueError as e:
                session.rollback()
                flash(f'Invalid input: {str(e)}', 'error')
                caregivers = session.query(Caregiver).join(User).all()
                jobs = session.query(Job).all()
                return render_template('job_application_form.html', application=None, caregivers=caregivers, jobs=jobs)
            except KeyError as e:
                session.rollback()
                flash(f'Missing required field: {str(e)}', 'error')
                caregivers = session.query(Caregiver).join(User).all()
                jobs = session.query(Job).all()
                return render_template('job_application_form.html', application=None, caregivers=caregivers, jobs=jobs)
            except SQLAlchemyError as e:
                session.rollback()
                error_msg = str(e.orig) if hasattr(e, 'orig') else str(e)
                if 'duplicate' in error_msg.lower() or 'unique' in error_msg.lower():
                    flash('This job application already exists.', 'error')
                elif 'foreign key' in error_msg.lower():
                    flash('Invalid caregiver or job ID. Please check your selection.', 'error')
                else:
                    flash(f'Database error: {error_msg}', 'error')
                caregivers = session.query(Caregiver).join(User).all()
                jobs = session.query(Job).all()
                return render_template('job_application_form.html', application=None, caregivers=caregivers, jobs=jobs)
            except Exception as e:
                session.rollback()
                flash(f'Error creating job application: {str(e)}', 'error')
                caregivers = session.query(Caregiver).join(User).all()
                jobs = session.query(Job).all()
                return render_template('job_application_form.html', application=None, caregivers=caregivers, jobs=jobs)
        
        caregivers = session.query(Caregiver).join(User).all()
        jobs = session.query(Job).all()
        return render_template('job_application_form.html', application=None, caregivers=caregivers, jobs=jobs)
    finally:
        session.close()


@app.route('/job-applications/<int:caregiver_user_id>/<int:job_id>/edit', methods=['GET', 'POST'])
def job_application_edit(caregiver_user_id, job_id):
    """Edit an existing job application"""
    session = get_session()
    try:
        application = first_or_404(session.query(JobApplication).filter_by(
            caregiver_user_id=caregiver_user_id,
            job_id=job_id
        ))
        
        if request.method == 'POST':
            application.caregiver_user_id = int(request.form['caregiver_user_id'])
            application.job_id = int(request.form['job_id'])
            date_applied_str = request.form.get('date_applied', '')
            application.date_applied = datetime.strptime(date_applied_str, '%Y-%m-%d').date() if date_applied_str else None
            session.commit()
            flash('Job application updated successfully!', 'success')
            return redirect(url_for('job_application_list'))
        
        caregivers = session.query(Caregiver).join(User).all()
        jobs = session.query(Job).all()
        return render_template('job_application_form.html', application=application, caregivers=caregivers, jobs=jobs)
    finally:
        session.close()


@app.route('/job-applications/<int:caregiver_user_id>/<int:job_id>/delete', methods=['POST'])
def job_application_delete(caregiver_user_id, job_id):
    """Delete a job application"""
    session = get_session()
    try:
        application = first_or_404(session.query(JobApplication).filter_by(
            caregiver_user_id=caregiver_user_id,
            job_id=job_id
        ))
        session.delete(application)
        session.commit()
        flash('Job application deleted successfully!', 'success')
    except Exception as e:
        session.rollback()
        flash(f'Error deleting job application: {str(e)}', 'error')
    finally:
        session.close()
    return redirect(url_for('job_application_list'))


# ==================== APPOINTMENT ROUTES ====================
@app.route('/appointments')
def appointment_list():
    """List all appointments with caregiver and member information"""
    session = get_session()
    try:
        # 使用 joinedload 预加载关系，避免 N+1 查询问题
        from sqlalchemy.orm import joinedload
        appointments = session.query(Appointment)\
            .options(joinedload(Appointment.caregiver).joinedload(Caregiver.user))\
            .options(joinedload(Appointment.member).joinedload(Member.user))\
            .all()
        return render_template('appointment_list.html', appointments=appointments)
    finally:
        session.close()


@app.route('/appointments/create', methods=['GET', 'POST'])
def appointment_create():
    """Create a new appointment"""
    session = get_session()
    try:
        if request.method == 'POST':
            try:
                appointment_date = None
                appointment_date_str = request.form.get('appointment_date', '')
                if appointment_date_str:
                    try:
                        appointment_date = datetime.strptime(appointment_date_str, '%Y-%m-%d').date()
                    except ValueError:
                        flash('Invalid date format. Please use YYYY-MM-DD format.', 'error')
                        caregivers = session.query(Caregiver).join(User).all()
                        members = session.query(Member).join(User).all()
                        return render_template('appointment_form.html', appointment=None, caregivers=caregivers, members=members)
                
                appointment_time = None
                appointment_time_str = request.form.get('appointment_time', '')
                if appointment_time_str:
                    try:
                        appointment_time = datetime.strptime(appointment_time_str, '%H:%M').time()
                    except ValueError:
                        flash('Invalid time format. Please use HH:MM format.', 'error')
                        caregivers = session.query(Caregiver).join(User).all()
                        members = session.query(Member).join(User).all()
                        return render_template('appointment_form.html', appointment=None, caregivers=caregivers, members=members)
                
                work_hours = None
                if request.form.get('work_hours'):
                    try:
                        work_hours = float(request.form['work_hours'])
                        if work_hours <= 0:
                            raise ValueError("Work hours must be greater than 0")
                    except ValueError as e:
                        flash(f'Invalid work hours: {str(e)}', 'error')
                        caregivers = session.query(Caregiver).join(User).all()
                        members = session.query(Member).join(User).all()
                        return render_template('appointment_form.html', appointment=None, caregivers=caregivers, members=members)
                
                status = request.form.get('status', 'pending')
                if status not in ('pending', 'accepted', 'declined'):
                    flash('Invalid status. Must be one of: pending, accepted, declined', 'error')
                    caregivers = session.query(Caregiver).join(User).all()
                    members = session.query(Member).join(User).all()
                    return render_template('appointment_form.html', appointment=None, caregivers=caregivers, members=members)
                
                appointment = Appointment(
                    caregiver_user_id=int(request.form['caregiver_user_id']),
                    member_user_id=int(request.form['member_user_id']),
                    appointment_date=appointment_date,
                    appointment_time=appointment_time,
                    work_hours=work_hours,
                    status=status
                )
                session.add(appointment)
                session.commit()
                flash('Appointment created successfully!', 'success')
                return redirect(url_for('appointment_list'))
            except ValueError as e:
                session.rollback()
                flash(f'Invalid input: {str(e)}', 'error')
                caregivers = session.query(Caregiver).join(User).all()
                members = session.query(Member).join(User).all()
                return render_template('appointment_form.html', appointment=None, caregivers=caregivers, members=members)
            except KeyError as e:
                session.rollback()
                flash(f'Missing required field: {str(e)}', 'error')
                caregivers = session.query(Caregiver).join(User).all()
                members = session.query(Member).join(User).all()
                return render_template('appointment_form.html', appointment=None, caregivers=caregivers, members=members)
            except SQLAlchemyError as e:
                session.rollback()
                error_msg = str(e.orig) if hasattr(e, 'orig') else str(e)
                if 'check' in error_msg.lower() or 'constraint' in error_msg.lower():
                    flash('Invalid data: One or more fields violate database constraints. Please check your input.', 'error')
                elif 'foreign key' in error_msg.lower():
                    flash('Invalid caregiver or member ID. Please check your selection.', 'error')
                else:
                    flash(f'Database error: {error_msg}', 'error')
                caregivers = session.query(Caregiver).join(User).all()
                members = session.query(Member).join(User).all()
                return render_template('appointment_form.html', appointment=None, caregivers=caregivers, members=members)
            except Exception as e:
                session.rollback()
                flash(f'Error creating appointment: {str(e)}', 'error')
                caregivers = session.query(Caregiver).join(User).all()
                members = session.query(Member).join(User).all()
                return render_template('appointment_form.html', appointment=None, caregivers=caregivers, members=members)
        
        caregivers = session.query(Caregiver).join(User).all()
        members = session.query(Member).join(User).all()
        return render_template('appointment_form.html', appointment=None, caregivers=caregivers, members=members)
    finally:
        session.close()


@app.route('/appointments/<int:appointment_id>/edit', methods=['GET', 'POST'])
def appointment_edit(appointment_id):
    """Edit an existing appointment"""
    session = get_session()
    try:
        appointment = first_or_404(session.query(Appointment).filter_by(appointment_id=appointment_id))
        
        if request.method == 'POST':
            appointment.caregiver_user_id = int(request.form['caregiver_user_id'])
            appointment.member_user_id = int(request.form['member_user_id'])
            appointment_date_str = request.form.get('appointment_date', '')
            appointment.appointment_date = datetime.strptime(appointment_date_str, '%Y-%m-%d').date() if appointment_date_str else None
            appointment_time_str = request.form.get('appointment_time', '')
            appointment.appointment_time = datetime.strptime(appointment_time_str, '%H:%M').time() if appointment_time_str else None
            appointment.work_hours = float(request.form['work_hours']) if request.form.get('work_hours') else None
            appointment.status = request.form.get('status', 'pending')
            session.commit()
            flash('Appointment updated successfully!', 'success')
            return redirect(url_for('appointment_list'))
        
        caregivers = session.query(Caregiver).join(User).all()
        members = session.query(Member).join(User).all()
        return render_template('appointment_form.html', appointment=appointment, caregivers=caregivers, members=members)
    finally:
        session.close()


@app.route('/appointments/<int:appointment_id>/delete', methods=['POST'])
def appointment_delete(appointment_id):
    """Delete an appointment"""
    session = get_session()
    try:
        appointment = first_or_404(session.query(Appointment).filter_by(appointment_id=appointment_id))
        session.delete(appointment)
        session.commit()
        flash('Appointment deleted successfully!', 'success')
    except Exception as e:
        session.rollback()
        flash(f'Error deleting appointment: {str(e)}', 'error')
    finally:
        session.close()
    return redirect(url_for('appointment_list'))


# Global error handler
@app.errorhandler(Exception)
def handle_error(e):
    """Handle all exceptions and display helpful error messages"""
    error_type = type(e).__name__
    error_message = str(e)
    
    # Log the full traceback for debugging
    print(f"\n{'='*60}")
    print(f"ERROR: {error_type}")
    print(f"Message: {error_message}")
    print(f"{'='*60}")
    traceback.print_exc()
    print(f"{'='*60}\n")
    
    # Return user-friendly error page
    return render_template('error.html', 
                         error_type=error_type,
                         error_message=error_message), 500


if __name__ == '__main__':
    app.run(debug=True, port=5001)
