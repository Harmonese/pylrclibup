"""
文件系统操作单元测试
"""

import pytest
from pathlib import Path
from pylrclibup.fs.mover import move_with_dedup
from pylrclibup.fs.cleaner import cleanup_empty_dirs


class TestMoveWithDedup:
    """测试 move_with_dedup 函数"""
    
    def test_basic_move(self, tmp_path: Path):
        src = tmp_path / "src" / "file.txt"
        dst_dir = tmp_path / "dst"
        
        src.parent.mkdir(parents=True)
        src.write_text("content")
        
        result = move_with_dedup(src, dst_dir)
        
        assert result is not None
        assert result.exists()
        assert result.name == "file.txt"
        assert not src.exists()
    
    def test_dedup_on_conflict(self, tmp_path: Path):
        src = tmp_path / "src" / "file.txt"
        dst_dir = tmp_path / "dst"
        existing = dst_dir / "file.txt"
        
        src.parent.mkdir(parents=True)
        dst_dir.mkdir(parents=True)
        src.write_text("new content")
        existing.write_text("existing content")
        
        result = move_with_dedup(src, dst_dir)
        
        assert result is not None
        assert result.name == "file_dup1.txt"
        assert existing.exists()
    
    def test_multiple_dedup(self, tmp_path: Path):
        src = tmp_path / "src" / "file.txt"
        dst_dir = tmp_path / "dst"
        
        src.parent.mkdir(parents=True)
        dst_dir.mkdir(parents=True)
        
        # 创建已存在的重名文件
        (dst_dir / "file.txt").write_text("1")
        (dst_dir / "file_dup1.txt").write_text("2")
        
        src.write_text("new")
        result = move_with_dedup(src, dst_dir)
        
        assert result is not None
        assert result.name == "file_dup2.txt"
    
    def test_rename_on_move(self, tmp_path: Path):
        src = tmp_path / "src" / "original.lrc"
        dst_dir = tmp_path / "dst"
        
        src.parent.mkdir(parents=True)
        src.write_text("lyrics")
        
        result = move_with_dedup(src, dst_dir, new_name="new_name")
        
        assert result is not None
        assert result.name == "new_name.lrc"
    
    def test_same_location_no_op(self, tmp_path: Path):
        file = tmp_path / "file.txt"
        file.write_text("content")
        
        result = move_with_dedup(file, tmp_path)
        
        assert result == file
        assert file.exists()


class TestCleanupEmptyDirs:
    """测试 cleanup_empty_dirs 函数"""
    
    def test_remove_empty_dirs(self, tmp_path: Path):
        empty_dir = tmp_path / "a" / "b" / "c"
        empty_dir.mkdir(parents=True)
        
        cleanup_empty_dirs(tmp_path)
        
        assert not (tmp_path / "a").exists()
    
    def test_keep_non_empty_dirs(self, tmp_path: Path):
        non_empty = tmp_path / "a" / "b"
        non_empty.mkdir(parents=True)
        (non_empty / "file.txt").write_text("content")
        
        cleanup_empty_dirs(tmp_path)
        
        assert non_empty.exists()
        assert (non_empty / "file.txt").exists()
    
    def test_keep_root(self, tmp_path: Path):
        cleanup_empty_dirs(tmp_path)
        
        assert tmp_path.exists()
    
    def test_mixed_dirs(self, tmp_path: Path):
        # 创建混合结构
        (tmp_path / "empty1" / "empty2").mkdir(parents=True)
        (tmp_path / "nonempty").mkdir(parents=True)
        (tmp_path / "nonempty" / "file.txt").write_text("x")
        
        cleanup_empty_dirs(tmp_path)
        
        assert not (tmp_path / "empty1").exists()
        assert (tmp_path / "nonempty").exists()
