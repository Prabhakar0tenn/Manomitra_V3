import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from config import settings

logger = logging.getLogger("study_hub.db")

class InMemoryCollection:
    def __init__(self):
        self._data = {}

    def insert_one(self, document):
        doc_id = document.get("document_id")
        self._data[doc_id] = dict(document)
        class InsertResult:
            inserted_id = doc_id
        return InsertResult()

    def find_one(self, filter_dict):
        doc_id = filter_dict.get("document_id")
        if not doc_id:
            for doc in self._data.values():
                match = True
                for k, v in filter_dict.items():
                    if doc.get(k) != v:
                        match = False
                        break
                if match:
                    return dict(doc)
            return None
        doc = self._data.get(doc_id)
        return dict(doc) if doc else None

    def find(self, filter_dict=None, projection=None):
        docs = []
        for doc in self._data.values():
            if filter_dict:
                match = True
                for k, v in filter_dict.items():
                    if doc.get(k) != v:
                        match = False
                        break
                if not match:
                    continue
            
            proj_doc = dict(doc)
            if projection:
                for k, v in projection.items():
                    if v == 0:
                        proj_doc.pop(k, None)
            docs.append(proj_doc)
        return docs

    def delete_one(self, filter_dict):
        doc_id = filter_dict.get("document_id")
        if doc_id in self._data:
            del self._data[doc_id]
            class DeleteResult:
                deleted_count = 1
            return DeleteResult()
        class DeleteResult:
            deleted_count = 0
        return DeleteResult()

class DatabaseManager:
    def __init__(self):
        self.client = None
        self.db = None
        self.mode = "in-memory"
        self._collections = {}
        self._init_db()

    def _init_db(self):
        # 1. Try MONGODB_URI first
        try:
            logger.info("Connecting to primary MongoDB URI...")
            self.client = MongoClient(settings.MONGODB_URI, serverSelectionTimeoutMS=2000)
            self.client.admin.command('ping')
            self.db = self.client.get_database("study_hub_db")
            self.mode = "connected"
            logger.info("Successfully connected to primary MongoDB Atlas.")
            return
        except Exception as e:
            logger.warning(f"Primary MongoDB connection failed: {e}")

        # 2. Try MONGODB_URI_FALLBACK
        try:
            logger.info("Connecting to fallback MongoDB URI...")
            self.client = MongoClient(settings.MONGODB_URI_FALLBACK, serverSelectionTimeoutMS=2000)
            self.client.admin.command('ping')
            self.db = self.client.get_database("study_hub_db")
            self.mode = "fallback"
            logger.info("Successfully connected to fallback MongoDB Atlas.")
            return
        except Exception as e:
            logger.warning(f"Fallback MongoDB connection failed: {e}")

        # 3. Use in-memory Python dict as fallback
        logger.error("Both MongoDB connections failed. Falling back to in-memory store.")
        self.mode = "in-memory"

    def get_collection(self, name: str):
        if self.mode in ("connected", "fallback"):
            return self.db[name]
        else:
            if name not in self._collections:
                self._collections[name] = InMemoryCollection()
            return self._collections[name]

db_manager = DatabaseManager()
