import os
import time

import pytest

from agents.clipboard_watcher import ClipboardEventExtractor
from agents.command_logger import CommandLogger
from agents.ocr_agent import SENSITIVE_PLACEHOLDER, filter_sensitive_content


@pytest.mark.parametrize('text', [
    'password=hunter2',
    'API_KEY: abc123',
    'Authorization: Bearer abcdefghijklmnop',
    '-----BEGIN RSA PRIVATE KEY-----',
])
def test_credentials_are_filtered(text):
    assert filter_sensitive_content(text) == SENSITIVE_PLACEHOLDER


@pytest.mark.parametrize('text', ['pwd', 'my keyboard key is stuck', 'a secret recipe'])
def test_ordinary_text_is_kept(text):
    assert filter_sensitive_content(text) == text


@pytest.mark.parametrize('content, expected', [
    ('https://example.com', 'url'),
    ('import os', 'code'),
    ('git status', 'command'),
    ('hello there', 'text'),
])
def test_content_type(content, expected):
    assert ClipboardEventExtractor.get_content_type(content) == expected


def wait_for(condition, seconds=3):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline and not condition():
        time.sleep(0.02)
    return condition()


@pytest.fixture
def logger(tmp_path):
    bash = tmp_path / '.bash_history'
    zsh = tmp_path / '.zsh_history'
    bash.write_text('old\n')
    os.utime(bash, (1, 1))
    zsh.write_text(': 1700000000:0;old\n')
    command_logger = CommandLogger()
    command_logger.bash_history_file = str(bash)
    command_logger.zsh_history_file = str(zsh)
    yield command_logger, zsh
    command_logger.stop()


def append(path, *commands):
    with open(path, 'a') as history:
        for index, command in enumerate(commands):
            history.write(f': {1700000001 + index}:0;{command}\n')


def test_logs_every_new_command_in_order(logger):
    command_logger, zsh = logger
    seen = []
    command_logger.monitor_commands(lambda command: seen.append(command['command']), check_interval=0.05)
    assert command_logger.active_history == str(zsh)

    append(zsh, 'first', 'second', 'second')

    assert wait_for(lambda: len(seen) == 3)
    assert seen == ['first', 'second', 'second']


def test_keeps_logging_after_history_is_trimmed(logger):
    command_logger, zsh = logger
    seen = []
    command_logger.monitor_commands(lambda command: seen.append(command['command']), check_interval=0.05)

    zsh.write_text('')
    time.sleep(0.2)
    append(zsh, 'after')

    assert wait_for(lambda: seen == ['after'])


def test_stop_ends_monitoring(logger):
    command_logger, zsh = logger
    seen = []
    command_logger.monitor_commands(lambda command: seen.append(command['command']), check_interval=0.05)
    command_logger.stop()
    time.sleep(0.2)

    append(zsh, 'late')
    time.sleep(0.2)

    assert seen == []
