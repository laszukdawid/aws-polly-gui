#!/usr/bin/python
# coding: UTF-8
import json
import logging
from PyQt5.QtMultimedia import QMediaPlayer

from aws_polly_gui.configuration import Configuration
from aws_polly_gui.cracker_gui import MainWindow
from aws_polly_gui.text_parser import TextParser
from aws_polly_gui.speaker.espeak import Espeak
from aws_polly_gui.speaker.polly import Polly


class Cracker(object):
    """Logic for running the Cracker program"""

    SPEAKER = {Polly.__name__: Polly, Espeak.__name__: Espeak}
    _logger = logging.getLogger(__name__)

    def __init__(self):
        super().__init__()

        self.config = Configuration()
        _ = self.config.read_default_config()

        self.player = QMediaPlayer()
        self.speaker = self.get_speaker(self.config.speaker, self.player)
        self.textParser = TextParser(config_path=self.config.parser_config)

        self.gui = MainWindow(self.config, speakers=self.SPEAKER)
        self.gui.speaker = self.speaker
        self.gui.player = self.player

        self._last_pid = None

    def get_speaker(self, speaker_name, player):
        if speaker_name == Polly.__name__:
            if "profile_name" in self.config.default_values:
                profile_name = self.config.default_values['profile_name']
                return Polly(player, profile_name)
            else:
                return Polly(player)
        elif speaker_name == Espeak.__name__:
            return Espeak(player)

    def run(self):
        self.gui.init()
        self.set_action()
        self.gui.show()

    def reduce_text(self):
        text = self.gui.textEdit.toPlainText()
        new_text = self.textParser.reduce_text(text)
        self.gui.textEdit.setText(new_text)

    def reduce_cite(self):
        text = self.gui.textEdit.toPlainText()
        new_text = self.textParser.reduce_cite(text)
        self.gui.textEdit.setText(new_text)

    def wiki_text(self):
        """Sets the text box with wikipedia specific cleaned text.
        Example of this is removing `citation needed` and other references.
        """
        text = self.gui.textEdit.toPlainText()
        text = self.textParser.wiki_text(text)
        self.gui.textEdit.setText(text)

    def read_text(self):
        """Reads out text in the text_box with selected speaker."""
        self.stop_text()
        text = self.gui.textEdit.toPlainText()  # TODO: toHtml() gives more control

        self.textParser.parser_rules = self.config.regex_config
        text = self.textParser.reduce_text(text)

        speaker_config = self._prepare_config()
        self._last_pid = self.speaker.read_text(text, **speaker_config)

    def toggle_read(self):
        if self.player.state() == QMediaPlayer.PausedState:
            self.player.play()
        else:
            self.player.pause()

    def stop_text(self):
        self.speaker.stop_text()

    def _prepare_config(self):
        config = dict(rate=self.gui.rate, volume=self.gui.volume, voice=self.gui.config.voice)
        return config

    def change_speaker(self, speaker_name):
        """Action on changing speaker.

        Important: Each speaker has its own configuration. These values should be updated on change."""
        self.speaker = self.SPEAKER[speaker_name](self.player)
        self.gui.change_speaker(speaker_name)

    def set_action(self):
        self.gui.stop_action.triggered.connect(self.stop_text)
        self.gui.read_action.triggered.connect(self.read_text)
        self.gui.toggle_action.triggered.connect(self.toggle_read)
        self.gui.reduce_action.triggered.connect(self.reduce_text)
        self.gui.wiki_action.triggered.connect(self.wiki_text)
        self.gui.speakerW.currentTextChanged.connect(self.change_speaker)
