import { node, rect, label, muted, button } from '../../../core/frame.mjs';
import { translate } from '../../../core/strings.mjs';
import {
    notices,
    toolbar as documentToolbar,
    policy,
    sectionSelector
} from '../admin.document.mjs';
import { inspector } from './inspector.ui.mjs';
export { inspector };
import { panel as catalogPanel } from './catalog.ui.mjs';
export { records, row, models } from './catalog.ui.mjs';
import { nodeTypeMeta } from './process.ui.mjs';
const own = (object, key) => Object.prototype.hasOwnProperty.call(object, key);
export function toolbar(model, ui, width, language) {
    const result = documentToolbar(model, ui, width, language),
        tr = (text) => translate(text, language);
    result.nodes = result.nodes.filter(
        (row) => row.id !== 'adminDocumentStatus'
    );
    result.nodes.push(
        button(
            model.mode === 'workflow'
                ? 'adminCreateDocument'
                : 'adminCreateSchemaType',
            rect(46, 0, 38, 38),
            tr(
                model.mode === 'workflow'
                    ? 'Create workflow'
                    : 'New Search Type'
            ),
            'add',
            {
                type:
                    model.mode === 'workflow' ? 'createWorkflow' : 'createType',
                searchType:
                    model.document.searchType || model.creationSearchType
            },
            !model.busy &&
                !model.uncertain &&
                (model.canWrite || model.metadata.canCreate) &&
                (!model.dirty || model.mode !== 'workflow') &&
                (model.mode !== 'workflow' ||
                    !!(model.document.searchType || model.creationSearchType)),
            {
                iconOnly: true
            }
        )
    );
    return result;
}
export function describe(model, ui, width, height, language) {
    if (width <= 0 || height <= 0)
        return {
            nodes: []
        };
    const tr = (text, values) => translate(text, language, values),
        workflow = model.mode === 'workflow',
        internalCatalog = workflow,
        narrow = width < (workflow ? 1000 : 800),
        edit = policy(model).editable && !ui.confirmation;
    const noticeModel = Object.assign({}, model, {
        error: model.error || ui.error
    });
    if (ui.confirmation === 'remove')
        noticeModel.confirmationText = workflow
            ? 'Remove the selection from this workflow draft?'
            : 'Remove the selection from the schema draft? Search Types, tables and data will be kept.';
    if (ui.confirmation === 'selection')
        noticeModel.confirmationText = 'Discard unapplied JSON changes?';
    const notice = notices(
            noticeModel,
            ui,
            width,
            language,
            undefined,
            ui.confirmation === 'remove' ? 'Remove from canvas' : undefined
        ),
        nodes = notice.nodes;
    let y = notice.top;
    nodes.push(
        sectionSelector(
            'adminGraphPages',
            [
                {
                    value: 'canvas',
                    label: tr('Canvas'),
                    icon: 'schema'
                },
                {
                    value: 'technical',
                    label: tr('Technical'),
                    icon: 'code'
                }
            ],
            ui.page,
            rect(0, y, Math.min(width, 320), 38),
            !model.busy,
            'page'
        )
    );
    if (workflow && ui.page === 'canvas') {
        const settingsY = width >= 560 ? y : y + 46;
        nodes.push(
            button(
                'adminEditPipeline',
                rect(
                    width >= 560 ? 328 : 0,
                    settingsY,
                    Math.min(200, width),
                    38
                ),
                tr('Pipeline settings'),
                'tune',
                { type: 'clear' },
                !model.busy
            )
        );
        if (width < 560) y += 46;
    }
    if (!workflow && ui.page === 'canvas') {
        const toggles = [
            [
                'adminSchemaToggleColumns',
                tr('Columns: from → to'),
                'code',
                'showColumns',
                172
            ],
            [
                'adminSchemaToggleRoles',
                tr('Parent / Child & M:N'),
                'hierarchy',
                'showRoles',
                188
            ],
            [
                'adminSchemaToggleCodes',
                tr('Tables & codes'),
                'table',
                'showCodes',
                148
            ],
            ['adminSchemaToggleLegend', tr('Legend'), 'info', 'showLegend', 118]
        ];
        if (width >= 980) {
            let bx = 332;
            for (const [id, text, icon, key, btnW] of toggles) {
                nodes.push(
                    button(
                        id,
                        rect(bx, y, btnW, 38),
                        text,
                        icon,
                        {
                            type: 'toggleSchemaView',
                            key
                        },
                        !model.busy,
                        {
                            highlighted: !!ui[key],
                            selected: !!ui[key],
                            round: false
                        }
                    )
                );
                bx += btnW + 8;
            }
        } else {
            y += 46;
            const cols = width >= 680 ? 4 : width >= 340 ? 2 : 1,
                gap = 8,
                cellW = Math.max(
                    40,
                    Math.floor((width - (cols - 1) * gap) / cols)
                );
            toggles.forEach(([id, text, icon, key], idx) => {
                const r = Math.floor(idx / cols),
                    c = idx % cols;
                nodes.push(
                    button(
                        id,
                        rect(c * (cellW + gap), y + r * 44, cellW, 38),
                        text,
                        icon,
                        {
                            type: 'toggleSchemaView',
                            key
                        },
                        !model.busy,
                        {
                            highlighted: !!ui[key],
                            selected: !!ui[key],
                            round: false
                        }
                    )
                );
            });
            y += (Math.ceil(toggles.length / cols) - 1) * 44;
        }
    }
    y += 46;
    if (workflow) {
        const searchType =
            model.document.searchType || model.creationSearchType || '';
        const details = (model.metadata.searchTypes || []).find(
            (record) => record.identity === searchType
        );
        const context =
            details && details.label && details.label !== searchType
                ? details.label + ' · ' + searchType
                : searchType;
        const text = searchType
            ? tr('Search Type: %1').replace('%1', context)
            : tr(
                  'No Search Type is linked. Create a workflow from the Search Type editor.'
              );
        const captionHeight = Math.max(
            18,
            Math.ceil((text.length * 6) / Math.max(1, width)) * 15
        );
        const color = details?.color || '';
        if (color)
            nodes.push(
                node(
                    'Box',
                    'adminWorkflowSearchTypeColor',
                    rect(0, y, 3, captionHeight),
                    { background: color, radius: 1 }
                )
            );
        nodes.push(
            label(
                'adminWorkflowSearchType',
                rect(
                    color ? 12 : 0,
                    y,
                    width - (color ? 12 : 0),
                    captionHeight
                ),
                text,
                Object.assign({}, muted, { wrap: true })
            )
        );
        y += captionHeight + 12;
    }
    if (!model.ready) {
        nodes.push(
            label(
                'adminGraphEmpty',
                rect(12, y, width - 24, 80),
                tr('Select a workflow or create a new one.'),
                {
                    wrap: true
                }
            )
        );
    }
    const info = model.metadata.shared
        ? 'Shared pipeline: read-only. Create a project-owned pipeline to make project-specific changes.'
        : !workflow && model.identity && !model.canWrite
          ? 'Built-in system schema · read-only'
          : '';
    if (info) {
        nodes.push(
            label(
                'adminGraphReadOnly',
                rect(0, y, width, 64),
                tr(info),
                Object.assign(
                    {
                        wrap: true
                    },
                    muted
                )
            )
        );
        y += 72;
    }
    const missing = workflow
        ? (model.nodes || [])
              .filter((row) => row.referenceOnly)
              .map((row) => row.identity)
        : [];
    if (missing.length) {
        nodes.push(
            node('Area', 'adminMissingProcesses', rect(0, y, width, 68), {
                label: tr('Missing processes'),
                text:
                    tr('Connections refer to missing processes') +
                    ': ' +
                    missing.join(', '),
                notice: true,
                readOnly: true,
                color: 'error'
            })
        );
        y += 76;
    }
    if (narrow) {
        nodes.push(
            sectionSelector(
                'adminGraphPanels',
                [].concat(
                    internalCatalog
                        ? [
                              {
                                  value: 'catalog',
                                  label: tr('Workflows'),
                                  icon: 'list'
                              }
                          ]
                        : [],
                    [
                        {
                            value: 'canvas',
                            label: tr('Canvas'),
                            icon: 'schema'
                        },
                        {
                            value: 'properties',
                            label: tr('Properties'),
                            icon: 'tune'
                        }
                    ]
                ),
                ui.panel,
                rect(0, y, width, 38),
                !model.busy,
                'panel'
            )
        );
        y += 46;
    }
    const h = Math.max(1, height - y),
        catalogWidth =
            internalCatalog && !narrow
                ? ui.catalogVisible
                    ? Math.min(ui.catalogWidth, width * 0.28)
                    : 56
                : 0,
        propertiesWidth = !narrow
            ? ui.propertiesVisible
                ? Math.min(
                      ui.propertiesWidth,
                      workflow ? 460 : 420,
                      width * (workflow ? 0.5 : 0.45)
                  )
                : 56
            : 0;
    if (internalCatalog && (!narrow || ui.panel === 'catalog')) {
        const w = narrow ? width : catalogWidth;
        nodes.push(
            Object.assign(
                catalogPanel(model, ui, rect(0, y, w, h), language, narrow),
                {
                    visible: ui.page === 'canvas' || !narrow
                }
            )
        );
        if (!narrow && ui.catalogVisible)
            nodes.push(
                node('Splitter', 'adminCatalogSplit', rect(w, y, 10, h), {
                    visible: ui.page === 'canvas' || !narrow,
                    text: tr('Workflow list width'),
                    value: w,
                    min: 180,
                    max: Math.min(420, width * 0.28),
                    action: {
                        type: 'catalogSplit'
                    }
                })
            );
    }
    const x = narrow ? 0 : internalCatalog ? catalogWidth + 10 : 0,
        graphWidth = narrow
            ? width
            : Math.max(1, width - x - propertiesWidth - 10);
    const searchTypeMap = {},
        linkTableSet = new Set();
    for (const item of model.metadata.searchTypes || []) {
        searchTypeMap[item.identity] = item;
    }
    for (const row of model.nodes || []) {
        if (
            row.kind === 'instance' ||
            row.attributes?.type === 'instance' ||
            row.attributes?.node_type === 'instance' ||
            searchTypeMap[row.identity]?.linkTable
        ) {
            linkTableSet.add(row.identity);
        }
    }
    if (!workflow) {
        const allEdges = model.edges || [];
        for (const edge of allEdges) {
            const inst =
                edge.instance_type ||
                (edge.relationship === 'instance' ? edge.path || '' : '');
            if (inst) linkTableSet.add(inst);
        }
        for (const row of model.nodes || []) {
            const id = String(row.identity || ''),
                outTargets = new Set(
                    allEdges
                        .filter((e) => e.from === id && e.to && e.to !== id)
                        .map((e) => e.to)
                ),
                inEdges = allEdges.filter(
                    (e) =>
                        e.to === id &&
                        e.from !== id &&
                        e.relationship !== 'instance'
                );
            if (
                /(^|\/)[a-z0-9_]+_in_[a-z0-9_]+$/i.test(id) ||
                (/\bin\b/i.test(row.label || '') &&
                    outTargets.size >= 2 &&
                    inEdges.length === 0)
            ) {
                linkTableSet.add(id);
            }
        }
    }
    const namespaceCounts = {};
    if (!workflow) {
        for (const row of model.nodes || []) {
            const id = String(row.identity || ''),
                ns = id.includes('/') ? id.split('/')[0] : '';
            if (
                ns &&
                ns !== 'sthpw' &&
                ns !== 'config' &&
                !linkTableSet.has(id)
            ) {
                namespaceCounts[ns] = (namespaceCounts[ns] || 0) + 1;
            }
        }
    }
    const primaryNamespace =
        Object.keys(namespaceCounts).sort(
            (a, b) => namespaceCounts[b] - namespaceCounts[a]
        )[0] || '';
    const nodeShortLabel = (identity) => {
        const found = (model.nodes || []).find((n) => n.identity === identity),
            meta = searchTypeMap[identity] || {},
            raw =
                (found && found.label) ||
                meta.label ||
                meta.table ||
                String(identity || '')
                    .split('/')
                    .pop() ||
                String(identity || '');
        return String(raw).length > 18
            ? String(raw).slice(0, 16) + '…'
            : String(raw);
    };
    const graphNodes = (model.nodes || []).map((row) => {
        const pendingCreation =
                !!model.document.newTypes &&
                own(model.document.newTypes, row.identity),
            draftType =
                !!model.document.draftTypes &&
                own(model.document.draftTypes, row.identity);
        let subtitle,
            secondarySubtitle = '',
            visualKind = '',
            icon = '',
            badgeText = '',
            nodeColor = row.color || '';
        if (workflow) {
            const wfKind = row.referenceOnly
                    ? 'missing'
                    : row.kind === 'process' || !row.kind
                      ? 'manual'
                      : row.kind,
                wfMeta = nodeTypeMeta(wfKind, tr);
            visualKind = wfKind;
            icon = row.referenceOnly ? 'warning' : wfMeta.icon;
            badgeText = row.referenceOnly ? '!' : wfMeta.badge;
            nodeColor = row.color || (row.referenceOnly ? '' : wfMeta.color);
            subtitle = row.referenceOnly ? tr('Missing process') : wfMeta.label;
        } else {
            const isLink = linkTableSet.has(row.identity) || pendingCreation,
                allEdges = model.edges || [],
                linkTargetSet = new Set(),
                meta = searchTypeMap[row.identity] || {},
                table =
                    meta.table ||
                    String(row.identity || '')
                        .split('/')
                        .pop(),
                ns = String(row.identity || '').includes('/')
                    ? String(row.identity || '').split('/')[0]
                    : '',
                isSystem = ns === 'sthpw' || ns === 'config',
                isExternal =
                    !isSystem &&
                    !draftType &&
                    !isLink &&
                    !!ns &&
                    !!primaryNamespace &&
                    ns !== primaryNamespace &&
                    Object.keys(namespaceCounts).length > 1;
            if (isLink) {
                for (const e of allEdges) {
                    if (
                        e.from === row.identity &&
                        e.to &&
                        e.to !== row.identity
                    )
                        linkTargetSet.add(e.to);
                    const inst =
                        e.instance_type ||
                        (e.relationship === 'instance' ? e.path || '' : '');
                    if (inst === row.identity) {
                        if (e.from) linkTargetSet.add(e.from);
                        if (e.to) linkTargetSet.add(e.to);
                    }
                }
            }
            const linkTargets = Array.from(linkTargetSet),
                isSelfLink = isLink && linkTargets.length === 1,
                linkSummary = isSelfLink
                    ? nodeShortLabel(linkTargets[0]) +
                      ' ⇄ ' +
                      nodeShortLabel(linkTargets[0]) +
                      ' · ' +
                      tr('Self M:N')
                    : isLink && linkTargets.length >= 2
                      ? nodeShortLabel(linkTargets[0]) +
                        ' ⇄ ' +
                        nodeShortLabel(linkTargets[1]) +
                        ' · M:N'
                      : tr('Link table · M:N');
            visualKind = row.referenceOnly
                ? 'missing'
                : draftType
                  ? 'draft'
                  : isLink
                    ? 'instance'
                    : isSystem
                      ? 'system'
                      : isExternal
                        ? 'external'
                        : 'search_type';
            icon = row.referenceOnly
                ? 'warning'
                : draftType
                  ? 'edit'
                  : isLink
                    ? 'link'
                    : isSystem
                      ? 'dns'
                      : isExternal
                        ? 'folder'
                        : 'table-view';
            badgeText = row.referenceOnly
                ? 'REF'
                : draftType
                  ? tr('DRAFT')
                  : isSelfLink
                    ? 'SELF M:N'
                    : isLink
                      ? 'M:N'
                      : isSystem
                        ? ns === 'config'
                            ? 'CFG'
                            : 'SYS'
                        : isExternal
                          ? ns.toUpperCase().slice(0, 8)
                          : '';
            nodeColor =
                row.color ||
                meta.color ||
                (row.referenceOnly
                    ? ''
                    : draftType
                      ? '#c7923e'
                      : isLink
                        ? '#488599'
                        : isSystem
                          ? '#9a9248'
                          : isExternal
                            ? '#7a6fa8'
                            : '#568c63');
            let roleLabel = '';
            if (ui.showRoles) {
                if (draftType) roleLabel = tr('Draft ("skeleton") · not in DB');
                else if (pendingCreation) roleLabel = tr('New · many-to-many');
                else if (isLink) roleLabel = linkSummary;
                else {
                    const edges = model.edges || [],
                        isHierarchyChild = edges.some(
                            (e) =>
                                e.from === row.identity &&
                                e.type === 'hierarchy'
                        ),
                        isHierarchyParent = edges.some(
                            (e) =>
                                e.to === row.identity && e.type === 'hierarchy'
                        ),
                        isFrom = edges.some(
                            (e) =>
                                e.from === row.identity &&
                                !linkTableSet.has(e.from) &&
                                e.relationship !== 'instance'
                        ),
                        isTo = edges.some(
                            (e) =>
                                e.to === row.identity &&
                                e.relationship !== 'instance'
                        ),
                        isMany = edges.some(
                            (e) =>
                                (e.from === row.identity ||
                                    e.to === row.identity) &&
                                (e.relationship === 'instance' ||
                                    e.type === 'many_to_many' ||
                                    !!e.instance_type)
                        );
                    if (
                        (isHierarchyChild || isFrom) &&
                        (isHierarchyParent || isTo)
                    )
                        roleLabel = tr('Parent & Child');
                    else if (isHierarchyChild)
                        roleLabel = tr('Child · hierarchy');
                    else if (isHierarchyParent)
                        roleLabel = tr('Parent · hierarchy');
                    else if (isFrom) roleLabel = tr('Child / source (from)');
                    else if (isTo) roleLabel = tr('Parent / target (to)');
                    else roleLabel = tr('Search Type');
                    if (isMany) roleLabel += ' · M:N';
                }
            }
            const codeLabel = ui.showCodes
                ? row.identity +
                  (table && !String(row.identity).endsWith('/' + table)
                      ? ' (' + table + ')'
                      : '')
                : '';
            if (ui.showRoles && ui.showCodes) {
                subtitle = roleLabel;
                secondarySubtitle = codeLabel;
            } else if (ui.showRoles) {
                subtitle = roleLabel;
            } else if (ui.showCodes) {
                subtitle = codeLabel;
            } else if (draftType) {
                subtitle = tr('Draft ("skeleton") · not in DB');
            } else if (pendingCreation) {
                subtitle = tr('New · many-to-many');
            } else if (isLink) {
                subtitle = linkSummary;
            } else if (isSystem) {
                subtitle =
                    ns === 'config'
                        ? tr('Config table · config')
                        : tr('System table · sthpw');
            } else if (isExternal) {
                subtitle = tr('External · {ns}', { ns });
            } else {
                subtitle =
                    table &&
                    table.toLowerCase() !==
                        String(row.label || '').toLowerCase()
                        ? 'search_type · ' + table
                        : 'search_type';
            }
        }
        return {
            identity: row.identity,
            label: row.label || row.identity,
            nodeX: row.nodeX,
            nodeY: row.nodeY,
            color: nodeColor,
            kind: workflow
                ? row.kind === 'process'
                    ? 'manual'
                    : row.kind
                : linkTableSet.has(row.identity) || pendingCreation
                  ? 'instance'
                  : row.kind,
            visualKind,
            icon,
            badgeText,
            subtitle,
            secondarySubtitle,
            referenceOnly: !!row.referenceOnly,
            pendingCreation,
            draftType
        };
    });
    const nodeColorMap = {};
    for (const n of graphNodes) {
        nodeColorMap[n.identity] = n.color;
    }
    const graphEdges = (model.edges || []).map((row, index) => {
        let badgeLines = [],
            primaryMono = false,
            tooltip = '';
        if (!workflow) {
            const toMeta = searchTypeMap[row.to] || {},
                fromMeta = searchTypeMap[row.from] || {},
                toTable =
                    toMeta.table ||
                    String(row.to || '')
                        .split('/')
                        .pop(),
                fromTable =
                    fromMeta.table ||
                    String(row.from || '')
                        .split('/')
                        .pop(),
                rel = row.relationship || 'code',
                isVirtualInstance =
                    (rel === 'instance' || !!row.instance_type) &&
                    !row.from_col &&
                    !row.to_col,
                isInstance =
                    isVirtualInstance ||
                    rel === 'many_to_many' ||
                    row.type === 'many_to_many',
                linkTable =
                    row.instance_type ||
                    (rel === 'instance' ? row.path || '' : ''),
                fromCol =
                    row.from_col ||
                    (isVirtualInstance
                        ? ''
                        : rel === 'search_type'
                          ? 'search_code'
                          : toTable + '_' + rel),
                toCol =
                    row.to_col ||
                    (isVirtualInstance
                        ? ''
                        : rel === 'search_type'
                          ? 'code'
                          : rel),
                pathSuffix =
                    row.path && !isVirtualInstance ? ' (' + row.path + ')' : '',
                columnLine = isVirtualInstance
                    ? linkTable
                        ? tr('via {table}', {
                              table: ui.showCodes
                                  ? linkTable
                                  : linkTable.split('/').pop()
                          })
                        : 'M:N · instance'
                    : (ui.showCodes
                          ? fromTable +
                            '.' +
                            fromCol +
                            ' → ' +
                            toTable +
                            '.' +
                            toCol
                          : fromCol + ' → ' + toCol) +
                      (ui.showRoles ? '' : pathSuffix),
                sameDirCount = (model.edges || []).filter(
                    (e) => e.from === row.from && e.to === row.to
                ).length;
            let roleLine = '';
            if (row.type === 'hierarchy')
                roleLine = tr('Child → Parent · hierarchy');
            else if (isVirtualInstance)
                roleLine =
                    row.from === row.to
                        ? tr('Self M:N · instance')
                        : tr('M:N · instance');
            else if (linkTableSet.has(row.from) || isInstance)
                roleLine = tr('Link → Target · {rel}', { rel });
            else roleLine = tr('Child → Parent · {rel}', { rel });
            if (pathSuffix) roleLine += pathSuffix;
            if (ui.showRoles && roleLine) badgeLines.push(roleLine);
            if (ui.showColumns && columnLine) badgeLines.push(columnLine);
            if (!ui.showRoles && !ui.showColumns && ui.showCodes)
                badgeLines.push((row.from || '') + ' → ' + (row.to || ''));
            if (
                !badgeLines.length &&
                (sameDirCount > 1 || row.from === row.to)
            ) {
                badgeLines.push(
                    isVirtualInstance
                        ? linkTable
                            ? 'M:N · ' +
                              tr('via {table}', {
                                  table: linkTable.split('/').pop()
                              })
                            : roleLine
                        : columnLine
                );
            }
            primaryMono = badgeLines.length === 1 && !ui.showRoles;
            tooltip =
                (row.from || '') +
                ' → ' +
                (row.to || '') +
                ' · ' +
                roleLine +
                ' · ' +
                columnLine;
        }
        return {
            from: row.from,
            to: row.to,
            edgeIndex: index,
            relationship: row.relationship || '',
            from_attr: row.from_attr || '',
            to_attr: row.to_attr || '',
            label: workflow ? row.from_attr || '' : row.relationship || 'code',
            badgeLines,
            primaryMono,
            tooltip,
            color: row.color || nodeColorMap[row.from] || ''
        };
    });
    let canvasY = y,
        canvasH = h;
    if (
        !workflow &&
        ui.page === 'canvas' &&
        (!narrow || ui.panel === 'canvas') &&
        ui.showLegend
    ) {
        const legCols = graphWidth >= 760 ? 3 : 1,
            legPad = 12,
            legGap = 10,
            colW = Math.max(
                40,
                Math.floor(
                    (graphWidth - legPad * 2 - (legCols - 1) * legGap) / legCols
                )
            ),
            cellH = legCols === 3 ? 98 : 82,
            legH =
                legPad * 2 + (legCols === 3 ? cellH : cellH * 3 + legGap * 2),
            items = [
                [
                    'ports',
                    'arrow-forward',
                    tr('Ports & direction: from → to'),
                    tr(
                        '● Right port (Output / from): source table with foreign key (from_col) or Child in a hierarchy.\n○ Left port (Input / to): target table with key (to_col) or Parent in a hierarchy.'
                    )
                ],
                [
                    'roles',
                    'hierarchy',
                    tr('Parent / Child & M:N'),
                    tr(
                        '• Hierarchy (Child → Parent): child links to parent (e.g. Shot.scenes_code → Episode.code).\n• M:N (instance): connects two types via a Link table (instance_type).'
                    )
                ],
                [
                    'columns',
                    'code',
                    tr('Columns & colors'),
                    tr(
                        '• Direct key (code / id): maps source column from_col to target column to_col.\n• Line color matches the source (from) Search Type. Click any badge or line to edit.'
                    )
                ]
            ],
            legChildren = [];
        items.forEach(([key, iconName, titleText, bodyText], idx) => {
            const r = Math.floor(idx / legCols),
                c = idx % legCols,
                cx = legPad + c * (colW + legGap),
                cy = legPad + r * (cellH + legGap);
            legChildren.push(
                node(
                    'Box',
                    'adminSchemaLegendTile_' + key,
                    rect(cx, cy, colW, cellH),
                    {
                        background: 'surfaceContainerHigh',
                        border: 'outlineVariant',
                        radius: 8,
                        children: [
                            node(
                                'Icon',
                                'adminSchemaLegendIcon_' + key,
                                rect(10, 9, 16, 16),
                                {
                                    icon: iconName,
                                    color: 'action'
                                }
                            ),
                            label(
                                'adminSchemaLegendTitle_' + key,
                                rect(32, 7, Math.max(0, colW - 40), 20),
                                titleText,
                                {
                                    weight: 600
                                }
                            ),
                            label(
                                'adminSchemaLegendBody_' + key,
                                rect(
                                    10,
                                    30,
                                    Math.max(0, colW - 20),
                                    cellH - 36
                                ),
                                bodyText,
                                Object.assign(
                                    {
                                        wrap: true,
                                        fontRole: 'caption'
                                    },
                                    muted
                                )
                            )
                        ]
                    }
                )
            );
        });
        nodes.push(
            node('Box', 'adminSchemaLegendCard', rect(x, y, graphWidth, legH), {
                background: 'surfaceContainerLow',
                border: 'outlineVariant',
                radius: 10,
                children: legChildren
            })
        );
        canvasY = y + legH + 8;
        canvasH = Math.max(1, h - legH - 8);
    }
    nodes.push(
        node(
            'Graph',
            'adminGraphCanvas',
            rect(x, canvasY, graphWidth, canvasH),
            {
                toolbarRightInset: 46,
                visible:
                    ui.page === 'canvas' && (!narrow || ui.panel === 'canvas'),
                help: false,
                label: tr(workflow ? 'Workflow' : 'Project schema'),
                nodes: graphNodes,
                edges: graphEdges,
                selectedNode: model.selectedNode || '',
                selectedNodes: model.selectedNodes || [],
                selectedEdge: model.selectedEdge,
                contextMenu: model.mode || 'schema',
                readOnly: !edit,
                selectionEnabled: !model.busy,
                resetKey:
                    model.identity || 'draft:' + model.document.searchType,
                language,
                action: {
                    type: 'graph'
                }
            }
        )
    );
    if (!narrow || ui.panel === 'properties') {
        const w = narrow ? width : propertiesWidth,
            px = narrow ? 0 : width - w,
            children = [];
        if (narrow || ui.propertiesVisible) {
            const inner = inspector(model, ui, w - 24, language);
            children.push(
                node(
                    'Scroll',
                    'adminGraphPropertiesScroll',
                    rect(12, 52, w - 24, Math.max(0, h - 64)),
                    {
                        contentHeight: inner.height,
                        resetKey:
                            ui.inspector +
                            ':' +
                            ui.processPage +
                            ':' +
                            model.selectedNode +
                            ':' +
                            model.selectedEdge,
                        scrollbarId: 'adminGraphPropertiesScrollBar',
                        children: inner.nodes
                    }
                )
            );
        }
        if (!narrow)
            children.push(
                button(
                    'adminToggleGraphProperties',
                    rect(
                        ui.propertiesVisible ? w - 46 : (w - 34) / 2,
                        10,
                        34,
                        34
                    ),
                    tr(
                        ui.propertiesVisible
                            ? 'Hide properties'
                            : 'Show properties'
                    ),
                    ui.propertiesVisible ? 'chevron-right' : 'chevron-left',
                    {
                        type: 'propertiesVisible'
                    },
                    true,
                    {
                        iconOnly: true,
                        iconAction: true,
                        round: false
                    }
                )
            );
        if (narrow || ui.propertiesVisible) {
            children.push(
                label(
                    'adminGraphInspectorTitle',
                    rect(12, 10, Math.max(0, w - (narrow ? 104 : 148)), 34),
                    tr('Inspector'),
                    { weight: 600 }
                ),
                button(
                    'adminGraphAddNode',
                    rect(w - (narrow ? 46 : 86), 10, 34, 34),
                    tr(ui.inspector === 'add_node' ? 'Selection' : 'Add node'),
                    ui.inspector === 'add_node' ? 'tune' : 'add',
                    {
                        type: 'inspector',
                        value:
                            ui.inspector === 'add_node'
                                ? 'selection'
                                : 'add_node'
                    },
                    !model.busy,
                    { iconOnly: true, round: false }
                )
            );
            if (workflow && (model.selectedNode || model.selectedEdge >= 0)) {
                const selectedNode = (model.nodes || []).find(
                    (record) => record.identity === model.selectedNode
                );
                children.push(
                    button(
                        'adminRemoveGraphSelection',
                        rect(w - (narrow ? 94 : 138), 12, 38, 38),
                        tr('Remove from canvas'),
                        'delete',
                        { type: 'remove' },
                        edit && !(selectedNode && selectedNode.referenceOnly),
                        { iconOnly: true, destructive: true }
                    )
                );
            }
        }
        nodes.push(
            node('Box', 'adminGraphProperties', rect(px, y, w, h), {
                visible: ui.page === 'canvas',
                background: 'surfaceContainerLow',
                border: 'outlineVariant',
                children
            })
        );
        if (!narrow && ui.propertiesVisible)
            nodes.push(
                node(
                    'Splitter',
                    'adminGraphSplitHandle',
                    rect(px - 10, y, 10, h),
                    {
                        visible: ui.page === 'canvas',
                        text: tr('Properties panel width'),
                        value: w,
                        min: 240,
                        max: Math.min(640, width * 0.4),
                        reverse: true,
                        action: {
                            type: 'propertiesSplit'
                        }
                    }
                )
            );
    }
    if (ui.page === 'technical')
        nodes.push(
            node(
                'Area',
                'adminGraphXmlEditor',
                rect(
                    narrow ? 0 : x,
                    y,
                    width - (narrow ? 0 : x),
                    Math.max(1, h - 46)
                ),
                {
                    label: tr('Native XML'),
                    text: own(ui.text, 'xml') ? ui.text.xml : model.xml || '',
                    monospace: true,
                    readOnly: !edit,
                    action: {
                        type: 'buffer',
                        key: 'xml'
                    }
                }
            ),
            button(
                'adminGraphApplyXml',
                rect(
                    narrow ? 0 : x,
                    height - 38,
                    Math.min(240, width - (narrow ? 0 : x)),
                    38
                ),
                tr('Apply XML'),
                'check',
                {
                    type: 'apply',
                    key: 'xml'
                },
                edit && own(ui.text, 'xml')
            )
        );
    if (ui.page === 'canvas' && (!narrow || ui.panel === 'canvas')) {
        // Layout commands share the graph's unused toolbar space after zoom controls.
        const toolbarX = x + 230,
            available = graphWidth - 230;
        if (available > 130) {
            nodes.push(
                node(
                    'Choice',
                    'adminGraphLayoutStyle',
                    rect(toolbarX, canvasY, Math.max(80, available - 46), 38),
                    {
                        label: tr('Automatic layout'),
                        options: [
                            {
                                value: 'flow',
                                label: tr('Directed flow')
                            },
                            {
                                value: 'network',
                                label: tr('Network clusters')
                            },
                            {
                                value: 'grid',
                                label: tr('Alphabetical grid')
                            }
                        ],
                        value: ui.arrange,
                        action: {
                            type: 'arrange'
                        },
                        enabled: edit
                    }
                ),
                button(
                    'adminArrangeGraph',
                    rect(x + graphWidth - 38, canvasY, 38, 38),
                    tr('Arrange nodes'),
                    'hierarchy',
                    {
                        type: 'layout'
                    },
                    edit && (model.nodes || []).length > 0,
                    {
                        iconOnly: true
                    }
                )
            );
        } else
            nodes.push(
                button(
                    'adminArrangeGraph',
                    rect(x + graphWidth - 38, canvasY, 38, 38),
                    tr('Arrange nodes'),
                    'hierarchy',
                    {
                        type: 'layout'
                    },
                    edit && (model.nodes || []).length > 0,
                    {
                        iconOnly: true
                    }
                )
            );
    }
    return {
        nodes
    };
}
