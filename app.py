from datetime import date
import json
import streamlit as st
from google import genai
from google.genai import types
from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client

from prompts import SYSTEM_PROMPT, ACADEMIC_EXTRACTION_PROMPT, STUDY_PLAN_PROMPT

#Gemini client
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
@st.cache_resource
def get_gemini_clint():
    return genai.Client(api_key=GEMINI_API_KEY)

gemini_clint = get_gemini_clint()

# Twilio WhatsApp configuration

TWILIO_ACCOUNT_SID = st.secrets["TWILIO_ACCOUNT_SID"]
TWILIO_AUTH_TOKEN = st.secrets["TWILIO_AUTH_TOKEN"]
TWILIO_WHATSAPP_NUMBER = st.secrets["TWILIO_WHATSAPP_NUMBER"]
TWILIO_CONTENT_SID = st.secrets["TWILIO_CONTENT_SID"]

twilio_client = Client(
    TWILIO_ACCOUNT_SID,
    TWILIO_AUTH_TOKEN
)

def send_whatsapp(to_number, user_name, study_plan):

    try:

        if not to_number.startswith("whatsapp:"):
            to_number = f"whatsapp:{to_number}"

        content_variables = json.dumps(
            {"1": user_name, "2": study_plan},
            ensure_ascii=False
        )

        message = twilio_client.messages.create(
            from_=TWILIO_WHATSAPP_NUMBER,
            to=to_number,
            content_sid=TWILIO_CONTENT_SID,
            content_variables=content_variables
        )

        return message.sid, None

    except TwilioRestException as error:
        return None, f"Twilio error {error.code}: {error.msg}"

    except Exception as error:
        print("WhatsApp Error:", error)
        return None, f"Unexpected error: {error}"

#Gemini image analyze function
def analyze_image(uploaded_file):
    image_bytes = uploaded_file.getvalue()
    image_part = types.Part.from_bytes(
        data=image_bytes,
        mime_type=uploaded_file.type
    )
    response = st.session_state.chat.send_message([
        image_part,
        "Analyze this academic document and explain the important information to me."
    ])
    return response.text

# Gemini academic extraction function
def extract_academic_information(uploaded_file, instruction):
    try:
        image_bytes = uploaded_file.getvalue()
        image_part = types.Part.from_bytes(
            data=image_bytes,
            mime_type=uploaded_file.type
        )
        response = gemini_clint.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=[
                instruction,
                image_part
                ]
        )
        return response.text
    except Exception as e:
        print("Gemini Error:", e)
        return None

def create_study_plan(
        timetable_info,
        assignment_info,
        daily_hours,
        preferred_time
):
    try:
        assignment_text = "\n\n".join(
            assignment for assignment in assignment_info if assignment
        )
        planning_prompt = f"""
{STUDY_PLAN_PROMPT}
STUDENT INFORMATION

Today's date:
{date.today().strftime("%A, %B %d, %Y")}

Daily available study time:
{daily_hours} hours

Preferred study time:
{preferred_time}

TIMETABLE:
{timetable_info}

ASSIGNMENTS:
{assignment_text}

Now create the student's recommended study plan.
"""
        response = gemini_clint.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=planning_prompt
        )
        return response.text
    except Exception as e:
        print("Study Planner Error:", e)
        return None

#Page configuration
st.set_page_config(
    page_title="StudySnap",
    page_icon="📚"
)

if "study_plan" not in st.session_state:
    st.session_state.study_plan = None

# Check whether the user has already completed onboarding
if "onboarded" not in st.session_state:

    st.title("📚 StudySnap")
    st.write("Snap your academics. Understand them. Plan them.")

    with st.form("onboarding_form"):

        name = st.text_input(
            "Your Name",
            placeholder="Enter your name"
        )

        whatsapp_number = st.text_input(
            "WhatsApp Number",
            placeholder="+91XXXXXXXXXX"
            # , help= "This is the number StudySnap will text you"
        )

        submitted = st.form_submit_button(
            "Let's Start 🚀"
        )

        if submitted:

            if not name.strip():
                st.warning(
                    "Please enter your name!"
                )
            elif not whatsapp_number.strip():
                st.warning(
                    "Please enter your WhatsApp number!"
                )

            else:

                st.session_state.name = name.strip()
                st.session_state.whatsapp_number = whatsapp_number.strip()

                st.session_state.chat = gemini_clint.chats.create(
                    model = "gemini-3.5-flash",
                    config=types.GenerateContentConfig(
                        system_instruction= SYSTEM_PROMPT
                    )
                )
                st.session_state.messages = []
                st.session_state.onboarded = True

                st.rerun()

    st.stop()

st.title("📚 StudySnap")
st.write(
    f"Welcome, {st.session_state.name}! 👋\n\n"
    "Upload your timetable and assignments, and StudySnap will "
    "create a personalized study plan for you."
)

st.subheader("📚 Your Academic Information")
#TimeTable
timetable_file = st.file_uploader(
    "📅 Upload your timetable",
    type=["jpg", "jpeg", "png"],
    key="timetable"
)
#Assignments
assignment_files = st.file_uploader(
    "📝 Upload your assignments",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True,
    key="assignments"
)
# #Other documents
# other_files = st.file_uploader(
#     "📄 Upload other academic documents (optional)",
#     type=["jpg", "jpeg", "png"],
#     accept_multiple_files=True,
#     key="other_documents"
# )

