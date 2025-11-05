"""
Unicode Sanitizer - Defense against emoji smuggling and Unicode attacks
Based on research: https://arxiv.org/abs/2411.01077
"""

import unicodedata
import re
from typing import Tuple, List

class UnicodeSanitizer:
    """
    Detect and neutralize Unicode-based attacks:
    - Emoji smuggling
    - Zero-width characters
    - Homoglyphs (lookalike characters)
    - Directional overrides (RTL)
    - Mixed script obfuscation
    """

    # Zero-width characters (invisible)
    ZERO_WIDTH_CHARS = [
        '\u200B',  # Zero Width Space
        '\u200C',  # Zero Width Non-Joiner
        '\u200D',  # Zero Width Joiner
        '\u2060',  # Word Joiner
        '\uFEFF',  # Zero Width No-Break Space
    ]

    # Directional override characters
    DIRECTIONAL_CHARS = [
        '\u202A',  # Left-to-Right Embedding
        '\u202B',  # Right-to-Left Embedding
        '\u202C',  # Pop Directional Formatting
        '\u202D',  # Left-to-Right Override
        '\u202E',  # Right-to-Left Override
    ]

    # Common homoglyphs (Cyrillic → Latin)
    HOMOGLYPHS = {
        # Cyrillic to Latin
        'А': 'A', 'В': 'B', 'Е': 'E', 'К': 'K', 'М': 'M',
        'Н': 'H', 'О': 'O', 'Р': 'P', 'С': 'C', 'Т': 'T',
        'Х': 'X', 'а': 'a', 'е': 'e', 'о': 'o', 'р': 'p',
        'с': 'c', 'у': 'y', 'х': 'x',
        # Cherokee lookalikes
        'Ꭺ': 'A', 'Ꮪ': 'S', 'Ꮯ': 'C', 'Ꭰ': 'D',
        # Greek lookalikes
        'Α': 'A', 'Β': 'B', 'Ε': 'E', 'Ζ': 'Z', 'Η': 'H',
        'Ι': 'I', 'Κ': 'K', 'Μ': 'M', 'Ν': 'N', 'Ο': 'O',
        'Ρ': 'P', 'Τ': 'T', 'Υ': 'Y', 'Χ': 'X',
    }

    # Suspicious emoji threshold
    MAX_EMOJIS = 10

    def __init__(self):
        # Compile emoji pattern
        self.emoji_pattern = re.compile(
            r'[\U0001F600-\U0001F64F'  # Emoticons
            r'\U0001F300-\U0001F5FF'   # Symbols & Pictographs
            r'\U0001F680-\U0001F6FF'   # Transport & Map
            r'\U0001F1E0-\U0001F1FF'   # Flags
            r'\U00002702-\U000027B0'   # Dingbats
            r'\U000024C2-\U0001F251]+',
            flags=re.UNICODE
        )

    def sanitize(self, text: str) -> dict:
        """
        Sanitize text and return cleaned version + violations found

        Returns:
            {
                'cleaned_text': str,
                'violations': List[str],
                'suspicious': bool
            }
        """
        violations = []
        cleaned = text

        # 1. Detect and remove zero-width characters
        for char in self.ZERO_WIDTH_CHARS:
            if char in cleaned:
                violations.append(f"zero_width_character_U+{ord(char):04X}")
                cleaned = cleaned.replace(char, '')

        # 2. Detect and remove directional overrides
        for char in self.DIRECTIONAL_CHARS:
            if char in cleaned:
                violations.append(f"directional_override_U+{ord(char):04X}")
                cleaned = cleaned.replace(char, '')

        # 3. Replace homoglyphs
        for fake, real in self.HOMOGLYPHS.items():
            if fake in cleaned:
                violations.append(f"homoglyph_{fake}_to_{real}")
                cleaned = cleaned.replace(fake, real)

        # 4. Normalize Unicode (NFC form)
        cleaned = unicodedata.normalize('NFC', cleaned)

        # 5. Detect suspicious emoji patterns
        emojis = self.emoji_pattern.findall(text)
        if len(emojis) > self.MAX_EMOJIS:
            violations.append(f"suspicious_emoji_count_{len(emojis)}")

        # 6. Check for mixed scripts (potential obfuscation)
        scripts = set()
        for char in text:
            if char.isalpha():
                try:
                    script = unicodedata.name(char, '').split()[0]
                    scripts.add(script)
                except:
                    pass

        if len(scripts) > 2:  # Mixed scripts (Latin + Cyrillic + Greek = suspicious)
            violations.append(f"mixed_scripts_{len(scripts)}")

        return {
            'cleaned_text': cleaned,
            'violations': violations,
            'suspicious': len(violations) > 0
        }

    def is_suspicious(self, text: str) -> bool:
        """Quick check if text contains suspicious Unicode"""
        result = self.sanitize(text)
        return result['suspicious']

