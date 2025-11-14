"""
Test that MillBreeder correctly uses fallback selection when all creatures have undesirable phenotypes.
"""
import pytest
import numpy as np
from gene_sim.models.creature import Creature
from gene_sim.models.breeder import MillBreeder
from gene_sim.models.trait import Trait, Genotype, TraitType


def test_mill_fallback_selects_minimum_undesirable():
    """Test that mill selects creatures with minimum undesirable phenotypes when all have some."""
    rng = np.random.default_rng(seed=42)
    
    # Create traits
    trait_size = Trait(
        trait_id=0,
        name="Size",
        trait_type=TraitType.SIMPLE_MENDELIAN,
        genotypes=[
            Genotype('SS', 'Large', 0.25),
            Genotype('Ss', 'Medium', 0.50),
            Genotype('ss', 'Small', 0.25)
        ]
    )
    
    trait_color = Trait(
        trait_id=1,
        name="Color",
        trait_type=TraitType.SIMPLE_MENDELIAN,
        genotypes=[
            Genotype('BB', 'Black', 0.25),
            Genotype('Bb', 'Brown', 0.50),
            Genotype('bb', 'White', 0.25)
        ]
    )
    
    trait_health = Trait(
        trait_id=2,
        name="Health",
        trait_type=TraitType.SIMPLE_MENDELIAN,
        genotypes=[
            Genotype('HH', 'Healthy', 0.25),
            Genotype('Hh', 'Carrier', 0.50),
            Genotype('hh', 'Sick', 0.25)
        ]
    )
    
    traits = [trait_size, trait_color, trait_health]
    
    # Create mill that avoids Small, White, and Sick phenotypes
    mill = MillBreeder(
        target_phenotypes=[
            {'trait_id': 0, 'phenotype': 'Large'}
        ],
        undesirable_phenotypes=[
            {'trait_id': 0, 'phenotype': 'Small'},
            {'trait_id': 1, 'phenotype': 'White'},
            {'trait_id': 2, 'phenotype': 'Sick'}
        ],
        max_creatures=7
    )
    mill.breeder_id = 1
    
    # Create creatures with different numbers of undesirable phenotypes
    # All have at least one undesirable phenotype (forcing fallback)
    
    # Creature with 3 undesirable: Small, White, Sick
    worst = Creature(
        simulation_id=1,
        creature_id=1,
        sex='male',
        birth_cycle=1,
        genome=['ss', 'bb', 'hh'],  # Small, White, Sick
        breeder_id=1
    )
    
    # Creature with 2 undesirable: Small, Sick (but not White)
    medium = Creature(
        simulation_id=1,
        creature_id=2,
        sex='male',
        birth_cycle=1,
        genome=['ss', 'BB', 'hh'],  # Small, Black, Sick
        breeder_id=1
    )
    
    # Creature with 1 undesirable: Small only
    best = Creature(
        simulation_id=1,
        creature_id=3,
        sex='male',
        birth_cycle=1,
        genome=['ss', 'BB', 'HH'],  # Small, Black, Healthy
        breeder_id=1
    )
    
    # Another creature with 1 undesirable: White only
    also_best = Creature(
        simulation_id=1,
        creature_id=4,
        sex='female',
        birth_cycle=1,
        genome=['SS', 'bb', 'HH'],  # Large, White, Healthy
        breeder_id=1
    )
    
    creatures = [worst, medium, best, also_best]
    
    # Try to select pairs - should use fallback and choose creatures with minimum undesirable
    males = [c for c in creatures if c.sex == 'male']
    females = [c for c in creatures if c.sex == 'female']
    pairs = mill.select_pairs(males, females, 1, rng, traits)
    
    # Verify that we got pairs (fallback worked)
    assert len(pairs) > 0, "Fallback selection should produce pairs"
    
    # Verify that selected creatures are the ones with minimum undesirable (1 each)
    selected_creatures = set()
    for male, female in pairs:
        selected_creatures.add(male.creature_id)
        selected_creatures.add(female.creature_id)
    
    # Should include best and also_best (both have 1 undesirable)
    # Should NOT include worst (3 undesirable) or medium (2 undesirable)
    assert best.creature_id in selected_creatures or also_best.creature_id in selected_creatures, \
        "Should select creatures with minimum undesirable phenotypes"
    assert worst.creature_id not in selected_creatures, \
        "Should not select creature with most undesirable phenotypes"


def test_mill_fallback_when_all_filtered():
    """Test that mill uses fallback when strict filtering removes all creatures."""
    rng = np.random.default_rng(seed=42)
    
    trait = Trait(
        trait_id=0,
        name="Temperament",
        trait_type=TraitType.SIMPLE_MENDELIAN,
        genotypes=[
            Genotype('AA', 'Aggressive', 0.25),
            Genotype('Aa', 'Moderate', 0.50),
            Genotype('aa', 'Gentle', 0.25)
        ]
    )
    
    traits = [trait]
    
    # Mill that avoids Aggressive temperament
    mill = MillBreeder(
        target_phenotypes=[
            {'trait_id': 0, 'phenotype': 'Gentle'}
        ],
        undesirable_phenotypes=[
            {'trait_id': 0, 'phenotype': 'Aggressive'}
        ],
        max_creatures=7
    )
    mill.breeder_id = 1
    
    # ALL creatures have Aggressive temperament
    all_aggressive = [
        Creature(simulation_id=1, creature_id=i, sex='male' if i % 2 == 0 else 'female', birth_cycle=1, genome=['AA'], breeder_id=1)
        for i in range(1, 11)
    ]
    
    # Without fallback, this would return empty list
    # With fallback, should select from all (they all have same undesirable count)
    males = [c for c in all_aggressive if c.sex == 'male']
    females = [c for c in all_aggressive if c.sex == 'female']
    pairs = mill.select_pairs(males, females, 2, rng, traits)
    
    # Should get pairs via fallback
    assert len(pairs) > 0, "Fallback should allow breeding when all have undesirable phenotypes"


