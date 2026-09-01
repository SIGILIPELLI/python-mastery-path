import 'package:flutter/material.dart';
import 'package:video_player/video_player.dart';
import '../content_repository.dart';
import '../models.dart';

class LessonScreen extends StatefulWidget {
  final Lesson lesson;

  const LessonScreen({super.key, required this.lesson});

  @override
  State<LessonScreen> createState() => _LessonScreenState();
}

class _LessonScreenState extends State<LessonScreen> {
  final _repo = ContentRepository();
  VideoPlayerController? _controller;
  String? _videoError;

  @override
  void initState() {
    super.initState();
    if (widget.lesson.videoAvailable) _initVideo();
  }

  void _initVideo() {
    final url = _repo.videoUrlFor(widget.lesson);
    final controller = VideoPlayerController.networkUrl(Uri.parse(url));
    controller.initialize().then((_) {
      if (mounted) setState(() {});
    }).catchError((e) {
      if (mounted) setState(() => _videoError = e.toString());
    });
    _controller = controller;
  }

  @override
  void dispose() {
    _controller?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final lesson = widget.lesson;
    return Scaffold(
      appBar: AppBar(title: Text(lesson.title)),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _VideoCard(
            controller: _controller,
            error: _videoError,
            unavailable: !lesson.videoAvailable,
            onRetry: () {
              setState(() {
                _videoError = null;
                _controller?.dispose();
                _initVideo();
              });
            },
          ),
          const SizedBox(height: 16),
          if (lesson.description.isNotEmpty) ...[
            Text(lesson.description, style: Theme.of(context).textTheme.bodyMedium),
            const SizedBox(height: 20),
          ],
          Text(
            'Test yourself',
            style: Theme.of(context).textTheme.titleLarge,
          ),
          const SizedBox(height: 4),
          Text(
            "Answer now if you're confident, or watch the video above first — you can replay it anytime.",
            style: Theme.of(context).textTheme.bodySmall,
          ),
          const SizedBox(height: 12),
          for (var i = 0; i < lesson.questions.length; i++)
            _QuestionCard(index: i, question: lesson.questions[i]),
        ],
      ),
    );
  }
}

class _VideoCard extends StatelessWidget {
  final VideoPlayerController? controller;
  final String? error;
  final bool unavailable;
  final VoidCallback onRetry;

  const _VideoCard({
    required this.controller,
    required this.error,
    required this.unavailable,
    required this.onRetry,
  });

  @override
  Widget build(BuildContext context) {
    return AspectRatio(
      aspectRatio: 16 / 9,
      child: ClipRRect(
        borderRadius: BorderRadius.circular(12),
        child: Container(
          color: Colors.black,
          child: _buildContent(context),
        ),
      ),
    );
  }

  Widget _buildContent(BuildContext context) {
    if (unavailable) {
      return const Center(
        child: Padding(
          padding: EdgeInsets.symmetric(horizontal: 24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(Icons.videocam_off_outlined, color: Colors.white70, size: 32),
              SizedBox(height: 8),
              Text(
                'Video not available offline yet.\nYou can still take the quiz below.',
                style: TextStyle(color: Colors.white70),
                textAlign: TextAlign.center,
              ),
            ],
          ),
        ),
      );
    }
    if (error != null) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.error_outline, color: Colors.white70, size: 32),
            const SizedBox(height: 8),
            const Padding(
              padding: EdgeInsets.symmetric(horizontal: 16),
              child: Text(
                "Couldn't load video. You can still answer the questions below.",
                style: TextStyle(color: Colors.white70),
                textAlign: TextAlign.center,
              ),
            ),
            TextButton(onPressed: onRetry, child: const Text('Retry')),
          ],
        ),
      );
    }
    final c = controller;
    if (c == null || !c.value.isInitialized) {
      return const Center(child: CircularProgressIndicator());
    }
    return Stack(
      alignment: Alignment.bottomCenter,
      children: [
        GestureDetector(
          onTap: () {
            c.value.isPlaying ? c.pause() : c.play();
          },
          child: Center(
            child: AspectRatio(
              aspectRatio: c.value.aspectRatio,
              child: VideoPlayer(c),
            ),
          ),
        ),
        _PlayPauseOverlay(controller: c),
        VideoProgressIndicator(c, allowScrubbing: true),
      ],
    );
  }
}

