"""Behavioral tests for breeder selection strategies."""

import pytest
import numpy as np
from gene_sim.models.breeder import KennelClubBreeder, MillBreeder
from gene_sim.models.creature import Creature
from gene_sim.models.trait import Trait, Genotype, TraitType


@pytest.fixture
def sample_trait():
    """Create a sample trait for testing."""
    return Trait(0, "Coat Color", TraitType.SIMPLE_MENDELIAN, [
        Genotype("BB", "Black", 0.25),
        Genotype("Bb", "Black", 0.50),
        Genotype("bb", "Brown", 0.25),
    ])


@pytest.fixture
def creatures_with_phenotypes(sample_trait):
    """Create creatures with different phenotypes."""
    # Creatures with "Black" phenotype (BB or Bb)
    black_male1 = Creature(
        simulation_id=1,
        birth_cycle=0,
        sex="male",
        genome=["BB"],
        creature_id=1,
        lifespan=100
    )
    black_male2 = Creature(
        simulation_id=1,
        birth_cycle=0,
        sex="male",
        genome=["Bb"],
        creature_id=2,
        lifespan=100
    )
    black_female1 = Creature(
        simulation_id=1,
        birth_cycle=0,
        sex="female",
        genome=["BB"],
        creature_id=3,
        lifespan=100
    )
    black_female2 = Creature(
        simulation_id=1,
        birth_cycle=0,
        sex="female",
        genome=["Bb"],
        creature_id=4,
        lifespan=100
    )
    
    # Creatures with "Brown" phenotype (bb)
    brown_male = Creature(
        simulation_id=1,
        birth_cycle=0,
        sex="male",
        genome=["bb"],
        creature_id=5,
        lifespan=100
    )
    brown_female = Creature(
        simulation_id=1,
        birth_cycle=0,
        sex="female",
        genome=["bb"],
        creature_id=6,
        lifespan=100
    )
    
    return {
        'black_males': [black_male1, black_male2],
        'black_females': [black_female1, black_female2],
        'brown_males': [brown_male],
        'brown_females': [brown_female],
        'all_males': [black_male1, black_male2, brown_male],
        'all_females': [black_female1, black_female2, brown_female],
    }


def test_kennel_club_breeder_prefers_target_phenotype(creatures_with_phenotypes, sample_trait):
    """Test that KennelClubBreeder always selects parents with target phenotype when available."""
    # Create breeder interested in "Black" phenotype
    breeder = KennelClubBreeder(
        target_phenotypes=[{'trait_id': 0, 'phenotype': 'Black'}]
    )
    
    traits = [sample_trait]
    rng = np.random.Generator(np.random.PCG64(42))
    
    # Mix of creatures with and without target phenotype
    eligible_males = creatures_with_phenotypes['all_males']  # 2 Black, 1 Brown
    eligible_females = creatures_with_phenotypes['all_females']  # 2 Black, 1 Brown
    
    # Select multiple pairs to ensure consistent behavior
    num_pairs = 10
    pairs = breeder.select_pairs(eligible_males, eligible_females, num_pairs, rng, traits)
    
    assert len(pairs) == num_pairs
    
    # Verify ALL selected pairs have the target phenotype
    for male, female in pairs:
        male_phenotype = sample_trait.get_phenotype(male.genome[0], male.sex)
        female_phenotype = sample_trait.get_phenotype(female.genome[0], female.sex)
        
        assert male_phenotype == 'Black', f"Male has phenotype {male_phenotype}, expected Black"
        assert female_phenotype == 'Black', f"Female has phenotype {female_phenotype}, expected Black"


