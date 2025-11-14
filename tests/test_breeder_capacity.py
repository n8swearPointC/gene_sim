"""Tests for breeder capacity limits and offspring assignment behavior."""

import pytest
import numpy as np
from gene_sim.models.breeder import RandomBreeder, MillBreeder, KennelClubBreeder
from gene_sim.models.trait import Trait, TraitType


@pytest.fixture
def rng():
    """Provide seeded random number generator."""
    return np.random.default_rng(seed=42)


@pytest.fixture
def simple_trait():
    """Create a simple Mendelian trait for testing."""
    genotypes_data = [
        {"genotype": "AA", "phenotype": "black", "initial_freq": 0.25},
        {"genotype": "Aa", "phenotype": "black", "initial_freq": 0.5},
        {"genotype": "aa", "phenotype": "white", "initial_freq": 0.25}
    ]
    
    trait = Trait(
        trait_id=0,
        name="coat_color",
        trait_type=TraitType.SIMPLE_MENDELIAN,
        genotypes=genotypes_data
    )
    return trait


class TestBreederCapacityAttributes:
    """Test breeder capacity attribute settings."""
    
    def test_default_max_creatures(self):
        """Test that default max_creatures is 7."""
        breeder = RandomBreeder()
        assert breeder.max_creatures == 7
    
    def test_custom_max_creatures(self):
        """Test setting custom max_creatures value."""
        breeder = RandomBreeder(max_creatures=10)
        assert breeder.max_creatures == 10
    
    def test_different_breeder_types_capacity(self):
        """Test that different breeder types can have different capacities."""
        mill_breeder = MillBreeder(
            max_creatures=5,
            target_phenotypes=[{"trait_id": 0, "phenotype": "black"}]
        )
        kennel_breeder = KennelClubBreeder(
            max_creatures=10,
            target_phenotypes=[{"trait_id": 0, "phenotype": "black"}]
        )
        
        assert mill_breeder.max_creatures == 5
        assert kennel_breeder.max_creatures == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
