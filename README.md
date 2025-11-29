# Mirobody Demo

**Next-Generation AI-Native Data Analysis Platform**

A modern data analysis platform with native support for:
- 🚀 **Write Tools Once, Use Everywhere** - One codebase, multiple AI clients
- 🔐 **OAuth MCP Server** - Standard MCP protocol with OAuth authentication
- 🤖 **Claude Apps Skills** - Seamless integration with Claude
- 🔌 **OpenAI Apps-SDK** - Direct ChatGPT integration
- 🔒 **100% Local Deployment** - Complete privacy control with full local deployment. All user personalized data is stored locally on your own infrastructure.

Build any data analysis capability you need - the platform adapts to your tools, not the other way around.


---

## 🏥 Showcase: Health Data Analysis Platform

As a capability demonstration, we've built a comprehensive health data analysis platform:

**Data Integration:**
- 📱 **300+ Device Manufacturers** - Support for diverse health devices
- 🍎 **Apple Health & Google Health** - With companion mobile apps
- 🏥 **EHR Integration** - Covering 90% of US population's electronic health records
- 💬 **Multi-Modal Input** - Voice, live chat, images, files, text, and more

**Focus on Tools, Not Configuration:**
The entire platform is powered by custom tools in the `tools/` directory. Want to build something different? Just write your own tools.

---

## Setup

1. Copy the example configuration file:
```bash
cd config
cp config.example.yaml config.yaml
```

2. Modify your configuration file:
   - **OPENROUTER_API_KEY** is **required** (needed for LLM connection)
   - **SERPER_API_KEY** (optional, needed for web search/crawler functionality)
   - Other parameters: refer to `config.example.yaml` and modify as needed
   - **Note**: All API keys will be automatically encrypted

3. **Tools-First Thinking**: Just write your Python tool files in the `tools/` directory. That's it!
   - ✨ **It's that simple** - No complex configuration needed
   - 🔧 Give it any tools, and it becomes whatever you want it to be
   - 💡 The power lies in the tools you provide, not just the prompts
   - 🚀 Focus on what you want to build, not how to configure it

## Deployment

```bash
# One-click deployment
./deploy.sh
```

4. Open browser and login:
   - **Service URL**: http://localhost:18080
   - **Login options**:
     - Google account
     - Apple account  
     - Pre-configured demo accounts: `demo@mirobody.ai` / `777777`

**That's it!** Your service now runs as:
- 🌐 Web application at http://localhost:18080
- 🔌 OAuth-enabled MCP server (use with Claude Desktop, etc.)
- 🤖 OpenAI-compatible endpoint (use directly in ChatGPT)

Enjoy it!
---

## 📊 Quick Test

```bash
# Test local wheel installation
./shell/test_local_install.sh

# Get MCP tools list
./shell/get_tools.sh

# Expected: 16 available tools
```

---

## 🔄 Update Mirobody

### Quick Update

```bash
./shell/update_mirobody.sh
```

### Manual Update

```bash
# 1. Update pip package
pip install --upgrade mirobody \
    --extra-index-url https://dev-nexus.aws.thetahealth.ai/repository/pypi-ai-snapshots/simple/

# 2. Rebuild Docker images
./deploy.sh
```

## 🔌 API Endpoints

| Endpoint | Description |
|----------|-------------|
| `http://localhost:18080/mcp` | MCP protocol interface (JSON-RPC 2.0) |
| `http://localhost:18080/api/chat` | AI chat interface |
| `http://localhost:18080/api/history` | Session history |

---
