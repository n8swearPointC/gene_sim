"""Test that founders are created with random ages."""

import pytest
import tempfile
import yaml
from pathlib import Path
from gene_sim import Simulation
from gene_sim.config import SimulationConfig


def test_founders_have_random_ages():
    """Test that founders are created with diverse birth_cycles (random ages)."""
    
    # Create a test configuration with a reasonable population size
    config_dict = {
        'seed': 42,
        'years': 5,
        'mode': 'quiet',
        'initial_population_size': 100,
        'initial_sex_ratio': {
            'male': 0.5,
            'female': 0.5
        },
        'creature_archetype': {
            'lifespan': {
                'min': 3,
                'max': 5
            },
            'sexual_maturity_months': 6,
            'max_fertility_age_years': {
                'male': 4.5,
                'female': 4.25
            },
            'gestation_period_days': 65,
            'nursing_period_days': 28,
            'menstrual_cycle_days': 24,
            'nearing_end_cycles': 12,
            'remove_ineligible_immediately': False,
            'litter_size': {
                'min': 3,
                'max': 6
            }
        },
        'target_phenotypes': [],
        'undesirable_phenotypes': [],
        'undesirable_genotypes': [],
        'breeders': {
            'random': 20,
            'inbreeding_avoidance': 0,
            'kennel_club': 0,
            'mill': 0
        },
        'traits': [
            {
                'trait_id': 0,
                'name': 'Test Trait',
                'trait_type': 'SIMPLE_MENDELIAN',
                'genotypes': [
                    {
                        'genotype': 'AA',
                        'phenotype': 'A',
                        'initial_freq': 0.25
                    },
                    {
                        'genotype': 'Aa',
                        'phenotype': 'A',
                        'initial_freq': 0.5
                    },
                    {
                        'genotype': 'aa',
                        'phenotype': 'a',
                        'initial_freq': 0.25
                    }
                ]
            }
        ]
    }
    
    # Create temporary config file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config_dict, f)
        config_path = f.name
    
    sim = None
    try:
        # Create simulation
        sim = Simulation.from_config(config_path)
        sim.initialize()
        
        # Get all founders (generation == 0)
        founders = [c for c in sim.population.creatures if c.generation == 0]
        
        # Test 1: We should have the expected number of founders
        assert len(founders) == 100, f"Expected 100 founders, got {len(founders)}"
        
        # Test 2: All founders should have generation == 0
        for founder in founders:
            assert founder.generation == 0, f"Founder has generation {founder.generation}, expected 0"
        
        # Test 3: Founders should have negative birth_cycles (indicating they were born before cycle 0)
        # This gives them random ages at simulation start
        negative_birth_cycles = [c for c in founders if c.birth_cycle < 0]
        assert len(negative_birth_cycles) > 0, "Expected some founders to have negative birth_cycles (random ages)"
        
        # Test 4: Birth cycles should be diverse, not all the same
        birth_cycles = [c.birth_cycle for c in founders]
        unique_birth_cycles = set(birth_cycles)
        assert len(unique_birth_cycles) > 1, "Founders should have diverse birth_cycles (ages), not all the same"
        
        # Test 5: Birth cycles should be within reasonable range based on lifespan
        # Founders can be aged up to their individual lifespan
        for founder in founders:
            # birth_cycle = -current_age, so current_age = -birth_cycle
            current_age = -founder.birth_cycle
            # Age should be between 1 and lifespan (inclusive)
            assert 1 <= current_age <= founder.lifespan, \
                f"Founder age {current_age} outside valid range [1, {founder.lifespan}]"
        
        # Test 6: With 100 founders and reasonable lifespan range, we should see good age diversity
        # At least 10% of the possible age range should be represented
        all_possible_ages = set()
        for founder in founders:
            all_possible_ages.add(-founder.birth_cycle)
        
        # Should have at least 10 different ages with 100 founders
        assert len(all_possible_ages) >= 10, \
            f"Expected diverse founder ages, got only {len(all_possible_ages)} unique ages"
        
        # Test 7: No founder should have birth_cycle == 0 (that was the old behavior)
        zero_birth_cycles = [c for c in founders if c.birth_cycle == 0]
        assert len(zero_birth_cycles) == 0, \
            "No founders should have birth_cycle == 0 (all should have random ages)"
        
        # Test 8: Founders should have no parents
        for founder in founders:
            assert founder.parent1_id is None, "Founders should have no parent1_id"
            assert founder.parent2_id is None, "Founders should have no parent2_id"
        
        print(f"✓ All {len(founders)} founders have random ages")
        print(f"✓ Birth cycles range from {min(birth_cycles)} to {max(birth_cycles)}")
        print(f"✓ {len(unique_birth_cycles)} unique birth cycles (ages) represented")
        print(f"✓ Age diversity: {len(all_possible_ages)} different ages")
    
    finally:
        # Cleanup
        Path(config_path).unlink(missing_ok=True)
        if sim and sim.db_path:
            try:
                Path(sim.db_path).unlink(missing_ok=True)
            except (PermissionError, FileNotFoundError):
                pass


