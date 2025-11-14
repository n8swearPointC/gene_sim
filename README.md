# Gene Sim - Genetic Breeding Simulator
## How Do Different Breeding Strategies Affect Animal Traits?

## What is This Project About?

This project uses computer simulations to study how traits (like eye color, coat type, or tail length) pass from parents to children in animal populations over many generations. We wanted to answer a big question: **What's the difference between responsible breeding (like a good kennel) and mass breeding (like a puppy mill)?**

## Why Does This Matter?

When people breed animals, their choices affect which traits become common and which traits disappear. Understanding this helps us:
- Learn how selective breeding works
- See why some traits are rare and others are common
- Understand the importance of responsible breeding practices
- Apply genetics lessons from biology class to real-world scenarios

## How the Simulation Works

### The Basics

**Creatures**: Each creature in our simulation has genes that determine 15 different traits. Just like you might have genes for brown eyes or blue eyes, our creatures have genes for things like:
- **Desirable traits**: Emerald Eyes, Silky Coat, Long Tail
- **Undesirable traits**: Cloudy Eyes, Matted Fur, Stubby Tail, and others

**Genetics Rules**: We follow the same genetics you learn in biology:
- Each creature has TWO copies of each gene (one from mom, one from dad)
- Some traits are **dominant** (only need one copy to show)
- Some traits are **recessive** (need two copies to show)
- Offspring randomly inherit one gene from each parent

**Example**: 
- Emerald Eyes is dominant (E)
- Regular eyes is recessive (e)
- A creature with Ee or EE will have emerald eyes
- A creature with ee will have regular eyes

### How Breeders Choose Mates

This is the heart of our experiment. We programmed two different types of breeders:

#### Kennel Club Breeders (Selective Breeding)
Kennels are careful and selective. Here's their step-by-step decision process:

1. **Look for desirable traits**: They prefer creatures with Emerald Eyes, Silky Coat, or Long Tail
2. **Check the genes closely**: They prefer creatures with "better" genotypes
   - For dominant desirable traits: They prefer EE over Ee (breeding two EE parents means ALL babies have the trait)
   - For recessive desirable traits: They prefer creatures that already show the trait (like silky coat)
3. **Prevent genetic problems**: They follow strict rules - never breed pairs that would produce genetically disadvantaged offspring (blind, high mortality risk, etc.)
4. **Avoid close relatives**: They won't breed parents with children or siblings together
5. **Breed fewer animals**: Each kennel only breeds 4-6 pairs per year
6. **Keep promising offspring**: They keep some babies to become future breeding animals

**Why this matters**: By being selective, kennels slowly increase the frequency of good traits in the population.

#### Mill Breeders (Volume Breeding)
Mills focus on quantity over quality. Here's how they operate:

1. **Breed as many as possible**: Each mill breeds 15-20 pairs per year
2. **Evaluate breed standards and aesthetics**: They check for basic appearance traits but not genotypes (underlying genes)
3. **Willing to breed relatives**: They don't check if animals are related
4. **Don't keep offspring long**: Babies are removed quickly to make room for more breeding
5. **Focus on any creature that can breed**: As long as it's old enough and healthy, it can breed

**Why this matters**: Mills produce more offspring but don't guide the population toward better genetic quality.

## Our Experiments: Runs 5 and 6

We conducted two experimental runs that differ only in **duration**:

- **Run 5**: 6 years - [Configuration](run5/run5_config.yaml) | [Results](run5/combined/)
- **Run 6**: 20 years - [Configuration](run6/run6_config.yaml) | [Results](run6/combined/)

**All other parameters are identical:**
- **Population**: 200 creatures
- **Total Breeders**: 20
- **Comparison**: Two scenarios tested side-by-side
  - **Scenario A**: 19 kennels + 1 mill (95% selective breeding)
  - **Scenario B**: 1 kennel + 19 mills (95% volume breeding)
- **Replications**: 15 simulations per scenario (30 total per run, 60 total overall)
- **Traits**: 3 desirable (Emerald Eyes, Silky Coat, Long Tail) + 12 undesirable

**Why 19:1 instead of 20:0?** When we tested 20 mills with 0 kennels, populations became unstable and often went extinct. Using 19:1 keeps the experiments symmetrical (both scenarios have the same total of 20 breeders) and allows both to complete successfully.

## What We Discovered

### Key Findings

1. **Kennel breeding increases desirable traits**: In populations with mostly kennels, desirable traits like Emerald Eyes increased from 25% to over 60% in just 20 years.

2. **Mill breeding struggles to improve traits**: In mill-dominated populations, trait frequencies stayed mostly random. Sometimes desirable traits even decreased.

3. **Recessive traits are fragile**: Recessive desirable traits (like Silky Coat) can disappear completely in mill populations but thrive under kennel breeding.

4. **Time matters**: The longer the simulation runs, the bigger the difference between kennels and mills.

5. **Population stability**: Mill populations sometimes declined dangerously or even went extinct because they weren't managing breeding carefully.

### The Science Behind It

Our results follow the principles of **Hardy-Weinberg equilibrium** and **Mendelian genetics**:
- Without selection (like in mills), trait frequencies stay roughly constant
- With selection (like in kennels), favored traits increase over time
- This matches what scientists observe in real animal breeding programs

## FAQ: Questions Science Fair Judges Might Ask

### About the Project

**Q: How did you make sure your results were accurate and not just random?**

A: We used several scientific methods:
- Ran each experiment 15 times with different random seeds to see if results were consistent
- Used the same genetic rules (Mendelian inheritance) that biologists use
- Compared short-term (6 years) and long-term (20 years) results to verify trends hold over time
- Tracked thousands of creatures across multiple generations to get statistically meaningful data

