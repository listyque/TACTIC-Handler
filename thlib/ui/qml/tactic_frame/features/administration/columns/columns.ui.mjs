import { button } from '../../../core/frame.mjs';
import { node } from '../../../core/frame.mjs';
import {
    rect,
    label,
    muted,
    toolbar,
    notices,
    tabs,
    policy
} from '../admin.document.mjs';
import {
    sections as form,
    captionHeight
} from '../../../controls/forms/sections.ui.mjs';
import { pending, elementFieldValue } from './columns.state.mjs';
import {
    displayWidgetArgs,
    editWidgetArgs,
    editWidgetOptionsFor,
    humanizeOptionName
} from './widget_args.mjs';
import { translate } from '../../../core/strings.mjs';
export { toolbar };
const WIDGET_SPECS = [
    {
        values: [
            '',
            'TextWdg',
            'SimpleTableElementWdg',
            'tactic.ui.common.SimpleTableElementWdg',
            'tactic.ui.common.base_table_element_wdg.SimpleTableElementWdg',
            'pyasm.widget.SimpleTableElementWdg',
            'pyasm.widget.table_element_wdg.SimpleTableElementWdg',
            'pyasm.widget.input_wdg.TextWdg'
        ],
        kind: 'value',
        title: 'Automatic',
        icon: 'type',
        summary:
            'Displays the field value using its schema type, cell icon, alignment, and badge style.',
        optionsHint:
            'XML options: <column>, <value_icon>, <value_align>, <value_style>, <value_text_style>.'
    },
    {
        values: [
            'format',
            'tactic.ui.table.FormatElementWdg',
            'tactic.ui.table.format_element_wdg.FormatElementWdg'
        ],
        kind: 'format',
        title: 'Format',
        icon: 'tune',
        summary:
            'Formats text, numbers, currency, dates, timestamps, or checkboxes.',
        optionsHint:
            'XML options: <type>integer|float|currency|percent|date|time|timecode|Checkbox</type>, <format>-1234.12|YYYY-MM-DD</format>, <fps>24</fps>, <total_summary>total|average|count</total_summary>.'
    },
    {
        values: [
            'expression',
            'tactic.ui.table.ExpressionElementWdg',
            'tactic.ui.table.expression_element_wdg.ExpressionElementWdg'
        ],
        kind: 'expression',
        title: 'Expression',
        icon: 'code',
        summary:
            'Computes a read-only value or aggregate from a TACTIC expression (@GET, @COUNT, @SUM).',
        optionsHint:
            'XML options: <expression>@GET(...)</expression>, <mode>value|boolean|check</mode>, <use_cache>true|false</use_cache>, <order_by>, <bottom>, <group_bottom>.'
    },
    {
        values: [
            'expression_value',
            'tactic.ui.table.ExpressionValueElementWdg',
            'tactic.ui.table.expression_element_wdg.ExpressionValueElementWdg'
        ],
        kind: 'expression',
        title: 'Expression value',
        icon: 'code',
        summary:
            'Evaluates a TACTIC expression while keeping the column bound to an editable field.',
        optionsHint:
            'XML options: <expression>@GET(...)</expression>, <mode>value|boolean|check</mode>, <use_cache>true|false</use_cache>.'
    },
    {
        values: [
            'link',
            'tactic.ui.table.LinkElementWdg',
            'tactic.ui.table.link_element_wdg.LinkElementWdg'
        ],
        kind: 'link',
        title: 'Link',
        icon: 'open-in-new',
        summary:
            'Renders the cell value as a clickable hyperlink or external URL.',
        optionsHint:
            'XML options: <column>, <icon> (reads URL from the column value or expression).'
    },
    {
        values: [
            'pyasm.widget.ThumbWdg',
            'ThumbWdg',
            'pyasm.widget.file_wdg.ThumbWdg',
            'tactic.ui.panel.ThumbWdg2'
        ],
        kind: 'preview',
        title: 'Thumbnail',
        icon: 'image',
        summary:
            'Shows the latest snapshot preview image or an avatar badge for the row.',
        optionsHint:
            'XML options: <icon_context>icon|publish</icon_context>, <filename>true|false</filename>, <latest_icon>true|false</latest_icon>, <original>true|false</original>.'
    },
    {
        values: [
            'tactic.ui.widget.DiscussionElementWdg',
            'tactic.ui.widget.discussion_wdg.DiscussionElementWdg',
            'DiscussionWdg',
            'pyasm.widget.DiscussionWdg',
            'pyasm.widget.discussion_wdg.DiscussionWdg',
            'tactic.ui.widget.DiscussionWdg',
            'tactic.ui.widget.discussion_wdg.DiscussionWdg'
        ],
        kind: 'notes',
        title: 'Notes',
        icon: 'comment',
        summary:
            'Opens process notes and discussion comments with a message count badge.',
        optionsHint:
            'XML options: <process>, <context>, <use_parent>true|false</use_parent>. Legacy HTML popup flags (note_format, dialog_position, show_fullscreen_button, allow_email) are ignored because notes open in the unified inspector.'
    },
    {
        values: [
            'tactic.ui.table.TaskElementWdg',
            'tactic.ui.table.task_element_wdg.TaskElementWdg',
            'SObjectTaskTableElement',
            'pyasm.widget.SObjectTaskTableElement',
            'pyasm.widget.task_wdg.SObjectTaskTableElement'
        ],
        kind: 'tasks',
        title: 'Tasks',
        icon: 'tasks',
        summary:
            'Displays interactive workflow task cards with process, status, and assignee.',
        optionsHint:
            'XML options: <process>, <context>, <pipeline_code>, <show_current_pipeline_only>true|false</show_current_pipeline_only>, <edit>true|false</edit>.'
    },
    {
        values: [
            'tactic.ui.table.TaskCompletionWdg',
            'tactic.ui.table.statistic_wdg.TaskCompletionWdg',
            'TaskCompletionWdg',
            'pyasm.widget.TaskCompletionWdg',
            'pyasm.widget.statistic_wdg.TaskCompletionWdg',
            'tactic.ui.table.MilestoneCompletionWdg',
            'tactic.ui.table.statistic_wdg.MilestoneCompletionWdg'
        ],
        kind: 'completion',
        title: 'Task completion',
        icon: 'check-circle',
        summary:
            'Renders a progress bar showing overall task completion percentage for the row.',
        optionsHint:
            'XML options: <task_expr> (optional TACTIC expression to filter which tasks are counted).'
    },
    {
        values: [
            'tactic.ui.table.gantt_element_wdg.GanttElementWdg',
            'tactic.ui.table.GanttElementWdg',
            'GanttWdg',
            'pyasm.widget.GanttWdg',
            'pyasm.widget.gantt_wdg.GanttWdg'
        ],
        kind: 'gantt',
        title: 'Gantt',
        icon: 'calendar',
        summary: 'Shows a schedule timeline bar from task start and end dates.',
        optionsHint:
            'XML options: <options>[{"start_date_col":"bid_start_date","end_date_col":"bid_end_date"}]</options>, <range_start_date>, <range_end_date>.'
    },
    {
        values: [
            'tactic.ui.table.hidden_row_element_wdg.HiddenRowElementWdg',
            'tactic.ui.table.HiddenRowElementWdg',
            'HiddenRowToggleWdg',
            'pyasm.widget.HiddenRowToggleWdg',
            'pyasm.widget.table_element_wdg.HiddenRowToggleWdg',
            'tactic.ui.table.hidden_row_element_wdg.RowAddElementWdg',
            'tactic.ui.table.RowAddElementWdg'
        ],
        kind: 'related',
        title: 'Show related table',
        icon: 'table',
        summary:
            'Adds a button with a counter that expands an inline nested table of related records.',
        optionsHint:
            'XML options: <search_type>, <view>, <dynamic_class>tactic.ui.panel.FastTableLayoutWdg</dynamic_class>, <value_icon>.'
    },
    {
        values: [
            'tactic.ui.table.DropElementWdg',
            'tactic.ui.table.drop_element_wdg.DropElementWdg'
        ],
        kind: 'related',
        title: 'Instance links',
        icon: 'layers',
        summary:
            'Lists linked related records and supports drag-and-drop linking.',
        optionsHint:
            'XML options: <instance_type>, <accepted_drop_type>, <path>.'
    },
    {
        values: [
            'tactic.ui.table.ButtonElementWdg',
            'tactic.ui.table.button_wdg.ButtonElementWdg'
        ],
        kind: 'action',
        title: 'Configured button',
        icon: 'play',
        actionIcon: 'play',
        summary:
            'Runs a custom server Python script or client action when clicked.',
        optionsHint: 'XML options: <script_path>, <icon>, <hint>, <color>.'
    },
    {
        values: [
            'tactic.ui.table.CustomLayoutElementWdg',
            'tactic.ui.table.custom_layout_element_wdg.CustomLayoutElementWdg'
        ],
        kind: 'expression',
        title: 'Custom Layout',
        icon: 'dashboard',
        summary:
            'Renders a custom HTML/Mako layout template inside the table cell.',
        optionsHint:
            'XML options: <view> (saved custom layout view name) or inline <html>.'
    },
    {
        values: [
            'tactic.ui.table.SObjectDetailElementWdg',
            'tactic.ui.table.sobject_detail_wdg.SObjectDetailElementWdg'
        ],
        kind: 'action',
        title: 'SObject details',
        icon: 'info',
        actionIcon: 'info',
        summary: 'Opens the full record detail inspector for the row.',
        optionsHint: 'XML options: no extra <display> options required.'
    },
    {
        values: [
            'tactic.ui.table.CheckinButtonElementWdg',
            'tactic.ui.table.table_element_wdg.CheckinButtonElementWdg'
        ],
        kind: 'action',
        title: 'Check-in',
        icon: 'upload',
        actionIcon: 'upload',
        summary:
            'Opens the file upload and snapshot check-in dialog for the row.',
        optionsHint:
            'XML options: <process>, <subcontext>, <transfer_mode>upload|copy|move</transfer_mode>, <sobject_mode>self|parent|connect|expression</sobject_mode>.'
    },
    {
        values: [
            'tactic.ui.table.ExploreElementWdg',
            'tactic.ui.table.ExplorerElementWdg',
            'tactic.ui.table.explorer_wdg.ExplorerElementWdg',
            'tactic.ui.table.ExplorerTableElementWdg',
            'tactic.ui.table.explorer_wdg.ExplorerTableElementWdg'
        ],
        kind: 'action',
        title: 'Explorer',
        icon: 'folder',
        actionIcon: 'folder',
        summary: 'Opens the local sandbox or repository folder for the row.',
        optionsHint: 'XML options: <mode>sandbox|repository</mode>.'
    },
    {
        values: [
            'tactic.ui.table.SObjectFilesElementWdg',
            'tactic.ui.table.sobject_summary_wdg.SObjectFilesElementWdg'
        ],
        kind: 'action',
        title: 'Files',
        icon: 'description',
        actionIcon: 'description',
        summary: 'Lists published snapshot files attached to the record.',
        optionsHint: 'XML options: <expression> (optional snapshot/file query).'
    },
    {
        values: [
            'tactic.ui.table.MetadataElementWdg',
            'tactic.ui.table.metadata_element_wdg.MetadataElementWdg'
        ],
        kind: 'action',
        title: 'Metadata',
        icon: 'tune',
        actionIcon: 'tune',
        summary: 'Inspects snapshot and file metadata for the record.',
        optionsHint: 'XML options: no extra <display> options required.'
    },
    {
        values: [
            'tactic.ui.table.DeleteElementWdg',
            'tactic.ui.table.delete_element_wdg.DeleteElementWdg'
        ],
        kind: 'action',
        title: 'Delete',
        icon: 'delete',
        actionIcon: 'delete',
        summary:
            'Provides an action button to delete the record from the table.',
        optionsHint: 'XML options: no extra <display> options required.'
    },
    {
        values: [
            'tactic.ui.common.base_table_element_wdg.RawTableElementWdg',
            'tactic.ui.common.RawTableElementWdg'
        ],
        kind: 'value',
        title: 'Raw value',
        icon: 'database',
        summary: 'Displays the unformatted raw database column value.',
        optionsHint:
            'XML options: <column> (optional database column override).'
    }
];

