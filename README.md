# Spy Cat Agency (SCA) Management System

A specialized backend management application built with **Django** and **Django REST Framework**, designed to streamline spy cat recruitment, mission planning, and field data collection.

---

##  System Architecture

The system is built on three core entities:
* **Spy Cats:** The field agents (Name, Breed, Experience, Salary).
* **Missions:** The operations assigned to cats.
* **Targets:** Specific objectives within a mission (1-3 per mission).



---

##  Business Rules & Constraints

* **Breed Validation:** Every new recruit's breed is verified against the official [TheCatAPI](https://thecatapi.com/).
* **Mission Capacity:** A mission must have between **1 and 3 targets**.
* **Assignment Logic:** A cat can only be assigned to **one active mission** at a time.
* **Intel Integrity:** Once a target is marked as completed, its notes become **frozen (read-only)**.
* **Deletion Safety:** Missions cannot be deleted if a cat is already assigned to them.
* **Auto-Completion:** Missions are automatically marked as completed once all their targets are done.

---

##  Installation & Build Guide

### 1. Environment Setup
We recommend using **Python 3.10** or higher.

```bash
# Clone the repository
cd SCA-test_application

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows use: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```
2. Database Initialization
# Generate database schema
```
python manage.py makemigrations
python manage.py migrate
```
3. Launching the System
```
python manage.py runserver
```
API Root: http://127.0.0.1:8000/api/

Admin Dashboard: http://127.0.0.1:8000/admin/

Agency Admin Panel
The Admin Panel is the "Command Center" for the agency, used to manage cats and missions through a visual interface.

URL: http://127.0.0.1:8000/admin/

Username: ```CatCEO```

Password: ```meow```

Developer Testing (Terminal)
Automated tests ensure the system logic remains secure. Run these from the root directory:

```

# Set the settings module environment variable
export DJANGO_SETTINGS_MODULE=SCA.settings

# Run the test suite
pytest
```
Tip: *You can also use the Run All Tests button directly from the Admin Dashboard to see real-time progress.*

Postman Collection
To simplify testing, a Postman Collection file (SCA_Collection.json) is provided in the root directory.

Open Postman.

Click Import.

Select the SCA_Collection.json file.

Ensure the base_url variable is set to http://127.0.0.1:8000.

---
API Reference & Body Examples

### Cats Endpoint (/api/cats/)

- RECRUIT NEW CAT (POST)

- 
```
  {
      "name": "Agent Whiskers",
      "years_of_experience": 5,
      "breed": "Siberian",
      "salary": "5000.00"
  }

```
- UPDATE SALARY (PATCH)
  URL: /api/cats/{id}/
  
```
  {
      "salary": "6000.00"
  }

```
---

### Missions Endpoint (/api/missions/)

- CREATE MISSION (POST)
  (Note: Must have 1-3 targets)

```
  {
      "targets": [
          {
              "name": "Infiltrate Kitchen",
              "country": "Household",
              "notes": "Check for premium tuna."
          },
          {
              "name": "Surveil Laser Pointer",
              "country": "Living Room",
              "notes": "High-velocity red dot detection."
          }
      ]
  }

```
- ASSIGN CAT (PATCH)
  URL: /api/missions/{id}/assign_cat/
  
```
  {
      "cat_id": 1
  }

```
---

###  Targets Endpoint (/api/targets/)

- UPDATE INTEL (PATCH)
  URL: /api/targets/{id}/
  
```
  {
      "notes": "Tuna found. Mission critical progress."
  }

```
- COMPLETE TARGET (PATCH)
  (Note: This freezes the notes forever)
  URL: /api/targets/{id}/
  
```
  {
      "is_completed": true
  }

```
---
