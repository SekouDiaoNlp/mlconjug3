#!/usr/bin/env python3
"""
UniMorph Parser for Verb Conjugation Tables
Parses UniMorph data files and generates conjugation tables for verbs across languages

Optimized for JSON output with compression support and high performance
"""

import os
import re
import json
import gzip
import logging
import argparse
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Tuple, Optional, Any, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
import unicodedata
from datetime import datetime
import hashlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('unimorph_data/unimorph_parser.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# UniMorph verb-related features
VERB_FEATURES = {
    'V', 'V.PTCP', 'V.MSDR', 'V.PTCP.PST', 'V.PTCP.PRS',  # Part of speech
    'FIN', 'NFIN',  # Finiteness
    'IND', 'SBJV', 'IMP', 'COND', 'OPT', 'NEC', 'POT', 'ADM',  # Mood
    'PRS', 'PST', 'FUT',  # Tense
    'PFV', 'IPFV', 'PROG', 'HAB', 'ITER', 'INCH',  # Aspect
    '1', '2', '3',  # Person
    'SG', 'PL', 'DU', 'PAUC', 'GRPL',  # Number
    'MASC', 'FEM', 'NEUT', 'COM',  # Gender
    'ACT', 'PASS', 'MID',  # Voice
    'POS', 'NEG',  # Polarity
    'INF', 'PRTC', 'GER', 'CONV',  # Non-finite forms
    'REFL',  # Reflexive
}

# Feature hierarchy for consistent ordering
FEATURE_HIERARCHY = [
    'FIN', 'NFIN', 'INF', 'PRTC', 'GER', 'CONV',  # Finiteness
    'IND', 'SBJV', 'IMP', 'COND', 'OPT', 'NEC', 'POT',  # Mood
    'PRS', 'PST', 'FUT',  # Tense
    'PFV', 'IPFV', 'PROG', 'HAB', 'ITER',  # Aspect
    '1', '2', '3',  # Person
    'SG', 'PL', 'DU', 'PAUC',  # Number
    'MASC', 'FEM', 'NEUT',  # Gender
    'ACT', 'PASS', 'MID',  # Voice
    'POS', 'NEG',  # Polarity
    'REFL'  # Reflexive
]


class OutputFormat(Enum):
    JSON = "json"
    JSONL = "jsonl"  # Line-delimited JSON for large files
    JSON_GZIP = "json.gz"  # Compressed JSON


@dataclass
class VerbForm:
    """Represents a single verb form with its features"""
    word: str
    lemma: str
    features: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'word': self.word,
            'lemma': self.lemma,
            'features': self.features
        }


@dataclass
class ConjugationEntry:
    """Represents a conjugation entry for a specific feature combination"""
    endings: List[Tuple[int, str]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'endings': [[idx, ending] for idx, ending in self.endings]
        }