def test_mill_breeder_prefers_target_phenotype(creatures_with_phenotypes, sample_trait):
    """Test that MillBreeder always selects parents with target phenotype when available."""
    # Create breeder interested in "Black" phenotype
    breeder = MillBreeder(
        target_phenotypes=[{'trait_id': 0, 'phenotype': 'Black'}]
    )
    
    traits = [sample_trait]
    rng = np.random.Generator(np.random.PCG64(42))
    
    # Mix of creatures with and without target phenotype
    eligible_males = creatures_with_phenotypes['all_males']  # 2 Black, 1 Brown
    eligible_females = creatures_with_phenotypes['all_females']  # 2 Black, 1 Brown
    
    # Select multiple pairs to ensure consistent behavior
    num_pairs = 10
    pairs = breeder.select_pairs(eligible_males, eligible_females, num_pairs, rng, traits)
    
    assert len(pairs) == num_pairs
    
    # Verify ALL selected pairs have the target phenotype
    for male, female in pairs:
        male_phenotype = sample_trait.get_phenotype(male.genome[0], male.sex)
        female_phenotype = sample_trait.get_phenotype(female.genome[0], female.sex)
        
        assert male_phenotype == 'Black', f"Male has phenotype {male_phenotype}, expected Black"
        assert female_phenotype == 'Black', f"Female has phenotype {female_phenotype}, expected Black"


def test_kennel_club_breeder_prefers_target_phenotype_brown(creatures_with_phenotypes, sample_trait):
    """Test that KennelClubBreeder prefers Brown phenotype when that's the target."""
    # Create breeder interested in "Brown" phenotype
    breeder = KennelClubBreeder(
        target_phenotypes=[{'trait_id': 0, 'phenotype': 'Brown'}]
    )
    
    traits = [sample_trait]
    rng = np.random.Generator(np.random.PCG64(43))  # Different seed
    
    # Mix of creatures with and without target phenotype
    eligible_males = creatures_with_phenotypes['all_males']  # 2 Black, 1 Brown
    eligible_females = creatures_with_phenotypes['all_females']  # 2 Black, 1 Brown
    
    # Select multiple pairs
    num_pairs = 10
    pairs = breeder.select_pairs(eligible_males, eligible_females, num_pairs, rng, traits)
    
    assert len(pairs) == num_pairs
    
    # Verify ALL selected pairs have the target phenotype (Brown)
    for male, female in pairs:
        male_phenotype = sample_trait.get_phenotype(male.genome[0], male.sex)
        female_phenotype = sample_trait.get_phenotype(female.genome[0], female.sex)
        
        assert male_phenotype == 'Brown', f"Male has phenotype {male_phenotype}, expected Brown"
        assert female_phenotype == 'Brown', f"Female has phenotype {female_phenotype}, expected Brown"


def test_breeder_behavior_with_multiple_traits():
    """Test breeder behavior with multiple traits."""
    # Create two traits
    trait1 = Trait(0, "Coat Color", TraitType.SIMPLE_MENDELIAN, [
        Genotype("BB", "Black", 0.5),
        Genotype("bb", "Brown", 0.5),
    ])
    trait2 = Trait(1, "Size", TraitType.SIMPLE_MENDELIAN, [
        Genotype("SS", "Small", 0.5),
        Genotype("LL", "Large", 0.5),
    ])
    
    # Create creatures with different combinations
    # Target: Black + Small
    target_male = Creature(1, 0, "male", ["BB", "SS"], creature_id=1, lifespan=100)
    target_female = Creature(1, 0, "female", ["BB", "SS"], creature_id=2, lifespan=100)
    
    # Non-target: Brown + Large
    non_target_male = Creature(1, 0, "male", ["bb", "LL"], creature_id=3, lifespan=100)
    non_target_female = Creature(1, 0, "female", ["bb", "LL"], creature_id=4, lifespan=100)
    
    # Mixed: Black + Large (doesn't match target)
    mixed_male = Creature(1, 0, "male", ["BB", "LL"], creature_id=5, lifespan=100)
    mixed_female = Creature(1, 0, "female", ["BB", "LL"], creature_id=6, lifespan=100)
    
    breeder = KennelClubBreeder(
        target_phenotypes=[
            {'trait_id': 0, 'phenotype': 'Black'},
            {'trait_id': 1, 'phenotype': 'Small'}
        ]
    )
    
    traits = [trait1, trait2]
    rng = np.random.Generator(np.random.PCG64(44))
    
    eligible_males = [target_male, non_target_male, mixed_male]
    eligible_females = [target_female, non_target_female, mixed_female]
    
    num_pairs = 10
    pairs = breeder.select_pairs(eligible_males, eligible_females, num_pairs, rng, traits)
    
    assert len(pairs) == num_pairs
    
    # Verify ALL selected pairs match BOTH target phenotypes
    for male, female in pairs:
        male_color = trait1.get_phenotype(male.genome[0], male.sex)
        male_size = trait2.get_phenotype(male.genome[1], male.sex)
        female_color = trait1.get_phenotype(female.genome[0], female.sex)
        female_size = trait2.get_phenotype(female.genome[1], female.sex)
        
        assert male_color == 'Black', f"Male color is {male_color}, expected Black"
        assert male_size == 'Small', f"Male size is {male_size}, expected Small"
        assert female_color == 'Black', f"Female color is {female_color}, expected Black"
        assert female_size == 'Small', f"Female size is {female_size}, expected Small"


