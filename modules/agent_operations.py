from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from modules.tool_operations import fetch_tool_objects, fetch_tools
from langgraph.prebuilt import create_react_agent
from modules.llm_config import llm
from modules.db_config import db
from bson import ObjectId

def agent_creation():
    agents_collection = db['agents']

    agent_name = input("\nEnter Agent Name: ")
    agent_description = input("Enter Agent Description: ")
    agent_prompt = input("Enter Agent Prompt: ")
    
    agent_data = {
        "name": agent_name,
        "description": agent_description,
        "prompt": agent_prompt
    }

    result = agents_collection.insert_one(agent_data)

    print(f"\n✅ Created agent with object id: {result.inserted_id} ✅\n\n")

def fetch_agents():
    agents_collection = db['agents']
    agents = agents_collection.find()
    available_agents = []
    for i, agent in enumerate(agents, start=1):
        available_agents.append({
            "reference_id": i,
            "agent_id": str(agent.get("_id")),
            "agent_name": agent.get("name"),
            "agent_description": agent.get("description"),
            "agent_prompt": agent.get("prompt"),
            "tools": agent.get("tools")
        })
    
    return available_agents

def display_agents(agents):
    if agents is None or len(agents) == 0:
        agents = fetch_agents()
    
    print("\n\nAvailable Agents:\n")
    for agent in agents:
        print(f"  - Reference ID: {agent['reference_id']}, Agent ID: {agent['agent_id']}, Name: {agent['agent_name']}, Description: {agent['agent_description']}, Prompt: {agent["agent_prompt"][:30]}...{agent["agent_prompt"][-30:]}")

def invoke_agent(agent, state):
    if agent['tools'] is None:
        agent['tools'] = []
    tool_ids = [tool_id for tool_id in agent['tools']]
    tools = fetch_tool_objects(tool_ids)
    worker_agent = create_react_agent(
        model=llm,
        tools=tools,
        prompt=ChatPromptTemplate([
            agent['agent_prompt'], 
            MessagesPlaceholder("messages")
        ]),
        name=agent['agent_name'],
    )
    agent_response = worker_agent.invoke({
        "messages": state
    })
    return agent_response["messages"][-1]

def map_agents_tools():
    agents = fetch_agents()
    for agent in agents:
        print(f"  - Reference ID: {agent['reference_id']}, Name: {agent['agent_name']}")

    agent_id_input = input("\nEnter the Reference ID of an agent to select: ")
    try:
        selected_agent_id = int(agent_id_input)
        selected_agent = next(agent for agent in agents if agent["reference_id"] == selected_agent_id)
    except Exception:
        print("\n❌ Invalid input. Please enter a valid numeric Reference ID. ❌")
        return

    tools = fetch_tools()
    print("\n\nAvailable Tools:")
    for tool in tools:
        print(f"  - Reference ID: {tool['reference_id']}, Name: {tool['tool_name']}")

    tool_ids_input = input("\nEnter comma-separated Reference IDs of tools to select: ")
    try:
        selected_tool_ids = [int(tool_id.strip()) for tool_id in tool_ids_input.split(',')]
        selected_tools = [tool for tool in tools if tool["reference_id"] in selected_tool_ids]
        selected_tool_ids = [selected_tool["tool_id"] for selected_tool in selected_tools]
    except Exception:
        print("\n❌ Invalid input. Please enter valid numeric Reference IDs. ❌")
        return

    if len(selected_tools) != len(selected_tool_ids):
        print("\n❌ Some Tool IDs were not found. Please try again. ❌")
        return

    agents_collection = db['agents']
    agents_collection.update_one(
        {"_id": ObjectId(selected_agent["agent_id"])},
        {"$set": {"tools": selected_tool_ids}}
    )

    print("✅ Tools mapped successfully!")