def test_mill_prefers_no_undesirable_when_available():
    """Test that mill still prefers creatures with no undesirable phenotypes when they exist."""
    rng = np.random.default_rng(seed=42)
    
    trait = Trait(
        trait_id=0,
        name="Size",
        trait_type=TraitType.SIMPLE_MENDELIAN,
        genotypes=[
            Genotype('SS', 'Large', 0.25),
            Genotype('Ss', 'Medium', 0.50),
            Genotype('ss', 'Small', 0.25)
        ]
    )
    
    traits = [trait]
    
    mill = MillBreeder(
        target_phenotypes=[
            {'trait_id': 0, 'phenotype': 'Large'}
        ],
        undesirable_phenotypes=[
            {'trait_id': 0, 'phenotype': 'Small'}
        ],
        max_creatures=7
    )
    mill.breeder_id = 1
    
    # Mix of creatures: some with undesirable, some without
    clean = Creature(simulation_id=1, creature_id=1, sex='male', birth_cycle=1, genome=['SS'], breeder_id=1)  # Large - no undesirable
    clean2 = Creature(simulation_id=1, creature_id=2, sex='female', birth_cycle=1, genome=['Ss'], breeder_id=1)  # Medium - no undesirable
    dirty = Creature(simulation_id=1, creature_id=3, sex='male', birth_cycle=1, genome=['ss'], breeder_id=1)  # Small - has undesirable
    dirty2 = Creature(simulation_id=1, creature_id=4, sex='female', birth_cycle=1, genome=['ss'], breeder_id=1)  # Small - has undesirable
    
    creatures = [clean, clean2, dirty, dirty2]
    
    males = [c for c in creatures if c.sex == 'male']
    females = [c for c in creatures if c.sex == 'female']
    pairs = mill.select_pairs(males, females, 1, rng, traits)
    
    # Should prefer clean creatures when available
    assert len(pairs) > 0, "Should produce pairs"
    male, female = pairs[0]
    
    # Both should be from clean set (SS or Ss), not dirty (ss)
    assert male.genome[0] != 'ss', "Should prefer creatures without undesirable phenotypes"
    assert female.genome[0] != 'ss', "Should prefer creatures without undesirable phenotypes"


def test_mill_count_undesirable_phenotypes():
    """Test the helper method that counts undesirable phenotypes."""
    rng = np.random.default_rng(seed=42)
    
    # Create multiple traits
    trait1 = Trait(trait_id=0, name="T1", trait_type=TraitType.SIMPLE_MENDELIAN,
                  genotypes=[Genotype('AA', 'P1', 0.25), Genotype('Aa', 'P2', 0.50), Genotype('aa', 'P3', 0.25)])
    trait2 = Trait(trait_id=1, name="T2", trait_type=TraitType.SIMPLE_MENDELIAN,
                  genotypes=[Genotype('BB', 'Q1', 0.25), Genotype('Bb', 'Q2', 0.50), Genotype('bb', 'Q3', 0.25)])
    trait3 = Trait(trait_id=2, name="T3", trait_type=TraitType.SIMPLE_MENDELIAN,
                  genotypes=[Genotype('CC', 'R1', 0.25), Genotype('Cc', 'R2', 0.50), Genotype('cc', 'R3', 0.25)])
    
    traits = [trait1, trait2, trait3]
    
    mill = MillBreeder(
        target_phenotypes=[],
        undesirable_phenotypes=[
            {'trait_id': 0, 'phenotype': 'P3'},
            {'trait_id': 1, 'phenotype': 'Q3'},
            {'trait_id': 2, 'phenotype': 'R3'}
        ],
        max_creatures=7
    )
    
    # Creature with 0 undesirable
    c0 = Creature(simulation_id=1, creature_id=1, sex='male', birth_cycle=1, genome=['AA', 'BB', 'CC'], breeder_id=1)
    assert mill._count_undesirable_phenotypes(c0, traits) == 0
    
    # Creature with 1 undesirable (P3)
    c1 = Creature(simulation_id=1, creature_id=2, sex='male', birth_cycle=1, genome=['aa', 'BB', 'CC'], breeder_id=1)
    assert mill._count_undesirable_phenotypes(c1, traits) == 1
    
    # Creature with 2 undesirable (P3, Q3)
    c2 = Creature(simulation_id=1, creature_id=3, sex='male', birth_cycle=1, genome=['aa', 'bb', 'CC'], breeder_id=1)
    assert mill._count_undesirable_phenotypes(c2, traits) == 2
    
    # Creature with 3 undesirable (P3, Q3, R3)
    c3 = Creature(simulation_id=1, creature_id=4, sex='male', birth_cycle=1, genome=['aa', 'bb', 'cc'], breeder_id=1)
    assert mill._count_undesirable_phenotypes(c3, traits) == 3
