import os
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://nuraiaripbay:050921@localhost:5432/caregiver_platform')

<<<<<<< HEAD
=======
# Database configuration
# Note: If DATABASE_URL environment variable is set, it will be used first
# If you encounter connection errors, check environment variable: echo $DATABASE_URL
# To clear environment variable: unset DATABASE_URL
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/caregiver_platform')

# Debug: Display configuration being used (password masked)
>>>>>>> 5c2d7286488f87a11aeaafed19c20ef22e1aec10
if DATABASE_URL and '@' in DATABASE_URL:
    parts = DATABASE_URL.split('@')
    if '://' in parts[0] and ':' in parts[0].split('://')[1]:
        protocol_user = parts[0].split('://')
        user_pass = protocol_user[1].split(':')
        print(f"[Config] Using: {protocol_user[0]}://{user_pass[0]}:****@{parts[1]}")

SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')# Flask configuration


