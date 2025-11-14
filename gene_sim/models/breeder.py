"""Breeder models for selecting mating pairs."""

from abc import ABC, abstractmethod
from typing import List, Tuple, Optional, TYPE_CHECKING
import numpy as np

if TYPE_CHECKING:
    from .creature import Creature
    from ..config import SimulationConfig
else:
    from .creature import Creature


class Breeder(ABC):
    """Abstract base class for breeder strategies."""
    
    def __init__(
        self,
        undesirable_phenotypes: Optional[List[dict]] = None,
        undesirable_genotypes: Optional[List[dict]] = None,
        avoid_undesirable_phenotypes: bool = False,
        avoid_undesirable_genotypes: bool = False,
        max_creatures: int = 7
    ):
        """
        Initialize breeder.
        
        Args:
            undesirable_phenotypes: List of {trait_id, phenotype} dicts to avoid
            undesirable_genotypes: List of {trait_id, genotype} dicts to avoid
            avoid_undesirable_phenotypes: If True, filter out creatures with undesirable phenotypes
            avoid_undesirable_genotypes: If True, filter out creatures with undesirable genotypes
            max_creatures: Maximum number of creatures this breeder can own
        """
        self.breeder_id: Optional[int] = None
        self.undesirable_phenotypes = undesirable_phenotypes or []
        self.undesirable_genotypes = undesirable_genotypes or []
        self.avoid_undesirable_phenotypes = avoid_undesirable_phenotypes
        self.avoid_undesirable_genotypes = avoid_undesirable_genotypes
        self.max_creatures = max_creatures
    
    def _has_undesirable_phenotype(self, creature: 'Creature', traits: List) -> bool:
        """Check if creature has any undesirable phenotype."""
        if not self.avoid_undesirable_phenotypes or not self.undesirable_phenotypes:
            return False
        
        from .trait import Trait
        
        for undesirable in self.undesirable_phenotypes:
            trait_id = undesirable['trait_id']
            undesirable_phenotype = undesirable['phenotype']
            
            if trait_id >= len(creature.genome) or creature.genome[trait_id] is None:
                continue
            
            # Find trait to get phenotype mapping
            trait = next((t for t in traits if t.trait_id == trait_id), None)
            if trait is None:
                continue
            
            actual_phenotype = trait.get_phenotype(creature.genome[trait_id], creature.sex)
            if actual_phenotype == undesirable_phenotype:
                return True
        
        return False
    
    def _has_undesirable_genotype(self, creature: 'Creature') -> bool:
        """Check if creature has any undesirable genotype."""
        if not self.avoid_undesirable_genotypes or not self.undesirable_genotypes:
            return False
        
        for undesirable in self.undesirable_genotypes:
            trait_id = undesirable['trait_id']
            undesirable_genotype = undesirable['genotype']
            
            if trait_id >= len(creature.genome) or creature.genome[trait_id] is None:
                continue
            
            if creature.genome[trait_id] == undesirable_genotype:
                return True
        
        return False
    
    def _filter_undesirable(self, creatures: List['Creature'], traits: List) -> List['Creature']:
        """Filter out creatures with undesirable phenotypes or genotypes."""
        filtered = []
        for creature in creatures:
            if self._has_undesirable_phenotype(creature, traits):
                continue
            if self._has_undesirable_genotype(creature):
                continue
            filtered.append(creature)
        return filtered
    
    def select_replacement(
        self,
        candidates: List['Creature'],
        sex: str,
        traits: List,
        rng: np.random.Generator
    ) -> Optional['Creature']:
        """
        Select best replacement creature from candidates.
        Base implementation: random selection after filtering undesirables.
        
        Args:
            candidates: List of potential replacement creatures
            sex: Required sex ('male' or 'female')
            traits: List of trait definitions
            rng: Random number generator
            
        Returns:
            Best replacement creature, or None if no suitable candidates
        """
        # Filter by sex
        sex_filtered = [c for c in candidates if c.sex == sex]
        if not sex_filtered:
            return None
        
        # Filter out undesirables
        filtered = self._filter_undesirable(sex_filtered, traits)
        
        # If filtering removed all candidates, use sex-filtered list
        if not filtered:
            filtered = sex_filtered
        
        # Random selection
        return rng.choice(filtered) if filtered else None
    
    @abstractmethod
    def select_pairs(
        self,
        eligible_males: List['Creature'],
        eligible_females: List['Creature'],
        num_pairs: int,
        rng: np.random.Generator
    ) -> List[Tuple['Creature', 'Creature']]:
        """
        Select mating pairs from eligible creatures.
        
        Args:
            eligible_males: Pre-filtered list of eligible male creatures
            eligible_females: Pre-filtered list of eligible female creatures
            num_pairs: Number of pairs to select
            rng: Seeded random number generator
            
        Returns:
            List of (male, female) tuples for reproduction
        """
        pass