function widgetSpec(widget) {
    const key = String(widget || '').trim();
    return (
        WIDGET_SPECS.find((item) => item.values.indexOf(key) >= 0) || {
            kind: 'value',
            title: key || 'Automatic',
            customTitle: Boolean(key),
            icon: 'cube',
            summary: 'Custom or legacy TACTIC table element class.',
            optionsHint:
                'XML options: edit custom <display> parameters directly in Selected element XML below.'
        }
    );
}

function alignOffset(containerWidth, contentWidth, align, pad = 10) {
    if (align === 'center')
        return Math.max(pad, Math.round((containerWidth - contentWidth) / 2));
    if (align === 'right')
        return Math.max(pad, containerWidth - contentWidth - pad);
    return pad;
}

function previewCellNodes(spec, element, cellW, cellH, headingText, tr) {
    const bodyY = 22,
        bodyH = cellH - bodyY,
        align = element.valueAlign || '';
    const children = [
        node('Box', 'definitionWidgetPreviewHeader', rect(0, 0, cellW, bodyY), {
            background: 'surfaceContainerHigh',
            radius: 7,
            children: [
                label(
                    'definitionWidgetPreviewHeaderLabel',
                    rect(8, 0, cellW - 16, bodyY),
                    String(
                        headingText || element.title || element.name || 'COLUMN'
                    )
                        .slice(0, 22)
                        .toUpperCase(),
                    {
                        fontRole: 'caption',
                        weight: 600,
                        align: 'center',
                        color: 'secondaryText'
                    }
                )
            ]
        })
    ];
    if (spec.kind === 'preview') {
        const x = alignOffset(cellW, 30, align || 'center', 10);
        children.push(
            node(
                'Box',
                'definitionWidgetPreviewThumb',
                rect(x, bodyY + Math.round((bodyH - 30) / 2), 30, 30),
                {
                    background: 'contentSelection',
                    border: 'primary',
                    radius: 15,
                    children: [
                        node(
                            'Icon',
                            'definitionWidgetPreviewThumbIcon',
                            rect(7, 7, 16, 16),
                            {
                                icon: 'image',
                                color: 'primaryText'
                            }
                        )
                    ]
                }
            )
        );
    } else if (spec.kind === 'notes') {
        const w = Math.min(cellW - 16, 118),
            x = alignOffset(cellW, w, align || 'center', 8);
        children.push(
            node(
                'Box',
                'definitionWidgetPreviewNotes',
                rect(x, bodyY + Math.round((bodyH - 28) / 2), w, 28),
                {
                    background: 'surfaceContainerHigh',
                    border: 'primary',
                    radius: 6,
                    children: [
                        node(
                            'Icon',
                            'definitionWidgetPreviewNotesIcon',
                            rect(8, 7, 14, 14),
                            {
                                icon: 'comment',
                                color: 'primary'
                            }
                        ),
                        label(
                            'definitionWidgetPreviewNotesLabel',
                            rect(26, 0, w - 32, 28),
                            tr('Notes') + ' (3)',
                            {
                                fontRole: 'caption',
                                weight: 600
                            }
                        )
                    ]
                }
            )
        );
    } else if (spec.kind === 'tasks') {
        const w = Math.min(cellW - 16, 136),
            x = alignOffset(cellW, w, align || 'left', 8);
        children.push(
            node(
                'Box',
                'definitionWidgetPreviewTasks',
                rect(x, bodyY + Math.round((bodyH - 34) / 2), w, 34),
                {
                    background: 'surfaceContainerHigh',
                    border: 'primary',
                    radius: 6,
                    children: [
                        label(
                            'definitionWidgetPreviewTaskProcess',
                            rect(8, 2, w - 16, 15),
                            'model',
                            {
                                fontRole: 'caption',
                                weight: 600
                            }
                        ),
                        node(
                            'Icon',
                            'definitionWidgetPreviewTaskUserIcon',
                            rect(8, 19, 11, 11),
                            {
                                icon: 'user',
                                color: 'secondaryText'
                            }
                        ),
                        label(
                            'definitionWidgetPreviewTaskUser',
                            rect(22, 16, w - 28, 15),
                            'admin',
                            {
                                fontRole: 'caption',
                                color: 'secondaryText'
                            }
                        )
                    ]
                }
            )
        );
    } else if (spec.kind === 'completion' || spec.kind === 'gantt') {
        const barW = Math.max(40, cellW - 24);
        children.push(
            node(
                'Box',
                'definitionWidgetPreviewBarTrack',
                rect(12, bodyY + 10, barW, 8),
                {
                    background: 'surfaceContainerHigh',
                    radius: 4,
                    children: [
                        node(
                            'Box',
                            'definitionWidgetPreviewBarFill',
                            rect(0, 0, Math.round(barW * 0.72), 8),
                            {
                                background: 'primary',
                                radius: 4
                            }
                        )
                    ]
                }
            ),
            label(
                'definitionWidgetPreviewBarLabel',
                rect(12, bodyY + 21, barW, 18),
                spec.kind === 'gantt' ? '12 May – 18 May' : '72%',
                {
                    fontRole: 'caption',
                    align: 'center',
                    color: 'secondaryText'
                }
            )
        );
    } else if (spec.kind === 'related') {
        const w = Math.min(cellW - 16, 128),
            x = alignOffset(cellW, w, align || 'center', 8),
            iconName =
                (Object.prototype.hasOwnProperty.call(element, 'valueIcon')
                    ? element.valueIcon
                    : '') || 'cube';
        children.push(
            node(
                'Box',
                'definitionWidgetPreviewRelated',
                rect(x, bodyY + Math.round((bodyH - 28) / 2), w, 28),
                {
                    background: 'surfaceContainerHigh',
                    border: 'outlineVariant',
                    radius: 6,
                    children: [
                        node(
                            'Icon',
                            'definitionWidgetPreviewRelatedIcon',
                            rect(8, 7, 14, 14),
                            {
                                icon: iconName,
                                color: 'secondaryText'
                            }
                        ),
                        label(
                            'definitionWidgetPreviewRelatedLabel',
                            rect(26, 0, w - 46, 28),
                            'Assets 4',
                            {
                                fontRole: 'caption',
                                weight: 600
                            }
                        ),
                        node(
                            'Icon',
                            'definitionWidgetPreviewRelatedArrow',
                            rect(w - 18, 7, 13, 13),
                            {
                                icon: 'chevron-right',
                                color: 'secondaryText'
                            }
                        )
                    ]
                }
            )
        );
    } else if (spec.kind === 'action') {
        const x = alignOffset(cellW, 30, align || 'center', 8);
        children.push(
            node(
                'Box',
                'definitionWidgetPreviewAction',
                rect(x, bodyY + Math.round((bodyH - 28) / 2), 30, 28),
                {
                    background: 'surfaceContainerHigh',
                    border: 'outlineVariant',
                    radius: 6,
                    children: [
                        node(
                            'Icon',
                            'definitionWidgetPreviewActionIcon',
                            rect(7, 6, 15, 15),
                            {
                                icon: spec.actionIcon || 'play',
                                color:
                                    spec.actionIcon === 'delete'
                                        ? 'error'
                                        : 'primaryText'
                            }
                        )
                    ]
                }
            )
        );
    } else if (spec.kind === 'link') {
        children.push(
            node(
                'Icon',
                'definitionWidgetPreviewLinkIcon',
                rect(10, bodyY + 15, 14, 14),
                {
                    icon: 'open-in-new',
                    color: 'primary'
                }
            ),
            label(
                'definitionWidgetPreviewLinkLabel',
                rect(28, bodyY + 8, cellW - 36, 28),
                element.name || 'EP-001',
                {
                    fontRole: 'caption',
                    weight: 600,
                    color: 'primary',
                    align: align || 'left'
                }
            )
        );
    } else if (spec.kind === 'expression') {
        children.push(
            node(
                'Box',
                'definitionWidgetPreviewExprTag',
                rect(10, bodyY + 12, 22, 20),
                {
                    background: 'surfaceContainerHigh',
                    border: 'outlineVariant',
                    radius: 4,
                    children: [
                        label(
                            'definitionWidgetPreviewExprTagLabel',
                            rect(0, 0, 22, 20),
                            'fx',
                            {
                                fontRole: 'caption',
                                weight: 600,
                                align: 'center',
                                color: 'primary'
                            }
                        )
                    ]
                }
            ),
            label(
                'definitionWidgetPreviewExprValue',
                rect(38, bodyY + 8, cellW - 46, 28),
                'Episode 01',
                {
                    fontRole:
                        element.valueTextStyle === 'heading'
                            ? 'bodyLarge'
                            : element.valueTextStyle === 'small'
                              ? 'caption'
                              : 'body',
                    weight: element.valueTextStyle === 'heading' ? 600 : 400,
                    align: align || 'left'
                }
            )
        );
    } else {
        const isBadge =
                element.valueStyle === 'badge' ||
                (!element.valueStyle && element.name === 'duration'),
            iconName = Object.prototype.hasOwnProperty.call(
                element,
                'valueIcon'
            )
                ? element.valueIcon
                : element.name === 'duration'
                  ? 'clock'
                  : '',
            sampleText =
                element.name === 'duration'
                    ? '20 Seconds'
                    : spec.kind === 'format'
                      ? '2026-11-04'
                      : 'Episode 01',
            fontRole =
                element.valueTextStyle === 'heading'
                    ? 'bodyLarge'
                    : element.valueTextStyle === 'small'
                      ? 'caption'
                      : 'body';
        if (isBadge) {
            const w = Math.min(cellW - 16, 118),
                x = alignOffset(cellW, w, align || 'left', 8);
            children.push(
                node(
                    'Box',
                    'definitionWidgetPreviewBadge',
                    rect(x, bodyY + Math.round((bodyH - 28) / 2), w, 28),
                    {
                        background: 'surfaceContainerHigh',
                        border: 'outlineVariant',
                        radius: 6,
                        children: (iconName
                            ? [
                                  node(
                                      'Icon',
                                      'definitionWidgetPreviewBadgeIcon',
                                      rect(8, 7, 14, 14),
                                      {
                                          icon: iconName,
                                          color: 'secondaryText'
                                      }
                                  )
                              ]
                            : []
                        ).concat([
                            label(
                                'definitionWidgetPreviewBadgeLabel',
                                rect(
                                    iconName ? 26 : 8,
                                    0,
                                    w - (iconName ? 32 : 16),
                                    28
                                ),
                                sampleText,
                                {
                                    fontRole: 'caption',
                                    weight: 600,
                                    align: iconName ? 'left' : 'center'
                                }
                            )
                        ])
                    }
                )
            );
        } else {
            if (iconName)
                children.push(
                    node(
                        'Icon',
                        'definitionWidgetPreviewValueIcon',
                        rect(10, bodyY + 15, 14, 14),
                        {
                            icon: iconName,
                            color: 'secondaryText'
                        }
                    )
                );
            children.push(
                label(
                    'definitionWidgetPreviewValueLabel',
                    rect(
                        iconName ? 28 : 10,
                        bodyY + 8,
                        cellW - (iconName ? 38 : 20),
                        28
                    ),
                    sampleText,
                    {
                        fontRole,
                        weight:
                            element.valueTextStyle === 'heading' ? 600 : 400,
                        align: align || 'left'
                    }
                )
            );
        }
    }
    return children;
}