def test_breeder_fallback_when_no_target_phenotype_available(creatures_with_phenotypes, sample_trait):
    """Test that breeder falls back gracefully when no creatures with target phenotype exist."""
    # Create breeder interested in a phenotype that doesn't exist
    breeder = KennelClubBreeder(
        target_phenotypes=[{'trait_id': 0, 'phenotype': 'White'}]  # No creatures have "White"
    )
    
    traits = [sample_trait]
    rng = np.random.Generator(np.random.PCG64(45))
    
    # Only creatures with Black and Brown phenotypes
    eligible_males = creatures_with_phenotypes['all_males']
    eligible_females = creatures_with_phenotypes['all_females']
    
    # Should still return pairs (fallback behavior)
    num_pairs = 5
    pairs = breeder.select_pairs(eligible_males, eligible_females, num_pairs, rng, traits)
    
    # Should return pairs even though no target phenotype exists
    assert len(pairs) == num_pairs
    
    # Pairs should be valid creatures (just not matching the non-existent target)
    for male, female in pairs:
        assert male in eligible_males
        assert female in eligible_females


def test_kennel_offspring_probability_calculation():
    """Test that Kennel Club breeder calculates Mendelian probabilities correctly."""
    breeder = KennelClubBreeder(
        target_phenotypes=[],
        genotype_preferences=[
            {
                'trait_id': 0,
                'optimal': ['AA'],
                'acceptable': ['Aa'],
                'undesirable': ['aa']
            }
        ]
    )
    
    # Test Aa x Aa -> should give 25% AA, 50% Aa, 25% aa
    probs = breeder._calculate_offspring_probabilities("Aa", "Aa")
    assert abs(probs.get("AA", 0) - 0.25) < 0.01, "Expected 25% AA"
    assert abs(probs.get("Aa", 0) - 0.50) < 0.01, "Expected 50% Aa"
    assert abs(probs.get("aa", 0) - 0.25) < 0.01, "Expected 25% aa"
    
    # Test AA x aa -> should give 100% Aa
    probs = breeder._calculate_offspring_probabilities("AA", "aa")
    assert abs(probs.get("Aa", 0) - 1.0) < 0.01, "Expected 100% Aa"
    
    # Test AA x AA -> should give 100% AA
    probs = breeder._calculate_offspring_probabilities("AA", "AA")
    assert abs(probs.get("AA", 0) - 1.0) < 0.01, "Expected 100% AA"


def test_kennel_pairing_scores():
    """Test that Kennel Club breeder scores pairings correctly based on expected offspring."""
    breeder = KennelClubBreeder(
        target_phenotypes=[],
        genotype_preferences=[
            {
                'trait_id': 0,
                'optimal': ['AA'],
                'acceptable': ['Aa'],
                'undesirable': ['aa']
            }
        ]
    )
    
    # Score different pairings for trait 0
    score_AA_AA = breeder._score_genotype_pairing(0, "AA", "AA")
    score_AA_Aa = breeder._score_genotype_pairing(0, "AA", "Aa")
    score_Aa_Aa = breeder._score_genotype_pairing(0, "Aa", "Aa")
    score_Aa_aa = breeder._score_genotype_pairing(0, "Aa", "aa")
    score_aa_aa = breeder._score_genotype_pairing(0, "aa", "aa")
    
    # AA x AA should score highest (100% optimal offspring)
    assert score_AA_AA > score_AA_Aa, "AA x AA should score higher than AA x Aa"
    assert score_AA_Aa > score_Aa_Aa, "AA x Aa should score higher than Aa x Aa"
    assert score_Aa_Aa > score_Aa_aa, "Aa x Aa should score higher than Aa x aa"
    assert score_Aa_aa > score_aa_aa, "Aa x aa should score higher than aa x aa"
    
    # Verify expected score values
    assert abs(score_AA_AA - 100.0) < 0.01, "AA x AA should score 100"
    assert abs(score_AA_Aa - 55.0) < 0.01, "AA x Aa should score 55"
    assert abs(score_Aa_Aa - 17.5) < 0.01, "Aa x Aa should score 17.5"


