# Copyright (c) 2025 Kris Naleszkiewicz
# Licensed under the MIT License - see LICENSE file for details

"""
Claim Extraction Module

This module is responsible for extracting discrete factual claims from
LLM responses. It identifies assertions that can be verified against
source documents and classifies them by type.
"""

from typing import List, Dict, Any, Optional, Tuple
import logging
import re
import uuid
import spacy
from collections import defaultdict

from ..utils.common import Claim, ClaimType

# Set up logging
logger = logging.getLogger(__name__)


class ClaimExtractor:
    """
    Extracts factual claims from LLM responses.
    
    The extractor identifies discrete factual assertions in text and
    classifies them by type for verification against source documents.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the claim extractor with configuration options.
        
        Args:
            config: Configuration options for claim extraction
        """
        self.config = config or {}
        
        # Default configuration values
        self.min_claim_length = self.config.get("min_claim_length", 5)
        self.max_claim_length = self.config.get("max_claim_length", 200)
        self.use_spacy = self.config.get("use_spacy", True)
        self.use_sentence_boundaries = self.config.get("use_sentence_boundaries", True)
        self.enable_entity_extraction = self.config.get("enable_entity_extraction", True)
        
        # Initialize components
        self._initialize_components()
        
        logger.debug("ClaimExtractor initialized with config: %s", self.config)
    
    def _initialize_components(self):
        """Initialize components needed for claim extraction."""
        try:
            if self.use_spacy:
                # Load a spaCy model for NLP tasks
                # Use 'en_core_web_sm' for better performance or 'en_core_web_md' for better accuracy
                self.nlp = spacy.load("en_core_web_sm")
                logger.debug("Loaded spaCy model for claim extraction")
            else:
                self.nlp = None
                logger.debug("Not using spaCy for claim extraction")
        except Exception as e:
            logger.warning("Could not load spaCy model; falling back to rule-based extraction: %s", e)
            self.nlp = None
            self.use_spacy = False
    
    def extract_claims(self, text: str) -> List[Claim]:
        """
        Extract factual claims from text.
        
        Args:
            text: Text to extract claims from (typically an LLM response)
            
        Returns:
            List of extracted claims
        """
        logger.debug("Extracting claims from text (%d characters)", len(text))
        
        if self.use_spacy and self.nlp is not None:
            # Use spaCy for claim extraction
            return self._extract_claims_spacy(text)
        else:
            # Fall back to rule-based extraction
            return self._extract_claims_rule_based(text)
    
    def _extract_claims_spacy(self, text: str) -> List[Claim]:
        """
        Extract claims using spaCy for NLP analysis.
        
        This approach uses linguistic features to identify factual statements.
        """
        claims = []
        
        # Process the text with spaCy
        doc = self.nlp(text)
        
        # Extract sentences as potential claims
        if self.use_sentence_boundaries:
            potential_claims = list(doc.sents)
        else:
            # If not using sentence boundaries, use a sliding window approach
            # This is a placeholder; in practice, would use more sophisticated chunking
            potential_claims = [doc[i:i+20] for i in range(0, len(doc), 10)]
        
        # Process each potential claim
        for span in potential_claims:
            # Skip if too short or too long
            if len(span.text) < self.min_claim_length or len(span.text) > self.max_claim_length:
                continue
            
            # Skip if not a factual claim
            if not self._is_factual_claim(span):
                continue
            
            # Create a claim object
            claim_type = self._determine_claim_type(span)
            claim_text = span.text.strip()
            start_idx = span.start_char
            end_idx = span.end_char
            
            # Extract entities if enabled
            entities = []
            if self.enable_entity_extraction:
                entities = self._extract_entities(span)
            
            # Create and add the claim
            claim = Claim(
                id=str(uuid.uuid4()),
                text=claim_text,
                type=claim_type,
                start_idx=start_idx,
                end_idx=end_idx,
                entities=entities
            )
            
            claims.append(claim)
        
        logger.debug("Extracted %d claims using spaCy", len(claims))
        return claims
    
    def _extract_claims_rule_based(self, text: str) -> List[Claim]:
        """
        Extract claims using rule-based heuristics.
        
        This is a fallback approach when spaCy is not available.
        """
        claims = []
        
        # Split into sentences using regex
        sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|\!)\s', text)
        
        # Process each sentence as a potential claim
        for sentence in sentences:
            clean_sentence = sentence.strip()
            
            # Skip if too short or too long
            if len(clean_sentence) < self.min_claim_length or len(clean_sentence) > self.max_claim_length:
                continue
            
            # Skip if not a factual claim (basic heuristics)
            if not self._is_factual_claim_text(clean_sentence):
                continue
            
            # Find the start and end indices in the original text
            # This is a simplified approach that may not be 100% accurate
            start_idx = text.find(clean_sentence)
            if start_idx == -1:
                # If exact match isn't found, use approximate position
                start_idx = text.lower().find(clean_sentence.lower())
                if start_idx == -1:
                    # Skip if we can't find position
                    continue
            
            end_idx = start_idx + len(clean_sentence)
            
            # Determine claim type using text-based heuristics
            claim_type = self._determine_claim_type_text(clean_sentence)
            
            # Extract entities if enabled (simplified approach)
            entities = []
            if self.enable_entity_extraction:
                entities = self._extract_entities_rule_based(clean_sentence)
            
            # Create and add the claim
            claim = Claim(
                id=str(uuid.uuid4()),
                text=clean_sentence,
                type=claim_type,
                start_idx=start_idx,
                end_idx=end_idx,
                entities=entities
            )
            
            claims.append(claim)
        
        logger.debug("Extracted %d claims using rule-based approach", len(claims))
        return claims
    
    def _is_factual_claim(self, span) -> bool:
        """
        Determine if a spaCy span represents a factual claim.
        
        Uses linguistic features to identify statements of fact.
        """
        # Skip questions
        if span.text.endswith("?"):
            return False
        
        # Skip imperative sentences (commands)
        if span[0].pos_ == "VERB" and span[0].tag_ in ["VB", "VBP"]:
            return False
        
        # Skip first-person statements (opinions)
        if any(token.text.lower() in ["i", "we", "my", "our"] and 
               token.pos_ == "PRON" for token in span[:3]):
            return False
        
        # Look for indicators of factual claims
        has_verb = any(token.pos_ == "VERB" for token in span)
        has_noun = any(token.pos_ == "NOUN" or token.pos_ == "PROPN" for token in span)
        
        # Most factual claims have both a noun and a verb
        return has_verb and has_noun
    
    def _is_factual_claim_text(self, text: str) -> bool:
        """
        Determine if text represents a factual claim using rule-based heuristics.
        
        This is a simplified approach when spaCy is not available.
        """
        # Skip questions
        if text.endswith("?"):
            return False
        
        # Skip imperatives (simplified check)
        first_word = text.split()[0].lower() if text.split() else ""
        if first_word in ["go", "do", "make", "try", "use", "find", "get", "see", "let", "take"]:
            return False
        
        # Skip first-person statements (opinions)
        if text.lower().startswith(("i ", "we ", "my ", "our ")):
            return False
        
        # Simple pattern matching for factual claims
        fact_patterns = [
            r' is ',
            r' are ',
            r' was ',
            r' were ',
            r' has ',
            r' have ',
            r' contains ',
            r' includes ',
            r' consists ',
            r' comprises ',
            r' equals ',
            r' means ',
            r' involves ',
            r' occurs ',
            r' happens ',
        ]
        
        for pattern in fact_patterns:
            if re.search(pattern, ' ' + text.lower() + ' '):
                return True
        
        # Check for statements with dates, numbers, or proper nouns
        # This is a simplified check; would be more sophisticated in practice
        has_number = bool(re.search(r'\d', text))
        has_date_pattern = bool(re.search(r'\b(in|on|during|since) (the )?\d{4}\b|\b\d{1,2}/\d{1,2}/\d{2,4}\b', text))
        has_proper_noun = bool(re.search(r'\b[A-Z][a-z]+\b', text))
        
        return has_number or has_date_pattern or has_proper_noun
    
    def _determine_claim_type(self, span) -> ClaimType:
        """
        Determine the type of a claim based on linguistic features.
        
        Uses spaCy analysis to categorize claims by content type.
        """
        text = span.text.lower()
        
        # Check for numerical claims
        has_number = any(token.like_num for token in span)
        has_money = any(token.ent_type_ == "MONEY" for token in span)
        has_quantity = any(token.ent_type_ in ["QUANTITY", "PERCENT", "CARDINAL"] for token in span)
        
        if has_money or has_quantity or has_number:
            return ClaimType.NUMERICAL
        
        # Check for temporal claims
        has_date = any(token.ent_type_ in ["DATE", "TIME"] for token in span)
        date_patterns = [r'\b(in|on|during|since) (the )?\d{4}\b', r'\b\d{1,2}/\d{1,2}/\d{2,4}\b']
        
        if has_date or any(re.search(pattern, text) for pattern in date_patterns):
            return ClaimType.TEMPORAL
        
        # Check for entity-focused claims
        named_entities = [ent for ent in span.ents if ent.label_ in ["PERSON", "ORG", "GPE", "LOC", "PRODUCT"]]
        if named_entities:
            return ClaimType.ENTITY
        
        # Check for causal claims
        causal_markers = ["because", "due to", "as a result", "therefore", "thus", "consequently", "leads to", "causes"]
        if any(marker in text for marker in causal_markers):
            return ClaimType.CAUSAL
        
        # Check for comparative claims
        comparative_markers = ["more", "less", "greater", "fewer", "better", "worse", "higher", "lower", "compared to"]
        if any(marker in text for marker in comparative_markers):
            return ClaimType.COMPARATIVE
        
        # Check for definitional claims
        if " is " in text or " are " in text:
            def_pattern = r'\b[A-Za-z]+ (is|are) (a|an|the) [A-Za-z]+\b'
            if re.search(def_pattern, text):
                return ClaimType.DEFINITIONAL
        
        # Check for citation claims
        citation_markers = ["according to", "cited by", "as stated in", "as reported by", "as shown by"]
        if any(marker in text for marker in citation_markers):
            return ClaimType.CITATION
        
        # Default to other
        return ClaimType.OTHER
    
    def _determine_claim_type_text(self, text: str) -> ClaimType:
        """
        Determine the type of a claim based on text patterns.
        
        Uses regex and text analysis when spaCy is not available.
        """
        text_lower = text.lower()
        
        # Check for numerical claims
        if re.search(r'\b\d+(\.\d+)?\b', text) or re.search(r'\b(zero|one|two|three|four|five|six|seven|eight|nine|ten)\b', text_lower):
            # Check for money specifically
            if re.search(r'\$\d+|\d+ dollars|\d+ euros|\d+ yen', text_lower):
                return ClaimType.NUMERICAL
            # Check for percentages
            if re.search(r'\d+(\.\d+)?( )?%|\d+( )?(percent|percentage)', text_lower):
                return ClaimType.NUMERICAL
            # Check for quantities
            if re.search(r'\d+( )?(kg|mb|gb|tb|mm|cm|m|km|inch|inches|feet|foot|yards|miles)', text_lower):
                return ClaimType.NUMERICAL
        
        # Check for temporal claims
        date_patterns = [
            r'\b(in|on|during|since) (the )?\d{4}\b',
            r'\b\d{1,2}/\d{1,2}/\d{2,4}\b',
            r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\b',
            r'\b\d{1,2}(st|nd|rd|th)?\b',
            r'\b(yesterday|today|tomorrow)\b',
            r'\b(year|month|week|day|hour|minute|century|decade)\b'
        ]
        
        if any(re.search(pattern, text, re.IGNORECASE) for pattern in date_patterns):
            return ClaimType.TEMPORAL
        
        # Check for entity-focused claims
        # This is a simplified approach; would be more sophisticated in practice
        if re.search(r'\b[A-Z][a-z]+ (is|was|has|have|will)\b', text):
            return ClaimType.ENTITY
        
        # Check for causal claims
        causal_markers = ["because", "due to", "as a result", "therefore", "thus", "consequently", "leads to", "causes"]
        if any(marker in text_lower for marker in causal_markers):
            return ClaimType.CAUSAL
        
        # Check for comparative claims
        comparative_markers = ["more", "less", "greater", "fewer", "better", "worse", "higher", "lower", "compared to"]
        if any(marker in text_lower for marker in comparative_markers):
            return ClaimType.COMPARATIVE
        
        # Check for definitional claims
        def_pattern = r'\b[A-Za-z]+ (is|are) (a|an|the) [A-Za-z]+\b'
        if re.search(def_pattern, text):
            return ClaimType.DEFINITIONAL
        
        # Check for citation claims
        citation_markers = ["according to", "cited by", "as stated in", "as reported by", "as shown by"]
        if any(marker in text_lower for marker in citation_markers):
            return ClaimType.CITATION
        
        # Default to other
        return ClaimType.OTHER
    
    def _extract_entities(self, span) -> List[Dict[str, Any]]:
        """
        Extract named entities from a spaCy span.
        
        Identifies people, organizations, locations, dates, etc.
        """
        entities = []
        
        for ent in span.ents:
            entity = {
                "text": ent.text,
                "label": ent.label_,
                "start": ent.start_char - span.start_char,
                "end": ent.end_char - span.start_char
            }
            entities.append(entity)
        
        return entities
    
    def _extract_entities_rule_based(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract entities using regex patterns when spaCy is not available.
        
        This is a simplified approach that focuses on common patterns.
        """
        entities = []
        
        # Match potential proper nouns (simplified approach)
        proper_noun_pattern = r'\b[A-Z][a-zA-Z]+ (?:[A-Z][a-zA-Z]+\s?)*'
        for match in re.finditer(proper_noun_pattern, text):
            entity = {
                "text": match.group(0).strip(),
                "label": "ENTITY",  # Generic label since we can't classify without NLP
                "start": match.start(),
                "end": match.end()
            }
            entities.append(entity)
        
        # Match dates (simplified approach)
        date_patterns = [
            r'\b\d{1,2}/\d{1,2}/\d{2,4}\b',
            r'\b(January|February|March|April|May|June|July|August|September|October|November|December) \d{1,2}(st|nd|rd|th)?, \d{4}\b'
        ]
        
        for pattern in date_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                entity = {
                    "text": match.group(0),
                    "label": "DATE",
                    "start": match.start(),
                    "end": match.end()
                }
                entities.append(entity)
        
        # Match monetary values
        money_pattern = r'\$\d+(?:,\d{3})*(?:\.\d{2})?|\d+(?:,\d{3})*(?:\.\d{2})? (dollars|euros|pounds)'
        for match in re.finditer(money_pattern, text):
            entity = {
                "text": match.group(0),
                "label": "MONEY",
                "start": match.start(),
                "end": match.end()
            }
            entities.append(entity)
        
        return entities


class ClaimMerger:
    """
    Merges related claims to avoid excessive fragmentation.
    
    This component can be used to combine claims that are closely
    related to improve verification efficiency.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the claim merger with configuration options.
        
        Args:
            config: Configuration options for claim merging
        """
        self.config = config or {}
        
        # Default configuration values
        self.max_distance = self.config.get("max_distance", 20)  # Max distance between claims to merge
        self.merge_same_type = self.config.get("merge_same_type", True)  # Only merge claims of same type
        
        logger.debug("ClaimMerger initialized with config: %s", self.config)
    
    def merge_claims(self, claims: List[Claim]) -> List[Claim]:
        """
        Merge related claims to improve verification efficiency.
        
        Args:
            claims: List of claims to potentially merge
            
        Returns:
            List of merged claims
        """
        if len(claims) <= 1:
            return claims
        
        # Sort claims by position
        sorted_claims = sorted(claims, key=lambda c: c.start_idx)
        
        # Track which claims should be merged
        merge_groups = []
        current_group = [0]  # Start with first claim
        
        for i in range(1, len(sorted_claims)):
            prev_claim = sorted_claims[current_group[-1]]
            current_claim = sorted_claims[i]
            
            # Check if claims should be merged
            if (current_claim.start_idx - prev_claim.end_idx <= self.max_distance and
                (not self.merge_same_type or current_claim.type == prev_claim.type)):
                # Add to current group
                current_group.append(i)
            else:
                # Finish current group and start a new one
                merge_groups.append(current_group)
                current_group = [i]
        
        # Add the last group
        if current_group:
            merge_groups.append(current_group)
        
        # Create merged claims
        merged_claims = []
        
        for group in merge_groups:
            if len(group) == 1:
                # No need to merge, just add the claim
                merged_claims.append(sorted_claims[group[0]])
            else:
                # Merge claims in this group
                merged_claim = self._merge_claim_group([sorted_claims[i] for i in group])
                merged_claims.append(merged_claim)
        
        logger.debug("Merged %d claims into %d claims", len(claims), len(merged_claims))
        return merged_claims
    
    def _merge_claim_group(self, claims: List[Claim]) -> Claim:
        """
        Merge a group of related claims into a single claim.
        
        Args:
            claims: List of related claims to merge
            
        Returns:
            Merged claim
        """
        # Get the full text span that encompasses all claims
        start_idx = min(claim.start_idx for claim in claims)
        end_idx = max(claim.end_idx for claim in claims)
        
        # Get the full text
        first_claim = min(claims, key=lambda c: c.start_idx)
        last_claim = max(claims, key=lambda c: c.end_idx)
        full_text = first_claim.text[:last_claim.start_idx - first_claim.start_idx] + last_claim.text
        
        # Determine the most appropriate claim type
        # Priority: numerical > temporal > entity > others
        type_priority = {
            ClaimType.NUMERICAL.value: 5,
            ClaimType.TEMPORAL.value: 4,
            ClaimType.ENTITY.value: 3,
            ClaimType.CAUSAL.value: 2,
            ClaimType.COMPARATIVE.value: 2,
            ClaimType.DEFINITIONAL.value: 2,
            ClaimType.CITATION.value: 1,
            ClaimType.OTHER.value: 0
        }
        
        claim_type = max(claims, key=lambda c: type_priority.get(c.type.value, 0)).type
        
        # Combine entities
        combined_entities = []
        seen_entity_texts = set()
        
        for claim in claims:
            for entity in claim.entities:
                # Adjust entity position relative to the merged claim
                adjusted_entity = entity.copy()
                adjusted_entity["start"] = entity["start"] + (claim.start_idx - start_idx)
                adjusted_entity["end"] = entity["end"] + (claim.start_idx - start_idx)
                
                # Only add if not already seen
                entity_key = (adjusted_entity["text"], adjusted_entity["label"])
                if entity_key not in seen_entity_texts:
                    combined_entities.append(adjusted_entity)
                    seen_entity_texts.add(entity_key)
        
        # Create the merged claim
        merged_claim = Claim(
            id=str(uuid.uuid4()),
            text=full_text,
            type=claim_type,
            start_idx=start_idx,
            end_idx=end_idx,
            entities=combined_entities
        )
        
        return merged_claim