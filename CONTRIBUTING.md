# 贡献指南

感谢您对 StoryLoom 项目的关注！我们欢迎各种形式的贡献。

## 🚀 快速开始

### 开发环境设置

1. Fork 并克隆项目
```bash
git clone https://github.com/looneyren/StoryLoom.git
cd StoryLoom
```

2. 创建虚拟环境
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

4. 运行测试
```bash
python script_adapter.py examples/yyds.txt
```

## 📝 如何贡献

### 报告问题

使用 [GitHub Issues](https://github.com/looneyren/StoryLoom/issues) 报告：
- 🐛 Bug 报告
- 💡 功能请求
- 📚 文档改进
- ❓ 使用问题

**报告 Bug 时请包含：**
- 操作系统信息
- Python 版本
- 详细的错误信息
- 重现步骤
- 预期结果 vs 实际结果

### 提交代码

1. **创建分支**
```bash
git checkout -b feature/your-feature-name
# 或
git checkout -b fix/bug-description
```

2. **编写代码**
- 遵循现有代码风格
- 添加必要的注释
- 确保代码可读性

3. **测试更改**
```bash
# 测试基础功能
python script_adapter.py examples/yyds.txt

# 测试 AI 功能（需要 API 密钥）
export OPENAI_API_KEY="your-key"
python script_adapter.py examples/yyds.txt
```

4. **提交更改**
```bash
git add .
git commit -m "feat: add new feature description"
# 或
git commit -m "fix: fix bug description"
```

5. **推送并创建 PR**
```bash
git push origin feature/your-feature-name
```

然后在 GitHub 上创建 Pull Request。

## 🎯 代码规范

### 提交信息格式

使用 [Conventional Commits](https://www.conventionalcommits.org/) 格式：

- `feat:` 新功能
- `fix:` 修复 bug
- `docs:` 文档更新
- `style:` 代码格式（不影响功能）
- `refactor:` 重构代码
- `test:` 添加或修改测试
- `chore:` 构建过程或工具变动

**示例：**
```
feat: add support for new AI model
fix: resolve parsing error with special characters
docs: update installation instructions
```

### Python 代码风格

- 使用 4 个空格缩进
- 行长度不超过 88 字符
- 使用有意义的变量名
- 添加类型注解（Python 3.7+）
- 编写清晰的文档字符串

### 文件组织

```
script-adapter/
├── script_adapter.py      # 主程序
├── examples/             # 示例文件
├── docs/                # 文档
├── test/               # 测试文件（被 .gitignore 忽略）
└── README.md           # 项目说明
```

## 🔧 功能开发指导

### 添加新的 AI 服务支持

1. 确保新服务兼容 OpenAI API 格式
2. 在 README.md 中添加配置示例
3. 测试所有核心功能
4. 更新文档

### 改进解析逻辑

1. 在 `parse_original_script` 方法中添加新的格式支持
2. 确保向后兼容
3. 添加测试用例
4. 更新输入格式文档

### 优化输出格式

1. 修改 `save_to_markdown` 方法
2. 保持现有格式兼容性
3. 更新示例输出
4. 测试各种场景

## 🧪 测试

目前项目主要依赖手动测试，将来可能会添加自动化测试。

### 手动测试清单

- [ ] 基础模式功能正常
- [ ] AI 增强模式功能正常
- [ ] 不同格式的输入文件
- [ ] 各种命令行参数组合
- [ ] 错误处理和边界情况
- [ ] 输出文件格式正确

## 📚 文档

### 更新文档时请确保：

- README.md 保持最新
- 示例代码可以正常运行
- API 更改反映在文档中
- 添加新功能的使用说明

## ❓ 需要帮助？

- 查看 [README.md](README.md) 了解基础使用
- 浏览 [Issues](https://github.com/looneyren/StoryLoom/issues) 寻找答案
- 创建新的 Issue 询问问题
- 参与 [Discussions](https://github.com/looneyren/StoryLoom/discussions)

## 🙏 致谢

感谢所有贡献者的努力！每一个贡献都让这个项目变得更好。

---

**记住：没有贡献太小，每个帮助都很重要！** ✨