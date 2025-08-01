#!/usr/bin/env python3
"""
StoryLoom 任务管理器
"""

import os
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

from models import ProjectTask, Scene, Character, Shot, ImagePrompt
from ai_service import AIService
from styles import get_style


class TaskManager:
    """任务管理器，处理项目任务的创建、执行和管理"""
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        self.tasks_dir = os.path.join(output_dir, "tasks")
        self.ensure_directories()
    
    def ensure_directories(self):
        """确保输出目录存在"""
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.tasks_dir, exist_ok=True)
    
    def create_task(self, input_file: str, style: str = "anime", custom_style_data: dict = None) -> str:
        """创建新的项目任务"""
        task_id = str(uuid.uuid4())[:8]
        
        task = ProjectTask(
            task_id=task_id,
            input_file=input_file,
            output_dir=os.path.join(self.output_dir, task_id),
            style=style,
            created_at=datetime.now(),
            custom_style_data=custom_style_data or {}
        )
        
        # 创建任务目录
        os.makedirs(task.output_dir, exist_ok=True)
        
        # 保存任务信息
        self._save_task(task)
        
        return task_id
    
    def get_task(self, task_id: str) -> Optional[ProjectTask]:
        """获取任务信息"""
        task_file = os.path.join(self.tasks_dir, f"{task_id}.json")
        if not os.path.exists(task_file):
            return None
        
        try:
            with open(task_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return ProjectTask(
                task_id=data['task_id'],
                input_file=data['input_file'],
                output_dir=data['output_dir'],
                style=data['style'],
                created_at=datetime.fromisoformat(data['created_at']),
                custom_style_data=data.get('custom_style_data', {}),
                status=data.get('status', 'pending'),
                progress=data.get('progress', {})
            )
        except Exception as e:
            print(f"读取任务失败: {e}")
            return None
    
    def execute_main_analysis(self, task_id: str, ai_service: AIService, custom_style_data: dict = None) -> bool:
        """执行主要分析（场景解析、角色提取、分镜设计）"""
        task = self.get_task(task_id)
        if not task:
            print(f"任务 {task_id} 不存在")
            return False
        
        print(f"🚀 开始执行任务 {task_id}")
        print(f"📁 输入文件: {task.input_file}")
        print(f"🎨 视觉风格: {task.style}")
        
        task.status = "processing"
        self._save_task(task)
        
        try:
            # 读取剧本文件
            print("📖 读取原始剧本...")
            with open(task.input_file, 'r', encoding='utf-8') as f:
                script_content = f.read()
            
            # 解析场景
            print("🎬 解析场景结构...")
            scenes = ai_service.parse_script(script_content)
            
            print(f"解析到 {len(scenes)} 个场景")
            task.progress["scenes_parsed"] = True
            self._save_task(task)
            
            # 保存场景数据
            self._save_scenes(task, scenes)
            
            # 生成故事概览
            print("📚 生成故事概览...")
            story_overview = ai_service.generate_story_overview(scenes)
            task.progress["story_overview_created"] = True
            self._save_task(task)
            
            # 提取角色
            print("👥 分析角色信息...")
            characters = ai_service.extract_characters(scenes)
            
            print(f"识别到 {len(characters)} 个角色")
            task.progress["characters_extracted"] = True
            self._save_task(task)
            
            # 获取视觉风格
            style = get_style(task.style, custom_style_data)
            
            # 为角色生成详细信息和提示词
            print("🎨 生成角色详细信息和图像提示词...")
            for i, character in enumerate(characters):
                print(f"处理角色 {i+1}/{len(characters)}: {character.name}")
                characters[i] = ai_service.generate_character_prompts(character, style)
            
            task.progress["character_prompts_generated"] = True
            self._save_task(task)
            
            # 保存角色数据
            self._save_characters(task, characters)
            
            # 生成专业分镜头
            print("🎯 设计专业分镜头...")
            shots = ai_service.generate_professional_storyboard(scenes, style)
            print(f"生成 {len(shots)} 个分镜头")
            task.progress["storyboard_created"] = True
            self._save_task(task)
            
            # 保存分镜数据
            self._save_shots(task, shots)
            
            # 生成带分镜的拍摄脚本
            print("📝 生成专业拍摄脚本...")
            shooting_script = self._generate_integrated_shooting_script(scenes, shots, style)
            self._save_shooting_script(task, shooting_script)
            task.progress["shooting_script_created"] = True
            self._save_task(task)
            
            # 生成主报告
            self._generate_main_report(task, scenes, characters, shots, shooting_script, story_overview)
            
            task.status = "completed"
            self._save_task(task)
            
            print("✅ 主要分析完成！")
            print(f"📂 结果保存在: {task.output_dir}")
            
            # 显示token使用统计
            if ai_service.is_available() and ai_service.usage_stats.total.total_tokens > 0:
                ai_service.usage_stats.print_report()
            
            return True
            
        except Exception as e:
            print(f"❌ 任务执行失败: {e}")
            task.status = "failed"
            self._save_task(task)
            return False
    
    def generate_image_prompts(self, task_id: str, ai_service: AIService, custom_style_data: dict = None) -> bool:
        """生成图像提示词（可选步骤）"""
        task = self.get_task(task_id)
        if not task:
            print(f"任务 {task_id} 不存在")
            return False
        
        # 如果任务中保存了自定义风格数据，优先使用
        if not custom_style_data and task.custom_style_data:
            custom_style_data = task.custom_style_data
        
        print(f"🎨 为任务 {task_id} 生成图像提示词...")
        
        try:
            # 加载现有数据
            scenes = self._load_scenes(task)
            characters = self._load_characters(task)
            shots = self._load_shots(task)
            
            if not shots:
                print("❌ 未找到分镜数据，请先执行主要分析")
                return False
            
            # 获取视觉风格
            style = get_style(task.style, custom_style_data)
            
            # 生成分镜图像提示词（批量处理，使用已保存的角色信息）
            print("🎬 为分镜生成图像提示词...")
            image_prompts = self._generate_batch_image_prompts(shots, style, ai_service, characters)
            
            print(f"生成 {len(image_prompts)} 个图像提示词")
            
            # 保存数据
            self._save_image_prompts(task, image_prompts)
            
            task.progress["image_prompts_generated"] = True
            self._save_task(task)
            
            print("✅ 图像提示词生成完成！")
            print(f"📂 保存位置: {task.output_dir}/image_prompts.*")
            
            return True
            
        except Exception as e:
            print(f"❌ 图像提示词生成失败: {e}")
            return False
    
    def _save_task(self, task: ProjectTask):
        """保存任务信息"""
        task_file = os.path.join(self.tasks_dir, f"{task.task_id}.json")
        with open(task_file, 'w', encoding='utf-8') as f:
            json.dump({
                'task_id': task.task_id,
                'input_file': task.input_file,
                'output_dir': task.output_dir,
                'style': task.style,
                'created_at': task.created_at.isoformat(),
                'custom_style_data': task.custom_style_data,
                'status': task.status,
                'progress': task.progress
            }, f, ensure_ascii=False, indent=2)
    
    
    def _generate_basic_storyboard(self, scenes: List[Scene]) -> List[Shot]:
        """生成基础分镜头"""
        shots = []
        shot_counter = 1
        
        for scene in scenes:
            # 为每个场景生成基本的分镜头
            shots.append(Shot(
                scene_number=scene.number,
                shot_number=shot_counter,
                shot_type="远景",
                duration="3秒",
                description=f"建立镜头：{scene.location}",
                camera_movement="静止",
                dialogue=""
            ))
            shot_counter += 1
            
            # 如果有对话，为每个对话生成镜头
            for dialogue in scene.dialogue:
                shots.append(Shot(
                    scene_number=scene.number,
                    shot_number=shot_counter,
                    shot_type="中景",
                    duration="4秒",
                    description=f"{dialogue['character']}说话",
                    camera_movement="轻微推进",
                    dialogue=dialogue['line']
                ))
                shot_counter += 1
        
        return shots
    
    def _generate_integrated_shooting_script(self, scenes: List[Scene], shots: List[Shot], style) -> str:
        """生成整合了分镜设计的拍摄脚本"""
        script = f"# 专业拍摄脚本\n\n*风格：{style.name} - {style.description}*\n\n"
        
        for scene in scenes:
            script += f"## 第{scene.number}场 - {scene.location}\n\n"
            script += f"**时间：** {scene.time}\n"
            script += f"**场景描述：** {scene.description.strip()}\n\n"
            
            # 添加对话内容
            if scene.dialogue:
                script += "**对话内容：**\n\n"
                for dialogue in scene.dialogue:
                    script += f"- **{dialogue['character']}：** {dialogue['line']}\n"
                script += "\n"
            
            # 添加该场景的分镜设计
            scene_shots = [shot for shot in shots if shot.scene_number == scene.number]
            if scene_shots:
                script += "**分镜设计：**\n\n"
                script += "| 镜头号 | 类型 | 时长 | 描述 | 镜头运动 | 对话 |\n"
                script += "|-------|-----|-----|-----|---------|-----|\n"
                for shot in scene_shots:
                    dialogue_text = ""
                    if shot.dialogue:
                        dialogue_text = shot.dialogue[:30] + "..." if len(shot.dialogue) > 30 else shot.dialogue
                    script += f"| {shot.shot_number} | {shot.shot_type} | {shot.duration} | {shot.description} | {shot.camera_movement} | {dialogue_text} |\n"
                script += "\n"
            
            script += "---\n\n"
        
        return script
    
    def _generate_batch_image_prompts(self, shots: List[Shot], style, ai_service, characters: List[Character] = None) -> List[ImagePrompt]:
        """批量生成分镜图像提示词（每5个为一组）"""
        image_prompts = []
        batch_size = 5
        
        for i in range(0, len(shots), batch_size):
            batch_shots = shots[i:i + batch_size]
            print(f"处理分镜 {i+1}-{min(i+batch_size, len(shots))}/{len(shots)}")
            
            # 为这一批镜头生成提示词
            batch_prompts = self._generate_shot_prompts_ai(batch_shots, style, ai_service, characters)
            image_prompts.extend(batch_prompts)
        
        return image_prompts
    
    def _generate_shot_prompts_ai(self, shots: List[Shot], style, ai_service, characters: List[Character] = None) -> List[ImagePrompt]:
        """使用AI为一组分镜生成MJ风格的提示词"""
        if not ai_service.is_available():
            return []
        
        # 构建批量处理的提示词
        shots_info = []
        for shot in shots:
            shots_info.append(f"镜头{shot.shot_number}: {shot.shot_type}, {shot.description}, {shot.dialogue if shot.dialogue else '无对话'}")
        
        shots_text = "\n".join(shots_info)
        
        # 构建角色信息文本
        characters_info = ""
        if characters:
            characters_info = "\n角色设定参考：\n"
            for char in characters:
                char_info = f"- {char.name}: {char.description}"
                if char.appearance and char.appearance != "符合指定视觉风格的角色设计":
                    char_info += f"\n  外貌: {char.appearance}"
                if char.face_prompt:
                    # 提取面部特征的核心部分，去掉重复的风格描述
                    face_features = char.face_prompt.split(',')[:3]  # 只取前3个特征
                    char_info += f"\n  面部特征: {', '.join(face_features)}"
                characters_info += char_info + "\n"
        
        prompt = f"""你是专业的AI绘画提示词专家，请为以下分镜头设计Midjourney风格的提示词。

视觉风格：{style.name} - {style.description}
风格特征：{style.character_style}, {style.color_palette}, {style.lighting_style}
{characters_info}
分镜信息：
{shots_text}

要求：
1. 每个分镜生成三个版本：
   - 完整版英文：详细的MJ风格提示词（英文，包含构图、光线、色彩、质感等）
   - 完整版中文：对应的中文描述版本
   - 简单版英文：简洁版本（核心要素）

2. 结合角色信息：
   - 仔细阅读上述角色设定，当分镜描述中提到角色名称时，必须使用对应角色的外貌特征
   - 直接引用角色的具体外貌描述（如发色、身材、服装、配件等）
   - 如果分镜涉及"王强"，使用他的外貌特征；涉及"张教授"使用他的特征
   - 保持角色在不同分镜中的形象一致性

3. MJ提示词格式要求：
   - 英文版本遵循 subject, environment, composition, lighting, style 结构
   - 中文版本使用自然的中文描述
   - 避免在提示词中使用引号和特殊字符

4. JSON格式要求：
   - 严格遵循JSON格式，使用双引号
   - 字符串内容中如有引号请使用转义字符
   - 不要包含换行符和制表符

请按以下JSON格式输出：
[{{
  "shot_number": 1,
  "full_prompt": "完整版MJ提示词内容(英文)",
  "full_prompt_cn": "完整版提示词内容(中文)",
  "simple_prompt": "简单版提示词内容(英文)"
}}]

重要：只返回标准JSON数组，不要添加任何说明文字："""
        
        try:
            print(f"  -> 正在调用AI生成提示词...")
            response = ai_service.client.chat.completions.create(
                model=ai_service.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.7
            )
            print(f"  -> AI响应完成")
            
            # 记录token使用
            if hasattr(response, 'usage'):
                ai_service.usage_stats.add_usage('image_prompts', response.usage)
            
            result_text = response.choices[0].message.content.strip()
            
            # 解析JSON
            if '```json' in result_text:
                result_text = result_text.replace('```json', '').replace('```', '')
            elif '```' in result_text:
                import re
                result_text = re.sub(r'```\w*\n', '', result_text)
                result_text = result_text.replace('```', '')
            
            json_start = result_text.find('[')
            json_end = result_text.rfind(']') + 1
            
            if json_start != -1 and json_end > json_start:
                json_content = result_text[json_start:json_end].strip()
                try:
                    prompts_data = json.loads(json_content)
                except json.JSONDecodeError as e:
                    print(f"⚠️ JSON解析失败: {e}")
                    print(f"原始JSON内容: {json_content[:500]}...")
                    # 尝试修复常见的JSON问题
                    import re
                    # 将单引号替换为双引号
                    fixed_content = json_content.replace("'", '"')
                    # 移除可能的换行符和多余的逗号
                    fixed_content = re.sub(r',\s*}', '}', fixed_content)
                    fixed_content = re.sub(r',\s*]', ']', fixed_content)
                    try:
                        prompts_data = json.loads(fixed_content)
                        print("✅ JSON修复成功")
                    except Exception as fix_error:
                        print(f"❌ JSON修复失败: {fix_error}")
                        return []
                
                image_prompts = []
                for prompt_data in prompts_data:
                    shot_number = prompt_data.get('shot_number')
                    # 找到对应的shot
                    shot = next((s for s in shots if s.shot_number == shot_number), None)
                    if shot:
                        image_prompts.append(ImagePrompt(
                            shot_id=f"S{shot.scene_number:02d}_{shot.shot_number:03d}",
                            full_prompt=prompt_data.get('full_prompt', ''),
                            full_prompt_cn=prompt_data.get('full_prompt_cn', ''),
                            simple_prompt=prompt_data.get('simple_prompt', ''),
                            style=f"{style.name} style",
                            technical_params="--ar 16:9 --q 2"
                        ))
                
                return image_prompts
            else:
                print("⚠️ 无法解析AI返回的提示词数据")
                return []
                
        except Exception as e:
            print(f"批量生成提示词失败: {e}")
            return []
    
    def _create_basic_image_prompt(self, shot: Shot, style) -> str:
        """创建基础图像提示词"""
        elements = [
            f"{style.name} style",
            style.color_palette.lower(),
            style.lighting_style.lower(),
            "high quality",
            "detailed"
        ]
        
        # 根据镜头类型设定构图
        if "特写" in shot.shot_type:
            elements.extend(["close-up shot", "detailed expression"])
        elif "远景" in shot.shot_type:
            elements.extend(["wide shot", "establishing shot"])
        else:
            elements.extend(["medium shot", "balanced composition"])
        
        return ", ".join(elements)
    
    def _save_scenes(self, task: ProjectTask, scenes: List[Scene]):
        """保存场景数据"""
        scenes_file = os.path.join(task.output_dir, "scenes.json")
        with open(scenes_file, 'w', encoding='utf-8') as f:
            scenes_data = []
            for scene in scenes:
                scenes_data.append({
                    'number': scene.number,
                    'location': scene.location,
                    'time': scene.time,
                    'description': scene.description,
                    'dialogue': scene.dialogue
                })
            json.dump(scenes_data, f, ensure_ascii=False, indent=2)
    
    def _save_characters(self, task: ProjectTask, characters: List[Character]):
        """保存角色数据"""
        chars_file = os.path.join(task.output_dir, "characters.json")
        with open(chars_file, 'w', encoding='utf-8') as f:
            chars_data = []
            for char in characters:
                chars_data.append({
                    'name': char.name,
                    'description': char.description,
                    'personality': char.personality,
                    'appearance': char.appearance,
                    'face_prompt': char.face_prompt,
                    'full_body_prompt': char.full_body_prompt
                })
            json.dump(chars_data, f, ensure_ascii=False, indent=2)
    
    def _save_shots(self, task: ProjectTask, shots: List[Shot]):
        """保存分镜数据"""
        shots_file = os.path.join(task.output_dir, "shots.json")
        with open(shots_file, 'w', encoding='utf-8') as f:
            shots_data = []
            for shot in shots:
                shots_data.append({
                    'scene_number': shot.scene_number,
                    'shot_number': shot.shot_number,
                    'shot_type': shot.shot_type,
                    'duration': shot.duration,
                    'description': shot.description,
                    'camera_movement': shot.camera_movement,
                    'dialogue': shot.dialogue
                })
            json.dump(shots_data, f, ensure_ascii=False, indent=2)
    
    def _save_shooting_script(self, task: ProjectTask, shooting_script: str):
        """保存拍摄脚本"""
        script_file = os.path.join(task.output_dir, "shooting_script.md")
        with open(script_file, 'w', encoding='utf-8') as f:
            f.write(shooting_script)
    
    def _save_image_prompts(self, task: ProjectTask, prompts: List[ImagePrompt]):
        """保存图像提示词数据（分镜映射格式）"""
        # 保存JSON格式的数据
        prompts_file = os.path.join(task.output_dir, "image_prompts.json")
        with open(prompts_file, 'w', encoding='utf-8') as f:
            prompts_data = {}
            for prompt in prompts:
                prompts_data[prompt.shot_id] = {
                    'full_prompt': prompt.full_prompt,
                    'full_prompt_cn': prompt.full_prompt_cn,
                    'simple_prompt': prompt.simple_prompt,
                    'style': prompt.style,
                    'technical_params': prompt.technical_params
                }
            json.dump(prompts_data, f, ensure_ascii=False, indent=2)
        
        # 同时保存一个可读的markdown格式
        prompts_md_file = os.path.join(task.output_dir, "image_prompts.md")
        with open(prompts_md_file, 'w', encoding='utf-8') as f:
            f.write("# 分镜图像提示词\n\n")
            for prompt in prompts:
                f.write(f"## {prompt.shot_id}\n\n")
                f.write(f"**完整版（英文）：** {prompt.full_prompt}\n\n")
                f.write(f"**完整版（中文）：** {prompt.full_prompt_cn}\n\n")
                f.write(f"**简单版：** {prompt.simple_prompt}\n\n")
                f.write(f"**参数：** {prompt.technical_params}\n\n")
                f.write("---\n\n")
    
    def _load_scenes(self, task: ProjectTask) -> List[Scene]:
        """加载场景数据"""
        scenes_file = os.path.join(task.output_dir, "scenes.json")
        if not os.path.exists(scenes_file):
            return []
        
        with open(scenes_file, 'r', encoding='utf-8') as f:
            scenes_data = json.load(f)
        
        scenes = []
        for data in scenes_data:
            scenes.append(Scene(
                number=data['number'],
                location=data['location'],
                time=data['time'],
                description=data['description'],
                dialogue=data['dialogue']
            ))
        return scenes
    
    def _load_characters(self, task: ProjectTask) -> List[Character]:
        """加载角色数据"""
        chars_file = os.path.join(task.output_dir, "characters.json")
        if not os.path.exists(chars_file):
            return []
        
        with open(chars_file, 'r', encoding='utf-8') as f:
            chars_data = json.load(f)
        
        characters = []
        for data in chars_data:
            characters.append(Character(
                name=data['name'],
                description=data['description'],
                personality=data['personality'],
                appearance=data['appearance'],
                face_prompt=data['face_prompt'],
                full_body_prompt=data['full_body_prompt']
            ))
        return characters
    
    def _load_shots(self, task: ProjectTask) -> List[Shot]:
        """加载分镜数据"""
        shots_file = os.path.join(task.output_dir, "shots.json")
        if not os.path.exists(shots_file):
            return []
        
        with open(shots_file, 'r', encoding='utf-8') as f:
            shots_data = json.load(f)
        
        shots = []
        for data in shots_data:
            shots.append(Shot(
                scene_number=data['scene_number'],
                shot_number=data['shot_number'],
                shot_type=data['shot_type'],
                duration=data['duration'],
                description=data['description'],
                camera_movement=data['camera_movement'],
                dialogue=data['dialogue']
            ))
        return shots
    
    def _generate_main_report(self, task: ProjectTask, scenes: List[Scene], 
                            characters: List[Character], shots: List[Shot], shooting_script: str = "", story_overview: str = ""):
        """生成主报告（不包含图像提示词）"""
        # 提取项目名称（文件名，不含扩展名）
        import os
        project_name = os.path.splitext(os.path.basename(task.input_file))[0]
        
        content = f"""# StoryLoom 分析报告

项目名称：{project_name}
任务ID：{task.task_id}
生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
视觉风格：{task.style}

## 故事概览

{story_overview if story_overview else '故事概览生成中...'}

## 场景结构 ({len(scenes)} 个场景)

"""
        
        for scene in scenes:
            content += f"### 第{scene.number}场 - {scene.location}\n"
            content += f"**时间：** {scene.time}\n"
            content += f"**描述：** {scene.description.strip()}\n"
            if scene.dialogue:
                content += f"**对话数：** {len(scene.dialogue)} 句\n"
            content += "\n"
        
        content += f"## 角色分析 ({len(characters)} 个角色)\n\n"
        
        for char in characters:
            content += f"### {char.name}\n"
            content += f"**人物描述：** {char.description}\n"
            content += f"**性格特征：** {char.personality}\n"
            if char.appearance and char.appearance != "符合指定视觉风格的角色设计":
                content += f"**外貌特征：** {char.appearance}\n"
            if char.face_prompt:
                content += f"**面部特写提示词：** `{char.face_prompt}`\n"
            if char.full_body_prompt:
                content += f"**全身照提示词：** `{char.full_body_prompt}`\n"
            content += "\n"
        
        # 添加拍摄脚本（如果有的话）
        if shooting_script:
            content += f"## 专业拍摄脚本\n\n"
            content += f"{shooting_script}\n\n"
        
        content += f"\n---\n*使用 `--generate-prompts {task.task_id}` 生成图像提示词*\n"
        
        report_file = os.path.join(task.output_dir, "main_report.md")
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(content)
    
