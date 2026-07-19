from typing import Dict, Any, List
from pydantic import BaseModel, Field
import numpy as np
import os
import asyncio
from .document_store import document_store
from .embedder import embedder
