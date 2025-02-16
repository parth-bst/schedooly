import re
import tiktoken

def count_tokens(html_content, model="gpt-4"):
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(html_content))

def trim_content(html_content, max_tokens=150000, model="gpt-4"):
    encoding = tiktoken.encoding_for_model(model)
    tokens = encoding.encode(html_content)
    
    if len(tokens) <= max_tokens:
        return html_content
        
    # Trim to max_tokens and decode back to text
    trimmed_tokens = tokens[:max_tokens]
    return encoding.decode(trimmed_tokens)


def prepare_content_for_llm(html_content, max_tokens=150000, model="gpt-4"):
    token_count = count_tokens(html_content, model)
    
    if token_count > max_tokens:
        return trim_content(html_content, max_tokens, model)
    
    return html_content

def parse_llm_xml_response(response_text, dict_tags=["python_dict", "form_dict"], explanation_tag="explanation"):
    """
    Parses LLM response containing XML tags and returns a dictionary of extracted content
    
    Args:
        response_text: String containing XML tagged content
        dict_tags: List of XML tag names wrapping python dictionaries
        explanation_tag: Name of the XML tag wrapping the explanation text
        
    Returns:
        dict: Contains dictionary content and explanation keys with extracted content
    """
    result = {}
    
    # Extract python dictionaries for each tag
    for tag in dict_tags:
        dict_match = re.search(f'<{tag}>(.*?)</{tag}>', response_text, re.DOTALL)
        if dict_match:
            result[tag] = eval(dict_match.group(1).strip())
    
    # Extract explanation
    explanation_match = re.search(f'<{explanation_tag}>(.*?)</{explanation_tag}>', response_text, re.DOTALL) 
    if explanation_match:
        result[explanation_tag] = explanation_match.group(1).strip()
        
    return result
