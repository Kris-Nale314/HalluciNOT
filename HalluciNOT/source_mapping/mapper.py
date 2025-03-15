# Copyright (c) 2025 Kris Naleszkiewicz
# Licensed under the MIT License - see LICENSE file for details
"""
Source Mapping Module

This module is responsible for mapping extracted claims back to specific
document chunks in the source material. It identifies which parts of the
source documents support or contradict each claim.
"""

from typing import List, Dict, Any, Optional, Set, Tuple
import logging
import uuid
import re

from ..utils.common import Claim, DocumentChunk, DocumentStore, SourceReference, ClaimType

# Set up logging
logger = logging.getLogger(__name__)


class SourceMapper:
    """
    Maps claims to their potential sources in document chunks.
    
    The mapper identifies which document chunks (if any) support or
    contradict each claim, and calculates alignment scores between
    claims and potential sources.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the source mapper with configuration options.
        
        Args:
            config: Configuration options for source mapping
        """
        self.config = config or {}
        
        # Default configuration values
        self.min_alignment_score = self.config.get("min_alignment_score", 0.6)
        self.max_sources_per_claim = self.config.get("max_sources_per_claim", 3)
        self.use_semantic_search = self.config.get("use_semantic_search", True)
        self.enable_entity_matching = self.config.get("enable_entity_matching", True)
        
        # Initialize components if needed
        self._initialize_components()
        
        logger.debug("SourceMapper initialized with config: %s", self.config)
    
    def _initialize_components(self):
        """Initialize components needed for source mapping."""
        # TODO: Initialize actual components
        # Placeholder for now
        self._components_initialized = True
    
    def map_to_sources(
        self, 
        claims: List[Claim],
        document_store: DocumentStore
    ) -> List[Claim]:
        """
        Map claims to their potential sources in the document store.
        
        Args:
            claims: List of claims to map to sources
            document_store: Collection of document chunks to search for sources
            
        Returns:
            List of claims with source references added
        """
        logger.debug("Mapping %d claims to sources in document store with %d chunks", 
                   len(claims), document_store.count)
        
        # Process each claim to find matching sources
        for claim in claims:
            # Get potential sources for this claim
            potential_sources = self._find_potential_sources(claim, document_store)
            logger.debug("Found %d potential sources for claim: %s", 
                       len(potential_sources), claim.text[:50])
            
            # Calculate alignment scores for each potential source
            scored_sources = self._score_sources(claim, potential_sources)
            logger.debug("Scored %d sources for claim", len(scored_sources))
            
            # Filter sources by minimum alignment score
            valid_sources = [s for s in scored_sources 
                            if s.alignment_score >= self.min_alignment_score]
            
            # Sort by alignment score and limit to max sources per claim
            valid_sources.sort(key=lambda s: s.alignment_score, reverse=True)
            claim.sources = valid_sources[:self.max_sources_per_claim]
            
            # Add verification notes
            if claim.sources:
                claim.verification_notes = f"Found {len(claim.sources)} supporting sources"
            else:
                claim.verification_notes = "No supporting sources found"
        
        return claims
    
    def _find_potential_sources(
        self, 
        claim: Claim,
        document_store: DocumentStore
    ) -> List[DocumentChunk]:
        """
        Find potential source chunks for a claim.
        
        This is the first filtering step, using search techniques to
        narrow down the set of chunks that might support the claim.
        """
        # TODO: Implement more sophisticated source finding
        
        if self.use_semantic_search:
            # Use semantic search if available
            # This would typically involve comparing embeddings
            potential_sources = self._semantic_search(claim, document_store)
        else:
            # Fall back to keyword-based search
            potential_sources = self._keyword_search(claim, document_store)
        
        # Add entity-based matching if enabled
        if self.enable_entity_matching and claim.entities:
            entity_sources = self._entity_search(claim, document_store)
            
            # Combine sources, avoiding duplicates
            seen_ids = {chunk.id for chunk in potential_sources}
            for chunk in entity_sources:
                if chunk.id not in seen_ids:
                    potential_sources.append(chunk)
                    seen_ids.add(chunk.id)
        
        return potential_sources
    
    def _semantic_search(
        self, 
        claim: Claim,
        document_store: DocumentStore
    ) -> List[DocumentChunk]:
        """
        Find potential sources using semantic search.
        
        This would typically use embeddings to find semantically
        similar chunks, but is simplified here for demonstration.
        """
        # TODO: Implement actual semantic search
        # This is a placeholder that just uses the document store's search
        
        # In a real implementation, we might:
        # 1. Generate an embedding for the claim
        # 2. Compare to chunk embeddings using cosine similarity
        # 3. Return the top N matches
        
        return document_store.search(claim.text, limit=10)
    
    def _keyword_search(
        self, 
        claim: Claim,
        document_store: DocumentStore
    ) -> List[DocumentChunk]:
        """
        Find potential sources using keyword search.
        
        Extracts important keywords from the claim and searches
        for chunks containing those keywords.
        """
        # Extract important words from the claim
        # This is a simplified approach - would be more sophisticated in practice
        words = re.findall(r'\b[A-Za-z]{3,}\b', claim.text)
        
        # Focus on less common words which are more distinctive
        # Again, this is simplified - would use TF-IDF or similar in practice
        keywords = [w for w in words if len(w) > 4][:5]
        
        if not keywords:
            # Fall back to using all words if no distinctive keywords found
            keywords = words[:5]
        
        # Search for chunks containing these keywords
        # This is a simplified approach - would be more sophisticated in practice
        matching_chunks = []
        for chunk in document_store.get_all_chunks():
            if any(keyword.lower() in chunk.text.lower() for keyword in keywords):
                matching_chunks.append(chunk)
        
        return matching_chunks[:10]  # Limit to 10 matches
    
    def _entity_search(
        self, 
        claim: Claim,
        document_store: DocumentStore
    ) -> List[DocumentChunk]:
        """
        Find potential sources based on entity matching.
        
        Searches for chunks containing the same entities as the claim.
        """
        matching_chunks = []
        
        # Extract entity texts
        entity_texts = [entity["text"].lower() for entity in claim.entities]
        
        if not entity_texts:
            return []
        
        # Look for chunks containing these entities
        for chunk in document_store.get_all_chunks():
            chunk_text_lower = chunk.text.lower()
            if any(entity in chunk_text_lower for entity in entity_texts):
                matching_chunks.append(chunk)
        
        return matching_chunks[:10]  # Limit to 10 matches
    
    def _score_sources(
        self, 
        claim: Claim,
        chunks: List[DocumentChunk]
    ) -> List[SourceReference]:
        """
        Score potential source chunks based on alignment with the claim.
        
        Creates SourceReference objects with alignment scores.
        """
        scored_sources = []
        
        for chunk in chunks:
            # Calculate alignment score
            alignment_score = self._calculate_alignment_score(claim, chunk)
            
            # Create a SourceReference if the score is high enough
            if alignment_score > 0:
                # Extract the most relevant excerpt from the chunk
                excerpt = self._extract_relevant_excerpt(claim, chunk)
                
                source_ref = SourceReference(
                    chunk_id=chunk.id,
                    document_id=chunk.source_document,
                    text_excerpt=excerpt,
                    alignment_score=alignment_score,
                    context={
                        "boundary_type": chunk.boundary_type.value if chunk.boundary_type else None,
                        "parent_section": chunk.parent_section
                    }
                )
                
                scored_sources.append(source_ref)
        
        return scored_sources
    
    def _calculate_alignment_score(
        self, 
        claim: Claim,
        chunk: DocumentChunk
    ) -> float:
        """
        Calculate an alignment score between a claim and a document chunk.
        
        The score represents how well the chunk supports the claim.
        """
        # TODO: Implement more sophisticated alignment scoring
        # This is a simplified placeholder implementation
        
        # Different claim types might use different scoring approaches
        if claim.type == ClaimType.NUMERICAL:
            return self._score_numerical_claim(claim, chunk)
        elif claim.type == ClaimType.TEMPORAL:
            return self._score_temporal_claim(claim, chunk)
        else:
            return self._score_generic_claim(claim, chunk)
    
    def _score_numerical_claim(
        self, 
        claim: Claim,
        chunk: DocumentChunk
    ) -> float:
        """Score alignment for numerical claims."""
        # Extract numbers from claim and chunk
        claim_numbers = re.findall(r'\d+(\.\d+)?', claim.text)
        chunk_numbers = re.findall(r'\d+(\.\d+)?', chunk.text)
        
        # If the claim has numbers but the chunk doesn't, poor alignment
        if claim_numbers and not chunk_numbers:
            return 0.0
        
        # Check if any of the same numbers appear in both
        shared_numbers = set(claim_numbers).intersection(set(chunk_numbers))
        if shared_numbers:
            # Score based on the proportion of shared numbers
            return min(1.0, len(shared_numbers) / len(claim_numbers))
        
        # Fall back to generic scoring
        return self._score_generic_claim(claim, chunk) * 0.8  # Penalty for no number match
    
    def _score_temporal_claim(
        self, 
        claim: Claim,
        chunk: DocumentChunk
    ) -> float:
        """Score alignment for temporal claims."""
        # Extract dates/times from claim and chunk
        # This is a simplified approach - would be more sophisticated in practice
        date_pattern = r'\b(19|20)\d{2}\b|\b\d{1,2}/\d{1,2}/\d{2,4}\b'
        claim_dates = re.findall(date_pattern, claim.text)
        chunk_dates = re.findall(date_pattern, chunk.text)
        
        # Also look for month names
        month_pattern = r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\b'
        claim_months = re.findall(month_pattern, claim.text, re.IGNORECASE)
        chunk_months = re.findall(month_pattern, chunk.text, re.IGNORECASE)
        
        # If the claim has dates but the chunk doesn't, poor alignment
        if (claim_dates or claim_months) and not (chunk_dates or chunk_months):
            return 0.0
        
        # Check for shared dates/months
        shared_dates = set(claim_dates).intersection(set(chunk_dates))
        shared_months = set(map(str.lower, claim_months)).intersection(set(map(str.lower, chunk_months)))
        
        if shared_dates or shared_months:
            # Score based on the proportion of shared temporal references
            shared_count = len(shared_dates) + len(shared_months)
            total_count = len(claim_dates) + len(claim_months)
            return min(1.0, shared_count / total_count)
        
        # Fall back to generic scoring
        return self._score_generic_claim(claim, chunk) * 0.8  # Penalty for no date match
    
    def _score_generic_claim(
        self, 
        claim: Claim,
        chunk: DocumentChunk
    ) -> float:
        """
        Score alignment for generic claims.
        
        This is a simplified implementation that could be replaced with
        more sophisticated techniques like semantic similarity.
        """
        # Count word overlap between claim and chunk
        claim_words = set(re.findall(r'\b[A-Za-z]{3,}\b', claim.text.lower()))
        chunk_words = set(re.findall(r'\b[A-Za-z]{3,}\b', chunk.text.lower()))
        
        if not claim_words:
            return 0.0
        
        # Calculate Jaccard similarity
        intersection = claim_words.intersection(chunk_words)
        union = claim_words.union(chunk_words)
        
        if not union:
            return 0.0
        
        jaccard = len(intersection) / len(union)
        
        # Boost score if important entities are matched
        entity_boost = 0.0
        if claim.entities and self.enable_entity_matching:
            entity_texts = [entity["text"].lower() for entity in claim.entities]
            chunk_text_lower = chunk.text.lower()
            
            matched_entities = sum(1 for entity in entity_texts 
                                  if entity in chunk_text_lower)
            
            if matched_entities:
                entity_boost = 0.2 * min(1.0, matched_entities / len(entity_texts))
        
        # Combine scores
        return min(1.0, jaccard + entity_boost)
    
    def _extract_relevant_excerpt(
        self, 
        claim: Claim, 
        chunk: DocumentChunk
    ) -> str:
        """
        Extract the most relevant excerpt from a chunk for a claim.
        
        This helps highlight the specific part of the chunk that
        supports or relates to the claim.
        """
        # This is a simplified approach - would be more sophisticated in practice
        
        # If the chunk is short, use the whole thing
        if len(chunk.text) <= 200:
            return chunk.text
        
        # Try to find important words from the claim in the chunk
        important_words = set(re.findall(r'\b[A-Za-z]{4,}\b', claim.text.lower()))
        
        best_sentence = ""
        best_score = 0
        
        # Split chunk into sentences and find the one with most claim words
        sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|\!)\s', chunk.text)
        
        for sentence in sentences:
            if len(sentence) < 10:  # Skip very short sentences
                continue
                
            sentence_words = set(re.findall(r'\b[A-Za-z]{4,}\b', sentence.lower()))
            overlap = sentence_words.intersection(important_words)
            
            score = len(overlap) / max(1, len(important_words))
            
            if score > best_score:
                best_score = score
                best_sentence = sentence
        
        # If no good sentence found, return the first part of the chunk
        if not best_sentence:
            return chunk.text[:200] + "..."
        
        return best_sentence.strip()