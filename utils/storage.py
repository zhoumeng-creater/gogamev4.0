"""
存储管理模块
处理游戏存档、云存储同步等
"""

import os
import json
import pickle
import gzip
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from pathlib import Path
from abc import ABC, abstractmethod
import hashlib
import threading
import time


@dataclass
class GameSave:
    """游戏存档数据"""
    save_id: str
    name: str
    date_created: str
    date_modified: str
    game_data: Dict[str, Any]
    board_size: int
    move_count: int
    player_black: str
    player_white: str
    result: str = ""
    description: str = ""
    tags: List[str] = None
    thumbnail: Optional[bytes] = None
    checksum: str = ""
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        
        # 生成校验和
        if not self.checksum:
            self.checksum = self._calculate_checksum()
    
    def _calculate_checksum(self) -> str:
        """计算数据校验和"""
        data_str = json.dumps(self.game_data, sort_keys=True)
        return hashlib.md5(data_str.encode()).hexdigest()
    
    def verify_integrity(self) -> bool:
        """验证数据完整性"""
        return self.checksum == self._calculate_checksum()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        # 移除缩略图（太大）
        if 'thumbnail' in data:
            del data['thumbnail']
        return data


class CloudStorage(ABC):
    """云存储接口基类"""
    
    @abstractmethod
    def connect(self, credentials: Dict[str, str]) -> bool:
        """连接到云存储服务"""
        pass
    
    @abstractmethod
    def upload(self, file_path: str, remote_path: str) -> bool:
        """上传文件"""
        pass
    
    @abstractmethod
    def download(self, remote_path: str, local_path: str) -> bool:
        """下载文件"""
        pass
    
    @abstractmethod
    def list_files(self, remote_dir: str = "") -> List[str]:
        """列出文件"""
        pass
    
    @abstractmethod
    def delete(self, remote_path: str) -> bool:
        """删除文件"""
        pass
    
    @abstractmethod
    def sync(self, local_dir: str, remote_dir: str, bidirectional: bool = True) -> bool:
        """同步目录"""
        pass


class GoogleDriveStorage(CloudStorage):
    """Google Drive云存储实现"""
    
    def __init__(self):
        self.connected = False
        # 实际实现需要Google API客户端库
    
    def connect(self, credentials: Dict[str, str]) -> bool:
        """连接到Google Drive"""
        # TODO: 实现Google Drive连接
        # 需要google-api-python-client库
        print("Google Drive存储接口（待实现）")
        return False
    
    def upload(self, file_path: str, remote_path: str) -> bool:
        return False
    
    def download(self, remote_path: str, local_path: str) -> bool:
        return False
    
    def list_files(self, remote_dir: str = "") -> List[str]:
        return []
    
    def delete(self, remote_path: str) -> bool:
        return False
    
    def sync(self, local_dir: str, remote_dir: str, bidirectional: bool = True) -> bool:
        return False


class DropboxStorage(CloudStorage):
    """Dropbox云存储实现"""
    
    def __init__(self):
        self.connected = False
        # 实际实现需要Dropbox SDK
    
    def connect(self, credentials: Dict[str, str]) -> bool:
        """连接到Dropbox"""
        # TODO: 实现Dropbox连接
        # 需要dropbox库
        print("Dropbox存储接口（待实现）")
        return False
    
    def upload(self, file_path: str, remote_path: str) -> bool:
        return False
    
    def download(self, remote_path: str, local_path: str) -> bool:
        return False
    
    def list_files(self, remote_dir: str = "") -> List[str]:
        return []
    
    def delete(self, remote_path: str) -> bool:
        return False
    
    def sync(self, local_dir: str, remote_dir: str, bidirectional: bool = True) -> bool:
        return False


