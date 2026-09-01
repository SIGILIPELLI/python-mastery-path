import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:quiz_academy/models.dart';
import 'package:quiz_academy/screens/lesson_list_screen.dart';
import 'package:quiz_academy/screens/lesson_screen.dart';

Question _question({int answerIndex = 1}) => Question(
      question: 'Which keyword exits a loop entirely?',
      options: const ['continue', 'break', 'return', 'exit'],
      answerIndex: answerIndex,
      explanation: 'break exits the loop; continue only skips an iteration.',
    );

Lesson _lesson({bool videoAvailable = false, List<Question>? questions}) => Lesson(
      id: 'c-level-1-03-control-flow-short',
      title: "C's switch Fallthrough",
      description: 'A short lesson.',
      video: 'c-level-1-03-control-flow-short.mp4',
      videoAvailable: videoAvailable,
      sourceUrl: 'https://example.invalid/lesson/',
      questions: questions ?? [_question()],
    );

Future<void> _tapOption(WidgetTester tester, String label) async {
  await tester.tap(find.text(label));
  await tester.pump();
}

/// The quiz sits below the video in a ListView. The default 800x600 test
/// viewport clips it, so give these tests a tall surface and let the whole
/// lesson lay out at once.
void _useTallViewport(WidgetTester tester) {
  tester.view.physicalSize = const Size(1000, 3000);
  tester.view.devicePixelRatio = 1.0;
  addTearDown(tester.view.reset);
}

void main() {
  group('manifest parsing', () {
    test('defaults videoAvailable to false when the field is absent', () {
      final lesson = Lesson.fromJson({
        'id': 'x',
        'title': 'X',
        'video': 'x.mp4',
        'questions': <dynamic>[],
      });
      expect(lesson.videoAvailable, isFalse);
    });

    test('parses a full language track', () {
      final track = LanguageTrack.fromJson({
        'id': 'c',
        'name': 'C',
        'status': 'available',
        'lessons': [
          {
            'id': 'c-1',
            'title': 'Lesson',
            'description': 'd',
            'video': 'c-1.mp4',
            'videoAvailable': true,
            'sourceUrl': 'u',
            'questions': [
              {
                'question': 'q',
                'options': ['a', 'b', 'c', 'd'],
                'answerIndex': 2,
                'explanation': 'e',
              }
            ],
          }
        ],
      });
      expect(track.isAvailable, isTrue);
      expect(track.lessons.single.questions.single.answerIndex, 2);
      expect(track.lessons.single.videoAvailable, isTrue);
    });

    test('coming_soon tracks are not available', () {
      final track = LanguageTrack.fromJson({
        'id': 'rust',
        'name': 'Rust',
        'status': 'coming_soon',
        'lessons': <dynamic>[],
      });
      expect(track.isAvailable, isFalse);
    });
  });

  group('lesson list', () {
    testWidgets('labels lessons that have no hosted video', (tester) async {
      await tester.pumpWidget(MaterialApp(
        home: LessonListScreen(
          language: LanguageTrack(
            id: 'c',
            name: 'C',
            status: 'available',
            lessons: [_lesson(videoAvailable: false)],
          ),
        ),
      ));
      expect(find.textContaining('No video yet'), findsOneWidget);
      expect(find.textContaining('1 questions'), findsOneWidget);
    });
  });

  group('quiz flow', () {
    testWidgets('a learner can answer without playing the video', (tester) async {
      _useTallViewport(tester);
      await tester.pumpWidget(MaterialApp(home: LessonScreen(lesson: _lesson())));
      await tester.pumpAndSettle();

      // Video is unavailable, but the quiz is still usable.
      expect(find.textContaining('You can still take the quiz'), findsOneWidget);

      await _tapOption(tester, 'break');

      expect(find.text('Correct'), findsOneWidget);
      expect(find.textContaining('break exits the loop'), findsOneWidget);
    });

    testWidgets('a wrong answer reveals the correct one and can be retried',
        (tester) async {
      _useTallViewport(tester);
      await tester.pumpWidget(MaterialApp(home: LessonScreen(lesson: _lesson())));
      await tester.pumpAndSettle();

      await _tapOption(tester, 'continue');
      expect(find.text('Not quite'), findsOneWidget);

      await _tapOption(tester, 'Try again');
      expect(find.text('Not quite'), findsNothing);

      await _tapOption(tester, 'break');
      expect(find.text('Correct'), findsOneWidget);
    });
  });
}
