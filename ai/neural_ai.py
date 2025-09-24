"""
神经网络AI模块
提供深度学习AI的框架和接口
注意：这是一个框架实现，实际的神经网络需要训练好的模型文件
"""

import time
import random
import numpy as np
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass
from pathlib import Path

from .base import AIPlayer, Move, AILevel
from .search_ai import MonteCarloAI, MCTSNode
from core import Board, Rules, MoveResult


@dataclass
class NeuralNetConfig:
    """神经网络配置"""
    model_path: Optional[str] = None
    use_gpu: bool = False
    batch_size: int = 8
    num_simulations: int = 800
    c_puct: float = 1.0
    dirichlet_alpha: float = 0.3
    dirichlet_weight: float = 0.25
    temperature: float = 1.0
    
    # 模型架构参数
    board_size: int = 19
    num_channels: int = 256
    num_residual_blocks: int = 20
    
    # 特征平面配置
    history_length: int = 8  # 历史局面数
    num_feature_planes: int = 17  # 特征平面数


class NeuralNetInterface:
    """
    神经网络接口
    实际应用中应该加载训练好的模型（如TensorFlow、PyTorch等）
    这里提供模拟实现
    """
    
    def __init__(self, config: NeuralNetConfig):
        self.config = config
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """
        加载神经网络模型
        实际实现应该从文件加载训练好的模型
        """
        if self.config.model_path and Path(self.config.model_path).exists():
            # 这里应该加载实际的模型
            # self.model = load_model(self.config.model_path)
            pass
        else:
            # 使用随机网络作为演示
            print("警告：未找到训练模型，使用随机初始化的网络")
            self.model = None
    
    def predict(self, features: np.ndarray) -> Tuple[np.ndarray, float]:
        """
        预测落子概率和局面价值
        
        Args:
            features: 输入特征 shape=(batch, channels, height, width)
        
        Returns:
            policy: 落子概率分布 shape=(batch, board_size * board_size)
            value: 局面价值评估 shape=(batch, 1)
        """
        if self.model is not None:
            # 使用实际模型预测
            # policy, value = self.model.predict(features)
            pass
        else:
            # 模拟预测（随机）
            batch_size = features.shape[0]
            board_size = self.config.board_size
            
            # 随机策略（加入一些启发式）
            policy = np.random.dirichlet([0.1] * (board_size * board_size), batch_size)
            
            # 添加一些位置偏好（中心和角部）
            for i in range(batch_size):
                for y in range(board_size):
                    for x in range(board_size):
                        idx = y * board_size + x
                        
                        # 角部星位加权
                        if (x, y) in [(3, 3), (3, 15), (15, 3), (15, 15), (9, 9)]:
                            policy[i, idx] *= 2.0
                        
                        # 边界降权
                        if x == 0 or x == board_size - 1 or y == 0 or y == board_size - 1:
                            policy[i, idx] *= 0.5
                
                # 归一化
                policy[i] /= policy[i].sum()
            
            # 随机价值
            value = np.random.uniform(-1, 1, (batch_size, 1))
        
        return policy, value


class FeatureExtractor:
    """特征提取器"""
    
    def __init__(self, config: NeuralNetConfig):
        self.config = config
    
    def extract_features(self, board: Board, color: str, 
                        history: List[Board] = None) -> np.ndarray:
        """
        提取棋盘特征
        
        Args:
            board: 当前棋盘
            color: 当前玩家颜色
            history: 历史棋盘列表
        
        Returns:
            特征张量 shape=(channels, height, width)
        """
        board_size = self.config.board_size
        num_planes = self.config.num_feature_planes
        
        features = np.zeros((num_planes, board_size, board_size), dtype=np.float32)
        
        # 平面0: 己方棋子
        # 平面1: 对方棋子
        # 平面2: 空点
        for y in range(board_size):
            for x in range(board_size):
                stone = board.get_stone(x, y)
                if stone == color:
                    features[0, y, x] = 1.0
                elif stone != '' and stone != color:
                    features[1, y, x] = 1.0
                else:
                    features[2, y, x] = 1.0
        
        # 平面3-4: 己方/对方的气数（1气的棋块）
        for group in board.get_all_groups():
            if len(group.liberties) == 1:
                plane_idx = 3 if group.color == color else 4
                for x, y in group.stones:
                    features[plane_idx, y, x] = 1.0
        
        # 平面5-6: 己方/对方的气数（2气的棋块）
        for group in board.get_all_groups():
            if len(group.liberties) == 2:
                plane_idx = 5 if group.color == color else 6
                for x, y in group.stones:
                    features[plane_idx, y, x] = 1.0
        
        # 平面7-8: 己方/对方的气数（3气的棋块）
        for group in board.get_all_groups():
            if len(group.liberties) == 3:
                plane_idx = 7 if group.color == color else 8
                for x, y in group.stones:
                    features[plane_idx, y, x] = 1.0
        
        # 平面9-10: 己方/对方的气数（4+气的棋块）
        for group in board.get_all_groups():
            if len(group.liberties) >= 4:
                plane_idx = 9 if group.color == color else 10
                for x, y in group.stones:
                    features[plane_idx, y, x] = 1.0
        
        # 平面11: 上一手落子位置
        # 平面12: 上上手落子位置
        # （需要历史信息，这里暂时跳过）
        
        # 平面13: 合法落子位置
        rules = Rules()
        for y in range(board_size):
            for x in range(board_size):
                if board.is_empty(x, y):
                    result = rules.is_legal_move(board, x, y, color, None)
                    if result == MoveResult.SUCCESS:
                        features[13, y, x] = 1.0
        
        # 平面14: 劫点
        # （需要游戏状态信息）
        
        # 平面15: 当前玩家是黑方
        if color == 'black':
            features[15, :, :] = 1.0
        
        # 平面16: 当前玩家是白方
        if color == 'white':
            features[16, :, :] = 1.0
        
        return features


