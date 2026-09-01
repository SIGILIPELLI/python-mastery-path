import 'package:flutter/material.dart';
import 'screens/language_picker_screen.dart';

void main() {
  runApp(const QuizAcademyApp());
}

class QuizAcademyApp extends StatelessWidget {
  const QuizAcademyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Quiz Academy',
      theme: ThemeData(colorScheme: ColorScheme.fromSeed(seedColor: Colors.indigo)),
      home: const LanguagePickerScreen(),
    );
  }
}
