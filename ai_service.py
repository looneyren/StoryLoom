#!/usr/bin/env python3
"""
StoryLoom AI服务模块
"""

import json
import os
from typing import List, Dict, Any
from openai import OpenAI

from models import Scene, Character, Shot, ImagePrompt, UsageStats, VisualStyle


class AIService:
    """AI服务类，处理所有与大模型相关的操作"""
    
    def __init__(self, api_key: str = None, base_url: str = None, model_name: str = None):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.base_url = base_url or os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')
        self.model_name = model_name or os.getenv('OPENAI_MODEL_NAME', 'gpt-3.5-turbo')
        self.usage_stats = UsageStats()
        
        if self.api_key:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
        else:
            self.client = None
    
    def is_available(self) -> bool:
        """检查AI服务是否可用"""
        return self.client is not None
    
    def parse_script(self, script_content: str) -> List[Scene]:
        """使用AI解析剧本结构"""
        if not self.is_available():
            raise Exception("AI服务不可用")
        
        prompt = f"""请将以下剧本文本解析为JSON格式的场景列表。

原始文本：
{script_content}

要求：
1. 识别场景分割点（地点变化、时间跳跃、章节标题等）
2. 提取对话（格式：角色名：台词）
3. 区分叙述和对话内容

JSON格式：
[{{
  "number": 1,
  "location": "场景地点",
  "time": "时间",
  "description": "场景描述",
  "dialogue": [{{"character": "角色名", "line": "台词"}}]
}}]

只返回JSON数组："""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2500,
                temperature=0.2
            )
            
            # 记录token使用
            if hasattr(response, 'usage'):
                self.usage_stats.add_usage('character_generation', response.usage)
            
            result_text = response.choices[0].message.content
            if result_text:
                result_text = result_text.strip()
            else:
                print("⚠️ AI返回了空响应")
                result_text = ""
            
            # 移除markdown标记
            if '```json' in result_text:
                result_text = result_text.replace('```json', '').replace('```', '')
            elif '```' in result_text:
                # 移除任何其他代码块标记
                import re
                result_text = re.sub(r'```\w*\n', '', result_text)
                result_text = result_text.replace('```', '')
            
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
            print(f"AI剧本解析失败: {e}")
            if 'result_text' in locals():
                print(f"原始返回内容 (前500字符): {result_text[:500]}")
                print(f"JSON开始位置: {result_text.find('[')}, JSON结束位置: {result_text.rfind(']')}")
            return []
    
    def extract_characters(self, scenes: List[Scene]) -> List[Character]:
        """使用AI智能分析和提取角色信息"""
        if not self.is_available():
            raise Exception("AI服务不可用")
        
        # 先转换场景为文本
        script_text = self._scenes_to_text(scenes)
        
        prompt = f"""
        你是专业的编剧和角色分析师，请从以下剧本中智能识别和提取所有真正的角色人物。

        请注意区分：
        1. **真正的角色名**：如"林小鱼"、"陈墨"、"苏苏"等人名
        2. **非角色内容**：描述性文本如"林小鱼的心跳加速"、"苏苏看到后直接评论"等

        剧本内容：
        {script_text}

        请返回JSON格式的角色列表，每个角色包含：
        - name: 角色名称
        - description: 人物描述（30-50字）
        - personality: 性格特征（20-30字）
        - appearance: 外貌特征（30-40字，包括身高体型、发色、服装风格等）
        - key_lines: 代表性台词（3-5句）
        - scenes: 出现的主要场景描述

        请只返回JSON数组，不要其他内容。
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500,
                temperature=0.3
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
                
                characters = []
                for char_data in characters_data:
                    character = Character(
                        name=char_data.get('name', '未知角色'),
                        description=char_data.get('description', ''),
                        personality=char_data.get('personality', ''),
                        appearance=char_data.get('appearance', '符合指定视觉风格的角色设计'),
                        face_prompt="",  # 在可选阶段生成
                        full_body_prompt=""  # 在可选阶段生成
                    )
                    characters.append(character)
                
                return characters
            else:
                raise ValueError("无法解析AI返回的角色数据")
                
        except Exception as e:
            print(f"AI角色分析失败: {e}")
            return []
    
    def generate_shooting_script(self, scenes: List[Scene], style: VisualStyle) -> str:
        """生成拍摄脚本"""
        if not self.is_available():
            raise Exception("AI服务不可用")
        
        scenes_text = self._scenes_to_text(scenes)
        
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
        
        3. **{style.name}风格融入**：
           - 体现{style.description}
           - 运用{style.shot_characteristics}
           - 营造{style.color_palette}的视觉氛围
        
        4. **标准格式包含**：
           - 场景设置（时间、地点、氛围营造）
           - 角色动作和情绪描述
           - 网络化的对话标注
           - 镜头语言建议
        
        原始场景内容：
        {scenes_text}
        
        请按照动漫短片制作标准输出，注重情感共鸣和网络传播效果。
        """
        
        try:
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
            print(f"拍摄脚本生成失败: {e}")
            return self._generate_basic_shooting_script(scenes)
    
    def generate_professional_storyboard(self, scenes: List[Scene], style: VisualStyle) -> List[Shot]:
        """生成专业分镜头"""
        if not self.is_available():
            raise Exception("AI服务不可用")
        
        shots = []
        shot_counter = 1
        
        for scene in scenes:
            scene_shots = self._generate_scene_shots_ai(scene, shot_counter, style)
            shots.extend(scene_shots)
            shot_counter += len(scene_shots)
        
        return shots
    
    def _generate_scene_shots_ai(self, scene: Scene, start_shot_num: int, style: VisualStyle) -> List[Shot]:
        """使用AI生成场景分镜头"""
        dialogue_text = "\n".join([f"{d['character']}：{d['line']}" for d in scene.dialogue])
        
        prompt = f"""
        你是一位专业的动漫导演，擅长创造具有网络传播力的分镜头设计。
        
        请为以下场景设计分镜头方案，要求：
        
        1. **导演思维**：
           - 分析场景的情感高潮点和视觉爽点
           - 设计具有冲击力的镜头语言
           - 考虑短视频用户的观看节奏
        
        2. **{style.name}风格特色**：
           - 运用{style.shot_characteristics}
           - 体现{style.color_palette}
           - 营造{style.lighting_style}
        
        3. **网络化表达**：
           - 突出戏剧张力，适合切片传播
           - 设计容易引起弹幕互动的镜头
           - 考虑表情包潜质的画面
        
        4. **分镜要求**：
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
            
            # 移除markdown标记
            if '```json' in result_text:
                result_text = result_text.replace('```json', '').replace('```', '')
            
            # 提取JSON部分
            json_start = result_text.find('[')
            json_end = result_text.rfind(']') + 1
            
            if json_start != -1 and json_end > json_start:
                json_content = result_text[json_start:json_end].strip()
                shots_data = json.loads(json_content)
                
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
            return self._generate_basic_scene_shots(scene, start_shot_num)
    
    def _generate_basic_shooting_script(self, scenes: List[Scene]) -> str:
        """基础拍摄脚本转换"""
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
    
    def _generate_basic_scene_shots(self, scene: Scene, start_shot_num: int) -> List[Shot]:
        """为单个场景生成基础分镜头"""
        shots = []
        
        # 场景建立镜头
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
        
        # 根据对话生成镜头
        for i, dialogue in enumerate(scene.dialogue):
            if i == 0:
                shot_type = "特写"
                camera_movement = "缓慢推进"
            elif "？" in dialogue['line'] or "！" in dialogue['line']:
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
        
        # 情感高潮镜头
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
    
    def generate_character_prompts(self, character: Character, style: VisualStyle) -> Character:
        """为角色生成详细的图像提示词"""
        if not self.is_available():
            return character
        
        prompt = f"""
        你是专业的角色设计师，请为以下角色设计详细外观和图像提示词。

        角色信息：
        - 名称：{character.name}
        - 描述：{character.description}
        - 性格：{character.personality}

        请以{style.name}的视觉风格为基准，生成以下内容：

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
        
        try:
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
            
            # 移除markdown标记
            if '```json' in result_text:
                result_text = result_text.replace('```json', '').replace('```', '')
            
            json_start = result_text.find('{')
            json_end = result_text.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_content = result_text[json_start:json_end].strip()
                details = json.loads(json_content)
                
                character.appearance = details.get('appearance', character.appearance)
                character.face_prompt = f"{details.get('face_prompt', '')}, {style.character_style}, {style.lighting_style}"
                character.full_body_prompt = f"{details.get('full_body_prompt', '')}, {style.character_style}, {style.color_palette}"
                
                return character
            else:
                raise ValueError("无法解析AI返回的详细信息")
                
        except Exception as e:
            print(f"AI角色提示词生成失败: {e}")
            return character
    
    def generate_story_overview(self, scenes: List[Scene]) -> str:
        """生成故事概览"""
        if not self.is_available():
            return "故事概览生成需要AI服务支持"
        
        scenes_text = self._scenes_to_text(scenes)
        
        prompt = f"""你是专业的故事分析师，请为以下剧本内容生成一个简洁而吸引人的故事概览。

剧本内容：
{scenes_text}

请生成：
1. **核心主题**：故事的主要主题和价值观（20-30字）
2. **故事梗概**：完整的故事情节概述（100-150字）
3. **亮点特色**：故事的独特之处和看点（50-80字）
4. **目标受众**：适合的观众群体（20-30字）

请用简洁生动的语言，突出故事的吸引力和网络化特色。直接输出内容，不需要JSON格式。
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
                self.usage_stats.add_usage('story_overview', response.usage)
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"故事概览生成失败: {e}")
            return "故事概览：一个关于现代年轻人通过AI技术寻找真爱的温馨喜剧故事。"

    def generate_custom_style(self, name: str, description: str) -> dict:
        """生成自定义视觉风格"""
        if not self.is_available():
            return None
        
        prompt = f"""你是专业的动画视觉风格设计师，请为以下自定义风格生成完整的风格定义。

