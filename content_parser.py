#!/usr/bin/env python3
"""
Content Parser for Alex Orator Bot
Parses and processes bot content from various sources
"""

import re
import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime


class ContentParser:
    """Parser for bot content files"""
    
    def __init__(self, content_dir: str = "texts"):
        self.content_dir = content_dir
        self.content_cache = {}
        
    def parse_text_file(self, filename: str) -> Dict[str, Any]:
        """Parse text file with bot content"""
        filepath = os.path.join(self.content_dir, filename)
        
        if not os.path.exists(filepath):
            return {}
            
        content = {}
        current_section = None
        current_key = None
        
        with open(filepath, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                
                if not line or line.startswith('#'):
                    continue
                    
                # Section header
                if line.startswith('##'):
                    current_section = line[2:].strip()
                    content[current_section] = {}
                    current_key = None
                    
                # Key-value pair
                elif ':' in line and current_section:
                    try:
                        key, value = line.split(':', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        if current_key and current_key in content[current_section]:
                            # Multi-line value
                            content[current_section][current_key] += f"\n{value}"
                        else:
                            content[current_section][key] = value
                            current_key = key
                            
                    except ValueError:
                        continue
                        
        return content
        
    def parse_json_file(self, filename: str) -> Dict[str, Any]:
        """Parse JSON file with bot content"""
        filepath = os.path.join(self.content_dir, filename)
        
        if not os.path.exists(filepath):
            return {}
            
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error parsing {filename}: {e}")
            return {}
            
    def get_content(self, content_type: str, key: str = None) -> Any:
        """Get content by type and optional key"""
        if content_type not in self.content_cache:
            if content_type == "messages":
                self.content_cache[content_type] = self.parse_text_file("bot_messages.txt")
            elif content_type == "exercises":
                self.content_cache[content_type] = self.parse_json_file("exercises.json")
            elif content_type == "topics":
                self.content_cache[content_type] = self.parse_json_file("topics.json")
            else:
                return None
                
        content = self.content_cache[content_type]
        
        if key:
            return content.get(key)
        return content
        
    def validate_content(self, content: Dict[str, Any]) -> List[str]:
        """Validate content structure and return errors"""
        errors = []
        
        required_fields = {
            "messages": ["welcome", "help", "error"],
            "exercises": ["exercises"],
            "topics": ["topics"]
        }
        
        for content_type, fields in required_fields.items():
            if content_type in content:
                for field in fields:
                    if field not in content[content_type]:
                        errors.append(f"Missing required field: {content_type}.{field}")
                        
        return errors
        
    def export_content(self, content_type: str, format: str = "json") -> str:
        """Export content in specified format"""
        content = self.get_content(content_type)
        
        if format == "json":
            return json.dumps(content, ensure_ascii=False, indent=2)
        elif format == "text":
            output = []
            for section, items in content.items():
                output.append(f"## {section}")
                if isinstance(items, dict):
                    for key, value in items.items():
                        output.append(f"{key}: {value}")
                output.append("")
            return "\n".join(output)
        else:
            raise ValueError(f"Unsupported format: {format}")


def main():
    """Test the content parser"""
    parser = ContentParser()
    
    # Test parsing different content types
    print("Testing Content Parser...")
    
    # Parse messages
    messages = parser.get_content("messages")
    print(f"Messages: {len(messages)} sections")
    
    # Parse exercises
    exercises = parser.get_content("exercises")
    print(f"Exercises: {len(exercises)} sections")
    
    # Parse topics
    topics = parser.get_content("topics")
    print(f"Topics: {len(topics)} sections")
    
    # Validate content
    all_content = {
        "messages": messages,
        "exercises": exercises,
        "topics": topics
    }
    
    errors = parser.validate_content(all_content)
    if errors:
        print("Validation errors:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("Content validation passed!")


if __name__ == "__main__":
    main()
