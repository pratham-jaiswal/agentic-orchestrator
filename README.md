![](https://res.cloudinary.com/dhzmockpa/image/upload/v1747072197/Agentic_Orchestrator_f0ezqh.png)

# 🧠 Agentic Orchestrator

Agentic Orchestrator is a lightweight command-line tool for building, managing, and executing AI agents, tools, and workflows using LangChain and LangGraph. It’s ideal for rapid prototyping and orchestration of agent-driven workflows.

---

## ⚙️ Features

- 🧰 **Create Agents** with assigned tools
- 🔧 **Define Tools** using Python code in the correct format (refer [this](https://github.com/pratham-jaiswal/agentic-orchestrator/blob/main/sample_codes/README.md))
- 🔗 **Map Tools to Agents** to extend their functionality
- 🧬 **Create Workflows** combining agents for specific tasks
- 🚀 **Invoke Workflows** directly from the CLI
- 🖥️ **Interactive CLI** menu for ease of use

---

## 📂 Project Structure

```
.
├── main.py                         # CLI entry point for user interaction
├── modules/
│   ├── agent_operations.py         # Handles agent creation, listing, and tool mapping
│   ├── tool_operations.py          # Manages tool creation, listing, and tool management
│   ├── workflow_operations.py      # Manages workflow creation, listing, and invocation
│   ├── db_config.py                # Configuration for MongoDB database connection
│   └── llm_config.py               # Configuration for Large Language Models (LLMs)
├── sample_codes/
│   ├── README.md                   # Instructions and guidelines for creating tools
│   └── *.py                        # Sample Python code files for tool creation
├── requirements.txt                # Python dependencies for the project
└── README.md                       # Project overview and documentation
```

---

## 🧩 Tool Development Guidelines

Read this [guide](https://github.com/pratham-jaiswal/agentic-orchestrator/blob/main/sample_codes/README.md).

---

## 📦 Requirements

- Python **3.13.3**
- [LangChain](https://www.langchain.com/)
- [LangGraph](https://www.langchain.com/langgraph)
- [OpenAI API Key](https://platform.openai.com/api-keys)
- [PyMongo](https://github.com/mongodb/mongo-python-driver)
- [Astor](https://github.com/berkerpeksag/astor)


### 🔧 Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 🧪 Running the CLI

Launch the tool using:

```bash
python main.py
```

You'll see an interactive menu:

```
--------------------------------------
What would you like to do?
1. Create an Agent
2. Fetch all Agents
3. Create a Tool
4. Fetch all Tools
5. Map Tools to an Agent
6. Create a Workflow
7. Fetch all Workflows
8. Invoke a Workflow
9. Exit
```

Follow the prompts to build and run agent-based workflows.

---