function widgetPreviewField(element, headingText, formWidth, tr) {
    const spec = widgetSpec(element.widget),
        rowWidth = Math.max(200, formWidth - 32),
        wide = rowWidth >= 420,
        cellW = wide ? 184 : Math.min(220, rowWidth - 24),
        cellH = 66,
        textX = wide ? cellW + 24 : 12,
        textW = wide ? rowWidth - cellW - 36 : rowWidth - 24,
        summary = tr(spec.summary),
        optionsHint = spec.optionsHint ? tr(spec.optionsHint) : '',
        descH = Math.max(18, captionHeight(summary, textW)),
        optH = optionsHint
            ? Math.max(18, captionHeight(optionsHint, textW))
            : 0,
        textTotalH = 34 + descH + (optH ? optH + 6 : 0),
        boxH = wide ? Math.max(92, textTotalH + 10) : textTotalH + cellH + 18,
        cellX = 12,
        cellY = wide ? Math.round((boxH - cellH) / 2) : textTotalH + 6;
    const previewChildren = [
        node(
            'Box',
            'definitionWidgetPreviewCell',
            rect(cellX, cellY, cellW, cellH),
            {
                background: 'workspace',
                border: 'outlineVariant',
                radius: 8,
                children: previewCellNodes(
                    spec,
                    element,
                    cellW,
                    cellH,
                    headingText,
                    tr
                )
            }
        ),
        node('Icon', 'definitionWidgetPreviewIcon', rect(textX, 12, 16, 16), {
            icon: spec.icon,
            color: 'primary'
        }),
        label(
            'definitionWidgetPreviewTitle',
            rect(textX + 22, 10, textW - 22, 20),
            spec.customTitle ? spec.title : tr(spec.title),
            {
                fontRole: 'body',
                weight: 600
            }
        ),
        label(
            'definitionWidgetPreviewSummary',
            rect(textX, 32, textW, descH),
            summary,
            Object.assign({}, muted, {
                fontRole: 'caption',
                wrap: true
            })
        )
    ];
    if (optionsHint)
        previewChildren.push(
            label(
                'definitionWidgetPreviewOptions',
                rect(textX, 36 + descH, textW, optH),
                optionsHint,
                Object.assign({}, muted, {
                    fontRole: 'caption',
                    wrap: true
                })
            )
        );
    return {
        kind: 'Box',
        id: 'definitionWidgetPreview',
        title: 'Widget preview',
        fullWidth: true,
        height: boxH,
        props: {
            background: 'surfaceContainerLow',
            border: 'outlineVariant',
            radius: 10,
            children: previewChildren
        }
    };
}
const list = (id, bounds, source, rowHeight) =>
    node('List', id, bounds, {
        source,
        rowHeight,
        keyField: source === 'definitions' ? 'identity' : 'path',
        fields: [],
        scrollbarId: id + 'ScrollBar'
    });

