# ScholarMatch PHP Auth Setup

This folder adds a PHP + MySQL authentication layer for ScholarMatch.

## What it does
- Register a user with: name, password, percentage, income, category, gender, disability, state, and education level
- Log in with: name + password
- Show the saved profile on a dashboard page after login
- Store data in MySQL using PHP sessions

## Files
- `schema.sql` - database and table definition
- `lib/db.php` - PDO connection helper
- `lib/auth.php` - session and auth helpers
- `register.php` - registration form and insert logic
- `login.php` - login form and session creation
- `dashboard.php` - profile summary after login
- `profile.php` - edit saved profile inputs
- `logout.php` - session logout

## Database setup
1. Create the database and table:
   ```sql
   source php/schema.sql;
   ```
2. Or run the SQL in phpMyAdmin / MySQL Workbench.

## Configuration
Update `php/lib/db.php` or set these environment variables:
- `DB_HOST`
- `DB_NAME`
- `DB_USER`
- `DB_PASS`

Default values are:
- host: `127.0.0.1`
- database: `scholarmatch_auth`
- user: `root`
- password: empty

## Run locally
If you have PHP installed, start a local server from the project root or the `php` folder.

Example:
```powershell
cd c:\Users\USER\Desktop\programming\scholarshipRecommmendation\php
php -S 127.0.0.1:8000
```

Then open:
- `http://127.0.0.1:8000/login.php`
- `http://127.0.0.1:8000/register.php`
- `http://127.0.0.1:8000/dashboard.php`

## Recommended flow
1. Register with your profile inputs.
2. Log in with your name and password.
3. Open the dashboard to review your profile.
4. Use the existing ScholarMatch recommendation UI with the saved profile values.

If you want the Python recommender to auto-load the PHP session profile, the next step is to add a small JSON endpoint that exports the current logged-in user data.
