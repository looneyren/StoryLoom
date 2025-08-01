#!/usr/bin/env python3
"""
StoryLoom 数据结构定义
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any
from datetime import datetime


@dataclass
class Scene:
    """场景类"""
    number: int
    location: str
    time: str
    description: str
    dialogue: List[Dict[str, str]]


@dataclass
class Shot:
    """镜头类"""
    scene_number: int
    shot_number: int
    shot_type: str  # 特写、中景、远景等
    duration: str
    description: str
    camera_movement: str
    dialogue: str


@dataclass
class Character:
    """角色类"""
    name: str
    description: str
    personality: str
    appearance: str
    face_prompt: str  # 面部特写提示词
    full_body_prompt: str  # 全身照提示词


@dataclass
class ImagePrompt:
    """文生图提示词类"""
    shot_id: str
    full_prompt: str  # 完整版提示词(MJ风格,英文)
    full_prompt_cn: str  # 完整版提示词(中文版)
    simple_prompt: str  # 简单版提示词(英文)
    style: str
    technical_params: str


@dataclass 
class VisualStyle:
    """视觉风格类"""
    name: str
    description: str
    shot_characteristics: str  # 镜头特征
    color_palette: str  # 色彩风格
    lighting_style: str  # 光影风格
    character_style: str  # 人物风格
    background_style: str  # 背景风格


@dataclass
class TokenUsage:
    """Token使用统计"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    
    def add(self, usage_data):
        """添加使用量数据"""
        if hasattr(usage_data, 'prompt_tokens'):
            self.prompt_tokens += usage_data.prompt_tokens or 0
            self.completion_tokens += usage_data.completion_tokens or 0
            self.total_tokens += usage_data.total_tokens or 0


@dataclass
class UsageStats:
    """使用统计报表"""
    character_generation: TokenUsage = field(default_factory=TokenUsage)
    story_overview: TokenUsage = field(default_factory=TokenUsage)
    shooting_script: TokenUsage = field(default_factory=TokenUsage)
    storyboard: TokenUsage = field(default_factory=TokenUsage)
    image_prompts: TokenUsage = field(default_factory=TokenUsage)
    total: TokenUsage = field(default_factory=TokenUsage)
    api_calls: int = 0
    
    def add_usage(self, category: str, usage_data):
        """添加特定类别的使用量"""
        self.api_calls += 1
        category_usage = getattr(self, category)
        category_usage.add(usage_data)
        self.total.add(usage_data)
    
    def print_report(self):
        """打印使用统计报表"""
        print("\n" + "="*50)
        print("📊 Token 使用统计报表")
        print("="*50)
        
        categories = [
            ("角色生成", self.character_generation),
            ("故事概览", self.story_overview),
            ("拍摄脚本", self.shooting_script),
            ("分镜设计", self.storyboard),
            ("图像提示", self.image_prompts)
        ]
        
        for name, usage in categories:
            if usage.total_tokens > 0:
                print(f"🎭 {name:8} | 输入: {usage.prompt_tokens:5,} | 输出: {usage.completion_tokens:5,} | 总计: {usage.total_tokens:6,}")
        
        print("-" * 50)
        print(f"📈 总计消耗     | 输入: {self.total.prompt_tokens:5,} | 输出: {self.total.completion_tokens:5,} | 总计: {self.total.total_tokens:6,}")
        print(f"🔄 API调用次数: {self.api_calls}")
        print("="*50)


@dataclass
class ProjectTask:
    """项目任务信息"""
    task_id: str
    input_file: str
    output_dir: str
    style: str
    created_at: datetime
    custom_style_data: Dict = field(default_factory=dict)  # 自定义风格数据
    status: str = "pending"  # pending, processing, completed, failed
    progress: Dict[str, bool] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.progress:
            self.progress = {
                "scenes_parsed": False,
                "characters_extracted": False,
                "shooting_script_generated": False,
                "storyboard_created": False,
                "image_prompts_generated": False
            }