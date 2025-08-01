#!/usr/bin/env python3
"""
剧本改编工具 - 将原始剧本转换为拍摄脚本，生成分镜头，并创建文生图提示词
适用于动漫短片创作工作流程
"""

import argparse
import json
import os
import re
from typing import List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from openai import OpenAI

# 尝试导入python-dotenv，如果没有安装则跳过
try:
    from dotenv import load_dotenv
    load_dotenv()  # 加载.env文件
except ImportError:
    pass  # 如果没有安装python-dotenv，则跳过


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
    prompt: str
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


class ScriptAdapter:
    """剧本改编器主类"""
    
    # 内置视觉风格库
    VISUAL_STYLES = {
        "ghibli": VisualStyle(
            name="宫崎骏 / Studio Ghibli",
            description="温暖细腻的手绘风格，注重自然光影和情感表达",
            shot_characteristics="柔和的镜头运动，丰富的景深层次，强调环境氛围",
            color_palette="温暖自然色调，绿色和蓝色为主，柔和过渡",
            lighting_style="自然光影，金黄色暖光，逆光和侧光营造氛围",
            character_style="圆润的人物设计，大眼睛，表情丰富细腻",
            background_style="详细的自然景观，手绘质感，层次丰富"
        ),
        "shinkai": VisualStyle(
            name="新海诚",
            description="超现实的细腻画风，光影效果极致，情感浓郁",
            shot_characteristics="静态长镜头，强调空间感，细节极致",
            color_palette="高饱和度，蓝色和橙色对比，梦幻色彩",
            lighting_style="戏剧化光影，强烈的逆光，霞光和云层效果",
            character_style="写实风格，精致五官，情感表达细腻",
            background_style="照片级写实背景，城市景观，天空云彩极致细腻"
        ),
        "kyoani": VisualStyle(
            name="京都动画",
            description="清新唯美的校园风格，人物动作流畅自然",
            shot_characteristics="流畅的人物动作，日常生活化镜头，温馨氛围",
            color_palette="清新明亮，粉色和蓝色系，色彩柔和",
            lighting_style="柔和自然光，室内外光线真实，温暖舒适",
            character_style="可爱圆润，大眼睛，发色丰富，校服等日常服装",
            background_style="日式校园和街道，生活化场景，细节丰富"
        ),
        "pixar": VisualStyle(
            name="皮克斯 / Pixar",
            description="3D卡通风格，色彩鲜明，角色造型可爱",
            shot_characteristics="动态镜头，丰富的镜头语言，戏剧化构图",
            color_palette="鲜明对比，原色系为主，色彩饱满",
            lighting_style="戏剧化打光，强烈明暗对比，卡通化光影",
            character_style="夸张可爱的3D造型，圆润设计，表情夸张",
            background_style="简化几何形状，色彩鲜明的环境设计"
        ),
        "disney": VisualStyle(
            name="迪士尼经典",
            description="传统手绘动画风格，梦幻童话色彩",
            shot_characteristics="经典动画镜头语言，流畅转场，戏剧化表现",
            color_palette="梦幻色彩，童话般的色调，温暖明亮",
            lighting_style="童话式光影，魔法般的光效，温暖金光",
            character_style="经典卡通造型，夸张表情，童话角色设计",
            background_style="童话场景，梦幻城堡，魔法森林"
        ),
        "anime": VisualStyle(
            name="现代日式动漫",
            description="标准TV动画风格，人物鲜明，剧情导向",
            shot_characteristics="标准动画镜头切换，强调剧情节奏",
            color_palette="标准动画配色，人物发色丰富，对比明确",
            lighting_style="动画标准光影，cell-shading效果",
            character_style="标准动漫人物比例，大眼睛，发型夸张",
            background_style="简化的背景设计，重点突出人物"
        ),
        "realistic": VisualStyle(
            name="写实风格",
            description="接近真人电影的写实画风，注重细节和真实感",
            shot_characteristics="电影级镜头语言，写实构图，真实光影",
            color_palette="自然真实色调，接近摄影色彩",
            lighting_style="真实光源，自然光影变化，电影级打光",
            character_style="写实人物比例，真实五官，自然表情",
            background_style="真实环境还原，细节丰富，质感真实"
        ),
        "minimalist": VisualStyle(
            name="极简主义",
            description="简洁线条，纯色搭配，几何化设计",
            shot_characteristics="简洁构图，几何化镜头，留白艺术",
            color_palette="单色或双色搭配，高对比度，纯色块",
            lighting_style="简化光影，平面化处理，强调形状",
            character_style="几何化人物设计，简化特征，线条清晰",
            background_style="极简背景，几何形状，纯色或渐变"
        )
    }
    
    def __init__(self, api_key: str = None, base_url: str = None, model_name: str = None, style: str = None):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.base_url = base_url or os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')
        self.model_name = model_name or os.getenv('OPENAI_MODEL_NAME', 'gpt-3.5-turbo')
        self.style = style or os.getenv('DEFAULT_STYLE', 'anime')  # 支持从环境变量读取默认风格
        
        # 验证风格是否存在
        if self.style not in self.VISUAL_STYLES:
            print(f"⚠️ 警告：风格 '{self.style}' 不存在，使用默认风格 'anime'")
            self.style = "anime"
        
        self.current_style = self.VISUAL_STYLES[self.style]
        self.usage_stats = UsageStats()  # 初始化统计
        
        if self.api_key:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
        else:
            self.client = None

    @classmethod
    def list_styles(cls):
        """显示所有可用的视觉风格"""
        print("\n🎨 StoryLoom 可用视觉风格：\n")
        for key, style in cls.VISUAL_STYLES.items():
            print(f"🔸 {key}")
            print(f"   名称：{style.name}")
            print(f"   描述：{style.description}")
            print(f"   用法：--style={key}")
            print()
    
    def extract_characters(self, scenes: List[Scene]) -> List[Character]:
        """从场景中提取角色信息"""
        if self.client:
            # 使用AI智能分析角色
            return self._extract_characters_ai(scenes)
        else:
            # 基础模式：简单收集对话中的角色名
            characters = {}
            
            for scene in scenes:
                for dialogue in scene.dialogue:
                    char_name = dialogue['character']
                    if char_name not in characters:
                        characters[char_name] = {
                            'name': char_name,
                            'lines': [],
                            'scenes': []
                        }
                    characters[char_name]['lines'].append(dialogue['line'])
                    if scene.number not in characters[char_name]['scenes']:
                        characters[char_name]['scenes'].append(scene.number)
            
            character_list = []
            for char_name, char_data in characters.items():
                character = self._generate_character_basic(char_name, char_data)
                character_list.append(character)
            
            return character_list
    
    def _extract_characters_ai(self, scenes: List[Scene]) -> List[Character]:
        """使用AI智能分析和提取角色信息"""
        # 先转换场景为文本
        script_text = self._scenes_to_text(scenes)
        
        prompt = f"""
        你是专业的编剧和角色分析师，请从以下剧本中智能识别和提取所有真正的角色人物。
        
        请注意区分：
        1. **真正的角色名**：如“林小鱼”、“陈墨”、“苏苏”等人名
        2. **非角色内容**：描述性文本如“林小鱼的心跳加速”、“苏苏看到后直接评论”等
        
        剧本内容：
        {script_text}
        
        请返回JSON格式的角色列表，每个角色包含：
        - name: 角色名称
        - description: 人物描述（30-50字）
        - personality: 性格特征（20-30字）
        - key_lines: 代表性台词（3-5句）
        - scenes: 出现的主要场景描述
        
        请只返回JSON数组，不要其他内容。
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500,
                temperature=0.3  # 降低温度以获得更准确的结果
            )
            
            # 记录token使用
            if hasattr(response, 'usage'):
                self.usage_stats.add_usage('character_generation', response.usage)
            
            result_text = response.choices[0].message.content.strip()
            
            # 移除markdown标记
            if '```json' in result_text:
                result_text = result_text.replace('```json', '').replace('```', '')
            
            # 提取JSON部分
            json_start = result_text.find('[')
            json_end = result_text.rfind(']') + 1
            
            if json_start != -1 and json_end > json_start:
                json_content = result_text[json_start:json_end].strip()
                characters_data = json.loads(json_content)
                
                character_list = []
                for char_data in characters_data:
                    character = self._create_character_from_ai_data(char_data)
                    character_list.append(character)
                
                return character_list
            else:
                raise ValueError("无法解析AI返回的角色数据")
                
        except Exception as e:
            print(f"AI角色分析失败: {e}，使用基础模式")
            return self._extract_characters_basic_fallback(scenes)
    
    def _create_character_from_ai_data(self, char_data: dict) -> Character:
        """根据AI分析结果创建角色对象"""
        name = char_data.get('name', '未知角色')
        description = char_data.get('description', '')
        personality = char_data.get('personality', '')
        
        # 生成风格化的图像提示词
        appearance = f"符合{self.current_style.name}风格的角色设计"
        
        # 使用AI生成更详细的外观和提示词
        if self.client:
            try:
                detailed_info = self._generate_character_details_ai(name, description, personality)
                appearance = detailed_info.get('appearance', appearance)
                face_prompt = detailed_info.get('face_prompt', f"{name} portrait, {self.current_style.character_style}")
                full_body_prompt = detailed_info.get('full_body_prompt', f"{name} full body, {self.current_style.character_style}")
            except:
                face_prompt = f"{name} character portrait, {self.current_style.character_style}, {self.current_style.lighting_style}, high quality"
                full_body_prompt = f"{name} full body character design, {self.current_style.character_style}, {self.current_style.color_palette}"
        else:
            face_prompt = f"{name} character portrait, {self.current_style.character_style}, {self.current_style.lighting_style}, high quality"
            full_body_prompt = f"{name} full body character design, {self.current_style.character_style}, {self.current_style.color_palette}"
        
        return Character(
            name=name,
            description=description,
            personality=personality,
            appearance=appearance,
            face_prompt=face_prompt,
            full_body_prompt=full_body_prompt
        )
    
    def _generate_character_details_ai(self, name: str, description: str, personality: str) -> dict:
        """使用AI生成角色详细信息"""
        prompt = f"""
        你是专业的角色设计师，请为以下角色设计详细外观和图像提示词。
        
        角色信息：
        - 名称：{name}
        - 描述：{description}
        - 性格：{personality}
        
        请以{self.current_style.name}的视觉风格为基准，生成以下内容：
        
        1. 外观特征（50字以内）- 身高体型、发色、服装风格等
        2. 面部特写提示词（英文）- 用于AI绘画的面部特写
        3. 全身照提示词（英文）- 用于AI绘画的全身像
        
        请按JSON格式输出：
        {{
            "appearance": "外观特征",
            "face_prompt": "face prompt in English",
            "full_body_prompt": "full body prompt in English"
        }}
        """
        
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=600,
            temperature=0.7
        )
        
        # 记录token使用
        if hasattr(response, 'usage'):
            self.usage_stats.add_usage('character_generation', response.usage)
        
        result_text = response.choices[0].message.content.strip()
        json_start = result_text.find('{')
        json_end = result_text.rfind('}') + 1
        
        if json_start != -1 and json_end > json_start:
            return json.loads(result_text[json_start:json_end])
        else:
            raise ValueError("无法解析AI返回的详细信息")
    
    def _extract_characters_basic_fallback(self, scenes: List[Scene]) -> List[Character]:
        """基础模式的角色提取（当AI失败时使用）"""
        characters = {}
        
        for scene in scenes:
            for dialogue in scene.dialogue:
                char_name = dialogue['character']
                if char_name not in characters:
                    characters[char_name] = {
                        'name': char_name,
                        'lines': [],
                        'scenes': []
                    }
                characters[char_name]['lines'].append(dialogue['line'])
                if scene.number not in characters[char_name]['scenes']:
                    characters[char_name]['scenes'].append(scene.number)
        
        character_list = []
        for char_name, char_data in characters.items():
            character = self._generate_character_basic(char_name, char_data)
            character_list.append(character)
        
        return character_list
    
    def _generate_character_ai(self, char_name: str, char_data: dict, scenes: List[Scene]) -> Character:
        """使用AI生成角色详细信息"""
        lines_text = "\n".join(char_data['lines'][:10])  # 限制台词数量
        scenes_text = ", ".join([f"第{s}场" for s in char_data['scenes']])
        
        prompt = f"""
        你是专业的角色设计师和编剧，请基于以下信息为角色 "{char_name}" 创建详细的人物档案。
        
        角色台词示例：
        {lines_text}
        
        出现场次：{scenes_text}
        
        请以{self.current_style.name}的视觉风格为基准，生成以下内容：
        
        1. 人物描述（50字以内）- 基本身份、年龄、职业等
        2. 性格特征（30字以内）- 主要性格特点
        3. 外貌特征（50字以内）- 身高体型、发色、服装风格等，符合{self.current_style.name}风格
        4. 面部特写提示词（英文）- 用于AI绘画的面部特写，体现{self.current_style.name}特色
        5. 全身照提示词（英文）- 用于AI绘画的全身像，包含服装和姿态
        
        请按JSON格式输出：
        {{
            "description": "人物描述",
            "personality": "性格特征", 
            "appearance": "外貌特征",
            "face_prompt": "face close-up prompt in English",
            "full_body_prompt": "full body prompt in English"
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                temperature=0.7
            )
            
            # 记录token使用
            if hasattr(response, 'usage'):
                self.usage_stats.add_usage('character_generation', response.usage)
            
            result_text = response.choices[0].message.content.strip()
            # 提取JSON部分
            json_start = result_text.find('{')
            json_end = result_text.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                import json
                char_info = json.loads(result_text[json_start:json_end])
                
                return Character(
                    name=char_name,
                    description=char_info.get('description', ''),
                    personality=char_info.get('personality', ''),
                    appearance=char_info.get('appearance', ''),
                    face_prompt=f"{char_info.get('face_prompt', '')}, {self.current_style.character_style}, {self.current_style.lighting_style}",
                    full_body_prompt=f"{char_info.get('full_body_prompt', '')}, {self.current_style.character_style}, {self.current_style.color_palette}"
                )
            else:
                raise ValueError("无法解析AI返回的角色数据")
                
        except Exception as e:
            print(f"AI角色生成失败: {e}，使用基础模式")
            return self._generate_character_basic(char_name, char_data)
    
    def _generate_character_basic(self, char_name: str, char_data: dict) -> Character:
        """基础角色信息生成"""
        line_count = len(char_data['lines'])
        scene_count = len(char_data['scenes'])
        
        # 基于台词分析性格
        lines_text = " ".join(char_data['lines']).lower()
        if any(word in lines_text for word in ['哈哈', '笑', '开心', '高兴']):
            personality = "开朗活泼"
        elif any(word in lines_text for word in ['？', '吗', '呢', '什么']):
            personality = "好奇好问"
        elif any(word in lines_text for word in ['！', '啊', '哇']):
            personality = "情感丰富"
        else:
            personality = "性格温和"
        
        return Character(
            name=char_name,
            description=f"剧中重要角色，共出现{scene_count}个场景，有{line_count}句台词",
            personality=personality,
            appearance=f"符合{self.current_style.name}风格的角色设计",
            face_prompt=f"{char_name} character portrait, {self.current_style.character_style}, {self.current_style.lighting_style}, high quality anime face",
            full_body_prompt=f"{char_name} full body character design, {self.current_style.character_style}, {self.current_style.color_palette}, standing pose"
        )

    def parse_original_script(self, script_content: str) -> List[Scene]:
        """解析原始剧本（使用AI智能解析）"""
        if self.client:
            return self._parse_script_ai(script_content)
        else:
            return self._parse_script_basic(script_content)
    
    def _parse_script_ai(self, script_content: str) -> List[Scene]:
        """使用AI智能解析剧本结构"""
        prompt = f"""
        你是专业的剧本分析师，请将以下文本解析为结构化的剧本场景。

        请注意区分：
        1. **真正的对话**：角色名 + 冒号 + 台词，如 "林小鱼：你好"
        2. **非对话内容**：叙述性文本，如 "林小鱼的心跳加速：这颜值..."
        3. **场景分割**：根据情节变化、地点转换等分割场景

        原始文本：
        {script_content}

        请返回JSON格式的场景列表，每个场景包含：
        - number: 场景编号
        - location: 场景地点/标题
        - time: 时间（白天/晚上/下午等）
        - description: 场景描述（叙述性内容）
        - dialogue: 对话列表，每个包含 character 和 line

        请只返回JSON数组，不要其他内容。
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2500,
                temperature=0.2  # 低温度以获得更准确的结构化结果
            )
            
            # 记录token使用
            if hasattr(response, 'usage'):
                self.usage_stats.add_usage('character_generation', response.usage)
            
            result_text = response.choices[0].message.content.strip()
            
            # 移除markdown标记
            if '```json' in result_text:
                result_text = result_text.replace('```json', '').replace('```', '')
            
            # 提取JSON部分  
            json_start = result_text.find('[')
            json_end = result_text.rfind(']') + 1
            
            if json_start != -1 and json_end > json_start:
                json_content = result_text[json_start:json_end].strip()
                scenes_data = json.loads(json_content)
                
                scenes = []
                for scene_data in scenes_data:
                    dialogue_list = []
                    for dlg in scene_data.get('dialogue', []):
                        if isinstance(dlg, dict) and 'character' in dlg and 'line' in dlg:
                            dialogue_list.append({
                                'character': str(dlg['character']).strip(),
                                'line': str(dlg['line']).strip()
                            })
                    
                    scene = Scene(
                        number=int(scene_data.get('number', len(scenes) + 1)),
                        location=str(scene_data.get('location', f'第{len(scenes) + 1}场')),
                        time=str(scene_data.get('time', '白天')),
                        description=str(scene_data.get('description', '')),
                        dialogue=dialogue_list
                    )
                    scenes.append(scene)
                
                return scenes
            else:
                raise ValueError("无法解析AI返回的场景数据")
                
        except Exception as e:
            print(f"AI剧本解析失败: {e}，使用基础模式")
            return self._parse_script_basic(script_content)
    
    def _parse_script_basic(self, script_content: str) -> List[Scene]:
        """基础模式的剧本解析（当AI不可用时）"""
        # 基础模式：按章节分割，不做复杂的对话解析
        lines = script_content.split('\n')
        scenes = []
        current_scene = None
        scene_number = 1
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 识别章节标题作为场景分割
            if line.startswith('## ') or line.startswith('# '):
                if current_scene:
                    scenes.append(current_scene)
                
                current_scene = Scene(
                    number=scene_number,
                    location=line.replace('#', '').strip(),
                    time="白天",
                    description="",
                    dialogue=[]
                )
                scene_number += 1
            elif current_scene:
                # 在基础模式下，所有内容都作为描述
                current_scene.description += line + " "
        
        if current_scene:
            scenes.append(current_scene)
        elif not scenes:  # 如果没有找到章节标题，创建一个默认场景
            scenes.append(Scene(
                number=1,
                location="完整剧本",
                time="白天",
                description=script_content,
                dialogue=[]
            ))
        
        return scenes

    def convert_to_shooting_script(self, scenes: List[Scene]) -> str:
        """将剧本转换为拍摄脚本"""
        if not self.api_key:
            return self._convert_to_shooting_script_basic(scenes)
        
        try:
            prompt = f"""
            你是一位经验丰富的编剧和导演，擅长将传统剧本改编为具有网络化特色的动漫短片脚本。
            
            请将以下剧本场景转换为现代网络用户喜爱的拍摄脚本格式，要求：
            
            1. **网感融入**：
               - 识别剧本中的情感爽点和戏剧冲突
               - 加入适合的网络梗和流行元素（但不要过度）
               - 考虑短视频用户的观看习惯
            
            2. **二次创作优化**：
               - 强化戏剧张力和节奏感
               - 增加视觉冲击力的描述
               - 优化对话，使其更符合年轻观众的语言习惯
            
            3. **标准格式包含**：
               - 场景设置（时间、地点、氛围营造）
               - 角色动作和情绪描述
               - 网络化的对话标注
               - 镜头语言建议
            
            原始场景内容：
            {self._scenes_to_text(scenes)}
            
            请按照动漫短片制作标准输出，注重情感共鸣和网络传播效果。
            """
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.8
            )
            
            # 记录token使用
            if hasattr(response, 'usage'):
                self.usage_stats.add_usage('shooting_script', response.usage)
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"API调用失败，使用基础转换: {e}")
            return self._convert_to_shooting_script_basic(scenes)

    def _convert_to_shooting_script_basic(self, scenes: List[Scene]) -> str:
        """基础拍摄脚本转换（不使用AI）"""
        script = "# 拍摄脚本\n\n"
        
        for scene in scenes:
            script += f"## 第{scene.number}场\n\n"
            script += f"**地点：** {scene.location}\n"
            script += f"**时间：** {scene.time}\n\n"
            script += f"**场景描述：** {scene.description.strip()}\n\n"
            
            if scene.dialogue:
                script += "**对话：**\n\n"
                for dialogue in scene.dialogue:
                    script += f"- **{dialogue['character']}：** {dialogue['line']}\n"
            
            script += "\n---\n\n"
        
        return script

    def generate_storyboard(self, scenes: List[Scene]) -> List[Shot]:
        """生成分镜头"""
        if not self.api_key:
            return self._generate_storyboard_basic(scenes)
        
        try:
            shots = []
            shot_counter = 1
            
            for scene in scenes:
                scene_shots = self._generate_scene_shots_ai(scene, shot_counter)
                shots.extend(scene_shots)
                shot_counter += len(scene_shots)
            
            return shots
            
        except Exception as e:
            print(f"AI分镜生成失败，使用基础模式: {e}")
            return self._generate_storyboard_basic(scenes)
    
    def _generate_storyboard_basic(self, scenes: List[Scene]) -> List[Shot]:
        """基础分镜生成"""
        shots = []
        shot_counter = 1
        
        for scene in scenes:
            scene_shots = self._generate_scene_shots(scene, shot_counter)
            shots.extend(scene_shots)
            shot_counter += len(scene_shots)
        
        return shots

    def _generate_scene_shots_ai(self, scene: Scene, start_shot_num: int) -> List[Shot]:
        """使用AI生成场景分镜头"""
        dialogue_text = "\n".join([f"{d['character']}：{d['line']}" for d in scene.dialogue])
        
        prompt = f"""
        你是一位专业的动漫导演，擅长创造具有网络传播力的分镜头设计。
        
        请为以下场景设计分镜头方案，要求：
        
        1. **导演思维**：
           - 分析场景的情感高潮点和视觉爽点
           - 设计具有冲击力的镜头语言
           - 考虑短视频用户的观看节奏
        
        2. **网络化表达**：
           - 突出戏剧张力，适合切片传播
           - 设计容易引起弹幕互动的镜头
           - 考虑表情包潜质的画面
        
        3. **分镜要求**：
           - 每个镜头指定类型（特写/中景/远景/过肩镜头等）
           - 标注镜头运动（推拉摇移、升降等）
           - 估算合理时长
           - 描述画面重点和情绪表达
        
        场景信息：
        地点：{scene.location}
        描述：{scene.description}
        对话：
        {dialogue_text}
        
        请按JSON格式输出分镜列表，格式如下：
        [{{
            "shot_type": "镜头类型",
            "duration": "时长",
            "description": "画面描述",
            "camera_movement": "镜头运动",
            "dialogue": "对话内容",
            "emotion_focus": "情感重点"
        }}]
        
        注意：要体现导演的专业判断，创造有网感的视觉语言。
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500,
                temperature=0.8
            )
            
            # 记录token使用
            if hasattr(response, 'usage'):
                self.usage_stats.add_usage('storyboard', response.usage)
            
            result_text = response.choices[0].message.content.strip()
            # 提取JSON部分
            json_start = result_text.find('[')
            json_end = result_text.rfind(']') + 1
            
            if json_start != -1 and json_end > json_start:
                shots_data = json.loads(result_text[json_start:json_end])
                
                shots = []
                for i, shot_data in enumerate(shots_data):
                    shots.append(Shot(
                        scene_number=scene.number,
                        shot_number=start_shot_num + i,
                        shot_type=shot_data.get('shot_type', '中景'),
                        duration=shot_data.get('duration', '3秒'),
                        description=shot_data.get('description', ''),
                        camera_movement=shot_data.get('camera_movement', '静止'),
                        dialogue=shot_data.get('dialogue', '')
                    ))
                
                return shots
            else:
                raise ValueError("无法解析AI返回的分镜数据")
                
        except Exception as e:
            print(f"AI分镜生成失败: {e}，使用基础分镜")
            return self._generate_scene_shots(scene, start_shot_num)
    
    def _generate_scene_shots(self, scene: Scene, start_shot_num: int) -> List[Shot]:
        """为单个场景生成分镜头（基础版本）"""
        shots = []
        
        # 网络化的基础分镜逻辑
        # 1. 场景建立镜头 - 注重视觉冲击
        shots.append(Shot(
            scene_number=scene.number,
            shot_number=start_shot_num,
            shot_type="远景",
            duration="2-3秒",
            description=f"快速建立场景：{scene.location}，营造氛围感",
            camera_movement="快速推进",
            dialogue=""
        ))
        
        shot_num = start_shot_num + 1
        
        # 2. 根据对话生成镜头 - 增加戏剧性
        for i, dialogue in enumerate(scene.dialogue):
            if i == 0:
                # 第一句话用特写突出
                shot_type = "特写"
                camera_movement = "缓慢推进"
            elif "？" in dialogue['line'] or "！" in dialogue['line']:
                # 疑问和感叹用特写
                shot_type = "特写" 
                camera_movement = "震动" if "！" in dialogue['line'] else "静止"
            else:
                shot_type = "中景" if i % 2 == 0 else "过肩镜头"
                camera_movement = "轻微摇摆"
            
            shots.append(Shot(
                scene_number=scene.number,
                shot_number=shot_num,
                shot_type=shot_type,
                duration="2-4秒",
                description=f"{dialogue['character']}说话，表情生动",
                camera_movement=camera_movement,
                dialogue=dialogue['line']
            ))
            shot_num += 1
        
        # 3. 情感高潮镜头
        if scene.dialogue:
            shots.append(Shot(
                scene_number=scene.number,
                shot_number=shot_num,
                shot_type="特写",
                duration="1-2秒",
                description="情感反应镜头，捕捉微表情",
                camera_movement="静止",
                dialogue=""
            ))
        
        return shots

    def generate_image_prompts(self, shots: List[Shot]) -> List[ImagePrompt]:
        """生成文生图提示词"""
        prompts = []
        
        for shot in shots:
            prompt_text = self._create_image_prompt(shot)
            
            prompts.append(ImagePrompt(
                shot_id=f"S{shot.scene_number:02d}_{shot.shot_number:03d}",
                prompt=prompt_text,
                style="anime style, high quality, detailed",
                technical_params="16:9 aspect ratio, 4K resolution"
            ))
        
        return prompts

    def _create_image_prompt(self, shot: Shot) -> str:
        """创建单个镜头的图像提示词"""
        if not self.api_key:
            return self._create_basic_image_prompt(shot)
        
        try:
            prompt = f"""
            你是专业的{self.current_style.name}风格美术指导，擅长创造具有这种风格特色的视觉作品。
            
            请为以下分镜头创建详细的文生图提示词：
            
            镜头信息：
            - 镜头类型：{shot.shot_type}
            - 场景描述：{shot.description}
            - 对话内容：{shot.dialogue}
            - 镜头运动：{shot.camera_movement}
            
            风格要求（{self.current_style.name}）：
            - 风格描述：{self.current_style.description}
            - 镜头特征：{self.current_style.shot_characteristics}
            - 色彩风格：{self.current_style.color_palette}
            - 光影风格：{self.current_style.lighting_style}
            - 背景风格：{self.current_style.background_style}
            
            创作要求：
            
            1. **视觉风格**：
               - 严格按照{self.current_style.name}的特色进行创作
               - 体现该风格的色彩和光影特点
               - 保持风格的一致性和专业性
            
            2. **构图设计**：
               - 符合{shot.shot_type}的专业构图
               - 融入{self.current_style.name}的镜头语言特色
               - 突出情感表达和戏剧张力
            
            3. **技术细节**：
               - 严格遵循{self.current_style.name}的视觉标准
               - 适合AI图像生成的描述方式
               - 重点体现该风格的独特魅力
            
            请生成简洁而专业的英文提示词，重点突出{self.current_style.name}风格的视觉特色。
            """
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.8
            )
            
            # 记录token使用
            if hasattr(response, 'usage'):
                self.usage_stats.add_usage('image_prompts', response.usage)
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"生成图像提示词失败，使用基础模式: {e}")
            return self._create_basic_image_prompt(shot)

    def _create_basic_image_prompt(self, shot: Shot) -> str:
        """基于风格的基础图像提示词生成"""
        # 基础风格元素
        base_elements = [
            f"{self.current_style.name} style",
            self.current_style.color_palette.lower(),
            self.current_style.lighting_style.lower(),
            "high quality",
            "detailed"
        ]
        
        # 根据镜头类型设定构图
        if "特写" in shot.shot_type:
            base_elements.extend([
                "close-up shot",
                "detailed facial expression",
                "emotional focus",
                "shallow depth of field"
            ])
        elif "远景" in shot.shot_type:
            base_elements.extend([
                "wide establishing shot",
                "detailed background",
                "cinematic composition"
            ])
        elif "过肩" in shot.shot_type:
            base_elements.extend([
                "over shoulder shot",
                "conversation angle",
                "depth composition"
            ])
        else:
            base_elements.extend([
                "medium shot",
                "balanced composition"
            ])
        
        # 场景环境判断
        if "室内" in shot.description or "房间" in shot.description or "咖啡厅" in shot.description:
            base_elements.extend(["indoor scene", "warm lighting"])
        elif "室外" in shot.description or "街道" in shot.description or "公园" in shot.description:
            base_elements.extend(["outdoor scene", "natural lighting"])
        
        # 情绪和氛围
        if "美" in shot.description or "漫" in shot.description:
            base_elements.extend(["romantic atmosphere", "soft lighting"])
        if "惊讶" in shot.dialogue or "！" in shot.dialogue:
            base_elements.extend(["dynamic expression", "dramatic lighting"])
        if "笑" in shot.description or "开心" in shot.description:
            base_elements.extend(["cheerful mood", "bright colors"])
        
        # 风格化元素
        base_elements.extend([
            self.current_style.shot_characteristics.lower(),
            self.current_style.background_style.lower()
        ])
        
        # 技术参数
        technical_params = [
            "16:9 aspect ratio",
            "4K resolution",
            f"{self.current_style.name} animation quality"
        ]
        
        # 根据对话内容添加特定元素
        if shot.dialogue:
            if "天气" in shot.dialogue:
                base_elements.append("weather discussion scene")
            if "约会" in shot.dialogue:
                base_elements.append("romantic date scene")
            if "美" in shot.dialogue:
                base_elements.append("compliment scene with blushing")
        
        # 组合所有元素
        all_elements = base_elements + technical_params
        prompt = ", ".join(all_elements)
        
        # 添加场景描述
        if shot.description:
            prompt += f", {shot.description}"
        
        return prompt

    def _is_dialogue_line(self, line: str) -> bool:
        """判断一行文本是否是对话"""
        # 排除明显的叙述性文本
        line_lower = line.lower()
        
        # 如果包含这些词汇，很可能是叙述而不是对话
        narrative_indicators = [
            '这天', '那天', '突然', '接着', '然后', '于是', '后来', '同时',
            '第二天', '一周后', '三个月后', '就在', '意外', '发生',
            '根据', '建议', '目标', '作战', '计划', '攻略'
        ]
        
        for indicator in narrative_indicators:
            if indicator in line:
                return False
        
        # 如果冒号前的内容太长（超过20个字符），可能是叙述
        colon_pos = line.find('：') if '：' in line else line.find(':')
        if colon_pos > 20:
            return False
        
        return True
    
    def _is_valid_character_name(self, name: str) -> bool:
        """判断是否是有效的角色名"""
        # 角色名通常比较短，不包含复杂描述
        if len(name) > 15:  # 角色名不应该太长
            return False
        
        # 排除包含明显叙述词汇的文本
        invalid_patterns = [
            '这天', '那天', '突然', '正在', '刚刚', '已经', '根据',
            '建议', '目标', '作战', '计划', '攻略', '与此同时',
            '就在', '意外', '发生', '第二天', '一周后', '三个月后'
        ]
        
        for pattern in invalid_patterns:
            if pattern in name:
                return False
        
        # 角色名通常是简单的中文姓名或称谓
        return True
    
    def _scenes_to_text(self, scenes: List[Scene]) -> str:
        """将场景列表转换为文本"""
        text = ""
        for scene in scenes:
            text += f"第{scene.number}场 - {scene.location}\n"
            text += f"描述：{scene.description}\n"
            for dialogue in scene.dialogue:
                text += f"{dialogue['character']}：{dialogue['line']}\n"
            text += "\n"
        return text

    def save_partial_results(self, output_file: str, step: str, **kwargs):
        """逐步保存结果到Markdown文件"""
        # 如果文件不存在，创建基本结构
        if not os.path.exists(output_file):
            header = f"""# StoryLoom 输出结果

生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
视觉风格：{self.current_style.name}
状态：正在处理...

"""
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(header)
        
        # 根据步骤更新内容
        if step == "scenes":
            self._append_scenes_section(output_file, kwargs.get('scenes', []))
        elif step == "characters":
            self._append_characters_section(output_file, kwargs.get('characters', []))
        elif step == "shooting_script":
            self._append_shooting_script_section(output_file, kwargs.get('shooting_script', ''))
        elif step == "storyboard":
            self._append_storyboard_section(output_file, kwargs.get('shots', []))
        elif step == "image_prompts":
            self._append_image_prompts_section(output_file, kwargs.get('image_prompts', []))
        elif step == "complete":
            self._update_completion_status(output_file)
            
    def _append_scenes_section(self, output_file: str, scenes: List[Scene]):
        """添加场景信息部分"""
        content = f"\n## 0. 场景结构\n\n"
        for scene in scenes:
            content += f"**第{scene.number}场** - {scene.location}\n"
            if scene.description.strip():
                content += f"  描述：{scene.description.strip()}\n"
            if scene.dialogue:
                content += f"  角色：{', '.join(set([d['character'] for d in scene.dialogue]))}\n"
            content += "\n"
        content += "---\n\n"
        
        with open(output_file, 'a', encoding='utf-8') as f:
            f.write(content)
    
    def _append_characters_section(self, output_file: str, characters: List[Character]):
        """添加角色信息部分"""
        content = "## 1. 演员表与角色设定\n\n"
        
        if characters:
            for char in characters:
                content += f"### {char.name}\n\n"
                content += f"**人物描述：** {char.description}\n\n"
                content += f"**性格特征：** {char.personality}\n\n"
                content += f"**外貌特征：** {char.appearance}\n\n"
                content += f"**面部特写提示词：** `{char.face_prompt}`\n\n"
                content += f"**全身照提示词：** `{char.full_body_prompt}`\n\n"
                content += "---\n\n"
        else:
            content += "暂无角色信息\n\n"
            
        with open(output_file, 'a', encoding='utf-8') as f:
            f.write(content)
            
    def _append_shooting_script_section(self, output_file: str, shooting_script: str):
        """添加拍摄脚本部分"""
        content = f"## 2. 拍摄脚本\n\n{shooting_script}\n\n"
        
        with open(output_file, 'a', encoding='utf-8') as f:
            f.write(content)
            
    def _append_storyboard_section(self, output_file: str, shots: List[Shot]):
        """添加分镜头表部分"""
        content = "## 3. 分镜头表\n\n| 场次 | 镜头号 | 镜头类型 | 时长 | 描述 | 镜头运动 | 对话 |\n|------|--------|----------|------|------|----------|------|\n"
        
        for shot in shots:
            content += f"| {shot.scene_number} | {shot.shot_number} | {shot.shot_type} | {shot.duration} | {shot.description} | {shot.camera_movement} | {shot.dialogue} |\n"
        
        content += "\n"
        
        with open(output_file, 'a', encoding='utf-8') as f:
            f.write(content)
            
    def _append_image_prompts_section(self, output_file: str, image_prompts: List[ImagePrompt]):
        """添加图像提示词部分"""
        content = "## 4. 文生图提示词\n\n"
        
        for prompt in image_prompts:
            content += f"### 镜头 {prompt.shot_id}\n\n"
            content += f"**提示词：** {prompt.prompt}\n\n"
            content += f"**风格：** {prompt.style}\n\n"
            content += f"**技术参数：** {prompt.technical_params}\n\n"
            content += "---\n\n"
            
        with open(output_file, 'a', encoding='utf-8') as f:
            f.write(content)
            
    def _update_completion_status(self, output_file: str):
        """更新完成状态"""
        # 读取现有内容
        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 更新状态
        content = content.replace('状态：正在处理...', f'状态：完成 - {datetime.now().strftime("%H:%M:%S")}')
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def save_to_markdown(self, output_file: str, scenes: List[Scene], 
                        shooting_script: str, shots: List[Shot], 
                        image_prompts: List[ImagePrompt], characters: List[Character] = None):
        """保存所有结果到Markdown文件（兼容旧版本）"""
        content = f"""# StoryLoom 输出结果

生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
视觉风格：{self.current_style.name}

## 1. 演员表与角色设定

"""

        # 添加角色信息
        if characters:
            for char in characters:
                content += f"### {char.name}\n\n"
                content += f"**人物描述：** {char.description}\n\n"
                content += f"**性格特征：** {char.personality}\n\n"
                content += f"**外貌特征：** {char.appearance}\n\n"
                content += f"**面部特写提示词：** `{char.face_prompt}`\n\n"
                content += f"**全身照提示词：** `{char.full_body_prompt}`\n\n"
                content += "---\n\n"
        else:
            content += "暂无角色信息\n\n"

        content += f"""## 2. 拍摄脚本

{shooting_script}

## 3. 分镜头表

| 场次 | 镜头号 | 镜头类型 | 时长 | 描述 | 镜头运动 | 对话 |
|------|--------|----------|------|------|----------|------|
"""
        
        for shot in shots:
            content += f"| {shot.scene_number} | {shot.shot_number} | {shot.shot_type} | {shot.duration} | {shot.description} | {shot.camera_movement} | {shot.dialogue} |\n"
        
        content += "\n## 4. 文生图提示词\n\n"
        
        for prompt in image_prompts:
            content += f"### 镜头 {prompt.shot_id}\n\n"
            content += f"**提示词：** {prompt.prompt}\n\n"
            content += f"**风格：** {prompt.style}\n\n"
            content += f"**技术参数：** {prompt.technical_params}\n\n"
            content += "---\n\n"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)

    def process_script(self, input_file: str, output_file: str):
        """处理完整的剧本改编流程（逐步保存）"""
        ai_mode = "AI增强" if self.api_key else "基础"
        print(f"🧶 启动StoryLoom - {ai_mode}模式")
        print(f"🎨 视觉风格：{self.current_style.name}")
        print(f"💾 逐步保存模式：{output_file}")
        
        print("正在读取原始剧本...")
        with open(input_file, 'r', encoding='utf-8') as f:
            script_content = f.read()
        
        print("正在解析剧本结构...")
        scenes = self.parse_original_script(script_content)
        print(f"解析到 {len(scenes)} 个场景")
        # 立即保存场景信息
        self.save_partial_results(output_file, "scenes", scenes=scenes)
        print(f"✓ 已保存场景结构")
        
        print("正在分析角色信息...")
        characters = self.extract_characters(scenes)
        print(f"识别到 {len(characters)} 个角色")
        # 立即保存角色信息
        self.save_partial_results(output_file, "characters", characters=characters)
        print(f"✓ 已保存角色设定")
        
        print("正在生成网络化拍摄脚本...")
        shooting_script = self.convert_to_shooting_script(scenes)
        # 立即保存拍摄脚本
        self.save_partial_results(output_file, "shooting_script", shooting_script=shooting_script)
        print(f"✓ 已保存拍摄脚本")
        
        print("正在设计导演分镜头...")
        shots = self.generate_storyboard(scenes)
        print(f"生成 {len(shots)} 个分镜头")
        # 立即保存分镜头表
        self.save_partial_results(output_file, "storyboard", shots=shots)
        print(f"✓ 已保存分镜头表")
        
        print("正在创建风格化文生图提示词...")
        image_prompts = self.generate_image_prompts(shots)
        # 立即保存图像提示词
        self.save_partial_results(output_file, "image_prompts", image_prompts=image_prompts)
        print(f"✓ 已保存图像提示词")
        
        # 标记为完成状态
        self.save_partial_results(output_file, "complete")
        
        print(f"✨ 处理完成！")
        print(f"📝 结果已保存到：{output_file}")
        print(f"🎭 共 {len(characters)} 个角色，{len(scenes)} 个场景，{len(shots)} 个镜头")
        print(f"🎨 生成 {len(image_prompts)} 个{self.current_style.name}风格提示词")
        
        # 显示token使用统计
        if self.api_key and self.usage_stats.total.total_tokens > 0:
            self.usage_stats.print_report()


