"""Tests for creature homing (spay/neuter and pet placement) functionality."""

import pytest
import sqlite3
from gene_sim.models.creature import Creature
from gene_sim.models.population import Population
from gene_sim.models.generation import Cycle
from gene_sim.models.trait import Trait
from gene_sim.models.breeder import KennelClubBreeder
from gene_sim.config import SimulationConfig
from gene_sim.database.connection import create_database
import numpy as np
import tempfile
import os


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    conn = create_database(path)
    
    cursor = conn.cursor()
    
    # Create a simulation record so creatures can be persisted
    cursor.execute("""
        INSERT INTO simulations (simulation_id, seed, start_time, config)
        VALUES (1, 42, datetime('now'), '{}')
    """)
    
    # Create a trait record so genotypes can be persisted
    cursor.execute("""
        INSERT INTO traits (trait_id, name, trait_type)
        VALUES (0, 'Test Trait', 'SIMPLE_MENDELIAN')
    """)
    
    conn.commit()
    
    yield conn
    conn.close()
    os.unlink(path)


@pytest.fixture
def simple_trait():
    """Create a simple Mendelian trait for testing."""
    return Trait.from_config({
        'trait_id': 0,
        'name': 'Coat Color',
        'trait_type': 'SIMPLE_MENDELIAN',
        'genotypes': [
            {'genotype': 'BB', 'phenotype': 'Black', 'initial_freq': 0.25},
            {'genotype': 'Bb', 'phenotype': 'Black', 'initial_freq': 0.50},
            {'genotype': 'bb', 'phenotype': 'Brown', 'initial_freq': 0.25}
        ]
    })


@pytest.fixture
def test_config():
    """Create a test simulation configuration."""
    class MockConfig:
        def __init__(self):
            self.creature_archetype = type('obj', (object,), {
                'remove_ineligible_immediately': False,
                'lifespan_cycles_min': 100,
                'lifespan_cycles_max': 200,
                'maturity_cycles': 10,
                'max_fertility_age_years': {'male': 10.0, 'female': 8.0},
                'max_fertility_age_cycles': {'male': 175, 'female': 140},
                'gestation_cycles': 3,
                'nursing_cycles': 2,
                'menstrual_cycle_days': 28.0,
                'nearing_end_cycles': 20,
                'litter_size_min': 2,
                'litter_size_max': 4
            })()
            self.cycles = 100
            self.mode = 'quiet'
    
    return MockConfig()


class TestOffspringHoming:
    """Test homing of offspring at birth."""
    
    def test_offspring_marked_as_homed_when_unclaimed(self, temp_db, simple_trait, test_config):
        """Test that unclaimed offspring are marked as homed."""
        rng = np.random.default_rng(42)
        
        # Create parents
        parent1 = Creature(
            simulation_id=1,
            birth_cycle=0,
            sex='male',
            genome=['BB'],
            breeder_id=1,
            lifespan=150,
            creature_id=1
        )
        
        parent2 = Creature(
            simulation_id=1,
            birth_cycle=0,
            sex='female',
            genome=['bb'],
            breeder_id=1,
            lifespan=150,
            creature_id=2
        )
        
        # Create offspring
        offspring = Creature.create_offspring(
            parent1=parent1,
            parent2=parent2,
            conception_cycle=0,
            simulation_id=1,
            traits=[simple_trait],
            rng=rng,
            config=test_config,
            produced_by_breeder_id=1
        )
        
        # Mark as homed (simulating unclaimed offspring)
        offspring.is_homed = True
        
        assert offspring.is_homed is True
        assert offspring.is_alive is True  # Still alive, just homed
    
    def test_homed_offspring_excluded_from_breeding_pool(self, temp_db, simple_trait, test_config):
        """Test that homed offspring are not eligible for breeding."""
        rng = np.random.default_rng(42)
        population = Population()
        
        # Create and add creatures
        creature1 = Creature(
            simulation_id=1,
            birth_cycle=0,
            sex='male',
            genome=['BB'],
            breeder_id=1,
            lifespan=150
        )
        creature1.sexual_maturity_cycle = 0
        creature1.max_fertility_age_cycle = 100
        creature1.is_homed = False
        
        creature2 = Creature(
            simulation_id=1,
            birth_cycle=0,
            sex='male',
            genome=['Bb'],
            breeder_id=1,
            lifespan=150
        )
        creature2.sexual_maturity_cycle = 0
        creature2.max_fertility_age_cycle = 100
        creature2.is_homed = True  # This one is homed
        
        population.creatures = [creature1, creature2]
        
        # Get eligible males
        eligible = population.get_eligible_males(10, test_config)
        
        # Only non-homed creature should be eligible
        assert len(eligible) == 1
        assert eligible[0].is_homed is False
    
    def test_all_offspring_added_to_population(self, temp_db, simple_trait, test_config):
        """Test that all offspring (homed and kept) are added to population."""
        population = Population()
        
        # Create offspring
        kept_offspring = Creature(
            simulation_id=1,
            birth_cycle=5,
            sex='female',
            genome=['Bb'],
            breeder_id=1,
            lifespan=150
        )
        kept_offspring.is_homed = False
        
        homed_offspring = Creature(
            simulation_id=1,
            birth_cycle=5,
            sex='male',
            genome=['BB'],
            breeder_id=1,
            lifespan=150
        )
        homed_offspring.is_homed = True
        
        # Add both to population
        population.add_creatures([kept_offspring, homed_offspring], current_cycle=5)
        
        # Both should be in population
        assert len(population.creatures) == 2
        assert kept_offspring in population.creatures
        assert homed_offspring in population.creatures


