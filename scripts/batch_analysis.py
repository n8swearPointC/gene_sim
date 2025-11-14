"""
Batch analysis script for processing all simulation databases in a directory.

DEPRECATED: Use batch_analysis_unified.py instead.
    python batch_analysis_unified.py --individual <directory>

This script is maintained for backward compatibility but the unified interface
provides better usability and consistent argument handling.

Creates individual analysis reports and consolidated charts showing
undesirable phenotype frequency trends across all runs.

Enhanced to:
- Create separate charts for each undesirable trait
- Show starting genotype frequencies
- Display individual runs in grey with aggregate trend line
"""

import sqlite3
import sys
from pathlib import Path
import matplotlib.pyplot as plt
import yaml
from collections import defaultdict
import numpy as np


def get_all_databases(directory="."):
    """Get all simulation database files in the directory."""
    path = Path(directory)
    db_files = sorted(path.glob("simulation_run_*.db"))
    return db_files


def get_simulation_info(db_path):
    """Get basic simulation information."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get simulation ID
    cursor.execute("SELECT simulation_id FROM simulations LIMIT 1")
    sim_id = cursor.fetchone()[0]
    
    # Get breeder counts
    cursor.execute("""
        SELECT breeder_type, COUNT(*) 
        FROM breeders 
        WHERE simulation_id = ?
        GROUP BY breeder_type
    """, (sim_id,))
    
    breeders = {}
    for breeder_type, count in cursor.fetchall():
        breeders[breeder_type] = count
    
    conn.close()
    return sim_id, breeders


def get_trait_info(directory, trait_id):
    """Get trait information from config file."""
    config_path = Path(directory) / "batch_config.yaml"
    
    if not config_path.exists():
        config_path = Path(directory).parent / "quick_test_config.yaml"
    
    if not config_path.exists():
        return None
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    traits = config.get('traits', [])
    for trait in traits:
        if trait.get('trait_id') == trait_id:
            return trait
    
    return None


def analyze_trait_characteristics(trait_info, target_phenotype, target_genotypes):
    """
    Analyze trait characteristics to determine dominance and frequency.
    
    Returns:
        dict: {
            'dominance': 'Dominant' or 'Recessive',
            'frequency': 'Common' or 'Uncommon',
            'starting_freq': float (percentage)
        }
    """
    if not trait_info:
        return {'dominance': 'Unknown', 'frequency': 'Unknown', 'starting_freq': 0.0}
    
    # Calculate starting frequency of undesirable phenotype
    total_freq = 0.0
    for genotype_info in trait_info.get('genotypes', []):
        if genotype_info['genotype'] in target_genotypes:
            total_freq += genotype_info['initial_freq']
    
    starting_freq_pct = total_freq * 100
    
    # Determine if common or uncommon (threshold at 50%)
    frequency = 'Common' if starting_freq_pct >= 50.0 else 'Uncommon'
    
    # Determine dominance pattern
    # For simple Mendelian: if heterozygote shows the trait, it's dominant
    # if only homozygote shows it, it's recessive
    dominance = 'Unknown'
    
    if trait_info.get('trait_type') == 'SIMPLE_MENDELIAN':
        # Check if heterozygote genotype is in target genotypes
        genotypes_list = [g['genotype'] for g in trait_info.get('genotypes', [])]
        
        # Find heterozygote (has both uppercase and lowercase of same letter)
        for genotype in genotypes_list:
            if len(genotype) == 2 and genotype[0].upper() == genotype[1].upper() and genotype[0] != genotype[1]:
                # This is heterozygote
                is_het_undesirable = genotype in target_genotypes
                
                # Find homozygous uppercase and lowercase
                upper_homo = genotype[0].upper() * 2
                lower_homo = genotype[0].lower() * 2
                
                is_upper_homo_undesirable = upper_homo in target_genotypes
                is_lower_homo_undesirable = lower_homo in target_genotypes
                
                # Determine dominance
                if is_het_undesirable and is_upper_homo_undesirable and not is_lower_homo_undesirable:
                    dominance = 'Dominant'
                elif is_het_undesirable and is_lower_homo_undesirable and not is_upper_homo_undesirable:
                    dominance = 'Recessive-allele Dominant'
                elif not is_het_undesirable and is_upper_homo_undesirable:
                    dominance = 'Recessive'
                elif not is_het_undesirable and is_lower_homo_undesirable:
                    dominance = 'Recessive'
                break
    
    return {
        'dominance': dominance,
        'frequency': frequency,
        'starting_freq': starting_freq_pct
    }


def get_target_phenotypes(directory="."):
    """Get list of target (desired) phenotypes from batch config file."""
    config_path = Path(directory) / "batch_config.yaml"
    
    if not config_path.exists():
        config_path = Path(directory).parent / "quick_test_config.yaml"
    
    if not config_path.exists():
        return []
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    target = config.get('target_phenotypes', [])
    
    return target


def analyze_undesirable_in_desired_population(db_path, trait_id, target_phenotype, directory="."):
    """
    Analyze undesirable phenotype frequency only among creatures with ALL desired phenotypes.
    
    Args:
        db_path: Path to database file
        trait_id: ID of the undesirable trait to analyze
        target_phenotype: Name of the undesirable phenotype
        directory: Directory for config lookup
    
    Returns:
        tuple: (cycles, frequencies, target_genotypes) where frequencies are percentages
               of creatures with the undesirable trait among those with all desired traits
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get simulation ID
    cursor.execute("SELECT simulation_id FROM simulations LIMIT 1")
    sim_id = cursor.fetchone()[0]
    
    # Get target (desired) phenotypes
    target_pheno_list = get_target_phenotypes(directory)
    
    if not target_pheno_list:
        conn.close()
        return [], [], []
    
    # Get genotypes that map to the undesirable phenotype
    cursor.execute("""
        SELECT genotype
        FROM genotypes
        WHERE trait_id = ? AND phenotype = ?
    """, (trait_id, target_phenotype))
    
    undesirable_genotypes = [row[0] for row in cursor.fetchall()]
    
    if not undesirable_genotypes:
        conn.close()
        return [], [], []
    
    # For each target phenotype, get the genotypes that express it
    target_genotype_map = {}
    for target in target_pheno_list:
        target_trait_id = target['trait_id']
        target_pheno = target['phenotype']
        
        cursor.execute("""
            SELECT genotype
            FROM genotypes
            WHERE trait_id = ? AND phenotype = ?
        """, (target_trait_id, target_pheno))
        
        target_genotype_map[target_trait_id] = [row[0] for row in cursor.fetchall()]
    
    # Get all creatures by generation and check their phenotypes
    cursor.execute("""
        SELECT DISTINCT generation
        FROM creatures
        WHERE simulation_id = ?
        ORDER BY generation
    """, (sim_id,))
    
    generations = [row[0] for row in cursor.fetchall()]
    generation_frequencies = {}
    
    for generation in generations:
        # Get all living creatures in this generation (homed or not)
        cursor.execute("""
            SELECT creature_id
            FROM creatures
            WHERE simulation_id = ? AND generation = ? AND is_alive = 1
        """, (sim_id, generation))
        
        creature_ids = [row[0] for row in cursor.fetchall()]
        
        if not creature_ids:
            continue
        
        # Count creatures with all desired phenotypes
        creatures_with_all_desired = []
        
        for creature_id in creature_ids:
            # Check if this creature has all desired phenotypes
            has_all_desired = True
            
            for target_trait_id, desired_genotypes in target_genotype_map.items():
                cursor.execute("""
                    SELECT genotype
                    FROM creature_genotypes
                    WHERE creature_id = ? AND trait_id = ?
                """, (creature_id, target_trait_id))
                
                result = cursor.fetchone()
                if not result or result[0] not in desired_genotypes:
                    has_all_desired = False
                    break
            
            if has_all_desired:
                creatures_with_all_desired.append(creature_id)
        
        # Among creatures with all desired phenotypes, count those with the undesirable trait
        if creatures_with_all_desired:
            count_with_undesirable = 0
            
            for creature_id in creatures_with_all_desired:
                cursor.execute("""
                    SELECT genotype
                    FROM creature_genotypes
                    WHERE creature_id = ? AND trait_id = ?
                """, (creature_id, trait_id))
                
                result = cursor.fetchone()
                if result and result[0] in undesirable_genotypes:
                    count_with_undesirable += 1
            
            frequency = count_with_undesirable / len(creatures_with_all_desired)
            generation_frequencies[generation] = frequency
        else:
            # No creatures with all desired phenotypes
            generation_frequencies[generation] = 0.0
    
    conn.close()
    
    # Convert to sorted lists
    cycles = sorted(generation_frequencies.keys())
    frequencies = [generation_frequencies[c] * 100 for c in cycles]  # Convert to percentage
    
    return cycles, frequencies, undesirable_genotypes


