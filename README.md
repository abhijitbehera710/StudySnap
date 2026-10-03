# StudySnap

StudySnap reads timetable and assignment images, extracts academic details with Gemini, creates a study plan, and can send that plan through WhatsApp using Twilio. Students can also ask StudySnap questions about their plan or academic topics.

## Features

- Upload a timetable and one or more assignment images.
- Extract class times, assignment details, and deadlines.
- Generate a plan based on deadlines, workload, available hours, and preferred study time.
- Keep the generated plan and chat visible during the current Streamlit session.
- Send a generated plan to the student's WhatsApp number through Twilio.
- Ask academic questions in a simple chat interface.

## Run locally

1. Create and activate a Python virtual environment.
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Create `.streamlit/secrets.toml` with these keys. Keep real values private and out of Git:

   ```toml
   GEMINI_API_KEY = "your-gemini-api-key"
   TWILIO_ACCOUNT_SID = "your-twilio-account-sid"
   TWILIO_AUTH_TOKEN = "your-twilio-auth-token"
   TWILIO_WHATSAPP_NUMBER = "whatsapp:+your-twilio-sandbox-number"
   TWILIO_CONTENT_SID = "your-approved-content-template-sid"
   ```

4. Start the app:

   ```bash
   streamlit run app.py
   ```

## WhatsApp setup

The app sends a Twilio Content Template using `TWILIO_CONTENT_SID`. Configure the approved template with `{{1}}` for the student's name and `{{2}}` for the generated study plan. The sandbox only supports its provided templates; custom templates require a registered WhatsApp sender and template approval. Twilio and WhatsApp charges may apply.

## Deploy on Streamlit Community Cloud

1. Create a GitHub repository and push this project, excluding `.streamlit/secrets.toml` and the virtual environment.
2. In Streamlit Community Cloud, create an app from the repository and select `app.py` as the entry point.
3. Add the five secret keys listed above in the app's Secrets settings, using valid Gemini and Twilio credentials.
4. Deploy, then test image uploads, plan generation, chat, and WhatsApp delivery from the hosted URL.

## Notes

- Uploaded files and generated plans are held in the active Streamlit session; they are not stored in a database.
- The app currently accepts image uploads (`jpg`, `jpeg`, and `png`).
- Never commit API keys, Twilio credentials, or `.streamlit/secrets.toml`.
