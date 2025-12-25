---
description: 'Run create-story, story-context, dev-story, and conditionally code-review'
---

# Pre-Workflow Setup
Create a new branch using the story ID (Px-x-x). All development for this workflow will be on this branch.

---

## Method: execute-workflow

<bad_method name="execute-workflow" required_param="workflow-config">
IT IS CRITICAL THAT YOU FOLLOW THESE STEPS - while staying in character as the current agent persona you may have loaded:
<steps CRITICAL="TRUE">
1. Always LOAD the FULL @.bmad/core/tasks/workflow.xml
2. READ its entire contents - this is the CORE OS for EXECUTING the specific workflow-config
3. Pass the provided 'workflow-config' parameter to the workflow.xml instructions
4. Follow workflow.xml instructions EXACTLY as written to process and follow the specific workflow config and its instructions
5. Save outputs after EACH section when generating any documents from templates
</steps>
</bad_method>

---

## Workflow Sequence

1. **create-story**
   - Execute: `execute-workflow(.bmad/bmm/workflows/4-implementation/create-story/workflow.yaml)`
   - Then: Open a GitHub issue

2. **story-context**
   - Execute: `execute-workflow(.bmad/bmm/workflows/4-implementation/story-context/workflow.yaml)`

3. **dev-story**
   - Execute: `execute-workflow(.bmad/bmm/workflows/4-implementation/dev-story/workflow.yaml)`

4. **code-review** *(conditional)*
   - Condition: Only if status indicates review is needed
   - Execute: `execute-workflow(.bmad/bmm/workflows/4-implementation/code-review/workflow.yaml)`

---

## Post-Workflow Finalization

1. Commit and push changes
2. Look up the GitHub issue link in backlog or sprint-status documents
3. Create a pull request tied to the appropriate GitHub issue
   - If PR already exists, add to existing one
4. Close out the GitHub issue
5. If this is the last story of the epic AND all GitHub actions pass → merge PR
   - If tests fail, fix until passing before merge
6. Move to next story