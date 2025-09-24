"""
网络对战模块
提供网络对战功能的框架（预留接口）
"""

import socket
import threading
import json
import time
import queue
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
import tkinter as tk
from tkinter import ttk, messagebox

# 导入核心模块
from core import Board, Game, Move


class NetworkMessageType(Enum):
    """网络消息类型"""
    # 连接管理
    CONNECT = 'connect'
    DISCONNECT = 'disconnect'
    HEARTBEAT = 'heartbeat'
    
    # 游戏管理
    CREATE_GAME = 'create_game'
    JOIN_GAME = 'join_game'
    LEAVE_GAME = 'leave_game'
    GAME_LIST = 'game_list'
    
    # 游戏进行
    MOVE = 'move'
    PASS = 'pass'
    RESIGN = 'resign'
    REQUEST_UNDO = 'request_undo'
    ACCEPT_UNDO = 'accept_undo'
    REJECT_UNDO = 'reject_undo'
    
    # 聊天
    CHAT = 'chat'
    
    # 状态同步
    SYNC_BOARD = 'sync_board'
    SYNC_TIME = 'sync_time'
    GAME_RESULT = 'game_result'


class ConnectionStatus(Enum):
    """连接状态"""
    DISCONNECTED = 'disconnected'
    CONNECTING = 'connecting'
    CONNECTED = 'connected'
    IN_GAME = 'in_game'
    ERROR = 'error'


@dataclass
class NetworkMessage:
    """网络消息"""
    type: NetworkMessageType
    data: Dict[str, Any]
    sender: str = ""
    timestamp: float = field(default_factory=time.time)
    
    def to_json(self) -> str:
        """转换为JSON"""
        return json.dumps({
            'type': self.type.value,
            'data': self.data,
            'sender': self.sender,
            'timestamp': self.timestamp
        })
    
    @classmethod
    def from_json(cls, json_str: str) -> 'NetworkMessage':
        """从JSON创建"""
        data = json.loads(json_str)
        return cls(
            type=NetworkMessageType(data['type']),
            data=data['data'],
            sender=data.get('sender', ''),
            timestamp=data.get('timestamp', time.time())
        )


@dataclass
class PlayerInfo:
    """玩家信息"""
    id: str
    name: str
    rating: int = 1500
    country: str = ""
    status: str = "online"
    current_game: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)


@dataclass
class GameRoom:
    """游戏房间"""
    id: str
    name: str
    host: PlayerInfo
    guest: Optional[PlayerInfo] = None
    board_size: int = 19
    rules: str = 'chinese'
    komi: float = 7.5
    time_control: str = 'none'
    main_time: int = 0
    status: str = 'waiting'  # waiting, playing, finished
    spectators: List[PlayerInfo] = field(default_factory=list)
    
    def is_full(self) -> bool:
        """房间是否已满"""
        return self.guest is not None
    
    def can_start(self) -> bool:
        """是否可以开始"""
        return self.is_full() and self.status == 'waiting'


class NetworkProtocol:
    """网络协议"""
    
    VERSION = "1.0"
    DEFAULT_PORT = 9999
    BUFFER_SIZE = 4096
    ENCODING = 'utf-8'
    
    @staticmethod
    def create_packet(message: NetworkMessage) -> bytes:
        """创建数据包"""
        json_str = message.to_json()
        # 添加长度前缀
        length = len(json_str)
        header = f"{length:08d}"
        return (header + json_str).encode(NetworkProtocol.ENCODING)
    
    @staticmethod
    def parse_packet(data: bytes) -> Optional[NetworkMessage]:
        """解析数据包"""
        try:
            # 解析长度前缀
            if len(data) < 8:
                return None
            
            header = data[:8].decode(NetworkProtocol.ENCODING)
            length = int(header)
            
            # 检查数据完整性
            if len(data) < 8 + length:
                return None
            
            # 解析消息
            json_str = data[8:8+length].decode(NetworkProtocol.ENCODING)
            return NetworkMessage.from_json(json_str)
        except Exception as e:
            print(f"解析数据包失败: {e}")
            return None