def get_undesirable_phenotypes(directory="."):

    """Get list of undesirable phenotypes from batch config file."""
    # Look for batch_config.yaml in the directory
    config_path = Path(directory) / "batch_config.yaml"
    
    if not config_path.exists():
        # Fallback to quick_test_config.yaml
        config_path = Path(directory).parent / "quick_test_config.yaml"
    
    if not config_path.exists():
        return []
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    undesirable = config.get('undesirable_phenotypes', [])
    
    return undesirable


def get_starting_genotype_frequencies(db_path, trait_id):
    """Get starting (generation 0) genotype frequencies for a trait."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get simulation ID
    cursor.execute("SELECT simulation_id FROM simulations LIMIT 1")
    sim_id = cursor.fetchone()[0]
    
    # Get generation 0 genotype frequencies
    cursor.execute("""
        SELECT genotype, frequency
        FROM generation_genotype_frequencies
        WHERE simulation_id = ? AND trait_id = ? AND generation = 0
        ORDER BY genotype
    """, (sim_id, trait_id))
    
    genotype_freqs = {row[0]: row[1] * 100 for row in cursor.fetchall()}
    conn.close()
    
    return genotype_freqs


def analyze_undesirable_phenotype_trend(db_path, trait_id, target_phenotype, directory="."):
    """
    Analyze the trend of undesirable phenotype frequency over generations.
    
    Args:
        db_path: Path to database file
        trait_id: ID of the trait to analyze
        target_phenotype: Name of the undesirable phenotype
        directory: Directory for config lookup
    
    Returns:
        tuple: (cycles, frequencies) where cycles are generation numbers
               and frequencies are percentages of undesirable phenotype
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get simulation ID
    cursor.execute("SELECT simulation_id FROM simulations LIMIT 1")
    sim_id = cursor.fetchone()[0]
    
    # Get genotypes that map to this phenotype
    cursor.execute("""
        SELECT genotype
        FROM genotypes
        WHERE trait_id = ? AND phenotype = ?
    """, (trait_id, target_phenotype))
    
    target_genotypes = [row[0] for row in cursor.fetchall()]
    
    if not target_genotypes:
        conn.close()
        return [], []
    
    # Get frequency data for each generation
    cursor.execute("""
        SELECT generation, genotype, frequency
        FROM generation_genotype_frequencies
        WHERE simulation_id = ? AND trait_id = ?
        ORDER BY generation
    """, (sim_id, trait_id))
    
    # Aggregate frequencies by generation
    generation_frequencies = defaultdict(float)
    
    for generation, genotype, frequency in cursor.fetchall():
        if genotype in target_genotypes:
            generation_frequencies[generation] += frequency
    
    conn.close()
    
    # Convert to sorted lists
    cycles = sorted(generation_frequencies.keys())
    frequencies = [generation_frequencies[c] * 100 for c in cycles]  # Convert to percentage
    
    return cycles, frequencies, target_genotypes


