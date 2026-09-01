import 'package:flutter/material.dart';
import '../models.dart';
import 'lesson_screen.dart';

class LessonListScreen extends StatelessWidget {
  final LanguageTrack language;

  const LessonListScreen({super.key, required this.language});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(language.name)),
      body: ListView.separated(
        padding: const EdgeInsets.all(12),
        itemCount: language.lessons.length,
        separatorBuilder: (_, _) => const SizedBox(height: 8),
        itemBuilder: (context, i) {
          final lesson = language.lessons[i];
          final bits = [
            lesson.videoAvailable ? 'Video' : 'No video yet',
            '${lesson.questions.length} questions',
          ];
          return Card(
            child: ListTile(
              leading: CircleAvatar(
                child: Icon(
                  lesson.videoAvailable ? Icons.play_arrow : Icons.quiz_outlined,
                ),
              ),
              title: Text(lesson.title),
              subtitle: Text(bits.join(' · ')),
              trailing: const Icon(Icons.chevron_right),
              onTap: () {
                Navigator.of(context).push(MaterialPageRoute(
                  builder: (_) => LessonScreen(lesson: lesson),
                ));
              },
            ),
          );
        },
      ),
    );
  }
}
