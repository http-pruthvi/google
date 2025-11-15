"""
Planner Agent for StudyConcierge
"""
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json
import logging
import asyncio

logger = logging.getLogger(__name__)

class PlannerAgent:
    def __init__(self, memory_bank=None, use_adk: bool = False, adk_model: Optional[str] = None):
        self.memory_bank = memory_bank
        self.use_adk = use_adk
        self.adk_model = adk_model
        
    def create_study_plan(self, syllabus: str, deadlines: Dict[str, str], user_preferences: Dict[str, Any]) -> Dict[str, Any]:
        """
        Creates a detailed study plan based on syllabus, deadlines, and user preferences.
        
        Args:
            syllabus (str): The course syllabus or study material topics
            deadlines (Dict[str, str]): Dictionary mapping subjects/tasks to deadline dates
            user_preferences (Dict[str, Any]): User preferences like study hours, difficulty levels, etc.
            
        Returns:
            Dict[str, Any]: Detailed study plan with daily schedule
        """
        logger.info("Creating study plan...")

        # Optional ADK path
        try:
            if self.use_adk:
                adk_plan = self._create_plan_with_adk(syllabus, deadlines, user_preferences)
                if adk_plan:
                    return adk_plan
        except Exception as e:
            logger.warning(f"ADK planning failed, falling back to built-in logic: {e}")
        
        # Retrieve past plans from memory for personalization
        past_plans = []
        if self.memory_bank:
            past_plans = self.memory_bank.retrieve("past_study_plans")
        
        # Parse deadlines
        parsed_deadlines = {}
        for subject, deadline_str in deadlines.items():
            try:
                parsed_deadlines[subject] = datetime.strptime(deadline_str, "%Y-%m-%d")
            except ValueError:
                parsed_deadlines[subject] = datetime.now() + timedelta(days=7)  # Default to 1 week
        
        # Create study plan
        study_plan = {
            "created_at": datetime.now().isoformat(),
            "syllabus": syllabus,
            "deadlines": parsed_deadlines,
            "preferences": user_preferences,
            "daily_schedule": {},
            "weekly_goals": {}
        }
        
        # Calculate study duration based on deadlines
        today = datetime.now()
        total_days = max([(deadline - today).days for deadline in parsed_deadlines.values()], default=7)
        total_days = max(total_days, 1)  # Ensure at least 1 day
        
        # Distribute study topics across days
        topics = [topic.strip() for topic in syllabus.split(",") if topic.strip()]
        topics_per_day = max(1, len(topics) // total_days)
        
        current_date = today
        topic_index = 0
        
        for day in range(total_days):
            date_key = current_date.strftime("%Y-%m-%d")
            daily_topics = topics[topic_index:topic_index + topics_per_day]
            
            if daily_topics:
                study_plan["daily_schedule"][date_key] = {
                    "topics": daily_topics,
                    "estimated_hours": user_preferences.get("hours_per_day", 2),
                    "priority": "high" if any(subject in ",".join(daily_topics) for subject in parsed_deadlines.keys()) else "normal"
                }
                
                # Set weekly goals
                week_number = current_date.isocalendar()[1]
                if week_number not in study_plan["weekly_goals"]:
                    study_plan["weekly_goals"][week_number] = []
                study_plan["weekly_goals"][week_number].extend(daily_topics)
            
            topic_index += topics_per_day
            current_date += timedelta(days=1)
            
            if topic_index >= len(topics):
                break
        
        # Store plan in memory
        if self.memory_bank:
            plan_summary = {
                "created_at": study_plan["created_at"],
                "subjects": list(parsed_deadlines.keys()),
                "total_days": total_days
            }
            self.memory_bank.save("past_study_plans", plan_summary)
        
        logger.info(f"Study plan created with {len(study_plan['daily_schedule'])} days scheduled")
        return study_plan
    
    def adjust_plan(self, feedback: str, current_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Adjusts the study plan based on user feedback.
        
        Args:
            feedback (str): User feedback on the current plan
            current_plan (Dict[str, Any]): Current study plan
            
        Returns:
            Dict[str, Any]: Adjusted study plan
        """
        logger.info(f"Adjusting plan based on feedback: {feedback}")
        
        # Simple adjustment logic - in a real implementation, this would be more sophisticated
        adjusted_plan = current_plan.copy()
        
        if "more time" in feedback.lower():
            for date in adjusted_plan["daily_schedule"]:
                adjusted_plan["daily_schedule"][date]["estimated_hours"] += 1
                
        elif "less time" in feedback.lower():
            for date in adjusted_plan["daily_schedule"]:
                adjusted_plan["daily_schedule"][date]["estimated_hours"] = max(
                    1, adjusted_plan["daily_schedule"][date]["estimated_hours"] - 1
                )
        
        adjusted_plan["adjusted_at"] = datetime.now().isoformat()
        
        # Store adjusted plan in memory
        if self.memory_bank:
            self.memory_bank.save("adjusted_study_plan", adjusted_plan)
            
        return adjusted_plan

    def _create_plan_with_adk(self, syllabus: str, deadlines: Dict[str, str], user_preferences: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Attempt to create a study plan using an ADK agent, return None on failure."""
        try:
            from studyconcierge.adk_agent import build_planner_adk_agent
        except Exception:
            return None
        agent = build_planner_adk_agent(memory_bank=self.memory_bank, model=self.adk_model)
        if agent is None:
            return None

        prompt = (
            "Create a detailed study plan as strict JSON with keys: "
            "created_at, syllabus, deadlines, preferences, daily_schedule, weekly_goals.\n"
            f"Syllabus: {syllabus}\n"
            f"Deadlines: {json.dumps(deadlines)}\n"
            f"Preferences: {json.dumps(user_preferences)}\n"
            "Ensure daily_schedule maps YYYY-MM-DD to an object with topics (list), estimated_hours (int), and priority (string)."
        )

        # Try multiple invocation methods for robustness
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
                    plan = json.loads(text) if isinstance(text, str) else result
                except Exception:
                    continue
                # Best-effort memory write
                try:
                    if self.memory_bank:
                        self.memory_bank.save(
                            "past_study_plans",
                            {
                                "created_at": plan.get("created_at"),
                                "subjects": list(deadlines.keys()),
                                "total_days": len(plan.get("daily_schedule", {})),
                            },
                        )
                except Exception:
                    pass
                return plan
            except Exception as e:
                logger.debug(f"ADK method {method} failed: {e}")
                continue
        return None