from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from modules.agent_operations import fetch_agents, display_agents, invoke_agent
from typing_extensions import TypedDict
from typing import Annotated, Optional
from modules.llm_config import llm
from modules.db_config import db
import json

def create_workflow():
    workdlows_collection = db['workflows']

    agents = fetch_agents()
    display_agents(agents)

    workflow_name = input("\nEnter Workflow Name: ")
    workflow_description = input("Enter Workflow Description: ")

    selected_ids_input = input("Enter comma-separated Agent Reference IDs to include in the workflow: ")
    try:
        selected_ids = [int(agent_id.strip()) for agent_id in selected_ids_input.split(',')]
    except Exception:
        print("\n❌ Invalid input. Please enter only numeric Agent Reference IDs. ❌")
        return

    selected_agents = [agent for agent in agents if agent["reference_id"] in selected_ids]
    if len(selected_agents) != len(selected_ids):
        print("\n❌ Some Agent IDs were not found. Please try again. ❌")
        return

    workflow_nodes = []
    print("\nNow, define the connections between the selected agents.")
    for agent in selected_agents:
        while True:
            print(f"\nAgent {agent['reference_id']} - {agent['agent_name']}")
            conn_input = input("\nEnter connected Agent IDs (comma-separated) or press Enter for none: ")

            if conn_input.strip() == "":
                connects = []
                break
            try:
                connects = [int(cid.strip()) for cid in conn_input.split(',')]
            except Exception:
                print("\n❌ Invalid input. Please enter only numeric Agent Reference IDs. ❌")
                continue

            if any(cid == agent["reference_id"] for cid in connects):
                print("\n❌ An agent cannot connect to itself. Please try again. ❌")
                continue

            if all(cid in selected_ids for cid in connects):
                break
            else:
                print("\n❌ One or more Agent Reference IDs are invalid or not in the selected workflow. Please try again. ❌")

        ref_to_agent = {agent["reference_id"]: agent["agent_id"] for agent in selected_agents}
        connects = [ref_to_agent[cid] for cid in connects if cid in ref_to_agent]

        workflow_nodes.append({
            "agent_id": agent["agent_id"],
            "name": agent["agent_name"],
            "description": agent["agent_description"],
            "connects": connects
        })

    print("\n\n✅ Workflow Details:")
    print(f"Name: {workflow_name}")
    print(f"Description: {workflow_description}")
    print("Nodes:")
    for node in workflow_nodes:
        print(f"  - Obj ID: {node['agent_id']}, Name: {node['name']}, Connects: {node['connects']}")

    workflow_data = {
        "workflow_name": workflow_name,
        "workflow_description": workflow_description,
        "workflow": workflow_nodes
    }

    result = workdlows_collection.insert_one(workflow_data)

    print(f"\n✅ Created workflow with object id: {result.inserted_id}")

def fetch_workflows():
    workflows_collection = db['workflows']
    workflows = workflows_collection.find()

    available_workflows = []
    for i, workflow in enumerate(workflows, start=1):
        available_workflows.append({
            "reference_id": i,
            "workflow_id": str(workflow.get("_id")),
            "workflow_name": workflow.get("workflow_name"),
            "workflow_description": workflow.get("workflow_description"),
            "workflow": workflow.get("workflow")
        })
    
    return available_workflows

def display_workflows(workflows):
    if workflows is None or len(workflows) == 0:
        workflows = fetch_workflows()
    print("\n\nAvailable Workflows:\n")
    for workflow in workflows:
        print(f"  - Reference ID: {workflow['reference_id']}, Workflow ID: {workflow['workflow_id']}, Name: {workflow['workflow_name']}, Description: {workflow['workflow_description']}")

def select_workflow():
    workflows = fetch_workflows()
    display_workflows(workflows)

    selected_id_input = input("\nEnter the Reference ID of a workflow to select: ")
    try:
        selected_id = int(selected_id_input)
    except Exception:
        print("\n❌ Invalid input. Please enter only a numeric Reference ID. ❌")
        return

    selected_workflow = next((workflow for workflow in workflows if workflow["reference_id"] == selected_id), None)
    if selected_workflow is None:
        print("\n❌ No workflow found with that Reference ID. Please try again. ❌")
        return

    return selected_workflow

