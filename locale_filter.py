#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Locale File Filter - Exclude translation/localization files from indexing
Filters out ~335K+ locale files from GitHub repositories
"""

import re
from pathlib import Path
from typing import Set

# Common locale/translation folder patterns
LOCALE_FOLDER_PATTERNS = {
    'locale', 'locales',
    'i18n', 'l10n',
    'translations', 'translation', 'translate',
    'lang', 'langs', 'language', 'languages',
    'intl', 'nls',
    '__locales__', '_locales',
}

# ISO 639-1 two-letter language codes (complete set)
LANGUAGE_CODES = {
    'aa', 'ab', 'af', 'am', 'ar', 'as', 'ay', 'az',
    'ba', 'be', 'bg', 'bh', 'bi', 'bn', 'bo', 'br',
    'ca', 'co', 'cs', 'cy', 'da', 'de', 'dz',
    'el', 'en', 'eo', 'es', 'et', 'eu',
    'fa', 'fi', 'fj', 'fo', 'fr', 'fy',
    'ga', 'gd', 'gl', 'gn', 'gu',
    'ha', 'he', 'hi', 'hr', 'hu', 'hy',
    'ia', 'id', 'ie', 'ik', 'is', 'it', 'iu',
    'ja', 'jw', 'ka', 'kk', 'kl', 'km', 'kn', 'ko', 'ks', 'ku', 'ky',
    'la', 'ln', 'lo', 'lt', 'lv',
    'mg', 'mi', 'mk', 'ml', 'mn', 'mo', 'mr', 'ms', 'mt', 'my',
    'na', 'ne', 'nl', 'no',
    'oc', 'om', 'or',
    'pa', 'pl', 'ps', 'pt',
    'qu',
    'rm', 'rn', 'ro', 'ru', 'rw',
    'sa', 'sd', 'sg', 'sh', 'si', 'sk', 'sl', 'sm', 'sn', 'so', 'sq', 'sr', 'ss', 'st', 'su', 'sv', 'sw',
    'ta', 'te', 'tg', 'th', 'ti', 'tk', 'tl', 'tn', 'to', 'tr', 'ts', 'tt', 'tw',
    'ug', 'uk', 'ur', 'uz',
    'vi', 'vo',
    'wo',
    'xh',
    'yi', 'yo',
    'za', 'zh', 'zu'
}


def should_exclude_file(file_path: str) -> bool:
    """
    Returns True if file should be excluded from indexing.
    
    Args:
        file_path: Path to the file (string or Path object)
        
    Returns:
        True if file should be excluded, False otherwise
    """
    path = Path(file_path)
    
    # Check if any folder in path contains locale-related terms
    for part in path.parts:
        part_lower = part.lower()
        for pattern in LOCALE_FOLDER_PATTERNS:
            if pattern in part_lower:
                return True
    
    # Check if filename contains "locale" 
    if 'locale' in path.name.lower():
        return True
    
    # Check for language code files
    stem = path.stem  # filename without extension
    
    # Pattern 1: Simple 2-letter codes (eu.js, fr.json, de.ts)
    if stem.lower() in LANGUAGE_CODES:
        return True
    
    # Pattern 2: Language-region codes (en-US, zh-CN, pt-BR, en_GB)
    lang_region_match = re.match(r'^([a-z]{2})[-_]([A-Z]{2}|[a-z]{2,3})$', stem)
    if lang_region_match:
        lang_code = lang_region_match.group(1).lower()
        if lang_code in LANGUAGE_CODES:
            return True
    
    # Pattern 3: Files like "messages.en.js", "strings.fr.json", "app.de.properties"
    parts = stem.split('.')
    if len(parts) >= 2:
        for part in parts:
            # Check if any part is a language code
            if part.lower() in LANGUAGE_CODES:
                return True
            
            # Check for lang-region in middle parts
            if re.match(r'^([a-z]{2})[-_]([A-Z]{2}|[a-z]{2,3})$', part):
                lang_part = part.split('-')[0] if '-' in part else part.split('_')[0]
                if lang_part.lower() in LANGUAGE_CODES:
                    return True
    
    # Pattern 4: Common translation file patterns
    common_locale_names = {
        'messages', 'strings', 'translations', 'resources',
    }
    
    stem_lower = stem.lower()
    for name in common_locale_names:
        if stem_lower.startswith(name + '.') or stem_lower.startswith(name + '_'):
            return True
    
    return False


def filter_file_list(files: list) -> tuple:
    """
    Filter a list of files, separating locale files from valid files.
    
    Args:
        files: List of file paths (strings or Path objects)
        
    Returns:
        Tuple of (valid_files, excluded_files)
    """
    valid_files = []
    excluded_files = []
    
    for file_path in files:
        if should_exclude_file(file_path):
            excluded_files.append(file_path)
        else:
            valid_files.append(file_path)
    
    return valid_files, excluded_files


def get_filter_stats(files: list) -> dict:
    """
    Get statistics about filtered files.
    
    Args:
        files: List of file paths
        
    Returns:
        Dictionary with statistics
    """
    valid, excluded = filter_file_list(files)
    
    return {
        'total_files': len(files),
        'valid_files': len(valid),
        'excluded_files': len(excluded),
        'exclusion_rate': f"{(len(excluded) / len(files) * 100):.1f}%" if files else "0%"
    }