def test_founder_age_distribution():
    """Test that founder ages follow expected uniform distribution."""
    
    config_dict = {
        'seed': 123,
        'years': 5,
        'mode': 'quiet',
        'initial_population_size': 200,  # Larger population for better distribution testing
        'initial_sex_ratio': {
            'male': 0.5,
            'female': 0.5
        },
        'creature_archetype': {
            'lifespan': {
                'min': 10,
                'max': 10  # Fixed lifespan for this test
            },
            'sexual_maturity_months': 6,
            'max_fertility_age_years': {
                'male': 9,
                'female': 9
            },
            'gestation_period_days': 65,
            'nursing_period_days': 28,
            'menstrual_cycle_days': 24,
            'nearing_end_cycles': 12,
            'remove_ineligible_immediately': False,
            'litter_size': {
                'min': 3,
                'max': 6
            }
        },
        'target_phenotypes': [],
        'undesirable_phenotypes': [],
        'undesirable_genotypes': [],
        'breeders': {
            'random': 20,
            'inbreeding_avoidance': 0,
            'kennel_club': 0,
            'mill': 0
        },
        'traits': [
            {
                'trait_id': 0,
                'name': 'Test Trait',
                'trait_type': 'SIMPLE_MENDELIAN',
                'genotypes': [
                    {
                        'genotype': 'AA',
                        'phenotype': 'A',
                        'initial_freq': 0.5
                    },
                    {
                        'genotype': 'aa',
                        'phenotype': 'a',
                        'initial_freq': 0.5
                    }
                ]
            }
        ]
    }
    
    # Create temporary config file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config_dict, f)
        config_path = f.name
    
    sim = None
    try:
        # Create simulation
        sim = Simulation.from_config(config_path)
        sim.initialize()
        
        # Get all founders
        founders = [c for c in sim.population.creatures if c.generation == 0]
        
        # Get age distribution
        ages = [-c.birth_cycle for c in founders]
        
        # With fixed lifespan of 10, ages should range from 1 to 10
        # (Note: lifespan is in cycles, calculated from years)
        # 10 years * 365.25 / 24 days per cycle = ~152 cycles
        expected_max_age = founders[0].lifespan  # All have same lifespan in this test
        
        min_age = min(ages)
        max_age = max(ages)
        
        assert min_age >= 1, f"Minimum age should be at least 1, got {min_age}"
        assert max_age <= expected_max_age, f"Maximum age should be <= {expected_max_age}, got {max_age}"
        
        # Check that we have good spread across the range
        # With 200 founders and uniform distribution, each age should appear roughly equally
        # Allow for randomness but check we're not clustered
        unique_ages = len(set(ages))
        age_range = expected_max_age - 1 + 1  # Range is [1, expected_max_age] inclusive
        
        # Should have at least 50% of possible ages represented with 200 samples
        assert unique_ages >= age_range * 0.5, \
            f"Expected at least {age_range * 0.5} unique ages, got {unique_ages}"
        
        print(f"✓ Age distribution test passed")
        print(f"✓ Ages range from {min_age} to {max_age} (expected max: {expected_max_age})")
        print(f"✓ {unique_ages} unique ages out of {age_range} possible ages")
    
    finally:
        # Cleanup
        Path(config_path).unlink(missing_ok=True)
        if sim and sim.db_path:
            try:
                Path(sim.db_path).unlink(missing_ok=True)
            except (PermissionError, FileNotFoundError):
                pass


if __name__ == '__main__':
    test_founders_have_random_ages()
    test_founder_age_distribution()
    print("\n✓ All founder age tests passed!")
