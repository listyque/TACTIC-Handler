export const DISPLAY_WIDGET_ARGS = [
  {
    "value": "",
    "class": "tactic.ui.common.base_table_element_wdg.SimpleTableElementWdg",
    "aliases": [
      "",
      "tactic.ui.common.base_table_element_wdg.SimpleTableElementWdg",
      "SimpleTableElementWdg",
      "TextWdg",
      "pyasm.widget.TextWdg",
      "tactic.ui.common.SimpleTableElementWdg",
      "pyasm.widget.SimpleTableElementWdg",
      "pyasm.widget.table_element_wdg.SimpleTableElementWdg",
      "pyasm.widget.input_wdg.TextWdg",
      "tactic.ui.common.base_table_element_wdg.RawTableElementWdg",
      "tactic.ui.common.RawTableElementWdg"
    ],
    "options": [
      {
        "name": "column",
        "title": "Column",
        "description": "Database column override to display in this cell",
        "category": "Display",
        "order": 1,
        "type": "TextWdg"
      }
    ]
  },
  {
    "value": "format",
    "class": "tactic.ui.table.format_element_wdg.FormatElementWdg",
    "aliases": [
      "format",
      "tactic.ui.table.format_element_wdg.FormatElementWdg",
      "FormatElementWdg",
      "tactic.ui.table.FormatElementWdg"
    ],
    "options": [
      {
        "name": "type",
        "title": "Type",
        "description": "Determines the type it should be displayed as",
        "category": "Required",
        "order": 1,
        "type": "tactic.ui.manager.FormatDefinitionEditWdg",
        "values": [
          "integer",
          "float",
          "percent",
          "currency",
          "date",
          "time",
          "scientific",
          "boolean",
          "text",
          "timecode"
        ],
        "default": "text"
      },
      {
        "name": "format",
        "title": "Format",
        "description": "Format pattern (e.g. -1234.12, YYYY-MM-DD, Checkbox)",
        "category": "Required",
        "order": 2,
        "type": "TextWdg"
      },
      {
        "name": "total_summary",
        "title": "Total Summary",
        "description": "Determines a calculation for the bottom row",
        "category": "Misc",
        "order": 2,
        "type": "SelectWdg",
        "values": [
          "count",
          "total",
          "average"
        ]
      },
      {
        "name": "constraint",
        "title": "Constraint",
        "description": "Determines what kind of index is put onto the created column",
        "category": "Misc",
        "order": 3,
        "type": "SelectWdg",
        "values": [
          "unique",
          "indexed"
        ]
      },
      {
        "name": "fps",
        "title": "Fps",
        "description": "Frames per second for timecode formatting (e.g. 24, 25, 30)",
        "category": "Misc",
        "order": 4,
        "type": "TextWdg"
      }
    ]
  },
  {
    "value": "expression",
    "class": "tactic.ui.table.expression_element_wdg.ExpressionElementWdg",
    "aliases": [
      "expression",
      "tactic.ui.table.expression_element_wdg.ExpressionElementWdg",
      "ExpressionElementWdg",
      "tactic.ui.table.ExpressionElementWdg",
      "expression_value",
      "ExpressionValueElementWdg",
      "tactic.ui.table.ExpressionValueElementWdg",
      "tactic.ui.table.expression_element_wdg.ExpressionValueElementWdg"
    ],
    "options": [
      {
        "name": "use_cache",
        "title": "Use Cache",
        "description": "Determines whether or not to use the cached value. Gets value from column with the same name as the element",
        "category": "Cache",
        "order": 0,
        "type": "SelectWdg",
        "values": [
          "true",
          "false"
        ]
      },
      {
        "name": "expression",
        "title": "Expression",
        "description": "Expression to evaluate the widget",
        "category": "Options",
        "order": 1,
        "type": "TextAreaWdg"
      },
      {
        "name": "display_expression",
        "title": "Display Expression",
        "description": "Expression for display purposes",
        "category": "Options",
        "order": 2,
        "type": "TextAreaWdg"
      },
      {
        "name": "display_format",
        "title": "Display Format",
        "description": "Predefined format for display",
        "category": "Options",
        "order": 3,
        "type": "TextWdg"
      },
      {
        "name": "link_expression",
        "title": "Link Expression",
        "description": "Expression for linking to another sobject",
        "category": "Options",
        "order": 4,
        "type": "TextAreaWdg"
      },
      {
        "name": "link_view",
        "title": "Link View",
        "description": "View to link result to another view",
        "category": "Options",
        "order": 5,
        "type": "TextWdg"
      },
      {
        "name": "order_by",
        "title": "Order By",
        "description": "Turn on Order by",
        "category": "Options",
        "order": 8,
        "type": "TextWdg"
      },
      {
        "name": "show_retired",
        "title": "Show Retired",
        "description": "true|false - true shows all the retired entries during the expression evaluation",
        "category": "Options",
        "order": 8,
        "type": "SelectWdg",
        "values": [
          "true",
          "false"
        ]
      },
      {
        "name": "group_by",
        "title": "Group By",
        "description": "Turn on Group by",
        "category": "Options",
        "order": 9,
        "type": "SelectWdg",
        "values": [
          "true",
          "false"
        ]
      },
      {
        "name": "group_by_time",
        "title": "Group By Time",
        "description": "Turn on Group by",
        "category": "Options",
        "order": 10,
        "type": "SelectWdg",
        "values": [
          "true",
          "false"
        ]
      },
      {
        "name": "justify",
        "title": "Justify",
        "description": "Result justification",
        "category": "Options",
        "order": 11,
        "type": "SelectWdg",
        "values": [
          "default",
          "left",
          "right",
          "center"
        ]
      },
      {
        "name": "filter_name",
        "title": "Filter Name",
        "description": "Name of filter to use",
        "category": "Options",
        "order": 12,
        "type": "TextWdg"
      },
      {
        "name": "mode",
        "title": "Mode",
        "description": "Display mode for this widget",
        "category": "Other Options",
        "order": 3,
        "type": "SelectWdg",
        "values": [
          "value",
          "check",
          "boolean"
        ]
      },
      {
        "name": "expression_mode",
        "title": "Expression Mode",
        "description": "If absolute mode is selected, it does not relate to the current SObject",
        "category": "Other Options",
        "order": 6,
        "type": "SelectWdg",
        "values": [
          "default",
          "absolute"
        ]
      },
      {
        "name": "calc_mode",
        "title": "Calc Mode",
        "description": "(ALPHA) fast|slow - fast uses new calculation mode. Only @SUM, @COUNT, @SOBJECT and @GET are current supported",
        "category": "Other Options",
        "order": 7,
        "type": "SelectWdg",
        "values": [
          "slow",
          "fast"
        ]
      },
      {
        "name": "bottom",
        "title": "Bottom",
        "description": "Expression to calculate the bottom row of the table",
        "category": "Other Options",
        "order": 99,
        "type": "TextAreaWdg"
      },
      {
        "name": "empty",
        "title": "Empty",
        "description": "vAlue to display if empty",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      },
      {
        "name": "group_bottom",
        "title": "Group Bottom",
        "description": "Expression to calculate the bottom of a group",
        "category": "Other Options",
        "order": 99,
        "type": "TextAreaWdg"
      },
      {
        "name": "inline_styles",
        "title": "Inline Styles",
        "description": "Styles to add to the DIV generated that contains the result of the expression",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      },
      {
        "name": "return",
        "title": "Return",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "SelectWdg",
        "values": [
          "single",
          "list"
        ]
      }
    ]
  },
  {
    "value": "link",
    "class": "tactic.ui.table.link_element_wdg.LinkElementWdg",
    "aliases": [
      "link",
      "tactic.ui.table.link_element_wdg.LinkElementWdg",
      "LinkElementWdg",
      "tactic.ui.table.LinkElementWdg"
    ],
    "options": [
      {
        "name": "empty",
        "title": "Empty",
        "description": "Text for an empty link",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      },
      {
        "name": "icon",
        "title": "Icon",
        "description": "Icon to display",
        "category": "Other Options",
        "order": 99,
        "type": "IconSelectWdg"
      }
    ]
  },
  {
    "value": "pyasm.widget.ThumbWdg",
    "class": "pyasm.widget.file_wdg.ThumbWdg",
    "aliases": [
      "pyasm.widget.ThumbWdg",
      "pyasm.widget.file_wdg.ThumbWdg",
      "ThumbWdg"
    ],
    "options": [
      {
        "name": "script_path",
        "title": "Script Path",
        "description": "Javascript path override for action when preview is clicked",
        "category": "Action",
        "order": 1,
        "type": "TextWdg"
      },
      {
        "name": "detail_class_name",
        "title": "Detail Class Name",
        "description": "Python widget to display in a new tab when preview is clicked",
        "category": "Action",
        "order": 2,
        "type": "TextWdg"
      },
      {
        "name": "icon_context",
        "title": "Icon Context",
        "description": "context on which the search is applied",
        "category": "Display",
        "order": 1,
        "type": "TextWdg"
      },
      {
        "name": "icon_size",
        "title": "Icon Size",
        "description": "control the icon size by percentage. e.g. 80%",
        "category": "Display",
        "order": 2,
        "type": "TextWdg"
      },
      {
        "name": "min_icon_size",
        "title": "Min Icon Size",
        "description": "The smallest size the icon will become on resize",
        "category": "Display",
        "order": 3,
        "type": "TextWdg"
      },
      {
        "name": "latest_icon",
        "title": "Latest Icon",
        "description": "whether to display the latest version under any context",
        "category": "Display",
        "order": 4,
        "type": "SelectWdg",
        "values": [
          "true",
          "false"
        ]
      },
      {
        "name": "filename",
        "title": "Filename",
        "description": "whether to display the main file name for download",
        "category": "Display",
        "order": 5,
        "type": "SelectWdg",
        "values": [
          "true",
          "false"
        ]
      },
      {
        "name": "original",
        "title": "Original",
        "description": "whether to display the original file when clicked on",
        "category": "Display",
        "order": 6,
        "type": "SelectWdg",
        "values": [
          "true",
          "false"
        ]
      },
      {
        "name": "file_type",
        "title": "File Type",
        "description": "whether to display the file type for download",
        "category": "Display",
        "order": 7,
        "type": "SelectWdg",
        "values": [
          "true",
          "false"
        ]
      },
      {
        "name": "detail",
        "title": "Detail",
        "description": "whether to display the single asset view when clicked on",
        "category": "Display",
        "order": 8,
        "type": "SelectWdg",
        "values": [
          "true",
          "false"
        ]
      },
      {
        "name": "protocol",
        "title": "Protocol",
        "description": "whether to open the link over http or file system",
        "category": "Display",
        "order": 9,
        "type": "SelectWdg",
        "values": [
          "http",
          "file"
        ]
      },
      {
        "name": "cascade_search",
        "title": "Cascade Search",
        "description": "determines whether to keep looking for any image to use as an icon",
        "category": "Display",
        "order": 99,
        "type": "SelectWdg",
        "values": [
          "true",
          "false"
        ]
      },
      {
        "name": "search_key",
        "title": "Search Key",
        "description": "search_key of sobject to use for displaying icon",
        "category": "Search",
        "order": 0,
        "type": "TextWdg"
      },
      {
        "name": "redirect_expr",
        "title": "Redirect Expr",
        "description": "expression to control another image related to this sobject. This is slower in performance. e.g. @SOBJECT(project/entity)",
        "category": "Search",
        "order": 1,
        "type": "TextWdg"
      }
    ]
  },
  {
    "value": "tactic.ui.widget.DiscussionElementWdg",
    "class": "tactic.ui.widget.discussion_wdg.DiscussionElementWdg",
    "aliases": [
      "tactic.ui.widget.DiscussionElementWdg",
      "tactic.ui.widget.discussion_wdg.DiscussionElementWdg",
      "DiscussionElementWdg"
    ],
    "options": [
      {
        "name": "process",
        "title": "Process",
        "description": "Explicitly set the process for notes that can be added.",
        "category": "Options",
        "order": 0,
        "type": "TextWdg"
      },
      {
        "name": "context",
        "title": "Context",
        "description": "Explicitly set the context(s) for notes that can be added. This can be a list separated by commas",
        "category": "Options",
        "order": 1,
        "type": "TextWdg"
      },
      {
        "name": "use_parent",
        "title": "Use Parent",
        "description": "Determine whether or not to enter notes for parent sObject",
        "category": "Options",
        "order": 2,
        "type": "SelectWdg",
        "values": [
          "true",
          "false"
        ]
      },
      {
        "name": "show_fullscreen_button",
        "title": "Show Fullscreen Button",
        "description": "Determine whether or not to show the expand notes icon button",
        "category": "Options",
        "order": 3,
        "type": "SelectWdg",
        "values": [
          "true",
          "false"
        ]
      },
      {
        "name": "note_format",
        "title": "Note Format",
        "description": "Determine if the notes are shown in compact or full mode. Full- shows thumbnail, login-info, email and notes. Compact- shows just the notes.",
        "category": "Options",
        "order": 4,
        "type": "SelectWdg",
        "values": [
          "compact",
          "full"
        ]
      },
      {
        "name": "show_note_status",
        "title": "Show Note Status",
        "description": "Determine whether or not to show the note status in abbreviated form.",
        "category": "Options",
        "order": 5,
        "type": "SelectWdg",
        "values": [
          "true",
          "false"
        ]
      },
      {
        "name": "show_context_notes",
        "title": "Show Context Notes",
        "description": "(DEPRECATED) Determine if the notes in the context are hidden",
        "category": "Options",
        "order": 6,
        "type": "SelectWdg",
        "values": [
          "true",
          "false"
        ]
      },
      {
        "name": "note_expandable",
        "title": "Note Expandable",
        "description": "Determine whether or not a note is expandable. True- shows a short version of the note that can be expanded. False- shows the full note",
        "category": "Options",
        "order": 7,
        "type": "SelectWdg",
        "values": [
          "true",
          "false"
        ]
      },
      {
        "name": "append_process",
        "title": "Append Process",
        "description": "Append a list of comma separated processes in addition of the ones defined in the pipeline",
        "category": "Options",
        "order": 8,
        "type": "TextWdg"
      },
      {
        "name": "allow_email",
        "title": "Allow Email",
        "description": "Allow email to be sent out directly in this widget",
        "category": "Options",
        "order": 9,
        "type": "SelectWdg",
        "values": [
          "true",
          "false"
        ]
      },
      {
        "name": "dialog_position",
        "title": "Dialog Position",
        "description": "Determine where the popup dialog will appear for the nots",
        "category": "Options",
        "order": 10,
        "type": "SelectWdg",
        "values": [
          "side",
          "center"
        ]
      },
      {
        "name": "mode",
        "title": "Mode",
        "description": "Determine if the table shows small icons or process names",
        "category": "Options",
        "order": 10,
        "type": "SelectWdg",
        "values": [
          "default",
          "icon"
        ]
      },
      {
        "name": "show_task_process",
        "title": "Show Task Process",
        "description": "Determine if Add Note widget only shows the processes of existing tasks",
        "category": "Options",
        "order": 10,
        "type": "SelectWdg",
        "values": [
          "true",
          "false"
        ]
      }
    ]
  },
  {
    "value": "tactic.ui.table.SObjectDetailElementWdg",
    "class": "tactic.ui.table.sobject_detail_wdg.SObjectDetailElementWdg",
    "aliases": [
      "tactic.ui.table.SObjectDetailElementWdg",
      "tactic.ui.table.sobject_detail_wdg.SObjectDetailElementWdg",
      "SObjectDetailElementWdg"
    ],
    "options": [
      {
        "name": "show_default_elements",
        "title": "Show Default Elements",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      },
      {
        "name": "show_task_process",
        "title": "Show Task Process",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      },
      {
        "name": "tab_element_names",
        "title": "Tab Element Names",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      },
      {
        "name": "use_parent",
        "title": "Use Parent",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      }
    ]
  },
  {
    "value": "tactic.ui.table.CheckinButtonElementWdg",
    "class": "tactic.ui.table.table_element_wdg.CheckinButtonElementWdg",
    "aliases": [
      "tactic.ui.table.CheckinButtonElementWdg",
      "tactic.ui.table.table_element_wdg.CheckinButtonElementWdg",
      "CheckinButtonElementWdg"
    ],
    "options": [
      {
        "name": "transfer_mode",
        "title": "Transfer Mode",
        "description": "Mode by which files are transferred to the server",
        "category": "1. Modes",
        "order": 1,
        "type": "SelectWdg",
        "values": [
          "upload",
          "copy",
          "move",
          "local"
        ]
      },
      {
        "name": "use_applet",
        "title": "Use Applet",
        "description": "Determines which sobject to check into",
        "category": "1. Modes",
        "order": 2,
        "type": "SelectWdg",
        "values": [
          "true",
          "false"
        ]
      },
      {
        "name": "mode",
        "title": "Mode",
        "description": "Determines whether this widget can only check-in sequences, file, or directory",
        "category": "1. Modes",
        "order": 3,
        "type": "SelectWdg",
        "values": [
          "sequence",
          "file",
          "dir",
          "multi_file",
          "add"
        ]
      },
      {
        "name": "checkin_script_path",
        "title": "Checkin Script Path",
        "description": "Path to the check-in script",
        "category": "2. Display",
        "order": 3,
        "type": "TextWdg"
      },
      {
        "name": "validate_script_path",
        "title": "Validate Script Path",
        "description": "Path to the validation script",
        "category": "2. Display",
        "order": 4,
        "type": "TextWdg"
      },
      {
        "name": "process",
        "title": "Process",
        "description": "Process under which the check-in occurs",
        "category": "2. Display",
        "order": 5,
        "type": "TextWdg"
      },
      {
        "name": "lock_process",
        "title": "Lock Process",
        "description": "If turned on, the process specified cannot be changed by the user",
        "category": "2. Display",
        "order": 6,
        "type": "CheckboxWdg"
      },
      {
        "name": "width",
        "title": "Width",
        "description": "Width of the widget",
        "category": "2. Display",
        "order": 7,
        "type": "TextWdg"
      },
      {
        "name": "show_context",
        "title": "Show Context",
        "description": "Determines whether to show the context selector",
        "category": "2. Display",
        "order": 8,
        "type": "SelectWdg",
        "values": [
          "true",
          "false"
        ]
      },
      {
        "name": "sobject_mode",
        "title": "Sobject Mode",
        "description": "Determines which sobject to check into",
        "category": "2. Display",
        "order": 8,
        "type": "SelectWdg",
        "values": [
          "parent",
          "connect",
          "sobject"
        ]
      },
      {
        "name": "checkin_options_view",
        "title": "Checkin Options View",
        "description": "Custom layout view which defines a custom check-in options UI",
        "category": "2. Display",
        "order": 9,
        "type": "TextWdg"
      }
    ]
  },
  {
    "value": "tactic.ui.table.TaskElementWdg",
    "class": "tactic.ui.table.task_element_wdg.TaskElementWdg",
    "aliases": [
      "tactic.ui.table.TaskElementWdg",
      "tactic.ui.table.task_element_wdg.TaskElementWdg",
      "TaskElementWdg",
      "pyasm.widget.task_wdg.SObjectTaskTableElement",
      "SObjectTaskTableElement",
      "pyasm.widget.SObjectTaskTableElement"
    ],
    "options": [
      {
        "name": "bg_color",
        "title": "Bg Color",
        "description": "Different modes of displaying the background color for each process",
        "category": "Color",
        "order": 2,
        "type": "SelectWdg",
        "values": [
          "status",
          "process"
        ]
      },
      {
        "name": "status_color",
        "title": "Status Color",
        "description": "Different modes of displaying status background color",
        "category": "Color",
        "order": 3,
        "type": "SelectWdg",
        "values": [
          "status",
          "process"
        ]
      },
      {
        "name": "context_color",
        "title": "Context Color",
        "description": "Different modes of displaying context background color",
        "category": "Color",
        "order": 4,
        "type": "SelectWdg",
        "values": [
          "status",
          "process"
        ]
      },
      {
        "name": "panel_width",
        "title": "Panel Width",
        "description": "Select the overall width for the panel layout",
        "category": "Display",
        "order": 6,
        "type": "SelectWdg",
        "values": [
          "35px",
          "50px",
          "75px",
          "100px",
          "125px"
        ]
      },
      {
        "name": "font_size",
        "title": "Font Size",
        "description": "font size of the text",
        "category": "Display",
        "order": 7,
        "type": "SelectWdg",
        "values": [
          "7",
          "8",
          "9",
          "10",
          "11",
          "12",
          "13",
          "14"
        ]
      },
      {
        "name": "show_process",
        "title": "Show Process",
        "description": "Flag for displaying the process of the tasks",
        "category": "Display",
        "order": 8,
        "type": "SelectWdg",
        "values": [
          "true",
          "false"
        ]
      },
      {
        "name": "show_context",
        "title": "Show Context",
        "description": "Flag for displaying the context of the tasks",
        "category": "Display",
        "order": 9,
        "type": "SelectWdg",
        "values": [
          "true",
          "false"
        ]
      },
      {
        "name": "show_assigned",
        "title": "Show Assigned",
        "description": "Flag for displaying the assigned user of the tasks",
        "category": "Display",
        "order": 10,
        "type": "SelectWdg",
        "values": [
          "true",
          "false"
        ]
      },
      {
        "name": "show_bid",
        "title": "Show Bid",
        "description": "Flag for displaying the bid duration tasks",
        "category": "Display",
        "order": 10,
        "type": "SelectWdg",
        "values": [
          "true",
          "false"
        ]
      },
      {
        "name": "show_status",
        "title": "Show Status",
        "description": "Flag for displaying the status of the tasks",
        "category": "Display",
        "order": 10,
        "type": "SelectWdg",
        "values": [
          "true",
          "false"
        ]
      },
      {
        "name": "assigned_label_attr",
        "title": "Assigned Label Attr",
        "description": "A list of | separated attributes displayed as the label of the assigned, e.g. \"first_name|last_name\"",
        "category": "Display",
        "order": 11,
        "type": "TextWdg"
      },
      {
        "name": "assigned_values_expr",
        "title": "Assigned Values Expr",
        "description": "An expression controlling what login values to show, e.g. @SOBJECT(sthpw/login['department','design'])",
        "category": "Display",
        "order": 12,
        "type": "TextWdg"
      },
      {
        "name": "show_dates",
        "title": "Show Dates",
        "description": "Flag for displaying the date range of the tasks",
        "category": "Display",
        "order": 13,
        "type": "SelectWdg",
        "values": [
          "true",
          "false"
        ]
      },
      {
        "name": "show_track",
        "title": "Show Track",
        "description": "Flag for displaying a tip to dynamically load the information of the last status",
        "category": "Display",
        "order": 14,
        "type": "SelectWdg",
        "values": [
          "true",
          "false"
        ]
      },
      {
        "name": "show_labels",
        "title": "Show Labels",
        "description": "Flag for displaying the label of the tasks",
        "category": "Display",
        "order": 15,
        "type": "SelectWdg",
        "values": [
          "true",
          "false"
        ]
      },
      {
        "name": "show_border",
        "title": "Show Border",
        "description": "Flag for displaying a border around each task panel",
        "category": "Display",
        "order": 16,
        "type": "SelectWdg",
        "values": [
          "all",
          "one-sided",
          "none"
        ]
      },
      {
        "name": "collate_columns",
        "title": "Collate Columns",
        "description": "Flag to collate columns that have the same processes together .",
        "category": "Display",
        "order": 18,
        "type": "SelectWdg",
        "values": [
          "true",
          "false"
        ]
      },
      {
        "name": "show_current_pipeline_only",
        "title": "Show Current Pipeline Only",
        "description": "Flag for displaying only the tasks associate with the current pipeline. Default to true.",
        "category": "Display",
        "order": 18,
        "type": "SelectWdg",
        "values": [
          "true",
          "false"
        ]
      },
      {
        "name": "show_add_task",
        "title": "Show Add Task",
        "description": "Flag for displaying the add task button even if there are existing tasks. Defaults to false",
        "category": "Display",
        "order": 19,
        "type": "SelectWdg",
        "values": [
          "true",
          "false"
        ]
      },
      {
        "name": "show_link_task_menu",
        "title": "Show Link Task Menu",
        "description": "Flag for displaying the task linking menu so one can virtually make a task shared by two or more people. Defaults to false",
        "category": "Display",
        "order": 20,
        "type": "SelectWdg",
        "values": [
          "true",
          "false"
        ]
      },
      {
        "name": "show_processes_in_title",
        "title": "Show Processes In Title",
        "description": "Display the processes in title. You are advised to turn on show_filler_tasks as well. Defaults to false",
        "category": "Display",
        "order": 21,
        "type": "SelectWdg",
        "values": [
          "true",
          "false"
        ]
      },
      {
        "name": "show_task_edit",
        "title": "Show Task Edit",
        "description": "Flag for displaying the edit icon for each task",
        "category": "Display",
        "order": 22,
        "type": "SelectWdg",
        "values": [
          "true",
          "false"
        ]
      },
      {
        "name": "task_edit_view",
        "title": "Task Edit View",
        "description": "A custom view specified for editing the task in this widget. Defaults to edit",
        "category": "Display",
        "order": 23,
        "type": "TextWdg",
        "default": "edit"
      },
      {
        "name": "task_filter",
        "title": "Task Filter",
        "description": "A filter on which type of tasks to display",
        "category": "Display",
        "order": 24,
        "type": "SelectWdg",
        "values": [
          "process_only",
          "context_only"
        ]
      },
      {
        "name": "layout",
        "title": "Layout",
        "description": "Determines layout for each process",
        "category": "Mode",
        "order": 1,
        "type": "SelectWdg",
        "values": [
          "panel",
          "vertical",
          "horizontal"
        ]
      },
      {
        "name": "show_filler_tasks",
        "title": "Show Filler Tasks",
        "description": "Flag to determine filler tasks are shown dynamically",
        "category": "Mode",
        "order": 2,
        "type": "SelectWdg",
        "values": [
          "true",
          "false"
        ]
      },
      {
        "name": "edit_status",
        "title": "Edit Status",
        "description": "Flag to determine whether the status is editable",
        "category": "Mode",
        "order": 3,
        "type": "SelectWdg",
        "values": [
          "true",
          "false"
        ]
      },
      {
        "name": "edit_assigned",
        "title": "Edit Assigned",
        "description": "Flag for editing the assigned user of the tasks",
        "category": "Mode",
        "order": 4,
        "type": "SelectWdg",
        "values": [
          "true",
          "false"
        ]
      }
    ]
  },
  {
    "value": "tactic.ui.table.TaskCompletionWdg",
    "class": "tactic.ui.table.statistic_wdg.TaskCompletionWdg",
    "aliases": [
      "tactic.ui.table.TaskCompletionWdg",
      "tactic.ui.table.statistic_wdg.TaskCompletionWdg",
      "TaskCompletionWdg",
      "tactic.ui.table.MilestoneCompletionWdg",
      "tactic.ui.table.statistic_wdg.MilestoneCompletionWdg",
      "tactic.ui.table.TaskGroupCompletionWdg",
      "tactic.ui.table.statistic_wdg.TaskGroupCompletionWdg",
      "pyasm.widget.statistic_wdg.TaskCompletionWdg",
      "pyasm.widget.TaskCompletionWdg"
    ],
    "options": [
      {
        "name": "task_expr",
        "title": "Task Expr",
        "description": "an expression that retrieves the tasks e.g. @SOBJECT(sthpw/task['context','anim'])",
        "category": "Display",
        "order": 0,
        "type": "TextAreaWdg"
      }
    ]
  },
  {
    "value": "tactic.ui.table.ExploreElementWdg",
    "class": "tactic.ui.table.explorer_wdg.ExplorerElementWdg",
    "aliases": [
      "tactic.ui.table.ExploreElementWdg",
      "tactic.ui.table.explorer_wdg.ExplorerElementWdg",
      "ExplorerElementWdg",
      "tactic.ui.table.ExplorerElementWdg",
      "tactic.ui.table.explorer_wdg.ExplorerTableElementWdg",
      "tactic.ui.table.ExplorerTableElementWdg"
    ],
    "options": [
      {
        "name": "mode",
        "title": "Mode",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg",
        "values": [
          "sandbox",
          "repository"
        ]
      }
    ]
  },
  {
    "value": "tactic.ui.table.SObjectFilesElementWdg",
    "class": "tactic.ui.table.sobject_summary_wdg.SObjectFilesElementWdg",
    "aliases": [
      "tactic.ui.table.SObjectFilesElementWdg",
      "tactic.ui.table.sobject_summary_wdg.SObjectFilesElementWdg",
      "SObjectFilesElementWdg"
    ],
    "options": [
      {
        "name": "expression",
        "title": "Expression",
        "description": "Optional snapshot or file expression filter",
        "category": "Display",
        "order": 1,
        "type": "TextAreaWdg"
      }
    ]
  },
  {
    "value": "tactic.ui.table.MetadataElementWdg",
    "class": "tactic.ui.table.metadata_element_wdg.MetadataElementWdg",
    "aliases": [
      "tactic.ui.table.MetadataElementWdg",
      "tactic.ui.table.metadata_element_wdg.MetadataElementWdg",
      "MetadataElementWdg"
    ],
    "options": [
      {
        "name": "context",
        "title": "Context",
        "description": "The context of the snapshot to get the file path from",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      }
    ]
  },
  {
    "value": "tactic.ui.table.JsonElementWdg",
    "class": "tactic.ui.table.json_element_wdg.JsonElementWdg",
    "aliases": [
      "tactic.ui.table.JsonElementWdg",
      "tactic.ui.table.json_element_wdg.JsonElementWdg",
      "JsonElementWdg"
    ],
    "options": [
      {
        "name": "height",
        "title": "Height",
        "description": "Maximum cell height",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      }
    ]
  },
  {
    "value": "tactic.ui.table.TaskSummaryElementWdg",
    "class": "tactic.ui.table.task_element_wdg.TaskSummaryElementWdg",
    "aliases": [
      "tactic.ui.table.TaskSummaryElementWdg",
      "tactic.ui.table.task_element_wdg.TaskSummaryElementWdg",
      "TaskSummaryElementWdg"
    ],
    "options": [
      {
        "name": "bg_color",
        "title": "Bg Color",
        "description": "Different modes of displaying the background color for each process",
        "category": "Color",
        "order": 2,
        "type": "SelectWdg",
        "values": [
          "status",
          "process"
        ]
      },
      {
        "name": "status_color",
        "title": "Status Color",
        "description": "Different modes of displaying status background color",
        "category": "Color",
        "order": 3,
        "type": "SelectWdg",
        "values": [
          "status",
          "process"
        ]
      },
      {
        "name": "context_color",
        "title": "Context Color",
        "description": "Different modes of displaying context background color",
        "category": "Color",
        "order": 4,
        "type": "SelectWdg",
        "values": [
          "status",
          "process"
        ]
      },
      {
        "name": "panel_width",
        "title": "Panel Width",
        "description": "Select the overall width for the panel layout",
        "category": "Display",
        "order": 6,
        "type": "SelectWdg",
        "values": [
          "35px",
          "50px",
          "75px",
          "100px",
          "125px"
        ]
      },
      {
        "name": "font_size",
        "title": "Font Size",
        "description": "font size of the text",
        "category": "Display",
        "order": 7,
        "type": "SelectWdg",
        "values": [
          "7",
          "8",
          "9",
          "10",
          "11",
          "12",
          "13",
          "14"
        ]
      },
      {
        "name": "show_process",
        "title": "Show Process",
        "description": "Flag for displaying the process of the tasks",
        "category": "Display",
        "order": 8,
        "type": "SelectWdg",
        "values": [
          "true",
          "false"
        ]
      },
      {
        "name": "show_context",
        "title": "Show Context",
        "description": "Flag for displaying the context of the tasks",
        "category": "Display",
        "order": 9,
        "type": "SelectWdg",
        "values": [
          "true",
          "false"
        ]
      },
      {
        "name": "show_assigned",
        "title": "Show Assigned",
        "description": "Flag for displaying the assigned user of the tasks",
        "category": "Display",
        "order": 10,
        "type": "SelectWdg",
        "values": [
          "true",
          "false"
        ]
      },
      {
        "name": "show_bid",
        "title": "Show Bid",
        "description": "Flag for displaying the bid duration tasks",
        "category": "Display",
        "order": 10,
        "type": "SelectWdg",
        "values": [
          "true",
          "false"
        ]
      },
      {
        "name": "show_status",
        "title": "Show Status",
        "description": "Flag for displaying the status of the tasks",
        "category": "Display",
        "order": 10,
        "type": "SelectWdg",
        "values": [
          "true",
          "false"
        ]
      },
      {
        "name": "assigned_label_attr",
        "title": "Assigned Label Attr",
        "description": "A list of | separated attributes displayed as the label of the assigned, e.g. \"first_name|last_name\"",
        "category": "Display",
        "order": 11,
        "type": "TextWdg"
      },
      {
        "name": "assigned_values_expr",
        "title": "Assigned Values Expr",
        "description": "An expression controlling what login values to show, e.g. @SOBJECT(sthpw/login['department','design'])",
        "category": "Display",
        "order": 12,
        "type": "TextWdg"
      },
      {
        "name": "show_dates",
        "title": "Show Dates",
        "description": "Flag for displaying the date range of the tasks",
        "category": "Display",
        "order": 13,
        "type": "SelectWdg",
        "values": [
          "true",
          "false"
        ]
      },
      {
        "name": "show_track",
        "title": "Show Track",
        "description": "Flag for displaying a tip to dynamically load the information of the last status",
        "category": "Display",
        "order": 14,
        "type": "SelectWdg",
        "values": [
          "true",
          "false"
        ]
      },
      {
        "name": "show_labels",
        "title": "Show Labels",
        "description": "Flag for displaying the label of the tasks",
        "category": "Display",
        "order": 15,
        "type": "SelectWdg",
        "values": [
          "true",
          "false"
        ]
      },
      {
        "name": "show_border",
        "title": "Show Border",
        "description": "Flag for displaying a border around each task panel",
        "category": "Display",
        "order": 16,
        "type": "SelectWdg",
        "values": [
          "all",
          "one-sided",
          "none"
        ]
      },
      {
        "name": "collate_columns",
        "title": "Collate Columns",
        "description": "Flag to collate columns that have the same processes together .",
        "category": "Display",
        "order": 18,
        "type": "SelectWdg",
        "values": [
          "true",
          "false"
        ]
      },
      {
        "name": "show_current_pipeline_only",
        "title": "Show Current Pipeline Only",
        "description": "Flag for displaying only the tasks associate with the current pipeline. Default to true.",
        "category": "Display",
        "order": 18,
        "type": "SelectWdg",
        "values": [
          "true",
          "false"
        ]
      },
      {
        "name": "show_add_task",
        "title": "Show Add Task",
        "description": "Flag for displaying the add task button even if there are existing tasks. Defaults to false",
        "category": "Display",
        "order": 19,
        "type": "SelectWdg",
        "values": [
          "true",
          "false"
        ]
      },
      {
        "name": "show_link_task_menu",
        "title": "Show Link Task Menu",
        "description": "Flag for displaying the task linking menu so one can virtually make a task shared by two or more people. Defaults to false",
        "category": "Display",
        "order": 20,
        "type": "SelectWdg",
        "values": [
          "true",
          "false"
        ]
      },
      {
        "name": "show_processes_in_title",
        "title": "Show Processes In Title",
        "description": "Display the processes in title. You are advised to turn on show_filler_tasks as well. Defaults to false",
        "category": "Display",
        "order": 21,
        "type": "SelectWdg",
        "values": [
          "true",
          "false"
        ]
      },
      {
        "name": "show_task_edit",
        "title": "Show Task Edit",
        "description": "Flag for displaying the edit icon for each task",
        "category": "Display",
        "order": 22,
        "type": "SelectWdg",
        "values": [
          "true",
          "false"
        ]
      },
      {
        "name": "task_edit_view",
        "title": "Task Edit View",
        "description": "A custom view specified for editing the task in this widget. Defaults to edit",
        "category": "Display",
        "order": 23,
        "type": "TextWdg",
        "default": "edit"
      },
      {
        "name": "task_filter",
        "title": "Task Filter",
        "description": "A filter on which type of tasks to display",
        "category": "Display",
        "order": 24,
        "type": "SelectWdg",
        "values": [
          "process_only",
          "context_only"
        ]
      },
      {
        "name": "layout",
        "title": "Layout",
        "description": "Determines layout for each process",
        "category": "Mode",
        "order": 1,
        "type": "SelectWdg",
        "values": [
          "panel",
          "vertical",
          "horizontal"
        ]
      },
      {
        "name": "show_filler_tasks",
        "title": "Show Filler Tasks",
        "description": "Flag to determine filler tasks are shown dynamically",
        "category": "Mode",
        "order": 2,
        "type": "SelectWdg",
        "values": [
          "true",
          "false"
        ]
      },
      {
        "name": "edit_status",
        "title": "Edit Status",
        "description": "Flag to determine whether the status is editable",
        "category": "Mode",
        "order": 3,
        "type": "SelectWdg",
        "values": [
          "true",
          "false"
        ]
      },
      {
        "name": "edit_assigned",
        "title": "Edit Assigned",
        "description": "Flag for editing the assigned user of the tasks",
        "category": "Mode",
        "order": 4,
        "type": "SelectWdg",
        "values": [
          "true",
          "false"
        ]
      },
      {
        "name": "mode",
        "title": "Mode",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      }
    ]
  },
  {
    "value": "tactic.ui.table.ButtonElementWdg",
    "class": "tactic.ui.table.button_wdg.ButtonElementWdg",
    "aliases": [
      "tactic.ui.table.ButtonElementWdg",
      "tactic.ui.table.button_wdg.ButtonElementWdg",
      "ButtonElementWdg"
    ],
    "options": [
      {
        "name": "align",
        "title": "Align",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      },
      {
        "name": "cbjs_action",
        "title": "Cbjs Action",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextAreaWdg"
      },
      {
        "name": "color",
        "title": "Color",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      },
      {
        "name": "enable",
        "title": "Enable",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      },
      {
        "name": "expression",
        "title": "Expression",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextAreaWdg"
      },
      {
        "name": "hint",
        "title": "Hint",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      },
      {
        "name": "icon",
        "title": "Icon",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "IconSelectWdg"
      },
      {
        "name": "icon_tip",
        "title": "Icon Tip",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      },
      {
        "name": "javascript",
        "title": "Javascript",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      },
      {
        "name": "path",
        "title": "Path",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      },
      {
        "name": "script",
        "title": "Script",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      },
      {
        "name": "script_code",
        "title": "Script Code",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      },
      {
        "name": "script_path",
        "title": "Script Path",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      },
      {
        "name": "size",
        "title": "Size",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      }
    ]
  },
  {
    "value": "ParallelStatusWdg",
    "class": "pyasm.widget.parallel_status.ParallelStatusWdg",
    "aliases": [
      "ParallelStatusWdg",
      "pyasm.widget.parallel_status.ParallelStatusWdg",
      "pyasm.widget.ParallelStatusWdg"
    ],
    "options": [
      {
        "name": "bar_height",
        "title": "Bar Height",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      },
      {
        "name": "label_format",
        "title": "Label Format",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      },
      {
        "name": "report",
        "title": "Report",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      }
    ]
  },
  {
    "value": "tactic.ui.widget.TaskStatusElementWdg",
    "class": "tactic.ui.widget.misc_input_wdg.TaskStatusElementWdg",
    "aliases": [
      "tactic.ui.widget.TaskStatusElementWdg",
      "tactic.ui.widget.misc_input_wdg.TaskStatusElementWdg",
      "TaskStatusElementWdg"
    ],
    "options": [
      {
        "name": "edit_scope",
        "title": "Edit Scope",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      }
    ]
  },
  {
    "value": "tactic.ui.table.WorkElementWdg",
    "class": "tactic.ui.table.task_element_wdg.WorkElementWdg",
    "aliases": [
      "tactic.ui.table.WorkElementWdg",
      "tactic.ui.table.task_element_wdg.WorkElementWdg",
      "WorkElementWdg"
    ],
    "options": [
      {
        "name": "icon",
        "title": "Icon",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "IconSelectWdg"
      },
      {
        "name": "mode",
        "title": "Mode",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      },
      {
        "name": "transfer_mode",
        "title": "Transfer Mode",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      }
    ]
  },
  {
    "value": "tactic.ui.table.DropElementWdg",
    "class": "tactic.ui.table.drop_element_wdg.DropElementWdg",
    "aliases": [
      "tactic.ui.table.DropElementWdg",
      "tactic.ui.table.drop_element_wdg.DropElementWdg",
      "DropElementWdg"
    ],
    "options": [
      {
        "name": "accepted_drop_type",
        "title": "Accepted Drop Type",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      },
      {
        "name": "cbjs_drop_action",
        "title": "Cbjs Drop Action",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      },
      {
        "name": "checkin_mode",
        "title": "Checkin Mode",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      },
      {
        "name": "context",
        "title": "Context",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      },
      {
        "name": "css_background-color",
        "title": "Css Background Color",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      },
      {
        "name": "display_expr",
        "title": "Display Expr",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      },
      {
        "name": "instance_type",
        "title": "Instance Type",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      },
      {
        "name": "path",
        "title": "Path",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      },
      {
        "name": "subcontext",
        "title": "Subcontext",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      },
      {
        "name": "subcontext_mode",
        "title": "Subcontext Mode",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      },
      {
        "name": "transfer_mode",
        "title": "Transfer Mode",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      }
    ]
  },
  {
    "value": "tactic.ui.table.CustomLayoutElementWdg",
    "class": "tactic.ui.table.custom_layout_element_wdg.CustomLayoutElementWdg",
    "aliases": [
      "tactic.ui.table.CustomLayoutElementWdg",
      "tactic.ui.table.custom_layout_element_wdg.CustomLayoutElementWdg",
      "CustomLayoutElementWdg"
    ],
    "options": [
      {
        "name": "html",
        "title": "Html",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextAreaWdg"
      },
      {
        "name": "icon_size",
        "title": "Icon Size",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      },
      {
        "name": "include_mako",
        "title": "Include Mako",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      },
      {
        "name": "search_key",
        "title": "Search Key",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      },
      {
        "name": "show_resize_scroll",
        "title": "Show Resize Scroll",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      },
      {
        "name": "view",
        "title": "View",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      }
    ]
  },
  {
    "value": "tactic.ui.table.hidden_row_element_wdg.HiddenRowElementWdg",
    "class": "tactic.ui.table.hidden_row_element_wdg.HiddenRowElementWdg",
    "aliases": [
      "tactic.ui.table.hidden_row_element_wdg.HiddenRowElementWdg",
      "HiddenRowElementWdg",
      "tactic.ui.table.HiddenRowElementWdg",
      "tactic.ui.table.hidden_row_element_wdg.RowAddElementWdg",
      "tactic.ui.table.RowAddElementWdg"
    ],
    "options": [
      {
        "name": "dynamic",
        "title": "Dynamic",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      },
      {
        "name": "dynamic_class",
        "title": "Dynamic Class",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      },
      {
        "name": "edit_view",
        "title": "Edit View",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      },
      {
        "name": "expression",
        "title": "Expression",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextAreaWdg"
      },
      {
        "name": "html",
        "title": "Html",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextAreaWdg"
      },
      {
        "name": "icon",
        "title": "Icon",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "IconSelectWdg"
      },
      {
        "name": "icon_tip",
        "title": "Icon Tip",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      },
      {
        "name": "include_mako",
        "title": "Include Mako",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      },
      {
        "name": "init_load_num",
        "title": "Init Load Num",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      },
      {
        "name": "insert_view",
        "title": "Insert View",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      },
      {
        "name": "label",
        "title": "Label",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      },
      {
        "name": "mode",
        "title": "Mode",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      },
      {
        "name": "related_types",
        "title": "Related Types",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      },
      {
        "name": "search_type",
        "title": "Search Type",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      },
      {
        "name": "search_view",
        "title": "Search View",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      },
      {
        "name": "show_gear",
        "title": "Show Gear",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      },
      {
        "name": "show_insert",
        "title": "Show Insert",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      },
      {
        "name": "show_resize_scroll",
        "title": "Show Resize Scroll",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      },
      {
        "name": "show_row_select",
        "title": "Show Row Select",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      },
      {
        "name": "show_search",
        "title": "Show Search",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      },
      {
        "name": "show_search_limit",
        "title": "Show Search Limit",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      },
      {
        "name": "show_select",
        "title": "Show Select",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      },
      {
        "name": "show_shelf",
        "title": "Show Shelf",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      },
      {
        "name": "title_icon",
        "title": "Title Icon",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      },
      {
        "name": "view",
        "title": "View",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      },
      {
        "name": "width",
        "title": "Width",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      }
    ]
  },
  {
    "value": "GanttWdg",
    "class": "pyasm.widget.gantt_wdg.GanttWdg",
    "aliases": [
      "GanttWdg",
      "pyasm.widget.gantt_wdg.GanttWdg",
      "pyasm.widget.GanttWdg"
    ],
    "options": [
      {
        "name": "actual_edit",
        "title": "Actual Edit",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      },
      {
        "name": "bid_edit",
        "title": "Bid Edit",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      },
      {
        "name": "cal_margin",
        "title": "Cal Margin",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      },
      {
        "name": "handlers",
        "title": "Handlers",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      },
      {
        "name": "width",
        "title": "Width",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      }
    ]
  },
  {
    "value": "tactic.ui.table.gantt_element_wdg.GanttElementWdg",
    "class": "tactic.ui.table.gantt_element_wdg.GanttElementWdg",
    "aliases": [
      "tactic.ui.table.gantt_element_wdg.GanttElementWdg",
      "GanttElementWdg",
      "tactic.ui.table.GanttElementWdg"
    ],
    "options": [
      {
        "name": "bar_height",
        "title": "Bar Height",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      },
      {
        "name": "color_mode",
        "title": "Color Mode",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      },
      {
        "name": "date_mode",
        "title": "Date Mode",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      },
      {
        "name": "options",
        "title": "Options",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      },
      {
        "name": "overlap",
        "title": "Overlap",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      },
      {
        "name": "range_end_date",
        "title": "Range End Date",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      },
      {
        "name": "range_start_date",
        "title": "Range Start Date",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      },
      {
        "name": "show_title",
        "title": "Show Title",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      },
      {
        "name": "week_display",
        "title": "Week Display",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      },
      {
        "name": "week_start",
        "title": "Week Start",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      },
      {
        "name": "width",
        "title": "Width",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      },
      {
        "name": "year_display",
        "title": "Year Display",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      }
    ]
  },
  {
    "value": "WeekTableElement",
    "class": "pyasm.widget.timecard_wdg.WeekTableElement",
    "aliases": [
      "WeekTableElement",
      "pyasm.widget.timecard_wdg.WeekTableElement",
      "pyasm.widget.WeekTableElement"
    ],
    "options": [
      {
        "name": "width",
        "title": "Width",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      }
    ]
  },
  {
    "value": "tactic.ui.table.work_hours_element_wdg.WorkHoursElementWdg",
    "class": "tactic.ui.table.work_hours_element_wdg.WorkHoursElementWdg",
    "aliases": [
      "tactic.ui.table.work_hours_element_wdg.WorkHoursElementWdg",
      "WorkHoursElementWdg",
      "tactic.ui.table.WorkHoursElementWdg"
    ],
    "options": [
      {
        "name": "day_width",
        "title": "Day Width",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      },
      {
        "name": "days_per_page",
        "title": "Days Per Page",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      },
      {
        "name": "show_all_users",
        "title": "Show All Users",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      },
      {
        "name": "show_overtime",
        "title": "Show Overtime",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      },
      {
        "name": "start_date",
        "title": "Start Date",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      },
      {
        "name": "unit",
        "title": "Unit",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      },
      {
        "name": "use_straight_time",
        "title": "Use Straight Time",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      },
      {
        "name": "width",
        "title": "Width",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      }
    ]
  },
  {
    "value": "tactic.ui.table.CheckoutButtonElementWdg",
    "class": "tactic.ui.table.table_element_wdg.CheckoutButtonElementWdg",
    "aliases": [
      "tactic.ui.table.CheckoutButtonElementWdg",
      "tactic.ui.table.table_element_wdg.CheckoutButtonElementWdg",
      "CheckoutButtonElementWdg"
    ],
    "options": [
      {
        "name": "transfer_mode",
        "title": "Transfer Mode",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      }
    ]
  },
  {
    "value": "pyasm.widget.SObjectConnectionElement",
    "class": "pyasm.widget.sobject_browser_wdg.SObjectConnectionElement",
    "aliases": [
      "pyasm.widget.SObjectConnectionElement",
      "pyasm.widget.sobject_browser_wdg.SObjectConnectionElement",
      "SObjectConnectionElement"
    ],
    "options": [
      {
        "name": "direction",
        "title": "Direction",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      },
      {
        "name": "icon_size",
        "title": "Icon Size",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      }
    ]
  },
  {
    "value": "tactic.ui.table.ParentGroupTableElementWdg",
    "class": "tactic.ui.table.group_element_wdg.ParentGroupTableElementWdg",
    "aliases": [
      "tactic.ui.table.ParentGroupTableElementWdg",
      "tactic.ui.table.group_element_wdg.ParentGroupTableElementWdg",
      "ParentGroupTableElementWdg"
    ],
    "options": [
      {
        "name": "disable",
        "title": "Disable",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      },
      {
        "name": "label",
        "title": "Label",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      }
    ]
  },
  {
    "value": "PublishTableElement",
    "class": "pyasm.widget.table_element_wdg.PublishTableElement",
    "aliases": [
      "PublishTableElement",
      "pyasm.widget.table_element_wdg.PublishTableElement",
      "pyasm.widget.PublishTableElement"
    ],
    "options": [
      {
        "name": "multi_publish",
        "title": "Multi Publish",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      }
    ]
  },
  {
    "value": "tactic.ui.table.GeneralPublishElementWdg",
    "class": "tactic.ui.table.table_element_wdg.GeneralPublishElementWdg",
    "aliases": [
      "tactic.ui.table.GeneralPublishElementWdg",
      "tactic.ui.table.table_element_wdg.GeneralPublishElementWdg",
      "GeneralPublishElementWdg"
    ],
    "options": [
      {
        "name": "preview",
        "title": "Preview",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      },
      {
        "name": "view",
        "title": "View",
        "description": "",
        "category": "Other Options",
        "order": 99,
        "type": "TextWdg"
      }
    ]
  }
];