def decide_next_node(state, selected_workflow):
    class DecidingSupervisorResponseFormat(TypedDict):
        next_node: Annotated[str, ..., "Node ID"]
        reasoning: Annotated[str, ..., "Reasoning"]
        instructions: Annotated[str, ..., "Instructions"]
        direct_response: Annotated[Optional[str], None, "Response to user"]
    
    deciding_supervisor_prompt = f"""
        You are a **supervising node/agent** in a directed graph-based team workflow.
        Your job is to oversee and manage task delegation until the user's original task is fully completed.

        Each team member is a node/agent in a graph, connected through the `connects` field.
        When a node finishes its part of the task, you—the supervisor—are informed.
        You must then decide which connected node should handle the next part of the task.
        Delegation is only allowed to nodes listed in the current node’s `connects`.
        Each agent may or may not have a set of tools, the details of which can only be answered by the node itself.

        ---

        ### 🎯 Primary Objective:

        Ensure the **user's task is fully and efficiently completed** by coordinating the workflow through the graph of capable agents.

        ---

        ### 🧠 Your Responsibilities:

        - Understand the **user’s overall task** and the **team structure**.
        - Break down the task into logical subtasks using each member’s `description`.
        - After each node completes a task:
        - Assess progress made so far.
        - Choose the next node from the available `connects`.
        - Provide the selected node with:
            - Relevant task context.
            - A clear description of what they need to do.
            - Any work already completed.

        - Avoid unnecessary or redundant assignments.
        - Make decisions based on:
            - **Skill alignment**
            - **Task continuity**
            - **Workflow logic**

        ---

        ### 🧾 You Will Receive:

        - The full **team structure**, including:
        - `name`, `node` (ID), `description`, and `connects` for each team member.
        - The **original user task**.
        - The **current state**, including:
            - The node that just completed its work.
            - Progress or outputs so far.
            - Chat history and context (always check this before deciding).

        ---

        ### 🧾 Your Output Must Include:

        1. **next_node**: ID of the next node (or `FINISH` if the task is done).
        2. **reasoning**: Justify why this node was chosen, based on the user query, their description and graph connections.
        3. **instructions**: Provide only the specific question or request the user asked.
        4. **direct_response**: A response to the user – only use when you give `next_node` as `FINISH`.

        ---

        ### ⚠️ Constraints:

        - You **can only choose from the current node’s `connects`**.
        - Never allow a node to delegate to itself.
        - If `connects` of previously used agent is empty, or the user just asked a general question (e.g., greetings or “what is your role”), respond with `FINISH` in `next_node`.
        - Once the workflow has started you may not finish until it’s complete (the previous agent has no connects).
        - Don’t assign tasks unless necessary—be efficient and purposeful.
        - Ensure each node receives enough information to pick up the task without confusion.
        - Stick to what user asked for and don't at all respond or ask your agents to respond with stuff user didn't ask for.
        - If the user's message is only requesting **information about agent(s)** (e.g., tools, roles, capabilities), DO NOT interpret it as the start or continuation of a workflow. Only gather and return the requested information.


        **❗ Strict Behavior Rule:**
        - When responding to a user request **about agent(s)**, you must ensure:
            - Agents respond **only to the question asked**, such as their capabilities, tools, or status.
            - Agents must **not begin performing their usual tasks** unless the user explicitly asks them to.
            - If you are querying multiple agents on behalf of the user, provide only the **exact query context** in `instructions`—do not imply task initiation.
            - DO NOT `FINISH` before asking the agent.
        ---

        ### 💬 Special Instruction:

        - You orchestrate the <given workflow> to ensure the user’s task is completed efficiently.
        - If the user asks about **any specific or all agent(s)** and you do **not already know** the answer:
            - You MUST **invoke and query** the relevant agent(s) directly to get accurate information.
            - You MUST prevent any agent from taking action **beyond answering** the specific user query.
            - Never assume or guess an agent's internal capabilities or tools unless explicitly provided.
            - ⚠️ If the user only asked about a **specific agent or their properties**, you need **NOT** follow with the workflow/graph or assign new tasks afterward—only return the requested information.
            - ⚠️ If the user asks about **all agents**, gather the requested information from each one, then return `FINISH` after collecting their responses. Do not initiate or resume the task workflow unless the user explicitly asks for it.

        Then provide the workflow details from the `Given Workflow` section below.

        ---

        ### 🧩 Given Workflow:
        {json.dumps(selected_workflow, indent=2)}
    """


    messages = [SystemMessage(content=deciding_supervisor_prompt)] + state

    supervisor_response = llm.with_structured_output(DecidingSupervisorResponseFormat).invoke(messages)

    return supervisor_response

def invoke_workflow():
    try:
        selected_workflow = select_workflow()
        agent_ids = [node["agent_id"] for node in selected_workflow["workflow"]] + ["FINISH"]
    except Exception:
        return

    user_prompt = input("\nYou: ")
    state = [HumanMessage(content=user_prompt, name="user")]

    supervisor_response = ""
    while True:
        supervisor_response = decide_next_node(state, selected_workflow)
        if supervisor_response["next_node"] == "FINISH":
            if "direct_response" in supervisor_response:
                print(f"\n{supervisor_response["direct_response"]}\n")
            else:
                print("\nWorkflow complete.\n")
            break
        elif supervisor_response["next_node"] in agent_ids:
            state.append(AIMessage(content=supervisor_response['instructions'], name="supervisor"))
            
            next_agent = next((agent for agent in fetch_agents() if agent["agent_id"] == supervisor_response["next_node"]), None)
            agent_response = invoke_agent(next_agent, state)
            agent_response.pretty_print()
            state.append(agent_response)
    
    return None
