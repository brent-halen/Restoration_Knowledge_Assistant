import logging
from pathlib import Path

from langchain_chroma import Chroma
from langchain_community.document_loaders import TextLoader
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.config import get_settings


logger = logging.getLogger(__name__)
ROOT_DIR = Path(__file__).resolve().parent.parent
KNOWLEDGE_DIR = ROOT_DIR / "data" / "knowledge"


def infer_damage_type(filename: str) -> str:
    name = filename.lower()
    if "water" in name:
        return "water_damage"
    if "mold" in name:
        return "mold"
    if "fire" in name or "smoke" in name:
        return "fire_damage"
    return "general"


def load_seed_documents():
    docs = []
    for path in sorted(KNOWLEDGE_DIR.glob("*.md")):
        loader = TextLoader(str(path), encoding="utf-8")
        loaded = loader.load()
        for doc in loaded:
            doc.metadata.update(
                {
                    "source": path.name,
                    "damage_type": infer_damage_type(path.name),
                }
            )
        docs.extend(loaded)
    logger.info("Loaded %s seeded knowledge documents", len(docs))
    return docs


def build_vectorstore(force_rebuild: bool = False) -> Chroma:
    settings = get_settings()
    persist_dir = str(ROOT_DIR / settings.chroma_persist_dir)

    vectorstore = Chroma(
        collection_name=settings.collection_name,
        embedding_function=OpenAIEmbeddings(
            model=settings.embedding_model,
            api_key=settings.openai_api_key,
        ),
        persist_directory=persist_dir,
    )
    existing_count = vectorstore._collection.count()
    if existing_count > 0 and not force_rebuild:
        logger.info("Using existing Chroma collection with %s chunks", existing_count)
        return vectorstore

    docs = load_seed_documents()
    splitter = RecursiveCharacterTextSplitter(chunk_size=900, chunk_overlap=150)
    chunks = splitter.split_documents(docs)
    if existing_count > 0 and force_rebuild:
        vectorstore.delete(ids=vectorstore.get()["ids"])
    vectorstore.add_documents(chunks)
    logger.info("Indexed %s chunks into Chroma", len(chunks))
    return vectorstore
