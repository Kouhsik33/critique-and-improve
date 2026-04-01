"""
Vector Store for memory and idea retrieval.
Uses FAISS for efficient similarity search.
"""

import os
import json
from typing import List, Optional, Dict, Any
import numpy as np
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.schema import Document
from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class VectorStoreSettings(BaseSettings):
    """Vector store configuration"""
    model_config = ConfigDict(extra="ignore", env_file=".env", case_sensitive=False)
    
    embedding_model: str = "text-embedding-3-small"
    vector_db_path: str = os.getenv("VECTOR_DB_PATH", "./data/vector_store")
    openai_api_key: Optional[str] = None


class MemoryStore:
    """
    Memory store for persisting and retrieving ideas, critiques, and insights.
    Uses FAISS for vector similarity search.
    """
    
    _instance: Optional["MemoryStore"] = None
    _vector_store: Optional[FAISS] = None
    _embedder: Optional[OpenAIEmbeddings] = None
    _settings: VectorStoreSettings = None
    _memory_index: Dict[str, Any] = {}  # Metadata for stored items
    
    def __new__(cls, settings: Optional[VectorStoreSettings] = None):
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize(settings or VectorStoreSettings())
        return cls._instance
    
    def _initialize(self, settings: VectorStoreSettings):
        """Initialize the memory store"""
        self._settings = settings
        self._embedder = OpenAIEmbeddings(
            model=settings.embedding_model,
            openai_api_key=settings.openai_api_key,
        )
        
        os.makedirs(settings.vector_db_path, exist_ok=True)
        
        # Try to load existing index
        index_path = os.path.join(settings.vector_db_path, "index")
        metadata_path = os.path.join(settings.vector_db_path, "metadata.json")
        
        if os.path.exists(index_path):
            try:
                self._vector_store = FAISS.load_local(index_path, self._embedder)
                if os.path.exists(metadata_path):
                    with open(metadata_path, "r") as f:
                        self._memory_index = json.load(f)
            except Exception as e:
                print(f"Failed to load existing FAISS index: {e}. Creating new.")
                self._vector_store = None
    
    def add_idea(
        self,
        idea: str,
        workflow_id: str,
        iteration: int,
        agent: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Add an idea to memory"""
        doc_id = f"{workflow_id}_idea_{iteration}_{agent}"
        
        doc = Document(
            page_content=idea,
            metadata={
                "doc_id": doc_id,
                "type": "idea",
                "workflow_id": workflow_id,
                "iteration": iteration,
                "agent": agent,
                **(metadata or {}),
            },
        )
        
        if self._vector_store is None:
            self._vector_store = FAISS.from_documents([doc], self._embedder)
        else:
            self._vector_store.add_documents([doc])
        
        self._memory_index[doc_id] = doc.metadata
        self._save_metadata()
        return doc_id
    
    def add_critique(
        self,
        critique: str,
        workflow_id: str,
        iteration: int,
        severity: float,
        category: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Add a critique to memory"""
        doc_id = f"{workflow_id}_critique_{iteration}_{category}"
        
        doc = Document(
            page_content=critique,
            metadata={
                "doc_id": doc_id,
                "type": "critique",
                "workflow_id": workflow_id,
                "iteration": iteration,
                "severity": severity,
                "category": category,
                **(metadata or {}),
            },
        )
        
        if self._vector_store is None:
            self._vector_store = FAISS.from_documents([doc], self._embedder)
        else:
            self._vector_store.add_documents([doc])
        
        self._memory_index[doc_id] = doc.metadata
        self._save_metadata()
        return doc_id
    
    def search_similar_ideas(
        self,
        query: str,
        workflow_id: str,
        k: int = 5,
    ) -> List[Dict[str, Any]]:
        """Search for similar ideas"""
        if self._vector_store is None:
            return []
        
        try:
            results = self._vector_store.similarity_search_with_score(query, k=k)
            
            filtered_results = []
            for doc, score in results:
                if (
                    doc.metadata.get("type") == "idea"
                    and doc.metadata.get("workflow_id") == workflow_id
                ):
                    filtered_results.append({
                        "content": doc.page_content,
                        "similarity_score": 1 - score,  # Convert distance to similarity
                        "metadata": doc.metadata,
                    })
            
            return filtered_results
        except Exception as e:
            print(f"Error searching similar ideas: {e}")
            return []
    
    def search_relevant_critiques(
        self,
        idea: str,
        workflow_id: str,
        k: int = 10,
    ) -> List[Dict[str, Any]]:
        """Find relevant critiques for an idea"""
        if self._vector_store is None:
            return []
        
        try:
            results = self._vector_store.similarity_search_with_score(idea, k=k)
            
            filtered_results = []
            for doc, score in results:
                if (
                    doc.metadata.get("type") == "critique"
                    and doc.metadata.get("workflow_id") == workflow_id
                ):
                    filtered_results.append({
                        "content": doc.page_content,
                        "similarity_score": 1 - score,
                        "severity": doc.metadata.get("severity", 0),
                        "category": doc.metadata.get("category", "general"),
                        "metadata": doc.metadata,
                    })
            
            return sorted(filtered_results, key=lambda x: x["severity"], reverse=True)
        except Exception as e:
            print(f"Error searching critiques: {e}")
            return []
    
    def get_evolution_history(self, workflow_id: str) -> List[Dict[str, Any]]:
        """Get the evolution history of ideas in a workflow"""
        history = []
        for doc_id, metadata in self._memory_index.items():
            if metadata.get("workflow_id") == workflow_id:
                history.append(metadata)
        
        return sorted(history, key=lambda x: x.get("iteration", 0))
    
    def _save_metadata(self):
        """Persist metadata to disk"""
        if self._vector_store is None:
            return
        
        try:
            index_path = os.path.join(self._settings.vector_db_path, "index")
            self._vector_store.save_local(index_path)
            
            metadata_path = os.path.join(self._settings.vector_db_path, "metadata.json")
            with open(metadata_path, "w") as f:
                json.dump(self._memory_index, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving vector store: {e}")
    
    def clear(self):
        """Clear all memory"""
        self._vector_store = None
        self._memory_index = {}
        self._save_metadata()
