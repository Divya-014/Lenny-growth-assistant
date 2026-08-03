import uuid
from typing import Optional, List, Dict, Any
from supabase import create_client, Client
from app.config import settings
from app.utils.logger import logger

class SupabaseDBClient:
    """
    Reusable database client wrapper for Supabase PostgreSQL.
    Provides methods to query and persist session histories.
    """
    def __init__(self):
        self.client: Optional[Client] = None
        self.initialize()

    def initialize(self):
        """
        Initializes the Supabase client using configuration environment variables.
        """
        try:
            url = settings.SUPABASE_URL.strip()
            # Clean up potential suffix '/rest/v1/' if present to get root Supabase URL
            if url.endswith("/rest/v1/"):
                url = url.replace("/rest/v1/", "")
            
            key = settings.SUPABASE_KEY.strip()
            
            if url and key and "your-project-id" not in url:
                self.client = create_client(url, key)
                logger.info(f"Supabase client initialized successfully. Endpoint: {url}")
            else:
                logger.warning("Supabase URL or Key not set to valid values. Operations will bypass database.")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            self.client = None

    def _to_uuid(self, session_id: str) -> str:
        """
        Ensures the session_id is a valid UUID string.
        If it's not a valid UUID format, generates a deterministic UUID based on the string.
        """
        try:
            # Check if session_id is already a valid UUID
            val = uuid.UUID(session_id)
            return str(val)
        except ValueError:
            # Generate a deterministic UUID based on the session_id string
            deterministic_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, session_id)
            logger.debug(f"Converted string session_id '{session_id}' to UUID '{deterministic_uuid}'")
            return str(deterministic_uuid)

    def create_chat_session(self, title: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Creates a new chat session in the database.
        If session_id is provided, uses it (converted to UUID).
        """
        if not self.client:
            logger.warning("Supabase client not initialized. Returning mock session.")
            return {"id": session_id or str(uuid.uuid4()), "title": title}

        db_session_id = self._to_uuid(session_id) if session_id else str(uuid.uuid4())
        
        try:
            data = {
                "id": db_session_id,
                "title": title
            }
            # Insert into chat_sessions table
            response = self.client.table("chat_sessions").insert(data).execute()
            logger.info(f"Created chat session: {title} (ID: {db_session_id})")
            # Supabase response data is in response.data list
            if response.data:
                return response.data[0]
            return data
        except Exception as e:
            logger.error(f"Error creating chat session: {e}")
            # If the session already exists (e.g. conflict on ID), return existing session details or default
            try:
                existing = self.client.table("chat_sessions").select("*").eq("id", db_session_id).execute()
                if existing.data:
                    return existing.data[0]
            except Exception as select_err:
                logger.error(f"Could not retrieve existing session: {select_err}")
            return {"id": db_session_id, "title": title}

    def get_chat_sessions(self) -> List[Dict[str, Any]]:
        """
        Fetches all chat sessions from the database.
        """
        if not self.client:
            logger.warning("Supabase client not initialized. Returning empty session list.")
            return []

        try:
            response = self.client.table("chat_sessions").select("*").order("created_at", desc=True).execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching chat sessions: {e}")
            return []

    def save_message(self, session_id: str, role: str, content: str, model_used: str = "openai") -> Dict[str, Any]:
        """
        Saves a message in the chat history.
        Ensures the session_id is a valid UUID format before saving.
        """
        db_session_id = self._to_uuid(session_id)
        
        # Ensure session exists in the DB first before attaching a message to it.
        # If the session is new and this is the user's first query, name the session based on the query.
        if role == "user":
            title_preview = content[:40].strip() + ("..." if len(content) > 40 else "")
            self.create_chat_session(title=title_preview, session_id=session_id)
        else:
            self.create_chat_session(title=f"Chat session - {session_id}", session_id=session_id)

        if not self.client:
            logger.warning("Supabase client not initialized. Message bypass database save.")
            return {"session_id": db_session_id, "role": role, "content": content}

        try:
            data = {
                "session_id": db_session_id,
                "role": role,
                "content": content,
                "model_used": model_used
            }
            response = self.client.table("chat_messages").insert(data).execute()
            logger.info(f"Saved chat message. Session: {db_session_id} | Role: {role}")
            if response.data:
                return response.data[0]
            return data
        except Exception as e:
            logger.error(f"Error saving chat message: {e}")
            return {"session_id": db_session_id, "role": role, "content": content}

    def get_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves all messages for a given session.
        """
        db_session_id = self._to_uuid(session_id)
        
        if not self.client:
            logger.warning("Supabase client not initialized. Returning empty message history.")
            return []

        try:
            response = (
                self.client.table("chat_messages")
                .select("*")
                .eq("session_id", db_session_id)
                .order("created_at", desc=False)
                .execute()
            )
            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching chat messages for session {db_session_id}: {e}")
            return []

# Shared database client instance
supabase_db = SupabaseDBClient()
