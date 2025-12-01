"""
pytest 共享 fixtures
"""

import pytest
from pathlib import Path


@pytest.fixture
def sample_lrc_content() -> str:
    """标准 LRC 文件内容样例"""
    return """[ti:测试歌曲]
[ar:测试艺术家]
[al:测试专辑]
[00:00.00]作词：张三
[00:01.00]作曲：李四
[00:02.00]第一行歌词
[00:05.00]第二行歌词
[00:10.00]第三行歌词
"""


@pytest.fixture
def sample_instrumental_lrc() -> str:
    """纯音乐 LRC 样例"""
    return """[00:00.00]纯音乐，请欣赏
"""


@pytest.fixture
def sample_lrc_with_translation() -> str:
    """带翻译的 LRC 样例"""
    return """[00:00.00]Hello world
[00:00.00]你好世界
[00:05.00]Goodbye
[00:05.00]再见
"""


@pytest.fixture
def create_lrc_file(tmp_path: Path):
    """创建临时 LRC 文件的工厂函数"""
    def _create(name: str, content: str) -> Path:
        lrc = tmp_path / name
        lrc.write_text(content, encoding='utf-8')
        return lrc
    return _create