def create_comprehensive_charts(db_files, output_dir=".", aggregate_method="mean"):
    """
    Create comprehensive charts showing undesirable phenotype trends
    across all simulation runs - one chart per undesirable trait.
    
    Args:
        db_files: List of database file paths
        output_dir: Directory to save charts
        aggregate_method: Method for aggregate line - 'mean', 'median', 'mean_ci', or 'moving_avg'
    """
    if not db_files:
        print("No database files found!")
        return
    
    # Get breeder distribution from first database (should be same for all)
    _, breeders = get_simulation_info(db_files[0])
    total_breeders = sum(breeders.values())
    kennel_pct = (breeders.get('kennel_club', 0) / total_breeders) * 100 if total_breeders > 0 else 0
    mill_pct = (breeders.get('mill', 0) / total_breeders) * 100 if total_breeders > 0 else 0
    
    # Get all undesirable phenotypes
    undesirable_list = get_undesirable_phenotypes(output_dir)
    
    if not undesirable_list:
        print("No undesirable phenotypes found in config!")
        return
    
    print(f"\nFound {len(undesirable_list)} undesirable traits to chart")
    
    # Create a chart for each undesirable trait
    for trait_idx, undesirable in enumerate(undesirable_list, 1):
        trait_id = undesirable['trait_id']
        target_phenotype = undesirable['phenotype']
        
        print(f"  [{trait_idx}/{len(undesirable_list)}] Creating chart for {target_phenotype} (trait {trait_id})...")
        
        # Collect data from all runs
        all_cycles = []
        all_frequencies = []
        target_genotypes = None
        starting_freqs = None
        
        for db_file in db_files:
            cycles, frequencies, genotypes = analyze_undesirable_phenotype_trend(
                db_file, trait_id, target_phenotype, output_dir
            )
            
            if cycles and frequencies:
                all_cycles.append(cycles)
                all_frequencies.append(frequencies)
                
                # Get genotypes and starting frequencies from first valid database
                if target_genotypes is None:
                    target_genotypes = genotypes
                    starting_freqs = get_starting_genotype_frequencies(db_file, trait_id)
        
        if not all_frequencies:
            print(f"    Warning: No data found for {target_phenotype}")
            continue
        
        # Get trait information and analyze characteristics
        trait_info = get_trait_info(output_dir, trait_id)
        trait_chars = analyze_trait_characteristics(trait_info, target_phenotype, target_genotypes)
        
        # Create the chart
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Find max length for padding
        max_len = max(len(cycles) for cycles in all_cycles)
        
        # Pad all frequency arrays and plot individual runs in grey
        padded_frequencies = []
        for cycles, frequencies in zip(all_cycles, all_frequencies):
            if len(frequencies) < max_len:
                # Pad with last value
                padded = frequencies + [frequencies[-1]] * (max_len - len(frequencies))
            else:
                padded = frequencies
            padded_frequencies.append(padded)
            
            # Invert y-axis by negating cycle numbers
            inverted_cycles = [-i for i in range(len(padded))]
            ax.plot(padded, inverted_cycles, color='grey', alpha=0.3, linewidth=1)
        
        # Calculate and plot aggregate line
        freq_array = np.array(padded_frequencies)
        inverted_cycles = [-i for i in range(max_len)]
        
        if aggregate_method == 'mean':
            aggregate = np.mean(freq_array, axis=0)
            ax.plot(aggregate, inverted_cycles, color='darkred', linewidth=2.5, 
                   label='Mean', zorder=10)
        
        elif aggregate_method == 'median':
            aggregate = np.median(freq_array, axis=0)
            ax.plot(aggregate, inverted_cycles, color='darkred', linewidth=2.5,
                   label='Median', zorder=10)
        
        elif aggregate_method == 'mean_ci':
            mean = np.mean(freq_array, axis=0)
            std = np.std(freq_array, axis=0)
            ci_upper = mean + std
            ci_lower = mean - std
            
            ax.fill_betweenx(inverted_cycles, ci_lower, ci_upper, 
                           color='darkred', alpha=0.2, label='Mean ± 1 SD')
            ax.plot(mean, inverted_cycles, color='darkred', linewidth=2.5,
                   label='Mean', zorder=10)
        
        elif aggregate_method == 'moving_avg':
            # Simple moving average with window of 3 generations
            window = 3
            aggregate = np.convolve(np.mean(freq_array, axis=0), 
                                   np.ones(window)/window, mode='same')
            ax.plot(aggregate, inverted_cycles, color='darkred', linewidth=2.5,
                   label='Moving Average', zorder=10)
        
        # Configure the chart
        ax.set_xlabel('Undesirable Phenotype (%)', fontsize=12, fontweight='bold')
        ax.set_ylabel('')  # No label for y-axis
        
        # Remove y-axis tick marks and labels
        ax.set_yticks([])
        ax.tick_params(axis='y', which='both', left=False, right=False)
        
        # Format x-axis
        ax.set_xlim(0, 100)
        ax.set_xticks(range(0, 101, 10))
        ax.grid(True, axis='x', alpha=0.3, linestyle='--')
        
        # Add title and subtitle with trait characteristics
        title = f"Undesirable | {trait_chars['dominance']} | {trait_chars['frequency']}"
        subtitle = f"Kennels {kennel_pct:.0f}% : {mill_pct:.0f}% Mills"
        trait_name = f"{target_phenotype} (Trait {trait_id})"
        
        ax.set_title(title, fontsize=16, fontweight='bold', pad=50)
        ax.text(0.5, 1.04, subtitle, transform=ax.transAxes, 
                ha='center', fontsize=12, style='italic')
        ax.text(0.5, 1.01, trait_name, transform=ax.transAxes,
                ha='center', fontsize=10, alpha=0.7)
        
        # Add starting genotype frequencies info
        if starting_freqs:
            # Format genotype info
            genotype_info = "Starting Frequencies: " + ", ".join(
                f"{gt}: {freq:.1f}%" for gt, freq in sorted(starting_freqs.items())
            )
            # Highlight tracked genotypes
            tracked_info = f"Tracked: {', '.join(sorted(target_genotypes))}"
            
            ax.text(0.5, 1.08, genotype_info, transform=ax.transAxes,
                   ha='center', fontsize=9, style='italic', alpha=0.8)
            ax.text(0.5, 1.06, tracked_info, transform=ax.transAxes,
                   ha='center', fontsize=9, fontweight='bold', alpha=0.9)
        
        # Add subtle note about y-axis orientation
        ax.text(0.02, 0.98, 'Earlier → Later Generations ↓', 
                transform=ax.transAxes, fontsize=9, alpha=0.6,
                verticalalignment='top')
        
        # Add legend
        ax.legend(loc='lower right', fontsize=10)
        
        plt.tight_layout()
        
        # Save the chart
        safe_name = target_phenotype.lower().replace(' ', '_')
        output_path = Path(output_dir) / f"undesirable_{safe_name}_trends.png"
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f"    Saved: {output_path.name}")
        plt.close()
    
    return len(undesirable_list)


