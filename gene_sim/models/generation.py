"""Cycle model for coordinating cycle-based simulation."""

from dataclasses import dataclass
from typing import List, Dict, Optional, TYPE_CHECKING
import json
import sqlite3
import numpy as np

if TYPE_CHECKING:
    from .population import Population
    from .breeder import Breeder
    from .creature import Creature
    from .trait import Trait
    from ..config import SimulationConfig


@dataclass
class CycleStats:
    """Statistics for a single cycle."""
    cycle: int
    population_size: int
    eligible_males: int
    eligible_females: int
    births: int
    deaths: int
    genotype_frequencies: Dict[int, Dict[str, float]]  # trait_id -> {genotype: frequency}
    allele_frequencies: Dict[int, Dict[str, float]]  # trait_id -> {allele: frequency}
    heterozygosity: Dict[int, float]  # trait_id -> heterozygosity
    genotype_diversity: Dict[int, int]  # trait_id -> diversity count
    homed_out: int = 0  # Creatures spayed/neutered and homed out


class Cycle:
    """Represents a single cycle in the simulation (one menstrual cycle)."""
    
    def __init__(self, cycle_number: int):
        """
        Initialize cycle.
        
        Args:
            cycle_number: Cycle number (0 = initial state)
        """
        self.cycle_number = cycle_number
    
    def execute_cycle(
        self,
        population: 'Population',
        breeders: List['Breeder'],
        traits: List['Trait'],
        rng: np.random.Generator,
        db_conn: sqlite3.Connection,
        simulation_id: int,
        config: 'SimulationConfig'
    ) -> CycleStats:
        """
        Execute one complete cycle (one menstrual cycle).
        
        Args:
            population: Current population working pool
            breeders: List of breeder instances
            traits: List of all traits
            rng: Random number generator
            db_conn: Database connection
            simulation_id: Simulation ID
            config: Simulation configuration
            
        Returns:
            CycleStats object with calculated metrics
        """
        from .creature import Creature
        
        current_cycle = self.cycle_number
        
        # 1. Handle births (creatures born when current_cycle == birth_cycle)
        births_this_cycle = []
        for creature in list(population.creatures):
            if creature.birth_cycle == current_cycle and creature.birth_cycle > 0:
                # Creature is born this cycle
                births_this_cycle.append(creature)
                # Set nursing_end_cycle for mother if this is a new birth
                # (Note: We need to find the mother - this is handled when offspring are created)
        
        # 2. Acquire replacements for creatures nearing end of breeding
        # Each breeder proactively seeks suitable replacements from available pool
        self._acquire_replacements(population, breeders, traits, rng, db_conn, current_cycle, config)
        
        # 3. Filter eligible creatures for breeding
        # Check gestation, nursing, maturity, etc. (all creatures are fertile at the same time)
        eligible_males = population.get_eligible_males(current_cycle, config)
        eligible_females = population.get_eligible_females(current_cycle, config)
        
        # 4. Distribute breeders and select pairs
        # Track males that have mated this cycle (max 1 mate per cycle)
        mated_males = set()
        
        num_pairs = min(len(eligible_males), len(eligible_females))
        all_pairs = []  # Initialize here so it's always defined
        
        if num_pairs == 0:
            # No eligible pairs, skip reproduction
            offspring = []
        else:
            # Filter out males that have already mated this cycle
            available_males = [m for m in eligible_males if m.creature_id not in mated_males]
            num_pairs = min(len(available_males), len(eligible_females))
            
            if num_pairs == 0:
                offspring = []
            else:
                # Distribute pairs to breeders
                if breeders and len(breeders) > 0:
                    pairs_per_breeder = num_pairs // len(breeders)
                    remaining_pairs = num_pairs % len(breeders)
                    
                    for i, breeder in enumerate(breeders):
                        num_for_breeder = pairs_per_breeder + (1 if i < remaining_pairs else 0)
                        if num_for_breeder > 0:
                            # Pass traits to breeders that need them
                            if hasattr(breeder, 'select_pairs'):
                                # Check if breeder needs traits parameter
                                import inspect
                                sig = inspect.signature(breeder.select_pairs)
                                if 'traits' in sig.parameters:
                                    pairs = breeder.select_pairs(
                                        available_males, eligible_females, num_for_breeder, rng, traits=traits
                                    )
                                else:
                                    pairs = breeder.select_pairs(
                                        available_males, eligible_females, num_for_breeder, rng
                                    )
                                # Tag each pair with the breeder that selected it
                                for pair in pairs:
                                    breeder_id = breeder.breeder_id if breeder.breeder_id is not None else None
                                    all_pairs.append((pair[0], pair[1], breeder_id))
                else:
                    # No breeders: create random pairs without breeder assignment
                    # This should not happen in normal operation, but handle gracefully
                    import random
                    shuffled_males = available_males.copy()
                    shuffled_females = eligible_females.copy()
                    rng.shuffle(shuffled_males)
                    rng.shuffle(shuffled_females)
                    for i in range(min(num_pairs, len(shuffled_males), len(shuffled_females))):
                        all_pairs.append((shuffled_males[i], shuffled_females[i], None))
                
                # 5. Create offspring at conception (current_cycle)
                offspring = []
                # Store parent references for later lookup when persisting removed offspring
                parent_map = {}  # child -> (parent1, parent2)
                
                for pair_data in all_pairs:
                    if len(pair_data) == 3:
                        male, female, breeder_id = pair_data
                    else:
                        # Backward compatibility: if no breeder_id, use None
                        male, female = pair_data
                        breeder_id = None
                    # Mark male as mated this cycle
                    if male.creature_id is not None:
                        mated_males.add(male.creature_id)
                    
                    # Set gestation_end_cycle for female
                    archetype = config.creature_archetype
                    female.gestation_end_cycle = current_cycle + archetype.gestation_cycles
                    
                    # Mark parents as having produced offspring (enables future transfers)
                    male.has_produced_offspring = True
                    female.has_produced_offspring = True
                    
                    # Determine litter size (number of offspring for this pair)
                    litter_size = rng.integers(
                        archetype.litter_size_min,
                        archetype.litter_size_max + 1  # +1 because randint is exclusive on upper bound
                    )
                    
                    # Create multiple offspring at conception (litter)
                    for _ in range(litter_size):
                        child = Creature.create_offspring(
                            parent1=male,
                            parent2=female,
                            conception_cycle=current_cycle,
                            simulation_id=simulation_id,
                            traits=traits,
                            rng=rng,
                            config=config,
                            produced_by_breeder_id=breeder_id
                        )
                        
                        # Store parent references
                        parent_map[child] = (male, female)
                        
                        # Update parent IDs from parent references
                        # All parents should already have IDs since all creatures are persisted immediately
                        if male.creature_id is None:
                            raise ValueError(
                                f"Parent1 (birth_cycle={male.birth_cycle}) does not have creature_id. "
                                f"All creatures must be persisted immediately upon creation."
                            )
                        if female.creature_id is None:
                            raise ValueError(
                                f"Parent2 (birth_cycle={female.birth_cycle}) does not have creature_id. "
                                f"All creatures must be persisted immediately upon creation."
                            )
                        child.parent1_id = male.creature_id
                        child.parent2_id = female.creature_id
                        
                        # Sample lifespan from config range (in cycles)
                        lifespan = rng.integers(
                            config.creature_archetype.lifespan_cycles_min,
                            config.creature_archetype.lifespan_cycles_max + 1
                        )
                        child.lifespan = lifespan
                        
                        offspring.append(child)
        
        # 5. Handle births: Set nursing_end_cycle for mothers when offspring are born
        # Note: Offspring are created at conception, but born later (when birth_cycle == current_cycle)
        # For now, we'll handle births when they occur (in step 1), but we need to set nursing periods
        # when births actually happen. Since offspring are created at conception, we need to track
        # which females gave birth this cycle and set their nursing_end_cycle.
        
        # Find females who gave birth this cycle and set nursing_end_cycle
        for child in births_this_cycle:
            if child.parent1_id is not None or child.parent2_id is not None:
                # Find the mother (female parent)
                # We need to look up parents - for now, assume parent2 is female if we can't determine
                # In practice, we'd query the database or have parent references
                # For cycle-based system, we'll set nursing when the birth actually occurs
                pass
        
        # 6. Determine which offspring to keep vs give away based on ownership rules
        # Rule 1: Breeder keeps offspring when parent is nearing end of reproduction
        # Rule 2: Breeder keeps offspring when they have predicted replacement needs
        # Offspring are strategically selected based on breeder criteria
        removed_offspring = []
        remaining_offspring = []
        
        # Also allow other breeders to claim offspring from this batch for their replacement needs
        available_for_claim = []
        
        # Group offspring by breeder (owner - inherited from mother)
        offspring_by_breeder: Dict[Optional[int], List[Creature]] = {}
        for child in offspring:
            breeder_id = child.breeder_id
            if breeder_id not in offspring_by_breeder:
                offspring_by_breeder[breeder_id] = []
            offspring_by_breeder[breeder_id].append(child)
        
        # Process each breeder's offspring
        for breeder_id, breeder_offspring in offspring_by_breeder.items():
            # Find the breeder object
            breeder_obj = next((b for b in breeders if b.breeder_id == breeder_id), None)
            
            # Check if any parent is nearing end of reproduction
            parent_nearing_end_male = False
            parent_nearing_end_female = False
            
            for child in breeder_offspring:
                if child in parent_map:
                    parent1, parent2 = parent_map[child]
                    # Check if either parent is nearing end (and owned by this breeder)
                    if (parent1.breeder_id == breeder_id and 
                        parent1.is_nearing_end_of_reproduction(current_cycle, config)):
                        if parent1.sex == 'male':
                            parent_nearing_end_male = True
                        else:
                            parent_nearing_end_female = True
                    if (parent2.breeder_id == breeder_id and 
                        parent2.is_nearing_end_of_reproduction(current_cycle, config)):
                        if parent2.sex == 'male':
                            parent_nearing_end_male = True
                        else:
                            parent_nearing_end_female = True
            
            # Check replacement needs calculated in _acquire_replacements
            # Subtract what we've already acquired this cycle from total needs
            total_need_male = getattr(breeder_obj, 'need_male_replacements', 0) if breeder_obj else 0
            total_need_female = getattr(breeder_obj, 'need_female_replacements', 0) if breeder_obj else 0
            already_acquired_male = getattr(breeder_obj, 'males_acquired_this_cycle', 0) if breeder_obj else 0
            already_acquired_female = getattr(breeder_obj, 'females_acquired_this_cycle', 0) if breeder_obj else 0
            
            need_male_replacements = max(0, total_need_male - already_acquired_male)
            need_female_replacements = max(0, total_need_female - already_acquired_female)
            
            kept_offspring = []
            parents_to_remove = []  # Track parents being actively replaced
            
            # Keep only the exact number of replacements still needed
            if need_male_replacements > 0 and breeder_obj:
                # Select best male offspring to keep
                for _ in range(need_male_replacements):
                    remaining_males = [c for c in breeder_offspring if c.sex == 'male' and c not in kept_offspring]
                    if remaining_males:
                        best_male = breeder_obj.select_replacement(remaining_males, 'male', traits, rng)
                        if best_male:
                            kept_offspring.append(best_male)
                            
                            # ACTIVE REMOVAL: If this is kennel club and offspring is optimal, remove sub-optimal parent
                            from .breeder import KennelClubBreeder
                            if isinstance(breeder_obj, KennelClubBreeder):
                                # Check if offspring has optimal genotype
                                is_optimal_offspring = True
                                if breeder_obj.genotype_preferences:
                                    for pref in breeder_obj.genotype_preferences:
                                        trait_id = pref['trait_id']
                                        if breeder_obj._get_genotype_tier(best_male, trait_id) != 0:
                                            is_optimal_offspring = False
                                            break
                                
                                # If optimal, find and remove a sub-optimal male parent
                                if is_optimal_offspring and hasattr(breeder_obj, 'male_targets_for_replacement'):
                                    targets = breeder_obj.male_targets_for_replacement
                                    if targets:
                                        # Pick the worst parent (highest tier / most undesirable)
                                        worst_parent = max(targets, key=lambda c: max(
                                            breeder_obj._get_genotype_tier(c, p['trait_id'])
                                            for p in breeder_obj.genotype_preferences
                                        ) if breeder_obj.genotype_preferences else 0)
                                        parents_to_remove.append(worst_parent)
                                        breeder_obj.male_targets_for_replacement.remove(worst_parent)
                
                # Update acquisition counter
                males_kept = len([c for c in kept_offspring if c.sex == 'male'])
                breeder_obj.males_acquired_this_cycle = already_acquired_male + males_kept
            
            if need_female_replacements > 0 and breeder_obj:
                # Select best female offspring to keep
                for _ in range(need_female_replacements):
                    remaining_females = [c for c in breeder_offspring if c.sex == 'female' and c not in kept_offspring]
                    if remaining_females:
                        best_female = breeder_obj.select_replacement(remaining_females, 'female', traits, rng)
                        if best_female:
                            kept_offspring.append(best_female)
                            
                            # ACTIVE REMOVAL: If this is kennel club and offspring is optimal, remove sub-optimal parent
                            from .breeder import KennelClubBreeder
                            if isinstance(breeder_obj, KennelClubBreeder):
                                # Check if offspring has optimal genotype
                                is_optimal_offspring = True
                                if breeder_obj.genotype_preferences:
                                    for pref in breeder_obj.genotype_preferences:
                                        trait_id = pref['trait_id']
                                        if breeder_obj._get_genotype_tier(best_female, trait_id) != 0:
                                            is_optimal_offspring = False
                                            break
                                
                                # If optimal, find and remove a sub-optimal female parent
                                if is_optimal_offspring and hasattr(breeder_obj, 'female_targets_for_replacement'):
                                    targets = breeder_obj.female_targets_for_replacement
                                    if targets:
                                        # Pick the worst parent (highest tier / most undesirable)
                                        worst_parent = max(targets, key=lambda c: max(
                                            breeder_obj._get_genotype_tier(c, p['trait_id'])
                                            for p in breeder_obj.genotype_preferences
                                        ) if breeder_obj.genotype_preferences else 0)
                                        parents_to_remove.append(worst_parent)
                                        breeder_obj.female_targets_for_replacement.remove(worst_parent)
                
                # Update acquisition counter
                females_kept = len([c for c in kept_offspring if c.sex == 'female'])
                breeder_obj.females_acquired_this_cycle = already_acquired_female + females_kept
            
            # Home out replaced parents (they are removed from breeding pool)
            for parent in parents_to_remove:
                parent.is_homed = True
                # Update in database
                cursor = db_conn.cursor()
                cursor.execute("""
                    UPDATE creatures SET is_homed = 1 WHERE creature_id = ?
                """, (parent.creature_id,))
            
            # Add kept offspring to remaining, make others available for other breeders
            remaining_offspring.extend(kept_offspring)
            for child in breeder_offspring:
                if child not in kept_offspring:
                    available_for_claim.append(child)
        
        # Now let other breeders claim offspring from the available pool if they still need replacements
        for breeder in breeders:
            if breeder.breeder_id is None:
                continue
            
            # Check how many they still need (total needed - already acquired from own litters)
            need_male = getattr(breeder, 'need_male_replacements', 0)
            need_female = getattr(breeder, 'need_female_replacements', 0)
            already_acquired_males = getattr(breeder, 'males_acquired_this_cycle', 0)
            already_acquired_females = getattr(breeder, 'females_acquired_this_cycle', 0)
            
            still_need_males = max(0, need_male - already_acquired_males)
            still_need_females = max(0, need_female - already_acquired_females)
            
            # Try to claim males
            for _ in range(still_need_males):
                males_available = [c for c in available_for_claim if c.sex == 'male']
                if males_available:
                    best_male = breeder.select_replacement(males_available, 'male', traits, rng)
                    if best_male:
                        # Transfer ownership to this breeder
                        best_male.breeder_id = breeder.breeder_id
                        remaining_offspring.append(best_male)
                        available_for_claim.remove(best_male)
            
            # Try to claim females
            for _ in range(still_need_females):
                females_available = [c for c in available_for_claim if c.sex == 'female']
                if females_available:
                    best_female = breeder.select_replacement(females_available, 'female', traits, rng)
                    if best_female:
                        # Transfer ownership to this breeder
                        best_female.breeder_id = breeder.breeder_id
                        remaining_offspring.append(best_female)
                        available_for_claim.remove(best_female)
        
        # Clear the acquisition counters for next cycle
        for breeder in breeders:
            if hasattr(breeder, 'males_acquired_this_cycle'):
                delattr(breeder, 'males_acquired_this_cycle')
            if hasattr(breeder, 'females_acquired_this_cycle'):
                delattr(breeder, 'females_acquired_this_cycle')
        
        # Unclaimed offspring are homed (given away to pet homes - still alive but not in breeding pool)
        homed_offspring = available_for_claim
        
        # Update parent IDs for all offspring before persisting
        all_offspring = homed_offspring + remaining_offspring
        for child in all_offspring:
            if child.birth_cycle > 0 and child in parent_map:
                parent1, parent2 = parent_map[child]
                if child.parent1_id is None:
                    if parent1.creature_id is None:
                        raise ValueError(
                            f"Parent1 (birth_cycle={parent1.birth_cycle}) does not have creature_id. "
                            f"All creatures must be persisted immediately upon creation."
                        )
                    child.parent1_id = parent1.creature_id
                if child.parent2_id is None:
                    if parent2.creature_id is None:
                        raise ValueError(
                            f"Parent2 (birth_cycle={parent2.birth_cycle}) does not have creature_id. "
                            f"All creatures must be persisted immediately upon creation."
                        )
                    child.parent2_id = parent2.creature_id
        
        # Mark homed offspring as homed (still alive, but not in breeding pool)
        for child in homed_offspring:
            child.is_homed = True
        
        # Persist all offspring immediately (both homed and kept)
        if all_offspring:
            population._persist_creatures(db_conn, simulation_id, all_offspring)
            # Add all offspring to population (including homed ones - they're alive, just not for breeding)
            population.add_creatures(all_offspring, current_cycle)
        
        # 8. Handle ownership transfers (after offspring are determined)
        # New rules: no transfer until breeding, no transfer if gestating/nursing, only one per cycle
        self._handle_ownership_transfers(
            population, breeders, db_conn, simulation_id, rng, config
        )
        
        # 8a. Spay/neuter and home out non-breeding creatures
        # Remove 80% of eligible creatures that didn't breed this cycle
        homed_out = self._spay_neuter_and_home(
            population, eligible_males, eligible_females, all_pairs, rng, db_conn, simulation_id, current_cycle
        )
        
        # 9. Get aged-out creatures (before removal)
        aged_out = population.get_aged_out_creatures()
        
        # 10. Calculate statistics (before removal)
        genotype_frequencies = {}
        allele_frequencies = {}
        heterozygosity = {}
        genotype_diversity = {}
        
        for trait in traits:
            trait_id = trait.trait_id
            genotype_frequencies[trait_id] = population.calculate_genotype_frequencies(trait_id)
            allele_frequencies[trait_id] = population.calculate_allele_frequencies(trait_id, trait)
            heterozygosity[trait_id] = population.calculate_heterozygosity(trait_id)
            genotype_diversity[trait_id] = population.calculate_genotype_diversity(trait_id)
        
        stats = CycleStats(
            cycle=current_cycle,
            population_size=len(population.creatures),
            eligible_males=len(eligible_males),
            eligible_females=len(eligible_females),
            births=len(births_this_cycle),  # Actual births this cycle
            deaths=len(aged_out),
            homed_out=homed_out,
            genotype_frequencies=genotype_frequencies,
            allele_frequencies=allele_frequencies,
            heterozygosity=heterozygosity,
            genotype_diversity=genotype_diversity
        )
        
        # 11. Persist cycle statistics
        self._persist_cycle_stats(db_conn, simulation_id, stats, traits)
        
        # 12. Remove aged-out creatures (they are already persisted)
        population.remove_aged_out_creatures(db_conn, simulation_id)
        
        return stats
    
    def _acquire_replacements(
        self,
        population: 'Population',
        breeders: List['Breeder'],
        traits: List,
        rng: np.random.Generator,
        db_conn: sqlite3.Connection,
        current_cycle: int,
        config: 'SimulationConfig'
    ) -> None:
        """
        Calculate replacement needs for each breeder.
        
        This method calculates how many replacements each breeder will need soon,
        which will be used during offspring distribution to preferentially assign
        offspring to breeders that need them.
        
        For kennel club breeders, this includes:
        1. Standard end-of-life replacements (creatures nearing death)
        2. Proactive replacements for creatures with undesirable genotypes
        
        The actual acquisition happens during offspring distribution phase.
        
        Args:
            population: Current population
            breeders: List of all breeders
            traits: List of trait definitions
            rng: Random number generator
            db_conn: Database connection
            current_cycle: Current cycle number
            config: Simulation configuration
        """
        from .breeder import KennelClubBreeder
        
        # Store replacement needs on each breeder for use during offspring distribution
        maturity_cycles = config.creature_archetype.maturity_cycles
        buffer_cycles = 3  # Safety buffer
        replacement_lead_time = maturity_cycles + buffer_cycles
        
        for breeder in breeders:
            if breeder.breeder_id is None:
                continue
            
            # Get this breeder's creatures
            breeder_creatures = [c for c in population.creatures if c.breeder_id == breeder.breeder_id]
            
            # Count how many need replacement soon (within lead time window)
            need_male_replacements = 0
            need_female_replacements = 0
            
            # Standard replacement: creatures nearing end of life
            for creature in breeder_creatures:
                # Calculate when this creature will die
                death_cycle = creature.birth_cycle + creature.lifespan
                
                # Check if we need to acquire replacement now (before creature dies)
                # Give enough lead time for offspring to mature
                if current_cycle + replacement_lead_time >= death_cycle:
                    if creature.sex == 'male':
                        need_male_replacements += 1
                    else:
                        need_female_replacements += 1
            
            # Kennel club breeders: also count creatures with undesirable genotypes
            # These are candidates for proactive replacement with superior offspring
            if isinstance(breeder, KennelClubBreeder):
                # Track which specific creatures need replacement for active removal
                breeder.male_targets_for_replacement = []
                breeder.female_targets_for_replacement = []
                
                for creature in breeder_creatures:
                    # Skip if already counted for end-of-life replacement
                    death_cycle = creature.birth_cycle + creature.lifespan
                    if current_cycle + replacement_lead_time >= death_cycle:
                        continue
                    
                    # Check if creature has sub-optimal genotype (not optimal)
                    # With new preference system: count creatures with acceptable or undesirable genotypes
                    is_sub_optimal = False
                    if breeder.genotype_preferences:
                        # Check if all genotypes are optimal
                        for pref in breeder.genotype_preferences:
                            trait_id = pref['trait_id']
                            tier = breeder._get_genotype_tier(creature, trait_id)
                            if tier > 0:  # Not optimal (acceptable or undesirable)
                                is_sub_optimal = True
                                break
                    else:
                        # Legacy: check if has undesirable genotype
                        is_sub_optimal = breeder._has_undesirable_genotype(creature)
                    
                    if is_sub_optimal:
                        # Track this specific creature for potential replacement
                        if creature.sex == 'male':
                            need_male_replacements += 1
                            breeder.male_targets_for_replacement.append(creature)
                        else:
                            need_female_replacements += 1
                            breeder.female_targets_for_replacement.append(creature)
            
            # Store on breeder object for use during offspring distribution
            breeder.need_male_replacements = need_male_replacements
            breeder.need_female_replacements = need_female_replacements
    
    def _spay_neuter_and_home(
        self,
        population: 'Population',
        eligible_males: List['Creature'],
        eligible_females: List['Creature'],
        breeding_pairs: List,
        rng: np.random.Generator,
        db_conn: sqlite3.Connection,
        simulation_id: int,
        current_cycle: int
    ) -> int:
        """
        Spay/neuter and home out 80% of eligible creatures that didn't breed this cycle.
        
        Creatures are marked as homed (is_homed=True), which means they're:
        - Still alive (is_alive=True)
        - Removed from breeding pool (not eligible for future breeding)
        - Will die naturally when they reach their lifespan
        
        Args:
            population: Current population
            eligible_males: List of eligible male creatures
            eligible_females: List of eligible female creatures
            breeding_pairs: List of (male, female, breeder_id) tuples that bred
            rng: Random number generator
            db_conn: Database connection
            simulation_id: Simulation ID
            current_cycle: Current cycle number
            
        Returns:
            Number of creatures homed out
        """
        # Extract creature IDs of those that bred
        bred_creature_ids = set()
        for pair in breeding_pairs:
            if len(pair) >= 2:
                male, female = pair[0], pair[1]
                if male.creature_id is not None:
                    bred_creature_ids.add(male.creature_id)
                if female.creature_id is not None:
                    bred_creature_ids.add(female.creature_id)
        
        # Find eligible creatures that didn't breed and aren't already homed
        non_breeding_males = [m for m in eligible_males 
                              if m.creature_id not in bred_creature_ids and not m.is_homed]
        non_breeding_females = [f for f in eligible_females 
                                if f.creature_id not in bred_creature_ids and not f.is_homed]
        
        # Randomly select 80% to home out
        num_males_to_home = int(len(non_breeding_males) * 0.8)
        num_females_to_home = int(len(non_breeding_females) * 0.8)
        
        # Shuffle and select
        rng.shuffle(non_breeding_males)
        rng.shuffle(non_breeding_females)
        
        males_to_home = non_breeding_males[:num_males_to_home]
        females_to_home = non_breeding_females[:num_females_to_home]
        
        homed_out = males_to_home + females_to_home
        
        # Mark creatures as homed (still alive, just not in breeding pool)
        if homed_out:
            cursor = db_conn.cursor()
            for creature in homed_out:
                # Mark as homed (stays alive but removed from breeding pool)
                creature.is_homed = True
                
                # Update in database
                cursor.execute("""
                    UPDATE creatures
                    SET is_homed = 1
                    WHERE creature_id = ?
                """, (creature.creature_id,))
            
            db_conn.commit()
        
        return len(homed_out)
    
    def _handle_ownership_transfers(
        self,
        population: 'Population',
        breeders: List['Breeder'],
        db_conn: sqlite3.Connection,
        simulation_id: int,
        rng: np.random.Generator,
        config: 'SimulationConfig'
    ) -> None:
        """
        Handle ownership transfers with new rules:
        - No transfer until creature has produced offspring
        - No transfer if gestating or nursing
        - Only one transfer per cycle
        - Kennels transfer males regularly, females ~3x in lifetime
        - Mills have low transfer probability
        - Kennels won't accept mill-origin creatures
        - Mills may replace breeding females
        
        Args:
            population: Current population
            breeders: List of all breeders
            db_conn: Database connection
            simulation_id: Simulation ID
            rng: Random number generator
            config: Simulation configuration
        """
        if not breeders:
            return
        
        from .breeder import KennelClubBreeder, MillBreeder
        
        cursor = db_conn.cursor()
        
        # Group breeders by type
        kennel_breeders = [b for b in breeders if isinstance(b, KennelClubBreeder)]
        mill_breeders = [b for b in breeders if isinstance(b, MillBreeder)]
        other_breeders = [b for b in breeders if not isinstance(b, (KennelClubBreeder, MillBreeder))]
        
        # Track if we've done a transfer this cycle (only one per cycle)
        transfer_done = False
        
        # Shuffle creatures for random selection
        eligible_creatures = list(population.creatures)
        rng.shuffle(eligible_creatures)
        
        for creature in eligible_creatures:
            if transfer_done:
                break
                
            if creature.breeder_id is None:
                continue
            
            # Rule: No transfer until has produced offspring
            if not creature.has_produced_offspring:
                continue
            
            # Rule: No transfer if gestating or nursing
            if creature.gestation_end_cycle is not None and creature.gestation_end_cycle > self.cycle_number:
                continue
            if creature.nursing_end_cycle is not None and creature.nursing_end_cycle > self.cycle_number:
                continue
            
            # Find current owner
            current_owner = next((b for b in breeders if b.breeder_id == creature.breeder_id), None)
            if current_owner is None:
                continue
            
            # Determine transfer probability based on breeder type
            transfer_prob = 0.0
            
            if isinstance(current_owner, KennelClubBreeder):
                # Kennels transfer males regularly
                if creature.sex == 'male':
                    transfer_prob = 0.15  # Higher probability for males
                else:
                    # Females transferred ~3x in lifetime
                    # Calculate probability to achieve target transfer count
                    avg_lifetime_cycles = (config.creature_archetype.lifespan_cycles_min + 
                                          config.creature_archetype.lifespan_cycles_max) / 2
                    target_transfers = config.breeders.kennel_female_transfer_count
                    transfer_prob = target_transfers / avg_lifetime_cycles if avg_lifetime_cycles > 0 else 0.0
                    
            elif isinstance(current_owner, MillBreeder):
                # Mills have very low transfer probability
                transfer_prob = config.breeders.mill_transfer_probability
            else:
                # Other breeders use baseline probability
                transfer_prob = 0.12
            
            # Check if transfer happens
            if rng.random() >= transfer_prob:
                continue
            
            # Select new owner based on breeder type
            available_breeders = []
            
            if isinstance(current_owner, KennelClubBreeder):
                # Kennels transfer to other kennels or random/inbreeding avoidance breeders
                available_breeders = [b for b in kennel_breeders + other_breeders 
                                     if b.breeder_id != creature.breeder_id]
                
            elif isinstance(current_owner, MillBreeder):
                # Mills may replace female with offspring
                # For now, transfer out to "homes" (remove from breeding pool by transferring to None or special breeder)
                # In this implementation, we'll transfer to other mills or random breeders
                available_breeders = [b for b in mill_breeders + other_breeders 
                                     if b.breeder_id != creature.breeder_id]
            else:
                # Other breeders can transfer to anyone except kennels if mill-origin
                if isinstance(current_owner, MillBreeder) or creature.produced_by_breeder_id in [b.breeder_id for b in mill_breeders]:
                    # Mill-origin, kennels won't accept
                    available_breeders = [b for b in mill_breeders + other_breeders 
                                         if b.breeder_id != creature.breeder_id]
                else:
                    # Not mill-origin, can go anywhere
                    available_breeders = [b for b in breeders if b.breeder_id != creature.breeder_id]
            
            if not available_breeders:
                continue
            
            # Additional kennel club restriction: won't accept mill-origin creatures
            if available_breeders:
                mill_breeder_ids = [b.breeder_id for b in mill_breeders]
                if creature.produced_by_breeder_id in mill_breeder_ids:
                    # Filter out kennel breeders from available
                    available_breeders = [b for b in available_breeders if not isinstance(b, KennelClubBreeder)]
            
            if not available_breeders:
                continue
            
            # Execute transfer
            new_owner = rng.choice(available_breeders)
            old_breeder_id = creature.breeder_id
            creature.breeder_id = new_owner.breeder_id
            creature.transfer_count += 1
            
            # Record ownership transfer in database
            cursor.execute("""
                INSERT INTO creature_ownership_history (
                    creature_id, breeder_id, transfer_generation
                ) VALUES (?, ?, ?)
            """, (creature.creature_id, new_owner.breeder_id, self.cycle_number))
            
            # Update creature's breeder_id in database
            cursor.execute("""
                UPDATE creatures
                SET breeder_id = ?
                WHERE creature_id = ?
            """, (new_owner.breeder_id, creature.creature_id))
            
            transfer_done = True  # Only one transfer per cycle
        
        db_conn.commit()
    
    def _persist_cycle_stats(
        self,
        db_conn: sqlite3.Connection,
        simulation_id: int,
        stats: CycleStats,
        traits: List['Trait']
    ) -> None:
        """Persist cycle statistics to database."""
        cursor = db_conn.cursor()
        
        # Insert generation_stats (using generation column to store cycle number)
        cursor.execute("""
            INSERT INTO generation_stats (
                simulation_id, generation, population_size,
                eligible_males, eligible_females, births, deaths
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            simulation_id,
            stats.cycle,  # Store cycle number in generation column
            stats.population_size,
            stats.eligible_males,
            stats.eligible_females,
            stats.births,
            stats.deaths
        ))
        
        # Batch insert genotype frequencies
        genotype_freq_data = []
        for trait_id, frequencies in stats.genotype_frequencies.items():
            for genotype, frequency in frequencies.items():
                genotype_freq_data.append((
                    simulation_id,
                    stats.cycle,  # Store cycle number in generation column
                    trait_id,
                    genotype,
                    frequency
                ))
        
        if genotype_freq_data:
            cursor.executemany("""
                INSERT INTO generation_genotype_frequencies (
                    simulation_id, generation, trait_id, genotype, frequency
                ) VALUES (?, ?, ?, ?, ?)
            """, genotype_freq_data)
        
        # Batch insert trait stats
        trait_stats_data = []
        for trait_id in [t.trait_id for t in traits]:
            allele_freqs = stats.allele_frequencies.get(trait_id, {})
            trait_stats_data.append((
                simulation_id,
                stats.cycle,  # Store cycle number in generation column
                trait_id,
                json.dumps(allele_freqs),
                stats.heterozygosity.get(trait_id, 0.0),
                stats.genotype_diversity.get(trait_id, 0)
            ))
        
        if trait_stats_data:
            cursor.executemany("""
                INSERT INTO generation_trait_stats (
                    simulation_id, generation, trait_id,
                    allele_frequencies, heterozygosity, genotype_diversity
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, trait_stats_data)
        
        db_conn.commit()
    
    def advance(self) -> int:
        """
        Advance to next cycle.
        
        Returns:
            New cycle number
        """
        self.cycle_number += 1
        return self.cycle_number