**Q: Why did you use a computer simulation instead of real animals?**

A: Several important reasons:
- **Ethics**: We can't experiment on real animals just for a project
- **Time**: Breeding real animals takes years; our simulation can test 20 generations in minutes
- **Control**: We can control exactly what variables change and what stays the same
- **Repeatability**: We can run the exact same experiment multiple times
- **Scale**: We track 200 creatures and 15 traits simultaneously, which would be impossible with real animals
- **Availability**: Real puppy mills don't exactly advertise—they're often hidden operations

**Q: How do you know your simulation matches real genetics?**

A: Our simulation follows the laws of Mendelian genetics:
- Each parent contributes one allele (gene version) to offspring
- Dominant and recessive traits work exactly like in real genetics (BB, Bb show dominant; bb shows recessive)
- We verified that trait ratios match expected Mendelian ratios (3:1 for simple dominant traits, etc.)
- The Hardy-Weinberg equilibrium principle predicts our results in the mill populations (random mating = stable frequencies)

### About the Breeding Strategies

**Q: In real life, are kennels always better than mills?**

A: For genetic health and trait quality, yes. Responsible kennels:
- Reduce genetic diseases through careful mate selection
- Improve breed characteristics over time
- Maintain genetic diversity by avoiding inbreeding
- Produce healthier animals

Puppy mills prioritize profit over animal welfare and genetic health, which is why they're widely criticized by veterinarians and animal welfare organizations.

**Q: What's the biggest difference in HOW kennels and mills choose which animals to breed?**

A: The key difference is **selection criteria**. Kennels use a multi-step evaluation:
1. Does this animal have desirable physical traits?
2. Does it have good genes (genotype) for those traits?
3. Will this pairing produce genetically healthy offspring? (no genetic defects, blindness, or high mortality risk)
4. Is it related to the potential mate? (avoid inbreeding)
5. Will the offspring likely have better traits than the current population?

Mills evaluate breed standards and aesthetics but don't check genotypes (the underlying genes). They mainly ask: "Is this animal old enough to breed and does it look right?"

**Q: Why did you choose 19 kennels vs 1 mill instead of 20 vs 0?**

A: We tested different ratios and found that 20 mills with 0 kennels led to unstable populations that often went extinct. We chose 19:1 because:
- It keeps the experiments symmetrical (both scenarios have 20 total breeders)
- It lets us see what happens in a *mostly* selective environment with a small amount of volume breeding
- It's more realistic—even in carefully managed populations, some less-selective breeding occurs

### About the Results

**Q: Were you surprised by any of your results?**

A: Yes! We were surprised by:
- **How fast recessive traits can disappear**: Even with 20% starting frequency, recessive desirable traits vanished in some mill runs within 10 years
- **How stable kennel populations were**: We expected more variation, but kennels consistently improved traits across all 15 runs
- **The extinction risk in mills**: Some mill-dominated populations declined to dangerously low numbers (under 50 creatures)

**Q: If kennels are so much better, why do puppy mills exist?**

A: Puppy mills exist because they're profitable in the short term:
- They produce many more puppies per year (15-20 litters vs 4-6 for kennels)
- They don't spend time on careful selection or genetic testing
- They don't keep offspring for evaluation

However, our simulation shows the long-term cost: declining genetic quality and potential population problems.

**Q: Could your findings apply to other situations besides dog breeding?**

A: Absolutely! The same principles apply to:
- **Conservation biology**: Managing endangered species in zoos
- **Agriculture**: Breeding crops and livestock for desirable traits
- **Evolution**: How natural selection changes wild populations
- **Human genetics**: Understanding genetic diseases and inheritance patterns

### About the Science

**Q: What's Hardy-Weinberg equilibrium and why does it matter?**

A: Hardy-Weinberg equilibrium is a principle in genetics that says: **If mating is totally random and there's no selection, mutation, or migration, trait frequencies stay constant.**

In our mill populations (random mating, no selection), we see this principle in action—trait frequencies barely change. In kennel populations (strong selection), frequencies change a lot because we're violating the "no selection" assumption. This proves our simulation follows real genetic principles!

**Q: What variables did you control in your experiment?**

A: We kept these the same across all simulations:
- Starting population (200 creatures)
- Initial trait frequencies (same for all traits)
- Total number of breeders (20)
- Creature lifespan and breeding ages
- Genetic rules (Mendelian inheritance)

We only changed:
- The ratio of kennels to mills (19:1 vs 1:19)
- The random seed (to test reproducibility)

**Q: How many creatures did you track in total?**

A: Across both experimental runs (short-term and long-term, both scenarios, all 60 simulations), we tracked over **100,000 individual creatures** across multiple generations! Each creature's genes, traits, parents, and offspring were recorded.

**Q: What would happen if you ran it for 100 years instead of 20?**

A: Based on our trends:
- **Kennel populations**: Desirable traits would likely reach 90-95% frequency and stabilize
- **Mill populations**: Trait frequencies might drift randomly; some traits could become fixed (100%) or lost (0%) purely by chance
- **Genetic diversity**: Mills might lose genetic diversity (fewer different genes available), making the population vulnerable


## Questions?

For more detailed information, check the `docs/` folder:
- `requirements.md`: Full project requirements and specifications
- `domain-model.md`: How the simulation code is organized
- `BATCH_ANALYSIS_DOCUMENTATION.md`: How to analyze and visualize results


- **Run 5**: 6 years - [Configuration](run5/run5_config.yaml) | [Results](run5/combined/)
- **Run 6**: 20 years - [Configuration](run6/run6_config.yaml) | [Results](run6/combined/)
