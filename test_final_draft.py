import asyncio
import tkinter as tk
import unittest
from unittest.mock import AsyncMock, patch

from draft_engine import draft_summary
from preview_ui import Preview
from vision import Image, match_name, read_image_async


class FinalDraftTests(unittest.TestCase):
    def test_finished_draft_with_missing_reads_is_not_an_open_slot(self):
        text = draft_summary(['Falstad', 'Stitches', 'Valeera'],
                             ['Leoric', "Gul'dan", 'Mei', 'Qhira', 'Brightwing'], final=True)
        self.assertIn('3/5 allies', text)
        self.assertIn('unread locked picks', text)
        self.assertNotIn('slot(s) left', text)
        self.assertNotIn('Still needed', text)

    def test_final_animation_does_not_turn_recognized_heroes_into_hovers(self):
        names = ['Falstad', 'Hogger', 'Li-Ming', 'Stitches', 'Valeera',
                 'Leoric', "Gul'dan", 'Mei', 'Qhira', 'Brightwing']
        # OCR has read the exact names; brightness changes during the countdown
        # must not make the reader treat a final pick as a hover.
        with patch('vision.ocr', new=AsyncMock(side_effect=['', 'MATCH STARTING'] + names)):
            result = asyncio.run(read_image_async(Image.new('RGB', (2048, 857), 'black')))
        self.assertTrue(result['valid'])
        self.assertEqual([s['hero'] for s in result['slots']], names)
        self.assertTrue(all(s['locked'] for s in result['slots']))
        self.assertEqual(result['bans'], [])

    def test_ribbon_fallback_keeps_exact_name_requirement(self):
        # The first card's full-card reads fail; its isolated ribbon succeeds.
        replies = ['', 'MATCH STARTING', 'noise', 'noise', 'noise', 'HOGGER']
        replies += ['Falstad', 'Li-Ming', 'Stitches', 'Valeera', 'Leoric',
                    "Gul'dan", 'Mei', 'Qhira', 'Brightwing']
        with patch('vision.ocr', new=AsyncMock(side_effect=replies)):
            result = asyncio.run(read_image_async(Image.new('RGB', (2048, 857), 'black')))
        self.assertEqual(result['slots'][0]['hero'], 'Hogger')
        self.assertIsNone(match_name('H0GGER', ['Hogger']))

    def test_partial_final_read_retains_confirmed_heroes_and_stops_draft_advice(self):
        root = tk.Tk(); root.withdraw()
        try:
            app = Preview(root); app.clear(); app.self_slot.set('1')
            app.allies[1].set('Hogger'); app.allies[2].set('Li-Ming')
            names = ['Falstad', None, None, 'Stitches', 'Valeera',
                     'Leoric', "Gul'dan", 'Mei', 'Qhira', 'Brightwing']
            frame = {'valid': True, 'phase': 'starting', 'map': None, 'bans': [],
                     'slots': [{'side': 'allies' if i < 5 else 'enemies', 'index': i % 5,
                                'hero': hero, 'locked': bool(hero)} for i, hero in enumerate(names)]}
            app.apply_read(frame, screenshot=True)
            self.assertEqual(app.allies[1].get(), 'Hogger')
            self.assertEqual(app.allies[2].get(), 'Li-Ming')
            self.assertIn('All 10 heroes recorded', app.status['text'])
            app.apply_read(frame, screenshot=True)
            self.assertIn('0 entries updated', app.live_status['text'])
            self.assertNotIn('expected bans', app.draft_warning['text'])
            # Reproduce the screenshot with two heroes never confirmed.
            app.allies[1].set(''); app.allies[2].set(''); app.refresh()
            self.assertIn('3/5 allies', app.status['text'])
            self.assertNotIn('Still needed', app.status['text'])
            self.assertIn('locked in HotS', app.draft_warning['text'])
            self.assertIn('Draft finished; no further bans', app.ban_text.get('1.0', 'end'))
            app.allies[0].set(''); app.refresh()
            self.assertNotIn('Fills the missing', app.pick_text.get('1.0', 'end'))
            self.assertIn('not been identified', app.pick_text.get('1.0', 'end'))
            self.assertEqual(app.build_name['text'], 'Your hero is unread')
            # A final observation must not leak into the next draft.
            app.clear()
            self.assertIn('slot(s) left', app.status['text'])
        finally:
            root.destroy()


if __name__ == '__main__':
    unittest.main()