def run_comprehensive_analytics(db_file, output_dir="."):
    """Run comprehensive analytics and save to file."""
    from analytics.comprehensive_analytics import analyze_comprehensive
    import sys
    from io import StringIO
    
    # Capture output
    old_stdout = sys.stdout
    sys.stdout = output_buffer = StringIO()
    
    try:
        analyze_comprehensive(str(db_file))
        output_text = output_buffer.getvalue()
    finally:
        sys.stdout = old_stdout
    
    # Save to file
    run_name = db_file.stem  # e.g., "simulation_run_001_seed_1000"
    output_path = Path(output_dir) / f"analysis_{run_name}.txt"
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(output_text)
    
    return output_path


def create_combined_charts(kennel_dir, mill_dir, output_dir, aggregate_method="mean"):
    """
    Create combined charts showing kennel and mill data together.
    
    Args:
        kennel_dir: Directory containing kennel databases
        mill_dir: Directory containing mill databases
        output_dir: Directory to save combined charts
        aggregate_method: Method for aggregate line
    """
    # Color-blind friendly colors
    # Blue/teal for kennels, Orange/red for mills
    kennel_color = '#0173B2'  # Blue (color-blind safe)
    kennel_light = '#56B4E9'  # Light blue
    mill_color = '#DE8F05'    # Orange (color-blind safe)
    mill_light = '#F0E442'    # Yellow-orange
    
    print("\n" + "="*80)
    print("CREATING COMBINED KENNEL vs MILL CHARTS")
    print("="*80)
    
    # Get databases
    kennel_files = get_all_databases(kennel_dir)
    mill_files = get_all_databases(mill_dir)
    
    if not kennel_files or not mill_files:
        print("Error: Need both kennel and mill databases!")
        return 0
    
    print(f"\nKennel databases: {len(kennel_files)}")
    print(f"Mill databases: {len(mill_files)}")
    
    # Get undesirable phenotypes from kennel config
    undesirable_list = get_undesirable_phenotypes(kennel_dir)
    
    if not undesirable_list:
        print("No undesirable phenotypes found in config!")
        return 0
    
    print(f"\nFound {len(undesirable_list)} undesirable traits to chart")
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Create a chart for each undesirable trait
    for trait_idx, undesirable in enumerate(undesirable_list, 1):
        trait_id = undesirable['trait_id']
        target_phenotype = undesirable['phenotype']
        
        print(f"  [{trait_idx}/{len(undesirable_list)}] Creating combined chart for {target_phenotype} (trait {trait_id})...")
        
        # Collect kennel data
        kennel_cycles_list = []
        kennel_frequencies_list = []
        target_genotypes = None
        starting_freqs = None
        trait_info = None
        
        for db_file in kennel_files:
            cycles, frequencies, genotypes = analyze_undesirable_phenotype_trend(
                db_file, trait_id, target_phenotype, kennel_dir
            )
            
            if cycles and frequencies:
                kennel_cycles_list.append(cycles)
                kennel_frequencies_list.append(frequencies)
                
                if target_genotypes is None:
                    target_genotypes = genotypes
                    starting_freqs = get_starting_genotype_frequencies(db_file, trait_id)
                    trait_info = get_trait_info(kennel_dir, trait_id)
        
        # Collect mill data
        mill_cycles_list = []
        mill_frequencies_list = []
        
        for db_file in mill_files:
            cycles, frequencies, genotypes = analyze_undesirable_phenotype_trend(
                db_file, trait_id, target_phenotype, mill_dir
            )
            
            if cycles and frequencies:
                mill_cycles_list.append(cycles)
                mill_frequencies_list.append(frequencies)
        
        if not kennel_frequencies_list or not mill_frequencies_list:
            print(f"    Warning: Missing data for {target_phenotype}")
            continue
        
        # Get trait characteristics
        trait_chars = analyze_trait_characteristics(trait_info, target_phenotype, target_genotypes)
        
        # Create the chart
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Find max length for padding
        max_len_kennel = max(len(cycles) for cycles in kennel_cycles_list)
        max_len_mill = max(len(cycles) for cycles in mill_cycles_list)
        max_len = max(max_len_kennel, max_len_mill)
        
        # Pad and plot kennel runs (faded blue)
        padded_kennel = []
        for cycles, frequencies in zip(kennel_cycles_list, kennel_frequencies_list):
            if len(frequencies) < max_len:
                padded = frequencies + [frequencies[-1]] * (max_len - len(frequencies))
            else:
                padded = frequencies
            padded_kennel.append(padded)
            
            inverted_cycles = [-i for i in range(len(padded))]
            ax.plot(padded, inverted_cycles, color=kennel_light, alpha=0.25, linewidth=1)
        
        # Pad and plot mill runs (faded orange)
        padded_mill = []
        for cycles, frequencies in zip(mill_cycles_list, mill_frequencies_list):
            if len(frequencies) < max_len:
                padded = frequencies + [frequencies[-1]] * (max_len - len(frequencies))
            else:
                padded = frequencies
            padded_mill.append(padded)
            
            inverted_cycles = [-i for i in range(len(padded))]
            ax.plot(padded, inverted_cycles, color=mill_light, alpha=0.25, linewidth=1)
        
        # Calculate and plot aggregate lines
        kennel_array = np.array(padded_kennel)
        mill_array = np.array(padded_mill)
        inverted_cycles = [-i for i in range(max_len)]
        
        if aggregate_method == 'mean':
            kennel_agg = np.mean(kennel_array, axis=0)
            mill_agg = np.mean(mill_array, axis=0)
            ax.plot(kennel_agg, inverted_cycles, color=kennel_color, linewidth=3, 
                   label='Kennels (Ensemble Avg)', zorder=10)
            ax.plot(mill_agg, inverted_cycles, color=mill_color, linewidth=3,
                   label='Mills (Ensemble Avg)', zorder=10)
        
        elif aggregate_method == 'median':
            kennel_agg = np.median(kennel_array, axis=0)
            mill_agg = np.median(mill_array, axis=0)
            ax.plot(kennel_agg, inverted_cycles, color=kennel_color, linewidth=3,
                   label='Kennels (Median)', zorder=10)
            ax.plot(mill_agg, inverted_cycles, color=mill_color, linewidth=3,
                   label='Mills (Median)', zorder=10)
        
        elif aggregate_method == 'mean_ci':
            kennel_mean = np.mean(kennel_array, axis=0)
            kennel_std = np.std(kennel_array, axis=0)
            mill_mean = np.mean(mill_array, axis=0)
            mill_std = np.std(mill_array, axis=0)
            
            ax.fill_betweenx(inverted_cycles, kennel_mean - kennel_std, kennel_mean + kennel_std,
                           color=kennel_color, alpha=0.15)
            ax.fill_betweenx(inverted_cycles, mill_mean - mill_std, mill_mean + mill_std,
                           color=mill_color, alpha=0.15)
            
            ax.plot(kennel_mean, inverted_cycles, color=kennel_color, linewidth=3,
                   label='Kennels (Ensemble Avg)', zorder=10)
            ax.plot(mill_mean, inverted_cycles, color=mill_color, linewidth=3,
                   label='Mills (Ensemble Avg)', zorder=10)
        
        elif aggregate_method == 'moving_avg':
            window = 3
            kennel_agg = np.convolve(np.mean(kennel_array, axis=0), 
                                   np.ones(window)/window, mode='same')
            mill_agg = np.convolve(np.mean(mill_array, axis=0),
                                 np.ones(window)/window, mode='same')
            ax.plot(kennel_agg, inverted_cycles, color=kennel_color, linewidth=3,
                   label='Kennels (Moving Avg)', zorder=10)
            ax.plot(mill_agg, inverted_cycles, color=mill_color, linewidth=3,
                   label='Mills (Moving Avg)', zorder=10)
        
        # Configure the chart
        ax.set_xlabel('Undesirable Phenotype (%)', fontsize=12, fontweight='bold')
        ax.set_ylabel('')
        
        # Remove y-axis tick marks and labels
        ax.set_yticks([])
        ax.tick_params(axis='y', which='both', left=False, right=False)
        
        # Format x-axis
        ax.set_xlim(0, 100)
        ax.set_xticks(range(0, 101, 10))
        ax.grid(True, axis='x', alpha=0.3, linestyle='--')
        
        # Add title and subtitle with trait characteristics
        title = f"Undesirable | {trait_chars['dominance']} | {trait_chars['frequency']}"
        subtitle = "Kennels vs Mills Comparison"
        trait_name = f"{target_phenotype} (Trait {trait_id})"
        
        ax.set_title(title, fontsize=16, fontweight='bold', pad=50)
        ax.text(0.5, 1.04, subtitle, transform=ax.transAxes, 
                ha='center', fontsize=12, style='italic')
        ax.text(0.5, 1.01, trait_name, transform=ax.transAxes,
                ha='center', fontsize=10, alpha=0.7)
        
        # Add starting genotype frequencies info
        if starting_freqs:
            genotype_info = "Starting Frequencies: " + ", ".join(
                f"{gt}: {freq:.1f}%" for gt, freq in sorted(starting_freqs.items())
            )
            tracked_info = f"Tracked: {', '.join(sorted(target_genotypes))}"
            
            ax.text(0.5, 1.08, genotype_info, transform=ax.transAxes,
                   ha='center', fontsize=9, style='italic', alpha=0.8)
            ax.text(0.5, 1.06, tracked_info, transform=ax.transAxes,
                   ha='center', fontsize=9, fontweight='bold', alpha=0.9)
        
        # Add note about y-axis orientation
        ax.text(0.02, 0.98, 'Earlier → Later Generations ↓', 
                transform=ax.transAxes, fontsize=9, alpha=0.6,
                verticalalignment='top')
        
        # Add legend
        ax.legend(loc='lower right', fontsize=11, framealpha=0.9)
        
        plt.tight_layout()
        
        # Save the chart
        safe_name = target_phenotype.lower().replace(' ', '_')
        output_file = output_path / f"combined_{safe_name}_trends.png"
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f"    Saved: {output_file.name}")
        plt.close()
    
    return len(undesirable_list)


