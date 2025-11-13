import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import json
from PIL import Image
import os
from typing import Dict, List, Optional
from database import QuizDatabase

# Load environment variables
load_dotenv()

# Initialize database
db = QuizDatabase()

# Configure Gemini API
api_key = "AIzaSyACMw6jZTMp9eaUVJyGl9IuEWcc6l-21rU"

if api_key:
    genai.configure(api_key=api_key)

# Page configuration
st.set_page_config(
    page_title="English Grammar Quiz Generator",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 1rem;
    }
    .quiz-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .score-display {
        font-size: 1.5rem;
        font-weight: bold;
        color: #4CAF50;
        text-align: center;
        padding: 10px;
        background-color: #E8F5E9;
        border-radius: 5px;
    }
    .question-number {
        font-size: 1.2rem;
        font-weight: bold;
        color: #1976D2;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# Grammar topics
GRAMMAR_TOPICS = [
    "Tenses",
    "Subject-Verb Agreement",
    "Articles (a, an, the)",
    "Prepositions",
    "Pronouns",
    "Adjectives and Adverbs",
    "Conditionals",
    "Passive Voice",
    "Reported Speech",
    "Modal Verbs",
    "Phrasal Verbs",
    "Relative Clauses",
    "Conjunctions",
    "Gerunds and Infinitives",
    "Punctuation",
    "Sentence Structure",
    "Common Grammar Mistakes",
    "Mixed Grammar Topics"
]

TENSE_SUBTOPICS = ["Present", "Past", "Future"]

QUESTION_TYPES = [
    "Multiple Choice (MCQ)",
    "Fill in the Blanks",
    "True/False",
    "Sentence Correction",
    "Short Answer",
    "Essay/Paragraph Writing"
]

DIFFICULTY_LEVELS = ["Easy", "Medium", "Hard"]

def configure_gemini():
    """Configure Gemini API"""
    if api_key:
        return True
    return False

def generate_batch_questions(grammar_topic: str, question_type: str, difficulty: str, count: int = 10) -> List[Dict]:
    """Generate multiple unique grammar questions using Gemini"""
    if not configure_gemini():
        return None

    try:
        model = genai.GenerativeModel('gemini-2.5-flash')

        prompt = f"""Generate {count} unique English grammar questions about '{grammar_topic}'.

Question Type: {question_type}
Difficulty Level: {difficulty}

Please provide the response as a JSON array with {count} questions in this format:
[
  {{
    "question": "The question text",
    "type": "{question_type}",
    "options": ["option1", "option2", "option3", "option4"],  // Only if MCQ
    "correct_answer": "The correct answer",
    "explanation": "Brief explanation of the correct answer",
    "difficulty": "{difficulty}"
  }},
  // ... {count-1} more questions
]

Make sure:
- All {count} questions are unique and educational
- For MCQ, provide 4 options for each question
- Questions match the {difficulty} difficulty level
- Questions are diverse and cover different aspects of '{grammar_topic}'"""

        response = model.generate_content(prompt)

        # Parse JSON response
        response_text = response.text.strip()
        # Remove markdown code blocks if present
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.startswith('```'):
            response_text = response_text[3:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]

        questions_data = json.loads(response_text.strip())
        return questions_data

    except Exception as e:
        error_msg = str(e)
        if "quota" in error_msg.lower() or "429" in error_msg:
            st.error("⚠️ **API Quota Exceeded**")
            st.warning("""
            You've reached the daily limit for the Gemini API free tier (50 requests/day).

            **Solutions:**
            - Wait 24 hours for the quota to reset
            - Use a different API key
            - Upgrade to a paid Gemini API plan

            For more information: https://ai.google.dev/gemini-api/docs/rate-limits
            """)
        else:
            st.error(f"Error generating questions: {error_msg}")
        return None

def evaluate_answer(question_data: Dict, user_answer: str, uploaded_image=None) -> Dict:
    """Evaluate user's answer using Gemini"""
    if not configure_gemini():
        return None

    try:
        model = genai.GenerativeModel('gemini-2.5-flash')

        if uploaded_image:
            # Process image answer
            prompt = f"""The question was: {question_data['question']}

The correct answer is: {question_data['correct_answer']}

The user has uploaded an image as their answer. Please analyze the image and:
1. Extract the text/answer from the image
2. Evaluate if it's correct
3. Provide feedback and a score out of 10

Respond in JSON format:
{{
    "extracted_answer": "text from image",
    "is_correct": true/false,
    "score": score out of 10,
    "feedback": "detailed feedback"
}}"""

            image = Image.open(uploaded_image)
            response = model.generate_content([prompt, image])
        else:
            # Process text answer
            prompt = f"""Evaluate this answer:

Question: {question_data['question']}
Correct Answer: {question_data['correct_answer']}
User's Answer: {user_answer}

Please evaluate and respond in JSON format:
{{
    "is_correct": true/false,
    "score": score out of 10,
    "feedback": "detailed feedback with explanation"
}}"""

            response = model.generate_content(prompt)

        # Parse response
        response_text = response.text.strip()
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.startswith('```'):
            response_text = response_text[3:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]

        evaluation = json.loads(response_text.strip())
        return evaluation

    except Exception as e:
        error_msg = str(e)
        if "quota" in error_msg.lower() or "429" in error_msg:
            st.error("⚠️ **API Quota Exceeded**")
            st.warning("""
            You've reached the daily limit for the Gemini API free tier (50 requests/day).

            **Solutions:**
            - Wait 24 hours for the quota to reset
            - Use a different API key
            - Upgrade to a paid Gemini API plan

            For more information: https://ai.google.dev/gemini-api/docs/rate-limits
            """)
        else:
            st.error(f"Error evaluating answer: {error_msg}")
        return None

def main():
    """Main application"""

    # Initialize session state
    if 'batch_questions' not in st.session_state:
        st.session_state.batch_questions = []
    if 'current_question_index' not in st.session_state:
        st.session_state.current_question_index = 0
    if 'total_score' not in st.session_state:
        st.session_state.total_score = 0
    if 'questions_answered' not in st.session_state:
        st.session_state.questions_answered = 0
    if 'quiz_mode' not in st.session_state:
        st.session_state.quiz_mode = False
    if 'quiz_started' not in st.session_state:
        st.session_state.quiz_started = False
    if 'quiz_submitted' not in st.session_state:
        st.session_state.quiz_submitted = False
    if 'show_chat_history' not in st.session_state:
        st.session_state.show_chat_history = False
    if 'question_results' not in st.session_state:
        st.session_state.question_results = {}

    # Sidebar menu
    with st.sidebar:
        st.title("📚 Menu")

        st.divider()

        # Navigation
        menu_option = st.radio(
            "Navigation",
            ["Generate Quiz", "Statistics"]
        )

        st.divider()

        # Quiz History Button (separate from navigation)
        if st.button("📜 Quiz History", use_container_width=True):
            st.session_state.show_chat_history = True
            menu_option = "Quiz History"

        st.divider()

        # Show quiz progress (without scores during quiz)
        if st.session_state.quiz_mode and st.session_state.batch_questions:
            answered_count = len(st.session_state.question_results)
            total_questions = len(st.session_state.batch_questions)
            st.metric("Quiz Progress", f"{answered_count}/{total_questions} questions answered")

    # Main header
    st.markdown('<div class="main-header">📚 English Grammar Quiz Generator</div>', unsafe_allow_html=True)

    # Reset quiz history flag when other navigation options are selected
    if menu_option != "Quiz History" and st.session_state.show_chat_history:
        st.session_state.show_chat_history = False

    # Main content based on menu selection
    if menu_option == "Generate Quiz":
        generate_quiz_page()
    elif menu_option == "Quiz History" or st.session_state.show_chat_history:
        quiz_history_page()
    elif menu_option == "Statistics":
        statistics_page()


def generate_quiz_page():
    """Quiz generation and answering page"""

    if not api_key:
        st.warning("⚠️ API key not configured.")
        return

    st.subheader("📝 Generate Quiz")

    # Topic and difficulty selection
    col1, col2 = st.columns(2)

    with col1:
        selected_topic = st.selectbox(
            "Select Grammar Topic",
            GRAMMAR_TOPICS,
            help="Choose a grammar topic for your quiz"
        )

    with col2:
        selected_type = st.selectbox(
            "Select Question Type",
            QUESTION_TYPES,
            help="Choose the type of questions"
        )

    # Tense subtopic selection (if Tenses is selected)
    if selected_topic == "Tenses":
        st.markdown("#### Select Tense Type")
        tense_cols = st.columns(3)
        selected_tense = None
        with tense_cols[0]:
            if st.button("📅 Present", use_container_width=True):
                selected_tense = "Present"
        with tense_cols[1]:
            if st.button("📆 Past", use_container_width=True):
                selected_tense = "Past"
        with tense_cols[2]:
            if st.button("📋 Future", use_container_width=True):
                selected_tense = "Future"

        if selected_tense:
            st.session_state.selected_tense = selected_tense
            st.info(f"Selected: {selected_tense} Tense")

        # Use the selected tense if available
        if 'selected_tense' in st.session_state:
            final_topic = f"{st.session_state.selected_tense} Tense"
        else:
            final_topic = "Tenses (General)"
    else:
        final_topic = selected_topic

    # Difficulty level selection
    st.markdown("#### Select Difficulty Level")
    diff_cols = st.columns(3)
    selected_difficulty = None

    with diff_cols[0]:
        if st.button("🟢 Easy", use_container_width=True):
            selected_difficulty = "Easy"
    with diff_cols[1]:
        if st.button("🟡 Medium", use_container_width=True):
            selected_difficulty = "Medium"
    with diff_cols[2]:
        if st.button("🔴 Hard", use_container_width=True):
            selected_difficulty = "Hard"

    if selected_difficulty:
        st.session_state.selected_difficulty = selected_difficulty
        st.success(f"Difficulty: {selected_difficulty}")

    # Generate quiz button
    if 'selected_difficulty' in st.session_state:
        if st.button("🎲 Generate Quiz", type="primary", use_container_width=True):
            with st.spinner("Generating 10 questions... This may take a moment."):
                questions = generate_batch_questions(
                    final_topic,
                    selected_type,
                    st.session_state.selected_difficulty,
                    10
                )
                if questions:
                    st.session_state.batch_questions = questions
                    st.session_state.current_question_index = 0
                    st.session_state.quiz_mode = True
                    st.session_state.quiz_started = False  # Set to False to show Start Quiz button
                    st.session_state.quiz_submitted = False  # Reset submission state
                    st.session_state.question_results = {}  # Clear previous results
                    st.session_state.current_topic = final_topic
                    st.success("✅ 10 questions generated successfully!")
                    st.rerun()

    # Show Start Quiz button if questions are generated but quiz not started
    if st.session_state.quiz_mode and st.session_state.batch_questions and not st.session_state.quiz_started:
        st.divider()
        st.info(f"📚 Quiz ready! 10 questions on **{st.session_state.current_topic}** have been generated.")
        if st.button("🚀 Start Quiz", type="primary", use_container_width=True):
            st.session_state.quiz_started = True
            st.rerun()

    # Display current question from batch (only if quiz started)
    if st.session_state.quiz_mode and st.session_state.batch_questions and st.session_state.quiz_started and not st.session_state.quiz_submitted:
        st.divider()

        # Progress
        total_questions = len(st.session_state.batch_questions)
        current_idx = st.session_state.current_question_index
        answered_count = len(st.session_state.question_results)

        # Show "Finish Quiz" button if at least one question is answered
        if answered_count > 0:
            st.info(f"📊 Progress: {answered_count}/{total_questions} questions answered")
            if st.button("🏁 Finish Quiz", type="primary", use_container_width=True):
                # Submit the quiz
                session_id = db.create_quiz_session(
                    st.session_state.current_topic,
                    total_questions
                )

                # Calculate total score
                total_score = sum(r['score'] for r in st.session_state.question_results.values())

                # Save all results to database with session_id
                for q_key, result in st.session_state.question_results.items():
                    db.save_to_history(
                        session_id,
                        result['grammar_topic'],
                        result['question'],
                        result['user_answer'],
                        result['correct_answer'],
                        result['is_correct'],
                        result['score'],
                        result['feedback'],
                        result['question_type']
                    )

                # Update session with total score
                db.update_session_score(session_id, total_score)

                # Mark quiz as submitted
                st.session_state.quiz_submitted = True
                st.rerun()

        if current_idx < total_questions:
            question_data = st.session_state.batch_questions[current_idx]

            st.markdown('<div class="quiz-card">', unsafe_allow_html=True)
            st.markdown(f'<div class="question-number">Question {current_idx + 1} of {total_questions}</div>', unsafe_allow_html=True)

            # Progress bar - fills completely when all questions answered
            progress_value = (current_idx + 1) / total_questions
            st.progress(progress_value)

            st.markdown(f"**Topic:** {st.session_state.current_topic}")
            st.markdown(f"**Type:** {question_data.get('type', 'N/A')}")
            st.markdown(f"**Difficulty:** {question_data.get('difficulty', 'N/A').title()}")
            st.markdown(f"\n{question_data['question']}")

            # Answer input based on question type
            user_answer = None
            uploaded_image = None

            if question_data.get('type') == "Multiple Choice (MCQ)" and 'options' in question_data:
                st.markdown("#### Select your answer:")
                user_answer = st.radio(
                    "Options",
                    question_data['options'],
                    key=f"mcq_answer_{current_idx}",
                    label_visibility="collapsed"
                )
            elif question_data.get('type') == "True/False":
                st.markdown("#### Select your answer:")
                col_t, col_f = st.columns(2)
                with col_t:
                    if st.button("✅ True", key=f"true_btn_{current_idx}", use_container_width=True, type="primary"):
                        st.session_state[f"tf_answer_{current_idx}"] = "True"
                with col_f:
                    if st.button("❌ False", key=f"false_btn_{current_idx}", use_container_width=True, type="secondary"):
                        st.session_state[f"tf_answer_{current_idx}"] = "False"

                # Display selected answer
                if f"tf_answer_{current_idx}" in st.session_state:
                    user_answer = st.session_state[f"tf_answer_{current_idx}"]
                    st.success(f"Selected: {user_answer}")
            else:
                st.markdown("#### Provide your answer:")

                answer_method = st.radio(
                    "Answer Method",
                    ["Type Answer", "Upload Image"],
                    horizontal=True,
                    key=f"answer_method_{current_idx}"
                )

                if answer_method == "Type Answer":
                    user_answer = st.text_area(
                        "Your Answer",
                        height=100,
                        placeholder="Type your answer here...",
                        label_visibility="collapsed",
                        key=f"text_answer_{current_idx}"
                    )
                else:
                    uploaded_image = st.file_uploader(
                        "Upload your answer as an image",
                        type=['png', 'jpg', 'jpeg'],
                        label_visibility="collapsed",
                        key=f"image_upload_{current_idx}"
                    )
                    if uploaded_image:
                        st.image(uploaded_image, caption="Your uploaded answer", use_column_width=True)
                        user_answer = "Image uploaded"

            st.markdown('</div>', unsafe_allow_html=True)

            # Navigation and Submit buttons
            col1, col2, col3 = st.columns([1, 1, 3])
            with col1:
                if st.button("⬅️ Back", key=f"back_{current_idx}", disabled=(current_idx == 0)):
                    st.session_state.current_question_index -= 1
                    st.rerun()
            with col2:
                if st.button("➡️ Next", key=f"next_{current_idx}", disabled=(current_idx >= total_questions - 1)):
                    st.session_state.current_question_index += 1
                    st.rerun()
            with col3:
                submit_button = st.button("✅ Submit Answer", type="primary", key=f"submit_{current_idx}", use_container_width=True)

            # Check if question already answered
            if 'question_results' not in st.session_state:
                st.session_state.question_results = {}

            question_key = f"q_{current_idx}"

            if submit_button:
                if not user_answer and not uploaded_image:
                    st.error("Please provide an answer before submitting.")
                else:
                    with st.spinner("Submitting..."):
                        evaluation = evaluate_answer(
                            question_data,
                            user_answer if user_answer else "",
                            uploaded_image
                        )

                        if evaluation:
                            # Store evaluation result silently
                            st.session_state.question_results[question_key] = {
                                'question': question_data['question'],
                                'user_answer': evaluation.get('extracted_answer', user_answer) if uploaded_image else user_answer,
                                'correct_answer': question_data['correct_answer'],
                                'is_correct': evaluation['is_correct'],
                                'score': evaluation['score'],
                                'feedback': evaluation['feedback'],
                                'explanation': question_data.get('explanation', ''),
                                'grammar_topic': st.session_state.current_topic,
                                'question_type': question_data.get('type', 'N/A')
                            }

                            # Check if this is the last question
                            if current_idx == total_questions - 1:
                                # Last question answered - automatically submit quiz
                                session_id = db.create_quiz_session(
                                    st.session_state.current_topic,
                                    total_questions
                                )

                                # Calculate total score
                                total_score = sum(r['score'] for r in st.session_state.question_results.values())

                                # Save all results to database with session_id
                                for q_key, result in st.session_state.question_results.items():
                                    db.save_to_history(
                                        session_id,
                                        result['grammar_topic'],
                                        result['question'],
                                        result['user_answer'],
                                        result['correct_answer'],
                                        result['is_correct'],
                                        result['score'],
                                        result['feedback'],
                                        result['question_type']
                                    )

                                # Update session with total score
                                db.update_session_score(session_id, total_score)

                                # Mark quiz as submitted
                                st.session_state.quiz_submitted = True
                            else:
                                # Auto-advance to next question if not the last one
                                st.session_state.current_question_index += 1

                            st.rerun()

            # Show if already answered (just indicator, no score) - but NOT if quiz is submitted
            if question_key in st.session_state.question_results and not st.session_state.quiz_submitted:
                st.info("✓ This question has been answered")

    # Show quiz completion screen when quiz is submitted
    if st.session_state.quiz_mode and st.session_state.quiz_submitted:
        st.divider()

        # Quiz completed header
        st.markdown("""
            <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        padding: 30px;
                        border-radius: 15px;
                        text-align: center;
                        margin: 20px 0;'>
                <h1 style='color: white; margin: 0; font-size: 2.5rem;'>🎉 QUIZ COMPLETED! 🎉</h1>
            </div>
        """, unsafe_allow_html=True)

        st.balloons()

        # Calculate final statistics
        if 'question_results' in st.session_state and st.session_state.question_results:
            total_questions = len(st.session_state.batch_questions)
            answered_questions = len(st.session_state.question_results)
            skipped_questions = total_questions - answered_questions

            results = list(st.session_state.question_results.values())
            total_score = sum(r['score'] for r in results)
            correct_count = sum(1 for r in results if r['is_correct'])
            wrong_count = answered_questions - correct_count
            avg_score = total_score / answered_questions if answered_questions > 0 else 0
            accuracy = (correct_count / answered_questions * 100) if answered_questions > 0 else 0

            # Display comprehensive statistics
            st.markdown("### 📊 Quiz Summary")

            # Main metrics in a nice grid
            col1, col2, col3, col4, col5 = st.columns(5)

            with col1:
                st.markdown("""
                    <div style='background-color: #e3f2fd; padding: 20px; border-radius: 10px; text-align: center;'>
                        <h2 style='color: #1976d2; margin: 0;'>{}</h2>
                        <p style='color: #666; margin: 5px 0 0 0;'>Total Questions</p>
                    </div>
                """.format(total_questions), unsafe_allow_html=True)

            with col2:
                st.markdown("""
                    <div style='background-color: #e8f5e9; padding: 20px; border-radius: 10px; text-align: center;'>
                        <h2 style='color: #388e3c; margin: 0;'>{}</h2>
                        <p style='color: #666; margin: 5px 0 0 0;'>Answered</p>
                    </div>
                """.format(answered_questions), unsafe_allow_html=True)

            with col3:
                st.markdown("""
                    <div style='background-color: #fff3e0; padding: 20px; border-radius: 10px; text-align: center;'>
                        <h2 style='color: #f57c00; margin: 0;'>{}</h2>
                        <p style='color: #666; margin: 5px 0 0 0;'>Skipped</p>
                    </div>
                """.format(skipped_questions), unsafe_allow_html=True)

            with col4:
                st.markdown("""
                    <div style='background-color: #e8f5e9; padding: 20px; border-radius: 10px; text-align: center;'>
                        <h2 style='color: #2e7d32; margin: 0;'>✅ {}</h2>
                        <p style='color: #666; margin: 5px 0 0 0;'>Correct</p>
                    </div>
                """.format(correct_count), unsafe_allow_html=True)

            with col5:
                st.markdown("""
                    <div style='background-color: #ffebee; padding: 20px; border-radius: 10px; text-align: center;'>
                        <h2 style='color: #c62828; margin: 0;'>❌ {}</h2>
                        <p style='color: #666; margin: 5px 0 0 0;'>Wrong</p>
                    </div>
                """.format(wrong_count), unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # Performance metrics
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("""
                    <div style='background-color: #f3e5f5; padding: 20px; border-radius: 10px; text-align: center;'>
                        <h2 style='color: #7b1fa2; margin: 0;'>{:.1f}%</h2>
                        <p style='color: #666; margin: 5px 0 0 0;'>Accuracy</p>
                    </div>
                """.format(accuracy), unsafe_allow_html=True)

            with col2:
                st.markdown("""
                    <div style='background-color: #e1f5fe; padding: 20px; border-radius: 10px; text-align: center;'>
                        <h2 style='color: #0277bd; margin: 0;'>{:.1f}/10</h2>
                        <p style='color: #666; margin: 5px 0 0 0;'>Average Score</p>
                    </div>
                """.format(avg_score), unsafe_allow_html=True)

            st.divider()

            # Detailed question-by-question review
            st.markdown("### 📝 Detailed Review")

            for idx, (q_key, result) in enumerate(st.session_state.question_results.items(), 1):
                # Create a card-like container for each question
                status_icon = '✅' if result['is_correct'] else '❌'
                status_color = '#d4edda' if result['is_correct'] else '#f8d7da'

                st.markdown(f"""
                    <div style='background-color: {status_color}; padding: 15px; border-radius: 10px; margin: 10px 0;'>
                        <h4 style='margin: 0;'>{status_icon} Question {idx} - Score: {result['score']}/10</h4>
                    </div>
                """, unsafe_allow_html=True)

                # Question text
                st.markdown(f"**Question:** {result['question']}")

                # Two columns: Your Answer | Correct Answer
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**Your Answer:**")
                    st.info(result['user_answer'])

                with col2:
                    st.markdown("**Correct Answer:**")
                    st.success(result['correct_answer'])

                # Feedback
                st.markdown(f"**Feedback:** {result['feedback']}")

                # Explanation if available
                if result['explanation']:
                    with st.expander("📖 View Explanation"):
                        st.markdown(result['explanation'])

                st.divider()

            st.divider()

        if st.button("🔄 Start New Quiz", use_container_width=True):
            st.session_state.quiz_mode = False
            st.session_state.quiz_started = False
            st.session_state.quiz_submitted = False
            st.session_state.batch_questions = []
            st.session_state.current_question_index = 0
            st.session_state.question_results = {}
            if 'selected_tense' in st.session_state:
                del st.session_state.selected_tense
            if 'selected_difficulty' in st.session_state:
                del st.session_state.selected_difficulty
            st.rerun()

def quiz_history_page():
    """Display quiz history with submitted quizzes grouped by session"""

    # Initialize delete confirmation state
    if 'awaiting_delete_all_confirm' not in st.session_state:
        st.session_state.awaiting_delete_all_confirm = False

    # Back button
    if st.button("⬅️ Back to Quiz", key="back_from_history"):
        st.session_state.show_chat_history = False
        st.session_state.awaiting_delete_all_confirm = False
        st.rerun()

    st.subheader("📜 Quiz History")

    sessions = db.get_quiz_sessions(100)

    if not sessions:
        st.info("No quiz history yet. Complete and submit a quiz to see your history here!")
        return

    # Header with count and delete button
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"**Showing {len(sessions)} quiz sessions**")
    with col2:
        # Delete All button - simple approach
        delete_all = st.button("🗑️ Clear History", type="secondary", key="delete_all_btn", use_container_width=True)

    st.divider()

    # Show confirmation if delete button was clicked
    if delete_all:
        st.session_state.awaiting_delete_all_confirm = True

    if st.session_state.get('awaiting_delete_all_confirm', False):
        st.error("⚠️ **WARNING:** This will permanently delete ALL quiz history!")

        col_yes, col_no, col_space = st.columns([1, 1, 3])

        with col_yes:
            confirm_delete = st.button("✅ Confirm Delete", type="primary", key="confirm_yes_delete", use_container_width=True)
            if confirm_delete:
                db.delete_all_history()
                st.session_state.awaiting_delete_all_confirm = False
                st.success("✅ All history has been cleared!")
                st.balloons()
                st.rerun()

        with col_no:
            cancel_delete = st.button("❌ Cancel", key="cancel_no_delete", use_container_width=True)
            if cancel_delete:
                st.session_state.awaiting_delete_all_confirm = False
                st.rerun()

        st.divider()

    # Display quiz sessions
    for idx, session in enumerate(sessions, 1):
        # Calculate accuracy
        accuracy = (session['correct_count'] / session['total_questions'] * 100) if session['total_questions'] > 0 else 0

        # Session header
        session_status = "✅" if accuracy >= 70 else "❌" if accuracy < 50 else "⚠️"

        with st.expander(
            f"{session_status} Quiz #{idx}: {session['topic']} - "
            f"{session['timestamp'][:19]} - Score: {session['correct_count']}/{session['total_questions']} "
            f"({accuracy:.0f}%)",
            expanded=False
        ):
            # Session summary with delete button
            col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
            col1.metric("Questions", session['total_questions'])
            col2.metric("Correct", f"{session['correct_count']}/{session['total_questions']}")
            col3.metric("Accuracy", f"{accuracy:.1f}%")

            # Delete button for this session
            with col4:
                session_id = session['session_id']
                delete_key = f"delete_{session_id}"

                if st.button("🗑️", key=delete_key, help="Delete this quiz", use_container_width=True):
                    db.delete_session(session_id)
                    st.rerun()

            st.divider()

            # Get all questions from this session
            questions = db.get_session_questions(session['session_id'])

            st.markdown("### 📝 Questions:")

            for q_idx, q in enumerate(questions, 1):
                status_icon = '✅' if q['is_correct'] else '❌'
                status_color = '#d4edda' if q['is_correct'] else '#f8d7da'

                st.markdown(f"""
                    <div style='background-color: {status_color}; padding: 10px; border-radius: 5px; margin: 5px 0;'>
                        <strong>{status_icon} Question {q_idx} - Score: {q['score']}/10</strong>
                    </div>
                """, unsafe_allow_html=True)

                st.markdown(f"**Q:** {q['question']}")

                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Your Answer:**")
                    st.info(q['user_answer'])
                with col2:
                    st.markdown("**Correct Answer:**")
                    st.success(q['correct_answer'])

                if q['feedback']:
                    st.markdown(f"**Feedback:** {q['feedback']}")

                st.divider()

def statistics_page():
    """Display statistics"""

    # Back button
    if st.button("⬅️ Back to Quiz", key="back_from_stats"):
        st.rerun()

    st.subheader("📊 Your Statistics")

    overall_stats = db.get_overall_stats()

    if overall_stats['total_questions'] == 0:
        st.info("No data available yet. Complete some quizzes to see your statistics!")
        return

    # Overall stats
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Questions", overall_stats['total_questions'])
    col2.metric("Correct Answers", overall_stats['correct_answers'])
    col3.metric("Accuracy", f"{overall_stats['accuracy']:.1f}%")
    col4.metric("Average Score", f"{overall_stats['avg_score']:.1f}/10")

    st.divider()

    # Topic-wise performance
    st.markdown("### 📚 Performance by Topic")
    user_stats = db.get_user_stats()

    if user_stats:
        for stat in user_stats:
            st.markdown(f"**{stat['topic']}**")
            col1, col2, col3 = st.columns(3)
            col1.write(f"Questions: {stat['total_attempts']}")
            col2.write(f"Accuracy: {stat['accuracy']:.1f}%")
            col3.write(f"Avg Score: {stat['avg_score']:.1f}/10")
            st.progress(stat['accuracy'] / 100)
    else:
        st.info("No topic statistics available yet.")

def about_page():
    """About page"""
    st.subheader("ℹ️ About")

    st.markdown("""
    ### English Grammar Quiz Generator

    This application helps you improve your English grammar skills through AI-generated questions.

    **Features:**
    - 📚 18 different grammar topics
    - 🎯 Tenses with sub-topics (Present, Past, Future)
    - 🎲 3 difficulty levels (Easy, Medium, Hard)
    - 📝 10 questions per quiz
    - 🤖 AI-powered question generation and evaluation
    - 📊 Multiple question types (MCQ, Fill in blanks, etc.)
    - 🖼️ Text, MCQ, and image-based answers
    - 📈 Detailed statistics and history
    - 💾 Persistent storage of quiz history

    **How to use:**
    1. Select a grammar topic and question type
    2. For Tenses, choose Present, Past, or Future
    3. Select difficulty level (Easy, Medium, or Hard)
    4. Click "Generate 10 Questions"
    5. Answer each question and get instant feedback
    6. Track your progress in the Statistics page

    **Powered by:**
    - Google Gemini AI for question generation and evaluation
    - Streamlit for the user interface
    - SQLite for data persistence

    **Version:** 2.0.0
    """)

if __name__ == "__main__":
    main()