class NetworkConnection:
    """网络连接基类"""
    
    def __init__(self):
        self.socket: Optional[socket.socket] = None
        self.status = ConnectionStatus.DISCONNECTED
        self.receive_queue = queue.Queue()
        self.send_queue = queue.Queue()
        self.receive_thread: Optional[threading.Thread] = None
        self.send_thread: Optional[threading.Thread] = None
        self.running = False
        
        # 回调函数
        self.on_message_received: Optional[Callable] = None
        self.on_connection_lost: Optional[Callable] = None
    
    def start(self):
        """启动连接"""
        self.running = True
        
        # 启动接收线程
        self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
        self.receive_thread.start()
        
        # 启动发送线程
        self.send_thread = threading.Thread(target=self._send_loop, daemon=True)
        self.send_thread.start()
    
    def stop(self):
        """停止连接"""
        self.running = False
        
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        
        self.status = ConnectionStatus.DISCONNECTED
    
    def send_message(self, message: NetworkMessage):
        """发送消息"""
        self.send_queue.put(message)
    
    def _receive_loop(self):
        """接收循环"""
        buffer = b""
        
        while self.running:
            try:
                if not self.socket:
                    time.sleep(0.1)
                    continue
                
                # 接收数据
                data = self.socket.recv(NetworkProtocol.BUFFER_SIZE)
                if not data:
                    # 连接关闭
                    self._handle_disconnect()
                    break
                
                buffer += data
                
                # 尝试解析消息
                while len(buffer) >= 8:
                    # 获取消息长度
                    header = buffer[:8].decode(NetworkProtocol.ENCODING)
                    try:
                        length = int(header)
                    except:
                        buffer = buffer[1:]  # 跳过无效字节
                        continue
                    
                    # 检查是否有完整消息
                    if len(buffer) >= 8 + length:
                        packet_data = buffer[:8+length]
                        buffer = buffer[8+length:]
                        
                        # 解析消息
                        message = NetworkProtocol.parse_packet(packet_data)
                        if message:
                            self.receive_queue.put(message)
                            if self.on_message_received:
                                self.on_message_received(message)
                    else:
                        break
                        
            except socket.timeout:
                continue
            except Exception as e:
                print(f"接收错误: {e}")
                time.sleep(0.1)
    
    def _send_loop(self):
        """发送循环"""
        while self.running:
            try:
                # 从队列获取消息
                message = self.send_queue.get(timeout=0.1)
                
                if self.socket and self.status == ConnectionStatus.CONNECTED:
                    # 创建数据包
                    packet = NetworkProtocol.create_packet(message)
                    
                    # 发送数据
                    self.socket.sendall(packet)
                    
            except queue.Empty:
                continue
            except Exception as e:
                print(f"发送错误: {e}")
    
    def _handle_disconnect(self):
        """处理断开连接"""
        self.status = ConnectionStatus.DISCONNECTED
        if self.on_connection_lost:
            self.on_connection_lost()