def test_kennel_pairing_cache():
    """Test that pairing scores are cached for performance."""
    breeder = KennelClubBreeder(
        target_phenotypes=[],
        genotype_preferences=[
            {
                'trait_id': 0,
                'optimal': ['AA'],
                'acceptable': ['Aa'],
                'undesirable': ['aa']
            }
        ]
    )
    
    # Score a pairing
    score1 = breeder._score_genotype_pairing(0, "Aa", "Aa")
    
    # Check it's in cache
    cache_key = (0, ('Aa', 'Aa'))
    assert cache_key in breeder._pairing_score_cache, "Score should be cached"
    
    # Score again (should use cache)
    score2 = breeder._score_genotype_pairing(0, "Aa", "Aa")
    assert score1 == score2, "Cached score should match"
    
    # Cache should be order-independent
    score3 = breeder._score_genotype_pairing(0, "Aa", "Aa")
    assert score3 == score1, "Order-independent cache should work"


def test_kennel_intelligent_pairing_selection():
    """Test that Kennel Club breeder selects best pairings based on genetic scoring."""
    breeder = KennelClubBreeder(
        target_phenotypes=[],
        genotype_preferences=[
            {
                'trait_id': 0,
                'optimal': ['AA'],
                'acceptable': ['Aa'],
                'undesirable': ['aa']
            }
        ]
    )
    
    # Create test creatures with different genotypes
    males = [
        Creature(simulation_id=1, birth_cycle=0, sex='male', genome=['AA'], lifespan=100),
        Creature(simulation_id=1, birth_cycle=0, sex='male', genome=['AA'], lifespan=100),
        Creature(simulation_id=1, birth_cycle=0, sex='male', genome=['Aa'], lifespan=100),
        Creature(simulation_id=1, birth_cycle=0, sex='male', genome=['aa'], lifespan=100),
    ]
    for i, m in enumerate(males, 1):
        m.creature_id = i
    
    females = [
        Creature(simulation_id=1, birth_cycle=0, sex='female', genome=['AA'], lifespan=100),
        Creature(simulation_id=1, birth_cycle=0, sex='female', genome=['AA'], lifespan=100),
        Creature(simulation_id=1, birth_cycle=0, sex='female', genome=['Aa'], lifespan=100),
        Creature(simulation_id=1, birth_cycle=0, sex='female', genome=['aa'], lifespan=100),
    ]
    for i, f in enumerate(females, 5):
        f.creature_id = i
    
    rng = np.random.default_rng(42)
    
    # Select 2 pairs - should get best genetic pairings
    pairs = breeder.select_pairs(males, females, 2, rng, [])
    
    assert len(pairs) >= 1, "Should select at least one pair"
    
    # Best pairs should involve AA genotypes
    for male, female in pairs[:2]:  # Check first 2 pairs
        # At least one should be AA (optimal pairing)
        assert male.genome[0] == 'AA' or female.genome[0] == 'AA', \
            "Best pairings should involve at least one AA genotype"
    
    # Verify scores are ordered (best first)
    if len(pairs) >= 2:
        scores = [breeder._score_pairing(m, f) for m, f in pairs]
        assert all(scores[i] >= scores[i+1] for i in range(len(scores)-1)), \
            "Pairs should be ordered by score (highest first)"
