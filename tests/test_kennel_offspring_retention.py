"""
Test that KennelClubBreeder correctly retains superior offspring and trades inferior parents.
"""
import pytest
import numpy as np
from gene_sim.models.creature import Creature
from gene_sim.models.breeder import KennelClubBreeder
from gene_sim.models.trait import Trait, Genotype, TraitType


def test_kennel_retains_superior_offspring():
    """Test that kennel keeps offspring with better genotypes than parents."""
    rng = np.random.default_rng(seed=42)
    
    # Create a simple trait with optimal and undesirable genotypes
    genotypes = [
        Genotype('SS', 'Large', 0.25),
        Genotype('Ss', 'Medium', 0.50),
        Genotype('ss', 'Small', 0.25)
    ]
    trait = Trait(0, "Size", TraitType.SIMPLE_MENDELIAN, genotypes)
    
    # Create kennel with preference for 'SS' (optimal)
    kennel = KennelClubBreeder(
        target_phenotypes=[
            {'trait_id': 0, 'phenotype': 'Large'}
        ],
        genotype_preferences=[
            {
                'trait_id': 0,
                'optimal': ['SS'],
                'acceptable': ['Ss'],
                'undesirable': ['ss']
            }
        ],
        max_creatures=10
    )
    kennel.breeder_id = 1
    
    # Create parent creatures with suboptimal genotypes
    parent1 = Creature(
        simulation_id=1,
        creature_id=1,
        sex='male',
        birth_cycle=0,
        genome=['Ss'],  # Acceptable, not optimal
        breeder_id=1
    )
    
    parent2 = Creature(
        simulation_id=1,
        creature_id=2,
        sex='female',
        birth_cycle=0,
        genome=['ss'],  # Undesirable
        breeder_id=1
    )
    
    # Create offspring with better genotypes
    offspring1 = Creature(
        simulation_id=1,
        creature_id=3,
        sex='male',
        birth_cycle=1,
        genome=['SS'],  # Optimal!
        breeder_id=1
    )
    
    offspring2 = Creature(
        simulation_id=1,
        creature_id=4,
        sex='female',
        birth_cycle=1,
        genome=['Ss'],  # Acceptable (better than parent2's 'ss')
        breeder_id=1
    )
    
    offspring3 = Creature(
        simulation_id=1,
        creature_id=5,
        sex='male',
        birth_cycle=1,
        genome=['ss'],  # Undesirable (no better than parents)
        breeder_id=1
    )
    
    # Evaluate offspring vs parents
    result = kennel.evaluate_offspring_vs_parents(
        offspring=[offspring1, offspring2, offspring3],
        parents=[parent1, parent2],
        rng=rng
    )
    
    # Assertions
    # offspring1 (SS) should be kept - it's optimal and better than both parents
    assert offspring1 in result['keep_offspring'], "Optimal offspring should be kept"
    
    # offspring2 (Ss) has same score as parent1 (Ss) - might not be kept since no improvement
    # offspring3 (ss) has same score as parent2 (ss) - should NOT be kept
    assert offspring3 in result['release_offspring'], "Offspring no better than worst parent should be released"
    
    # parent2 (ss) should be traded - it's worse than offspring1 (SS)
    assert parent2 in result['trade_parents'], "Worst parent should be traded for better offspring"
    
    # We should keep 1 offspring and trade 1 parent
    assert len(result['keep_offspring']) == 1, "Should keep 1 superior offspring"
    assert len(result['trade_parents']) == 1, "Should trade 1 inferior parent"
    assert len(result['release_offspring']) == 2, "Should release 2 offspring that aren't better"


def test_kennel_respects_capacity():
    """Test that kennel doesn't keep more offspring than capacity allows."""
    rng = np.random.default_rng(seed=42)
    
    kennel = KennelClubBreeder(
        target_phenotypes=[
            {'trait_id': 0, 'phenotype': 'Optimal'}
        ],
        genotype_preferences=[
            {
                'trait_id': 0,
                'optimal': ['AA'],
                'acceptable': ['Aa'],
                'undesirable': ['aa']
            }
        ],
        max_creatures=5  # Small capacity
    )
    kennel.breeder_id = 1
    
    # Create many parents with suboptimal genotypes
    parents = [
        Creature(simulation_id=1, creature_id=i, sex='male' if i % 2 == 0 else 'female', birth_cycle=0, genome=['aa'], breeder_id=1)
        for i in range(1, 6)  # 5 parents (at capacity)
    ]
    
    # Create many optimal offspring
    offspring = [
        Creature(simulation_id=1, creature_id=i, sex='male' if i % 2 == 0 else 'female', birth_cycle=1, genome=['AA'], breeder_id=1)
        for i in range(10, 20)  # 10 offspring, all optimal
    ]
    
    result = kennel.evaluate_offspring_vs_parents(
        offspring=offspring,
        parents=parents,
        rng=rng
    )
    
    # Should keep offspring equal to number of parents traded
    # (can't exceed capacity even with all optimal offspring)
    assert len(result['keep_offspring']) == len(result['trade_parents']), \
        "Should only keep as many offspring as parents traded"
    assert len(result['keep_offspring']) <= len(parents), \
        "Can't keep more offspring than available parent slots"


def test_kennel_no_offspring():
    """Test that kennel handles empty offspring list gracefully."""
    rng = np.random.default_rng(seed=42)
    
    kennel = KennelClubBreeder(
        target_phenotypes=[
            {'trait_id': 0, 'phenotype': 'Optimal'}
        ],
        genotype_preferences=[
            {'trait_id': 0, 'optimal': ['AA'], 'acceptable': ['Aa'], 'undesirable': ['aa']}
        ],
        max_creatures=10
    )
    kennel.breeder_id = 1
    
    parents = [Creature(simulation_id=1, creature_id=1, sex='male', birth_cycle=0, genome=['Aa'], breeder_id=1)]
    
    result = kennel.evaluate_offspring_vs_parents(
        offspring=[],
        parents=parents,
        rng=rng
    )
    
    assert result['keep_offspring'] == []
    assert result['trade_parents'] == []
    assert result['release_offspring'] == []


def test_kennel_no_parents():
    """Test that kennel handles empty parent list gracefully."""
    rng = np.random.default_rng(seed=42)
    
    kennel = KennelClubBreeder(
        target_phenotypes=[
            {'trait_id': 0, 'phenotype': 'Optimal'}
        ],
        genotype_preferences=[
            {'trait_id': 0, 'optimal': ['AA'], 'acceptable': ['Aa'], 'undesirable': ['aa']}
        ],
        max_creatures=10
    )
    kennel.breeder_id = 1
    
    offspring = [Creature(simulation_id=1, creature_id=1, sex='male', birth_cycle=1, genome=['AA'], breeder_id=1)]
    
    result = kennel.evaluate_offspring_vs_parents(
        offspring=offspring,
        parents=[],
        rng=rng
    )
    
    # With no parents to compare to, all offspring should be released
    assert result['keep_offspring'] == []
    assert result['trade_parents'] == []
    assert result['release_offspring'] == offspring
