#!/bin/bash
cd /home/claude/presheaf-curiosity/src
export KD=80 ROUNDS=2
if [ "$1" = "syn6" ]; then for s in $2; do NTR=120 NGAD=6 /home/claude/venv/bin/python e30.py syn $s >> ../results/e30_log_syn6.txt 2>&1; done
elif [ "$1" = "syn1" ]; then for s in $2; do NTR=120 NGAD=1 /home/claude/venv/bin/python e30.py syn $s >> ../results/e30_log_syn1.txt 2>&1; done
else for s in $2; do KD=40 /home/claude/venv/bin/python e30.py $1 $s >> ../results/e30_log_$1.txt 2>&1; done; fi
