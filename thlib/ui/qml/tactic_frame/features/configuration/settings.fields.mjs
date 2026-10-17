// Field captions and operations from the original Handler Configuration pages (EPL-1.0).
export const definitions = {
    server: [
        {
            kind: 'Heading',
            id: 'serverSection0',
            title: 'Connection',
            description:
                'Server endpoint, active preset and current sign-in status.'
        },
        {
            kind: 'Field',
            field: 'serverUrl',
            title: 'Server address',
            description:
                'TACTIC HTTP endpoint used by the active server preset and connection test.',
            nativeOnly: true
        },
        {
            kind: 'Choice',
            field: 'presetName',
            title: 'Server preset',
            description:
                'Select a saved endpoint and its account and routing configuration.',
            nativeOnly: true
        },
        {
            kind: 'Choice',
            field: 'rpcTransport',
            title: 'API transport',
            description:
                'XML-RPC supports Legacy TACTIC and TACTIC Stream. JSON requires TACTIC Stream. Saved separately for each preset; applying reconnects.',
            nativeOnly: true,
            options: [
                {
                    value: 'xmlrpc',
                    label: 'XML-RPC'
                },
                {
                    value: 'json',
                    label: 'JSON (TACTIC Stream)'
                }
            ]
        },
        {
            kind: 'Choice',
            field: 'queryMode',
            title: 'Query execution',
            description:
                'Local mode needs no server installation. Plugin mode installs or updates the server package on first use with an administrator ticket.',
            nativeOnly: true,
            options: [
                {
                    value: 'local',
                    label: 'Local'
                },
                {
                    value: 'plugin',
                    label: 'Server plugin'
                }
            ]
        },
        {
            kind: 'Heading',
            id: 'serverSection5',
            title: 'Background checks',
            description:
                'Committed changes are coalesced by one server worker. Only subscribed data is refreshed; presence and authentication keep their own heartbeat.'
        },
        {
            kind: 'Choice',
            field: 'serverUpdateMode',
            title: 'Update delivery',
            description:
                'Server push (SSE) uses the TACTIC Stream collector and refreshes only subscribed data. Other servers require periodic checks.',
            nativeOnly: true,
            options: [
                {
                    value: 'poll',
                    label: 'Periodic checks'
                },
                {
                    value: 'sse',
                    label: 'Server push (SSE)'
                }
            ]
        },
        {
            kind: 'Choice',
            field: 'serverUpdateBatchDelay',
            title: 'Update batching delay',
            description:
                'Combine arriving changes before reading data. A longer delay reduces requests during bursts; it also delays visible updates.',
            nativeOnly: true,
            options: [
                {
                    value: 100,
                    label: '100 ms'
                },
                {
                    value: 200,
                    label: '200 ms'
                },
                {
                    value: 500,
                    label: '500 ms'
                },
                {
                    value: 1000,
                    label: '1000 ms'
                }
            ]
        },
        {
            kind: 'Choice',
            field: 'serverUpdateInterval',
            title: 'Server updates',
            description:
                'Interval for the shared request, including the connection check and presence heartbeat.',
            nativeOnly: true,
            options: [
                {
                    value: 5,
                    label: 'Every 5 seconds'
                },
                {
                    value: 10,
                    label: 'Every 10 seconds'
                },
                {
                    value: 30,
                    label: 'Every 30 seconds'
                },
                {
                    value: 60,
                    label: 'Every 60 seconds'
                }
            ]
        },
        {
            kind: 'Heading',
            id: 'serverSection9',
            title: 'Application updates',
            description:
                'Check ZIP snapshots on this TACTIC sObject at startup and once a day.'
        },
        {
            kind: 'Field',
            field: 'updateSearchKey',
            title: 'Update sObject search key',
            description:
                'Leave empty to disable automatic checks. Publish release ZIPs as snapshots of this object.',
            nativeOnly: true
        }
    ],
    global: [
        {
            kind: 'Heading',
            id: 'globalSection0',
            title: 'Application window',
            description: 'Choose what happens when the main window is closed.'
        },
        {
            kind: 'Switch',
            field: 'closeToTray',
            title: 'Close to system tray',
            description:
                'Keep TACTIC Handler running in the system tray when the main window close button is pressed. Disable this to exit completely.',
            nativeOnly: true
        },
        {
            kind: 'Heading',
            id: 'globalSection2',
            title: 'DCC connections',
            description: 'Control the local server used by DCC clients.'
        },
        {
            kind: 'Switch',
            field: 'autoStartHandlerServer',
            title: 'Start Handler Server automatically',
            description:
                'Launch the local DCC server when TACTIC Handler starts. Disable this if you only use the standalone app; manual start remains available. Takes effect next launch.',
            nativeOnly: true
        },
        {
            kind: 'Heading',
            id: 'globalSection4',
            title: 'Notifications',
            description:
                'Choose which background updates appear as pop-up notifications.'
        },
        {
            kind: 'Switch',
            field: 'activityNotifications',
            title: 'Activity feed notifications',
            description:
                'Show a bottom-right notification when another user creates a new activity event. This setting applies immediately.'
        },
        {
            kind: 'Switch',
            field: 'messageNotifications',
            title: 'Message notifications',
            description:
                'Show a bottom-right notification for new messages when their conversation is not open. This setting applies immediately.'
        },
        {
            kind: 'Heading',
            id: 'globalSection7',
            title: 'Background workers',
            description:
                'Limit parallel server requests and local background work.'
        },
        {
            kind: 'Number',
            field: 'serverThreads',
            title: 'TACTIC request threads',
            description:
                'Maximum simultaneous XMLRPC requests. Repository Sync sends this many different chunks at once.',
            nativeOnly: true,
            min: 1,
            max: 32,
            step: 1
        },
        {
            kind: 'Number',
            field: 'localThreads',
            title: 'Local worker threads',
            description:
                'Maximum simultaneous local background operations. This does not change the Repository Sync download limit.',
            nativeOnly: true,
            min: 1,
            max: 32,
            step: 1
        },
        {
            kind: 'Heading',
            id: 'globalSection10',
            title: 'Diagnostics',
            description:
                'Choose which event types are written to the diagnostic log.'
        },
        {
            kind: 'Heading',
            id: 'globalSection11',
            title: 'Configuration location',
            description:
                'Location used by the shared TACTIC Handler configuration API.'
        },
        {
            kind: 'Field',
            field: 'configPath',
            title: 'Active configuration root',
            description:
                'This path is managed by the application environment and is shown here for diagnostics.',
            nativeOnly: true,
            readOnly: true
        }
    ],
    cache: [
        {
            kind: 'Heading',
            id: 'cacheSection0',
            title: 'Workspace cache',
            description:
                'Control saved Search Tab layout separately from cached server records.'
        },
        {
            kind: 'Switch',
            field: 'cacheProcessTabs',
            title: 'Cache process tabs',
            description:
                'Restore search process tabs from the persistent cache instead of rebuilding every tab during startup.'
        },
        {
            kind: 'Button',
            field: 'clearTabs',
            title: 'Clear tabs cache',
            description:
                'Discard cached search tabs and rebuild them from current project data on the next load.',
            action: {
                type: 'clearTabs'
            }
        },
        {
            kind: 'Heading',
            id: 'cacheSection3',
            title: 'Cached server data',
            description:
                'Choose which unchanged TACTIC data may be restored locally. Refresh actions always bypass these caches.'
        },
        {
            kind: 'Switch',
            field: 'reference',
            title: 'Projects and reference data',
            description:
                'Projects, Search Types, pipelines, processes, statuses, users, groups and tags.',
            nativeOnly: true
        },
        {
            kind: 'Switch',
            field: 'search',
            title: 'Search results and sObjects',
            description:
                'Ordered search pages and unchanged object fields used by Search Tabs.',
            nativeOnly: true
        },
        {
            kind: 'Switch',
            field: 'snapshots',
            title: 'Snapshots and files',
            description:
                'Snapshot and file metadata. Repository files remain managed by Repository Sync.',
            nativeOnly: true
        },
        {
            kind: 'Switch',
            field: 'relations',
            title: 'Children and relations',
            description:
                'Expanded child branches and linked-object membership.',
            nativeOnly: true
        },
        {
            kind: 'Switch',
            field: 'tasks',
            title: 'Tasks',
            description: 'Task Manager scopes, pages and task metadata.',
            nativeOnly: true
        },
        {
            kind: 'Switch',
            field: 'notes',
            title: 'Notes',
            description:
                'Object and process note histories with attachment metadata.',
            nativeOnly: true
        },
        {
            kind: 'Switch',
            field: 'messages',
            title: 'Messages',
            description:
                'A bounded set of recent conversation histories and attachment metadata.',
            nativeOnly: true
        },
        {
            kind: 'Switch',
            field: 'activity',
            title: 'Activity Feed',
            description:
                'Recent activity pages and complete calendar day counts.',
            nativeOnly: true
        },
        {
            kind: 'Switch',
            field: 'work_hours',
            title: 'Work hours',
            description:
                'Timesheet and report query results for previously opened ranges.',
            nativeOnly: true
        },
        {
            kind: 'Heading',
            id: 'cacheSection13',
            title: 'Cache maintenance',
            description:
                'Clearing raises the cache generation first, so an older background request cannot restore cleared data.'
        },
        {
            kind: 'Button',
            field: 'clearData',
            title: 'Clear all cached server data',
            description:
                'Search tabs will keep their layout, but server records will be loaded again when needed.',
            action: {
                type: 'clearData'
            }
        }
    ],
    appearance: [
        {
            kind: 'Heading',
            id: 'appearanceSection0',
            title: 'Appearance',
            description:
                'Choose the interface style, color mode, palettes, and semantic icon set.'
        },
        {
            kind: 'Switch',
            field: 'darkTheme',
            title: 'Dark color mode',
            description:
                'Use dark surfaces and the dark palette assigned to the selected interface style.'
        },
        {
            kind: 'Choice',
            field: 'themeStyle',
            title: 'Interface style',
            description: ''
        },
        {
            kind: 'View',
            field: 'lightAccent',
            title: 'Light mode palette',
            description:
                'Base surface and accent used when the application is in light mode.',
            props: {
                view: 'lightAccent'
            },
            height: 79
        },
        {
            kind: 'View',
            field: 'darkAccent',
            title: 'Dark mode palette',
            description:
                'Base surface and accent used when the application is in dark mode.',
            props: {
                view: 'darkAccent'
            },
            height: 79
        },
        {
            kind: 'Choice',
            field: 'iconSet',
            title: 'Icon set',
            description: ''
        },
        {
            kind: 'Switch',
            field: 'clickAnimations',
            title: 'Click animations',
            description:
                'Animate press feedback, ripples, switches, and disclosure controls.'
        },
        {
            kind: 'Switch',
            field: 'hoverAnimations',
            title: 'Hover animations',
            description:
                'Animate pointer hover feedback while keeping the same hover states available instantly when disabled.'
        },
        {
            kind: 'Switch',
            field: 'fadeAnimations',
            title: 'Fades and transitions',
            description:
                'Animate appearing content, view transitions, expansion, and other interface fades.'
        },
        {
            kind: 'Switch',
            field: 'popupAnimations',
            title: 'Menu and popup animations',
            description:
                'Animate opening and closing menus, dropdowns, popups, and tooltips. Disable for instant appearance and dismissal.'
        },
        {
            kind: 'Heading',
            id: 'appearanceSection10',
            title: 'Language',
            description:
                'Choose the language used by the application interface.'
        },
        {
            kind: 'Choice',
            field: 'language',
            title: 'Interface language',
            description:
                'Changes application labels and help text while project-defined names remain unchanged.'
        },
        {
            kind: 'Heading',
            id: 'appearanceSection12',
            title: 'Rendering',
            description:
                'Choose how Qt Quick draws and presents the interface. Changes take effect after restarting TACTIC Handler.'
        },
        {
            kind: 'Choice',
            field: 'renderBackend',
            title: 'Graphics backend',
            description: '',
            nativeOnly: true,
            options: [
                {
                    value: 'automatic',
                    label: 'Automatic (recommended)',
                    description:
                        'Uses the stable OpenGL backend on Windows and the native Qt default on other systems.'
                },
                {
                    value: 'opengl',
                    label: 'OpenGL',
                    description:
                        'GPU rendering without the Windows DXGI/MPO presentation path that can cause full-display flicker.'
                },
                {
                    value: 'd3d11',
                    label: 'Direct3D 11',
                    description:
                        'Native Windows backend. On some MPO or HDR configurations it can make the whole display flicker during UI updates.'
                },
                {
                    value: 'd3d12',
                    label: 'Direct3D 12',
                    description:
                        'Modern native Windows backend. Requires compatible graphics drivers.'
                },
                {
                    value: 'vulkan',
                    label: 'Vulkan',
                    description:
                        'Cross-platform GPU backend. Requires a working Vulkan driver.'
                },
                {
                    value: 'software',
                    label: 'Software',
                    description:
                        'CPU rendering for troubleshooting. It avoids graphics-driver issues but is noticeably slower.'
                }
            ]
        }
    ],
    tasks: [
        {
            kind: 'Heading',
            id: 'tasksSection0',
            title: 'Task workspace defaults',
            description:
                'Initial task surface, presentation, ordering and grouping.'
        },
        {
            kind: 'Choice',
            field: 'workspaceSurface',
            title: 'Initial task surface',
            description: 'Open Quick Tasks or the detailed Task Browser first.',
            options: [
                {
                    value: 'quick',
                    label: 'Quick Tasks'
                },
                {
                    value: 'browser',
                    label: 'Task Browser'
                }
            ]
        },
        {
            kind: 'Choice',
            field: 'quickViewMode',
            title: 'Quick Tasks presentation',
            description: 'Show editable process cards or a compact task list.',
            options: [
                {
                    value: 'cards',
                    label: 'Cards'
                },
                {
                    value: 'compact',
                    label: 'Compact list'
                }
            ]
        },
        {
            kind: 'Choice',
            field: 'viewMode',
            title: 'Initial view',
            description:
                'View opened first when Task Browser has no saved local state.',
            options: [
                {
                    value: 'list',
                    label: 'Table'
                },
                {
                    value: 'gantt',
                    label: 'Gantt'
                }
            ]
        },
        {
            kind: 'Choice',
            field: 'sortMode',
            title: 'Initial sorting',
            description:
                'Default order used before the user applies a table or column sort.',
            options: [
                {
                    value: 'due',
                    label: 'Deadline'
                },
                {
                    value: 'recent',
                    label: 'Recently changed'
                },
                {
                    value: 'process',
                    label: 'Process'
                },
                {
                    value: 'user',
                    label: 'Assignee'
                },
                {
                    value: 'status',
                    label: 'Status'
                },
                {
                    value: 'object',
                    label: 'Parent object'
                },
                {
                    value: 'priority',
                    label: 'Priority'
                },
                {
                    value: 'milestone',
                    label: 'Milestone'
                },
                {
                    value: 'supervisor',
                    label: 'Supervisor'
                }
            ]
        },
        {
            kind: 'Choice',
            field: 'groupMode',
            title: 'Initial grouping',
            description:
                'Default group structure used when Task Browser is opened.',
            options: [
                {
                    value: 'process',
                    label: 'By Process'
                },
                {
                    value: 'status',
                    label: 'By Status'
                },
                {
                    value: 'user',
                    label: 'By Assignee'
                },
                {
                    value: 'object',
                    label: 'By Parent Object'
                },
                {
                    value: 'project',
                    label: 'By Project'
                },
                {
                    value: 'search_type',
                    label: 'By Search Type'
                },
                {
                    value: 'none',
                    label: 'No Groups'
                }
            ]
        },
        {
            kind: 'Switch',
            field: 'inspectorExpanded',
            title: 'Task Inspector expanded',
            description:
                'Open Task Inspector in its expanded state when no saved dock state exists.'
        },
        {
            kind: 'Heading',
            id: 'tasksSection7',
            title: 'Task table columns',
            description:
                'Choose visible columns, their width and display order. Object remains visible.'
        }
    ],
    checkin: [
        {
            kind: 'Heading',
            id: 'checkinSection0',
            title: 'Search results',
            description:
                'Choose how result items are loaded and initially presented.'
        },
        {
            kind: 'Switch',
            field: 'previewsThroughHttp',
            title: 'Preview delivery',
            description: '',
            nativeOnly: true
        },
        {
            kind: 'Switch',
            field: 'showBuiltinProcesses',
            title: 'Built-in processes',
            description:
                'Include TACTIC built-in processes together with project-defined processes in result items.',
            nativeOnly: true
        },
        {
            kind: 'Number',
            field: 'displayLimit',
            title: 'Result limit',
            description:
                'Maximum number of sObjects requested for one search result page.',
            min: 20,
            max: 5000,
            step: 5
        },
        {
            kind: 'Choice',
            field: 'loadingMode',
            title: 'Loading mode',
            description:
                'Use explicit result pages or load the next page when scrolling reaches the end.',
            options: [
                {
                    value: 'pages',
                    label: 'Pages'
                },
                {
                    value: 'infinite',
                    label: 'Continuous'
                }
            ]
        },
        {
            kind: 'Choice',
            field: 'defaultViewMode',
            title: 'Default result view',
            description:
                'Initial presentation used when a search tab has no saved view state.',
            options: [
                {
                    value: 0,
                    label: 'Continuous'
                },
                {
                    value: 1,
                    label: 'Cards'
                }
            ]
        },
        {
            kind: 'Heading',
            id: 'checkinSection6',
            title: 'Item interactions',
            description:
                'Define the actions performed by double-click gestures on result items.'
        },
        {
            kind: 'Switch',
            field: 'doubleClickSave',
            title: 'Double-click to save',
            description:
                'A regular double-click downloads or saves the selected snapshot using the configured checkout behaviour.',
            nativeOnly: true
        },
        {
            kind: 'Switch',
            field: 'doubleClickOpen',
            title: 'Shift + double-click to open',
            description:
                'Holding Shift while double-clicking opens the selected file in its associated application.',
            nativeOnly: true
        },
        {
            kind: 'Heading',
            id: 'checkinSection9',
            title: 'Versions and descriptions',
            description:
                'Control version placement and the amount of descriptive text shown on result items.'
        },
        {
            kind: 'Switch',
            field: 'versionsSeparate',
            title: 'Separate versions',
            description:
                'Display snapshot versions in a dedicated area instead of mixing them with the main item content.',
            nativeOnly: true
        },
        {
            kind: 'Choice',
            field: 'versionsPosition',
            title: 'Versions position',
            description:
                'Choose where the separate version area appears relative to the result item.',
            nativeOnly: true,
            options: [
                {
                    value: 0,
                    label: 'Right'
                },
                {
                    value: 1,
                    label: 'Bottom'
                }
            ]
        },
        {
            kind: 'Switch',
            field: 'descriptionLimitEnabled',
            title: 'Description length',
            description:
                'Limit long sObject descriptions in results. Disable the switch to show the complete text.',
            nativeOnly: true
        },
        {
            kind: 'Heading',
            id: 'checkinSection13',
            title: 'Snapshot Browser defaults',
            description:
                'Choose the initial content and layout used by Snapshot Browser.'
        },
        {
            kind: 'Switch',
            field: 'snapshotShowAll',
            title: 'Show every snapshot',
            description:
                'Include snapshots from every process instead of only the selected process.',
            nativeOnly: true
        },
        {
            kind: 'Switch',
            field: 'snapshotShowMore',
            title: 'Show more metadata',
            description: 'Expand the additional snapshot metadata by default.',
            nativeOnly: true
        },
        {
            kind: 'Choice',
            field: 'snapshotContentMode',
            title: 'Initial content',
            description:
                'Show preview and files together, preview only, or files only.',
            nativeOnly: true,
            options: [
                {
                    value: 'both',
                    label: 'Preview and files'
                },
                {
                    value: 'preview',
                    label: 'Preview only'
                },
                {
                    value: 'files',
                    label: 'Files only'
                }
            ]
        },
        {
            kind: 'Choice',
            field: 'snapshotImageMode',
            title: 'Preview scaling',
            description:
                'Fit shows the whole image; Fill covers all available space and crops the edges.',
            nativeOnly: true,
            options: [
                {
                    value: 'fit',
                    label: 'Fit'
                },
                {
                    value: 'fill',
                    label: 'Fill'
                }
            ]
        },
        {
            kind: 'Choice',
            field: 'snapshotOrientation',
            title: 'Initial orientation',
            description:
                'Arrange preview and file content side by side or from top to bottom.',
            nativeOnly: true,
            options: [
                {
                    value: 'horizontal',
                    label: 'Horizontal'
                },
                {
                    value: 'vertical',
                    label: 'Vertical'
                }
            ]
        },
        {
            kind: 'Heading',
            id: 'checkinSection19',
            title: 'File transfer',
            description:
                'Choose how files move between TACTIC and the workstation.'
        },
        {
            kind: 'Choice',
            field: 'checkinMethod',
            title: 'Check-in method',
            description: '',
            nativeOnly: true,
            options: [
                {
                    value: 0,
                    label: 'Preallocate'
                },
                {
                    value: 1,
                    label: 'In-Place'
                },
                {
                    value: 2,
                    label: 'Copy'
                },
                {
                    value: 3,
                    label: 'Move'
                },
                {
                    value: 4,
                    label: 'Upload'
                }
            ]
        },
        {
            kind: 'Choice',
            field: 'checkoutMethod',
            title: 'Check-out method',
            description: '',
            nativeOnly: true,
            options: [
                {
                    value: 0,
                    label: 'Local'
                },
                {
                    value: 1,
                    label: 'HTTP'
                }
            ]
        },
        {
            kind: 'Heading',
            id: 'checkinSection22',
            title: 'Snapshot creation',
            description:
                'Defaults applied while preparing new snapshots and DCC output files.'
        },
        {
            kind: 'Switch',
            field: 'updateVersionless',
            title: 'Update versionless snapshot',
            description:
                'Refresh the versionless snapshot whenever a new numbered version is checked in.',
            nativeOnly: true
        },
        {
            kind: 'Choice',
            field: 'versionlessMode',
            title: 'Local versionless files',
            description:
                'Copy is the default. Links point to the numbered version, including previews. Symbolic links on Windows need Developer Mode or privileges; hard links need the same volume. Versionless-only check-ins use copies. Remote server aliases follow its own configuration.',
            nativeOnly: true,
            options: [
                {
                    value: 0,
                    label: 'Copy'
                },
                {
                    value: 1,
                    label: 'Symbolic link'
                },
                {
                    value: 2,
                    label: 'Hard link'
                }
            ]
        },
        {
            kind: 'Switch',
            field: 'generatePreviews',
            title: 'Generate previews',
            description:
                'Create supported thumbnail and preview files as part of the check-in preparation.'
        },
        {
            kind: 'Switch',
            field: 'commitQueueAutoClean',
            title: 'Clean completed Commit Queue items',
            description:
                'Remove successful operations from Commit Queue automatically.'
        },
        {
            kind: 'Switch',
            field: 'confirmSaving',
            title: 'Confirm saving',
            description:
                'Ask for confirmation before saving a prepared check-in operation.',
            nativeOnly: true
        },
        {
            kind: 'Switch',
            field: 'confirmRevision',
            title: 'Confirm revision saving',
            description:
                'Ask separately before saving a revision instead of a new version.'
        },
        {
            kind: 'Switch',
            field: 'sequencePaddingEnabled',
            title: 'Sequence padding',
            description:
                'Enable a fixed number of digits when sequence frame numbers are generated.',
            nativeOnly: true
        },
        {
            kind: 'Heading',
            id: 'checkinSection30',
            title: 'Repository synchronization',
            description:
                'Control repository discovery, validation, and completed transfer cleanup.'
        },
        {
            kind: 'Switch',
            field: 'verifyRepositoryMd5',
            title: 'Verify files with MD5',
            description:
                'Compare checksums to detect changed local files. Enable only when stronger validation is worth the additional CPU work.',
            nativeOnly: true
        },
        {
            kind: 'Switch',
            field: 'autoCleanRepositorySync',
            title: 'Clean completed downloads',
            description:
                'Remove completed Repository Sync rows automatically after each successful download batch.',
            nativeOnly: true
        },
        {
            kind: 'Choice',
            field: 'repositorySyncScopeMode',
            title: 'Discovery mode',
            description:
                'Full scope discovers every file before downloading; partial scope overlaps discovery and transfer in chunks.',
            nativeOnly: true,
            options: [
                {
                    value: 0,
                    label: 'Full scope'
                },
                {
                    value: 1,
                    label: 'Partial scope'
                }
            ]
        },
        {
            kind: 'Number',
            field: 'repositorySyncPartialChunkSize',
            title: 'Partial scope chunk size',
            description:
                'Number of repository records discovered per chunk while partial scope mode is active.',
            nativeOnly: true,
            min: 1,
            max: 250,
            step: 1
        },
        {
            kind: 'Heading',
            id: 'checkinSection35',
            title: 'Drop Plate completion',
            description:
                'Choose what happens to Drop Plate state after a successful check-in.'
        },
        {
            kind: 'Switch',
            field: 'syncDropPlate',
            title: 'Share Drop Plate across tabs',
            description:
                'Use one Drop Plate selection for every compatible search tab.',
            nativeOnly: true
        },
        {
            kind: 'Switch',
            field: 'uncheckDropPlate',
            title: 'Uncheck submitted files',
            description:
                'Keep submitted files in Drop Plate but clear their checked state after check-in.',
            nativeOnly: true
        },
        {
            kind: 'Switch',
            field: 'clearDropPlate',
            title: 'Clear submitted files',
            description:
                'Remove successfully submitted files from Drop Plate after check-in.',
            nativeOnly: true
        },
        {
            kind: 'Heading',
            id: 'checkinSection39',
            title: 'File matching and naming',
            description:
                'Define how dropped directories, sequences, UDIM sets, and snapshot filenames are recognized.'
        },
        {
            kind: 'Switch',
            field: 'groupCheckin',
            title: 'Group selected files',
            description:
                'Combine the selected files into one snapshot instead of preparing a snapshot for each file.'
        },
        {
            kind: 'Switch',
            field: 'keepFilename',
            title: 'Keep original filename',
            description:
                'Preserve source filenames instead of applying the active naming template.'
        },
        {
            kind: 'Switch',
            field: 'includeSubfolders',
            title: 'Include subfolders',
            description:
                'Scan nested folders when a directory is added to Drop Plate.',
            nativeOnly: true
        },
        {
            kind: 'Switch',
            field: 'allowSingleUdim',
            title: 'Allow a single UDIM or UV tile',
            description:
                'Recognize one matching tile as a valid UDIM or UV set instead of requiring multiple tiles.',
            nativeOnly: true
        },
        {
            kind: 'Switch',
            field: 'allowSingleFrame',
            title: 'Allow a single-frame sequence',
            description:
                'Recognize one numbered file as a sequence when its padding matches the configured rules.',
            nativeOnly: true
        },
        {
            kind: 'Number',
            field: 'minimumFramePadding',
            title: 'Minimum frame padding',
            description:
                'Smallest number of frame digits accepted by automatic sequence detection.',
            nativeOnly: true,
            min: 1,
            max: 9,
            step: 1
        },
        {
            kind: 'Button',
            field: 'matchingTemplates',
            title: 'Matching templates',
            description:
                'Edit the templates used to associate dropped files with check-in contexts.',
            nativeOnly: true,
            action: {
                type: 'matchingTemplates'
            }
        }
    ]
};
