#!/bin/bash
# Fetch the public data sets used by the experiments into ./data (override with DATA_DIR).
# We do not redistribute any of them; check each repository's licence before reuse.
set -e
DATA="${DATA_DIR:-$(cd "$(dirname "$0")/.." && pwd)/data}"
mkdir -p "$DATA"; cd "$DATA"
# ISCAS-85 benchmark netlists (c6288 = 16x16 array multiplier)
[ -d hdl-benchmarks ] || git clone --depth 1 https://github.com/ispras/hdl-benchmarks
# EPFL combinational benchmarks (arithmetic/*.blif); only used for a negative check
[ -d benchmarks ] || git clone --depth 1 https://github.com/lsils/benchmarks
# OSM street networks of Spanish provincial capitals (street-type experiments)
[ -d spain-cities-geojson ] || git clone --depth 1 https://github.com/amoraschi/spain-cities-geojson
echo "data in $DATA"
