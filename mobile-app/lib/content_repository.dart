import 'dart:convert';
import 'package:flutter/foundation.dart' show defaultTargetPlatform, kIsWeb, TargetPlatform;
import 'package:flutter/services.dart' show rootBundle;
import 'models.dart';

/// Base URL the rendered lesson videos are served from.
///
/// Override at build/run time with
/// `--dart-define=VIDEO_BASE_URL=https://example.com/videos`.
/// Defaults to the local dev server serving `video-studio/output/renders`
/// (`python3 -m http.server 8000`); the Android emulator reaches the host
/// machine via 10.0.2.2, every other platform via localhost.
const String _videoBaseUrlOverride = String.fromEnvironment('VIDEO_BASE_URL');

String get videoBaseUrl {
  if (_videoBaseUrlOverride.isNotEmpty) return _videoBaseUrlOverride;
  final host = (!kIsWeb && defaultTargetPlatform == TargetPlatform.android)
      ? '10.0.2.2'
      : 'localhost';
  return 'http://$host:8000';
}

class ContentRepository {
  ContentManifest? _cached;

  Future<ContentManifest> load() async {
    if (_cached != null) return _cached!;
    final raw = await rootBundle.loadString('assets/content/manifest.json');
    final json = jsonDecode(raw) as Map<String, dynamic>;
    _cached = ContentManifest.fromJson(json);
    return _cached!;
  }

  String videoUrlFor(Lesson lesson) => '$videoBaseUrl/${lesson.video}';
}
