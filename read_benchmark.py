from pathlib import Path

import yaml

from params.Params import Params


root = Path(__file__).resolve().parent

# Params initializes all defaults from params/params.json, then applies the
# values provided by config.json.
params = Params()
params.load(root / "configs/config.json")

# Resolve relative benchmark paths from the repository root.
benchmark_path = Path(params.yaml_input[0])
if not benchmark_path.is_absolute():
    benchmark_path = root / benchmark_path

# FullLoader is required because the benchmark contains !!python/tuple values.
with benchmark_path.open() as stream:
    benchmark = yaml.load(stream, Loader=yaml.FullLoader)

settings = benchmark["settings"]
print(f"Design: {settings['design']}")
print(f"Instances: {len(benchmark['instances'])}")
print(f"Nets: {len(benchmark['nets'])}")
print(f"Die area: {settings['die_area']}")