风格名称：{name}
风格描述：{description}

请生成完整的风格参数，包括：
1. 角色设计风格
2. 色彩调色板
3. 光线风格
4. 背景风格
5. 镜头语言特点
6. 技术特征

参考现有风格的格式，生成JSON格式的风格定义：
{{
  "name": "风格中文名称",
  "description": "详细的风格描述（50-80字）",
  "character_style": "角色设计特点",
  "color_palette": "色彩风格",
  "lighting_style": "光线特点",
  "background_style": "背景风格",
  "camera_style": "镜头语言特点"
}}

只返回JSON格式："""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                temperature=0.7
            )
            
            # 记录token使用
            if hasattr(response, 'usage'):
                self.usage_stats.add_usage('story_overview', response.usage)
            
            result_text = response.choices[0].message.content.strip()
            
            # 解析JSON
            if '```json' in result_text:
                result_text = result_text.replace('```json', '').replace('```', '')
            elif '```' in result_text:
                import re
                result_text = re.sub(r'```\w*\n', '', result_text)
                result_text = result_text.replace('```', '')
            
            json_start = result_text.find('{')
            json_end = result_text.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_content = result_text[json_start:json_end].strip()
                import json
                style_data = json.loads(json_content)
                return style_data
            else:
                print("⚠️ 无法解析AI返回的风格数据")
                return None
                
        except Exception as e:
            print(f"自定义风格生成失败: {e}")
            return None

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