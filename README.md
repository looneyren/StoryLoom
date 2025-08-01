# 🧶 StoryLoom

> 故事织机 - 专为动漫短片创作设计的AI增强工具，将原始剧本编织成完整的视觉制作方案，包括标准拍摄脚本、分镜头表和文生图提示词。

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![AI](https://img.shields.io/badge/AI-Enhanced-purple.svg)](https://openai.com)

## ✨ 功能特性

- 🎬 **剧本转换** - 将文学剧本转换为标准的影视拍摄脚本
- 📝 **分镜头生成** - 按场次自动生成详细的分镜头表
- 🎨 **文生图提示词** - 为每个镜头生成适合AI绘画的提示词
- 🤖 **AI增强** - 支持OpenAI兼容API，提升转换质量
- 🌐 **网络化创作** - 融入网感和二次创作，适合现代观众
- 🎥 **导演思维** - 模拟专业导演的分镜思路
- 📄 **Markdown输出** - 生成结构化的Markdown文档
- ⚡ **简洁高效** - 专注核心功能，避免复杂度

## 🚀 快速开始

### 安装

```bash
# 克隆项目
git clone https://github.com/looneyren/StoryLoom.git
cd StoryLoom

# 安装依赖
pip install -r requirements.txt
```

### 基础使用

```bash
# 基础模式（不使用AI）
python script_adapter.py examples/yyds.txt

# 指定输出文件
python script_adapter.py examples/yyds.txt -o my_project.md
```

### AI增强模式

#### 环境变量配置（推荐）

```bash
# OpenAI
export OPENAI_API_KEY="your-openai-key"
export OPENAI_BASE_URL="https://api.openai.com/v1"
export OPENAI_MODEL_NAME="gpt-4"

# 智谱AI
export OPENAI_API_KEY="your-zhipu-key"
export OPENAI_BASE_URL="https://open.bigmodel.cn/api/paas/v4/"
export OPENAI_MODEL_NAME="glm-4.5"

# DMX API
export OPENAI_API_KEY="your-dmx-key"
export OPENAI_BASE_URL="https://www.dmxapi.com/v1"
export OPENAI_MODEL_NAME="gpt-4o"

# 运行工具
python script_adapter.py examples/yyds.txt
```

#### 命令行参数

```bash
# 使用OpenAI API
python script_adapter.py examples/yyds.txt --api-key your-key

# 使用其他兼容OpenAI的服务
python script_adapter.py examples/yyds.txt \
    --api-key your-key \
    --base-url https://api.example.com/v1 \
    --model gpt-4

# 完整示例
python script_adapter.py examples/yyds.txt \
    --api-key your-key \
    --base-url https://www.dmxapi.com/v1 \
    --model gpt-4o \
    -o output/result.md
```

## 📖 使用示例

### 输入格式

创建一个文本文件，按以下格式编写剧本：

```
第1场：咖啡厅 - 白天

温暖的午后阳光透过落地窗洒进咖啡厅。

小明：今天的天气真不错呢。
小红：是啊，很适合约会。

第2场：公园 - 傍晚

夕阳西下，金色的光线穿过树叶。

小红：这里真美。
小明：和你在一起，哪里都很美。
```

### 输出示例

查看 [`examples/yyds_gpt4o_output.md`](examples/yyds_gpt4o_output.md) 了解完整的输出格式。

## 🛠️ 命令行参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `input` | 输入剧本文件路径（必需） | `examples/yyds.txt` |
| `-o, --output` | 输出Markdown文件路径 | `-o result.md` |
| `--api-key` | OpenAI API密钥 | `--api-key sk-xxx` |
| `--base-url` | API服务地址 | `--base-url https://api.example.com/v1` |
| `--model` | 模型名称 | `--model gpt-4` |

## 🌐 支持的AI服务

工具支持所有兼容OpenAI标准的服务：

- ✅ OpenAI GPT (GPT-3.5, GPT-4, GPT-4o)
- ✅ Azure OpenAI
- ✅ DeepSeek
- ✅ 智谱AI (GLM-4, GLM-4.5)
- ✅ 通义千问
- ✅ DMX API
- ✅ 其他兼容服务

## 📁 输出格式

工具会生成包含以下内容的Markdown文件：

### 1. 拍摄脚本
- 场景设置（时间、地点、环境）
- 网络化的角色动作和情绪描述
- 标准对话标注
- 专业镜头语言建议

### 2. 分镜头表
| 场次 | 镜头号 | 镜头类型 | 时长 | 描述 | 镜头运动 | 对话 |
|------|--------|----------|------|------|----------|------|
| 1 | 1 | 远景 | 3-5秒 | 建立镜头：咖啡厅全景 | 静止 | |
| 1 | 2 | 中景 | 2-4秒 | 小明说话特写 | 轻微推进 | 今天的天气真不错呢 |

### 3. 文生图提示词
为每个镜头生成详细的AI绘画提示词，包括：
- 专业构图建议
- 现代动漫风格描述
- 网络化视觉元素
- 技术参数设置

## 🏗️ 项目结构

```
StoryLoom/
├── script_adapter.py      # 主程序
├── requirements.txt       # 依赖列表
├── README.md             # 项目说明
├── LICENSE               # 许可证
├── .gitignore           # Git忽略文件
├── examples/            # 示例文件
│   ├── yyds.txt        # 示例小说
│   └── yyds_gpt4o_output.md  # 示例输出
└── docs/               # 文档
    ├── PRD.md         # 产品需求文档
    └── PROMPT.md      # 提示词文档
```

## 🎯 适用场景

- 🌌 **网络动漫短片** - 适合社交媒体传播的动漫制作
- 📱 **短视频创作** - 具有网感的分镜头方案
- 🎭 **剧本二创** - 从传统剧本到网络化内容的转换
- 🎨 **视觉概念** - 为美术团队提供网络化视觉参考
- 📚 **教育内容** - 将小说改编为视觉化教材
- 🎬 **独立制作** - 个人创作者的制作流程工具

## 🔧 工作流程

```mermaid
graph LR
    A[原始剧本] --> B[场景解析]
    B --> C[拍摄脚本]
    C --> D[分镜头生成]
    D --> E[提示词创建]
    E --> F[Markdown输出]
```

## ⚠️ 注意事项

1. **剧本格式** - 建议使用"第X场"标记场景，支持章节格式
2. **对话格式** - 使用"角色名：对话内容"格式
3. **模型选择** - 更高级的模型（如GPT-4）能提供更好的网感和创意
4. **API限制** - 注意API调用频率和token限制
5. **文件编码** - 确保文本文件使用UTF-8编码

## 🤝 贡献指南

我们欢迎各种形式的贡献！

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- 感谢所有贡献者的努力
- 感谢 OpenAI 提供的强大AI能力
- 感谢各个AI服务提供商的支持

## 📞 联系我们

- 提交 Issue：[GitHub Issues](https://github.com/looneyren/StoryLoom/issues)
- 讨论：[GitHub Discussions](https://github.com/looneyren/StoryLoom/discussions)

---

<div align="center">

**StoryLoom - 编织故事与视觉的桥梁，让创意成为现实**

⭐ 如果这个项目对你有帮助，请给我们一个星标！

</div>