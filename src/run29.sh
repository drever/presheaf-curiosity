#!/bin/bash
cd /home/claude/presheaf-curiosity/src
if [ "$1" = "syn" ]; then
for s in $2; do for fh in 0.0 0.3 0.6; do for cfg in "0.0 0.0" "0.05 0.0" "0.1 0.0" "0.0 0.05"; do
 /home/claude/venv/bin/python e29.py syn $s $cfg $fh >> ../results/e29_log_syn.txt 2>&1
done; done; done
else
for s in $2; do /home/claude/venv/bin/python e29.py $1 $s >> ../results/e29_log_$1.txt 2>&1; done
fi