class OneDriveStorage(CloudStorage):
    """OneDrive云存储实现"""
    
    def __init__(self):
        self.connected = False
        # 实际实现需要Microsoft Graph API
    
    def connect(self, credentials: Dict[str, str]) -> bool:
        """连接到OneDrive"""
        # TODO: 实现OneDrive连接
        # 需要msal和msgraph-core库
        print("OneDrive存储接口（待实现）")
        return False
    
    def upload(self, file_path: str, remote_path: str) -> bool:
        return False
    
    def download(self, remote_path: str, local_path: str) -> bool:
        return False
    
    def list_files(self, remote_dir: str = "") -> List[str]:
        return []
    
    def delete(self, remote_path: str) -> bool:
        return False
    
    def sync(self, local_dir: str, remote_dir: str, bidirectional: bool = True) -> bool:
        return False


class StorageManager:
    """存储管理器"""
    
    SAVE_FORMATS = {
        'pickle': '.pkl',
        'json': '.json',
        'sgf': '.sgf'
    }
    
    def __init__(self, config_manager=None):
        """
        初始化存储管理器
        
        Args:
            config_manager: 配置管理器
        """
        self.config = config_manager
        
        # 设置存储路径
        if config_manager:
            self.save_dir = config_manager.get('storage.save_path', './saves')
            self.sgf_dir = config_manager.get('storage.sgf_path', './sgf')
            self.compress = config_manager.get('storage.compress_saves', True)
            self.max_saves = config_manager.get('storage.max_saves', 100)
            self.auto_save = config_manager.get('storage.auto_save', True)
            self.auto_save_interval = config_manager.get('storage.auto_save_interval', 60)
        else:
            self.save_dir = './saves'
            self.sgf_dir = './sgf'
            self.compress = True
            self.max_saves = 100
            self.auto_save = True
            self.auto_save_interval = 60
        
        # 创建目录
        os.makedirs(self.save_dir, exist_ok=True)
        os.makedirs(self.sgf_dir, exist_ok=True)
        
        # 云存储
        self.cloud_storage: Optional[CloudStorage] = None
        self.cloud_enabled = False
        self.sync_thread = None
        self.stop_sync = False
        
        # 存档缓存
        self.save_cache: Dict[str, GameSave] = {}
        self._load_save_index()
        
        # 自动保存
        self.auto_save_thread = None
        self.auto_save_callback = None
        if self.auto_save:
            self._start_auto_save()
    
    def _load_save_index(self):
        """加载存档索引"""
        index_file = os.path.join(self.save_dir, 'index.json')
        
        if os.path.exists(index_file):
            try:
                with open(index_file, 'r', encoding='utf-8') as f:
                    index_data = json.load(f)
                    
                for save_id, save_info in index_data.items():
                    # 不加载完整游戏数据，只加载元信息
                    save_info['game_data'] = {}
                    self.save_cache[save_id] = GameSave(**save_info)
                    
            except Exception as e:
                print(f"加载存档索引失败: {e}")
    
    def _save_index(self):
        """保存存档索引"""
        index_file = os.path.join(self.save_dir, 'index.json')
        
        try:
            index_data = {}
            for save_id, game_save in self.save_cache.items():
                index_data[save_id] = game_save.to_dict()
            
            with open(index_file, 'w', encoding='utf-8') as f:
                json.dump(index_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"保存存档索引失败: {e}")
    
    def save_game(self, game_data: Dict[str, Any], name: str = None,
                  format: str = 'pickle', tags: List[str] = None,
                  description: Optional[str] = None) -> Optional[str]:
        """
        保存游戏
        
        Args:
            game_data: 游戏数据
            name: 存档名称
            format: 存储格式
            tags: 标签
        
        Returns:
            存档ID或None
        """
        try:
            # 生成存档ID
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            save_id = f"save_{timestamp}_{hashlib.md5(str(game_data).encode()).hexdigest()[:8]}"
            
            # 创建存档对象
            game_save = GameSave(
                save_id=save_id,
                name=name or f"存档 {timestamp}",
                date_created=datetime.now().isoformat(),
                date_modified=datetime.now().isoformat(),
                game_data=game_data,
                board_size=game_data.get('board_size', 19),
                move_count=len(game_data.get('moves', [])),
                player_black=game_data.get('player_black', 'Black'),
                player_white=game_data.get('player_white', 'White'),
                result=game_data.get('result', ''),
                description=description or "",
                tags=tags or []
            )
            
            # 选择文件路径和格式
            ext = self.SAVE_FORMATS.get(format, '.pkl')
            file_name = f"{save_id}{ext}"
            
            if self.compress and format != 'sgf':
                file_name += '.gz'
            
            file_path = os.path.join(self.save_dir, file_name)
            
            # 保存文件
            if format == 'pickle':
                self._save_pickle(game_save, file_path)
            elif format == 'json':
                self._save_json(game_save, file_path)
            elif format == 'sgf':
                self._save_sgf(game_save, file_path)
            else:
                raise ValueError(f"不支持的格式: {format}")
            
            # 更新缓存
            self.save_cache[save_id] = game_save
            self._save_index()
            
            # 清理旧存档
            self._cleanup_old_saves()
            
            # 同步到云
            if self.cloud_enabled:
                self._queue_cloud_sync(file_path)
            
            return save_id
            
        except Exception as e:
            print(f"保存游戏失败: {e}")
            return None
    
    def _save_pickle(self, game_save: GameSave, file_path: str):
        """使用pickle格式保存"""
        if self.compress:
            with gzip.open(file_path, 'wb') as f:
                pickle.dump(game_save, f)
        else:
            with open(file_path, 'wb') as f:
                pickle.dump(game_save, f)
    
    def _save_json(self, game_save: GameSave, file_path: str):
        """使用JSON格式保存"""
        data = game_save.to_dict()
        
        if self.compress:
            with gzip.open(file_path, 'wt', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        else:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _save_sgf(self, game_save: GameSave, file_path: str):
        """使用SGF格式保存"""
        from .sgf import SGFParser, SGFGame
        
        # 转换为SGF
        game = SGFGame()
        # TODO: 实现game_data到SGF的转换
        sgf_text = SGFParser.generate(game)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(sgf_text)
    
    def load_game(self, save_id: str) -> Optional[GameSave]:
        """
        加载游戏
        
        Args:
            save_id: 存档ID
        
        Returns:
            GameSave对象或None
        """
        try:
            # 查找存档文件
            save_files = os.listdir(self.save_dir)
            target_file = None
            
            for file_name in save_files:
                if file_name.startswith(save_id):
                    target_file = os.path.join(self.save_dir, file_name)
                    break
            
            if not target_file:
                return None
            
            # 判断格式并加载
            if target_file.endswith('.pkl.gz'):
                with gzip.open(target_file, 'rb') as f:
                    return pickle.load(f)
            elif target_file.endswith('.pkl'):
                with open(target_file, 'rb') as f:
                    return pickle.load(f)
            elif target_file.endswith('.json.gz'):
                with gzip.open(target_file, 'rt', encoding='utf-8') as f:
                    data = json.load(f)
                    return GameSave(**data)
            elif target_file.endswith('.json'):
                with open(target_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return GameSave(**data)
            elif target_file.endswith('.sgf'):
                # TODO: 实现SGF加载
                pass
            
        except Exception as e:
            print(f"加载游戏失败: {e}")
        
        return None
    
    def list_saves(self, sort_by: str = 'date', reverse: bool = True) -> List[GameSave]:
        """
        列出所有存档
        
        Args:
            sort_by: 排序方式 (date/name/size)
            reverse: 是否倒序
        
        Returns:
            存档列表
        """
        saves = list(self.save_cache.values())
        
        if sort_by == 'date':
            saves.sort(key=lambda x: x.date_modified, reverse=reverse)
        elif sort_by == 'name':
            saves.sort(key=lambda x: x.name, reverse=reverse)
        elif sort_by == 'moves':
            saves.sort(key=lambda x: x.move_count, reverse=reverse)
        
        return saves
    
    def delete_save(self, save_id: str) -> bool:
        """
        删除存档
        
        Args:
            save_id: 存档ID
        
        Returns:
            是否成功
        """
        try:
            # 删除文件
            save_files = os.listdir(self.save_dir)
            for file_name in save_files:
                if file_name.startswith(save_id):
                    file_path = os.path.join(self.save_dir, file_name)
                    os.remove(file_path)
            
            # 更新缓存
            if save_id in self.save_cache:
                del self.save_cache[save_id]
                self._save_index()
            
            return True
            
        except Exception as e:
            print(f"删除存档失败: {e}")
            return False
    
    def _cleanup_old_saves(self):
        """清理旧存档"""
        if len(self.save_cache) > self.max_saves:
            # 按日期排序
            saves = self.list_saves(sort_by='date', reverse=False)
            
            # 删除最旧的存档
            to_delete = len(saves) - self.max_saves
            for i in range(to_delete):
                self.delete_save(saves[i].save_id)
    
    def enable_cloud_sync(self, provider: str, credentials: Dict[str, str]) -> bool:
        """
        启用云同步
        
        Args:
            provider: 云存储提供商
            credentials: 认证信息
        
        Returns:
            是否成功
        """
        try:
            # 创建云存储实例
            if provider == 'google':
                self.cloud_storage = GoogleDriveStorage()
            elif provider == 'dropbox':
                self.cloud_storage = DropboxStorage()
            elif provider == 'onedrive':
                self.cloud_storage = OneDriveStorage()
            else:
                return False
            
            # 连接
            if self.cloud_storage.connect(credentials):
                self.cloud_enabled = True
                self._start_sync_thread()
                return True
                
        except Exception as e:
            print(f"启用云同步失败: {e}")
        
        return False
    
    def _start_sync_thread(self):
        """启动同步线程"""
        if self.sync_thread and self.sync_thread.is_alive():
            return
        
        self.stop_sync = False
        self.sync_thread = threading.Thread(target=self._sync_worker, daemon=True)
        self.sync_thread.start()
    
    def _sync_worker(self):
        """同步工作线程"""
        while not self.stop_sync:
            try:
                if self.cloud_enabled and self.cloud_storage:
                    # 执行同步
                    self.cloud_storage.sync(self.save_dir, 'GoMaster/saves')
                    self.cloud_storage.sync(self.sgf_dir, 'GoMaster/sgf')
            except Exception as e:
                print(f"云同步失败: {e}")
            
            # 等待下次同步
            time.sleep(300)  # 5分钟同步一次
    
    def _queue_cloud_sync(self, file_path: str):
        """将文件加入云同步队列"""
        # TODO: 实现异步上传队列
        pass
    
    def _start_auto_save(self):
        """启动自动保存"""
        if self.auto_save_thread and self.auto_save_thread.is_alive():
            return
        
        self.auto_save_thread = threading.Thread(target=self._auto_save_worker, daemon=True)
        self.auto_save_thread.start()
    
    def _auto_save_worker(self):
        """自动保存工作线程"""
        while self.auto_save:
            time.sleep(self.auto_save_interval)
            
            if self.auto_save_callback:
                try:
                    self.auto_save_callback()
                except Exception as e:
                    print(f"自动保存失败: {e}")
    
    def set_auto_save_callback(self, callback):
        """设置自动保存回调"""
        self.auto_save_callback = callback
    
    def export_to_sgf(self, save_id: str, output_path: str) -> bool:
        """
        导出为SGF格式
        
        Args:
            save_id: 存档ID
            output_path: 输出路径
        
        Returns:
            是否成功
        """
        try:
            game_save = self.load_game(save_id)
            if not game_save:
                return False
            
            # TODO: 实现导出逻辑
            return True
            
        except Exception as e:
            print(f"导出SGF失败: {e}")
            return False
    
    def import_sgf(self, sgf_path: str, name: str = None) -> Optional[str]:
        """
        导入SGF文件
        
        Args:
            sgf_path: SGF文件路径
            name: 存档名称
        
        Returns:
            存档ID或None
        """
        try:
            from .sgf import SGFParser
            
            game = SGFParser.load_from_file(sgf_path)
            if not game:
                return None
            
            # TODO: 实现SGF到game_data的转换
            game_data = {}
            
            return self.save_game(game_data, name)
            
        except Exception as e:
            print(f"导入SGF失败: {e}")
            return None
    
    def cleanup(self):
        """清理资源"""
        self.stop_sync = True
        self.auto_save = False
        
        if self.sync_thread:
            self.sync_thread.join(timeout=1.0)
        
        if self.auto_save_thread:
            self.auto_save_thread.join(timeout=1.0)
