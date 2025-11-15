"""
Quiz Agent for StudyConcierge
"""
from datetime import datetime
from typing import Dict, List, Any, Optional
import random
import logging
import json
import asyncio

logger = logging.getLogger(__name__)

class QuizAgent:
    def __init__(self, memory_bank=None, use_adk: bool = False, adk_model: Optional[str] = None):
        self.memory_bank = memory_bank
        self.use_adk = use_adk
        self.adk_model = adk_model
        
    def generate_quiz(self, topic: str, content: str, num_questions: int = 5) -> Dict[str, Any]:
        """
        Generates a quiz based on the provided topic and content.
        
        Args:
            topic (str): The topic for the quiz
            content (str): The content to base the quiz on
            num_questions (int): Number of questions to generate
            
        Returns:
            Dict[str, Any]: Quiz with questions and metadata
        """
        logger.info(f"Generating quiz for topic: {topic}")

        # Optional ADK path
        try:
            if self.use_adk:
                adk_quiz = self._generate_quiz_with_adk(topic, content, num_questions)
                if adk_quiz:
                    return adk_quiz
        except Exception as e:
            logger.warning(f"ADK quiz generation failed, falling back: {e}")
        
        # Retrieve past quizzes from memory for personalization
        past_quizzes = []
        if self.memory_bank:
            past_quizzes = self.memory_bank.retrieve("past_quizzes")
        
        # Generate quiz
        quiz = {
            "topic": topic,
            "generated_at": datetime.now().isoformat(),
            "questions": [],
            "metadata": {
                "num_questions": num_questions,
                "source_content_length": len(content)
            }
        }
        
        # Extract key terms from content
        key_terms = self._extract_key_terms(content)
        
        # Generate questions
        for i in range(min(num_questions, len(key_terms))):
            question = self._generate_question(key_terms[i], content)
            if question:
                quiz["questions"].append(question)
        
        # If we don't have enough questions
        if len(quiz["questions"]) < num_questions:
            # Generate additional general questions
            for i in range(num_questions - len(quiz["questions"])):
                question = self._generate_general_question(topic, content, i+1)
                if question:
                    quiz["questions"].append(question)
        
        # Store quiz in memory
        if self.memory_bank:
            self.memory_bank.save("quizzes", quiz)
        
        return quiz
    
    def _extract_key_terms(self, content: str) -> List[str]:
        """
        Extracts key terms from the content.
        
        Args:
            content (str): Content to extract terms from
            
        Returns:
            List[str]: List of key terms
        """
        # Simple term extraction - in reality, this would use NLP techniques
        words = content.split()
        # Filter for potentially important words (longer words, capitalized words)
        key_terms = []
        for word in words:
            cleaned_word = word.strip(".,!?;:").lower()
            if len(cleaned_word) > 4 and cleaned_word.isalpha():
                key_terms.append(cleaned_word)
        
        # Return unique terms
        return list(set(key_terms))[:10]  # Limit to 10 terms
    
    def _generate_question(self, term: str, content: str) -> Dict[str, Any]:
        """
        Generates a question based on a key term.
        
        Args:
            term (str): Key term to base question on
            content (str): Source content
            
        Returns:
            Dict[str, Any]: Question object
        """
        # Simple question generation - in reality, this would use an LLM
        question_types = [
            f"What is the significance of {term} in this context?",
            f"How does {term} relate to the main topic?",
            f"Define {term} based on the provided content.",
            f"Explain the role of {term} in the subject matter."
        ]
        
        options = [
            f"It is a key concept related to the topic.",
            f"It plays a minor role in the overall context.",
            f"It is not directly relevant to the main subject.",
            f"Its importance cannot be determined from the given information."
        ]
        
        # Shuffle options and make one correct
        random.shuffle(options)
        correct_answer = options[0]  # Assume first option is correct for simplicity
        
        return {
            "question": random.choice(question_types),
            "options": options,
            "correct_answer": correct_answer,
            "explanation": f"This question tests understanding of '{term}' in the provided context."
        }
    
    def _generate_general_question(self, topic: str, content: str, question_num: int) -> Dict[str, Any]:
        """
        Generates a general question about the topic.
        
        Args:
            topic (str): The topic
            content (str): Source content
            question_num (int): Question number
            
        Returns:
            Dict[str, Any]: Question object
        """
        general_questions = [
            f"What is the main focus of {topic}?",
            f"Which of the following is most relevant to {topic}?",
            f"How would you summarize the key points of {topic}?",
            f"What is the primary purpose of studying {topic}?"
        ]
        
        options = [
            "To gain a comprehensive understanding of the subject.",
            "To complete a mandatory assignment.",
            "To prepare for an upcoming examination.",
            "To develop critical thinking skills."
        ]
        
        # Shuffle options and make one correct
        random.shuffle(options)
        correct_answer = options[0]  # Assume first option is correct for simplicity
        
        return {
            "question": general_questions[(question_num-1) % len(general_questions)],
            "options": options,
            "correct_answer": correct_answer,
            "explanation": f"This question assesses general understanding of {topic}."
        }

    def _generate_quiz_with_adk(self, topic: str, content: str, num_questions: int) -> Optional[Dict[str, Any]]:
        """Attempt to generate a quiz via ADK, return None on failure."""
        try:
            from studyconcierge.adk_agent import build_quiz_adk_agent
        except Exception:
            return None
        agent = build_quiz_adk_agent(memory_bank=self.memory_bank, model=self.adk_model)
        if agent is None:
            return None

        prompt = (
            "Generate a multiple-choice quiz as strict JSON with keys: topic, generated_at, questions. "
            "Each question must have: question, options (list of 4 strings), correct_answer, explanation.\n"
            f"Topic: {topic}\n"
            f"Source content: {content[:1000]}\n"
            f"Number of questions: {num_questions}\n"
        )

        for method in ("run", "ask", "call", "generate"):
            fn = getattr(agent, method, None)
            if not callable(fn):
                continue
            try:
                result = fn(prompt)
                if asyncio.iscoroutine(result):
                    result = asyncio.get_event_loop().run_until_complete(result)
                text = result if isinstance(result, str) else json.dumps(result)
                try:
                    quiz = json.loads(text) if isinstance(text, str) else result
                except Exception:
                    continue
                if self.memory_bank:
                    try:
                        self.memory_bank.save("quizzes", quiz)
                    except Exception:
                        pass
                return quiz
            except Exception as e:
                logger.debug(f"ADK method {method} failed: {e}")
                continue
        return None