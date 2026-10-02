from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import main


class BonusTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.file = Path(self.temp.name) / 'state.json'
        self.state = patch.object(main, 'STATE_FILE', str(self.file))
        self.state.start()
        self.game = main.QuizGame()
        self.game.quizzes = [main.Quiz('시험 문제', ['가', '나', '다', '라'], 2, '두 번째')]

    def tearDown(self):
        self.state.stop()
        self.temp.cleanup()

    def test_repeated_hint_penalty_once_and_persistence(self):
        with patch('builtins.input', side_effect=['1', 'h', 'h', '2']), redirect_stdout(io.StringIO()):
            self.game.play()
        self.assertEqual(self.game.history[0]['score'], 50)
        with patch('builtins.input', side_effect=['1', '2']), redirect_stdout(io.StringIO()):
            self.game.play()
        restored = main.QuizGame()
        with redirect_stdout(io.StringIO()):
            restored.load()
        self.assertEqual([r['score'] for r in restored.history], [50, 100])
        self.assertEqual(restored.best_score, 100)
        self.assertEqual(restored.quizzes[0].hint, '두 번째')
        self.assertEqual(restored.history[0]['total'], 1)
        self.assertTrue(restored.history[0]['played_at'])

    def test_question_count_random_selection(self):
        self.game.quizzes = main.default_quizzes()
        with patch.object(main.random, 'sample', return_value=self.game.quizzes[:2]) as sampling, patch('builtins.input', side_effect=['2', '2', '3']), redirect_stdout(io.StringIO()):
            self.game.play()
        sampling.assert_called_once_with(self.game.quizzes, 2)
        self.assertEqual(self.game.history[0]['total'], 2)
        self.assertEqual(self.game.history[0]['score'], 100)

    def test_delete_saved_and_hint_roundtrip(self):
        with patch('builtins.input', side_effect=['1']), redirect_stdout(io.StringIO()):
            self.game.delete_quiz()
        data=json.loads(self.file.read_text())
        self.assertEqual(data['quizzes'], [])
        quiz = main.Quiz.from_dict(main.default_quizzes()[0].to_dict())
        self.assertTrue(quiz.hint)


if __name__ == '__main__':
    unittest.main()
