"""
story_context.py - Story context manager for AI writing
Fetches recent chapters from Notion and builds context for LLM
"""

import re
from typing import List, Dict, Any, Optional
from .page_client import NotionPageClient
from .block_builder import BlockBuilder

def get_child_pages(client:NotionPageClient, parent_id: Optional[str] = None) -> List[Dict[str, str]]:
    """
    Get all child pages (chapters) from a parent page
    
    Args:
        parent_id: Parent page ID (uses main_page_id if None)
        
    Returns:
        List of dicts with page id, title, and created time
    """
    parent_id = parent_id or client.main_page_id
    blocks = client.get_page_content(parent_id)
    
    chapters = []
    for block in blocks:
        if block.get("type") == "child_page":
            chapters.append({
                "id": block["id"],
                "title": block.get("child_page", {}).get("title", "Untitled"),
                "created_time": block.get("created_time")
            })
    
    return chapters

class StoryContext:
    """Manages story context from Notion for AI generation"""
    
    def __init__(self, notion_client: NotionPageClient):
        """
        Initialize with existing NotionPageClient
        
        Args:
            notion_client: Configured NotionPageClient instance
        """
        self.client = notion_client
    
    def get_chapter_content(self, page_id: str) -> Dict[str, any]:
        """
        Get a single chapter's content
        
        Args:
            page_id: Notion page ID of the chapter
            
        Returns:
            Dict with title and content
        """
        try:
            # Get page metadata
            page = self.client.get_page(page_id)
            title = self.client._get_page_title(page)
            
            # Get content
            content = self.client.extract_text_from_page(page_id)
            
            return {
                "id": page_id,
                "title": title,
                "content": content,
                "created_time": page.get("created_time"),
                "last_edited_time": page.get("last_edited_time")
            }
        except Exception as e:
            print(f"Error getting chapter {page_id}: {e}")
            return None
       
    def get_recent_chapters(
        self, 
        parent_id: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, any]]:
        """
        Get recent chapters with full content
        
        Args:
            parent_id: Parent page containing chapters
            limit: Number of recent chapters to fetch
            
        Returns:
            List of chapter dicts with content
        """
        # Get all child pages
        child_pages =  get_child_pages(client=self.client, parent_id=parent_id)
        
        # Sort by created time (most recent first)
        child_pages.sort(
            key=lambda x: x.get("created_time", ""), 
            reverse=False
        )
        
        # Get content for recent chapters
        recent_chapters = []
        for page_info in child_pages[-limit:]:
            chapter = self.get_chapter_content(page_info["id"])
            if chapter:
                recent_chapters.append(chapter)
        
        return recent_chapters
    
    def build_full_context(
        self, 
        parent_id: Optional[str] = None,
        num_chapters: int = 5
    ) -> str:
        """
        Build full context string with all recent chapters
        
        Args:
            parent_id: Parent page containing chapters
            num_chapters: Number of chapters to include
            
        Returns:
            Formatted context string
        """

        chapters = self.get_recent_chapters(parent_id, limit=num_chapters)
        
        if not chapters:
            return "No previous chapters found."
        
        context_parts = ["=== Story Context: Recent Chapters ===\n"]
        
        for chapter in enumerate(chapters, 1):
            context_parts.append(f"\n# {chapter[1]['title']} ")
            context_parts.append(chapter[1]['content'])
            context_parts.append("")  # Blank line
        
        return "\n".join(context_parts)
    
    def build_hybrid_context(
        self,
        parent_id: Optional[str] = None,
        num_chapters: int = 5
    ) -> str:
        """
        Build smart context: full latest + previews of older chapters
        
        Args:
            parent_id: Parent page containing chapters
            num_chapters: Total number of chapters to include
            
        Returns:
            Formatted context string
        """
        chapters = self.get_recent_chapters(parent_id, limit=num_chapters)
        
        if not chapters:
            return "No previous chapters found."
        
        context_parts = ["=== Story Context ===\n"]
        
        # Full content of most recent chapter
        if chapters:
            latest = chapters[0]
            context_parts.append(f"=== Latest Chapter: {latest['title']} ===")
            context_parts.append(latest['content'])
            context_parts.append("\n")
        
        # Previews of older chapters
        if len(chapters) > 1:
            context_parts.append("=== Previous Chapters (Summaries) ===\n")
            
            for chapter in chapters[1:]:
                # Get first 500 characters as preview
                preview = chapter['content'][:500]
                if len(chapter['content']) > 500:
                    preview += "..."
                
                context_parts.append(f"**{chapter['title']}**:")
                context_parts.append(preview)
                context_parts.append("")  # Blank line
        
        return "\n".join(context_parts)
    
    def get_context_for_generation(
        self,
        parent_id: Optional[str] = None,
        strategy: str = "full",
        num_chapters: int = 5
    ) -> str:
        """
        Get context optimized for AI generation
        
        Args:
            parent_id: Parent page containing chapters
            strategy: "full" or "hybrid" 
            num_chapters: Number of chapters to include
            
        Returns:
            Context string ready for LLM
        """
        chapters = get_child_pages(client=self.client, parent_id=parent_id)
        chapters_page = None

        total_context = ["=== Story Setting ===\n"]
        for chapter in chapters:
            if chapter["title"] == "Setting":
                setting_page = chapter['id']
            if chapter['title'] == 'Chapters':
                chapters_page = chapter['id']
        total_context.append(self.build_full_context(setting_page, 2))

        if strategy == "full":
            total_context.append(self.build_full_context(chapters_page, num_chapters))
        else:
            total_context.append(self.build_hybrid_context(chapters_page, num_chapters))
        return "\n".join(total_context)
    

