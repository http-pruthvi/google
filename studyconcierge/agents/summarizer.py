"""
Summarizer Agent for StudyConcierge
"""
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging
import asyncio

# Optional ADK imports
try:
    from google.adk.agents import Agent as AdkAgent
except Exception:
    AdkAgent = None

logger = logging.getLogger(__name__)

class SummarizerAgent:
    def __init__(self, search_tool=None, pdf_tool=None, memory_bank=None, use_adk: bool = False, adk_model: Optional[str] = None):
        self.search_tool = search_tool
        self.pdf_tool = pdf_tool
        self.memory_bank = memory_bank
        self.use_adk = use_adk
        self.adk_model = adk_model
        
    async def summarize_content(self, content: str, content_type: str = "text", 
                              max_length: int = 500) -> Dict[str, Any]:
        """
        Summarizes content using appropriate tools based on content type.
        
        Args:
            content (str): The content to summarize
            content_type (str): Type of content ("text", "pdf", "web")
            max_length (int): Maximum length of summary
            
        Returns:
            Dict[str, Any]: Summary result with metadata
        """
        logger.info(f"Summarizing {content_type} content...")
        
        summary_result = {
            "original_content_type": content_type,
            "summary": "",
            "key_points": [],
            "metadata": {
                "summarized_at": datetime.now().isoformat(),
                "original_length": len(content)
            }
        }
        
        try:
            if content_type == "pdf":
                # Handle PDF content
                if self.pdf_tool:
                    extracted_text = await self.pdf_tool.extract_text(content)
                    summary_result["summary"] = await self._generate_summary(extracted_text, max_length)
                    summary_result["key_points"] = await self._extract_key_points(extracted_text)
                else:
                    summary_result["summary"] = f"PDF summary not available (no PDF tool configured). Content preview: {content[:100]}..."
                    
            elif content_type == "web":
                # Handle web content
                if self.search_tool:
                    search_results = await self.search_tool.search(content)
                    combined_content = "\n".join([result.get("snippet", "") for result in search_results])
                    summary_result["summary"] = await self._generate_summary(combined_content, max_length)
                    summary_result["key_points"] = await self._extract_key_points(combined_content)
                    summary_result["search_results"] = search_results
                else:
                    summary_result["summary"] = f"Web search summary not available (no search tool configured). Search term: {content}"
                    
            else:  # text
                summary_result["summary"] = await self._generate_summary(content, max_length)
                summary_result["key_points"] = await self._extract_key_points(content)
                
            # Store summary in memory
            if self.memory_bank:
                # MemoryBank.save is sync in our implementation
                try:
                    self.memory_bank.save("content_summaries", summary_result)
                except Exception:
                    # If a custom async memory implementation is used elsewhere
                    if hasattr(self.memory_bank, "save") and asyncio.iscoroutinefunction(self.memory_bank.save):
                        await self.memory_bank.save("content_summaries", summary_result)
                
        except Exception as e:
            logger.error(f"Error summarizing content: {str(e)}")
            summary_result["error"] = str(e)
            summary_result["summary"] = f"Error occurred while summarizing: {str(e)}"
            
        return summary_result
    
    async def _generate_summary(self, text: str, max_length: int) -> str:
        """
        Generates a summary of the given text.
        
        Args:
            text (str): Text to summarize
            max_length (int): Maximum length of summary
            
        Returns:
            str: Generated summary
        """
        # Prefer ADK-driven summarization if configured
        if self.use_adk and AdkAgent is not None and self.adk_model:
            try:
                return await self._generate_summary_with_adk(text, max_length)
            except Exception as e:
                logger.warning(f"ADK summarization failed, falling back to simple summary: {e}")
        
        # Simple extractive summary fallback
        sentences = text.split(". ")
        if len(sentences) <= 3:
            return ". ".join(sentences) + "."
            
        # Take the first and last sentences as key parts
        summary_sentences = [sentences[0]]
        if len(sentences) > 1:
            summary_sentences.append(sentences[-1])
            
        summary = ". ".join(summary_sentences) + "."
        
        # Truncate if too long
        if len(summary) > max_length:
            summary = summary[:max_length-3] + "..."
            
        return summary
    
    async def _generate_summary_with_adk(self, text: str, max_length: int) -> str:
        """Generate a summary using Google ADK LLM agent, if available."""
        if AdkAgent is None:
            raise RuntimeError("ADK Agent not available")
        
        # Create a lightweight ADK agent per request to avoid global state
        instruction = (
            "You are a concise academic summarizer. Summarize the input text into a single paragraph "
            f"no longer than {max_length} characters. Keep key ideas intact."
        )
        agent = AdkAgent(
            name="summarizer",
            model=self.adk_model,
            instruction=instruction,
            description="Summarizes academic content concisely."
        )
        
        # ADK APIs may differ; attempt common invocation patterns
        prompt = f"Summarize the following text:\n\n{text}\n\nOutput only the summary paragraph."
        response_text = None
        for method_name in ("run", "invoke", "execute"):
            method = getattr(agent, method_name, None)
            if callable(method):
                try:
                    maybe_resp = method(prompt)
                    # Support async or sync methods
                    if asyncio.iscoroutine(maybe_resp):
                        resp = await maybe_resp
                    else:
                        resp = maybe_resp
                    # Try to extract text
                    if isinstance(resp, str):
                        response_text = resp
                    elif isinstance(resp, dict) and "text" in resp:
                        response_text = resp["text"]
                    elif hasattr(resp, "text"):
                        response_text = getattr(resp, "text")
                    if response_text:
                        break
                except Exception:
                    continue
        
        if not response_text:
            # Final fallback: simple truncation of original text
            response_text = text[:max_length-3] + "..." if len(text) > max_length else text
        
        # Trim to max_length
        if len(response_text) > max_length:
            response_text = response_text[:max_length-3] + "..."
        return response_text
    
    async def _extract_key_points(self, text: str) -> List[str]:
        """
        Extracts key points from the text.
        
        Args:
            text (str): Text to extract key points from
            
        Returns:
            List[str]: List of key points
        """
        # Simple key point extraction - in reality, this would use NLP techniques
        sentences = text.split(". ")
        key_points = []
        
        # Extract sentences that seem important (contain certain keywords)
        important_keywords = ["important", "key", "main", "significant", "crucial", "essential"]
        
        for sentence in sentences[:10]:  # Limit to first 10 sentences
            if any(keyword in sentence.lower() for keyword in important_keywords):
                key_points.append(sentence.strip())
                
        # If we didn't find any keyword-based points, take the first few sentences
        if not key_points:
            key_points = [sentence.strip() for sentence in sentences[:3]]
            
        return key_points
    
    async def process_large_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        Processes a large PDF file in chunks for long-running operations.
        
        Args:
            pdf_path (str): Path to the PDF file
            
        Returns:
            Dict[str, Any]: Processing result with status and summary
        """
        logger.info(f"Processing large PDF: {pdf_path}")
        
        result = {
            "pdf_path": pdf_path,
            "status": "processing",
            "chunks_processed": 0,
            "total_chunks": 0,
            "summary": None,
            "started_at": datetime.now().isoformat()
        }
        
        try:
            if not self.pdf_tool:
                raise Exception("PDF tool not configured")
                
            # Split PDF into chunks for processing
            chunks = await self.pdf_tool.split_into_chunks(pdf_path, chunk_size=1000)
            result["total_chunks"] = len(chunks)
            
            processed_chunks = []
            for i, chunk in enumerate(chunks):
                # Process each chunk
                chunk_summary = await self.summarize_content(chunk, "text", 200)
                processed_chunks.append(chunk_summary)
                result["chunks_processed"] = i + 1
                
                # Simulate processing time for demonstration
                await asyncio.sleep(0.1)
            
            # Combine chunk summaries into final summary
            combined_text = " ".join([chunk["summary"] for chunk in processed_chunks])
            final_summary = await self.summarize_content(combined_text, "text", 500)
            
            result["status"] = "completed"
            result["summary"] = final_summary
            result["completed_at"] = datetime.now().isoformat()
            
            # Store in memory
            if self.memory_bank:
                try:
                    self.memory_bank.save("large_pdf_processing", result)
                except Exception:
                    if hasattr(self.memory_bank, "save") and asyncio.iscoroutinefunction(self.memory_bank.save):
                        await self.memory_bank.save("large_pdf_processing", result)
                
        except Exception as e:
            logger.error(f"Error processing large PDF: {str(e)}")
            result["status"] = "failed"
            result["error"] = str(e)
            result["completed_at"] = datetime.now().isoformat()
            
        return result