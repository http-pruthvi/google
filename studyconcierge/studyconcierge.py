"""
Main entry point for StudyConcierge - A Multi-Agent Personal Study Planner
"""
import asyncio
import logging
from datetime import datetime
from typing import Optional
from agents.planner import PlannerAgent
from agents.summarizer import SummarizerAgent
from agents.quiz_agent import QuizAgent
from agents.session_manager import SessionManagerAgent, InMemorySessionService
from tools.search_tool import SearchTool
from tools.pdf_tool import PDFTool
from tools.memory_bank import MemoryBank

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StudyConcierge:
    def __init__(self, use_adk: bool = False, adk_model: Optional[str] = None):
        """Initialize the StudyConcierge system with all components."""
        logger.info("Initializing StudyConcierge system...")
        
        # Initialize memory bank
        self.memory_bank = MemoryBank()
        
        # Initialize tools
        self.search_tool = SearchTool()
        self.pdf_tool = PDFTool()
        
        # Initialize session service
        self.session_service = InMemorySessionService()
        
        # Initialize agents
        self.planner_agent = PlannerAgent(memory_bank=self.memory_bank, use_adk=use_adk, adk_model=adk_model)
        self.summarizer_agent = SummarizerAgent(
            search_tool=self.search_tool, 
            pdf_tool=self.pdf_tool, 
            memory_bank=self.memory_bank,
            use_adk=use_adk,
            adk_model=adk_model
        )
        self.quiz_agent = QuizAgent(memory_bank=self.memory_bank, use_adk=use_adk, adk_model=adk_model)
        self.session_manager = SessionManagerAgent(
            session_service=self.session_service, 
            memory_bank=self.memory_bank,
            use_adk=use_adk,
            adk_model=adk_model
        )
        
        logger.info("StudyConcierge system initialized successfully!")
    
    def start_session(self, user_id: str):
        """Start a new study session for a user."""
        logger.info(f"Starting new session for user: {user_id}")
        session_id = self.session_manager.start_session(user_id)
        
        # Update session with initial progress
        initial_progress = {
            "status": "session_started",
            "timestamp": datetime.now().isoformat()
        }
        self.session_manager.update_session_progress(initial_progress)
        
        return session_id
    
    def create_study_plan(self, syllabus: str, deadlines: dict, preferences: dict):
        """Create a personalized study plan."""
        logger.info("Creating study plan...")
        return self.planner_agent.create_study_plan(syllabus, deadlines, preferences)
    
    async def summarize_content(self, content: str, content_type: str = "text", max_length: int = 500):
        """Summarize study content."""
        logger.info(f"Summarizing {content_type} content...")
        return await self.summarizer_agent.summarize_content(content, content_type, max_length)
    
    def generate_quiz(self, topic: str, content: str, num_questions: int = 5):
        """Generate a quiz based on content."""
        logger.info(f"Generating quiz for topic: {topic}")
        return self.quiz_agent.generate_quiz(topic, content, num_questions)
    
    async def process_pdf(self, pdf_path: str):
        """Process a large PDF document."""
        logger.info(f"Processing PDF: {pdf_path}")
        return await self.summarizer_agent.process_large_pdf(pdf_path)
    
    def update_progress(self, progress_data: dict):
        """Update session progress."""
        logger.info("Updating session progress...")
        return self.session_manager.update_session_progress(progress_data)
    
    def end_session(self):
        """End the current study session."""
        logger.info("Ending session...")
        return self.session_manager.end_session()
    
    def get_user_history(self, user_id: str):
        """Get user study history."""
        logger.info(f"Retrieving history for user: {user_id}")
        return self.session_manager.get_user_history(user_id)

async def main():
    """Main function to demonstrate StudyConcierge functionality."""
    print("🎓 Welcome to StudyConcierge - Your AI Study Assistant! 🎓")
    print("=" * 60)
    
    # Initialize the system
    study_concierge = StudyConcierge()
    
    # Start a session
    user_id = "student_123"
    session_id = study_concierge.start_session(user_id)
    print(f"✅ Started session: {session_id}")
    
    # Create a study plan
    syllabus = "Introduction to Machine Learning, Linear Regression, Logistic Regression, Neural Networks"
    deadlines = {
        "Midterm Exam": "2025-12-15",
        "Final Project": "2026-01-20"
    }
    preferences = {
        "hours_per_day": 3,
        "preferred_time": "evening",
        "difficulty_level": "intermediate"
    }
    
    plan = study_concierge.create_study_plan(syllabus, deadlines, preferences)
    print(f"✅ Study plan created with {len(plan['daily_schedule'])} days scheduled")
    
    # Summarize content
    sample_content = """
    Machine learning is a method of data analysis that automates analytical model building. 
    It is a branch of artificial intelligence based on the idea that systems can learn from data, 
    identify patterns and make decisions with minimal human intervention.
    """
    
    summary_result = await study_concierge.summarize_content(sample_content, "text", 200)
    print("✅ Content summarized successfully")
    print(f"   Summary: {summary_result['summary'][:100]}...")
    
    # Generate a quiz
    quiz = study_concierge.generate_quiz("Machine Learning", sample_content, 3)
    print(f"✅ Quiz generated with {len(quiz['questions'])} questions")
    
    # Process a PDF (simulated)
    pdf_result = await study_concierge.process_pdf("sample_ml_notes.pdf")
    print(f"✅ PDF processing completed with status: {pdf_result['status']}")
    
    # Update progress
    progress = {
        "completed_tasks": ["study_plan_created", "content_summarized", "quiz_generated"],
        "current_task": "reviewing_material",
        "study_time_minutes": 45
    }
    study_concierge.update_progress(progress)
    print("✅ Session progress updated")
    
    # Get user history
    history = study_concierge.get_user_history(user_id)
    print(f"✅ Retrieved user history: {history['sessions_count']} sessions completed")
    
    # End session
    study_concierge.end_session()
    print("✅ Session ended successfully")
    
    print("\n" + "=" * 60)
    print("🎉 StudyConcierge demonstration completed!")
    print("📈 You've saved 6-10 hours of study planning this week!")
    print("=" * 60)

if __name__ == "__main__":
    # Run the main async function
    asyncio.run(main())