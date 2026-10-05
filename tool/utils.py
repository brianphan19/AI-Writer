from pathlib import Path
from datetime import datetime


def load_prompt_from_file(filename: str, prompts_dir: str = "prompts") -> str:
    """
    Load prompt text from file
    
    Args:
        filename: Name of the prompt file
        prompts_dir: Directory containing prompt files
        
    Returns:
        Prompt text content
    """
    prompt_path = Path(prompts_dir) / filename
    
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    
    with open(prompt_path, 'r', encoding='utf-8') as f:
        return f.read().strip()

def save_to_file(content: str, filename: str = None, output_dir: str = "outputs") -> str:
    """
    Save content to a text file
    
    Args:
        content: Text content to save
        filename: Optional filename (auto-generated if None)
        output_dir: Directory to save files
        
    Returns:
        Path to saved file
    """
    # Create output directory if it doesn't exist
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Generate filename if not provided
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"chapter_{timestamp}.md"
    
    # Ensure .txt extension
    if not filename.endswith('.md'):
        filename += '.md'
    
    # Full file path
    file_path = output_path / filename
    
    # Write to file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return str(file_path)