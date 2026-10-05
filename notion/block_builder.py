from typing import Any, Dict, List
import re


class BlockBuilder:
    """Helper class to build Notion blocks"""
    
    @staticmethod
    def _parse_inline_formatting(text: str) -> List[Dict[str, Any]]:
        """
        Parse inline markdown formatting (bold, italic, code, links) into rich_text segments
        
        Args:
            text: Text with inline markdown formatting
            
        Returns:
            List of rich_text objects for Notion API
        """
        rich_text = []
        pos = 0
        
        # Pattern to match: ***text***, **text**, *text*, `code`, or [link](url)
        # Order matters: match longer patterns first
        pattern = r'(\*\*\*(.+?)\*\*\*|\*\*(.+?)\*\*|\*(.+?)\*|`(.+?)`|\[([^\]]+)\]\(([^\)]+)\))'
        
        matches = list(re.finditer(pattern, text))
        
        for match in matches:
            # Add any text before this match as plain text
            if match.start() > pos:
                plain = text[pos:match.start()]
                if plain:
                    rich_text.append({
                        "type": "text",
                        "text": {"content": plain},
                        "annotations": {
                            "bold": False,
                            "italic": False,
                            "code": False
                        }
                    })
            
            # Determine what type of formatting this is
            full_match = match.group(0)
            
            if full_match.startswith('***'):  # Bold + Italic
                content = match.group(2)
                rich_text.append({
                    "type": "text",
                    "text": {"content": content},
                    "annotations": {
                        "bold": True,
                        "italic": True,
                        "code": False
                    }
                })
            elif full_match.startswith('**'):  # Bold
                content = match.group(3)
                rich_text.append({
                    "type": "text",
                    "text": {"content": content},
                    "annotations": {
                        "bold": True,
                        "italic": False,
                        "code": False
                    }
                })
            elif full_match.startswith('*'):  # Italic
                content = match.group(4)
                rich_text.append({
                    "type": "text",
                    "text": {"content": content},
                    "annotations": {
                        "bold": False,
                        "italic": True,
                        "code": False
                    }
                })
            elif full_match.startswith('`'):  # Inline code
                content = match.group(5)
                rich_text.append({
                    "type": "text",
                    "text": {"content": content},
                    "annotations": {
                        "bold": False,
                        "italic": False,
                        "code": True
                    }
                })
            elif full_match.startswith('['):  # Link
                link_text = match.group(6)
                link_url = match.group(7)
                rich_text.append({
                    "type": "text",
                    "text": {
                        "content": link_text,
                        "link": {"url": link_url}
                    },
                    "annotations": {
                        "bold": False,
                        "italic": False,
                        "code": False
                    }
                })
            
            pos = match.end()
        
        # Add any remaining text after the last match
        if pos < len(text):
            plain = text[pos:]
            if plain:
                rich_text.append({
                    "type": "text",
                    "text": {"content": plain},
                    "annotations": {
                        "bold": False,
                        "italic": False,
                        "code": False
                    }
                })
        
        # If no formatting found, return the whole text as plain
        if not rich_text:
            rich_text.append({
                "type": "text",
                "text": {"content": text},
                "annotations": {
                    "bold": False,
                    "italic": False,
                    "code": False
                }
            })
        
        return rich_text
    
    @staticmethod
    def paragraph(text: str, bold: bool = False, italic: bool = False, 
                  color: str = "default", parse_formatting: bool = False) -> Dict[str, Any]:
        """
        Create a paragraph block
        
        Args:
            text: Text content
            bold: Apply bold to entire text (ignored if parse_formatting=True)
            italic: Apply italic to entire text (ignored if parse_formatting=True)
            color: Text color
            parse_formatting: If True, parse inline markdown formatting
        """
        if parse_formatting:
            rich_text = BlockBuilder._parse_inline_formatting(text)
        else:
            rich_text = [{
                "type": "text",
                "text": {"content": text},
                "annotations": {
                    "bold": bold,
                    "italic": italic,
                    "color": color
                }
            }]
        
        return {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": rich_text,
                "color": color
            }
        }
    
    @staticmethod
    def heading(text: str, level: int = 1, parse_formatting: bool = False) -> Dict[str, Any]:
        """
        Create a heading block (level 1, 2, or 3)
        
        Args:
            text: Heading text
            level: Heading level (1, 2, or 3)
            parse_formatting: If True, parse inline markdown formatting
        """
        heading_type = f"heading_{level}"
        
        if parse_formatting:
            rich_text = BlockBuilder._parse_inline_formatting(text)
        else:
            rich_text = [{
                "type": "text",
                "text": {"content": text}
            }]
        
        return {
            "object": "block",
            "type": heading_type,
            heading_type: {
                "rich_text": rich_text
            }
        }
    
    @staticmethod
    def bulleted_list_item(text: str, parse_formatting: bool = False) -> Dict[str, Any]:
        """
        Create a bulleted list item
        
        Args:
            text: List item text
            parse_formatting: If True, parse inline markdown formatting
        """
        if parse_formatting:
            rich_text = BlockBuilder._parse_inline_formatting(text)
        else:
            rich_text = [{
                "type": "text",
                "text": {"content": text}
            }]
        
        return {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": rich_text
            }
        }
    
    @staticmethod
    def numbered_list_item(text: str, parse_formatting: bool = False) -> Dict[str, Any]:
        """
        Create a numbered list item
        
        Args:
            text: List item text
            parse_formatting: If True, parse inline markdown formatting
        """
        if parse_formatting:
            rich_text = BlockBuilder._parse_inline_formatting(text)
        else:
            rich_text = [{
                "type": "text",
                "text": {"content": text}
            }]
        
        return {
            "object": "block",
            "type": "numbered_list_item",
            "numbered_list_item": {
                "rich_text": rich_text
            }
        }
    
    @staticmethod
    def to_do(text: str, checked: bool = False, parse_formatting: bool = False) -> Dict[str, Any]:
        """
        Create a to-do item
        
        Args:
            text: Todo text
            checked: Whether the todo is checked
            parse_formatting: If True, parse inline markdown formatting
        """
        if parse_formatting:
            rich_text = BlockBuilder._parse_inline_formatting(text)
        else:
            rich_text = [{
                "type": "text",
                "text": {"content": text}
            }]
        
        return {
            "object": "block",
            "type": "to_do",
            "to_do": {
                "rich_text": rich_text,
                "checked": checked
            }
        }
    
    @staticmethod
    def code(code: str, language: str = "python") -> Dict[str, Any]:
        """Create a code block"""
        return {
            "object": "block",
            "type": "code",
            "code": {
                "rich_text": [{
                    "type": "text",
                    "text": {"content": code}
                }],
                "language": language
            }
        }
    
    @staticmethod
    def quote(text: str, parse_formatting: bool = False) -> Dict[str, Any]:
        """
        Create a quote block
        
        Args:
            text: Quote text
            parse_formatting: If True, parse inline markdown formatting
        """
        if parse_formatting:
            rich_text = BlockBuilder._parse_inline_formatting(text)
        else:
            rich_text = [{
                "type": "text",
                "text": {"content": text}
            }]
        
        return {
            "object": "block",
            "type": "quote",
            "quote": {
                "rich_text": rich_text
            }
        }
    
    @staticmethod
    def callout(text: str, icon: str = "💡", color: str = "gray_background", 
                parse_formatting: bool = False) -> Dict[str, Any]:
        """
        Create a callout block
        
        Args:
            text: Callout text
            icon: Emoji icon
            color: Background color
            parse_formatting: If True, parse inline markdown formatting
        """
        if parse_formatting:
            rich_text = BlockBuilder._parse_inline_formatting(text)
        else:
            rich_text = [{
                "type": "text",
                "text": {"content": text}
            }]
        
        return {
            "object": "block",
            "type": "callout",
            "callout": {
                "rich_text": rich_text,
                "icon": {"type": "emoji", "emoji": icon},
                "color": color
            }
        }
    
    @staticmethod
    def divider() -> Dict[str, Any]:
        """Create a divider block"""
        return {
            "object": "block",
            "type": "divider",
            "divider": {}
        }
    
    @staticmethod
    def toggle(text: str, children: List[Dict[str, Any]] = None, 
               parse_formatting: bool = False) -> Dict[str, Any]:
        """
        Create a toggle block
        
        Args:
            text: Toggle text
            children: Child blocks
            parse_formatting: If True, parse inline markdown formatting
        """
        if parse_formatting:
            rich_text = BlockBuilder._parse_inline_formatting(text)
        else:
            rich_text = [{
                "type": "text",
                "text": {"content": text}
            }]
        
        block = {
            "object": "block",
            "type": "toggle",
            "toggle": {
                "rich_text": rich_text
            }
        }
        if children:
            block["toggle"]["children"] = children
        return block
    
    @staticmethod
    def bookmark(url: str) -> Dict[str, Any]:
        """Create a bookmark block"""
        return {
            "object": "block",
            "type": "bookmark",
            "bookmark": {
                "url": url
            }
        }
