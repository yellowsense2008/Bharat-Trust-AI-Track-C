"""citizen_response_service.py
Service to simplify AI-generated resolutions for citizen-facing responses.
Keeps timeline but simplifies it into a single expectation sentence.
"""

import re

def simplify_resolution(resolution_text: str) -> str:
    """
    Simplify AI-generated resolution for citizens.
    
    Extracts:
    - Main resolution action (what will happen)
    - Timeline (when it will happen) - simplified to single sentence
    
    Removes:
    - Regulatory references
    - Technical jargon
    - Multiple timeline bullets (converts to single expectation)
    
    Returns citizen-friendly resolution with clear expectation.
    """
    if not resolution_text:
        return "Your complaint is currently under review."
    
    lines = resolution_text.split('\n')
    
    resolution_sentences = []
    timeline_days = []
    
    skip_section = False
    
    for line in lines:
        line_stripped = line.strip()
        line_lower = line_stripped.lower()
        
        # Skip regulatory and next steps sections
        if any(skip in line_lower for skip in [
            'regulatory reference:', 'specific regulatory', 
            'rbi/', 'circular on', 'next steps:', 'customer care team'
        ]):
            skip_section = True
            continue
        
        if skip_section:
            continue
        
        # Skip section headers
        if line_stripped.startswith('**') or 'timeline:' in line_lower:
            continue
        
        # Extract timeline days
        if 'working day' in line_lower or 'days' in line_lower:
            # Extract number of days
            day_match = re.search(r'(\d+)\s*(?:working\s*)?days?', line_lower)
            if day_match:
                timeline_days.append(int(day_match.group(1)))
        
        # Collect resolution sentences (before timeline section)
        elif line_stripped and not line_stripped.startswith('*') and not line_stripped.startswith('-'):
            # Only keep sentences with action words
            if any(word in line_lower for word in [
                'will', 'refund', 'investigate', 'verify', 'initiate', 'taken up', 'contact'
            ]):
                # Clean up the sentence
                clean_sentence = line_stripped.replace('Based on the complaint and similar cases, I suggest the following resolution:', '').strip()
                clean_sentence = clean_sentence.replace('**Resolution:**', '').strip()
                if clean_sentence and len(clean_sentence) > 20:
                    resolution_sentences.append(clean_sentence)
    
    # Build main resolution (first 2-3 key sentences)
    main_resolution = ' '.join(resolution_sentences[:3])
    
    # Simplify to citizen-friendly language
    main_resolution = main_resolution.replace('The matter will be taken up with', 'Your bank will')
    main_resolution = main_resolution.replace('the customer\'s account', 'your account')
    main_resolution = main_resolution.replace('the customer', 'you')
    
    # Add simplified timeline with status-aware message
    if timeline_days:
        max_days = max(timeline_days)
        timeline_text = f"\n\nThis process usually takes up to {max_days} working days. You will be notified once completed."
    else:
        timeline_text = "\n\nYou will be notified once the resolution is complete."
    
    result = main_resolution + timeline_text
    
    # Fallback if extraction failed
    if len(result.strip()) < 30:
        return "Your complaint has been resolved. The bank will contact you shortly with further details."
    
    return result.strip()
