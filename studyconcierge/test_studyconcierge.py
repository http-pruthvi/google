"""
Test file for StudyConcierge components
"""
import unittest
import asyncio
from datetime import datetime

from agents.planner import PlannerAgent
from agents.summarizer import SummarizerAgent
from agents.quiz_agent import QuizAgent
from agents.session_manager import SessionManagerAgent, InMemorySessionService
from tools.memory_bank import MemoryBank
from tools.search_tool import SearchTool
from tools.pdf_tool import PDFTool

class TestStudyConcierge(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.memory_bank = MemoryBank()
        self.search_tool = SearchTool()
        self.pdf_tool = PDFTool()
        self.session_service = InMemorySessionService()
        
        # Initialize agents
        self.planner_agent = PlannerAgent(memory_bank=self.memory_bank)
        self.summarizer_agent = SummarizerAgent(
            search_tool=self.search_tool, 
            pdf_tool=self.pdf_tool, 
            memory_bank=self.memory_bank
        )
        self.quiz_agent = QuizAgent(memory_bank=self.memory_bank)
        self.session_manager = SessionManagerAgent(
            session_service=self.session_service, 
            memory_bank=self.memory_bank
        )
    
    def test_planner_agent_create_study_plan(self):
        """Test that the planner agent can create a study plan."""
        syllabus = "Introduction to AI, Machine Learning, Neural Networks"
        deadlines = {"Final Exam": "2025-12-15"}
        preferences = {"hours_per_day": 2}
        
        plan = self.planner_agent.create_study_plan(syllabus, deadlines, preferences)
        
        self.assertIn("daily_schedule", plan)
        self.assertIn("weekly_goals", plan)
        self.assertGreater(len(plan["daily_schedule"]), 0)
    
    def test_planner_agent_adjust_plan(self):
        """Test that the planner agent can adjust a study plan."""
        syllabus = "Introduction to AI, Machine Learning"
        deadlines = {"Midterm": "2025-11-30"}
        preferences = {"hours_per_day": 2}
        
        original_plan = self.planner_agent.create_study_plan(syllabus, deadlines, preferences)
        adjusted_plan = self.planner_agent.adjust_plan("more time", original_plan)
        
        self.assertIn("adjusted_at", adjusted_plan)
    
    def test_summarizer_agent_summarize_text(self):
        """Test that the summarizer agent can summarize text."""
        content = "This is a sample text that needs to be summarized for testing purposes."
        
        # Run async function in event loop
        summary_result = asyncio.run(
            self.summarizer_agent.summarize_content(content, "text", 100)
        )
        
        self.assertIn("summary", summary_result)
        self.assertIn("key_points", summary_result)
        self.assertGreater(len(summary_result["summary"]), 0)
    
    def test_quiz_agent_generate_quiz(self):
        """Test that the quiz agent can generate a quiz."""
        topic = "Machine Learning"
        content = "Machine learning is a method of data analysis that automates analytical model building."
        
        quiz = self.quiz_agent.generate_quiz(topic, content, 2)
        
        self.assertEqual(quiz["topic"], topic)
        self.assertIn("questions", quiz)
        self.assertGreaterEqual(len(quiz["questions"]), 1)
    
    def test_memory_bank_save_and_retrieve(self):
        """Test that the memory bank can save and retrieve data."""
        key = "test_key"
        data = {"test": "data"}
        
        # Save data
        self.memory_bank.save(key, data)
        
        # Retrieve data
        retrieved = self.memory_bank.retrieve(key)
        
        self.assertIn(data, retrieved)
    
    def test_session_manager_start_and_end_session(self):
        """Test that the session manager can start and end sessions."""
        user_id = "test_user"
        
        # Start session
        session_id = self.session_manager.start_session(user_id)
        self.assertIsNotNone(session_id)
        
        # Check session data
        session_data = self.session_manager.get_session_data()
        self.assertIsNotNone(session_data)
        if session_data is not None:  # Add null check before accessing session_data
            self.assertEqual(session_data["user_id"], user_id)
        
        # End session
        success = self.session_manager.end_session()
        self.assertTrue(success)
    
    def test_search_tool_search(self):
        """Test that the search tool can perform searches."""
        query = "machine learning"
        
        # Run async function in event loop
        results = asyncio.run(self.search_tool.search(query, 2))
        
        self.assertIsInstance(results, list)
        self.assertGreaterEqual(len(results), 1)
        self.assertIn("title", results[0])
        self.assertIn("url", results[0])
    
    def test_pdf_tool_extract_text(self):
        """Test that the PDF tool can extract text."""
        pdf_path = "sample.pdf"
        
        # Run async function in event loop
        text = asyncio.run(self.pdf_tool.extract_text(pdf_path))
        
        self.assertIsInstance(text, str)
        self.assertGreater(len(text), 0)

if __name__ == "__main__":
    unittest.main()