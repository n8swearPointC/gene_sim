import tempfile
import yaml
import sqlite3
from pathlib import Path
from gene_sim.simulation import Simulation

# Load config
with open('quick_test_config.yaml', 'r') as f:
    config = yaml.safe_load(f)

config['years'] = 2

# Save to temp
f = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
yaml.dump(config, f)
f.close()
config_path = f.name

# Create temp db
db_f = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
db_f.close()
db_path = db_f.name

print(f"Config: {config_path}")
print(f"DB: {db_path}")

# Run sim
sim = Simulation(config_path, db_path=db_path)
sim.run()

# Check tables
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
tables = [r[0] for r in cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
print(f"Tables: {tables}")
conn.close()

# Clean up
Path(config_path).unlink()
Path(db_path).unlink()
