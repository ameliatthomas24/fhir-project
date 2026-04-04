This project is a web-based health portal designed for diabetes management. It leverages the FHIR  standard to store, retrieve, and visualize patient clinical data, to track indicators of diabetes.

1. Start HAPI server (port 8080)
2. Install requirements.txt
3. Run upload_patients.py to load patients on the HAPI server.
4. Activate virtual environment.
5. pip install xgboost, pandas, and sci-kit learn (inside the venv)
6. From src/backend/
    run "uvicorn main:app --reload" (port 8000)
7. From src/frontend/
   run "npm run dev" (port 3000)
8. Defaults to homepage, ml risk page is available as well.