class MarkdownToNotionConverter:
    """Convert Markdown content to Notion blocks"""
    
    def __init__(self, notion_client: NotionPageClient):
        self.client = notion_client
        self.block_builder = BlockBuilder()
    def parse_markdown_to_blocks(self, markdown: str) -> List[Dict[str, Any]]:
        """
        Parse Markdown text into Notion blocks
        
        Args:
            markdown: Markdown formatted text
            
        Returns:
            List of Notion block objects
        """
        blocks = []
        lines = markdown.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Skip empty lines
            if not line.strip():
                i += 1
                continue
            
            # Heading 1
            if line.startswith('# ') and not line.startswith('##'):
                text = line[2:].strip()
                blocks.append(self.block_builder.heading(text, level=1, parse_formatting=True))
                i += 1
            
            # Heading 2
            elif line.startswith('## ') and not line.startswith('###'):
                text = line[3:].strip()
                blocks.append(self.block_builder.heading(text, level=2, parse_formatting=True))
                i += 1
            
            # Heading 3
            elif line.startswith('### '):
                text = line[4:].strip()
                blocks.append(self.block_builder.heading(text, level=3, parse_formatting=True))
                i += 1
            
            # Code block
            elif line.startswith('```'):
                language = line[3:].strip() or 'plain text'
                code_lines = []
                i += 1
                
                while i < len(lines) and not lines[i].startswith('```'):
                    code_lines.append(lines[i])
                    i += 1
                
                code = '\n'.join(code_lines)
                blocks.append(self.block_builder.code(code, language))
                i += 1  # Skip closing ```
            
            # Quote
            elif line.startswith('> '):
                text = line[2:].strip()
                blocks.append(self.block_builder.quote(text, parse_formatting=True))
                i += 1
            
            # Bulleted list
            elif line.startswith('- ') or line.startswith('* '):
                text = line[2:].strip()
                blocks.append(self.block_builder.bulleted_list_item(text, parse_formatting=True))
                i += 1
            
            # Numbered list
            elif re.match(r'^\d+\.\s', line):
                text = re.sub(r'^\d+\.\s', '', line).strip()
                blocks.append(self.block_builder.numbered_list_item(text, parse_formatting=True))
                i += 1
            
            # Todo/Checkbox
            elif line.startswith('- [ ]') or line.startswith('- [x]'):
                checked = '[x]' in line or '[X]' in line
                text = line[5:].strip()
                blocks.append(self.block_builder.to_do(text, checked=checked, parse_formatting=True))
                i += 1
            
            # Horizontal rule
            elif line.strip() in ['---', '***', '___']:
                blocks.append(self.block_builder.divider())
                i += 1
            
            # Paragraph (default)
            else:
                text = line.strip()
                if text:
                    blocks.append(self.block_builder.paragraph(text, parse_formatting=True))
                i += 1
        
        return blocks
    
    def create_page_from_markdown(
        self,
        title: str,
        markdown_content: str,
        parent_id: Optional[str] = None,
        icon: Optional[str] = None,
        cover: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a new Notion page from Markdown content
        
        Args:
            parent_id: Parent page ID
            title: Page title
            markdown_content: Markdown formatted content
            icon: Emoji icon 
            cover: Cover image URL
            
        Returns:
            Created page object
        """
        try:
            # Convert markdown to blocks
            blocks = self.parse_markdown_to_blocks(markdown_content)
            
            if not parent_id:
                chapters = get_child_pages(client=self.client, parent_id=parent_id)
                for chapter in chapters:
                    if chapter["title"] == "Chapters":
                        parent_id = chapter['id']

            # Create the page
            page = self.client.create_page(
                parent_id=parent_id,
                title=title,
                content=blocks,
                icon=icon,
                cover=cover
            )
            
            print(f"   Successfully created page: {title}")
            print(f"   Page ID: {page['id']}")
            print(f"   Blocks created: {len(blocks)}")
            
            return page
        
        except Exception as e:
            print(f"Error creating page from markdown: {e}")
            raise
    
    def append_markdown_to_page(
        self,
        page_id: str,
        markdown_content: str
    ) -> Dict[str, Any]:
        """
        Append Markdown content to an existing page
        
        Args:
            page_id: Target page ID
            markdown_content: Markdown formatted content
            
        Returns:
            Response object
        """
        try:
            # Convert markdown to blocks
            blocks = self.parse_markdown_to_blocks(markdown_content)
            
            # Append to page
            response = self.client.append_blocks(page_id=page_id, blocks=blocks)
            
            print(f"  Successfully appended {len(blocks)} blocks to page")
            
            return response
        
        except Exception as e:
            print(f"  Error appending markdown to page: {e}")
            raise


