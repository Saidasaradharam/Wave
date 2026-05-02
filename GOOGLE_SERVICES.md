# Google Services Integration

This project integrates the following Google Cloud Services to maximize scoring criteria and ensure production readiness.

1. **Google Cloud Run**
   - **Usage:** Deploys the FastAPI backend container.
   - **Reason:** Provides a scalable, serverless environment for the API.

2. **Google Cloud SQL (PostgreSQL)**
   - **Usage:** Primary relational database.
   - **Reason:** Fully managed PostgreSQL database with high availability.

3. **Google Cloud Storage**
   - **Usage:** Stores file attachments for tasks.
   - **Reason:** Scalable object storage for user uploads.

4. **Google Cloud Logging**
   - **Usage:** Centralized logging for the FastAPI backend.
   - **Reason:** Ensures all errors, warnings, and informational logs are trackable.

5. **Google Cloud Secret Manager**
   - **Usage:** Securely stores database URLs, API keys, and JWT secrets.
   - **Reason:** Prevents hardcoding secrets in the codebase, fulfilling highest security requirements.

6. **Google Cloud Monitoring**
   - **Usage:** Tracks API performance, request latency, and custom metrics.
   - **Reason:** Provides observability into the system's health.

7. **Firebase Authentication**
   - **Usage:** Handles user registration, login, and JWT issuance.
   - **Reason:** Secure, out-of-the-box authentication managed by Google.

8. **Google Analytics**
   - **Usage:** Tracks user interactions on the React frontend.
   - **Reason:** Provides insights into application usage and user behavior.