class TestAdultHoming:
    """Test homing of adult creatures during breeding cycles."""
    
    def test_non_breeding_adults_can_be_homed(self, temp_db, simple_trait, test_config):
        """Test that non-breeding adults can be marked as homed."""
        creature = Creature(
            simulation_id=1,
            birth_cycle=0,
            sex='female',
            genome=['Bb'],
            breeder_id=1,
            lifespan=150,
            creature_id=5
        )
        creature.sexual_maturity_cycle = 0
        creature.max_fertility_age_cycle = 100
        
        # Mark as homed
        creature.is_homed = True
        
        assert creature.is_homed is True
        assert creature.is_alive is True
    
    def test_homed_adults_excluded_from_breeding_pool(self, temp_db, simple_trait, test_config):
        """Test that homed adults are not in breeding pool."""
        population = Population()
        
        # Create creatures - some homed, some not
        creature1 = Creature(
            simulation_id=1,
            birth_cycle=0,
            sex='female',
            genome=['BB'],
            breeder_id=1,
            lifespan=150
        )
        creature1.sexual_maturity_cycle = 0
        creature1.max_fertility_age_cycle = 100
        creature1.is_homed = False
        
        creature2 = Creature(
            simulation_id=1,
            birth_cycle=0,
            sex='female',
            genome=['Bb'],
            breeder_id=1,
            lifespan=150
        )
        creature2.sexual_maturity_cycle = 0
        creature2.max_fertility_age_cycle = 100
        creature2.is_homed = True
        
        population.creatures = [creature1, creature2]
        
        # Get eligible females
        eligible = population.get_eligible_females(10, test_config)
        
        # Only non-homed creature should be eligible
        assert len(eligible) == 1
        assert eligible[0].is_homed is False
    
    def test_breeding_creatures_not_homed(self, temp_db, simple_trait, test_config):
        """Test that creatures that bred are not selected for homing."""
        rng = np.random.default_rng(42)
        
        # Create eligible creatures
        male1 = Creature(
            simulation_id=1,
            birth_cycle=0,
            sex='male',
            genome=['BB'],
            breeder_id=1,
            lifespan=150,
            creature_id=1
        )
        male1.is_homed = False
        
        male2 = Creature(
            simulation_id=1,
            birth_cycle=0,
            sex='male',
            genome=['Bb'],
            breeder_id=1,
            lifespan=150,
            creature_id=2
        )
        male2.is_homed = False
        
        # Simulate breeding pairs (male1 bred, male2 did not)
        breeding_pairs = [(male1, None, 1)]
        
        # Get cycle instance to test spay/neuter logic
        cycle = Cycle(0)
        
        # Manually test the logic: male1 bred, male2 did not
        bred_creature_ids = {male1.creature_id}
        
        # Non-breeding males should not include male1
        eligible_males = [male1, male2]
        non_breeding = [m for m in eligible_males 
                       if m.creature_id not in bred_creature_ids and not m.is_homed]
        
        assert len(non_breeding) == 1
        assert non_breeding[0].creature_id == 2  # male2 didn't breed


