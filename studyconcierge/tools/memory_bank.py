"""
Memory Bank for StudyConcierge
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)

class MemoryBank:
    def __init__(self):
        # In-memory storage for simplicity
        # In a real implementation, this would use a vector database like FAISS
        self.storage = {}
        self.embeddings = {}  # Would store actual embeddings in a real implementation
        
    def save(self, key: str, data: Any) -> bool:
        """
        Saves data to memory with a key.
        
        Args:
            key (str): Key to store data under
            data (Any): Data to store
            
        Returns:
            bool: True if successful
        """
        logger.info(f"Saving data to memory with key: {key}")
        
        if key not in self.storage:
            self.storage[key] = []
            
        # Add timestamp to data
        timestamped_data = {
            "data": data,
            "timestamp": datetime.now().isoformat(),
            "key": key
        }
        
        self.storage[key].append(timestamped_data)
        return True
    
    def retrieve(self, key: str, limit: int = 10) -> List[Any]:
        """
        Retrieves data from memory by key.
        
        Args:
            key (str): Key to retrieve data for
            limit (int): Maximum number of items to return
            
        Returns:
            List[Any]: List of stored data items
        """
        logger.info(f"Retrieving data from memory with key: {key}")
        
        if key in self.storage:
            # Return the most recent items first
            items = self.storage[key]
            # Sort by timestamp (newest first)
            sorted_items = sorted(items, key=lambda x: x["timestamp"], reverse=True)
            # Return just the data, not the metadata
            return [item["data"] for item in sorted_items[:limit]]
        
        return []
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Searches memory using semantic similarity.
        
        Args:
            query (str): Search query
            top_k (int): Number of results to return
            
        Returns:
            List[Dict[str, Any]]: List of relevant memory items
        """
        logger.info(f"Searching memory for: {query}")
        
        # In a real implementation, this would use embeddings to find semantically similar items
        # For now, we'll do a simple keyword search
        results = []
        
        query_words = set(query.lower().split())
        
        for key, items in self.storage.items():
            for item in items:
                # Simple keyword matching
                item_text = str(item["data"]).lower()
                item_words = set(item_text.split())
                
                # Calculate simple overlap score
                overlap = len(query_words.intersection(item_words))
                if overlap > 0:
                    results.append({
                        "key": key,
                        "data": item["data"],
                        "score": overlap,
                        "timestamp": item["timestamp"]
                    })
        
        # Sort by score (highest first)
        results.sort(key=lambda x: x["score"], reverse=True)
        
        return results[:top_k]
    
    def delete(self, key: str) -> bool:
        """
        Deletes data from memory by key.
        
        Args:
            key (str): Key to delete
            
        Returns:
            bool: True if successful
        """
        logger.info(f"Deleting data from memory with key: {key}")
        
        if key in self.storage:
            del self.storage[key]
            return True
        return False
    
    def get_all_keys(self) -> List[str]:
        """
        Gets all keys in memory.
        
        Returns:
            List[str]: List of all keys
        """
        return list(self.storage.keys())
    
    def clear(self) -> bool:
        """
        Clears all data from memory.
        
        Returns:
            bool: True if successful
        """
        logger.info("Clearing all data from memory")
        self.storage.clear()
        self.embeddings.clear()
        return True