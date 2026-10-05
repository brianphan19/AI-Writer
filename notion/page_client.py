"""
notion_page_client.py - Comprehensive Notion Page API Client
Handles reading and writing to Notion pages with all block types
"""
from notion_client import Client
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

from config import NotionConfig

# Load environment variables
load_dotenv()


class NotionPageClient:
    """Client for working with Notion pages and all block types"""
    
    def __init__(self, notion_config: NotionConfig):
        """Initialize the Notion client"""
        self.token = notion_config.notion_token
        if not self.token:
            raise ValueError("NOTION_TOKEN is required")
        self.main_page_id = notion_config.chapters_page_id
        self.notion = Client(auth=self.token)
    
    # ========== PAGE OPERATIONS ==========
    
    def get_page(self, page_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get page metadata and properties
        
        Args:
            page_id: The page ID
            
        Returns:
            Page object with metadata
        """
        try:
            page_id = page_id or self.main_page_id
            page = self.notion.pages.retrieve(page_id=page_id)
            return page
        except Exception as e:
            print(f"Error getting page: {e}")
            raise
    
    def get_page_content(self, page_id: Optional[str] = None, recursive: bool = False) -> List[Dict[str, Any]]:
        """
        Get all blocks (content) from a page
        
        Args:
            page_id: The page ID
            recursive: If True, recursively fetch content of child blocks
            
        Returns:
            List of block objects
        """
        try:
            blocks = []
            has_more = True
            start_cursor = None
            page_id = page_id or self.main_page_id

            while has_more:
                response = self.notion.blocks.children.list(
                    block_id=page_id,
                    start_cursor=start_cursor
                )
                blocks.extend(response.get("results", []))
                has_more = response.get("has_more", False)
                start_cursor = response.get("next_cursor")
            
            # If recursive, get children of blocks that have children
            if recursive:
                for block in blocks:
                    if block.get("has_children"):
                        block["children"] = self.get_page_content(block["id"], recursive=True)
            
            return blocks
        except Exception as e:
            print(f"Error getting page content: {e}")
            raise
    
    def create_page(
        self,
        parent_id: str,
        title: str,
        content: Optional[List[Dict[str, Any]]] = None,
        icon: Optional[str] = None,
        cover: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new page as a child of another page
        
        Args:
            parent_id: Parent page ID
            title: Page title
            content: List of blocks to add as content
            icon: Emoji icon (e.g., "📄")
            cover: Cover image URL
            
        Returns:
            Created page object
        """
        try:
            page_data = {
                "parent": {"page_id": parent_id},
                "properties": {
                    "title": {
                        "title": [{"text": {"content": title}}]
                    }
                }
            }
            
            if icon:
                page_data["icon"] = {"type": "emoji", "emoji": icon}
            
            if cover:
                page_data["cover"] = {"type": "external", "external": {"url": cover}}
            
            if content:
                page_data["children"] = content
            
            page = self.notion.pages.create(**page_data)
            return page
        except Exception as e:
            print(f"Error creating page: {e}")
            raise
    
    def append_blocks(self, page_id: Optional[str] = None, blocks: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Append blocks to a page
        
        Args:
            page_id: The page ID
            blocks: List of blocks to append
            
        Returns:
            Response object
        """
        try:
            page_id = page_id or self.main_page_id
            response = self.notion.blocks.children.append(
                block_id=page_id,
                children=blocks
            )
            return response
        except Exception as e:
            print(f"Error appending blocks: {e}")
            raise
    
    def update_block(self, block_id: str, block_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing block
        
        Args:
            block_id: The block ID
            block_data: New block data
            
        Returns:
            Updated block object
        """
        try:
            block = self.notion.blocks.update(block_id=block_id, **block_data)
            return block
        except Exception as e:
            print(f"Error updating block: {e}")
            raise
    
    def delete_block(self, block_id: str) -> Dict[str, Any]:
        """
        Delete (archive) a block
        
        Args:
            block_id: The block ID
            
        Returns:
            Deleted block object
        """
        try:
            block = self.notion.blocks.delete(block_id=block_id)
            return block
        except Exception as e:
            print(f"Error deleting block: {e}")
            raise
    
    # ========== CONTENT EXTRACTION ==========
    
    def extract_text_from_page(self, page_id: Optional[str] = None) -> str:
        """
        Extract all text content from a page as plain text
        
        Args:
            page_id: The page ID
            
        Returns:
            Plain text content
        """
        page_id = page_id or self.main_page_id
        blocks = self.get_page_content(page_id)
        text_parts = []

        for block in blocks:
            block_type = block.get("type")
            
            # Extract text from different block types
            if block_type in ["paragraph", "heading_1", "heading_2", "heading_3", 
                             "bulleted_list_item", "numbered_list_item", "to_do", "quote", "callout"]:
                rich_text = block[block_type].get("rich_text", [])
                text = self._extract_plain_text(rich_text)
                if text:
                    text_parts.append(text)
            
            elif block_type == "code":
                rich_text = block[block_type].get("rich_text", [])
                code = self._extract_plain_text(rich_text)
                if code:
                    text_parts.append(f"Code:\n{code}")
            
            elif block_type == "child_page":
                title = block.get("child_page", {}).get("title", "Untitled")
                text_parts.append(f"[Sub-page: {title}]")
        
        return "\n\n".join(text_parts)
    
    def _extract_plain_text(self, rich_text: List[Dict[str, Any]]) -> str:
        """Extract plain text from rich_text array"""
        return "".join([rt.get("plain_text", "") for rt in rich_text])
    
    def parse_page_structure(self, page_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Parse page into structured format showing all block types
        
        Args:
            page_id: The page ID
            
        Returns:
            Structured representation of the page
        """
        page_id = page_id or self.main_page_id
        page = self.get_page(page_id)
        blocks = self.get_page_content(page_id, recursive=True)
        
        return {
            "page_id": page_id,
            "title": self._get_page_title(page),
            "created_time": page.get("created_time"),
            "last_edited_time": page.get("last_edited_time"),
            "blocks": self._parse_blocks(blocks)
        }
    
    def _get_page_title(self, page: Dict[str, Any]) -> str:
        """Extract page title"""
        properties = page.get("properties", {})
        title_prop = properties.get("title", {})
        title_array = title_prop.get("title", [])
        if title_array:
            return "".join([t.get("plain_text", "") for t in title_array])
        return "Untitled"
    
    def _parse_blocks(self, blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse blocks into simplified structure"""
        parsed = []
        
        for block in blocks:
            block_type = block.get("type")
            block_id = block.get("id")
            
            parsed_block = {
                "id": block_id,
                "type": block_type,
                "has_children": block.get("has_children", False)
            }
            
            # Parse content based on block type
            if block_type == "paragraph":
                parsed_block["text"] = self._extract_plain_text(block["paragraph"].get("rich_text", []))
            
            elif block_type in ["heading_1", "heading_2", "heading_3"]:
                parsed_block["text"] = self._extract_plain_text(block[block_type].get("rich_text", []))
            
            elif block_type in ["bulleted_list_item", "numbered_list_item"]:
                parsed_block["text"] = self._extract_plain_text(block[block_type].get("rich_text", []))
            
            elif block_type == "to_do":
                parsed_block["text"] = self._extract_plain_text(block["to_do"].get("rich_text", []))
                parsed_block["checked"] = block["to_do"].get("checked", False)
            
            elif block_type == "toggle":
                parsed_block["text"] = self._extract_plain_text(block["toggle"].get("rich_text", []))
            
            elif block_type == "code":
                parsed_block["language"] = block["code"].get("language", "plain text")
                parsed_block["text"] = self._extract_plain_text(block["code"].get("rich_text", []))
            
            elif block_type == "quote":
                parsed_block["text"] = self._extract_plain_text(block["quote"].get("rich_text", []))
            
            elif block_type == "callout":
                parsed_block["text"] = self._extract_plain_text(block["callout"].get("rich_text", []))
                parsed_block["icon"] = block["callout"].get("icon", {})
            
            elif block_type == "divider":
                parsed_block["text"] = "---"
            
            elif block_type == "table_of_contents":
                parsed_block["text"] = "[Table of Contents]"
            
            elif block_type == "child_page":
                parsed_block["title"] = block["child_page"].get("title", "Untitled")
            
            elif block_type == "image":
                image_data = block["image"]
                if image_data.get("type") == "external":
                    parsed_block["url"] = image_data["external"].get("url")
                elif image_data.get("type") == "file":
                    parsed_block["url"] = image_data["file"].get("url")
            
            elif block_type == "bookmark":
                parsed_block["url"] = block["bookmark"].get("url")
            
            elif block_type == "link_preview":
                parsed_block["url"] = block["link_preview"].get("url")
            
            # Add children if they exist
            if "children" in block:
                parsed_block["children"] = self._parse_blocks(block["children"])
            
            parsed.append(parsed_block)
        
        return parsed
    
    # ========== DISPLAY HELPERS ==========
    
    def print_page_structure(self, page_id: Optional[str] = None):
        """Print page structure in a readable format"""
        page_id = page_id or self.main_page_id
        structure = self.parse_page_structure(page_id)
        
        print(f"\n📄 Page: {structure['title']}")
        print(f"   ID: {structure['page_id']}")
        print(f"   Created: {structure['created_time']}")
        print(f"   Last Edited: {structure['last_edited_time']}")
        print("\n" + "="*60 + "\n")
        
        self._print_blocks(structure['blocks'])
    
    def _print_blocks(self, blocks: List[Dict[str, Any]], indent: int = 0):
        """Recursively print blocks with proper indentation"""
        for block in blocks:
            prefix = "  " * indent
            block_type = block['type']
            
            if block_type == "heading_1":
                print(f"{prefix}# {block.get('text', '')}")
            elif block_type == "heading_2":
                print(f"{prefix}## {block.get('text', '')}")
            elif block_type == "heading_3":
                print(f"{prefix}### {block.get('text', '')}")
            elif block_type == "paragraph":
                print(f"{prefix}{block.get('text', '')}")
            elif block_type == "bulleted_list_item":
                print(f"{prefix}• {block.get('text', '')}")
            elif block_type == "numbered_list_item":
                print(f"{prefix}1. {block.get('text', '')}")
            elif block_type == "to_do":
                checkbox = "☑" if block.get('checked') else "☐"
                print(f"{prefix}{checkbox} {block.get('text', '')}")
            elif block_type == "code":
                lang = block.get('language', 'text')
                print(f"{prefix}```{lang}")
                print(f"{prefix}{block.get('text', '')}")
                print(f"{prefix}```")
            elif block_type == "quote":
                print(f"{prefix}> {block.get('text', '')}")
            elif block_type == "callout":
                print(f"{prefix}💡 {block.get('text', '')}")
            elif block_type == "divider":
                print(f"{prefix}---")
            elif block_type == "child_page":
                print(f"{prefix}📄 Sub-page: {block.get('title', 'Untitled')}")
            elif block_type == "image":
                print(f"{prefix}🖼️ Image: {block.get('url', '')}")
            elif block_type == "bookmark":
                print(f"{prefix}🔗 Bookmark: {block.get('url', '')}")
            else:
                print(f"{prefix}[{block_type}]")
            
            # Print children if they exist
            if block.get('children'):
                self._print_blocks(block['children'], indent + 1)
