# English Grammar Quiz Generator

An AI-powered English grammar quiz application that generates unique questions, evaluates answers, and tracks your progress.

## Features

- **18 Grammar Topics**: Covers all major grammar areas including tenses, articles, prepositions, conditionals, and more
- **Multiple Question Types**: MCQ, Fill in the blanks, True/False, Sentence Correction, Short Answer, and Essay questions
- **Flexible Answer Methods**:
  - Select from multiple choice options
  - Type text answers
  - Upload handwritten/typed answers as images
- **AI-Powered Evaluation**: Google Gemini AI evaluates answers and provides detailed feedback
- **Progress Tracking**: View your quiz history, statistics, and performance by topic
- **Persistent Storage**: All quiz history saved in SQLite database

## Requirements

- Python 3.8 or higher
- Google Gemini API key (get it from [Google AI Studio](https://makersuite.google.com/app/apikey))

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Get your Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey)

## Usage

1. Run the application:
```bash
streamlit run app1.py
```

2. Enter your Gemini API key in the sidebar

3. Select a grammar topic and question type

4. Click "Generate New Question" to get a unique question

5. Answer using one of the methods:
   - Select from options (for MCQ)
   - Type your answer
   - Upload an image of your answer

6. Submit and receive instant feedback with scoring

7. View your history and statistics in the respective menu pages

## Application Structure

```
English quiz generator/
├── app1.py                    # Main Streamlit application
├── requirements.txt           # Python dependencies
├── chat_history.database      # SQLite database (auto-created)
└── README.md                  # This file
```

## Database Schema

The application uses SQLite with two tables:

### quiz_history
- Stores all quiz questions, answers, and evaluations
- Fields: id, timestamp, grammar_topic, question, user_answer, correct_answer, is_correct, score, feedback, question_type

### sessions
- Tracks quiz sessions
- Fields: id, session_start, total_questions, total_score, topics_covered

## Menu Options

1. **Generate Quiz**: Create and answer new questions
2. **Chat History**: View all past questions and answers with filters
3. **Statistics**: See your performance metrics by topic
4. **About**: Application information and usage guide

## Grammar Topics Covered

- Tenses (Present, Past, Future)
- Subject-Verb Agreement
- Articles (a, an, the)
- Prepositions
- Pronouns
- Adjectives and Adverbs
- Conditionals
- Passive Voice
- Reported Speech
- Modal Verbs
- Phrasal Verbs
- Relative Clauses
- Conjunctions
- Gerunds and Infinitives
- Punctuation
- Sentence Structure
- Common Grammar Mistakes
- Mixed Grammar Topics

## Scoring System

- Each question is scored out of 10 points
- AI evaluates partial correctness for non-MCQ questions
- Detailed feedback provided for each answer
- Track accuracy and average scores by topic

## Tips for Best Results

1. Be specific in your answers for short answer questions
2. When uploading images, ensure the text is clear and readable
3. Review the feedback and explanations to learn from mistakes
4. Try different question types to diversify your learning
5. Revisit topics where your accuracy is lower

## Troubleshooting

**API Key Issues:**
- Ensure your Gemini API key is valid and active
- Check your API quota and rate limits

**Database Issues:**
- The database is created automatically on first run
- If corrupted, delete `chat_history.database` and restart the app

**Image Upload Issues:**
- Supported formats: PNG, JPG, JPEG
- Ensure images are clear and readable
- Image evaluation requires gemini-pro-vision model

## Version

1.0.0

## License

This project is for educational purposes.
