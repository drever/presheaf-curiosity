#!/bin/bash
# Synthesise the Quip benchmark circuits to gate-level Yosys JSON (data/quip_synth/NAME.json).
# Needs: pip install yowasp-yosys ; data/hdl-benchmarks from scripts/fetch_data.sh. Default `synth`, nothing tuned.
set -e
cd "$(dirname "$0")/../data/hdl-benchmarks/quip"; OUT=../../quip_synth; mkdir -p $OUT
for d in barrel16 barrel32 barrel64 mux8_64bit mux8_128bit mux32_16bit mux64_16bit oc_aes_core oc_des_area_opt oc_des_perf_opt; do
  files=$(grep -v des_test $d/fileorder.list | sed "s|^|$d/|" | tr '\n' ' ')
  yowasp-yosys -q -p "read_verilog $files; synth -flatten -top $d; write_json $OUT/$d.json"
done