class _PlayPauseOverlay extends StatefulWidget {
  final VideoPlayerController controller;

  const _PlayPauseOverlay({required this.controller});

  @override
  State<_PlayPauseOverlay> createState() => _PlayPauseOverlayState();
}

class _PlayPauseOverlayState extends State<_PlayPauseOverlay> {
  @override
  void initState() {
    super.initState();
    widget.controller.addListener(_onChange);
  }

  void _onChange() {
    if (mounted) setState(() {});
  }

  @override
  void dispose() {
    widget.controller.removeListener(_onChange);
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final playing = widget.controller.value.isPlaying;
    return IgnorePointer(
      child: AnimatedOpacity(
        opacity: playing ? 0 : 1,
        duration: const Duration(milliseconds: 200),
        child: const Icon(Icons.play_circle_fill, color: Colors.white70, size: 56),
      ),
    );
  }
}

class _QuestionCard extends StatefulWidget {
  final int index;
  final Question question;

  const _QuestionCard({required this.index, required this.question});

  @override
  State<_QuestionCard> createState() => _QuestionCardState();
}

class _QuestionCardState extends State<_QuestionCard> {
  int? _selected;

  @override
  Widget build(BuildContext context) {
    final q = widget.question;
    final answered = _selected != null;
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Q${widget.index + 1}. ${q.question}',
              style: const TextStyle(fontWeight: FontWeight.w600),
            ),
            const SizedBox(height: 10),
            for (var i = 0; i < q.options.length; i++)
              _OptionTile(
                text: q.options[i],
                state: !answered
                    ? _OptionState.neutral
                    : i == q.answerIndex
                        ? _OptionState.correct
                        : i == _selected
                            ? _OptionState.wrong
                            : _OptionState.disabled,
                onTap: answered ? null : () => setState(() => _selected = i),
              ),
            if (answered) ...[
              const SizedBox(height: 8),
              Row(
                children: [
                  Icon(
                    _selected == q.answerIndex ? Icons.check_circle : Icons.cancel,
                    color: _selected == q.answerIndex ? Colors.green : Colors.red,
                    size: 18,
                  ),
                  const SizedBox(width: 6),
                  Text(
                    _selected == q.answerIndex ? 'Correct' : 'Not quite',
                    style: TextStyle(
                      fontWeight: FontWeight.w600,
                      color: _selected == q.answerIndex ? Colors.green : Colors.red,
                    ),
                  ),
                ],
              ),
              if (q.explanation.isNotEmpty) ...[
                const SizedBox(height: 4),
                Text(q.explanation, style: Theme.of(context).textTheme.bodySmall),
              ],
              Align(
                alignment: Alignment.centerRight,
                child: TextButton(
                  onPressed: () => setState(() => _selected = null),
                  child: const Text('Try again'),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

enum _OptionState { neutral, correct, wrong, disabled }

class _OptionTile extends StatelessWidget {
  final String text;
  final _OptionState state;
  final VoidCallback? onTap;

  const _OptionTile({required this.text, required this.state, required this.onTap});

  @override
  Widget build(BuildContext context) {
    Color? bg;
    Color? border = Theme.of(context).dividerColor;
    switch (state) {
      case _OptionState.neutral:
        break;
      case _OptionState.correct:
        bg = Colors.green.withValues(alpha: 0.15);
        border = Colors.green;
        break;
      case _OptionState.wrong:
        bg = Colors.red.withValues(alpha: 0.15);
        border = Colors.red;
        break;
      case _OptionState.disabled:
        break;
    }
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(8),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
          decoration: BoxDecoration(
            color: bg,
            border: Border.all(color: border),
            borderRadius: BorderRadius.circular(8),
          ),
          child: Text(text),
        ),
      ),
    );
  }
}