def main():
    parser = argparse.ArgumentParser(
        description='🧶 StoryLoom - 故事织机：将剧本编织成完整的视觉制作方案',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法：
  # 基础使用
  %(prog)s script.txt
  
  # 使用宫崎骏风格
  %(prog)s script.txt --style=ghibli -o output.md
  
  # 查看所有可用风格
  %(prog)s --style-list
  
  # AI增强模式（优先使用.env文件配置）
  %(prog)s script.txt --api-key=your-key --style=shinkai

环境变量配置：
  复制 .env.example 为 .env 并填入您的API配置

支持的视觉风格：
  ghibli, shinkai, kyoani, pixar, disney, anime, realistic, minimalist
        """
    )
    
    parser.add_argument('input', nargs='?', help='输入剧本文件路径')
    parser.add_argument('-o', '--output', default='output.md', help='输出Markdown文件路径')
    parser.add_argument('--style', default='anime', help='视觉风格 (默认: anime)')
    parser.add_argument('--style-list', action='store_true', help='显示所有可用的视觉风格')
    parser.add_argument('--api-key', help='OpenAI API密钥')
    parser.add_argument('--base-url', help='API基础URL（支持兼容OpenAI的服务）')
    parser.add_argument('--model', help='模型名称（默认：gpt-3.5-turbo）')
    
    args = parser.parse_args()
    
    # 显示风格列表
    if args.style_list:
        ScriptAdapter.list_styles()
        return
    
    # 检查输入文件
    if not args.input:
        parser.error("需要提供输入剧本文件路径")
    
    if not os.path.exists(args.input):
        print(f"❌ 错误：输入文件 {args.input} 不存在")
        return
    
    # 创建适配器并处理
    try:
        adapter = ScriptAdapter(
            api_key=args.api_key, 
            base_url=args.base_url,
            model_name=args.model,
            style=args.style
        )
        adapter.process_script(args.input, args.output)
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断操作")
    except Exception as e:
        print(f"❌ 处理过程中出现错误: {e}")
        print("请检查输入文件格式或网络连接")


if __name__ == '__main__':
    main()