class GameServer(NetworkConnection):
    """游戏服务器"""
    
    def __init__(self, port: int = NetworkProtocol.DEFAULT_PORT):
        super().__init__()
        self.port = port
        self.server_socket: Optional[socket.socket] = None
        self.clients: Dict[str, socket.socket] = {}
        self.players: Dict[str, PlayerInfo] = {}
        self.games: Dict[str, GameRoom] = {}
        self.accept_thread: Optional[threading.Thread] = None
    
    def start_server(self) -> bool:
        """启动服务器"""
        try:
            # 创建服务器套接字
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('', self.port))
            self.server_socket.listen(5)
            
            print(f"服务器启动在端口 {self.port}")
            
            # 启动接受连接线程
            self.accept_thread = threading.Thread(target=self._accept_loop, daemon=True)
            self.accept_thread.start()
            
            self.status = ConnectionStatus.CONNECTED
            return True
            
        except Exception as e:
            print(f"启动服务器失败: {e}")
            return False
    
    def stop_server(self):
        """停止服务器"""
        self.running = False
        
        # 关闭所有客户端连接
        for client_socket in self.clients.values():
            try:
                client_socket.close()
            except:
                pass
        
        # 关闭服务器套接字
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        self.status = ConnectionStatus.DISCONNECTED
    
    def _accept_loop(self):
        """接受连接循环"""
        while self.running:
            try:
                if not self.server_socket:
                    break
                
                # 接受新连接
                client_socket, address = self.server_socket.accept()
                client_socket.settimeout(1.0)
                
                print(f"新连接: {address}")
                
                # 创建客户端处理线程
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, address),
                    daemon=True
                )
                client_thread.start()
                
            except socket.timeout:
                continue
            except Exception as e:
                print(f"接受连接错误: {e}")
    
    def _handle_client(self, client_socket: socket.socket, address):
        """处理客户端"""
        client_id = f"{address[0]}:{address[1]}"
        self.clients[client_id] = client_socket
        
        buffer = b""
        
        while self.running:
            try:
                # 接收数据
                data = client_socket.recv(NetworkProtocol.BUFFER_SIZE)
                if not data:
                    break
                
                buffer += data
                
                # 处理消息（类似_receive_loop）
                while len(buffer) >= 8:
                    header = buffer[:8].decode(NetworkProtocol.ENCODING)
                    try:
                        length = int(header)
                    except:
                        buffer = buffer[1:]
                        continue
                    
                    if len(buffer) >= 8 + length:
                        packet_data = buffer[:8+length]
                        buffer = buffer[8+length:]
                        
                        message = NetworkProtocol.parse_packet(packet_data)
                        if message:
                            self._process_message(client_id, message)
                    else:
                        break
                        
            except socket.timeout:
                continue
            except Exception as e:
                print(f"客户端处理错误: {e}")
                break
        
        # 清理断开的客户端
        self._remove_client(client_id)
    
    def _process_message(self, client_id: str, message: NetworkMessage):
        """处理客户端消息"""
        if message.type == NetworkMessageType.CONNECT:
            # 处理连接请求
            player_info = PlayerInfo(**message.data)
            self.players[client_id] = player_info
            
            # 发送欢迎消息
            response = NetworkMessage(
                type=NetworkMessageType.CONNECT,
                data={'status': 'connected', 'player_id': client_id}
            )
            self._send_to_client(client_id, response)
            
        elif message.type == NetworkMessageType.CREATE_GAME:
            # 创建游戏房间
            self._create_game_room(client_id, message.data)
            
        elif message.type == NetworkMessageType.JOIN_GAME:
            # 加入游戏
            self._join_game_room(client_id, message.data['game_id'])
            
        elif message.type == NetworkMessageType.MOVE:
            # 处理棋步
            self._process_move(client_id, message.data)
            
        # TODO: 处理其他消息类型
    
    def _send_to_client(self, client_id: str, message: NetworkMessage):
        """发送消息到客户端"""
        if client_id in self.clients:
            try:
                packet = NetworkProtocol.create_packet(message)
                self.clients[client_id].sendall(packet)
            except Exception as e:
                print(f"发送到客户端失败: {e}")
    
    def _broadcast_to_game(self, game_id: str, message: NetworkMessage):
        """广播消息到游戏房间"""
        if game_id in self.games:
            game = self.games[game_id]
            
            # 发送给主机
            for client_id, player in self.players.items():
                if player.id == game.host.id:
                    self._send_to_client(client_id, message)
                    break
            
            # 发送给客人
            if game.guest:
                for client_id, player in self.players.items():
                    if player.id == game.guest.id:
                        self._send_to_client(client_id, message)
                        break
            
            # 发送给观众
            for spectator in game.spectators:
                for client_id, player in self.players.items():
                    if player.id == spectator.id:
                        self._send_to_client(client_id, message)
    
    def _create_game_room(self, client_id: str, game_data: Dict[str, Any]):
        """创建游戏房间"""
        if client_id not in self.players:
            return
        
        player = self.players[client_id]
        game_id = f"game_{len(self.games) + 1}"
        
        game = GameRoom(
            id=game_id,
            name=game_data.get('name', f"{player.name}的对局"),
            host=player,
            board_size=game_data.get('board_size', 19),
            rules=game_data.get('rules', 'chinese'),
            komi=game_data.get('komi', 7.5),
            time_control=game_data.get('time_control', 'none'),
            main_time=game_data.get('main_time', 0)
        )
        
        self.games[game_id] = game
        player.current_game = game_id
        
        # 发送确认
        response = NetworkMessage(
            type=NetworkMessageType.CREATE_GAME,
            data={'status': 'created', 'game_id': game_id}
        )
        self._send_to_client(client_id, response)
    
    def _join_game_room(self, client_id: str, game_id: str):
        """加入游戏房间"""
        if client_id not in self.players or game_id not in self.games:
            return
        
        player = self.players[client_id]
        game = self.games[game_id]
        
        if not game.is_full():
            game.guest = player
            player.current_game = game_id
            
            # 通知所有人
            message = NetworkMessage(
                type=NetworkMessageType.JOIN_GAME,
                data={
                    'status': 'joined',
                    'game_id': game_id,
                    'player': player.to_dict()
                }
            )
            self._broadcast_to_game(game_id, message)
        else:
            # 作为观众加入
            game.spectators.append(player)
            player.current_game = game_id
    
    def _process_move(self, client_id: str, move_data: Dict[str, Any]):
        """处理棋步"""
        if client_id not in self.players:
            return
        
        player = self.players[client_id]
        if not player.current_game:
            return
        
        game = self.games.get(player.current_game)
        if not game:
            return
        
        # 广播棋步
        message = NetworkMessage(
            type=NetworkMessageType.MOVE,
            data=move_data,
            sender=player.id
        )
        self._broadcast_to_game(game.id, message)
    
    def _remove_client(self, client_id: str):
        """移除客户端"""
        if client_id in self.clients:
            try:
                self.clients[client_id].close()
            except:
                pass
            del self.clients[client_id]
        
        if client_id in self.players:
            player = self.players[client_id]
            
            # 从游戏中移除
            if player.current_game and player.current_game in self.games:
                game = self.games[player.current_game]
                
                if game.host.id == player.id:
                    # 主机离开，解散游戏
                    del self.games[player.current_game]
                elif game.guest and game.guest.id == player.id:
                    # 客人离开
                    game.guest = None
                else:
                    # 观众离开
                    game.spectators = [s for s in game.spectators if s.id != player.id]
            
            del self.players[client_id]


