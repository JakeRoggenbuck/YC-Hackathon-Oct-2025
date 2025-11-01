"""
GitHub Repository Python Code Puller

Takes github link. Fetches the repo and parses and chunks the source files 
to be used by Moss agent and Convex agent.

Module Structure:
├── parse_github_url()           # Extract owner/repo from URL
├── fetch_python_files()         # Get all .py files from GitHub
├── parse_python_file()          # Use AST to extract functions/classes
├── create_chunks()              # Convert AST nodes to Moss-ready chunks
└── pull_and_chunk_repo()        # Main orchestrator function
"""

import ast
import os
import re
import logging
from typing import List, Dict, Tuple
from pathlib import Path
from github import Github, GithubException

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Directories to exclude from processing
EXCLUDED_DIRS = {
    'venv', '.venv', 'env', '.env',
    '__pycache__', '.git', '.github',
    'node_modules', 'dist', 'build',
    '.pytest_cache', '.tox', 'htmlcov',
    'site-packages'
}

# File patterns to exclude
EXCLUDED_EXTENSIONS = {'.pyc', '.pyo', '.pyd'}


def parse_github_url(url: str) -> Tuple[str, str]:
    """
    Extract owner and repo name from GitHub URL.
    
    Supports formats:
    - https://github.com/owner/repo
    - https://github.com/owner/repo.git
    - github.com/owner/repo
    - owner/repo
    
    Args:
        url: GitHub repository URL
        
    Returns:
        Tuple of (owner, repo_name)
        
    Raises:
        ValueError: If URL is invalid or cannot be parsed
    """
    # Remove trailing slashes and .git extension
    url = url.strip().rstrip('/').rstrip('.git')
    
    # Pattern to match GitHub URLs
    patterns = [
        r'github\.com/([^/]+)/([^/]+)',  # https://github.com/owner/repo
        r'^([^/]+)/([^/]+)$',             # owner/repo
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            owner, repo = match.groups()
            return owner, repo
    
    raise ValueError(f"Invalid GitHub URL: {url}. Expected format: https://github.com/owner/repo")


def _should_skip_path(file_path: str) -> bool:
    """
    Check if a file path should be skipped based on exclusion rules.
    
    Args:
        file_path: Path to check
        
    Returns:
        True if file should be skipped, False otherwise
    """
    path = Path(file_path)
    
    # Check if any parent directory is in excluded dirs
    for part in path.parts:
        if part in EXCLUDED_DIRS:
            return True
    
    # Check file extension
    if path.suffix in EXCLUDED_EXTENSIONS:
        return True
    
    # Skip files that aren't .py
    if path.suffix != '.py':
        return True
        
    return False


def fetch_python_files(owner: str, repo: str, max_files: int = 500) -> List[Tuple[str, str]]:
    """
    Fetch all Python files from a GitHub repository.
    
    Args:
        owner: Repository owner
        repo: Repository name
        max_files: Maximum number of files to fetch (default: 500)
        
    Returns:
        List of (file_path, file_content) tuples
        
    Raises:
        ValueError: If repository not found
        RuntimeError: If GitHub API rate limit exceeded
    """
    try:
        # Initialize GitHub client (public repos only, no auth needed)
        g = Github(os.getenv('GITHUB_TOKEN'))
        repository = g.get_repo(f"{owner}/{repo}")
        
        logger.info(f"Fetching Python files from {owner}/{repo}")
        
        python_files = []
        
        # Get all contents recursively
        contents = repository.get_contents("")
        
        while contents and len(python_files) < max_files:
            file_content = contents.pop(0)
            
            if file_content.type == "dir":
                # Skip excluded directories
                if file_content.path.split('/')[0] not in EXCLUDED_DIRS:
                    try:
                        contents.extend(repository.get_contents(file_content.path))
                    except GithubException as e:
                        logger.warning(f"Could not access directory {file_content.path}: {e}")
            else:
                # Check if this is a Python file we want to process
                if not _should_skip_path(file_content.path):
                    try:
                        # Decode file content
                        content = file_content.decoded_content.decode('utf-8')
                        python_files.append((file_content.path, content))
                        logger.debug(f"Fetched: {file_content.path}")
                        
                        if len(python_files) >= max_files:
                            logger.warning(f"Reached maximum file limit ({max_files}). Stopping fetch.")
                            break
                    except Exception as e:
                        logger.warning(f"Could not decode {file_content.path}: {e}")
        
        logger.info(f"Successfully fetched {len(python_files)} Python files")
        return python_files
        
    except GithubException as e:
        if e.status == 404:
            raise ValueError(f"Repository not found: {owner}/{repo}")
        elif e.status == 403:
            raise RuntimeError(f"GitHub API rate limit exceeded. Please try again later.")
        else:
            raise RuntimeError(f"GitHub API error: {e}")


def parse_python_file(content: str, file_path: str, repo_id: str) -> List[Dict[str, str]]:
    """
    Parse Python file using AST to extract functions and classes.
    
    Args:
        content: Raw file content
        file_path: Path to file in repository
        repo_id: Repository identifier (owner/repo)
        
    Returns:
        List of chunks with format: [{"id": str, "text": str}, ...]
        Returns empty list if file has syntax errors
    """
    chunks = []
    
    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        logger.warning(f"Syntax error in {file_path}: {e}. Skipping file.")
        return []
    
    lines = content.split('\n')
    
    for node in ast.walk(tree):
        chunk_text = None
        chunk_name = None
        chunk_type = None
        
        if isinstance(node, ast.FunctionDef):
            # Extract function definition
            chunk_type = "function"
            chunk_name = node.name
            start_line = node.lineno - 1
            end_line = node.end_lineno if node.end_lineno else start_line + 1
            
            # Get the complete function code including decorators
            function_lines = lines[start_line:end_line]
            chunk_text = '\n'.join(function_lines)
            
        elif isinstance(node, ast.ClassDef):
            # Extract class definition
            chunk_type = "class"
            chunk_name = node.name
            start_line = node.lineno - 1
            end_line = node.end_lineno if node.end_lineno else start_line + 1
            
            # Get the complete class code including decorators
            class_lines = lines[start_line:end_line]
            chunk_text = '\n'.join(class_lines)
        
        if chunk_text and chunk_name:
            # Create chunk ID
            chunk_id = f"{repo_id}:{file_path}:{chunk_name}"
            
            # Format chunk with context
            formatted_text = f"""# File: {file_path}
# {chunk_type.capitalize()}: {chunk_name}

{chunk_text}"""
            
            chunks.append({
                "id": chunk_id,
                "text": formatted_text
            })
    
    return chunks


def pull_and_chunk_repo(github_url: str, max_files: int = 500) -> List[Dict[str, str]]:
    """
    Main function to pull and chunk a GitHub repository.
    
    This is the primary entry point for pulling code from a GitHub repository
    and preparing it for Moss indexing.
    
    Args:
        github_url: Full GitHub repository URL
        max_files: Maximum number of Python files to process (default: 500)
        
    Returns:
        List of documents ready for Moss indexing
        Format: [{"id": str, "text": str}, ...]
        
    Raises:
        ValueError: If URL is invalid or repository not found
        RuntimeError: If GitHub API errors occur
        
    Example:
        >>> chunks = pull_and_chunk_repo("https://github.com/pallets/flask")
        >>> print(f"Generated {len(chunks)} code chunks")
        >>> # Pass directly to Moss:
        >>> # await client.createIndex('flask-repo', chunks, 'moss-minilm')
    """
    logger.info(f"Starting repository pull and chunk process for: {github_url}")
    
    # Parse the GitHub URL
    owner, repo = parse_github_url(github_url)
    repo_id = f"{owner}/{repo}"
    
    logger.info(f"Repository: {repo_id}")
    
    # Fetch all Python files
    python_files = fetch_python_files(owner, repo, max_files)
    
    if not python_files:
        logger.warning(f"No Python files found in repository {repo_id}")
        return []
    
    # Parse and chunk each file
    all_chunks = []
    files_processed = 0
    files_skipped = 0
    
    for file_path, content in python_files:
        chunks = parse_python_file(content, file_path, repo_id)
        
        if chunks:
            all_chunks.extend(chunks)
            files_processed += 1
            logger.debug(f"Processed {file_path}: {len(chunks)} chunks")
        else:
            files_skipped += 1
    
    logger.info(f"Processing complete:")
    logger.info(f"  - Files processed: {files_processed}")
    logger.info(f"  - Files skipped: {files_skipped}")
    logger.info(f"  - Total chunks generated: {len(all_chunks)}")
    
    return all_chunks


if __name__ == "__main__":
    # Example usage
    import sys
    import json
    from datetime import datetime
    
    if len(sys.argv) < 2:
        print("Usage: python puller.py <github_url> [output_file]")
        print("Example: python puller.py https://github.com/pallets/flask")
        print("Example: python puller.py https://github.com/pallets/flask output.json")
        sys.exit(1)
    
    url = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        chunks = pull_and_chunk_repo(url)
        print(f"\n Successfully generated {len(chunks)} code chunks")
        
        # Save to file if specified
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(chunks, f, indent=2, ensure_ascii=False)
            print(f" Output saved to: {output_file}")
        else:
            # Auto-generate filename based on repo name and timestamp
            owner, repo = parse_github_url(url)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            auto_filename = f"chunks_{owner}_{repo}_{timestamp}.json"
            with open(auto_filename, 'w', encoding='utf-8') as f:
                json.dump(chunks, f, indent=2, ensure_ascii=False)
            print(f" Output saved to: {auto_filename}")\
        
        print("\n First chunk example:")
        if chunks:
            print(f"ID: {chunks[0]['id']}")
            print(f"Text preview:\n{chunks[0]['text'][:300]}...")
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)