class RandomBreeder(Breeder):
    """Randomly pairs eligible males and females with no selection bias."""
    
    def select_pairs(
        self,
        eligible_males: List['Creature'],
        eligible_females: List['Creature'],
        num_pairs: int,
        rng: np.random.Generator,
        traits: List = None
    ) -> List[Tuple['Creature', 'Creature']]:
        """Randomly select pairs."""
        if not eligible_males or not eligible_females:
            return []
        
        # Filter out undesirable creatures if avoidance is enabled
        if traits is None:
            traits = []
        filtered_males = self._filter_undesirable(eligible_males, traits)
        filtered_females = self._filter_undesirable(eligible_females, traits)
        
        # If filtering removed all candidates, fall back to original lists
        if not filtered_males:
            filtered_males = eligible_males
        if not filtered_females:
            filtered_females = eligible_females
        
        pairs = []
        for _ in range(num_pairs):
            male = rng.choice(filtered_males)
            female = rng.choice(filtered_females)
            pairs.append((male, female))
        
        return pairs


class InbreedingAvoidanceBreeder(Breeder):
    """Avoids pairs that would produce offspring with high inbreeding coefficient."""
    
    def __init__(
        self,
        max_inbreeding_coefficient: float = 0.25,
        undesirable_phenotypes: Optional[List[dict]] = None,
        undesirable_genotypes: Optional[List[dict]] = None,
        avoid_undesirable_phenotypes: bool = False,
        avoid_undesirable_genotypes: bool = False,
        max_creatures: int = 7
    ):
        """
        Initialize inbreeding avoidance breeder.
        
        Args:
            max_inbreeding_coefficient: Maximum allowed inbreeding coefficient for offspring
            undesirable_phenotypes: List of {trait_id, phenotype} dicts to avoid
            undesirable_genotypes: List of {trait_id, genotype} dicts to avoid
            avoid_undesirable_phenotypes: If True, filter out creatures with undesirable phenotypes
            avoid_undesirable_genotypes: If True, filter out creatures with undesirable genotypes
            max_creatures: Maximum number of creatures this breeder can own
        """
        super().__init__(undesirable_phenotypes, undesirable_genotypes, avoid_undesirable_phenotypes, avoid_undesirable_genotypes, max_creatures)
        self.max_inbreeding_coefficient = max_inbreeding_coefficient
    
    def select_pairs(
        self,
        eligible_males: List['Creature'],
        eligible_females: List['Creature'],
        num_pairs: int,
        rng: np.random.Generator,
        traits: List = None
    ) -> List[Tuple['Creature', 'Creature']]:
        """Select pairs that avoid high inbreeding."""
        if not eligible_males or not eligible_females:
            return []
        
        # Filter out undesirable creatures if avoidance is enabled
        if traits is None:
            traits = []
        filtered_males = self._filter_undesirable(eligible_males, traits)
        filtered_females = self._filter_undesirable(eligible_females, traits)
        
        # If filtering removed all candidates, fall back to original lists
        if not filtered_males:
            filtered_males = eligible_males
        if not filtered_females:
            filtered_females = eligible_females
        
        pairs = []
        attempts = 0
        max_attempts = num_pairs * 100  # Prevent infinite loops
        
        while len(pairs) < num_pairs and attempts < max_attempts:
            male = rng.choice(filtered_males)
            female = rng.choice(filtered_females)
            
            # Calculate potential offspring inbreeding coefficient
            potential_f = Creature.calculate_inbreeding_coefficient(male, female)
            
            if potential_f <= self.max_inbreeding_coefficient:
                pairs.append((male, female))
            
            attempts += 1
        
        # If we couldn't find enough pairs, fill with random pairs
        while len(pairs) < num_pairs:
            male = rng.choice(filtered_males)
            female = rng.choice(filtered_females)
            pairs.append((male, female))
        
        return pairs