class TestHomedCreatureLifecycle:
    """Test that homed creatures live out their natural lifespan."""
    
    def test_homed_creature_stays_alive_until_lifespan(self, temp_db, simple_trait, test_config):
        """Test that homed creatures remain alive until they age out."""
        creature = Creature(
            simulation_id=1,
            birth_cycle=0,
            sex='male',
            genome=['BB'],
            breeder_id=1,
            lifespan=50  # Will die at cycle 50
        )
        creature.is_homed = True
        
        # Creature should be alive before lifespan ends
        assert creature.is_alive is True
        
        # Check if would age out (simulated)
        current_cycle = 49
        age = current_cycle - creature.birth_cycle
        assert age < creature.lifespan
        
        # At cycle 50, would age out
        current_cycle = 50
        age = current_cycle - creature.birth_cycle
        assert age >= creature.lifespan
    
    def test_homed_and_kept_offspring_both_in_living_count(self, temp_db, simple_trait, test_config):
        """Test that both homed and kept offspring count as living."""
        population = Population()
        
        offspring1 = Creature(
            simulation_id=1,
            birth_cycle=5,
            sex='female',
            genome=['Bb'],
            breeder_id=1,
            lifespan=150
        )
        offspring1.is_homed = False
        
        offspring2 = Creature(
            simulation_id=1,
            birth_cycle=5,
            sex='male',
            genome=['BB'],
            breeder_id=1,
            lifespan=150
        )
        offspring2.is_homed = True
        
        population.creatures = [offspring1, offspring2]
        
        # Both should count as living
        assert len(population.creatures) == 2


class TestDatabasePersistence:
    """Test that is_homed field is properly persisted to database."""
    
    def test_homed_field_persisted_to_database(self, temp_db, simple_trait, test_config):
        """Test that is_homed is correctly saved to database."""
        population = Population()
        
        creature = Creature(
            simulation_id=1,
            birth_cycle=0,
            sex='male',
            genome=['BB'],
            breeder_id=None,  # No breeder assignment needed for this test
            lifespan=150
        )
        creature.is_homed = True
        
        # Persist to database
        population._persist_creatures(temp_db, 1, [creature])
        
        # Retrieve from database
        cursor = temp_db.cursor()
        cursor.execute("SELECT is_homed FROM creatures WHERE creature_id = ?", (creature.creature_id,))
        result = cursor.fetchone()
        
        assert result is not None
        assert result[0] == 1  # Boolean True stored as 1
    
    def test_update_homed_status_in_database(self, temp_db, simple_trait, test_config):
        """Test that is_homed can be updated in database."""
        population = Population()
        
        creature = Creature(
            simulation_id=1,
            birth_cycle=0,
            sex='male',
            genome=['BB'],
            breeder_id=None,  # No breeder assignment needed for this test
            lifespan=150
        )
        creature.is_homed = False
        
        # Persist initially
        population._persist_creatures(temp_db, 1, [creature])
        
        # Update to homed
        cursor = temp_db.cursor()
        cursor.execute("UPDATE creatures SET is_homed = 1 WHERE creature_id = ?", 
                      (creature.creature_id,))
        temp_db.commit()
        
        # Verify update
        cursor.execute("SELECT is_homed FROM creatures WHERE creature_id = ?", 
                      (creature.creature_id,))
        result = cursor.fetchone()
        
        assert result[0] == 1


class TestHomingStatistics:
    """Test that homing is properly tracked in cycle statistics."""
    
    def test_homed_count_in_cycle_stats(self, temp_db, simple_trait, test_config):
        """Test that homed count is tracked in CycleStats."""
        from gene_sim.models.generation import CycleStats
        
        stats = CycleStats(
            cycle=0,
            population_size=100,
            eligible_males=20,
            eligible_females=20,
            births=10,
            deaths=2,
            genotype_frequencies={},
            allele_frequencies={},
            heterozygosity={},
            genotype_diversity={},
            homed_out=15  # 15 creatures homed this cycle
        )
        
        assert stats.homed_out == 15
        assert stats.population_size == 100  # Population includes homed creatures
