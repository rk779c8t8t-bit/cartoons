#!/usr/bin/env bash
# Скачивает бесплатные модели распознавания речи (sherpa-onnx, GitHub releases) в ./models
set -e; cd "$(dirname "$0")/.."; mkdir -p models; cd models
U=https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models
for n in sherpa-onnx-whisper-turbo sherpa-onnx-nemo-ctc-giga-am-v2-russian-2025-04-19 sherpa-onnx-nemo-transducer-giga-am-v2-russian-2025-04-19; do
  [ -d "$n" ] || curl -sSL "$U/$n.tar.bz2" | tar xj
done
