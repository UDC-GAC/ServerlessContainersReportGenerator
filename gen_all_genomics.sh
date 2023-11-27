for i in {1..4}; do
  bash scripts/generate_report.sh "genomics_greedy_${i}" conf/experiments/blockchain/genomics_greedy.ini
  bash scripts/generate_report.sh "genomics_conservative_${i}" conf/experiments/blockchain/genomics_conservative.ini
  bash scripts/generate_report.sh "genomics_4fold_${i}" conf/experiments/blockchain/genomics_4fold.ini
done