class NeuralMCTSNode(MCTSNode):
    """神经网络增强的MCTS节点"""
    
    def __init__(self, board: Board, move: Optional[Tuple[int, int]],
                 parent: Optional['NeuralMCTSNode'], current_color: str,
                 prior: float = 0.0):
        super().__init__(board, move, parent, current_color)
        self.prior = prior  # 先验概率（来自神经网络）
        self.value_sum = 0.0  # 价值累计
        
    def select_child_puct(self, c_puct: float = 1.0) -> 'NeuralMCTSNode':
        """使用PUCT算法选择子节点"""
        return max(
            self.children,
            key=lambda c: self._puct_score(c, c_puct)
        )
    
    def _puct_score(self, child: 'NeuralMCTSNode', c_puct: float) -> float:
        """计算PUCT分数"""
        if child.visits == 0:
            q_value = 0
        else:
            q_value = child.value_sum / child.visits
        
        # PUCT = Q + U
        # U = c_puct * P * sqrt(parent_visits) / (1 + visits)
        u_value = c_puct * child.prior * np.sqrt(self.visits) / (1 + child.visits)
        
        return q_value + u_value
    
    def expand(self, priors: Dict[Tuple[int, int], float]):
        """使用先验概率扩展节点"""
        for move, prior in priors.items():
            if move in self.untried_moves:
                # 创建新棋盘
                new_board = self.board.copy()
                new_board.place_stone(move[0], move[1], self.current_color)
                
                # 切换颜色
                next_color = 'white' if self.current_color == 'black' else 'black'
                
                # 创建子节点
                child = NeuralMCTSNode(
                    new_board, move, self, next_color, prior
                )
                
                self.untried_moves.remove(move)
                self.children.append(child)
    
    def backup(self, value: float):
        """反向传播价值"""
        self.visits += 1
        self.value_sum += value
        
        if self.parent:
            self.parent.backup(-value)  # 对手的价值相反