if timetable_file is not None:
    st.write("### 📅 Timetable")
    st.image(
        timetable_file,
        caption="Your Timetable",
        use_container_width=True
    )

if assignment_files:
    st.write("### 📝 Assignments")
    for file in assignment_files:
        st.image(
            file,
            caption=file.name,
            use_container_width=True
        )

# if other_files:
#     st.write("### 📄 Other Documents")
#     for file in other_files:
#         st.image(
#             file,
#             caption=file.name,
#             use_container_width=True
#         )

# Study preferences
st.subheader("⏰ Your Study Preferences")
daily_hours = st.number_input(
    "How many hours can you study each day?",
    min_value=1.0,
    max_value=12.0,
    value=2.0,
    step=0.5
)

preferred_time = st.selectbox(
    "When do you prefer studying?",
    [
        "Morning",
        "Afternoon",
        "Evening",
        "Night",
        "Flexible"
    ]
)
# Createing study plan
st.divider()

if st.button("Create My Study Plan", type="primary"):
    if timetable_file is None:
        st.warning("Please Upload Your timetable first.")
    elif not assignment_files:
        st.warning("Please Upload at least one assignment.")
    else:
        with st.spinner("Reading your academic information..."):
            #Featch Timetable
            timetable_info = extract_academic_information(
                timetable_file,
                ACADEMIC_EXTRACTION_PROMPT
            )
            #Featch assignment
            assignment_info = []
            for file in assignment_files:
                information = extract_academic_information(
                    file,
                    ACADEMIC_EXTRACTION_PROMPT
                )
                assignment_info.append(information)

            #Display timetable
            if timetable_info is None:
                st.error(
                    "⚠️ We couldn't analyze your timetable right now. "
                    "Please try again in a moment."
                )
            else:
                st.subheader("📅 Extracted Timetable")
                st.write(timetable_info)

            #Display assignment
            if assignment_info and all(assignment_info):
                st.subheader("📝 Extracted Assignments")

                for index, assignment in enumerate(assignment_info, start=1):
                    st.write(f"### Assignment {index}")
                    st.write(assignment)
            else:
                st.error(
                    "⚠️ We couldn't analyze every assignment document. "
                    "Please try again before creating a plan."
                )

            if timetable_info and assignment_info and all(assignment_info):
                with st.spinner("Creating your personalized study plan..."):

                    study_plan = create_study_plan(
                        timetable_info,
                        assignment_info,
                        daily_hours,
                        preferred_time
                    )
                if study_plan is None:
                    st.error("⚠️ We couldn't create your study plan right now. "
                        "Please try again in a moment.")
                else:
                    st.session_state.study_plan = study_plan

if st.session_state.study_plan:

    st.divider()

    st.subheader("📅 Your Personalized Study Plan")

    st.write(st.session_state.study_plan)

    st.divider()

    if st.button("📱 Send Study Plan to WhatsApp"):

        with st.spinner("Sending your study plan to WhatsApp..."):

            message_sid, whatsapp_error = send_whatsapp(
                st.session_state.whatsapp_number,
                st.session_state.name,
                st.session_state.study_plan
            )

        if message_sid:

            st.success(
                "✅ Your study plan has been sent to WhatsApp!"
            )

        else:
            if whatsapp_error and "63016" in whatsapp_error:
                st.error(
                    "The WhatsApp 24-hour messaging window has expired. "
                    "Send a new WhatsApp message to your Twilio Sandbox, "
                    "then click Send Study Plan again."
                )
            elif whatsapp_error and "63015" in whatsapp_error:
                st.error(
                    "This number has not joined your Twilio Sandbox. "
                    "Join it using the code shown on your Twilio Sandbox page, "
                    "then try again."
                )
            else:
                st.error(
                    "StudySnap couldn't send the WhatsApp message. "
                    f"{whatsapp_error or 'Twilio did not return an error detail.'}"
                )

st.divider()
st.subheader("💬 Ask StudySnap")
if not st.session_state.messages:
    st.info(
        f"Hi {st.session_state.name}! I'm StudySnap, your academic assistant. "
        "Ask me what to work on first, ask a question about your study plan, "
        "or ask me to explain an academic topic."
    )

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

chat_question = st.chat_input("Ask about your plan or an academic topic...")
if chat_question:
    st.session_state.messages.append(
        {"role": "user", "content": chat_question}
    )
    with st.chat_message("user"):
        st.markdown(chat_question)

    current_plan = st.session_state.study_plan or "No study plan has been generated yet."
    chat_context = (
        f"The student's current StudySnap study plan is:\n{current_plan}\n\n"
        f"The student's question is: {chat_question}"
    )

    try:
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                chat_response = st.session_state.chat.send_message(chat_context)
            assistant_reply = chat_response.text or (
                "I couldn't create a response just now. Please try again."
            )
            st.markdown(assistant_reply)
        st.session_state.messages.append(
            {"role": "assistant", "content": assistant_reply}
        )
    except Exception as error:
        print("StudySnap Chat Error:", error)
        st.error("I couldn't answer just now. Please try again.")
