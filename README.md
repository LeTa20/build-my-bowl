Build My Bowl: A full-stack web application for creating and analyzing yogurt bowls with real-time nutritional tracking.

Instructions
Requirements 
* Python 3.8 or higher
  * Download from [python.org](https://www.python.org/downloads/) or install via brew install python3 (macOS) / sudo apt install python3 (Linux)
  * Verify installation: python3 --version
* PostgreSQL database
  * This application uses PostgreSQL for persistent storage. In the CS326 development environment PostgreSQL is provided via Docker.
  * Start PostgreSQL service: brew services start postgresql (macOS) / sudo systemctl start postgresql (Linux)
* pip (Python package manager)
  * Usually included with Python 3.4+. If missing, install via: `python3 -m ensurepip --upgrade` or download [get-pip.py](https://bootstrap.pypa.io/get-pip.py)
  * Verify installation: pip --version

How to Set Up
1. Clone or download the project to the local machine 
2. Install the required dependencies:
  * python3 -m pip install -r requirements.txt
3. Set up PostgreSQL database 
  * Create a database named app (or update the DATABASE_URL in app/db.py)
4. Configure the database connection:
  * By default, the database connection is configured in `app/db.py`. If needed, you may override it by setting the `DATABASE_URL` environment variable to match your PostgreSQL credentials.

  Example:
  ```bash
  export DATABASE_URL="postgresql+psycopg://app:app@localhost:5432/app"
  ```
  # If you're running Postgres locally and you don't already have the app/app setup:
  psql -U postgres

  -- inside the psql prompt:
  CREATE USER app WITH PASSWORD 'app';
  CREATE DATABASE app OWNER app;
  GRANT ALL PRIVILEGES ON DATABASE app TO app;
  \q

5. Seed the database
  * python3 -m app.seed

How to Run
Start FastAPI server:
  * uvicorn app.main:app --reload
  * Find the application at `http://localhost:8000`

How to Test
1. Go to http://localhost:8000 in web browser 
2. Register a new account (name, username, and password) or log in with an existing account
3. Create a bowl (set its name) and add ingredients 
  * See real-time nutritional calculations
    * calories, fiber, protein, and sugar 
    * low, moderate, and high nutrition tags
  * Visual representation of a bowl with hand-drawn images 
4. Delete ingredients using the remove button
5. Save bowl for later access (available on the right-hand panel on the screen) 
6. Remove saved bowls using the Remove button under the bowl name in the right panel 
7. Completely reset the bowl using the create new bowl button  