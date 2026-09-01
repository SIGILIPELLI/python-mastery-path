import 'dart:convert';
import 'package:flutter/services.dart' show rootBundle;
import 'models.dart';

/// Base URL the rendered lesson videos are served from.
///
/// 10.0.2.2 is the Android emulator's alias for the host machine's
/// localhost, matching the local dev server started for `video-studio/output/renders`.
/// Swap this for a real hosted URL once the videos are published publicly.
const String videoBaseUrl = 'http://10.0.2.2:8000';

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