export const EDIT_WIDGET_ARGS = [
  {
    "value": "text",
    "label": "Text",
    "class": "pyasm.widget.input_wdg.TextWdg",
    "aliases": [
      "TextWdg",
      "TextInputWdg",
      "pyasm.widget.TextWdg",
      "pyasm.widget.input_wdg.TextWdg",
      "tactic.ui.input.TextInputWdg",
      "tactic.ui.input.text_input_wdg.TextInputWdg"
    ],
    "options": [
      {
        "name": "size",
        "title": "Size",
        "description": "Width of the text field in pixels",
        "category": "Options",
        "order": 0,
        "type": "TextWdg"
      },
      {
        "name": "width",
        "title": "Width",
        "description": "Width of the text element",
        "category": "Options",
        "order": 1,
        "type": "TextWdg"
      },
      {
        "name": "read_only",
        "title": "Read Only",
        "description": "Whether to set this text field to read-only",
        "category": "Options",
        "order": 2,
        "type": "SelectWdg",
        "values": [
          "true",
          "false"
        ]
      },
      {
        "name": "required",
        "title": "Required",
        "description": "Designate this field to be filled in",
        "category": "Options",
        "order": 3,
        "type": "SelectWdg",
        "values": [
          "true",
          "false"
        ]
      },
      {
        "name": "default",
        "title": "Default",
        "description": "Default value in an edit form",
        "category": "Options",
        "order": 4,
        "type": "TextWdg"
      },
      {
        "name": "hint_text",
        "title": "Hint Text",
        "description": "Initial hint text",
        "category": "Options",
        "order": 5,
        "type": "TextWdg"
      },
      {
        "name": "display_format",
        "title": "Display Format",
        "description": "Format key to display the data",
        "category": "Options",
        "order": 6,
        "type": "TextWdg"
      },
      {
        "name": "validation_scheme",
        "title": "Validation Scheme",
        "description": "Built-in validation scheme (INTEGER, NUMERIC, POS_INTEGER)",
        "category": "Options",
        "order": 7,
        "type": "SelectWdg",
        "values": [
          "INTEGER",
          "NUMERIC",
          "POS_INTEGER"
        ]
      }
    ]
  },
  {
    "value": "textarea",
    "label": "Multi-line text",
    "class": "pyasm.widget.input_wdg.TextAreaWdg",
    "aliases": [
      "TextAreaWdg",
      "pyasm.widget.TextAreaWdg",
      "pyasm.widget.input_wdg.TextAreaWdg"
    ],
    "options": [
      {
        "name": "rows",
        "title": "Rows",
        "description": "The number of rows to show",
        "category": "Options",
        "order": 1,
        "type": "TextWdg"
      },
      {
        "name": "cols",
        "title": "Cols",
        "description": "The number of columns to show",
        "category": "Options",
        "order": 2,
        "type": "TextWdg"
      },
      {
        "name": "required",
        "title": "Required",
        "description": "Designate this field to be filled in",
        "category": "Options",
        "order": 3,
        "type": "SelectWdg",
        "values": [
          "true",
          "false"
        ]
      },
      {
        "name": "read_only",
        "title": "Read Only",
        "description": "Whether to set this field to read-only",
        "category": "Options",
        "order": 4,
        "type": "SelectWdg",
        "values": [
          "true",
          "false"
        ]
      }
    ]
  },
  {
    "value": "select",
    "label": "Select",
    "class": "pyasm.widget.input_wdg.SelectWdg",
    "aliases": [
      "SelectWdg",
      "pyasm.widget.SelectWdg",
      "pyasm.widget.input_wdg.SelectWdg"
    ],
    "options": [
      {
        "name": "labels_expr",
        "title": "Labels Expr",
        "description": "A list of labels retrieved through an expression, e.g. @GET(prod/shot.name)",
        "category": "Misc",
        "order": 1,
        "type": "TextAreaWdg"
      },
      {
        "name": "values_expr",
        "title": "Values Expr",
        "description": "A list of values retrieved through an expression, e.g. @GET(prod/shot.code)",
        "category": "Misc",
        "order": 2,
        "type": "TextAreaWdg"
      },
      {
        "name": "mode_expr",
        "title": "Mode Expr",
        "description": "Specify if it uses the current sObject as a starting point",
        "category": "Misc",
        "order": 3,
        "type": "SelectWdg",
        "values": [
          "relative"
        ]
      },
      {
        "name": "query",
        "title": "Query",
        "description": "Query shorthand in the form of <search_type>|<value_column>|<label_column>",
        "category": "Misc",
        "order": 4,
        "type": "TextWdg"
      },
      {
        "name": "values",
        "title": "Values",
        "description": "A list of values separated by | that determine the actual values of the selection",
        "category": "Options",
        "order": 1,
        "type": "TextWdg"
      },
      {
        "name": "labels",
        "title": "Labels",
        "description": "A list of values separated by | that determine the label of the selection",
        "category": "Options",
        "order": 2,
        "type": "TextWdg"
      },
      {
        "name": "empty",
        "title": "Empty",
        "description": "Include an empty selection option",
        "category": "Options",
        "order": 3,
        "type": "SelectWdg",
        "values": [
          "true",
          "false"
        ]
      },
      {
        "name": "default",
        "title": "Default",
        "description": "The default selection value in an edit form",
        "category": "Options",
        "order": 4,
        "type": "TextWdg"
      },
      {
        "name": "required",
        "title": "Required",
        "description": "Designate this field to have some value",
        "category": "Options",
        "order": 5,
        "type": "SelectWdg",
        "values": [
          "true",
          "false"
        ]
      },
      {
        "name": "read_only",
        "title": "Read Only",
        "description": "Whether to set this field to read-only",
        "category": "Options",
        "order": 6,
        "type": "SelectWdg",
        "values": [
          "true",
          "false"
        ]
      }
    ]
  },
  {
    "value": "calendar",
    "label": "Calendar",
    "class": "tactic.ui.widget.calendar_wdg.CalendarInputWdg",
    "aliases": [
      "CalendarInputWdg",
      "calendar_time",
      "time",
      "tactic.ui.widget.CalendarInputWdg",
      "tactic.ui.widget.calendar_wdg.CalendarInputWdg"
    ],
    "options": [
      {
        "name": "first_day_of_week",
        "title": "First Day Of Week",
        "description": "Integer representing first day of the week (6=Sunday, 0=Monday)",
        "category": "Display",
        "order": 0,
        "type": "SelectWdg",
        "values": [
          "6",
          "0"
        ],
        "labels": [
          "Sunday",
          "Monday"
        ]
      },
      {
        "name": "show_time",
        "title": "Show Time",
        "description": "Determines whether or not a time value is entered",
        "category": "Display",
        "order": 1,
        "type": "SelectWdg",
        "values": [
          "true",
          "false"
        ]
      },
      {
        "name": "show_calendar",
        "title": "Show Calendar",
        "description": "Determines whether or not the calendar is shown",
        "category": "Display",
        "order": 2,
        "type": "SelectWdg",
        "values": [
          "true",
          "false"
        ]
      },
      {
        "name": "read_only",
        "title": "Read Only",
        "description": "Sets the widget to be read only",
        "category": "Display",
        "order": 3,
        "type": "SelectWdg",
        "values": [
          "true",
          "false"
        ]
      },
      {
        "name": "default",
        "title": "Default",
        "description": "The default selection value in an edit form",
        "category": "Display",
        "order": 4,
        "type": "TextWdg"
      },
      {
        "name": "time_input_default",
        "title": "Time Input Default",
        "description": "The default for time, e.g. 5:00 PM",
        "category": "Display",
        "order": 5,
        "type": "TextWdg"
      },
      {
        "name": "display_mode",
        "title": "Display Mode",
        "description": "Determines whether to use the TACTIC calendar or the browser calendar",
        "category": "Display",
        "order": 6,
        "type": "SelectWdg",
        "values": [
          "browser",
          "inline"
        ]
      },
      {
        "name": "date_format",
        "title": "Date Format",
        "description": "Format of the date on clicking on a day in the Calendar, e.g. %m-%d-%Y",
        "category": "Display",
        "order": 8,
        "type": "TextWdg"
      },
      {
        "name": "display_format",
        "title": "Display Format",
        "description": "Display format like YYYY/MM/DD HH:MM AM",
        "category": "Display",
        "order": 9,
        "type": "TextWdg"
      },
      {
        "name": "hint_text",
        "title": "Hint Text",
        "description": "Hint text when the calendar input is read only",
        "category": "Display",
        "order": 10,
        "type": "TextWdg"
      }
    ]
  },
  {
    "value": "checkbox",
    "label": "Checkbox",
    "class": "pyasm.widget.input_wdg.CheckboxWdg",
    "aliases": [
      "CheckboxWdg",
      "CurrentCheckboxWdg",
      "pyasm.widget.CheckboxWdg",
      "pyasm.widget.input_wdg.CheckboxWdg",
      "pyasm.widget.input_wdg.CurrentCheckboxWdg"
    ],
    "options": [
      {
        "name": "default",
        "title": "Default",
        "description": "Default state of the checkbox (true|false)",
        "category": "Options",
        "order": 1,
        "type": "SelectWdg",
        "values": [
          "true",
          "false"
        ]
      },
      {
        "name": "read_only",
        "title": "Read Only",
        "description": "Whether to set this checkbox to read-only",
        "category": "Options",
        "order": 2,
        "type": "SelectWdg",
        "values": [
          "true",
          "false"
        ]
      }
    ]
  },
  {
    "value": "color",
    "label": "Color",
    "class": "tactic.ui.input.color_input_wdg.ColorInputWdg",
    "aliases": [
      "ColorInputWdg",
      "tactic.ui.input.ColorInputWdg",
      "tactic.ui.input.color_input_wdg.ColorInputWdg"
    ],
    "options": [
      {
        "name": "start_color",
        "title": "Start Color",
        "description": "Default starting hex color",
        "category": "Options",
        "order": 1,
        "type": "TextWdg"
      },
      {
        "name": "read_only",
        "title": "Read Only",
        "description": "Whether to set this field to read-only",
        "category": "Options",
        "order": 2,
        "type": "SelectWdg",
        "values": [
          "true",
          "false"
        ]
      }
    ]
  }
];

export function displayWidgetArgs(widget) {
  const key = String(widget || '').trim();
  const match = DISPLAY_WIDGET_ARGS.find(
    (item) => item.value === key || item.class === key || (item.aliases || []).indexOf(key) >= 0
  );
  return match ? match.options : [];
}

export function editWidgetArgs(widget) {
  const key = String(widget || '').trim();
  if (!key) return EDIT_WIDGET_ARGS[0].options;
  const match = EDIT_WIDGET_ARGS.find(
    (item) => item.value === key || item.class === key || (item.aliases || []).indexOf(key) >= 0
  );
  return match ? match.options : [];
}

export function editWidgetOptionsFor(widget) {
  const key = String(widget || '').trim();
  const base = [{ value: '', label: 'Default' }].concat(
    EDIT_WIDGET_ARGS.map((item) => ({
      value:
        item.value === key ||
        item.class === key ||
        (item.aliases || []).indexOf(key) >= 0
          ? key
          : item.value,
      label: item.label
    }))
  );
  if (!key || base.some((item) => item.value === key)) return base;
  return [{ value: key, label: key }].concat(base);
}

export function humanizeOptionName(name) {
  return String(name || '')
    .replace(/-/g, '_')
    .split('_')
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
}
