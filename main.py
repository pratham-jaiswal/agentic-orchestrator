from modules.workflow_operations import create_workflow, display_workflows, invoke_workflow
from modules.agent_operations import agent_creation, display_agents, map_agents_tools
from modules.tool_operations import tool_creation, display_tools

def main():
    while True:
        print("""\n--------------------------------------
What would you like to do?
1. Create an Agent
2. Fetch all Agents
3. Create a Tool
4. Fetch all Tools
5. Map Tools to an Agent
6. Create a Workflow
7. Fetch all Workflows
8. Invoke a Workflow
9. Exit\n""")
        
        choice = input("\nEnter your choice: ")
        try:
            choice = int(choice)
        except Exception:
            print("\n❌ Invalid input. Please enter a number. ❌")
            continue
        
        switcher = {
            1: agent_creation,
            2: lambda: display_agents(None),
            3: tool_creation,
            4: lambda: display_tools(None),
            5: map_agents_tools,
            6: create_workflow,
            7: lambda: display_workflows(None),
            8: invoke_workflow,
            9: exit
        }

        action = switcher.get(choice, lambda: print("\n❌ Invalid choice. Please try again. ❌\n"))
        action()

if __name__ == "__main__":
    main()