class GameClient(NetworkConnection):
    """游戏客户端"""
    
    def __init__(self):
        super().__init__()
        self.player_info: Optional[PlayerInfo] = None
        self.current_game: Optional[GameRoom] = None
    
    def connect_to_server(self, host: str, port: int = NetworkProtocol.DEFAULT_PORT) -> bool:
        """连接到服务器"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5.0)
            self.socket.connect((host, port))
            self.socket.settimeout(1.0)
            
            self.status = ConnectionStatus.CONNECTED
            self.start()
            
            return True
            
        except Exception as e:
            print(f"连接服务器失败: {e}")
            self.status = ConnectionStatus.ERROR
            return False
    
    def disconnect_from_server(self):
        """断开服务器连接"""
        if self.status == ConnectionStatus.CONNECTED:
            # 发送断开消息
            message = NetworkMessage(
                type=NetworkMessageType.DISCONNECT,
                data={'player_id': self.player_info.id if self.player_info else ''}
            )
            self.send_message(message)
        
        self.stop()
    
    def login(self, player_name: str, rating: int = 1500):
        """登录"""
        self.player_info = PlayerInfo(
            id=f"{player_name}_{time.time()}",
            name=player_name,
            rating=rating
        )
        
        message = NetworkMessage(
            type=NetworkMessageType.CONNECT,
            data=self.player_info.to_dict()
        )
        
        self.send_message(message)
    
    def create_game(self, name: str, board_size: int = 19, 
                    rules: str = 'chinese', **kwargs):
        """创建游戏"""
        message = NetworkMessage(
            type=NetworkMessageType.CREATE_GAME,
            data={
                'name': name,
                'board_size': board_size,
                'rules': rules,
                **kwargs
            }
        )
        
        self.send_message(message)
    
    def join_game(self, game_id: str):
        """加入游戏"""
        message = NetworkMessage(
            type=NetworkMessageType.JOIN_GAME,
            data={'game_id': game_id}
        )
        
        self.send_message(message)
    
    def send_move(self, x: int, y: int, color: str):
        """发送棋步"""
        message = NetworkMessage(
            type=NetworkMessageType.MOVE,
            data={
                'x': x,
                'y': y,
                'color': color,
                'timestamp': time.time()
            }
        )
        
        self.send_message(message)
    
    def send_pass(self):
        """发送虚手"""
        message = NetworkMessage(
            type=NetworkMessageType.PASS,
            data={'timestamp': time.time()}
        )
        
        self.send_message(message)
    
    def send_resign(self):
        """发送认输"""
        message = NetworkMessage(
            type=NetworkMessageType.RESIGN,
            data={'timestamp': time.time()}
        )
        
        self.send_message(message)
    
    def send_chat(self, text: str):
        """发送聊天"""
        message = NetworkMessage(
            type=NetworkMessageType.CHAT,
            data={
                'text': text,
                'timestamp': time.time()
            }
        )
        
        self.send_message(message)


class NetworkGame:
    """网络对局"""
    
    def __init__(self, client: GameClient, game_room: GameRoom):
        self.client = client
        self.game_room = game_room
        self.local_game = Game(
            board_size=game_room.board_size,
            rule_set=game_room.rules,
            komi=game_room.komi
        )
        
        # 确定本地玩家颜色
        if self.client.player_info:
            if game_room.host.id == self.client.player_info.id:
                self.local_color = 'black'
            elif game_room.guest and game_room.guest.id == self.client.player_info.id:
                self.local_color = 'white'
            else:
                self.local_color = None  # 观众
        else:
            self.local_color = None
        
        # 回调
        self.on_move_received: Optional[Callable] = None
        self.on_game_ended: Optional[Callable] = None
        self.on_chat_received: Optional[Callable] = None
    
    def is_my_turn(self) -> bool:
        """是否轮到自己"""
        return (self.local_color and 
                self.local_game.current_player == self.local_color)
    
    def make_local_move(self, x: int, y: int) -> bool:
        """本地落子"""
        if not self.is_my_turn():
            return False
        
        # 在本地游戏中落子
        result = self.local_game.make_move(x, y)
        
        if result.value == 'success':
            # 发送到服务器
            self.client.send_move(x, y, self.local_color)
            return True
        
        return False
    
    def receive_remote_move(self, x: int, y: int, color: str):
        """接收远程落子"""
        if color != self.local_color:
            # 在本地游戏中执行
            self.local_game.make_move(x, y)
            
            # 触发回调
            if self.on_move_received:
                self.on_move_received(x, y, color)
    
    def pass_turn(self):
        """虚手"""
        if self.is_my_turn():
            self.local_game.pass_turn()
            self.client.send_pass()
    
    def resign(self):
        """认输"""
        if self.local_color:
            self.client.send_resign()
            
            # 结束游戏
            if self.on_game_ended:
                winner = 'white' if self.local_color == 'black' else 'black'
                self.on_game_ended(winner, 'resign')


class MatchMaker:
    """匹配系统"""
    
    def __init__(self, server: Optional[GameServer] = None):
        self.server = server
        self.waiting_players: List[PlayerInfo] = []
        self.match_thread: Optional[threading.Thread] = None
        self.running = False
    
    def start_matching(self):
        """开始匹配"""
        self.running = True
        self.match_thread = threading.Thread(target=self._match_loop, daemon=True)
        self.match_thread.start()
    
    def stop_matching(self):
        """停止匹配"""
        self.running = False
        if self.match_thread:
            self.match_thread.join(timeout=1.0)
    
    def add_player(self, player: PlayerInfo):
        """添加等待匹配的玩家"""
        if player not in self.waiting_players:
            self.waiting_players.append(player)
    
    def remove_player(self, player: PlayerInfo):
        """移除玩家"""
        if player in self.waiting_players:
            self.waiting_players.remove(player)
    
    def _match_loop(self):
        """匹配循环"""
        while self.running:
            if len(self.waiting_players) >= 2:
                # 简单匹配：选择前两个玩家
                player1 = self.waiting_players.pop(0)
                player2 = self.waiting_players.pop(0)
                
                # 根据等级差决定是否匹配
                if abs(player1.rating - player2.rating) <= 200:
                    self._create_match(player1, player2)
                else:
                    # 重新加入等待队列
                    self.waiting_players.append(player1)
                    self.waiting_players.append(player2)
            
            time.sleep(1.0)
    
    def _create_match(self, player1: PlayerInfo, player2: PlayerInfo):
        """创建匹配"""
        if not self.server:
            return
        
        # 创建游戏房间
        game_id = f"match_{time.time()}"
        
        game = GameRoom(
            id=game_id,
            name=f"{player1.name} vs {player2.name}",
            host=player1,
            guest=player2,
            board_size=19,
            rules='chinese',
            komi=7.5,
            time_control='byoyomi',
            main_time=600,
            status='playing'
        )
        
        self.server.games[game_id] = game
        
        # 通知玩家
        message = NetworkMessage(
            type=NetworkMessageType.CREATE_GAME,
            data={
                'game_id': game_id,
                'matched': True,
                'opponent': player2.to_dict()
            }
        )
        
        # TODO: 发送通知给两个玩家