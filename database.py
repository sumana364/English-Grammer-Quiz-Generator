import sqlite3
from datetime import datetime
from typing import Dict, List, Optional

class QuizDatabase:
    def __init__(self, db_name="chat_history.database"):
        self.db_name = db_name
        self.init_database()

    def init_database(self):
        """Initialize SQLite database for quiz history"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        # Create quiz_history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quiz_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                timestamp TEXT NOT NULL,
                grammar_topic TEXT NOT NULL,
                question TEXT NOT NULL,
                user_answer TEXT,
                correct_answer TEXT,
                is_correct BOOLEAN,
                score INTEGER,
                feedback TEXT,
                question_type TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions (id)
            )
        ''')

        # Create sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_start TEXT NOT NULL,
                total_questions INTEGER DEFAULT 0,
                total_score INTEGER DEFAULT 0,
                topics_covered TEXT
            )
        ''')

        # Create user_stats table for aggregated statistics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                grammar_topic TEXT UNIQUE NOT NULL,
                total_attempts INTEGER DEFAULT 0,
                correct_attempts INTEGER DEFAULT 0,
                total_score INTEGER DEFAULT 0,
                last_practiced TEXT
            )
        ''')

        conn.commit()
        conn.close()

    def create_quiz_session(self, grammar_topic: str, total_questions: int) -> int:
        """Create a new quiz session and return session_id"""
        conn = sqlite3.connect(self.db_name, timeout=10.0)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO sessions (session_start, total_questions, total_score, topics_covered)
                VALUES (?, ?, 0, ?)
            ''', (
                datetime.now().isoformat(),
                total_questions,
                grammar_topic
            ))

            session_id = cursor.lastrowid
            conn.commit()
            return session_id
        finally:
            conn.close()

    def save_to_history(self, session_id: int, grammar_topic: str, question: str, user_answer: str,
                       correct_answer: str, is_correct: bool, score: int,
                       feedback: str, question_type: str):
        """Save quiz interaction to database"""
        conn = sqlite3.connect(self.db_name, timeout=10.0)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO quiz_history
                (session_id, timestamp, grammar_topic, question, user_answer, correct_answer,
                 is_correct, score, feedback, question_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                session_id,
                datetime.now().isoformat(),
                grammar_topic,
                question,
                user_answer,
                correct_answer,
                is_correct,
                score,
                feedback,
                question_type
            ))

            # Update user stats in the same connection
            cursor.execute('''
                INSERT INTO user_stats (grammar_topic, total_attempts, correct_attempts, total_score, last_practiced)
                VALUES (?, 1, ?, ?, ?)
                ON CONFLICT(grammar_topic) DO UPDATE SET
                    total_attempts = total_attempts + 1,
                    correct_attempts = correct_attempts + ?,
                    total_score = total_score + ?,
                    last_practiced = ?
            ''', (
                grammar_topic,
                1 if is_correct else 0,
                score,
                datetime.now().isoformat(),
                1 if is_correct else 0,
                score,
                datetime.now().isoformat()
            ))

            conn.commit()
        finally:
            conn.close()

    def update_user_stats(self, grammar_topic: str, is_correct: bool, score: int):
        """Update aggregated statistics for a grammar topic"""
        conn = sqlite3.connect(self.db_name, timeout=10.0)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO user_stats (grammar_topic, total_attempts, correct_attempts, total_score, last_practiced)
                VALUES (?, 1, ?, ?, ?)
                ON CONFLICT(grammar_topic) DO UPDATE SET
                    total_attempts = total_attempts + 1,
                    correct_attempts = correct_attempts + ?,
                    total_score = total_score + ?,
                    last_practiced = ?
            ''', (
                grammar_topic,
                1 if is_correct else 0,
                score,
                datetime.now().isoformat(),
                1 if is_correct else 0,
                score,
                datetime.now().isoformat()
            ))

            conn.commit()
        finally:
            conn.close()

    def get_chat_history(self, limit: int = 50) -> List[Dict]:
        """Retrieve chat history from database"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT timestamp, grammar_topic, question, user_answer,
                   correct_answer, is_correct, score, feedback, question_type
            FROM quiz_history
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))

        rows = cursor.fetchall()
        conn.close()

        history = []
        for row in rows:
            history.append({
                'timestamp': row[0],
                'grammar_topic': row[1],
                'question': row[2],
                'user_answer': row[3],
                'correct_answer': row[4],
                'is_correct': row[5],
                'score': row[6],
                'feedback': row[7],
                'question_type': row[8]
            })

        return history

    def get_user_stats(self) -> List[Dict]:
        """Get aggregated user statistics"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT grammar_topic, total_attempts, correct_attempts, total_score, last_practiced
            FROM user_stats
            ORDER BY total_attempts DESC
        ''')

        rows = cursor.fetchall()
        conn.close()

        stats = []
        for row in rows:
            accuracy = (row[2] / row[1] * 100) if row[1] > 0 else 0
            avg_score = (row[3] / row[1]) if row[1] > 0 else 0
            stats.append({
                'topic': row[0],
                'total_attempts': row[1],
                'correct_attempts': row[2],
                'accuracy': accuracy,
                'avg_score': avg_score,
                'last_practiced': row[4]
            })

        return stats

    def get_overall_stats(self) -> Dict:
        """Get overall statistics"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM quiz_history')
        total_questions = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM quiz_history WHERE is_correct = 1')
        correct_answers = cursor.fetchone()[0]

        cursor.execute('SELECT SUM(score) FROM quiz_history')
        total_score = cursor.fetchone()[0] or 0

        conn.close()

        avg_score = (total_score / total_questions) if total_questions > 0 else 0
        accuracy = (correct_answers / total_questions * 100) if total_questions > 0 else 0

        return {
            'total_questions': total_questions,
            'correct_answers': correct_answers,
            'total_score': total_score,
            'avg_score': avg_score,
            'accuracy': accuracy
        }

    def delete_all_history(self):
        """Clear all quiz history"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        cursor.execute('DELETE FROM quiz_history')
        cursor.execute('DELETE FROM sessions')
        cursor.execute('DELETE FROM user_stats')

        conn.commit()
        conn.close()

    def delete_session(self, session_id: int):
        """Delete a specific quiz session and its questions"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        # Delete all questions from this session
        cursor.execute('DELETE FROM quiz_history WHERE session_id = ?', (session_id,))

        # Delete the session
        cursor.execute('DELETE FROM sessions WHERE id = ?', (session_id,))

        conn.commit()
        conn.close()

    def update_session_score(self, session_id: int, total_score: int):
        """Update the total score for a quiz session"""
        conn = sqlite3.connect(self.db_name, timeout=10.0)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                UPDATE sessions
                SET total_score = ?
                WHERE id = ?
            ''', (total_score, session_id))

            conn.commit()
        finally:
            conn.close()

    def get_quiz_sessions(self, limit: int = 50) -> List[Dict]:
        """Get all quiz sessions with summary info"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT s.id, s.session_start, s.total_questions, s.total_score, s.topics_covered,
                   COUNT(CASE WHEN h.is_correct = 1 THEN 1 END) as correct_count
            FROM sessions s
            LEFT JOIN quiz_history h ON s.id = h.session_id
            GROUP BY s.id
            ORDER BY s.session_start DESC
            LIMIT ?
        ''', (limit,))

        rows = cursor.fetchall()
        conn.close()

        sessions = []
        for row in rows:
            sessions.append({
                'session_id': row[0],
                'timestamp': row[1],
                'total_questions': row[2],
                'total_score': row[3],
                'topic': row[4],
                'correct_count': row[5]
            })

        return sessions

    def get_session_questions(self, session_id: int) -> List[Dict]:
        """Get all questions from a specific quiz session"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT timestamp, grammar_topic, question, user_answer,
                   correct_answer, is_correct, score, feedback, question_type
            FROM quiz_history
            WHERE session_id = ?
            ORDER BY timestamp ASC
        ''', (session_id,))

        rows = cursor.fetchall()
        conn.close()

        questions = []
        for row in rows:
            questions.append({
                'timestamp': row[0],
                'grammar_topic': row[1],
                'question': row[2],
                'user_answer': row[3],
                'correct_answer': row[4],
                'is_correct': row[5],
                'score': row[6],
                'feedback': row[7],
                'question_type': row[8]
            })

        return questions

    def get_topic_history(self, topic: str, limit: int = 20) -> List[Dict]:
        """Get history for a specific topic"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT timestamp, question, user_answer, correct_answer,
                   is_correct, score, feedback, question_type
            FROM quiz_history
            WHERE grammar_topic = ?
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (topic, limit))

        rows = cursor.fetchall()
        conn.close()

        history = []
        for row in rows:
            history.append({
                'timestamp': row[0],
                'question': row[1],
                'user_answer': row[2],
                'correct_answer': row[3],
                'is_correct': row[4],
                'score': row[5],
                'feedback': row[6],
                'question_type': row[7]
            })

        return history