class KennelClubBreeder(Breeder):
    """Selects pairs based on target phenotypes with kennel club guidelines."""
    
    def __init__(
        self,
        target_phenotypes: List[dict],
        max_inbreeding_coefficient: Optional[float] = None,
        required_phenotype_ranges: Optional[List[dict]] = None,
        undesirable_phenotypes: Optional[List[dict]] = None,
        undesirable_genotypes: Optional[List[dict]] = None,
        genotype_preferences: Optional[List[dict]] = None,
        avoid_undesirable_phenotypes: bool = False,
        avoid_undesirable_genotypes: bool = False,
        max_creatures: int = 7
    ):
        """
        Initialize kennel club breeder.
        
        Args:
            target_phenotypes: List of {trait_id, phenotype} dicts
            max_inbreeding_coefficient: Maximum allowed inbreeding (optional)
            required_phenotype_ranges: List of {trait_id, min, max} dicts (optional)
            undesirable_phenotypes: List of {trait_id, phenotype} dicts to avoid
            undesirable_genotypes: List of {trait_id, genotype} dicts to avoid (legacy)
            genotype_preferences: List of {trait_id, optimal, acceptable, undesirable} dicts
            avoid_undesirable_phenotypes: If True, filter out creatures with undesirable phenotypes
            avoid_undesirable_genotypes: If True, filter out creatures with undesirable genotypes
            max_creatures: Maximum number of creatures this breeder can own
        """
        super().__init__(undesirable_phenotypes, undesirable_genotypes, avoid_undesirable_phenotypes, avoid_undesirable_genotypes, max_creatures)
        self.target_phenotypes = target_phenotypes
        self.max_inbreeding_coefficient = max_inbreeding_coefficient
        self.required_phenotype_ranges = required_phenotype_ranges or []
        self.genotype_preferences = genotype_preferences or []
        
        # Cache for genotype pairing scores: {(trait_id, genotype1, genotype2): score}
        self._pairing_score_cache = {}
    
    def _get_genotype_tier(self, creature: 'Creature', trait_id: int) -> int:
        """
        Get preference tier for a creature's genotype.
        
        Returns:
            0 = optimal, 1 = acceptable, 2 = undesirable, 3 = not configured
        """
        if not self.genotype_preferences:
            return 3  # Not configured, use legacy behavior
        
        # Find preference config for this trait
        pref = next((p for p in self.genotype_preferences if p['trait_id'] == trait_id), None)
        if not pref:
            return 3  # Not configured for this trait
        
        if trait_id >= len(creature.genome) or creature.genome[trait_id] is None:
            return 3
        
        genotype = creature.genome[trait_id]
        
        if genotype in pref.get('optimal', []):
            return 0
        elif genotype in pref.get('acceptable', []):
            return 1
        elif genotype in pref.get('undesirable', []):
            return 2
        else:
            return 3
    
    def _has_acceptable_or_better_genotypes(self, creature: 'Creature') -> bool:
        """Check if creature has only optimal or acceptable genotypes (no undesirable)."""
        if not self.genotype_preferences:
            return not self._has_undesirable_genotype(creature)  # Legacy behavior
        
        for pref in self.genotype_preferences:
            trait_id = pref['trait_id']
            tier = self._get_genotype_tier(creature, trait_id)
            if tier == 2:  # Undesirable
                return False
        return True
    
    def _has_optimal_genotype(self, creature: 'Creature', trait_id: int) -> bool:
        """Check if creature has optimal genotype for a specific trait."""
        return self._get_genotype_tier(creature, trait_id) == 0
    
    def _matches_target_phenotypes(self, creature: 'Creature', traits: List) -> bool:
        """Check if creature matches target phenotypes."""
        from .trait import Trait
        
        for target in self.target_phenotypes:
            trait_id = target['trait_id']
            target_phenotype = target['phenotype']
            
            if trait_id >= len(creature.genome) or creature.genome[trait_id] is None:
                return False
            
            # Find trait to get phenotype mapping
            trait = next((t for t in traits if t.trait_id == trait_id), None)
            if trait is None:
                return False
            
            actual_phenotype = trait.get_phenotype(creature.genome[trait_id], creature.sex)
            if actual_phenotype != target_phenotype:
                return False
        
        return True
    
    def _matches_phenotype_ranges(self, creature: 'Creature', traits: List) -> bool:
        """Check if creature matches required phenotype ranges."""
        from .trait import Trait
        
        for range_req in self.required_phenotype_ranges:
            trait_id = range_req['trait_id']
            min_val = float(range_req['min'])
            max_val = float(range_req['max'])
            
            if trait_id >= len(creature.genome) or creature.genome[trait_id] is None:
                return False
            
            trait = next((t for t in traits if t.trait_id == trait_id), None)
            if trait is None:
                return False
            
            phenotype_str = trait.get_phenotype(creature.genome[trait_id], creature.sex)
            try:
                phenotype_val = float(phenotype_str)
                if not (min_val <= phenotype_val <= max_val):
                    return False
            except ValueError:
                # Not a numeric phenotype, skip range check
                pass
        
        return True
    
    def _calculate_offspring_probabilities(self, genotype1: str, genotype2: str) -> dict:
        """
        Calculate Mendelian offspring probabilities for a genotype pairing.
        
        Args:
            genotype1: First parent's genotype (e.g., "Aa")
            genotype2: Second parent's genotype (e.g., "Aa")
            
        Returns:
            Dict mapping offspring genotypes to probabilities (0.0 to 1.0)
        """
        # Extract alleles (assumes diploid with 2-character genotypes)
        if len(genotype1) != 2 or len(genotype2) != 2:
            return {}
        
        allele1_p1, allele2_p1 = genotype1[0], genotype1[1]
        allele1_p2, allele2_p2 = genotype2[0], genotype2[1]
        
        # Generate all possible offspring genotypes from Punnett square
        offspring_counts = {}
        for a1 in [allele1_p1, allele2_p1]:
            for a2 in [allele1_p2, allele2_p2]:
                # Normalize genotype (uppercase first, or alphabetical)
                if a1.isupper() and a2.islower():
                    offspring = a1 + a2
                elif a2.isupper() and a1.islower():
                    offspring = a2 + a1
                elif a1.isupper() and a2.isupper():
                    offspring = ''.join(sorted([a1, a2], reverse=True))
                else:
                    offspring = ''.join(sorted([a1, a2]))
                
                offspring_counts[offspring] = offspring_counts.get(offspring, 0) + 1
        
        # Convert counts to probabilities
        total = sum(offspring_counts.values())
        return {genotype: count / total for genotype, count in offspring_counts.items()}
    
    def _score_genotype_pairing(self, trait_id: int, genotype1: str, genotype2: str) -> float:
        """
        Score a genotype pairing for a specific trait based on expected offspring quality.
        Uses caching for performance.
        
        Args:
            trait_id: The trait being evaluated
            genotype1: First parent's genotype
            genotype2: Second parent's genotype
            
        Returns:
            Score (higher is better). Weighted heavily toward optimal outcomes.
        """
        # Check cache first (order-independent key)
        cache_key = (trait_id, tuple(sorted([genotype1, genotype2])))
        if cache_key in self._pairing_score_cache:
            return self._pairing_score_cache[cache_key]
        
        # Find preference config for this trait
        pref = next((p for p in self.genotype_preferences if p['trait_id'] == trait_id), None)
        if not pref:
            # No preference configured, neutral score
            self._pairing_score_cache[cache_key] = 0.0
            return 0.0
        
        # Calculate offspring probabilities
        offspring_probs = self._calculate_offspring_probabilities(genotype1, genotype2)
        
        # Score based on preference tiers with heavy weighting for desirable outcomes
        score = 0.0
        for offspring_genotype, probability in offspring_probs.items():
            if offspring_genotype in pref.get('optimal', []):
                # Optimal genotypes: +100 points per 100% probability
                score += 100.0 * probability
            elif offspring_genotype in pref.get('acceptable', []):
                # Acceptable genotypes: +10 points per 100% probability
                score += 10.0 * probability
            elif offspring_genotype in pref.get('undesirable', []):
                # Undesirable genotypes: -50 points per 100% probability
                score -= 50.0 * probability
        
        self._pairing_score_cache[cache_key] = score
        return score
    
    def _score_pairing(self, male: 'Creature', female: 'Creature') -> float:
        """
        Score a male-female pairing based on expected offspring quality across all traits.
        
        Args:
            male: Male creature
            female: Female creature
            
        Returns:
            Total score (higher is better)
        """
        if not self.genotype_preferences:
            return 0.0  # No preferences configured
        
        total_score = 0.0
        for pref in self.genotype_preferences:
            trait_id = pref['trait_id']
            
            # Get genotypes for this trait
            if (trait_id >= len(male.genome) or male.genome[trait_id] is None or
                trait_id >= len(female.genome) or female.genome[trait_id] is None):
                continue
            
            male_genotype = male.genome[trait_id]
            female_genotype = female.genome[trait_id]
            
            # Score this trait pairing
            trait_score = self._score_genotype_pairing(trait_id, male_genotype, female_genotype)
            total_score += trait_score
        
        return total_score
    
    def select_pairs(
        self,
        eligible_males: List['Creature'],
        eligible_females: List['Creature'],
        num_pairs: int,
        rng: np.random.Generator,
        traits: List = None
    ) -> List[Tuple['Creature', 'Creature']]:
        """
        Select pairs based on target phenotypes with tiered genotype preferences.
        
        Preference order:
        1. Optimal genotypes only (e.g., LL)
        2. Acceptable genotypes (e.g., Ll) - temporary until optimal available
        3. Mix of acceptable and optimal
        4. Fall back to undesirable if absolutely necessary
        """
        if not eligible_males or not eligible_females:
            return []
        
        if traits is None:
            traits = []
        
        # Start with all eligible creatures
        filtered_males = eligible_males.copy()
        filtered_females = eligible_females.copy()
        
        # Use new preference system if configured, otherwise legacy
        if self.genotype_preferences:
            # Tiered filtering: try optimal > acceptable > undesirable as fallback
            # Tier 0: Creatures with optimal genotypes (e.g., LL)
            optimal_males = [m for m in filtered_males if all(
                self._get_genotype_tier(m, p['trait_id']) == 0 
                for p in self.genotype_preferences
            )]
            optimal_females = [f for f in filtered_females if all(
                self._get_genotype_tier(f, p['trait_id']) == 0 
                for p in self.genotype_preferences
            )]
            
            # Tier 1: Creatures with acceptable or better (e.g., LL or Ll, but not ll)
            acceptable_or_better_males = [m for m in filtered_males if self._has_acceptable_or_better_genotypes(m)]
            acceptable_or_better_females = [f for f in filtered_females if self._has_acceptable_or_better_genotypes(f)]
            
            # Try optimal first, fall back to acceptable, then fall back to all
            if optimal_males and optimal_females:
                filtered_males = optimal_males
                filtered_females = optimal_females
            elif acceptable_or_better_males and acceptable_or_better_females:
                filtered_males = acceptable_or_better_males
                filtered_females = acceptable_or_better_females
            # else: use all filtered (fallback to undesirable if necessary)
            
        else:
            # Legacy: filter out undesirable genotypes
            if self.undesirable_genotypes:
                for undesirable in self.undesirable_genotypes:
                    trait_id = undesirable['trait_id']
                    undesirable_genotype = undesirable['genotype']
                    filtered_males = [m for m in filtered_males 
                                    if trait_id >= len(m.genome) or m.genome[trait_id] is None or m.genome[trait_id] != undesirable_genotype]
                    filtered_females = [f for f in filtered_females 
                                      if trait_id >= len(f.genome) or f.genome[trait_id] is None or f.genome[trait_id] != undesirable_genotype]
            
            # If filtering removed all candidates, fall back to original lists
            if not filtered_males:
                filtered_males = eligible_males
            if not filtered_females:
                filtered_females = eligible_females
        
        # Filter undesirable phenotypes if global flag is enabled
        if self.avoid_undesirable_phenotypes:
            filtered_males = [m for m in filtered_males if not self._has_undesirable_phenotype(m, traits)]
            filtered_females = [f for f in filtered_females if not self._has_undesirable_phenotype(f, traits)]
        
        # Filter creatures that match target phenotypes
        matching_males = [m for m in filtered_males if self._matches_target_phenotypes(m, traits)]
        matching_females = [f for f in filtered_females if self._matches_target_phenotypes(f, traits)]
        
        # If no matches, fall back to filtered lists (which may be original if no filtering)
        if not matching_males:
            matching_males = filtered_males
        if not matching_females:
            matching_females = filtered_females
        
        # NEW: Intelligent pairing selection using genetic scoring
        # Generate and score all possible pairings, then select best ones
        if self.genotype_preferences and matching_males and matching_females:
            # Generate all possible pairings
            all_possible_pairings = []
            for male in matching_males:
                for female in matching_females:
                    # Check inbreeding limit if set
                    if self.max_inbreeding_coefficient is not None:
                        potential_f = Creature.calculate_inbreeding_coefficient(male, female)
                        if potential_f > self.max_inbreeding_coefficient:
                            continue
                    
                    # Check phenotype ranges if set
                    if self.required_phenotype_ranges:
                        if not (self._matches_phenotype_ranges(male, traits) and 
                                self._matches_phenotype_ranges(female, traits)):
                            continue
                    
                    # Score this pairing based on expected offspring quality
                    score = self._score_pairing(male, female)
                    all_possible_pairings.append((score, male, female))
            
            if not all_possible_pairings:
                # No valid pairings found, return empty
                return []
            
            # Sort by score (highest first)
            all_possible_pairings.sort(key=lambda x: x[0], reverse=True)
            
            # Select best unique pairings (avoid reusing same creature multiple times if possible)
            pairs = []
            used_males = set()
            used_females = set()
            
            # First pass: select best non-overlapping pairings
            for score, male, female in all_possible_pairings:
                if len(pairs) >= num_pairs:
                    break
                if male.creature_id not in used_males and female.creature_id not in used_females:
                    pairs.append((male, female))
                    used_males.add(male.creature_id)
                    used_females.add(female.creature_id)
            
            # Second pass: fill remaining slots with best available (allows reuse)
            if len(pairs) < num_pairs:
                remaining_needed = num_pairs - len(pairs)
                for score, male, female in all_possible_pairings:
                    if len(pairs) >= num_pairs:
                        break
                    # Allow this pairing even if creatures are reused
                    if (male, female) not in pairs:
                        pairs.append((male, female))
            
            return pairs
        
        # Legacy behavior: random selection with constraints
        pairs = []
        attempts = 0
        max_attempts = num_pairs * 100
        
        while len(pairs) < num_pairs and attempts < max_attempts:
            male = rng.choice(matching_males)
            female = rng.choice(matching_females)
            
            # Check inbreeding limit if set
            if self.max_inbreeding_coefficient is not None:
                potential_f = Creature.calculate_inbreeding_coefficient(male, female)
                if potential_f > self.max_inbreeding_coefficient:
                    attempts += 1
                    continue
            
            # Check phenotype ranges if set
            if self.required_phenotype_ranges:
                if not (self._matches_phenotype_ranges(male, traits) and 
                        self._matches_phenotype_ranges(female, traits)):
                    attempts += 1
                    continue
            
            pairs.append((male, female))
            attempts += 1
        
        # Fill remaining with random pairs if needed
        while len(pairs) < num_pairs:
            male = rng.choice(filtered_males)
            female = rng.choice(filtered_females)
            pairs.append((male, female))
        
        return pairs
    
    def select_replacement(
        self,
        candidates: List['Creature'],
        sex: str,
        traits: List,
        rng: np.random.Generator
    ) -> Optional['Creature']:
        """
        Select best replacement for kennel club breeder.
        Priority: No undesirable genotypes > Best genotype for target phenotype.
        
        For dominant traits: prefer homozygous dominant (AA)
        For recessive traits: prefer homozygous recessive (aa)
        
        Args:
            candidates: List of potential replacement creatures
            sex: Required sex ('male' or 'female')
            traits: List of trait definitions
            rng: Random number generator
            
        Returns:
            Best replacement creature, or None if no suitable candidates
        """
        from .trait import Trait
        
        # Filter by sex
        sex_filtered = [c for c in candidates if c.sex == sex]
        if not sex_filtered:
            return None
        
        # Use new preference system if available
        if self.genotype_preferences:
            # Tier-based scoring with strong preference for optimal genotypes
            def score_candidate_tiered(creature: 'Creature') -> int:
                """Score based on genotype preference tiers."""
                score = 0
                
                for pref in self.genotype_preferences:
                    trait_id = pref['trait_id']
                    tier = self._get_genotype_tier(creature, trait_id)
                    
                    # Heavily weight optimal genotypes
                    if tier == 0:  # Optimal (e.g., LL)
                        score += 100
                    elif tier == 1:  # Acceptable (e.g., Ll)
                        score += 10
                    elif tier == 2:  # Undesirable (e.g., ll)
                        score += 0
                    # tier == 3: not configured, neutral
                
                # Also check target phenotypes
                for target in self.target_phenotypes:
                    trait_id = target['trait_id']
                    target_phenotype = target['phenotype']
                    
                    if trait_id >= len(creature.genome) or creature.genome[trait_id] is None:
                        continue
                    
                    trait = next((t for t in traits if t.trait_id == trait_id), None)
                    if trait is None:
                        continue
                    
                    genotype = creature.genome[trait_id]
                    phenotype = trait.get_phenotype(genotype, creature.sex)
                    
                    if phenotype == target_phenotype:
                        score += 5  # Bonus for target phenotype match
                
                return score
            
            # Score all candidates
            scored = [(c, score_candidate_tiered(c)) for c in sex_filtered]
            max_score = max(score for _, score in scored)
            best_candidates = [c for c, score in scored if score == max_score]
            
            return rng.choice(best_candidates) if best_candidates else None
        
        # Legacy behavior: filter out undesirable genotypes
        filtered = sex_filtered.copy()
        if self.undesirable_genotypes:
            for undesirable in self.undesirable_genotypes:
                trait_id = undesirable['trait_id']
                undesirable_genotype = undesirable['genotype']
                filtered = [c for c in filtered 
                           if trait_id >= len(c.genome) or c.genome[trait_id] is None or c.genome[trait_id] != undesirable_genotype]
        
        if not filtered:
            return None
        
        # Score each candidate based on genotypes for target phenotypes
        def score_candidate(creature: 'Creature') -> int:
            """Score based on optimal genotypes for target phenotypes."""
            score = 0
            for target in self.target_phenotypes:
                trait_id = target['trait_id']
                target_phenotype = target['phenotype']
                
                if trait_id >= len(creature.genome) or creature.genome[trait_id] is None:
                    continue
                
                # Find trait definition
                trait = next((t for t in traits if t.trait_id == trait_id), None)
                if trait is None:
                    continue
                
                genotype = creature.genome[trait_id]
                phenotype = trait.get_phenotype(genotype, creature.sex)
                
                # Check if phenotype matches target
                if phenotype == target_phenotype:
                    # Bonus for matching phenotype
                    score += 10
                    
                    # Additional bonus for homozygous genotypes
                    # This helps stabilize the trait
                    if len(genotype) == 2 and genotype[0] == genotype[1]:
                        score += 5  # Homozygous bonus (AA or aa)
                    
            return score
        
        # Find candidates with highest scores
        scored = [(c, score_candidate(c)) for c in filtered]
        max_score = max(score for _, score in scored)
        best_candidates = [c for c, score in scored if score == max_score]
        
        # Return random choice from best candidates
        return rng.choice(best_candidates) if best_candidates else None

    def _score_creature_genotypes(self, creature: 'Creature') -> tuple:
        """
        Score a creature based on genotype tiers.
        
        Returns tuple of (optimal_count, acceptable_count, undesirable_count, not_configured_count)
        Lower tier numbers are better (0=optimal, 1=acceptable, 2=undesirable, 3=not configured).
        """
        counts = [0, 0, 0, 0]  # [optimal, acceptable, undesirable, not_configured]
        
        for trait_id in range(len(creature.genome)):
            if creature.genome[trait_id] is None:
                continue
            
            tier = self._get_genotype_tier(creature, trait_id)
            counts[tier] += 1
        
        return tuple(counts)
    
    def evaluate_offspring_vs_parents(
        self,
        offspring: List['Creature'],
        parents: List['Creature'],
        rng: np.random.Generator
    ) -> dict:
        """
        Evaluate offspring vs parents to determine which offspring to keep and which parents to trade.
        
        Kennels get "first dibs" on their offspring - they compare each offspring's genotypes to both
        parents and keep offspring that are superior (more optimal/acceptable genotypes, fewer undesirable).
        Inferior parents are marked for trading to make room.
        
        Args:
            offspring: List of offspring creatures produced by this breeder
            parents: List of parent creatures currently owned by this breeder
            rng: Random number generator for tie-breaking
        
        Returns:
            dict with:
                - 'keep_offspring': List of offspring to retain
                - 'trade_parents': List of parents to trade away
                - 'release_offspring': List of offspring to release for trading
        """
        if not offspring or not parents:
            return {
                'keep_offspring': [],
                'trade_parents': [],
                'release_offspring': offspring.copy() if offspring else []
            }
        
        # Score all offspring and parents
        offspring_scores = [(o, self._score_creature_genotypes(o)) for o in offspring]
        parent_scores = [(p, self._score_creature_genotypes(p)) for p in parents]
        
        # Sort offspring by quality (more optimal, then fewer undesirable, then fewer not_configured)
        # Better score = more optimal (index 0), fewer undesirable (index 2)
        offspring_scores.sort(key=lambda x: (-x[1][0], x[1][2], x[1][3]), reverse=False)
        
        # Sort parents by quality (worst first - these will be traded)
        parent_scores.sort(key=lambda x: (-x[1][0], x[1][2], x[1][3]), reverse=True)
        
        keep_offspring = []
        trade_parents = []
        release_offspring = []
        
        # Compare each offspring to the worst parent
        # If offspring is better, keep offspring and mark parent for trading
        offspring_idx = 0
        parent_idx = 0
        
        while offspring_idx < len(offspring_scores) and parent_idx < len(parent_scores):
            offspring_creature, offspring_score = offspring_scores[offspring_idx]
            parent_creature, parent_score = parent_scores[parent_idx]
            
            # Compare scores: offspring is better if it has:
            # 1. More optimal genotypes, OR
            # 2. Same optimal but fewer undesirable, OR
            # 3. Same optimal and undesirable but fewer not_configured
            offspring_better = False
            if offspring_score[0] > parent_score[0]:  # More optimal
                offspring_better = True
            elif offspring_score[0] == parent_score[0]:  # Same optimal
                if offspring_score[2] < parent_score[2]:  # Fewer undesirable
                    offspring_better = True
                elif offspring_score[2] == parent_score[2]:  # Same undesirable
                    if offspring_score[3] < parent_score[3]:  # Fewer not_configured
                        offspring_better = True
            
            if offspring_better:
                # Keep this offspring, trade this parent
                keep_offspring.append(offspring_creature)
                trade_parents.append(parent_creature)
                offspring_idx += 1
                parent_idx += 1
            else:
                # Offspring not better than worst parent - release for trading
                release_offspring.append(offspring_creature)
                offspring_idx += 1
        
        # Any remaining offspring that weren't compared - release for trading
        while offspring_idx < len(offspring_scores):
            release_offspring.append(offspring_scores[offspring_idx][0])
            offspring_idx += 1
        
        return {
            'keep_offspring': keep_offspring,
            'trade_parents': trade_parents,
            'release_offspring': release_offspring
        }


