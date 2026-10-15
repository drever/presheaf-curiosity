cd /home/claude/presheaf-curiosity/src
for s in "$@"; do
 for n in 60 150; do setsid nohup /home/claude/venv/bin/python e31.py $s $n d2 > ../results/e31_log_d2_${s}_${n}.txt 2>&1 & done
done