const NON_TABLE_VIEWS = [
    'color',
    'custom_filter',
    'filter',
    'search',
    'simple_filter',
    'insert',
    'add_item',
    'overview'
];
const NON_TABLE_WIDGET_TYPES = [
    'widget',
    'layout',
    'theme',
    'dashboard',
    'chart',
    'sidebar',
    'custom_layout'
];
const NON_TABLE_SEARCH_TYPES = ['SideBarWdg', 'CustomLayoutWdg'];
const NON_TABLE_LAYOUT_RE =
    /layout\s*=\s*["'](?:CustomLayoutWdg|tactic\.ui\.panel\.CustomLayoutWdg|sobject-layout|ItemLayoutWdg)["']/i;

export function records(model, ui) {
    const query = ui.query.trim().toLowerCase();
    return model.records.filter((row) => {
        const view = String(row.view || '');
        const stype = String(row.searchType || '');
        const wtype = String(row.widgetType || '').toLowerCase();
        const cfg = String(row.config || '');
        if (NON_TABLE_SEARCH_TYPES.indexOf(stype) >= 0) return false;
        if (view.indexOf('link_search:') === 0) return false;
        if (NON_TABLE_VIEWS.indexOf(view) >= 0) return false;
        if (wtype && NON_TABLE_WIDGET_TYPES.indexOf(wtype) >= 0) return false;
        if (cfg && NON_TABLE_LAYOUT_RE.test(cfg)) return false;
        return (
            (!ui.searchType || stype === ui.searchType) &&
            (!query ||
                [
                    row.view,
                    row.searchType,
                    row.code,
                    row.login,
                    row.category,
                    row.widgetType,
                    row.config
                ]
                    .join(' ')
                    .toLowerCase()
                    .indexOf(query) >= 0)
        );
    });
}

function sanitizeId(raw) {
    return String(raw || '').replace(/[^A-Za-z0-9_-]/g, '_');
}

function buildOptionFields(specs, optionsMap, prefix, ui, text, tr, idPrefix) {
    const fields = [];
    const knownNames = {};
    const groups = [];
    const byCat = {};
    for (let i = 0; i < specs.length; i++) {
        const opt = specs[i];
        knownNames[opt.name] = true;
        const cat = opt.category || 'Options';
        if (!byCat[cat]) {
            byCat[cat] = [];
            groups.push({ category: cat, items: byCat[cat] });
        }
        byCat[cat].push(opt);
    }
    for (let g = 0; g < groups.length; g++) {
        const group = groups[g];
        const catKey = prefix + ':' + group.category;
        const collapsed = !!ui.collapsedCategories[catKey];
        const catId = idPrefix + 'Cat_' + sanitizeId(group.category) + '_' + g;
        fields.push({
            kind: 'Action',
            id: catId,
            title: group.category,
            fullWidth: true,
            height: 32,
            showDivider: false,
            props: {
                text: tr(group.category),
                normalColor: 'surfaceContainerHigh',
                selectedColor: 'contentSelection',
                action: {
                    type: 'toggleCategory',
                    key: catKey
                },
                children: [
                    node('Icon', catId + '_Icon', rect(8, 8, 16, 16), {
                        icon: collapsed ? 'chevron-right' : 'chevron-down',
                        color: 'primary'
                    }),
                    label(
                        catId + '_Label',
                        rect(28, 0, 260, 32),
                        tr(group.category),
                        {
                            fontRole: 'body',
                            weight: 600
                        }
                    ),
                    label(
                        catId + '_Count',
                        rect(290, 0, 48, 32),
                        String(group.items.length),
                        Object.assign({ align: 'right' }, muted)
                    )
                ]
            }
        });
        if (!collapsed) {
            for (let j = 0; j < group.items.length; j++) {
                const opt = group.items[j];
                const fieldKey = prefix + ':' + opt.name;
                const currentVal = String(
                    (optionsMap && optionsMap[opt.name]) || ''
                );
                const optId = idPrefix + 'Opt_' + sanitizeId(opt.name);
                const desc = [
                    opt.description || '',
                    opt.default ? 'Default: ' + opt.default : ''
                ]
                    .filter(Boolean)
                    .join(' · ');
                if (opt.values && opt.values.length) {
                    const choices = [
                        { value: '', label: tr('Default') }
                    ].concat(
                        opt.values.map((v) => ({
                            value: String(v),
                            label: String(v)
                        }))
                    );
                    if (
                        currentVal &&
                        !choices.some((c) => c.value === currentVal)
                    )
                        choices.splice(1, 0, {
                            value: currentVal,
                            label: currentVal
                        });
                    fields.push({
                        kind: 'Choice',
                        id: optId,
                        title: opt.title || humanizeOptionName(opt.name),
                        dataLabel: true,
                        description: desc,
                        field: fieldKey,
                        options: choices,
                        props: {
                            value: currentVal
                        }
                    });
                } else if (opt.type === 'CheckboxWdg') {
                    fields.push({
                        kind: 'Switch',
                        id: optId,
                        title: opt.title || humanizeOptionName(opt.name),
                        dataLabel: true,
                        description: desc,
                        field: fieldKey,
                        props: {
                            checked:
                                ['true', '1', 'yes', 'on'].indexOf(
                                    currentVal.toLowerCase()
                                ) >= 0
                        }
                    });
                } else {
                    fields.push({
                        id: optId,
                        title: opt.title || humanizeOptionName(opt.name),
                        dataLabel: true,
                        description: desc,
                        field: fieldKey,
                        props: {
                            text: text(fieldKey),
                            placeholder: opt.default ? String(opt.default) : '',
                            action: {
                                type: 'text',
                                field: fieldKey
                            },
                            commitAction: {
                                type: 'commit'
                            }
                        }
                    });
                }
            }
        }
    }

    const extraKeys = Object.keys(optionsMap || {}).filter(
        (k) => !knownNames[k]
    );
    if (extraKeys.length || prefix === 'option') {
        const extraCatKey = prefix + ':__extra__';
        const extraCollapsed = !!ui.collapsedCategories[extraCatKey];
        const extraCatId = idPrefix + 'Cat_ExtraOptions';
        fields.push({
            kind: 'Action',
            id: extraCatId,
            title: 'Extra Options',
            fullWidth: true,
            height: 32,
            showDivider: false,
            props: {
                text: tr('Extra Options'),
                normalColor: 'surfaceContainerHigh',
                selectedColor: 'contentSelection',
                action: {
                    type: 'toggleCategory',
                    key: extraCatKey
                },
                children: [
                    node('Icon', extraCatId + '_Icon', rect(8, 8, 16, 16), {
                        icon: extraCollapsed ? 'chevron-right' : 'chevron-down',
                        color: 'primary'
                    }),
                    label(
                        extraCatId + '_Label',
                        rect(28, 0, 260, 32),
                        tr('Extra Options'),
                        {
                            fontRole: 'body',
                            weight: 600
                        }
                    ),
                    label(
                        extraCatId + '_Count',
                        rect(290, 0, 48, 32),
                        String(extraKeys.length),
                        Object.assign({ align: 'right' }, muted)
                    )
                ]
            }
        });
        if (!extraCollapsed) {
            for (let k = 0; k < extraKeys.length; k++) {
                const key = extraKeys[k];
                const fieldKey = prefix + ':' + key;
                fields.push({
                    id: idPrefix + 'ExtraOpt_' + sanitizeId(key),
                    title: humanizeOptionName(key),
                    dataLabel: true,
                    description: '<' + key + '>',
                    field: fieldKey,
                    props: {
                        text: text(fieldKey),
                        action: {
                            type: 'text',
                            field: fieldKey
                        },
                        commitAction: {
                            type: 'commit'
                        }
                    }
                });
            }
            if (prefix === 'option') {
                fields.push({
                    id: 'definitionExtraOptAdd',
                    title: 'Add Extra Option',
                    description:
                        'Enter name=value and press Enter to add a custom <display> option.',
                    field: 'extraOptionAdd',
                    props: {
                        text: text('extraOptionAdd'),
                        placeholder: 'option_name=value',
                        action: {
                            type: 'text',
                            field: 'extraOptionAdd'
                        },
                        commitAction: {
                            type: 'commit'
                        }
                    }
                });
            }
        }
    }
    return fields;
}

function colorsSectionField(element, ui, formWidth, tr) {
    const open = !!ui.colorsOpen;
    const entries = element.colorMap || [];
    const rowWidth = Math.max(200, formWidth - 32);
    const children = [
        node('Action', 'definitionColorsToggle', rect(0, 0, rowWidth, 34), {
            text: tr('Colors'),
            normalColor: 'surfaceContainerHigh',
            selectedColor: 'contentSelection',
            action: {
                type: 'toggleSection',
                section: 'colors'
            },
            children: [
                node('Icon', 'definitionColorsToggleIcon', rect(8, 9, 16, 16), {
                    icon: open ? 'chevron-down' : 'chevron-right',
                    color: 'primary'
                }),
                label(
                    'definitionColorsToggleLabel',
                    rect(28, 0, rowWidth - 80, 34),
                    tr('Colors'),
                    {
                        fontRole: 'body',
                        weight: 600
                    }
                ),
                label(
                    'definitionColorsToggleCount',
                    rect(rowWidth - 52, 0, 44, 34),
                    entries.length ? String(entries.length) : '',
                    Object.assign({ align: 'right' }, muted)
                )
            ]
        })
    ];
    let totalH = 34;
    if (open) {
        if (!entries.length) {
            children.push(
                label(
                    'definitionColorsEmptyLabel',
                    rect(12, totalH + 6, rowWidth - 24, 28),
                    tr('No colors have been defined.'),
                    muted
                )
            );
            totalH += 40;
        } else {
            for (let i = 0; i < entries.length; i++) {
                const entry = entries[i];
                const ry = totalH + 6 + i * 28;
                children.push(
                    label(
                        'definitionColorItemLabel_' + i,
                        rect(16, ry, Math.max(60, rowWidth - 150), 24),
                        String(entry.label || ''),
                        { fontRole: 'caption', weight: 600 }
                    ),
                    label(
                        'definitionColorItemValue_' + i,
                        rect(Math.max(80, rowWidth - 130), ry, 116, 24),
                        String(entry.color || ''),
                        Object.assign(
                            { fontRole: 'caption', align: 'right' },
                            muted
                        )
                    )
                );
            }
            totalH += entries.length * 28 + 12;
        }
    }
    return {
        kind: 'Box',
        id: 'definitionColorsSection',
        title: 'Colors',
        fullWidth: true,
        height: totalH,
        showDivider: false,
        props: {
            background: 'surfaceContainerLow',
            border: 'outlineVariant',
            radius: 8,
            children
        }
    };
}

function configsSectionField(layers, ui, formWidth, tr) {
    const open = ui.configsOpen !== false;
    const listLayers = layers || [];
    const rowWidth = Math.max(200, formWidth - 32);
    const children = [
        node('Action', 'definitionConfigsToggle', rect(0, 0, rowWidth, 34), {
            text: tr('Definitions in Config (Advanced)'),
            normalColor: 'surfaceContainerHigh',
            selectedColor: 'contentSelection',
            action: {
                type: 'toggleSection',
                section: 'configs'
            },
            children: [
                node(
                    'Icon',
                    'definitionConfigsToggleIcon',
                    rect(8, 9, 16, 16),
                    {
                        icon: open ? 'chevron-down' : 'chevron-right',
                        color: 'primary'
                    }
                ),
                label(
                    'definitionConfigsToggleLabel',
                    rect(28, 0, rowWidth - 40, 34),
                    tr('Definitions in Config (Advanced)'),
                    {
                        fontRole: 'body',
                        weight: 600
                    }
                )
            ]
        })
    ];
    let totalH = 34;
    if (open) {
        if (!listLayers.length) {
            children.push(
                label(
                    'definitionConfigsEmptyLabel',
                    rect(12, totalH + 6, rowWidth - 24, 28),
                    tr('Select a Search Type to inspect layered definitions.'),
                    muted
                )
            );
            totalH += 40;
        } else {
            totalH += 4;
            for (let i = 0; i < listLayers.length; i++) {
                const layer = listLayers[i];
                const layerOpen = !!ui.expandedLayers[layer.key];
                const lid = 'definitionConfigLayer_' + sanitizeId(layer.key);
                children.push(
                    node('Action', lid, rect(4, totalH, rowWidth - 8, 30), {
                        text: layer.label,
                        normalColor: 'transparent',
                        selectedColor: 'contentSelection',
                        enabled: !!layer.defined && !!layer.xml,
                        action: {
                            type: 'toggleLayer',
                            key: layer.key
                        },
                        children: [
                            node('Icon', lid + '_Arrow', rect(8, 7, 15, 15), {
                                icon: layerOpen
                                    ? 'chevron-down'
                                    : 'chevron-right',
                                color: layer.defined
                                    ? 'primaryText'
                                    : 'secondaryText'
                            }),
                            label(
                                lid + '_Label',
                                rect(28, 0, rowWidth - 64, 30),
                                layer.label,
                                {
                                    fontRole: 'caption',
                                    weight: layer.defined ? 600 : 400,
                                    color: layer.defined
                                        ? 'primaryText'
                                        : 'secondaryText'
                                }
                            ),
                            node(
                                'Box',
                                lid + '_Dot',
                                rect(rowWidth - 28, 9, 12, 12),
                                {
                                    background: layer.defined
                                        ? 'green'
                                        : 'error',
                                    border: 'outlineVariant',
                                    radius: 6,
                                    children: [
                                        label(
                                            lid + '_DotText',
                                            rect(0, 0, 12, 12),
                                            ''
                                        )
                                    ]
                                }
                            )
                        ]
                    })
                );
                totalH += 32;
                if (layerOpen && layer.xml) {
                    children.push(
                        node(
                            'Area',
                            lid + '_Xml',
                            rect(24, totalH, rowWidth - 36, 96),
                            {
                                text: layer.xml,
                                label: layer.label,
                                monospace: true,
                                readOnly: true
                            }
                        )
                    );
                    totalH += 102;
                }
            }
            totalH += 6;
        }
    }
    return {
        kind: 'Box',
        id: 'definitionConfigsSection',
        title: 'Definitions in Config (Advanced)',
        fullWidth: true,
        height: totalH,
        showDivider: false,
        props: {
            background: 'surfaceContainerLow',
            border: 'outlineVariant',
            radius: 8,
            children
        }
    };
}

export function describe(model, ui, width, height, language) {
    if (width <= 0 || height <= 0)
        return {
            nodes: []
        };
    const tr = (text) => translate(text, language),
        notice = notices(
            model,
            ui,
            width,
            language,
            'Discard unsaved definition changes?'
        ),
        nodes = notice.nodes;
    const y = notice.top,
        minimum = y + 380;
    if (height < minimum)
        return {
            nodes: [
                node('Scroll', 'columnsPageScroll', rect(0, 0, width, height), {
                    contentHeight: minimum,
                    scrollbarId: 'columnsPageScrollBar',
                    children: describe(model, ui, width - 16, minimum, language)
                        .nodes
                })
            ]
        };
    const split = width >= 850,
        catalogVisible = ui.catalogVisible !== false,
        left = split
            ? catalogVisible
                ? Math.min(ui.catalogWidth, width * 0.44)
                : 56
            : width,
        h = height - y;
    const edit = policy(model).editable && !ui.confirmation,
        navigate =
            !model.busy && !model.dirty && !model.uncertain && !ui.confirmation;
    if (split || !ui.editing) {
        const filteredRecords = records(model, ui),
            children = [];
        if (!split || catalogVisible) {
            children.push(
                label(
                    'definitionCatalogHeading',
                    rect(12, 10, Math.max(0, left - (split ? 108 : 70)), 34),
                    tr('Saved definitions'),
                    {
                        weight: 600
                    }
                ),
                label(
                    'definitionCatalogCount',
                    rect(left - (split ? 92 : 58), 10, 42, 34),
                    String(filteredRecords.length),
                    muted
                ),
                node(
                    'Choice',
                    'definitionCatalogSearchTypeFilter',
                    rect(12, 52, left - 24, 38),
                    {
                        label: tr('Filter by Search Type'),
                        value: ui.searchType,
                        options: [
                            {
                                value: '',
                                label: tr('All Search Types')
                            }
                        ].concat(
                            model.typeOptions.map((row) => ({
                                value: row.value,
                                label: row.label
                            }))
                        ),
                        enabled: navigate,
                        action: {
                            type: 'searchType'
                        }
                    }
                ),
                node(
                    'Field',
                    'definitionCatalogFilter',
                    rect(12, 98, left - 24, 38),
                    {
                        text: ui.query,
                        label: tr('Filter saved views'),
                        placeholder: tr('Filter saved views'),
                        enabled: navigate,
                        action: {
                            type: 'query'
                        }
                    }
                ),
                list(
                    'definitionCatalogList',
                    rect(12, 144, left - 24, Math.max(0, h - 156)),
                    'definitions',
                    64
                )
            );
            if (!filteredRecords.length)
                children.push(
                    label(
                        'definitionCatalogEmpty',
                        rect(24, 156, left - 48, 100),
                        tr(
                            model.busy
                                ? 'Working on the server…'
                                : 'No saved definitions match the filter'
                        ),
                        {
                            wrap: true,
                            color: 'secondaryText'
                        }
                    )
                );
        }
        if (split)
            children.push(
                button(
                    'columnsToggleCatalog',
                    rect(
                        catalogVisible ? left - 46 : (left - 34) / 2,
                        10,
                        34,
                        34
                    ),
                    tr(
                        catalogVisible
                            ? 'Hide saved definitions'
                            : 'Show saved definitions'
                    ),
                    catalogVisible ? 'chevron-left' : 'chevron-right',
                    {
                        type: 'catalogVisible'
                    },
                    true,
                    {
                        iconOnly: true,
                        iconAction: true,
                        round: false
                    }
                )
            );
        nodes.push(
            node('Box', 'definitionCatalogPanel', rect(0, y, left, h), {
                background: 'surfaceContainerLow',
                border: 'outlineVariant',
                children
            })
        );
    }
    if (split && catalogVisible)
        nodes.push(
            node(
                'Splitter',
                'columnsCatalogSplitHandle',
                rect(left, y, 10, h),
                {
                    text: tr('Saved definitions panel width'),
                    min: 220,
                    max: width * 0.44,
                    value: left,
                    action: {
                        type: 'split',
                        field: 'catalogWidth'
                    }
                }
            )
        );
    if (split || ui.editing)
        editor(
            nodes,
            model,
            ui,
            rect(
                split ? left + 10 : 0,
                y,
                split ? width - left - 10 : width,
                h
            ),
            language,
            edit,
            !split
        );
    return {
        nodes
    };
}

function editor(nodes, model, ui, bounds, language, edit, back) {
    const tr = (text) => translate(text, language),
        width = bounds.width,
        inner = width - 40,
        children = [];
    let y = 12;
    if (back) {
        children.push(
            button(
                'columnsBack',
                rect(12, y, 100, 36),
                tr('Back'),
                'chevron-left',
                {
                    type: 'back'
                },
                !model.busy
            )
        );
        y += 44;
    }
    if (!model.ready)
        children.push(
            label(
                'columnsSelectHelp',
                rect(12, y, inner, 100),
                tr('Select a definition'),
                {
                    wrap: true,
                    color: 'secondaryText'
                }
            )
        );
    else {
        const selected = model.selected,
            compactHeader = width < 620,
            modeTabsW = compactHeader ? Math.floor((width - 32) / 2) : 176,
            viewEditTabsW = compactHeader
                ? width - 32 - modeTabsW
                : Math.min(240, Math.max(180, width - 380)),
            tabsX = compactHeader
                ? 12 + viewEditTabsW + 8
                : width - modeTabsW - 12,
            viewEditX = compactHeader ? 12 : tabsX - viewEditTabsW - 8,
            metaText = [
                selected.searchType,
                selected.login,
                model.wizard?.layout ? tr('Layout: ') + model.wizard.layout : ''
            ]
                .filter(Boolean)
                .join(' · ');
        children.push(
            label(
                'definitionViewTitle',
                rect(
                    12,
                    y,
                    compactHeader ? inner : Math.max(80, viewEditX - 20),
                    24
                ),
                selected.view,
                {
                    fontRole: 'section',
                    weight: 600
                }
            )
        );
        if (!compactHeader && metaText) {
            const titleW = Math.min(180, selected.view.length * 9 + 16);
            if (viewEditX - 24 - titleW > 40)
                children.push(
                    label(
                        'definitionViewType',
                        rect(
                            12 + titleW,
                            y + 2,
                            Math.max(1, viewEditX - 24 - titleW),
                            22
                        ),
                        metaText,
                        muted
                    )
                );
        }
        if (compactHeader && metaText) {
            y += 26;
            children.push(
                label(
                    'definitionViewType',
                    rect(12, y, inner, 20),
                    metaText,
                    muted
                )
            );
            y += 24;
        }
        children.push(
            tabs(
                'definitionViewEditMode',
                [
                    {
                        value: 'view',
                        label: tr('VIEW MODE'),
                        icon: 'eye'
                    },
                    {
                        value: 'edit',
                        label: tr('EDIT MODE'),
                        icon: 'edit'
                    }
                ],
                ui.viewMode || 'view',
                rect(viewEditX, compactHeader ? y : y - 4, viewEditTabsW, 34),
                !model.busy,
                'viewMode'
            ),
            tabs(
                'definitionCatalogMode',
                [
                    {
                        value: 'simple',
                        label: tr('Form'),
                        icon: 'table'
                    },
                    {
                        value: 'xml',
                        label: 'XML',
                        icon: 'code'
                    }
                ],
                ui.mode,
                rect(tabsX, compactHeader ? y : y - 4, modeTabsW, 34),
                !model.busy,
                'mode'
            )
        );
        y += compactHeader ? 42 : 38;
        if (ui.mode === 'xml')
            children.push(
                node(
                    'Area',
                    'definitionCatalogXml',
                    rect(12, y, width - 24, bounds.height - y - 42),
                    {
                        text: model.xml,
                        label: tr('Definition XML'),
                        monospace: true,
                        enabled: edit,
                        action: {
                            type: 'xml'
                        }
                    }
                )
            );
        else if (model.wizard.supported && model.elements.length) {
            const stacked = width < 720,
                columnWidth = stacked
                    ? width - 24
                    : Math.min(ui.columnWidth, width * 0.4),
                columnHeight = stacked
                    ? Math.min(ui.columnHeight, (bounds.height - y - 42) * 0.48)
                    : bounds.height - y - 42,
                selectedIndex = model.elements.findIndex(
                    (row) => row.path === model.element.path
                ),
                defElements = model.definitionElements || [],
                hasDefSection = defElements.length > 0 && columnHeight >= 220,
                topListH = hasDefSection
                    ? Math.max(84, Math.floor((columnHeight - 72) * 0.52))
                    : Math.max(40, columnHeight - 34),
                canRemoveFromView =
                    edit &&
                    !pending(ui) &&
                    model.elements.length > 1 &&
                    selectedIndex >= 0 &&
                    [
                        'definition',
                        'default_definition',
                        'edit_definition'
                    ].indexOf(selected.view) < 0;
            children.push(
                label(
                    'definitionColumnsLabel',
                    rect(12, y + 2, Math.max(40, columnWidth - 110), 24),
                    humanizeOptionName(selected.view || 'Columns'),
                    {
                        fontRole: 'secondary',
                        weight: 600,
                        color: 'primaryText'
                    }
                )
            );
            for (const [offset, title, icon, x] of [
                [-1, 'Move up', 'arrow-up', 12 + columnWidth - 106],
                [1, 'Move down', 'arrow-down', 12 + columnWidth - 70]
            ])
                children.push(
                    node(
                        'Button',
                        offset < 0
                            ? 'definitionColumnUp'
                            : 'definitionColumnDown',
                        rect(x, y, 32, 28),
                        {
                            text: tr(title),
                            icon,
                            iconOnly: true,
                            round: false,
                            enabled:
                                edit &&
                                !pending(ui) &&
                                selectedIndex >= 0 &&
                                !!model.elements[selectedIndex + offset],
                            action: { type: 'move', value: offset }
                        }
                    )
                );
            children.push(
                node(
                    'Button',
                    'definitionColumnRemove',
                    rect(12 + columnWidth - 34, y, 32, 28),
                    {
                        text: tr('Remove from view'),
                        icon: 'delete',
                        iconOnly: true,
                        round: false,
                        destructive: true,
                        enabled: canRemoveFromView,
                        action: { type: 'removeElement' }
                    }
                ),
                list(
                    'definitionCatalogElementList',
                    rect(12, y + 32, columnWidth, topListH),
                    'columns',
                    52
                )
            );

            if (hasDefSection) {
                const defHeaderY = y + 32 + topListH + 8,
                    defListY = defHeaderY + 28,
                    defListH = Math.max(48, y + columnHeight - defListY),
                    rowW = Math.max(80, columnWidth - 16),
                    defRowH = 44;
                children.push(
                    label(
                        'definitionAllColumnsHeading',
                        rect(
                            12,
                            defHeaderY,
                            Math.max(40, columnWidth - 52),
                            24
                        ),
                        tr('Definition'),
                        {
                            fontRole: 'secondary',
                            weight: 600,
                            color: 'primaryText'
                        }
                    ),
                    label(
                        'definitionAllColumnsCount',
                        rect(12 + columnWidth - 44, defHeaderY, 44, 24),
                        String(defElements.length),
                        Object.assign({ align: 'right' }, muted)
                    )
                );
                const defRows = [];
                for (let i = 0; i < defElements.length; i++) {
                    const item = defElements[i];
                    const itemKey = sanitizeId(item.name || i);
                    const isSelected =
                        model.element.name === item.name &&
                        model.element.path === item.path;
                    const canAdd =
                        edit &&
                        !pending(ui) &&
                        !item.inView &&
                        ['definition', 'default_definition'].indexOf(
                            selected.view
                        ) < 0;
                    const textW = canAdd ? rowW - 72 : rowW - 38;
                    const shortWidget = (item.widget || '').split('.').pop();
                    defRows.push(
                        node(
                            'Action',
                            'definitionAllColumn_' + itemKey,
                            rect(
                                0,
                                i * defRowH,
                                canAdd ? rowW - 34 : rowW,
                                defRowH - 2
                            ),
                            {
                                text: item.name,
                                selected: isSelected,
                                normalColor: 'transparent',
                                selectedColor: 'contentSelection',
                                rail: false,
                                enabled: !model.busy && !ui.confirmation,
                                action: {
                                    type: 'column',
                                    path: item.path
                                },
                                children: [
                                    node(
                                        'Icon',
                                        'definitionAllColumnIcon_' + itemKey,
                                        rect(8, 12, 16, 16),
                                        {
                                            icon: item.inView
                                                ? 'check-circle'
                                                : 'cube',
                                            color: item.inView
                                                ? 'action'
                                                : 'secondaryText'
                                        }
                                    ),
                                    label(
                                        'definitionAllColumnTitle_' + itemKey,
                                        rect(30, 3, Math.max(20, textW), 20),
                                        item.title || item.name,
                                        {
                                            fontRole: 'caption',
                                            weight: 600
                                        }
                                    ),
                                    label(
                                        'definitionAllColumnDetail_' + itemKey,
                                        rect(30, 22, Math.max(20, textW), 16),
                                        item.name +
                                            (shortWidget
                                                ? ' · ' + shortWidget
                                                : ''),
                                        Object.assign(
                                            { fontRole: 'caption' },
                                            muted
                                        )
                                    )
                                ]
                            }
                        )
                    );
                    if (canAdd) {
                        defRows.push(
                            node(
                                'Button',
                                'definitionAddColumn_' + itemKey,
                                rect(rowW - 30, i * defRowH + 6, 28, 28),
                                {
                                    text: tr('Add to view'),
                                    icon: 'add',
                                    iconOnly: true,
                                    round: false,
                                    enabled: true,
                                    action: {
                                        type: 'addElement',
                                        name: item.name
                                    }
                                }
                            )
                        );
                    }
                }
                children.push(
                    node(
                        'Box',
                        'definitionAllColumnsBox',
                        rect(12, defListY, columnWidth, defListH),
                        {
                            background: 'surfaceContainer',
                            border: 'outlineVariant',
                            radius: 8,
                            children: [
                                node(
                                    'Scroll',
                                    'definitionAllColumnsScroll',
                                    rect(
                                        2,
                                        2,
                                        columnWidth - 4,
                                        Math.max(1, defListH - 4)
                                    ),
                                    {
                                        contentHeight: Math.max(
                                            defListH - 4,
                                            defElements.length * defRowH
                                        ),
                                        scrollbarId:
                                            'definitionAllColumnsScrollBar',
                                        children: defRows
                                    }
                                )
                            ]
                        }
                    )
                );
            }

            children.push(
                node(
                    'Splitter',
                    'definitionColumnsSplitHandle',
                    rect(
                        stacked ? 12 : 12 + columnWidth,
                        stacked ? y + columnHeight : y,
                        stacked ? columnWidth : 10,
                        stacked ? 10 : columnHeight
                    ),
                    {
                        horizontal: stacked,
                        text: tr(
                            stacked
                                ? 'Columns list height'
                                : 'Columns list width'
                        ),
                        value: stacked ? columnHeight : columnWidth,
                        min: stacked ? 100 : 180,
                        max: stacked
                            ? Math.max(100, bounds.height * 0.48)
                            : width * 0.4,
                        action: {
                            type: 'split',
                            field: stacked ? 'columnHeight' : 'columnWidth'
                        }
                    }
                )
            );
            const formX = stacked ? 12 : columnWidth + 22,
                formY = stacked ? y + columnHeight + 10 : y,
                formWidth = width - formX - 28;
            const element = model.element,
                text = (key) =>
                    Object.prototype.hasOwnProperty.call(ui.text, key)
                        ? ui.text[key]
                        : elementFieldValue(element, key),
                isEditMode = ui.viewMode === 'edit';

            let fields = [
                {
                    kind: 'Heading',
                    id: 'definitionColumnHeading',
                    title: isEditMode
                        ? 'Edit Mode Definition'
                        : 'Edit Column Definition',
                    description: isEditMode
                        ? 'Configure how this column is edited in tables and forms (edit / edit_definition).'
                        : 'Configure display attributes, widget options, colors, and layered definitions.'
                },
                {
                    kind: 'Label',
                    id: 'definitionWidgetIdentifier',
                    fullWidth: true,
                    height: Math.max(
                        34,
                        captionHeight(
                            element.widget || tr('Inherited from definition'),
                            formWidth - 32
                        )
                    ),
                    props: {
                        text: element.widget || tr('Inherited from definition'),
                        wrap: true
                    }
                }
            ];

            if (
                element.inView === false &&
                element.name &&
                ['definition', 'default_definition'].indexOf(selected.view) < 0
            ) {
                fields.push({
                    kind: 'Button',
                    id: 'definitionAddSelectedToView',
                    title: 'Add column to current view',
                    props: {
                        icon: 'add',
                        highlighted: true,
                        enabled: edit && !pending(ui),
                        action: {
                            type: 'addElement',
                            name: element.name
                        }
                    }
                });
            }

            if (!isEditMode) {
                const displaySpecs = displayWidgetArgs(
                    element.widget || element.displayClass
                );
                fields = fields.concat([
                    {
                        id: 'definitionCatalogTitle',
                        title: 'Title',
                        description: 'The column heading shown to users.',
                        field: 'title',
                        props: {
                            text: text('title'),
                            placeholder: element.name || '',
                            action: {
                                type: 'text',
                                field: 'title'
                            },
                            commitAction: {
                                type: 'commit'
                            }
                        }
                    },
                    {
                        kind: 'Label',
                        id: 'definitionCatalogName',
                        title: 'Name',
                        description: 'Native field identifier.',
                        props: {
                            text: element.name || ''
                        }
                    },
                    {
                        kind: 'Number',
                        min: 48,
                        max: 640,
                        step: 8,
                        value: element.width,
                        id: 'definitionCatalogWidth',
                        title: 'Width',
                        description: 'Default width in the table view.',
                        field: 'width',
                        props: {
                            text: text('width'),
                            inputMode: 'numeric',
                            action: {
                                type: 'text',
                                field: 'width'
                            },
                            commitAction: {
                                type: 'commit'
                            },
                            keys: {
                                ArrowUp: {
                                    type: 'step',
                                    value: 8
                                },
                                ArrowDown: {
                                    type: 'step',
                                    value: -8
                                }
                            }
                        }
                    },
                    {
                        kind: 'Switch',
                        id: 'definitionCatalogColor',
                        title: 'Enable Colors',
                        description:
                            'Apply value-based cell colors from the color config.',
                        field: 'color',
                        props: {
                            checked: element.color !== false
                        }
                    },
                    {
                        kind: 'Switch',
                        id: 'definitionCatalogVisible',
                        title: 'Show in table',
                        description:
                            'Keep the column visible in this saved view.',
                        field: 'visible',
                        props: {
                            checked: element.visible !== false
                        }
                    },
                    {
                        id: 'definitionCatalogValueIcon',
                        kind: 'IconChoice',
                        title: 'Cell icon',
                        description:
                            'Icon beside text values and related-table counts. Used by quick filters unless overridden.',
                        field: 'valueIcon',
                        props: {
                            value: Object.prototype.hasOwnProperty.call(
                                element,
                                'valueIcon'
                            )
                                ? element.valueIcon
                                : element.name === 'duration'
                                  ? 'clock'
                                  : '',
                            tacticCompatibleOnly: true
                        }
                    },
                    {
                        kind: 'Choice',
                        id: 'definitionCatalogTextStyle',
                        title: 'Cell text style',
                        description:
                            'Size and emphasis of text values in this column.',
                        field: 'valueTextStyle',
                        options: [
                            { value: '', label: tr('Standard') },
                            { value: 'heading', label: tr('Heading') },
                            { value: 'small', label: tr('Small text') }
                        ],
                        props: { value: element.valueTextStyle || '' }
                    },
                    {
                        kind: 'Choice',
                        id: 'definitionCatalogValueAlign',
                        title: 'Cell alignment',
                        description:
                            'Horizontal position of content in this column.',
                        field: 'valueAlign',
                        options: [
                            { value: '', label: tr('Automatic') },
                            { value: 'left', label: tr('Left') },
                            { value: 'center', label: tr('Center') },
                            { value: 'right', label: tr('Right') }
                        ],
                        props: { value: element.valueAlign || '' }
                    },
                    {
                        kind: 'Choice',
                        id: 'definitionCatalogValueStyle',
                        title: 'Value appearance',
                        description: 'Automatic shows Duration as a badge.',
                        field: 'valueStyle',
                        options: [
                            { value: '', label: tr('Automatic') },
                            { value: 'text', label: tr('Text') },
                            { value: 'badge', label: tr('Badge') }
                        ],
                        props: { value: element.valueStyle || '' }
                    },
                    {
                        kind: 'Heading',
                        id: 'definitionDisplayOptionsHeading',
                        title: 'Display Options',
                        description:
                            'Widget type, Python class path, and widget-specific <display> parameters.'
                    },
                    {
                        kind: 'Choice',
                        id: 'definitionCatalogWidget',
                        title: 'Widget Type',
                        description: 'Choose a supported TACTIC table widget.',
                        field: 'widget',
                        options: model.widgetOptions.map((row) => ({
                            value: row.value,
                            label: tr(row.label)
                        })),
                        props: {
                            value: element.widget || ''
                        }
                    },
                    {
                        kind: 'Switch',
                        id: 'definitionCatalogShowAllWidgets',
                        title: 'Show specialized and system widgets',
                        description:
                            'Include task, snapshot, timecard, JSON/XML, and administrative table widgets.',
                        props: {
                            checked: !!ui.showAllWidgets,
                            action: {
                                type: 'showAllWidgets'
                            }
                        }
                    },
                    {
                        id: 'definitionCatalogDisplayClass',
                        title: 'Class Name',
                        description:
                            'Explicit Python class name (<display class="..."/>), e.g. ThumbWdg.',
                        field: 'displayClass',
                        props: {
                            text: Object.prototype.hasOwnProperty.call(
                                ui.text,
                                'displayClass'
                            )
                                ? ui.text.displayClass
                                : element.displayClass || element.widget || '',
                            placeholder: 'pyasm.widget.ThumbWdg',
                            action: {
                                type: 'text',
                                field: 'displayClass'
                            },
                            commitAction: {
                                type: 'commit'
                            }
                        }
                    },
                    widgetPreviewField(
                        element,
                        text('title') || element.title,
                        formWidth,
                        tr
                    )
                ]);

                fields = fields.concat(
                    buildOptionFields(
                        displaySpecs,
                        element.displayOptions || {},
                        'option',
                        ui,
                        text,
                        tr,
                        'definitionDisplay'
                    )
                );

                fields.push(
                    colorsSectionField(element, ui, formWidth, tr),
                    configsSectionField(
                        element.configLayers || [],
                        ui,
                        formWidth,
                        tr
                    )
                );
            } else {
                const editSpecs = editWidgetArgs(
                    element.editWidget || element.editClass
                );
                const editChoices = editWidgetOptionsFor(
                    element.editWidget
                ).map((row) => ({
                    value: row.value,
                    label: tr(row.label)
                }));
                fields = fields.concat([
                    {
                        kind: 'Label',
                        id: 'definitionCatalogName',
                        title: 'Name',
                        description: 'Native field identifier.',
                        props: {
                            text: element.name || ''
                        }
                    },
                    {
                        kind: 'Switch',
                        id: 'definitionCatalogEditable',
                        title: 'Enable Edit',
                        description:
                            'Allow editing this column in tables and forms.',
                        field: 'editable',
                        props: {
                            checked: element.editable !== false
                        }
                    },
                    {
                        kind: 'Heading',
                        id: 'definitionEditOptionsHeading',
                        title: 'Edit Options',
                        description:
                            'Input widget type, Python class name, and <edit> / <display> parameters.'
                    },
                    {
                        kind: 'Choice',
                        id: 'definitionCatalogEditWidget',
                        title: 'Widget Type',
                        description: 'Choose an input widget for editing.',
                        field: 'editWidget',
                        options: editChoices,
                        props: {
                            value: element.editWidget || ''
                        }
                    },
                    {
                        id: 'definitionCatalogEditClass',
                        title: 'Class Name',
                        description:
                            'Explicit input widget class name, e.g. pyasm.widget.SelectWdg.',
                        field: 'editClass',
                        props: {
                            text: Object.prototype.hasOwnProperty.call(
                                ui.text,
                                'editClass'
                            )
                                ? ui.text.editClass
                                : element.editClass || element.editWidget || '',
                            placeholder: 'pyasm.widget.TextWdg',
                            action: {
                                type: 'text',
                                field: 'editClass'
                            },
                            commitAction: {
                                type: 'commit'
                            }
                        }
                    }
                ]);

                fields = fields.concat(
                    buildOptionFields(
                        editSpecs,
                        element.editOptions || {},
                        'editOption',
                        ui,
                        text,
                        tr,
                        'definitionEdit'
                    )
                );

                fields.push(
                    {
                        kind: 'Heading',
                        id: 'definitionEditActionHeading',
                        title: 'Action',
                        description:
                            'Server command executed when saving this field (<action class="..."/>).'
                    },
                    {
                        id: 'definitionCatalogActionClass',
                        title: 'Action Class Name',
                        description:
                            'Optional command handler class, e.g. pyasm.command.NullAction.',
                        field: 'actionClass',
                        props: {
                            text: text('actionClass'),
                            placeholder: 'pyasm.command.DatabaseAction',
                            action: {
                                type: 'text',
                                field: 'actionClass'
                            },
                            commitAction: {
                                type: 'commit'
                            }
                        }
                    }
                );

                const actionOptKeys = Object.keys(element.actionOptions || {});
                for (let a = 0; a < actionOptKeys.length; a++) {
                    const aKey = actionOptKeys[a];
                    const aField = 'actionOption:' + aKey;
                    fields.push({
                        id: 'definitionActionOpt_' + sanitizeId(aKey),
                        title: humanizeOptionName(aKey),
                        dataLabel: true,
                        description: '<action><' + aKey + '>',
                        field: aField,
                        props: {
                            text: text(aField),
                            action: {
                                type: 'text',
                                field: aField
                            },
                            commitAction: {
                                type: 'commit'
                            }
                        }
                    });
                }

                fields.push(
                    configsSectionField(
                        element.editConfigLayers || [],
                        ui,
                        formWidth,
                        tr
                    )
                );
            }

            fields = fields.concat([
                {
                    kind: 'Heading',
                    id: 'definitionElementXmlHeading',
                    title: 'Selected element XML'
                },
                {
                    kind: 'Area',
                    id: 'definitionCatalogElementXml',
                    title: 'Selected element XML',
                    fullWidth: true,
                    height: 180,
                    props: {
                        text: text('xml'),
                        monospace: true,
                        wrap: false,
                        action: {
                            type: 'text',
                            field: 'xml'
                        }
                    }
                },
                {
                    kind: 'Button',
                    id: 'definitionApplyElementXml',
                    title: 'Apply XML',
                    props: {
                        icon: 'code',
                        enabled:
                            edit &&
                            Object.prototype.hasOwnProperty.call(
                                ui.text,
                                'xml'
                            ),
                        action: {
                            type: 'commit'
                        }
                    }
                }
            ]);

            const body = form(fields, formWidth, language, edit);
            children.push(
                node(
                    'Scroll',
                    'definitionCatalogForm',
                    rect(
                        formX,
                        formY,
                        width - formX - 12,
                        Math.max(1, bounds.height - formY - 42)
                    ),
                    {
                        contentHeight: body.height,
                        resetKey: ui.path + ':' + (ui.viewMode || 'view'),
                        scrollbarId: 'definitionCatalogFormScrollBar',
                        children: body.nodes
                    }
                )
            );
        } else {
            children.push(
                label(
                    'definitionCatalogWizardEmpty',
                    rect(12, y, width - 24, 100),
                    tr(
                        model.wizard.error ||
                            (model.wizard.supported
                                ? 'This TACTIC view has no columns. Add elements in XML mode.'
                                : 'This definition does not use a native TACTIC table layout. Open XML to edit its exact structure.')
                    ),
                    {
                        wrap: true,
                        color: 'secondaryText'
                    }
                ),
                button(
                    'definitionOpenXml',
                    rect(12, y + 108, inner, 38),
                    tr('Open XML'),
                    'code',
                    {
                        type: 'mode',
                        value: 'xml'
                    },
                    !model.busy
                )
            );
        }
        children.push(
            label(
                'definitionCode',
                rect(12, bounds.height - 30, inner, 22),
                selected.code || '',
                muted
            )
        );
    }
    nodes.push(
        node('Box', 'definitionEditorPanel', bounds, {
            background: 'surfaceContainerLow',
            border: 'outlineVariant',
            children
        })
    );
}
export function row(listNode, record, model, ui) {
    const width = listNode.width - 16,
        definition = listNode.source === 'definitions',
        selected = definition
            ? model.selected.identity === record.identity
            : model.element.path === record.path;
    return {
        nodes: [
            node(
                'Action',
                definition
                    ? 'definitionRow_' + record.identity
                    : 'definitionColumn_' + record.path,
                rect(0, 0, width, definition ? 60 : 48),
                {
                    text: definition
                        ? record.view +
                          ' · ' +
                          record.searchType +
                          (record.login ? ' · ' + record.login : '')
                        : record.name,
                    selected,
                    normalColor: 'transparent',
                    selectedColor: 'contentSelection',
                    rail: false,
                    enabled:
                        !model.busy &&
                        !ui.confirmation &&
                        (!definition || (!model.dirty && !model.uncertain)),
                    action: definition
                        ? {
                              type: 'select',
                              identity: record.identity
                          }
                        : {
                              type: 'column',
                              path: record.path
                          },
                    children: [
                        node(
                            'Icon',
                            'definitionRowIcon_' +
                                (record.identity || record.path),
                            rect(10, definition ? 18 : 15, 18, 18),
                            {
                                icon: definition
                                    ? 'table'
                                    : record.visible
                                      ? 'eye'
                                      : 'eye-off',
                                color: 'action'
                            }
                        ),
                        label(
                            'definitionRowTitle_' +
                                (record.identity || record.path),
                            rect(38, definition ? 6 : 4, width - 48, 22),
                            definition ? record.view : record.title,
                            {
                                weight: 600
                            }
                        ),
                        label(
                            'definitionRowDetail_' +
                                (record.identity || record.path),
                            rect(38, definition ? 30 : 25, width - 48, 18),
                            definition
                                ? record.searchType +
                                      (record.login ? ' · ' + record.login : '')
                                : record.name,
                            muted
                        )
                    ]
                }
            )
        ]
    };
}
