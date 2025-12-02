"""History manager for chat conversation persistence."""

import json
import uuid
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from llm_chat.core.chat_client import Conversation, Message
from llm_chat.utils.logger import setup_logger


logger = setup_logger(__name__)


class HistoryManager:
    """Manages chat history persistence."""
    
    def __init__(self, history_file: Optional[str] = None):
        """Initialize the history manager.
        
        Args:
            history_file: Path to history file. Defaults to ~/.llm_chat/history.json
        """
        if history_file:
            self.history_file = Path(history_file)
        else:
            self.history_file = Path.home() / ".llm_chat" / "history.json"
        
        self._conversations: Dict[str, Conversation] = {}
        self._load()
    
    def _ensure_dir(self) -> None:
        """Ensure the history directory exists."""
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
    
    def _load(self) -> None:
        """Load history from file."""
        self._ensure_dir()
        
        if self.history_file.exists():
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                for conv_data in data.get("conversations", []):
                    conv = Conversation.from_dict(conv_data)
                    self._conversations[conv.id] = conv
                    
                logger.info(f"Loaded {len(self._conversations)} conversations from history")
            except (json.JSONDecodeError, KeyError) as e:
                logger.error(f"Failed to load history: {e}")
                self._conversations = {}
    
    def _save(self) -> None:
        """Save history to file."""
        self._ensure_dir()
        
        data = {
            "conversations": [conv.to_dict() for conv in self._conversations.values()]
        }
        
        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    
    def create_conversation(self, title: Optional[str] = None) -> Conversation:
        """Create a new conversation.
        
        Args:
            title: Optional title for the conversation.
            
        Returns:
            New Conversation object.
        """
        conv_id = str(uuid.uuid4())
        title = title or f"Conversation {len(self._conversations) + 1}"
        
        conversation = Conversation(id=conv_id, title=title)
        self._conversations[conv_id] = conversation
        self._save()
        
        logger.info(f"Created conversation: {conv_id}")
        return conversation
    
    def get_conversation(self, conv_id: str) -> Optional[Conversation]:
        """Get a conversation by ID.
        
        Args:
            conv_id: Conversation ID.
            
        Returns:
            Conversation or None if not found.
        """
        return self._conversations.get(conv_id)
    
    def list_conversations(self, limit: Optional[int] = None) -> List[Conversation]:
        """List all conversations.
        
        Args:
            limit: Optional limit on number of conversations to return.
            
        Returns:
            List of conversations, sorted by updated_at descending.
        """
        conversations = sorted(
            self._conversations.values(),
            key=lambda c: c.updated_at,
            reverse=True
        )
        
        if limit:
            return conversations[:limit]
        return conversations
    
    def add_message(self, conv_id: str, message: Message) -> None:
        """Add a message to a conversation.
        
        Args:
            conv_id: Conversation ID.
            message: Message to add.
        """
        if conv_id not in self._conversations:
            raise ValueError(f"Conversation not found: {conv_id}")
        
        self._conversations[conv_id].messages.append(message)
        self._conversations[conv_id].updated_at = datetime.now()
        self._save()
    
    def update_title(self, conv_id: str, title: str) -> None:
        """Update conversation title.
        
        Args:
            conv_id: Conversation ID.
            title: New title.
        """
        if conv_id not in self._conversations:
            raise ValueError(f"Conversation not found: {conv_id}")
        
        self._conversations[conv_id].title = title
        self._conversations[conv_id].updated_at = datetime.now()
        self._save()
    
    def delete_conversation(self, conv_id: str) -> None:
        """Delete a conversation.
        
        Args:
            conv_id: Conversation ID.
        """
        if conv_id in self._conversations:
            del self._conversations[conv_id]
            self._save()
            logger.info(f"Deleted conversation: {conv_id}")
    
    def clear_all(self) -> None:
        """Clear all conversations."""
        self._conversations.clear()
        self._save()
        logger.info("Cleared all conversations")
    
    def search(self, query: str) -> List[Conversation]:
        """Search conversations by content.
        
        Args:
            query: Search query.
            
        Returns:
            List of matching conversations.
        """
        query = query.lower()
        results = []
        
        for conv in self._conversations.values():
            # Search in title
            if query in conv.title.lower():
                results.append(conv)
                continue
            
            # Search in messages
            for msg in conv.messages:
                if query in msg.content.lower():
                    results.append(conv)
                    break
        
        return sorted(results, key=lambda c: c.updated_at, reverse=True)
    
    def export_conversation(self, conv_id: str, format: str = "json") -> str:
        """Export a conversation.
        
        Args:
            conv_id: Conversation ID.
            format: Export format ("json" or "text").
            
        Returns:
            Exported conversation as string.
        """
        conv = self.get_conversation(conv_id)
        if not conv:
            raise ValueError(f"Conversation not found: {conv_id}")
        
        if format == "json":
            return json.dumps(conv.to_dict(), indent=2)
        elif format == "text":
            lines = [f"# {conv.title}", f"Created: {conv.created_at}", ""]
            for msg in conv.messages:
                role = msg.role.capitalize()
                lines.append(f"**{role}**: {msg.content}")
                lines.append("")
            return "\n".join(lines)
        else:
            raise ValueError(f"Unknown export format: {format}")
