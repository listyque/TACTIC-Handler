// Fields from Handler AdminProcessFields.qml; native keys are unchanged.
export const fieldGroups = [
  {
    "title": "Appearance",
    "description": "",
    "fields": [
      {
        "section": "properties",
        "key": "label",
        "label": "Display label",
        "help": "Shown on the canvas without changing the process name.",
        "editor": "text"
      },
      {
        "section": "properties",
        "key": "color",
        "label": "Color",
        "help": "Used for this process on the canvas and in task views.",
        "editor": "color"
      }
    ]
  },
  {
    "title": "Task settings",
    "description": "Assignment choices and default estimates for this process.",
    "kinds": [
      "manual",
      "node",
      "approval"
    ],
    "fields": [
      {
        "section": "properties",
        "key": "assigned_group",
        "label": "Assigned group",
        "help": "Limits the available assignees to members of this group.",
        "options": "groups"
      },
      {
        "section": "properties",
        "key": "supervisor_group",
        "label": "Supervisor group",
        "help": "Limits the available supervisors to members of this group.",
        "options": "groups"
      },
      {
        "section": "properties",
        "key": "duration",
        "label": "Default duration, days",
        "help": "Initial interval between a task's start and end dates.",
        "editor": "integer"
      },
      {
        "section": "properties",
        "key": "bid_duration",
        "label": "Estimated work, hours",
        "help": "Default planned effort for a new task.",
        "editor": "integer"
      },
      {
        "section": "properties",
        "key": "completion",
        "label": "Completion, %",
        "help": "Completion level represented by this process or status.",
        "editor": "integer",
        "maximum": 100
      },
      {
        "section": "properties",
        "key": "task_creation",
        "label": "Create tasks",
        "help": "Include this process when generating tasks.",
        "editor": "boolean",
        "initial": true
      },
      {
        "section": "properties",
        "key": "autocreate_task",
        "label": "Create tasks automatically",
        "help": "Create a task when a workflow event reaches this process.",
        "editor": "boolean"
      },
      {
        "section": "",
        "key": "task_number",
        "label": "Number of tasks",
        "help": "How many tasks to create for this process.",
        "editor": "integer",
        "minimum": 1
      }
    ]
  },
  {
    "title": "Approval",
    "description": "Default reviewer for approval tasks.",
    "kinds": [
      "approval"
    ],
    "fields": [
      {
        "section": "default",
        "key": "assigned",
        "label": "Assigned user",
        "help": "Choose an existing user to receive approval tasks.",
        "options": "users"
      }
    ]
  },
  {
    "title": "Related workflow",
    "description": "Choose which objects and processes this node signals or tracks.",
    "kinds": [
      "dependency",
      "progress"
    ],
    "fields": [
      {
        "key": "related_search_type",
        "label": "Search Type",
        "help": "The related objects affected by this node.",
        "options": "searchTypes"
      },
      {
        "key": "related_pipeline_code",
        "label": "Related pipeline",
        "help": "Only pipelines of the selected Search Type are listed.",
        "options": "relatedPipelines"
      },
      {
        "key": "related_process",
        "label": "Related process",
        "help": "The process to signal or listen to; leave empty to use the native default.",
        "options": "relatedProcesses"
      },
      {
        "key": "related_scope",
        "label": "Scope",
        "help": "Affect related objects only, or all objects of this Search Type.",
        "choices": [
          {
            "identity": "local",
            "label": "Related objects"
          },
          {
            "identity": "global",
            "label": "All objects"
          }
        ],
        "initial": "local"
      },
      {
        "key": "related_status",
        "label": "Signal",
        "help": "The native workflow signal sent to the related process.",
        "choices": [
          {
            "identity": "Pending",
            "label": "Pending"
          },
          {
            "identity": "Action",
            "label": "Action"
          },
          {
            "identity": "Complete",
            "label": "Complete"
          }
        ],
        "kinds": [
          "dependency"
        ]
      },
      {
        "key": "related_wait",
        "label": "Wait for completion",
        "help": "Wait for a completion signal instead of completing this node immediately.",
        "editor": "boolean",
        "kinds": [
          "dependency"
        ]
      },
      {
        "key": "expression",
        "label": "Related object expression",
        "help": "Optional TACTIC search expression; it replaces selection by Search Type.",
        "editor": "text"
      }
    ]
  },
  {
    "title": "Status behavior",
    "description": "Map this status to a native behavior, or explicitly change a connected process.",
    "kinds": [
      "status"
    ],
    "fields": [
      {
        "section": "default",
        "key": "mapping",
        "label": "Behave as",
        "help": "Native task status behavior.",
        "choices": [
          {
            "identity": "Assignment",
            "label": "Assignment"
          },
          {
            "identity": "Pending",
            "label": "Pending"
          },
          {
            "identity": "In Progress",
            "label": "In Progress"
          },
          {
            "identity": "Waiting",
            "label": "Waiting"
          },
          {
            "identity": "Need Assistance",
            "label": "Need Assistance"
          },
          {
            "identity": "Revise",
            "label": "Revise"
          },
          {
            "identity": "Reject",
            "label": "Reject"
          },
          {
            "identity": "Complete",
            "label": "Complete"
          },
          {
            "identity": "Approved",
            "label": "Approved"
          }
        ]
      },
      {
        "section": "default",
        "key": "direction",
        "label": "Change process",
        "help": "Used when no status mapping is selected.",
        "choices": [
          {
            "identity": "output",
            "label": "Output process"
          },
          {
            "identity": "input",
            "label": "Input process"
          },
          {
            "identity": "process",
            "label": "This process"
          }
        ]
      },
      {
        "section": "default",
        "key": "status",
        "label": "Target status",
        "help": "Exact status name understood by the target process.",
        "editor": "text"
      }
    ]
  }
]
