from __future__ import annotations

import re
import html
from typing import Optional


def clean_html_content(text: str) -> str:
    """Clean and validate HTML content for Telegram"""
    if not text:
        return ""
    
    # Remove any malformed HTML tags
    text = re.sub(r'<[^>]*$', '', text)  # Remove incomplete tags at end
    text = re.sub(r'^[^<]*>', '', text)  # Remove incomplete tags at start
    
    # Fix common HTML issues
    text = re.sub(r'<([^>]+)>([^<]*)<([^>]+)>', r'<\1>\2</\3>', text)  # Fix mismatched tags
    
    # Remove unsupported HTML tags and attributes
    unsupported_tags = ['script', 'style', 'iframe', 'object', 'embed', 'form', 'input', 'button']
    for tag in unsupported_tags:
        text = re.sub(f'<{tag}[^>]*>.*?</{tag}>', '', text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(f'<{tag}[^>]*/?>', '', text, flags=re.IGNORECASE)
    
    # Remove unsupported attributes
    text = re.sub(r'\s+class\s*=\s*["\'][^"\']*["\']', '', text)
    text = re.sub(r'\s+id\s*=\s*["\'][^"\']*["\']', '', text)
    text = re.sub(r'\s+style\s*=\s*["\'][^"\']*["\']', '', text)
    
    # Fix common Persian number issues
    text = re.sub(r'۰\.۳\)،', '0.3)', text)  # Fix the specific error
    text = re.sub(r'[۰-۹]', lambda m: str(ord(m.group()) - ord('۰')), text)  # Convert Persian numbers
    
    # Clean up extra spaces and newlines
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\n\s*\n', '\n', text)
    
    return text.strip()


def validate_telegram_html(text: str) -> tuple[bool, str]:
    """Validate HTML content for Telegram compatibility"""
    if not text:
        return True, text
    
    try:
        # Check for malformed tags
        open_tags = re.findall(r'<([^/>][^>]*)>', text)
        close_tags = re.findall(r'</([^>]+)>', text)
        
        # Check for self-closing tags
        self_closing = re.findall(r'<([^>]+)/>', text)
        
        # Check for unclosed tags
        tag_stack = []
        for tag in open_tags:
            if not tag.endswith('/'):
                tag_name = tag.split()[0]
                tag_stack.append(tag_name)
        
        for tag in close_tags:
            if tag_stack and tag_stack[-1] == tag:
                tag_stack.pop()
            else:
                return False, f"Unmatched closing tag: </{tag}>"
        
        if tag_stack:
            return False, f"Unclosed tags: {tag_stack}"
        
        # Check for unsupported characters in tags
        if re.search(r'<[^>]*[۰-۹][^>]*>', text):
            return False, "Persian numbers in HTML tags not supported"
        
        return True, text
        
    except Exception as e:
        return False, f"HTML validation error: {str(e)}"


def prepare_telegram_message(text: str, parse_mode: str = "HTML") -> tuple[str, str]:
    """Prepare text for Telegram sending with proper HTML formatting"""
    if not text:
        return "", "HTML"
    
    # Clean the content
    cleaned_text = clean_html_content(text)
    
    # Validate HTML if parse_mode is HTML
    if parse_mode == "HTML":
        is_valid, validated_text = validate_telegram_html(cleaned_text)
        if not is_valid:
            # Fall back to plain text if HTML is invalid
            plain_text = re.sub(r'<[^>]+>', '', cleaned_text)
            plain_text = html.unescape(plain_text)
            return plain_text, "Markdown"
        return validated_text, "HTML"
    
    return cleaned_text, parse_mode


def escape_html_special_chars(text: str) -> str:
    """Escape special characters for HTML"""
    if not text:
        return ""
    
    # Escape HTML special characters
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    
    return text


def format_telegram_bold(text: str) -> str:
    """Format text as bold for Telegram"""
    if not text:
        return ""
    
    # Remove existing bold tags and add new ones
    text = re.sub(r'<b>|</b>|<strong>|</strong>', '', text)
    return f"<b>{text}</b>"


def format_telegram_italic(text: str) -> str:
    """Format text as italic for Telegram"""
    if not text:
        return ""
    
    # Remove existing italic tags and add new ones
    text = re.sub(r'<i>|</i>|<em>|</em>', '', text)
    return f"<i>{text}</i>"


def format_telegram_code(text: str) -> str:
    """Format text as code for Telegram"""
    if not text:
        return ""
    
    # Remove existing code tags and add new ones
    text = re.sub(r'<code>|</code>', '', text)
    return f"<code>{text}</code>"


def format_telegram_pre(text: str) -> str:
    """Format text as pre-formatted for Telegram"""
    if not text:
        return ""
    
    # Remove existing pre tags and add new ones
    text = re.sub(r'<pre>|</pre>', '', text)
    return f"<pre>{text}</pre>"


def create_telegram_safe_message(content: str) -> str:
    """Create a Telegram-safe message with proper formatting"""
    if not content:
        return ""
    
    # Clean the content
    cleaned = clean_html_content(content)
    
    # Validate and prepare
    message, parse_mode = prepare_telegram_message(cleaned, "HTML")
    
    # If HTML validation failed, return plain text
    if parse_mode != "HTML":
        return message
    
    return message