def create_combined_charts_desired_only(kennel_dir, mill_dir, output_dir, aggregate_method="mean"):
    """
    Create combined charts showing kennel and mill data together,
    but calculating undesirable trait frequency ONLY among creatures with all desired phenotypes.
    
    Args:
        kennel_dir: Directory containing kennel databases
        mill_dir: Directory containing mill databases
        output_dir: Directory to save combined charts
        aggregate_method: Method for aggregate line
    """
    # Color-blind friendly colors
    kennel_color = '#0173B2'  # Blue (color-blind safe)
    kennel_light = '#56B4E9'  # Light blue
    mill_color = '#DE8F05'    # Orange (color-blind safe)
    mill_light = '#F0E442'    # Yellow-orange
    
    print("\n" + "="*80)
    print("CREATING COMBINED CHARTS - Desired Population Only")
    print("="*80)
    
    # Get databases
    kennel_files = get_all_databases(kennel_dir)
    mill_files = get_all_databases(mill_dir)
    
    if not kennel_files or not mill_files:
        print("Error: Need both kennel and mill databases!")
        return 0
    
    print(f"\nKennel databases: {len(kennel_files)}")
    print(f"Mill databases: {len(mill_files)}")
    
    # Get target phenotypes
    target_phenos = get_target_phenotypes(kennel_dir)
    if target_phenos:
        print(f"\nDesired phenotypes (creatures must have ALL of these):")
        for tp in target_phenos:
            print(f"  - {tp['phenotype']} (trait {tp['trait_id']})")
    
    # Get undesirable phenotypes from kennel config
    undesirable_list = get_undesirable_phenotypes(kennel_dir)
    
    if not undesirable_list:
        print("No undesirable phenotypes found in config!")
        return 0
    
    print(f"\nFound {len(undesirable_list)} undesirable traits to chart")
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Create a chart for each undesirable trait
    for trait_idx, undesirable in enumerate(undesirable_list, 1):
        trait_id = undesirable['trait_id']
        target_phenotype = undesirable['phenotype']
        
        print(f"  [{trait_idx}/{len(undesirable_list)}] Creating chart for {target_phenotype} (trait {trait_id})...")
        
        # Collect kennel data
        kennel_cycles_list = []
        kennel_frequencies_list = []
        target_genotypes = None
        starting_freqs = None
        trait_info = None
        
        for db_file in kennel_files:
            cycles, frequencies, genotypes = analyze_undesirable_in_desired_population(
                db_file, trait_id, target_phenotype, kennel_dir
            )
            
            if cycles and frequencies:
                kennel_cycles_list.append(cycles)
                kennel_frequencies_list.append(frequencies)
                
                if target_genotypes is None:
                    target_genotypes = genotypes
                    starting_freqs = get_starting_genotype_frequencies(db_file, trait_id)
                    trait_info = get_trait_info(kennel_dir, trait_id)
        
        # Collect mill data
        mill_cycles_list = []
        mill_frequencies_list = []
        
        for db_file in mill_files:
            cycles, frequencies, genotypes = analyze_undesirable_in_desired_population(
                db_file, trait_id, target_phenotype, mill_dir
            )
            
            if cycles and frequencies:
                mill_cycles_list.append(cycles)
                mill_frequencies_list.append(frequencies)
        
        if not kennel_frequencies_list or not mill_frequencies_list:
            print(f"    Warning: Missing data for {target_phenotype}")
            continue
        
        # Get trait characteristics
        trait_chars = analyze_trait_characteristics(trait_info, target_phenotype, target_genotypes)
        
        # Create the chart
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Find max length for padding
        max_len_kennel = max(len(cycles) for cycles in kennel_cycles_list)
        max_len_mill = max(len(cycles) for cycles in mill_cycles_list)
        max_len = max(max_len_kennel, max_len_mill)
        
        # Pad and plot kennel runs (faded blue)
        padded_kennel = []
        for cycles, frequencies in zip(kennel_cycles_list, kennel_frequencies_list):
            if len(frequencies) < max_len:
                padded = frequencies + [frequencies[-1]] * (max_len - len(frequencies))
            else:
                padded = frequencies
            padded_kennel.append(padded)
            
            inverted_cycles = [-i for i in range(len(padded))]
            ax.plot(padded, inverted_cycles, color=kennel_light, alpha=0.25, linewidth=1)
        
        # Pad and plot mill runs (faded orange)
        padded_mill = []
        for cycles, frequencies in zip(mill_cycles_list, mill_frequencies_list):
            if len(frequencies) < max_len:
                padded = frequencies + [frequencies[-1]] * (max_len - len(frequencies))
            else:
                padded = frequencies
            padded_mill.append(padded)
            
            inverted_cycles = [-i for i in range(len(padded))]
            ax.plot(padded, inverted_cycles, color=mill_light, alpha=0.25, linewidth=1)
        
        # Calculate and plot aggregate lines
        kennel_array = np.array(padded_kennel)
        mill_array = np.array(padded_mill)
        inverted_cycles = [-i for i in range(max_len)]
        
        if aggregate_method == 'mean':
            kennel_agg = np.mean(kennel_array, axis=0)
            mill_agg = np.mean(mill_array, axis=0)
            ax.plot(kennel_agg, inverted_cycles, color=kennel_color, linewidth=3, 
                   label='Kennels (Ensemble Avg)', zorder=10)
            ax.plot(mill_agg, inverted_cycles, color=mill_color, linewidth=3,
                   label='Mills (Ensemble Avg)', zorder=10)
        
        elif aggregate_method == 'median':
            kennel_agg = np.median(kennel_array, axis=0)
            mill_agg = np.median(mill_array, axis=0)
            ax.plot(kennel_agg, inverted_cycles, color=kennel_color, linewidth=3,
                   label='Kennels (Median)', zorder=10)
            ax.plot(mill_agg, inverted_cycles, color=mill_color, linewidth=3,
                   label='Mills (Median)', zorder=10)
        
        elif aggregate_method == 'mean_ci':
            kennel_mean = np.mean(kennel_array, axis=0)
            kennel_std = np.std(kennel_array, axis=0)
            mill_mean = np.mean(mill_array, axis=0)
            mill_std = np.std(mill_array, axis=0)
            
            ax.fill_betweenx(inverted_cycles, kennel_mean - kennel_std, kennel_mean + kennel_std,
                           color=kennel_color, alpha=0.15)
            ax.fill_betweenx(inverted_cycles, mill_mean - mill_std, mill_mean + mill_std,
                           color=mill_color, alpha=0.15)
            
            ax.plot(kennel_mean, inverted_cycles, color=kennel_color, linewidth=3,
                   label='Kennels (Ensemble Avg)', zorder=10)
            ax.plot(mill_mean, inverted_cycles, color=mill_color, linewidth=3,
                   label='Mills (Ensemble Avg)', zorder=10)
        
        elif aggregate_method == 'moving_avg':
            window = 3
            kennel_agg = np.convolve(np.mean(kennel_array, axis=0), 
                                   np.ones(window)/window, mode='same')
            mill_agg = np.convolve(np.mean(mill_array, axis=0),
                                 np.ones(window)/window, mode='same')
            ax.plot(kennel_agg, inverted_cycles, color=kennel_color, linewidth=3,
                   label='Kennels (Moving Avg)', zorder=10)
            ax.plot(mill_agg, inverted_cycles, color=mill_color, linewidth=3,
                   label='Mills (Moving Avg)', zorder=10)
        
        # Configure the chart
        ax.set_xlabel('Undesirable Phenotype (% of Living w/ Desired Traits)', fontsize=12, fontweight='bold')
        ax.set_ylabel('')
        
        # Remove y-axis tick marks and labels
        ax.set_yticks([])
        ax.tick_params(axis='y', which='both', left=False, right=False)
        
        # Format x-axis
        ax.set_xlim(0, 100)
        ax.set_xticks(range(0, 101, 10))
        ax.grid(True, axis='x', alpha=0.3, linestyle='--')
        
        # Add title and subtitle with trait characteristics
        title = f"Undesirable | {trait_chars['dominance']} | {trait_chars['frequency']}"
        subtitle = "Kennels vs Mills - All Living Creatures with Desired Phenotypes"
        trait_name = f"{target_phenotype} (Trait {trait_id})"
        
        ax.set_title(title, fontsize=16, fontweight='bold', pad=50)
        ax.text(0.5, 1.04, subtitle, transform=ax.transAxes, 
                ha='center', fontsize=11, style='italic')
        ax.text(0.5, 1.01, trait_name, transform=ax.transAxes,
                ha='center', fontsize=10, alpha=0.7)
        
        # Add starting genotype frequencies info
        if starting_freqs:
            genotype_info = "Starting Frequencies: " + ", ".join(
                f"{gt}: {freq:.1f}%" for gt, freq in sorted(starting_freqs.items())
            )
            tracked_info = f"Tracked: {', '.join(sorted(target_genotypes))}"
            
            ax.text(0.5, 1.08, genotype_info, transform=ax.transAxes,
                   ha='center', fontsize=9, style='italic', alpha=0.8)
            ax.text(0.5, 1.06, tracked_info, transform=ax.transAxes,
                   ha='center', fontsize=9, fontweight='bold', alpha=0.9)
        
        # Add note about y-axis orientation
        ax.text(0.02, 0.98, 'Earlier → Later Generations ↓', 
                transform=ax.transAxes, fontsize=9, alpha=0.6,
                verticalalignment='top')
        
        # Add legend
        ax.legend(loc='lower right', fontsize=11, framealpha=0.9)
        
        plt.tight_layout()
        
        # Save the chart
        safe_name = target_phenotype.lower().replace(' ', '_')
        output_file = output_path / f"combined_desired_{safe_name}_trends.png"
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f"    Saved: {output_file.name}")
        plt.close()
    
    return len(undesirable_list)


