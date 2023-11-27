for i in {1..4}; do
  bash scripts/generate_report.sh "transcode_basic_${i}" conf/experiments/blockchain/transcode_basic.ini
  bash scripts/generate_report.sh "transcode_greedy_${i}" conf/experiments/blockchain/transcode_greedy.ini
  bash scripts/generate_report.sh "transcode_4fold_${i}" conf/experiments/blockchain/transcode_4fold.ini
done

