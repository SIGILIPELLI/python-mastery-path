import 'package:flutter/material.dart';
import '../content_repository.dart';
import '../models.dart';
import 'lesson_list_screen.dart';

class LanguagePickerScreen extends StatefulWidget {
  const LanguagePickerScreen({super.key});

  @override
  State<LanguagePickerScreen> createState() => _LanguagePickerScreenState();
}

class _LanguagePickerScreenState extends State<LanguagePickerScreen> {
  final _repo = ContentRepository();
  late Future<ContentManifest> _manifestFuture;

  @override
  void initState() {
    super.initState();
    _manifestFuture = _repo.load();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Quiz Academy')),
      body: FutureBuilder<ContentManifest>(
        future: _manifestFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) {
            return Center(child: Text('Failed to load content: ${snapshot.error}'));
          }
          final languages = snapshot.data!.languages;
          return Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Padding(
                padding: EdgeInsets.fromLTRB(16, 16, 16, 8),
                child: Text(
                  'Pick a language or track',
                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600),
                ),
              ),
              Expanded(
                child: GridView.builder(
                  padding: const EdgeInsets.all(16),
                  gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                    crossAxisCount: 2,
                    childAspectRatio: 2.4,
                    crossAxisSpacing: 12,
                    mainAxisSpacing: 12,
                  ),
                  itemCount: languages.length,
                  itemBuilder: (context, i) => _LanguageCard(language: languages[i]),
                ),
              ),
            ],
          );
        },
      ),
    );
  }
}

class _LanguageCard extends StatelessWidget {
  final LanguageTrack language;

  const _LanguageCard({required this.language});

  @override
  Widget build(BuildContext context) {
    final available = language.isAvailable;
    return Card(
      elevation: available ? 2 : 0,
      color: available ? null : Theme.of(context).colorScheme.surfaceContainerHighest,
      child: InkWell(
        onTap: available
            ? () {
                Navigator.of(context).push(MaterialPageRoute(
                  builder: (_) => LessonListScreen(language: language),
                ));
              }
            : null,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text(
                language.name,
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                  color: available ? null : Theme.of(context).disabledColor,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                available ? '${language.lessons.length} lessons' : 'Coming soon',
                style: TextStyle(
                  fontSize: 12,
                  color: available
                      ? Theme.of(context).colorScheme.primary
                      : Theme.of(context).disabledColor,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
