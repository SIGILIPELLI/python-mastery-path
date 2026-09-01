class Question {
  final String question;
  final List<String> options;
  final int answerIndex;
  final String explanation;

  Question({
    required this.question,
    required this.options,
    required this.answerIndex,
    required this.explanation,
  });

  factory Question.fromJson(Map<String, dynamic> json) => Question(
        question: json['question'] as String,
        options: List<String>.from(json['options'] as List),
        answerIndex: json['answerIndex'] as int,
        explanation: json['explanation'] as String? ?? '',
      );
}

class Lesson {
  final String id;
  final String title;
  final String description;
  final String video;

  /// Whether the rendered .mp4 is currently hosted. The video pipeline prunes
  /// `output/renders/` once a video is uploaded to YouTube, so a lesson can
  /// exist in the catalog with no playable video behind it.
  final bool videoAvailable;

  final String sourceUrl;
  final List<Question> questions;

  Lesson({
    required this.id,
    required this.title,
    required this.description,
    required this.video,
    required this.videoAvailable,
    required this.sourceUrl,
    required this.questions,
  });

  factory Lesson.fromJson(Map<String, dynamic> json) => Lesson(
        id: json['id'] as String,
        title: json['title'] as String,
        description: json['description'] as String? ?? '',
        video: json['video'] as String,
        videoAvailable: json['videoAvailable'] as bool? ?? false,
        sourceUrl: json['sourceUrl'] as String? ?? '',
        questions: (json['questions'] as List)
            .map((q) => Question.fromJson(q as Map<String, dynamic>))
            .toList(),
      );
}

class LanguageTrack {
  final String id;
  final String name;
  final String status; // "available" | "coming_soon"
  final List<Lesson> lessons;

  LanguageTrack({
    required this.id,
    required this.name,
    required this.status,
    required this.lessons,
  });

  bool get isAvailable => status == 'available';

  factory LanguageTrack.fromJson(Map<String, dynamic> json) => LanguageTrack(
        id: json['id'] as String,
        name: json['name'] as String,
        status: json['status'] as String,
        lessons: (json['lessons'] as List)
            .map((l) => Lesson.fromJson(l as Map<String, dynamic>))
            .toList(),
      );
}

class ContentManifest {
  final List<LanguageTrack> languages;

  ContentManifest({required this.languages});

  factory ContentManifest.fromJson(Map<String, dynamic> json) =>
      ContentManifest(
        languages: (json['languages'] as List)
            .map((l) => LanguageTrack.fromJson(l as Map<String, dynamic>))
            .toList(),
      );
}