class UniMorphParser:
    """Parser for UniMorph data files with performance optimizations"""

    def __init__(self, data_dir: str = "./unimorph_data", cache_enabled: bool = True):
        self.data_dir = Path(data_dir)
        self.cache_enabled = cache_enabled
        self.cache: Dict[str, Any] = {}
        self.verb_data: Dict[str, Dict[str, List[VerbForm]]] = defaultdict(lambda: defaultdict(list))
        self.conjugation_classes: Dict[str, Dict[str, Any]] = {}
        self.conjugation_tables: Dict[str, Dict[str, Any]] = {}
        self.stats: Dict[str, Any] = defaultdict(int)

    def is_verb(self, features: List[str]) -> bool:
        """Check if a word form is a verb based on its features"""
        # Quick check for verb POS tags
        for feat in features:
            if feat in VERB_FEATURES or feat.startswith('V'):
                return True
        return False

    def normalize_unicode(self, text: str) -> str:
        """Normalize Unicode text to NFC form for consistency"""
        return unicodedata.normalize('NFC', text)

    def extract_verb_info(self, line: str) -> Optional[VerbForm]:
        """
        Parse a line from UniMorph file.
        Format: word\tlemma\tfeature1;feature2;feature3

        Optimized for speed with minimal allocations
        """
        line = line.strip()
        if not line or line.startswith('#'):
            return None

        # Use split with maxsplit for better performance
        parts = line.split('\t', 2)
        if len(parts) < 3:
            logger.warning(f"Skipping malformed line: {line[:100]}...")
            return None

        word = self.normalize_unicode(parts[0].strip())
        lemma = self.normalize_unicode(parts[1].strip())

        # Split features efficiently
        features = [f.strip() for f in parts[2].split(';') if f.strip()]

        return VerbForm(word, lemma, features)

    def get_conjugation_key(self, features: List[str]) -> str:
        """
        Generate a key for a specific conjugation pattern
        Using feature hierarchy for consistent ordering
        """
        # Extract and order relevant features
        relevant_features = []
        features_set = set(features)

        for feat in FEATURE_HIERARCHY:
            if feat in features_set:
                relevant_features.append(feat)

        # Add any remaining features not in hierarchy
        for feat in features:
            if feat not in FEATURE_HIERARCHY and feat not in relevant_features:
                relevant_features.append(feat)

        return ';'.join(relevant_features) if relevant_features else 'base'

    def find_conjugation_template(self, verb_forms: List[VerbForm]) -> Dict[str, Dict[str, List[Tuple[int, str]]]]:
        """
        Find conjugation patterns and create templates
        Optimized with caching for repeated patterns
        """
        templates = defaultdict(lambda: defaultdict(list))

        # Group by lemma
        lemma_forms = defaultdict(list)
        for form in verb_forms:
            lemma_forms[form.lemma].append(form)

        for lemma, forms in lemma_forms.items():
            # Cache key for this lemma's processing
            cache_key = f"template_{lemma}_{hash(str(sorted([f.word for f in forms])))}"

            if self.cache_enabled and cache_key in self.cache:
                cached_templates = self.cache[cache_key]
                for template, conj in cached_templates.items():
                    for conj_key, endings in conj.items():
                        templates[template][conj_key].extend(endings)
                continue

            # Find the base form (infinitive or present tense 3rd person singular)
            base_form = None
            for form in forms:
                if 'INF' in form.features or (
                    'PRS' in form.features and '3' in form.features and 'SG' in form.features):
                    base_form = form
                    break

            if not base_form and forms:
                # Fallback to the shortest form as base
                base_form = min(forms, key=lambda x: len(x.word))

            if not base_form:
                continue

            # Determine root and template
            root, template = self.determine_template(base_form.word, lemma)

            # Store conjugation patterns
            pattern_key = f"{root}:{template}" if template else f":{lemma}"

            for form in forms:
                conj_key = self.get_conjugation_key(form.features)

                # Calculate ending efficiently
                if root and form.word.startswith(root):
                    ending = form.word[len(root):]
                else:
                    # Try suffix-based ending detection
                    ending = self.extract_ending(form.word, root, lemma)

                # Determine person/number index
                person_num_idx = self.get_person_number_index(form.features)

                templates[pattern_key][conj_key].append((person_num_idx, ending))

            # Cache the results for this lemma
            if self.cache_enabled:
                lemma_templates = {}
                for template, conj in templates.items():
                    if template.startswith(f"{root}:") or template == f":{lemma}":
                        lemma_templates[template] = dict(conj)
                self.cache[cache_key] = lemma_templates

        return templates

    def extract_ending(self, word: str, root: str, lemma: str) -> str:
        """
        Extract ending by finding common suffix with lemma
        """
        # Find common suffix
        min_len = min(len(word), len(lemma))
        common_suffix_len = 0
        for i in range(1, min_len + 1):
            if word[-i] == lemma[-i]:
                common_suffix_len = i
            else:
                break

        if common_suffix_len > 0:
            # If we have a common suffix, the ending is the part after the root
            # or the whole word if no root
            if root and len(word) > len(root):
                return word[len(root):]
            else:
                return word
        else:
            return word

    def determine_template(self, word: str, lemma: str) -> Tuple[str, str]:
        """
        Determine the conjugation template (prefix:ending)
        Improved algorithm for better template detection
        """
        word = self.normalize_unicode(word)
        lemma = self.normalize_unicode(lemma)

        # Find longest common prefix
        common_prefix_len = 0
        for i in range(min(len(word), len(lemma))):
            if word[i] == lemma[i]:
                common_prefix_len += 1
            else:
                break

        # Find longest common suffix
        common_suffix_len = 0
        for i in range(1, min(len(word), len(lemma)) + 1):
            if word[-i] == lemma[-i]:
                common_suffix_len = i
            else:
                break

        # Decision logic for template type
        if common_prefix_len > len(word) // 2:
            # Word shares significant prefix with lemma
            root = word[:common_prefix_len]
            # Remove the common part to get the ending
            if len(lemma) > common_prefix_len:
                ending = lemma[common_prefix_len:]
            else:
                ending = ""
            return root, ending
        elif common_suffix_len > 3:
            # Share significant suffix (e.g., regular -ed, -ing patterns)
            root = word[:-common_suffix_len] if len(word) > common_suffix_len else ""
            ending = word[-common_suffix_len:]
            return root, ending
        else:
            # Default: use whole word as template
            return "", lemma

    def get_person_number_index(self, features: List[str]) -> int:
        """
        Map person and number to an index (0-5 typically)
        0: 1st person singular
        1: 2nd person singular
        2: 3rd person singular
        3: 1st person plural
        4: 2nd person plural
        5: 3rd person plural

        Extended for dual and paucal numbers
        """
        person = None
        number = None

        # Efficient feature lookup using set
        features_set = set(features)

        if '1' in features_set:
            person = 1
        elif '2' in features_set:
            person = 2
        elif '3' in features_set:
            person = 3

        if 'SG' in features_set:
            number = 'SG'
        elif 'PL' in features_set:
            number = 'PL'
        elif 'DU' in features_set:
            number = 'DU'
        elif 'PAUC' in features_set:
            number = 'PAUC'

        # Map to index
        if person is None:
            # Handle impersonal forms
            return 6  # Special index for impersonal

        if number == 'SG':
            return person - 1
        elif number == 'PL':
            return person + 2
        elif number == 'DU':
            return person + 5  # 6-8 for dual
        elif number == 'PAUC':
            return person + 8  # 9-11 for paucal

        return person - 1  # Default to singular

    def build_conjugation_table(self, templates: Dict[str, Dict[str, List[Tuple[int, str]]]]) -> Dict[str, Any]:
        """
        Build the final conjugation table structure with improved organization
        """
        table = {}

        for template, conjugations in templates.items():
            table[template] = {}

            # Group by grammatical categories
            for conj_key, endings in conjugations.items():
                # Parse the conjugation key into categories
                parts = conj_key.split(';')
                parts_set = set(parts)

                # Determine grammatical categories
                mood = self.determine_mood(parts_set)
                tense = self.determine_tense(parts_set)
                aspect = self.determine_aspect(parts_set)
                voice = self.determine_voice(parts_set)
                finiteness = self.determine_finiteness(parts_set)

                # Build the category path
                if finiteness == 'non-finite':
                    category = self.build_nonfinite_category(parts_set)
                else:
                    category = self.build_finite_category(mood, tense, aspect, voice)

                # Store endings with deduplication
                if category not in table[template]:
                    table[template][category] = {}

                # Process endings with syncretism handling
                ending_dict = {}
                for idx, ending in endings:
                    # Handle multiple possible endings (syncretism)
                    if idx in ending_dict:
                        if isinstance(ending_dict[idx], list):
                            if ending not in ending_dict[idx]:
                                ending_dict[idx].append(ending)
                        else:
                            if ending != ending_dict[idx]:
                                ending_dict[idx] = [ending_dict[idx], ending]
                    else:
                        ending_dict[idx] = ending

                # Convert to list format for JSON serialization
                ending_list = self.endings_to_list(ending_dict)

                # Store under the appropriate subcategory
                if aspect or voice:
                    subcat = f"{tense}"
                    if aspect:
                        subcat += f"_{aspect}"
                    if voice and voice != 'active':
                        subcat += f"_{voice}"

                    if subcat not in table[template][category]:
                        table[template][category][subcat] = []
                    table[template][category][subcat].extend(ending_list)
                else:
                    if tense not in table[template][category]:
                        table[template][category][tense] = []
                    table[template][category][tense].extend(ending_list)

        return table

    def determine_mood(self, features: Set[str]) -> str:
        """Determine mood from features"""
        if 'IMP' in features:
            return 'imperative'
        elif 'SBJV' in features:
            return 'subjunctive'
        elif 'COND' in features:
            return 'conditional'
        elif 'OPT' in features:
            return 'optative'
        elif 'NEC' in features:
            return 'necessitative'
        elif 'POT' in features:
            return 'potential'
        elif 'IND' in features:
            return 'indicative'
        else:
            return 'indicative'  # Default

    def determine_tense(self, features: Set[str]) -> str:
        """Determine tense from features"""
        if 'PST' in features:
            return 'past'
        elif 'FUT' in features:
            return 'future'
        elif 'PRS' in features:
            return 'present'
        else:
            return 'present'  # Default

    def determine_aspect(self, features: Set[str]) -> str:
        """Determine aspect from features"""
        if 'PFV' in features:
            return 'perfective'
        elif 'IPFV' in features:
            return 'imperfective'
        elif 'PROG' in features:
            return 'progressive'
        elif 'HAB' in features:
            return 'habitual'
        elif 'ITER' in features:
            return 'iterative'
        elif 'INCH' in features:
            return 'inchoative'
        else:
            return ''

    def determine_voice(self, features: Set[str]) -> str:
        """Determine voice from features"""
        if 'PASS' in features:
            return 'passive'
        elif 'MID' in features:
            return 'middle'
        elif 'ACT' in features:
            return 'active'
        else:
            return 'active'  # Default

    def determine_finiteness(self, features: Set[str]) -> str:
        """Determine finiteness from features"""
        if 'FIN' in features:
            return 'finite'
        elif 'NFIN' in features or 'INF' in features or 'PRTC' in features:
            return 'non-finite'
        else:
            return 'finite'  # Default

    def build_nonfinite_category(self, features: Set[str]) -> str:
        """Build category name for non-finite forms"""
        if 'INF' in features:
            return 'infinitive'
        elif 'PRTC' in features:
            if 'PST' in features:
                return 'past_participle'
            elif 'PRS' in features:
                return 'present_participle'
            else:
                return 'participle'
        elif 'GER' in features:
            return 'gerund'
        elif 'CONV' in features:
            return 'converb'
        else:
            return 'nonfinite'

    def build_finite_category(self, mood: str, tense: str, aspect: str, voice: str) -> str:
        """Build category name for finite forms"""
        parts = [mood]
        if voice != 'active':
            parts.append(voice)
        parts.append(tense)
        if aspect:
            parts.append(aspect)
        return '_'.join(parts)

    def endings_to_list(self, ending_dict: Dict[int, Union[str, List[str]]]) -> List[List[Union[int, str]]]:
        """Convert ending dictionary to list format for JSON serialization"""
        # Determine max index (supports up to 12 for dual/paucal)
        max_idx = max(ending_dict.keys()) if ending_dict else 5

        ending_list = []
        for idx in range(max_idx + 1):
            if idx in ending_dict:
                val = ending_dict[idx]
                if isinstance(val, list):
                    # Join multiple variants with slash
                    ending_list.append([idx, '/'.join(val)])
                else:
                    ending_list.append([idx, val])
            else:
                ending_list.append([idx, ''])

        return ending_list

    def parse_language(self, lang_code: str) -> bool:
        """
        Parse all verb data for a specific language with performance optimizations
        """
        lang_file = self.data_dir / lang_code / lang_code

        if not lang_file.exists():
            logger.warning(f"Language file not found: {lang_file}")
            return False

        logger.info(f"Processing language: {lang_code} from {lang_file}")

        # Check cache
        cache_key = f"parsed_{lang_code}"
        if self.cache_enabled and cache_key in self.cache:
            logger.info(f"Loading {lang_code} from cache")
            cached_data = self.cache[cache_key]
            self.conjugation_classes[lang_code] = cached_data['classes']
            self.conjugation_tables[lang_code] = cached_data['tables']
            self.stats[lang_code] = cached_data['stats']
            return True

        verbs_found = 0
        verb_forms_by_lemma = defaultdict(list)
        file_size = lang_file.stat().st_size

        logger.info(f"File size: {file_size:,} bytes")

        try:
            # Read file in chunks for large files
            with open(lang_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    verb_form = self.extract_verb_info(line)

                    if verb_form and self.is_verb(verb_form.features):
                        verbs_found += 1
                        verb_forms_by_lemma[verb_form.lemma].append(verb_form)

                        # Periodic logging
                        if verbs_found % 5000 == 0:
                            logger.info(f"Processed {verbs_found:,} verb forms for {lang_code}")

            logger.info(f"Found {verbs_found:,} verb forms for {lang_code} across {len(verb_forms_by_lemma):,} lemmas")

            if not verb_forms_by_lemma:
                logger.warning(f"No verbs found for {lang_code}")
                return False

            # Process each lemma to find conjugation patterns
            all_templates = {}
            verbs_info = {}

            # Process in batches for memory efficiency
            batch_size = 1000
            lemma_items = list(verb_forms_by_lemma.items())

            for i in range(0, len(lemma_items), batch_size):
                batch = lemma_items[i:i + batch_size]

                for lemma, forms in batch:
                    # Find conjugation template for this lemma
                    templates = self.find_conjugation_template(forms)

                    for template, conjugations in templates.items():
                        if template not in all_templates:
                            all_templates[template] = {}

                        # Merge conjugations
                        for conj_key, endings in conjugations.items():
                            if conj_key not in all_templates[template]:
                                all_templates[template][conj_key] = []
                            all_templates[template][conj_key].extend(endings)

                    # Store verb mapping with template detection
                    if templates:
                        # Get the most specific template for this verb
                        primary_template = max(templates.keys(), key=len) if templates else f":{lemma}"
                        root = primary_template.split(':')[0] if ':' in primary_template else ''

                        verbs_info[lemma] = {
                            'root': root,
                            'template': primary_template
                        }
                    else:
                        verbs_info[lemma] = {
                            'root': '',
                            'template': f":{lemma}"
                        }

                logger.debug(f"Processed batch {i // batch_size + 1}/{(len(lemma_items) - 1) // batch_size + 1}")

            # Build conjugation tables
            conjugation_table = self.build_conjugation_table(all_templates)

            # Store results
            self.conjugation_classes[lang_code] = verbs_info
            self.conjugation_tables[lang_code] = conjugation_table
            self.stats[lang_code] = {
                'verb_forms': verbs_found,
                'lemmas': len(verbs_info),
                'templates': len(all_templates),
                'conjugation_patterns': sum(len(v) for v in conjugation_table.values())
            }

            # Cache results
            if self.cache_enabled:
                self.cache[cache_key] = {
                    'classes': verbs_info,
                    'tables': conjugation_table,
                    'stats': self.stats[lang_code]
                }

            logger.info(
                f"Successfully processed {lang_code}: {len(verbs_info):,} verbs, {len(all_templates)} templates")
            return True

        except Exception as e:
            logger.error(f"Error processing {lang_code}: {str(e)}", exc_info=True)
            return False

    def save_results(self, output_dir: str, format: OutputFormat = OutputFormat.JSON, compress_level: int = 6):
        """
        Save the parsed results to files with compression support
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Save metadata about the generation
        metadata = {
            'generated_at': datetime.now().isoformat(),
            'format': format.value,
            'compression_level': compress_level if format == OutputFormat.JSON_GZIP else None,
            'languages_processed': list(self.stats.keys()),
            'statistics': dict(self.stats)
        }

        # Save metadata
        metadata_file = output_path / "generation_metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        for lang_code in self.conjugation_classes:
            # Save verbs file
            verbs_file = output_path / f"verbs-{lang_code}.{format.value.replace('.gz', '')}"
            conjugations_file = output_path / f"conjugations-{lang_code}.{format.value.replace('.gz', '')}"

            try:
                if format == OutputFormat.JSON:
                    # Standard JSON format
                    with open(verbs_file, 'w', encoding='utf-8') as f:
                        json.dump(self.conjugation_classes[lang_code], f,
                                  ensure_ascii=False, indent=2, sort_keys=True)

                    with open(conjugations_file, 'w', encoding='utf-8') as f:
                        json.dump(self.conjugation_tables[lang_code], f,
                                  ensure_ascii=False, indent=2, sort_keys=True)

                elif format == OutputFormat.JSONL:
                    # Line-delimited JSON for large files
                    self.save_as_jsonl(verbs_file, self.conjugation_classes[lang_code])
                    self.save_as_jsonl(conjugations_file, self.conjugation_tables[lang_code])

                elif format == OutputFormat.JSON_GZIP:
                    # Compressed JSON
                    verbs_gz = Path(str(verbs_file) + '.gz')
                    conjugations_gz = Path(str(conjugations_file) + '.gz')

                    with gzip.open(verbs_gz, 'wt', encoding='utf-8', compresslevel=compress_level) as f:
                        json.dump(self.conjugation_classes[lang_code], f,
                                  ensure_ascii=False, indent=2, sort_keys=True)

                    with gzip.open(conjugations_gz, 'wt', encoding='utf-8', compresslevel=compress_level) as f:
                        json.dump(self.conjugation_tables[lang_code], f,
                                  ensure_ascii=False, indent=2, sort_keys=True)

                    verbs_file = verbs_gz
                    conjugations_file = conjugations_gz

                # Log file sizes
                verbs_size = verbs_file.stat().st_size
                conj_size = conjugations_file.stat().st_size
                logger.info(f"Saved verbs for {lang_code} to {verbs_file} ({verbs_size:,} bytes)")
                logger.info(f"Saved conjugations for {lang_code} to {conjugations_file} ({conj_size:,} bytes)")

            except Exception as e:
                logger.error(f"Error saving results for {lang_code}: {str(e)}")

    def save_as_jsonl(self, filepath: Path, data: Dict[str, Any]):
        """Save data as line-delimited JSON (JSONL format)"""
        with open(filepath, 'w', encoding='utf-8') as f:
            for key, value in data.items():
                line = json.dumps({key: value}, ensure_ascii=False, sort_keys=True)
                f.write(line + '\n')

    def process_all_languages(self, languages: Optional[List[str]] = None, max_languages: Optional[int] = None):
        """
        Process all languages in the data directory with optional limits
        """
        if languages:
            lang_codes = languages
        else:
            # Find all language directories that have the main data file
            lang_codes = []
            for d in self.data_dir.iterdir():
                if d.is_dir() and not d.name.startswith('.'):
                    data_file = d / d.name
                    if data_file.exists():
                        lang_codes.append(d.name)

            lang_codes.sort()

        if max_languages:
            lang_codes = lang_codes[:max_languages]

        logger.info(
            f"Processing {len(lang_codes)} languages: {', '.join(lang_codes[:10])}{'...' if len(lang_codes) > 10 else ''}")

        successful = 0
        start_time = datetime.now()

        for i, lang_code in enumerate(lang_codes, 1):
            logger.info(f"[{i}/{len(lang_codes)}] Processing {lang_code}...")
            lang_start = datetime.now()

            if self.parse_language(lang_code):
                successful += 1
                elapsed = (datetime.now() - lang_start).total_seconds()
                logger.info(f"Completed {lang_code} in {elapsed:.2f} seconds")
            else:
                logger.warning(f"Failed to process {lang_code}")

        total_elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"Successfully processed {successful}/{len(lang_codes)} languages in {total_elapsed:.2f} seconds")

        # Print summary statistics
        total_verbs = sum(stats.get('lemmas', 0) for stats in self.stats.values())
        total_forms = sum(stats.get('verb_forms', 0) for stats in self.stats.values())
        logger.info(
            f"Total statistics: {total_verbs:,} unique verbs, {total_forms:,} verb forms across {successful} languages")


def main():
    parser = argparse.ArgumentParser(
        description="Parse UniMorph files and generate verb conjugation tables",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --languages eng spa fra
  %(prog)s --format json.gz --compress 9
  %(prog)s --output-dir ./data --max-languages 10
        """
    )
    parser.add_argument(
        '--data-dir',
        default='./unimorph_data',
        help='Path to UniMorph data directory (default: ./unimorph_data)'
    )
    parser.add_argument(
        '--output-dir',
        default='conjugation_data',
        help='Directory to save output files (default: conjugation_data)'
    )
    parser.add_argument(
        '--format',
        choices=['json', 'jsonl', 'json.gz'],
        default='json',
        help='Output file format: json (standard), jsonl (line-delimited), json.gz (compressed)'
    )
    parser.add_argument(
        '--compress',
        type=int,
        choices=range(0, 10),
        default=6,
        help='Compression level for gzip (0-9, default: 6)'
    )
    parser.add_argument(
        '--languages',
        nargs='+',
        help='Specific languages to process (space-separated language codes)'
    )
    parser.add_argument(
        '--max-languages',
        type=int,
        help='Maximum number of languages to process (for testing)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging (DEBUG level)'
    )
    parser.add_argument(
        '--no-cache',
        action='store_true',
        help='Disable caching (uses more memory but ensures fresh data)'
    )
    parser.add_argument(
        '--stats-only',
        action='store_true',
        help='Only show statistics without saving files'
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")

    logger.info("=" * 60)
    logger.info("UniMorph Verb Conjugation Parser")
    logger.info("=" * 60)
    logger.info(f"Data directory: {args.data_dir}")
    logger.info(f"Output directory: {args.output_dir}")
    logger.info(f"Output format: {args.format}")
    logger.info(f"Cache enabled: {not args.no_cache}")

    # Map format string to enum
    format_map = {
        'json': OutputFormat.JSON,
        'jsonl': OutputFormat.JSONL,
        'json.gz': OutputFormat.JSON_GZIP
    }
    output_format = format_map[args.format]

    # Initialize parser
    unimorph_parser = UniMorphParser(args.data_dir, cache_enabled=not args.no_cache)

    # Process languages
    unimorph_parser.process_all_languages(args.languages, args.max_languages)

    # Save results if not stats-only
    if not args.stats_only and unimorph_parser.conjugation_classes:
        unimorph_parser.save_results(args.output_dir, output_format, args.compress)

        # Print output file locations
        output_path = Path(args.output_dir)
        logger.info(f"\nOutput files saved to: {output_path.absolute()}")
        logger.info(f"  - verbs-*.{output_format.value.replace('.gz', '')}")
        logger.info(f"  - conjugations-*.{output_format.value.replace('.gz', '')}")
        logger.info(f"  - generation_metadata.json")

    logger.info("=" * 60)
    logger.info("UniMorph parser completed successfully")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