class NeuralNetAI(AIPlayer):
    """
    神经网络AI - 最高难度
    基于深度学习的AI，类似AlphaGo的架构
    """
    
    def __init__(self, color: str, board_size: int = 19, **kwargs):
        super().__init__(color, board_size, thinking_time=10.0, level=AILevel.MASTER)
        
        # 配置
        self.config = NeuralNetConfig(
            model_path=kwargs.get('model_path'),
            use_gpu=kwargs.get('use_gpu', False),
            num_simulations=kwargs.get('simulations', 800),
            board_size=board_size
        )
        
        # 初始化组件
        self.neural_net = NeuralNetInterface(self.config)
        self.feature_extractor = FeatureExtractor(self.config)
        
        # 备用AI（当神经网络不可用时）
        self.fallback_ai = MonteCarloAI(color, board_size, simulations=1000)
        
        # 历史记录（用于特征提取）
        self.board_history = []
    
    def get_move(self, board: Board, game_info: Dict[str, Any]) -> Optional[Tuple[int, int]]:
        """
        使用神经网络MCTS选择落子
        
        Args:
            board: 当前棋盘
            game_info: 游戏信息
        
        Returns:
            最佳落子位置
        """
        # 如果没有可用的神经网络模型，使用备用AI
        if self.neural_net.model is None:
            return self.fallback_ai.get_move(board, game_info)
        
        start_time = time.time()
        
        # 获取合法着法
        ko_point = game_info.get('ko_point')
        legal_moves = self.get_legal_moves(board, ko_point)
        
        if not legal_moves:
            return None
        
        if len(legal_moves) == 1:
            return legal_moves[0]
        
        # 执行神经网络MCTS
        root = self._neural_mcts_search(board, legal_moves, game_info)
        
        self.time_spent = time.time() - start_time
        
        # 选择最佳着法
        if root.children:
            # 根据访问次数选择（也可以根据其他策略）
            if self.config.temperature > 0:
                # 带温度的选择（增加随机性）
                visits = np.array([child.visits for child in root.children])
                probs = visits ** (1.0 / self.config.temperature)
                probs /= probs.sum()
                
                idx = np.random.choice(len(root.children), p=probs)
                best_child = root.children[idx]
            else:
                # 选择访问次数最多的
                best_child = max(root.children, key=lambda c: c.visits)
            
            return best_child.move
        
        return None
    
    def _neural_mcts_search(self, board: Board, legal_moves: List[Tuple[int, int]], 
                           game_info: Dict[str, Any]) -> NeuralMCTSNode:
        """执行神经网络增强的MCTS"""
        # 创建根节点
        root = NeuralMCTSNode(board, None, None, self.color)
        root.untried_moves = legal_moves
        
        # 获取初始预测
        features = self.feature_extractor.extract_features(board, self.color, self.board_history)
        features_batch = np.expand_dims(features, 0)
        
        policy, value = self.neural_net.predict(features_batch)
        
        # 将策略转换为先验概率
        priors = {}
        for move in legal_moves:
            idx = move[1] * self.config.board_size + move[0]
            priors[move] = float(policy[0, idx])
        
        # 添加Dirichlet噪声（用于探索）
        if self.config.dirichlet_weight > 0:
            noise = np.random.dirichlet([self.config.dirichlet_alpha] * len(legal_moves))
            for i, move in enumerate(legal_moves):
                priors[move] = (1 - self.config.dirichlet_weight) * priors[move] + \
                              self.config.dirichlet_weight * noise[i]
        
        # 扩展根节点
        root.expand(priors)
        
        # 执行模拟
        for _ in range(self.config.num_simulations):
            node = root
            path = [node]
            
            # 1. 选择 - 沿着树向下选择
            while node.children and not node.untried_moves:
                node = node.select_child_puct(self.config.c_puct)
                path.append(node)
            
            # 2. 扩展和评估
            if node.untried_moves:
                # 获取神经网络预测
                features = self.feature_extractor.extract_features(
                    node.board, node.current_color, self.board_history
                )
                features_batch = np.expand_dims(features, 0)
                
                policy, value = self.neural_net.predict(features_batch)
                
                # 转换策略为先验
                child_priors = {}
                for move in node.untried_moves:
                    idx = move[1] * self.config.board_size + move[0]
                    child_priors[move] = float(policy[0, idx])
                
                # 扩展节点
                node.expand(child_priors)
                
                # 使用神经网络的价值评估
                leaf_value = float(value[0, 0])
            else:
                # 终局节点，直接评估
                leaf_value = self._evaluate_terminal(node.board)
            
            # 3. 反向传播
            for n in reversed(path):
                # 从当前节点的角度更新价值
                if n.current_color == self.color:
                    n.backup(leaf_value)
                else:
                    n.backup(-leaf_value)
        
        return root
    
    def _evaluate_terminal(self, board: Board) -> float:
        """评估终局状态"""
        # 简单的终局评估
        my_territory = 0
        opp_territory = 0
        
        for y in range(board.size):
            for x in range(board.size):
                stone = board.get_stone(x, y)
                if stone == self.color:
                    my_territory += 1
                elif stone == self.opponent_color:
                    opp_territory += 1
        
        # 归一化到[-1, 1]
        total = board.size * board.size
        score = (my_territory - opp_territory) / total
        
        return max(-1.0, min(1.0, score))
    
    def get_policy_output(self, board: Board, game_info: Dict[str, Any]) -> Dict[Tuple[int, int], float]:
        """
        获取策略网络的输出（用于分析和训练）
        
        Returns:
            每个合法位置的概率分布
        """
        # 提取特征
        features = self.feature_extractor.extract_features(board, self.color, self.board_history)
        features_batch = np.expand_dims(features, 0)
        
        # 获取预测
        policy, value = self.neural_net.predict(features_batch)
        
        # 转换为字典
        ko_point = game_info.get('ko_point')
        legal_moves = self.get_legal_moves(board, ko_point)
        
        policy_dict = {}
        for move in legal_moves:
            idx = move[1] * self.config.board_size + move[0]
            policy_dict[move] = float(policy[0, idx])
        
        # 归一化
        total = sum(policy_dict.values())
        if total > 0:
            for move in policy_dict:
                policy_dict[move] /= total
        
        return policy_dict
    
    def update_history(self, board: Board):
        """更新历史记录"""
        self.board_history.append(board.copy())
        
        # 保持固定长度
        if len(self.board_history) > self.config.history_length:
            self.board_history.pop(0)
    
    def get_analysis(self, board: Board, last_move: Optional[Tuple[int, int]] = None) -> str:
        """获取神经网络分析"""
        if self.neural_net.model is None:
            return "神经网络AI: 模型未加载，使用备用AI"
        
        # 获取神经网络评估
        features = self.feature_extractor.extract_features(board, self.color, self.board_history)
        features_batch = np.expand_dims(features, 0)
        
        policy, value = self.neural_net.predict(features_batch)
        
        win_prob = (float(value[0, 0]) + 1.0) / 2.0  # 转换到[0, 1]
        
        analysis = [
            "神经网络AI分析:",
            f"胜率评估: {win_prob:.1%}",
            f"局面价值: {float(value[0, 0]):.3f}",
            f"模拟次数: {self.config.num_simulations}",
            f"思考时间: {self.time_spent:.2f}秒"
        ]
        
        return "\n".join(analysis)