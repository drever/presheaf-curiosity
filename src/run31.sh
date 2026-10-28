cd "$(dirname "$0")"
for s in "$@"; do
 for n in 60 150; do setsid nohup python e31.py $s $n d2 > ../results/e31_log_d2_${s}_${n}.txt 2>&1 & done
done
