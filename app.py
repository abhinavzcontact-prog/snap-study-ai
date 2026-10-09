import streamlit as st
from google import genai
from google.genai import types
from prompts import SYSTEM_PROMPT
from io import BytesIO
import smtplib
from email.message import EmailMessage



st.set_page_config(
    page_title="Snap & Study",
    page_icon="📚",
    layout="centered",
)
def send_explanation_email(recipient_email, subject, explanation):
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = st.secrets["GMAIL_ADDRESS"]
    message["To"] = recipient_email

    message.set_content(explanation)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(
            st.secrets["GMAIL_ADDRESS"],
            st.secrets["GMAIL_APP_PASSWORD"]
        )
        smtp.send_message(message)



MODEL_NAME = "gemini-3.5-flash-lite"

client = genai.Client(
    api_key=st.secrets["GEMINI_API_KEY"]
)




if "messages" not in st.session_state:
    st.session_state.messages = []




st.title("📚 Snap & Study")

st.write(
    "Upload a study question, diagram, or notes "
    "and let AI explain it."
)




for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        if message["content"]:
            st.write(message["content"])

        if message.get("image_bytes"):
            st.image(
                BytesIO(message["image_bytes"]),
                caption="Uploaded study image",
                use_container_width=True,
            )




chat_input = st.chat_input(
    "Ask me about your study material...",
    accept_file=True,
    file_type=["png", "jpg", "jpeg"],
)




if chat_input:

    user_text = chat_input.text.strip()

    uploaded_files = chat_input.files

    image_bytes = None
    image_mime = None

    

    if uploaded_files:

        uploaded_image = uploaded_files[0]

        image_bytes = uploaded_image.getvalue()

        image_mime = uploaded_image.type

    

    if image_bytes and not user_text:

        user_text = (
            "Examine this study image carefully. "
            "Explain its contents in simple terms. "
            "If it contains a question, solve it "
            "step by step."
        )

    

    if user_text or image_bytes:

        

        user_message = {
            "role": "user",
            "content": user_text,
            "image_bytes": image_bytes,
            "image_mime": image_mime,
        }

        st.session_state.messages.append(user_message)

        

        conversation_contents = []

        for message in st.session_state.messages:

            parts = []

            

            if message["content"]:

                parts.append(
                    types.Part.from_text(
                        text=message["content"]
                    )
                )

            

            if message.get("image_bytes"):

                parts.append(
                    types.Part.from_bytes(
                        data=message["image_bytes"],
                        mime_type=message["image_mime"],
                    )
                )

        

            gemini_role = (
                "user"
                if message["role"] == "user"
                else "model"
            )

            conversation_contents.append(
                types.Content(
                    role=gemini_role,
                    parts=parts,
                )
            )


        try:

            with st.spinner(
                "Snap & Study is thinking..."
            ):

                response = client.models.generate_content(
                    model=MODEL_NAME,
                    contents=conversation_contents,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT
                    ),
                )

                response_text = (
                    response.text
                    or "Sorry, I couldn't generate a response. "
                       "Please try asking another way."
                )

            

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": response_text,
                    "image_bytes": None,
                    "image_mime": None,
                }
            )

            

            st.rerun()

        except Exception as error:

            st.error(
                "Something went wrong while contacting Gemini."
            )

            st.caption(
                f"Error details: {error}"
            )
st.divider()
st.subheader("📧 Save your explanation by email")

recipient_email = st.text_input(
    "Recipient email address",
    placeholder="you@example.com"
)

if st.button("Send explanation by email"):
    explanations = [
        message["content"]
        for message in st.session_state.messages
        if message["role"] == "assistant" and message.get("content")
    ]

    if not recipient_email or "@" not in recipient_email:
        st.warning("Please enter a valid email address.")
    elif not explanations:
        st.warning("Ask a question first so I have an explanation to send.")
    else:
        try:
            send_explanation_email(
                recipient_email,
                "Your Snap & Study Explanation",
                explanations[-1]
            )
            st.success(f"Explanation sent to {recipient_email}!")
        except Exception as error:
            st.error("Email could not be sent. Check your Gmail settings.")
            st.caption(str(error))