def main():
    """Main batch analysis function."""
    import sys
    
    # Print deprecation warning
    print("\n" + "!"*80)
    print("DEPRECATION WARNING")
    print("!"*80)
    print("\nThis script (batch_analysis.py) is deprecated.")
    print("Please use the unified interface instead:")
    print()
    print("  python batch_analysis_unified.py --individual <directory> [--aggregate method]")
    print()
    print("Example:")
    print("  python batch_analysis_unified.py --individual run4/run4a_kennels")
    print()
    print("Continuing with legacy behavior...")
    print("!"*80 + "\n")
    
    # Determine directory to process
    directory = "."
    aggregate_method = "mean"  # Default: ensemble average
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        directory = sys.argv[1]
    
    if len(sys.argv) > 2:
        aggregate_method = sys.argv[2]
        if aggregate_method not in ['mean', 'median', 'mean_ci', 'moving_avg']:
            print(f"Invalid aggregate method: {aggregate_method}")
            print("Valid options: mean, median, mean_ci, moving_avg")
            return
    
    print("="*80)
    print("BATCH ANALYSIS - Undesirable Phenotype Trends")
    print("="*80)
    print(f"\nSearching for databases in: {directory}")
    print(f"Aggregate method: {aggregate_method}")
    print()
    print("Aggregate options:")
    print("  mean       - Ensemble average of all runs (DEFAULT)")
    print("  median     - Median value (less affected by outliers)")
    print("  mean_ci    - Ensemble average with shaded ±1 standard deviation")
    print("  moving_avg - Smoothed 3-generation moving average")
    print()
    
    # Get all database files
    db_files = get_all_databases(directory)
    
    if not db_files:
        print("No simulation databases found!")
        print("Looking for files matching: simulation_run_*.db")
        return
    
    print(f"Found {len(db_files)} database files\n")
    
    # Create output directory for text analyses
    output_dir = Path(directory) / "batch_analysis"
    output_dir.mkdir(exist_ok=True)
    
    # Process each database
    print("Generating individual analysis reports...")
    for i, db_file in enumerate(db_files, 1):
        print(f"  [{i}/{len(db_files)}] {db_file.name}...", end=" ")
        try:
            output_path = run_comprehensive_analytics(db_file, output_dir)
            print(f"✓ Saved to {output_path.name}")
        except Exception as e:
            print(f"✗ Error: {e}")
    
    print(f"\nText analyses saved to: {output_dir}")
    
    # Create comprehensive charts
    print("\nGenerating undesirable phenotype trend charts...")
    num_charts = create_comprehensive_charts(db_files, directory, aggregate_method)
    
    print("\n" + "="*80)
    print("BATCH ANALYSIS COMPLETE")
    print("="*80)
    print(f"\nOutputs:")
    print(f"  - Individual analyses: {output_dir}/")
    print(f"  - Trend charts: {num_charts} charts in {directory}/")
    print(f"    (undesirable_*_trends.png)")
    print()


if __name__ == "__main__":
    main()
