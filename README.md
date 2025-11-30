# Mirobody

### The Open-Source, Self-Hosted MCP Server Solution for Your Data

**Next-Generation AI-Native Data Analysis Platform**

Mirobody is a modern, privacy-first platform designed to bridge your data with the latest AI capabilities. It serves as a universal adapter for your tools, compliant with the Model Context Protocol (MCP).

---

## 🌟 Why Mirobody?

Mirobody isn't just another chatbot wrapper. It is a **Dual MCP Architecture** system that revolutionizes how AI interacts with your local data:
Mirobody isn't just another chatbot wrapper. It is a system that revolutionizes how AI interacts with your local data:

* 🚀 **Write Tools Once, Use Everywhere**
    Build tools in standard Python once. Mirobody automatically bridges them to **ChatGPT** (via native Apps-SDK) and **the entire MCP Ecosystem** (Claude, Cursor, IDEs), ensuring your code runs seamlessly across platforms.

* 🤖 **Native Agent Engine & Analysis**
    Powered by a **self-developed agent engine** that fully reproduces **Claude Code's** capabilities locally. Designed to directly load standard **Claude Agent Skills** (Coming Soon) for infinite extensibility.

* 📂 **Store Data Locally, Context Everywhere**
    Your personal data resides permanently on your local encrypted storage but serves as instant context for **any connected AI**. No need to upload files repeatedly—your data remains private while powering your entire workflow.

* 🛡️ **Secure Dual MCP Architecture**
    Works simultaneously as an **MCP Client** (consuming tools) and an **OAuth-enabled MCP Server** (providing tools). This unique architecture enables complex tool orchestration while ensuring secure, authenticated access.

---

## 🏥 Showcase: Health Data Platform

To demonstrate the capability of Mirobody, we have included a comprehensive **Health Data Analysis** suite out-of-the-box. This proves that Mirobody can handle complex, multi-modal, and sensitive data environments.

* **Broad Integration**: Connects with **300+ device manufacturers**, Apple Health, and Google Health.
* **EHR Ready**: Compatible with systems covering **90% of the US population's** Electronic Health Records.
* **Multi-Modal**: Analyze health via Voice, Image, Files, or Text.

> *💡 **Tip:** The platform adapts to your tools. Want to build a Finance Analyzer or DevOps Bot instead? Just swap the files in the `tools/` directory!*

---

## ⚡ Quick Start

### 1. Configuration
Initialize your environment in seconds:

```bash
cd config
cp config.example.yaml config.yaml
````

> **Note**:
>
>   * **LLM Setup**: `OPENROUTER_API_KEY` is required.
>   * **Auth Setup**: To enable **Google/Apple OAuth** or **Email Verification**, fill in the respective fields in `config.yaml`.
>   * All API keys are encrypted automatically.

### 2\. Create Your Tools

Mirobody adopts a **"Tools-First"** philosophy. No complex binding logic is required. Simply drop your Python scripts into the `tools/` directory:

  * ✨ **Zero Config**: The system auto-discovers your functions.
  * 🐍 **Pure Python**: Use the libraries you love (Pandas, NumPy, etc.).
  * 🔧 **Universal**: A single tool file works for both REST API and MCP.

### 3\. Deployment

Launch the platform using our unified deployment script.

**Option A: Local Mode**
*Builds everything from scratch.*

```bash
./deploy.sh --mode=local
```

**Option B: Cloud Mode (ARM ready, x86 coming soon)**
*Downloads pre-built images.*

```bash
./deploy.sh --mode=image
```

**Daily Startup**
*For regular use after initial setup, simply run:*

```bash
./deploy.sh
```

-----

## 🔐 Access & Authentication

Once deployed, you can access the platform through the local web interface or our official hosted client.

### 1\. Access Interfaces

| Interface | URL | Description |
|-----------|-----|-------------|
| **Local Web App** | `http://localhost:18080` | Fully self-hosted web interface running locally. |
| **Official Client**| [https://my.mirobody.ai](https://my.mirobody.ai) | **Recommended.** Our official web client that connects securely to your local backend service. |
| **MCP Server** | `http://localhost:18080/mcp` | For Claude Desktop / Cursor integration. |

### 2\. Login Methods

You can choose to configure your own authentication providers or use the pre-set demo account.

  * **Social Login**: Google Account / Apple Account (Requires configuration in `config.yaml`)
  * **Email Login**: Email Verification Code (Requires configuration in `config.yaml`)
  * **Demo Account** (Instant Access):
      * **Users:** `demo1@mirobody.ai`, `demo2@mirobody.ai`, `demo3@mirobody.ai` (More demo users configurable in `config.yaml`)
      * **Password:** `777777`

-----

## 🔌 API Reference

Mirobody provides standard endpoints for integration:

| Endpoint | Description | Protocol |
|----------|-------------|----------|
| `/mcp` | MCP Protocol Interface | JSON-RPC 2.0 |
| `/api/chat` | AI Chat Interface | OpenAI Compatible |
| `/api/history` | Session Management | REST |

-----

\<p align="center"\>
\<sub\>Built with ❤️ for the AI Open Source Community.\</sub\>
\</p\>
