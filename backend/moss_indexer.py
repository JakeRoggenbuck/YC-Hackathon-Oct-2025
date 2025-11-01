"""
Moss Indexer for Semantic Code Search

Indexes GitHub repositories and provides semantic search over source code.

Usage:
    # Index a repository
    python moss_indexer.py index https://github.com/owner/repo
    
    # Search indexed code
    python moss_indexer.py search owner-repo "your search query"
    
    # Index and search in one command
    python moss_indexer.py search-repo https://github.com/owner/repo "query"

    #Example commands:
        python moss_indexer.py search testdrivenio-fastapi-crud-async "POST endpoint validation"

Functions:
    index_github_repo() - Pull, chunk, and index a GitHub repository
    search_code() - Semantic search over indexed code
    create_moss_index() - Create Moss index from chunks
    load_moss_index() - Load index into memory
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Optional
from dotenv import load_dotenv
from inferedge_moss import MossClient, DocumentInfo
from puller import pull_and_chunk_repo, parse_github_url

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MOSS_PROJECT_ID = os.getenv('MOSS_PROJECT_ID')
MOSS_API_KEY = os.getenv('MOSS_API_KEY')
DEFAULT_EMBEDDING_MODEL = 'moss-minilm'


def _get_moss_client() -> MossClient:
    """
    Initialize and return a Moss client.
    
    Returns:
        MossClient instance
        
    Raises:
        ValueError: If credentials are not set
    """
    if not MOSS_PROJECT_ID or not MOSS_API_KEY:
        raise ValueError(
            "Moss credentials not found. Please set MOSS_PROJECT_ID and MOSS_API_KEY "
            "environment variables."
        )
    
    return MossClient(MOSS_PROJECT_ID, MOSS_API_KEY)


def _generate_index_name(github_url: str) -> str:
    """Generate clean index name from GitHub URL (format: owner-repo)."""
    owner, repo = parse_github_url(github_url)
    index_name = f"{owner}-{repo}".lower()
    index_name = ''.join(c if c.isalnum() or c == '-' else '-' for c in index_name)
    return index_name


async def create_moss_index(
    chunks: List[Dict[str, str]],
    index_name: str,
    embedding_model: str = DEFAULT_EMBEDDING_MODEL,
    skip_if_exists: bool = True
) -> str:
    """Create a Moss index from code chunks."""
    if not chunks:
        raise ValueError("Cannot create index from empty chunks list")
    
    client = _get_moss_client()
    
    logger.info(f"Creating Moss index: {index_name}")
    logger.info(f"  Chunks: {len(chunks)}, Model: {embedding_model}")
    
    try:
        if skip_if_exists:
            try:
                existing_indexes = await client.list_indexes()
                if index_name in existing_indexes:
                    logger.info(f"Index '{index_name}' already exists. Skipping creation.")
                    return index_name
            except Exception as e:
                logger.debug(f"Could not check existing indexes: {e}")
        
        docs = [DocumentInfo(id=chunk["id"], text=chunk["text"]) for chunk in chunks]
        
        await client.create_index(
            index_name=index_name,
            docs=docs,
            model_id=embedding_model
        )
        
        logger.info(f"Successfully created Moss index: {index_name}")
        return index_name
        
    except Exception as e:
        logger.error(f"Failed to create Moss index: {e}")
        raise RuntimeError(f"Moss index creation failed: {e}")


async def load_moss_index(index_name: str) -> bool:
    """Load an existing Moss index into memory."""
    client = _get_moss_client()
    
    logger.info(f"Loading Moss index: {index_name}")
    
    try:
        await client.load_index(index_name)
        logger.info(f"Successfully loaded index: {index_name}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to load Moss index '{index_name}': {e}")
        raise RuntimeError(f"Failed to load index: {e}")


async def search_code(
    index_name: str,
    query: str,
    top_k: int = 5,
    auto_load: bool = True
) -> List[Dict]:
    """
    Search for code using semantic similarity.
    
    Returns list of dicts with 'id', 'text', and 'score' keys.
    """
    client = _get_moss_client()
    
    logger.info(f"Searching index '{index_name}' for: '{query}'")
    
    try:
        if auto_load:
            try:
                await client.load_index(index_name)
                logger.debug(f"Index '{index_name}' loaded")
            except Exception as load_err:
                logger.debug(f"Index load skipped: {load_err}")
        
        results = await client.query(
            index_name=index_name,
            query=query,
            top_k=top_k
        )
        
        formatted_results = []
        if hasattr(results, 'docs'):
            for doc in results.docs[:top_k]:
                formatted_results.append({
                    'id': getattr(doc, 'id', 'unknown'),
                    'text': getattr(doc, 'text', ''),
                    'score': getattr(doc, 'score', 0.0)
                })
        
        logger.info(f"Found {len(formatted_results)} results")
        return formatted_results
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise RuntimeError(f"Moss search failed: {e}")


async def index_github_repo(
    github_url: str,
    max_files: int = 500,
    embedding_model: str = DEFAULT_EMBEDDING_MODEL,
    skip_if_exists: bool = True
) -> str:
    """
    Pull GitHub repo, chunk code, and create Moss index.
    
    Returns the index name for use with search_code().
    """
    logger.info(f"Starting GitHub repository indexing: {github_url}")
    
    index_name = _generate_index_name(github_url)
    logger.info(f"Index name: {index_name}")
    
    logger.info("Pulling and chunking repository...")
    chunks = pull_and_chunk_repo(github_url, max_files=max_files)
    
    if not chunks:
        raise ValueError(f"No code chunks extracted from repository: {github_url}")
    
    logger.info(f"Extracted {len(chunks)} code chunks")
    
    logger.info("Creating Moss index...")
    await create_moss_index(
        chunks=chunks,
        index_name=index_name,
        embedding_model=embedding_model,
        skip_if_exists=skip_if_exists
    )
    
    logger.info("Loading index into memory...")
    await load_moss_index(index_name)
    
    logger.info(f"Repository indexed successfully: {index_name}")
    
    return index_name


async def search_github_repo(
    github_url: str,
    query: str,
    top_k: int = 5,
    max_files: int = 500
) -> List[Dict]:
    """Index repository (if needed) and search in one call."""
    index_name = await index_github_repo(
        github_url=github_url,
        max_files=max_files,
        skip_if_exists=True
    )
    
    results = await search_code(
        index_name=index_name,
        query=query,
        top_k=top_k
    )
    
    return results


if __name__ == "__main__":
    import sys
    import asyncio
    import json
    
    async def main():
        if len(sys.argv) < 2:
            print("Usage: python moss_indexer.py <command> [args...]")
            print("\nCommands:")
            print("  index <github_url>                    - Index a repository")
            print("  search <index_name> <query>           - Search an indexed repo")
            print("  search-repo <github_url> <query>      - Index and search in one go")
            print("\nExamples:")
            print("  python moss_indexer.py index https://github.com/pallets/flask")
            print("  python moss_indexer.py search pallets-flask 'How to create routes?'")
            print("  python moss_indexer.py search-repo https://github.com/pallets/flask 'POST handler'")
            sys.exit(1)
        
        command = sys.argv[1]
        
        try:
            if command == "index":
                if len(sys.argv) < 3:
                    print("Error: Please provide GitHub URL")
                    sys.exit(1)
                
                github_url = sys.argv[2]
                index_name = await index_github_repo(github_url)
                print(f"\nSuccess! Index created: {index_name}")
                
            elif command == "search":
                if len(sys.argv) < 4:
                    print("Error: Please provide index name and query")
                    sys.exit(1)
                
                index_name = sys.argv[2]
                query = sys.argv[3]
                
                results = await search_code(index_name, query)
                
                print(f"\nSearch results for: '{query}'")
                print(f"Found {len(results)} matches\n")
                
                for i, result in enumerate(results, 1):
                    print(f"{i}. {result['id']}")
                    print(f"   Score: {result['score']:.3f}")
                    print(f"   Preview: {result['text'][:150]}...")
                    print()
                
            elif command == "search-repo":
                if len(sys.argv) < 4:
                    print("Error: Please provide GitHub URL and query")
                    sys.exit(1)
                
                github_url = sys.argv[2]
                query = sys.argv[3]
                
                results = await search_github_repo(github_url, query)
                
                print(f"\nSearch results for: '{query}'")
                print(f"Found {len(results)} matches\n")
                
                for i, result in enumerate(results, 1):
                    print(f"{i}. {result['id']}")
                    print(f"   Score: {result['score']:.3f}")
                    print(f"   Preview: {result['text'][:150]}...")
                    print()
            
            else:
                print(f"Unknown command: {command}")
                sys.exit(1)
                
        except Exception as e:
            logger.error(f"Error: {e}")
            sys.exit(1)
    
    asyncio.run(main())