class MillBreeder(Breeder):
    """Selects pairs based on target phenotypes. Mill breeders always avoid undesirable phenotypes."""
    
    def __init__(
        self,
        target_phenotypes: List[dict],
        undesirable_phenotypes: Optional[List[dict]] = None,
        undesirable_genotypes: Optional[List[dict]] = None,
        avoid_undesirable_phenotypes: bool = False,
        avoid_undesirable_genotypes: bool = False,
        max_creatures: int = 7
    ):
        """
        Initialize mill breeder.
        
        Args:
            target_phenotypes: List of {trait_id, phenotype} dicts
            undesirable_phenotypes: List of {trait_id, phenotype} dicts to avoid
            undesirable_genotypes: List of {trait_id, genotype} dicts to avoid
            avoid_undesirable_phenotypes: Ignored - mill breeders always avoid undesirable phenotypes
            avoid_undesirable_genotypes: If True, filter out creatures with undesirable genotypes
            max_creatures: Maximum number of creatures this breeder can own
        """
        super().__init__(undesirable_phenotypes, undesirable_genotypes, avoid_undesirable_phenotypes, avoid_undesirable_genotypes, max_creatures)
        self.target_phenotypes = target_phenotypes
    
    def _matches_target_phenotypes(self, creature: 'Creature', traits: List) -> bool:
        """Check if creature matches target phenotypes."""
        from .trait import Trait
        
        for target in self.target_phenotypes:
            trait_id = target['trait_id']
            target_phenotype = target['phenotype']
            
            if trait_id >= len(creature.genome) or creature.genome[trait_id] is None:
                return False
            
            trait = next((t for t in traits if t.trait_id == trait_id), None)
            if trait is None:
                return False
            
            actual_phenotype = trait.get_phenotype(creature.genome[trait_id], creature.sex)
            if actual_phenotype != target_phenotype:
                return False
        
        return True
    
    def _count_undesirable_phenotypes(self, creature: 'Creature', traits: List) -> int:
        """Count number of undesirable phenotypes in a creature."""
        if not self.undesirable_phenotypes:
            return 0
        
        from .trait import Trait
        count = 0
        
        for undesirable in self.undesirable_phenotypes:
            trait_id = undesirable['trait_id']
            undesirable_phenotype = undesirable['phenotype']
            
            if trait_id >= len(creature.genome) or creature.genome[trait_id] is None:
                continue
            
            # Find trait to get phenotype mapping
            trait = next((t for t in traits if t.trait_id == trait_id), None)
            if trait is None:
                continue
            
            actual_phenotype = trait.get_phenotype(creature.genome[trait_id], creature.sex)
            if actual_phenotype == undesirable_phenotype:
                count += 1
        
        return count
    
    def select_pairs(
        self,
        eligible_males: List['Creature'],
        eligible_females: List['Creature'],
        num_pairs: int,
        rng: np.random.Generator,
        traits: List = None
    ) -> List[Tuple['Creature', 'Creature']]:
        """Select pairs based on target phenotypes. Mill breeders always avoid undesirable phenotypes."""
        if not eligible_males or not eligible_females:
            return []
        
        if traits is None:
            traits = []
        
        # Mill breeder always filters out undesirable phenotypes
        # Also respects global avoidance flag for genotypes
        filtered_males = eligible_males.copy()
        filtered_females = eligible_females.copy()
        
        # Always filter undesirable phenotypes (mill requirement)
        # Note: We bypass the avoid_undesirable_phenotypes flag check for mill
        if self.undesirable_phenotypes:
            from .trait import Trait
            for undesirable in self.undesirable_phenotypes:
                trait_id = undesirable['trait_id']
                undesirable_phenotype = undesirable['phenotype']
                trait = next((t for t in traits if t.trait_id == trait_id), None)
                if trait is not None:
                    filtered_males = [m for m in filtered_males 
                                    if trait_id >= len(m.genome) or m.genome[trait_id] is None or 
                                    trait.get_phenotype(m.genome[trait_id], m.sex) != undesirable_phenotype]
                    filtered_females = [f for f in filtered_females 
                                      if trait_id >= len(f.genome) or f.genome[trait_id] is None or 
                                      trait.get_phenotype(f.genome[trait_id], f.sex) != undesirable_phenotype]
        
        # Filter undesirable genotypes if global flag is enabled
        if self.avoid_undesirable_genotypes:
            filtered_males = [m for m in filtered_males if not self._has_undesirable_genotype(m)]
            filtered_females = [f for f in filtered_females if not self._has_undesirable_genotype(f)]
        
        # NEW: If filtering removed all candidates, use fallback strategy
        # Select creatures with MINIMUM number of undesirable phenotypes
        if not filtered_males:
            # Count undesirable phenotypes for each male
            male_scores = [(m, self._count_undesirable_phenotypes(m, traits)) for m in eligible_males]
            if male_scores:
                min_score = min(score for _, score in male_scores)
                filtered_males = [m for m, score in male_scores if score == min_score]
            else:
                filtered_males = eligible_males
        
        if not filtered_females:
            # Count undesirable phenotypes for each female
            female_scores = [(f, self._count_undesirable_phenotypes(f, traits)) for f in eligible_females]
            if female_scores:
                min_score = min(score for _, score in female_scores)
                filtered_females = [f for f, score in female_scores if score == min_score]
            else:
                filtered_females = eligible_females
        
        # Filter creatures that match target phenotypes
        matching_males = [m for m in filtered_males if self._matches_target_phenotypes(m, traits)]
        matching_females = [f for f in filtered_females if self._matches_target_phenotypes(f, traits)]
        
        # If no matches, fall back to filtered lists (which may be original if no filtering)
        if not matching_males:
            matching_males = filtered_males
        if not matching_females:
            matching_females = filtered_females
        
        pairs = []
        for _ in range(num_pairs):
            male = rng.choice(matching_males)
            female = rng.choice(matching_females)
            pairs.append((male, female))
        
        return pairs
    
    def select_replacement(
        self,
        candidates: List['Creature'],
        sex: str,
        traits: List,
        rng: np.random.Generator
    ) -> Optional['Creature']:
        """
        Select best replacement for mill breeder.
        Priority: Target phenotype > avoid undesirable phenotypes.
        
        Args:
            candidates: List of potential replacement creatures
            sex: Required sex ('male' or 'female')
            traits: List of trait definitions
            rng: Random number generator
            
        Returns:
            Best replacement creature, or None if no suitable candidates
        """
        from .trait import Trait
        
        # Filter by sex
        sex_filtered = [c for c in candidates if c.sex == sex]
        if not sex_filtered:
            return None
        
        # Always filter out undesirable phenotypes (mill requirement)
        filtered = sex_filtered.copy()
        if self.undesirable_phenotypes:
            for undesirable in self.undesirable_phenotypes:
                trait_id = undesirable['trait_id']
                undesirable_phenotype = undesirable['phenotype']
                trait = next((t for t in traits if t.trait_id == trait_id), None)
                if trait is not None:
                    filtered = [c for c in filtered 
                               if trait_id >= len(c.genome) or c.genome[trait_id] is None or 
                               trait.get_phenotype(c.genome[trait_id], c.sex) != undesirable_phenotype]
        
        if not filtered:
            return None
        
        # Priority: creatures with target phenotypes
        matching = [c for c in filtered if self._matches_target_phenotypes(c, traits)]
        
        # If we have matching candidates, choose from them
        if matching:
            return rng.choice(matching)
        
        # Otherwise, choose from filtered (non-undesirable)
        return rng.choice(filtered) if filtered else None

