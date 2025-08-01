#!/usr/bin/env python3
"""
测试角色分析功能
"""

import os
from script_adapter import ScriptAdapter

def test_character_extraction():
    """测试角色提取功能"""
    
    # 设置API（如果有的话）
    api_key = os.getenv('OPENAI_API_KEY')
    base_url = os.getenv('OPENAI_BASE_URL')
    model_name = os.getenv('OPENAI_MODEL_NAME')
    
    print("🧪 测试角色分析功能")
    print(f"API模式: {'AI增强' if api_key else '基础模式'}")
    
    # 创建适配器
    adapter = ScriptAdapter(
        api_key=api_key,
        base_url=base_url, 
        model_name=model_name,
        style='kyoani'
    )
    
    # 读取剧本
    print("📖 读取剧本文件...")
    with open('examples/yyds.txt', 'r', encoding='utf-8') as f:
        script_content = f.read()

    # 解析场景
    print("🎬 解析场景结构...")
    scenes = adapter.parse_original_script(script_content)
    print(f"解析到 {len(scenes)} 个场景")
    print(scenes)
    
    # 提取角色
    print("👥 分析角色信息...")
    characters = adapter.extract_characters(scenes)
    print(f"识别到 {len(characters)} 个角色")
    
    # 输出结果
    print("\n" + "="*50)
    print("🎭 角色分析结果")
    print("="*50)
    
    for i, char in enumerate(characters, 1):
        print(f"\n【角色 {i}】{char.name}")
        print(f"描述: {char.description}")
        print(f"性格: {char.personality}")
        print(f"外观: {char.appearance}")
        print(f"面部提示词: {char.face_prompt}")
        print(f"全身提示词: {char.full_body_prompt}")
        print("-" * 40)
    
    # 显示token使用统计
    if api_key and adapter.usage_stats.total.total_tokens > 0:
        adapter.usage_stats.print_report()
    
    print("✅ 测试完成")

if __name__ == '__main__':
    test_character_extraction()