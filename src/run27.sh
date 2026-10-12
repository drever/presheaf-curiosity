#!/bin/bash
# $1 = Teilmenge der Seeds
cd /home/claude/presheaf-curiosity/src
for s in $1; do for fh in 0.0 0.3 0.6; do for cfg in "0.0 0.0" "0.05 0.0" "0.1 0.0" "0.0 0.05"; do
 /home/claude/venv/bin/python e27.py $s 40 $cfg $fh >> ../results/e27_log_$s.txt 2>&1
done; done; done
