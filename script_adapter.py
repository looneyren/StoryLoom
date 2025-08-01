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
from dataclasses import dataclass
from datetime import datetime
from openai import OpenAI


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
class ImagePrompt:
    """文生图提示词类"""
    shot_id: str
    prompt: str
    style: str
    technical_params: str


class ScriptAdapter:
    """剧本改编器主类"""
    
    def __init__(self, api_key: str = None, base_url: str = None, model_name: str = None):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.base_url = base_url or os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')
        self.model_name = model_name or os.getenv('OPENAI_MODEL_NAME', 'gpt-3.5-turbo')
        
        if self.api_key:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
        else:
            self.client = None

    def parse_original_script(self, script_content: str) -> List[Scene]:
        """解析原始剧本"""
        scenes = []
        scene_pattern = r'第(\d+)场[：:]?\s*(.+?)(?=第\d+场|$)'
        
        # 简单解析，实际使用中可根据具体格式调整
        lines = script_content.split('\n')
        current_scene = None
        scene_number = 1
        
        for line in lines:
            if not line:
                continue
                
            # 识别场景标题 - 支持章节格式
            if '场' in line or ('INT.' in line.upper() or 'EXT.' in line.upper()) or line.startswith('## 第') and '章' in line:
                if current_scene:
                    scenes.append(current_scene)
                
                current_scene = Scene(
                    number=scene_number,
                    location=line.strip(),
                    time="白天",  # 默认值
                    description="",
                    dialogue=[]
                )
                scene_number += 1
            
            elif current_scene:
                # 识别对话
                if '：' in line or ':' in line:
                    parts = line.split('：' if '：' in line else ':')
                    if len(parts) >= 2:
                        current_scene.dialogue.append({
                            'character': parts[0].strip(),
                            'line': parts[1].strip()
                        })
                else:
                    # 场景描述
                    current_scene.description += line.strip() + " "
        
        if current_scene:
            scenes.append(current_scene)
            
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
            你是专业的动漫美术指导，擅长创造具有网络传播力的视觉作品。
            
            请为以下分镜头创建详细的文生图提示词：
            
            镜头信息：
            - 镜头类型：{shot.shot_type}
            - 场景描述：{shot.description}
            - 对话内容：{shot.dialogue}
            - 镜头运动：{shot.camera_movement}
            
            创作要求：
            
            1. **视觉风格**：
               - 现代动漫风格，高质量渲染
               - 色彩鲜明，适合社交媒体传播
               - 考虑表情包化的潜质
            
            2. **构图设计**：
               - 符合{shot.shot_type}的专业构图
               - 突出情感表达和戏剧张力
               - 适合手机屏幕观看
            
            3. **网络化元素**：
               - 融入适当的流行元素（不要过度）
               - 考虑弹幕文化的视觉需求
               - 增强画面的记忆点
            
            4. **技术细节**：
               - 光影效果要有电影感
               - 细节丰富但不复杂
               - 适合AI图像生成的描述方式
            
            请生成简洁而专业的英文提示词，重点突出画面的情感冲击力。
            """
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.8
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"生成图像提示词失败，使用基础模式: {e}")
            return self._create_basic_image_prompt(shot)

    def _create_basic_image_prompt(self, shot: Shot) -> str:
        """网络化的基础图像提示词生成"""
        # 基础风格和镜头类型
        base_elements = [
            "modern anime style",
            "high quality",
            "detailed",
            "vibrant colors"
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
        
        # 网络化元素
        base_elements.extend([
            "trending on social media",
            "perfect for screenshots",
            "meme potential"
        ])
        
        # 技术参数
        technical_params = [
            "16:9 aspect ratio",
            "4K resolution",
            "professional animation quality"
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

    def save_to_markdown(self, output_file: str, scenes: List[Scene], 
                        shooting_script: str, shots: List[Shot], 
                        image_prompts: List[ImagePrompt]):
        """保存所有结果到Markdown文件"""
        content = f"""# 剧本改编工具输出结果

生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 1. 拍摄脚本

{shooting_script}

## 2. 分镜头表

| 场次 | 镜头号 | 镜头类型 | 时长 | 描述 | 镜头运动 | 对话 |
|------|--------|----------|------|------|----------|------|
"""
        
        for shot in shots:
            content += f"| {shot.scene_number} | {shot.shot_number} | {shot.shot_type} | {shot.duration} | {shot.description} | {shot.camera_movement} | {shot.dialogue} |\n"
        
        content += "\n## 3. 文生图提示词\n\n"
        
        for prompt in image_prompts:
            content += f"### 镜头 {prompt.shot_id}\n\n"
            content += f"**提示词：** {prompt.prompt}\n\n"
            content += f"**风格：** {prompt.style}\n\n"
            content += f"**技术参数：** {prompt.technical_params}\n\n"
            content += "---\n\n"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)

    def process_script(self, input_file: str, output_file: str):
        """处理完整的剧本改编流程"""
        ai_mode = "AI增强" if self.api_key else "基础"
        print(f"启动剧本改编工具 - {ai_mode}模式")
        
        print("正在读取原始剧本...")
        with open(input_file, 'r', encoding='utf-8') as f:
            script_content = f.read()
        
        print("正在解析剧本结构...")
        scenes = self.parse_original_script(script_content)
        print(f"解析到 {len(scenes)} 个场景")
        
        print("正在生成网络化拍摄脚本...")
        shooting_script = self.convert_to_shooting_script(scenes)
        
        print("正在设计导演分镜头...")
        shots = self.generate_storyboard(scenes)
        print(f"生成 {len(shots)} 个分镜头")
        
        print("正在创建文生图提示词...")
        image_prompts = self.generate_image_prompts(shots)
        
        print("正在保存结果...")
        self.save_to_markdown(output_file, scenes, shooting_script, shots, image_prompts)
        
        print(f"✨ 处理完成！")
        print(f"📝 结果已保存到：{output_file}")
        print(f"🎥 共 {len(scenes)} 个场景，{len(shots)} 个镜头")
        print(f"🎨 生成 {len(image_prompts)} 个文生图提示词")


def main():
    parser = argparse.ArgumentParser(description='剧本改编工具 - 将剧本转换为拍摄脚本和分镜头')
    parser.add_argument('input', help='输入剧本文件路径')
    parser.add_argument('-o', '--output', default='output.md', help='输出Markdown文件路径')
    parser.add_argument('--api-key', help='OpenAI API密钥')
    parser.add_argument('--base-url', help='API基础URL（支持兼容OpenAI的服务）')
    parser.add_argument('--model', help='模型名称（默认：gpt-3.5-turbo）')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print(f"错误：输入文件 {args.input} 不存在")
        return
    
    adapter = ScriptAdapter(
        api_key=args.api_key, 
        base_url=args.base_url,
        model_name=args.model
    )
    adapter.process_script(args.input, args.output)


if __name__ == '__main__':
    main()