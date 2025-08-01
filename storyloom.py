#!/usr/bin/env python3
"""
🧶 StoryLoom - 故事织机：将剧本编织成完整的视觉制作方案

重构版本，支持分阶段执行和任务管理
"""

import argparse
import os
import sys

# 尝试导入python-dotenv，如果没有安装则跳过
try:
    from dotenv import load_dotenv
    load_dotenv()  # 加载.env文件
except ImportError:
    pass  # 如果没有安装python-dotenv，则跳过

from ai_service import AIService
from task_manager import TaskManager
from styles import list_styles, get_style


def main():
    parser = argparse.ArgumentParser(
        description='🧶 StoryLoom - 故事织机：将剧本编织成完整的视觉制作方案',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法：
  # 创建新任务并执行主要分析
  %(prog)s script.txt --style=ghibli
  %(prog)s script.txt --custom-style="赛博朋克:未来主义科幻风格，霓虹灯效果，暗色调"
  
  # 为已有任务生成图像提示词
  %(prog)s --generate-prompts TASK_ID
  
  # 查看所有可用风格
  %(prog)s --style-list
  
  # 指定输出目录
  %(prog)s script.txt --output-dir ./my_output

环境变量配置：
  复制 .env.example 为 .env 并填入您的API配置

支持的视觉风格：
  ghibli, shinkai, kyoani, pixar, disney, anime, realistic, minimalist
        """
    )
    
    # 主要参数
    parser.add_argument('input', nargs='?', help='输入剧本文件路径')
    parser.add_argument('-o', '--output-dir', default='output', help='输出目录路径')
    parser.add_argument('--style', default='anime', help='视觉风格 (默认: anime)')
    parser.add_argument('--custom-style', metavar='NAME:DESCRIPTION', 
                       help='自定义样式 (格式: "名称:描述")')
    
    # 分阶段执行参数
    parser.add_argument('--generate-prompts', metavar='TASK_ID', 
                       help='为指定任务ID生成图像提示词')
    
    # 显示信息参数
    parser.add_argument('--style-list', action='store_true', help='显示所有可用的视觉风格')
    
    # API配置参数
    parser.add_argument('--api-key', help='OpenAI API密钥')
    parser.add_argument('--base-url', help='API基础URL（支持兼容OpenAI的服务）')
    parser.add_argument('--model', help='模型名称（默认：gpt-3.5-turbo）')
    
    args = parser.parse_args()
    
    # 显示风格列表
    if args.style_list:
        list_styles()
        return
    
    # 生成图像提示词
    if args.generate_prompts:
        generate_image_prompts_for_task(args.generate_prompts, args)
        return
    
    # 检查输入文件
    if not args.input:
        parser.error("需要提供输入剧本文件路径")
    
    if not os.path.exists(args.input):
        print(f"❌ 错误：输入文件 {args.input} 不存在")
        return
    
    # 执行主要分析
    execute_main_analysis(args)


def execute_main_analysis(args):
    """执行主要分析（场景、角色、分镜）"""
    print("🧶 StoryLoom - 故事织机")
    print("=" * 50)
    
    # 初始化服务
    ai_service = AIService(
        api_key=args.api_key,
        base_url=args.base_url,
        model_name=args.model
    )
    
    task_manager = TaskManager(args.output_dir)
    
    # 检查AI服务
    if not ai_service.is_available():
        print("❌ 错误：需要配置AI服务才能使用StoryLoom")
        print("请设置环境变量或使用命令行参数：")
        print("  --api-key YOUR_API_KEY")
        print("  --base-url API_BASE_URL")
        print("或者配置 .env 文件")
        return
    
    print(f"🤖 工作模式: AI增强")
    
    # 处理自定义样式
    custom_style_data = None
    if args.custom_style:
        if ':' not in args.custom_style:
            print("❌ 自定义样式格式错误，请使用 '名称:描述' 格式")
            return
        
        custom_name, custom_description = args.custom_style.split(':', 1)
        custom_name = custom_name.strip()
        custom_description = custom_description.strip()
        
        if not custom_name or not custom_description:
            print("❌ 样式名称和描述不能为空")
            return
        
        print(f"🎨 正在生成自定义样式: {custom_name}")
        print(f"📝 样式描述: {custom_description}")
        
        # 使用AI生成完整的样式定义
        ai_service = AIService()
        custom_style_data = ai_service.generate_custom_style(custom_name, custom_description)
        
        if not custom_style_data:
            print("❌ 自定义样式生成失败，使用默认样式")
            custom_style_data = None
        else:
            print(f"✅ 自定义样式生成完成: {custom_style_data.get('name', custom_name)}")
    
    # 验证和获取风格
    style = get_style(args.style, custom_style_data)
    print(f"🎨 视觉风格: {style.name}")
    
    try:
        # 创建任务
        actual_style_name = custom_style_data.get('name', style.name) if custom_style_data else args.style
        task_id = task_manager.create_task(args.input, actual_style_name, custom_style_data)
        print(f"📋 任务ID: {task_id}")
        
        # 执行主要分析
        success = task_manager.execute_main_analysis(task_id, ai_service, custom_style_data)
        
        if success:
            print(f"\n✅ 主要分析完成！")
            print(f"📋 任务ID: {task_id}")
            print(f"📂 结果目录: {os.path.join(args.output_dir, task_id)}")
            print(f"\n💡 下一步：")
            print(f"   生成图像提示词: python storyloom.py --generate-prompts {task_id}")
        else:
            print(f"\n❌ 任务执行失败")
            
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断操作")
    except Exception as e:
        print(f"❌ 处理过程中出现错误: {e}")
        print("请检查输入文件格式或网络连接")


def generate_image_prompts_for_task(task_id: str, args):
    """为指定任务生成图像提示词"""
    print("🎨 StoryLoom - 图像提示词生成器")
    print("=" * 50)
    
    # 初始化服务
    ai_service = AIService(
        api_key=args.api_key,
        base_url=args.base_url,
        model_name=args.model
    )
    
    task_manager = TaskManager(args.output_dir)
    
    # 检查AI服务
    if not ai_service.is_available():
        print("❌ 错误：需要配置AI服务才能生成图像提示词")
        print("请设置环境变量或使用命令行参数：")
        print("  --api-key YOUR_API_KEY")
        print("或者配置 .env 文件")
        return
    
    print(f"🤖 工作模式: AI增强")
    print(f"📋 任务ID: {task_id}")
    
    try:
        # 生成图像提示词
        success = task_manager.generate_image_prompts(task_id, ai_service, None)
        
        if success:
            print(f"\n✅ 图像提示词生成完成！")
            task = task_manager.get_task(task_id)
        else:
            print(f"\n❌ 图像提示词生成失败")
            
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断操作")
    except Exception as e:
        print(f"❌ 处理过程中出现错误: {e}")


if __name__ == '__main__':
    main()