#!/usr/bin/env bash
# Build the Quiz Academy macOS app on a Mac (requires Flutter + Xcode).
# Usage: ./build_macos.sh   ->  QuizAcademy-macos.dmg in this folder
set -euo pipefail
cd "$(dirname "$0")"
command -v flutter >/dev/null || { echo "Install Flutter: https://docs.flutter.dev/get-started/install/macos"; exit 1; }
flutter config --enable-macos-desktop
flutter pub get
flutter build macos --release ${VIDEO_BASE_URL:+--dart-define=VIDEO_BASE_URL=$VIDEO_BASE_URL}
APP="build/macos/Build/Products/Release/quiz_academy.app"
hdiutil create -volname "Quiz Academy" -srcfolder "$APP" -ov -format UDZO QuizAcademy-macos.dmg
echo "Built: $PWD/QuizAcademy-macos.dmg  (and $APP)"
echo "Videos: run 'python3 -m http.server 8000' inside ../video-studio/output/renders"
