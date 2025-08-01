#!/usr/bin/env python3
"""
StoryLoom 视觉风格库
"""

from models import VisualStyle


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


def list_styles():
    """显示所有可用的视觉风格"""
    print("\n🎨 StoryLoom 可用视觉风格：\n")
    for key, style in VISUAL_STYLES.items():
        print(f"🔸 {key}")
        print(f"   名称：{style.name}")
        print(f"   描述：{style.description}")
        print(f"   用法：--style={key}")
        print()


def create_custom_style(style_data: dict) -> VisualStyle:
    """根据AI生成的数据创建自定义视觉风格"""
    return VisualStyle(
        name=style_data.get('name', '自定义风格'),
        description=style_data.get('description', '用户自定义的视觉风格'),
        shot_characteristics=style_data.get('camera_style', style_data.get('shot_characteristics', '自定义镜头语言')),
        color_palette=style_data.get('color_palette', '自定义色彩'),
        lighting_style=style_data.get('lighting_style', '自定义光线'),
        character_style=style_data.get('character_style', '自定义角色设计'),
        background_style=style_data.get('background_style', '自定义背景')
    )

def get_style(style_name: str, custom_style_data: dict = None) -> VisualStyle:
    """获取指定的视觉风格，支持自定义样式"""
    # 如果提供了自定义样式数据，优先使用
    if custom_style_data:
        return create_custom_style(custom_style_data)
    
    # 否则从预定义样式中获取
    if style_name not in VISUAL_STYLES:
        print(f"⚠️ 警告：风格 '{style_name}' 不存在，使用默认风格 'anime'")
        style_name = "anime"
    return VISUAL_STYLES[style_name]