import {node} from '../../../core/frame.mjs';
import {rect,label,muted,notices,toolbar as documentToolbar,policy,sectionSelector} from '../admin.document.mjs';
import {form} from '../admin.form.mjs';
import {translate} from '../admin.strings.mjs';
import * as Process from './process.ui.mjs';
const button=(id,bounds,text,icon,action,enabled,extra)=>node('Button',id,bounds,Object.assign({text,icon,action,enabled},extra||{}));
const own=(object,key)=>Object.prototype.hasOwnProperty.call(object,key);
export function toolbar(model,ui,width,language){
  const result=documentToolbar(model,ui,width,language),tr=text=>translate(text,language);
  result.nodes=result.nodes.filter(row=>row.id!=='adminDocumentStatus');
  result.nodes.push(button(model.mode==='workflow'?'adminCreateDocument':'adminCreateSchemaType',rect(46,0,38,38),tr(model.mode==='workflow'?'Create workflow':'New Search Type'),'add',{type:model.mode==='workflow'?'createWorkflow':'createType',searchType:model.document.searchType||model.creationSearchType},!model.busy&&!model.uncertain&&(model.canWrite||model.metadata.canCreate)&&(!model.dirty||model.mode!=='workflow')&&(model.mode!=='workflow'||!!(model.document.searchType||model.creationSearchType)),{iconOnly:true}));return result;
}
export function records(model,ui,language){
  const tr=text=>translate(text,language),groups={},query=ui.query.trim().toLowerCase();
  for(const row of model.catalog||[]){if(!query||(row.label+' '+row.identity+' '+row.searchType).toLowerCase().includes(query))(groups[row.searchType||'']||(groups[row.searchType||'']=[])).push(row);}
  groups['sthpw/task']=groups['sthpw/task']||[];
  if(model.ready&&!model.identity)groups[model.document.searchType||'']=groups[model.document.searchType||'']||[];
  const keys=Object.keys(groups).sort((a,b)=>a==='sthpw/task'?1:b==='sthpw/task'?-1:a.localeCompare(b)),out=[];
  for(const key of keys){const info=(model.metadata.searchTypes||[]).find(row=>row.identity===key)||{};
    out.push({identity:'group:'+key,group:true,searchType:key,label:key==='sthpw/task'?tr('Task status workflows'):info.label||key||tr('No Search Type')});
    if(ui.collapsed.indexOf(key)<0||!model.identity&&model.document.searchType===key){
      if(model.ready&&!model.identity&&model.document.searchType===key)out.push({identity:'',label:tr('New workflow'),searchType:key});
      out.push.apply(out,groups[key].slice().sort((a,b)=>(a.label||a.identity).localeCompare(b.label||b.identity)));
    }
  }
  return out;
}
export function row(list,record,model,ui,language){
  const width=list.width-16,tr=text=>translate(text,language);
  if(list.source==='graphPipelines'){
    if(record.group)return {nodes:[button('workflowGroup_'+record.searchType,rect(0,0,width-42,38),record.label,ui.collapsed.indexOf(record.searchType)>=0?'chevron-right':'chevron-down',{type:'collapse',identity:record.searchType},!model.busy),button('workflowCreate_'+record.searchType,rect(width-38,0,38,38),tr('Create workflow'),'add',{type:'createWorkflow',searchType:record.searchType},!model.busy&&!model.dirty&&!model.uncertain&&(model.canWrite||model.metadata.canCreate),{iconOnly:true})]};
    return {nodes:[node('Action','workflowPipeline_'+record.identity,rect(0,0,width,38),{text:record.label||record.identity,selected:model.identity===record.identity,normalColor:'surfaceContainerHigh',selectedColor:'contentSelection',enabled:!model.busy&&!model.uncertain,children:[label('workflowPipelineTitle_'+record.identity,rect(10,0,width-20,38),record.label||record.identity)],action:{type:'selectPipeline',identity:record.identity}})]};
  }
  if(list.source==='graphTypes')return {nodes:[node('Action','graphType_'+record.identity,rect(0,0,width,62),{text:record.label||record.identity,selected:ui.typeToAdd===record.identity,normalColor:'surfaceContainerHigh',selectedColor:'contentSelection',enabled:!model.busy,children:[label('graphTypeTitle_'+record.identity,rect(10,4,width-20,26),record.label||record.identity,{weight:600}),label('graphTypeIdentity_'+record.identity,rect(10,32,width-20,22),record.identity,muted)],action:{type:'typeToAdd',value:record.identity}})]};
  if(list.source==='graphSelection')return {nodes:[node('CheckBox','graphSelect_'+record.identity,rect(0,0,width,38),{text:record.label||record.identity,checked:model.selectedNodes.indexOf(record.identity)>=0,enabled:!model.busy,action:{type:'selectNodes',identities:model.selectedNodes.indexOf(record.identity)>=0?model.selectedNodes.filter(value=>value!==record.identity):model.selectedNodes.concat([record.identity]),primary:record.identity}})]};
  return {nodes:[]};
}
export function models(model,ui,language){const query=ui.typeQuery.trim().toLowerCase();return {graphPipelines:records(model,ui,language),graphTypes:(model.metadata.searchTypes||[]).filter(row=>(row.label+' '+row.identity).toLowerCase().includes(query)),graphSelection:model.nodes||[]};}
export function inspector(model,ui,width,language){
  const tr=text=>translate(text,language),nodes=[],edit=policy(model).editable&&!ui.confirmation,w=width-24;
  const current=(model.nodes||[]).find(row=>row.identity===model.selectedNode),edge=(model.edges||[])[model.selectedEdge],readonly=!!(current&&current.referenceOnly);
  let y=0;
  function addForm(fields,enabled){const body=form(fields,w,language,enabled===undefined?edit:enabled);nodes.push(node('Box','graphInspectorForm_'+y,rect(0,y,w,body.height),{children:body.nodes}));y+=body.height+8;}
  function action(id,text,icon,event,enabled){nodes.push(button(id,rect(0,y,w,38),tr(text),icon,event,enabled===undefined?edit:enabled));y+=46;}
  function heading(id,text,description){addForm([{kind:'Heading',id,title:text,description}],false);}
  function editor(key,title,source,description){heading('graph_'+key+'Heading',title,description);nodes.push(node('Area','graph_'+key+'Editor',rect(0,y,w,220),{label:tr(title),text:own(ui.text,key)?ui.text[key]:source||'',monospace:true,readOnly:!edit||readonly,action:{type:'buffer',key}}));y+=228;action('graphApply_'+key,'Apply','check',{type:'apply',key},edit&&!readonly&&own(ui.text,key));}
  nodes.push(sectionSelector('adminGraphInspectorPages',[{value:'selection',label:tr('Selection'),icon:'tune'},{value:'add_node',label:tr('Add node'),icon:'add'}],ui.inspector,rect(0,y,w,38),!model.busy,'inspector'));y+=46;
  if(ui.inspector==='add_node'){
    if(model.mode==='workflow'){
      addForm([{id:'adminNodeName',title:'Node name',description:'Enter a unique node name',props:{text:ui.nodeName,action:{type:'nodeName'}}},
        {kind:'Choice',id:'adminNodeKind',title:'Node type',options:(model.metadata.nodeTypes||[]).map(value=>({value,label:value})),props:{value:model.document.searchType==='sthpw/task'?'status':ui.nodeKind,enabled:edit&&model.document.searchType!=='sthpw/task',action:{type:'nodeKind'}}}]);
    }else{
      action('adminCreateSchemaTypeInspector','New Search Type','add',{type:'createType'});
      addForm([{id:'adminGraphTypeFilter',title:'Find a Search Type',props:{text:ui.typeQuery,action:{type:'typeQuery'}}}],!model.busy);
      nodes.push(node('List','adminGraphTypeCatalog',rect(0,y,w,220),{source:'graphTypes',keyField:'identity',rowHeight:66,scrollbarId:'adminGraphTypeCatalogScrollBar'}));y+=228;
    }
    action('adminAddNode','Add node','add',{type:'addNode'},edit&&!!(model.mode==='workflow'?ui.nodeName.trim():ui.typeToAdd));
    const options=(model.nodes||[]).filter(row=>!row.referenceOnly).map(row=>({value:row.identity,label:row.label||row.identity}));
    addForm([{kind:'Choice',id:'adminConnectSource',title:'Source',options,props:{value:ui.source,action:{type:'source'}}},{kind:'Choice',id:'adminConnectTarget',title:'Destination',options,props:{value:ui.target,action:{type:'target'}}}]);
    action('adminConnectNodes','Connect','link',{type:'connect'},edit&&!!ui.source&&!!ui.target&&ui.source!==ui.target);
  }else if(current||edge){
    heading('graphSelectionHeading',current?current.identity:edge.from+' → '+edge.to,readonly?model.mode==='workflow'?'This process is referenced by a connection. Add the missing process or remove its connections before saving.':'This type is referenced by a connection. Add its registered node to the canvas to move it.':'');
    if((model.selectedNodes||[]).length>1){nodes.push(node('List','adminGraphMultiSelection',rect(0,y,w,152),{source:'graphSelection',keyField:'identity',rowHeight:40}));y+=160;}
    action('adminRemoveGraphSelection','Remove from canvas','close',{type:'remove'},edit&&!readonly||edit&&!!edge);
    if(current&&!readonly){
      addForm([{id:'adminGraphPositionX',title:'Horizontal position',description:'Move this node without dragging.',props:{text:own(ui.text,'positionX')?ui.text.positionX:String(current.nodeX),inputMode:'decimal',action:{type:'buffer',key:'positionX'},commitAction:{type:'position',key:'positionX'}}},{id:'adminGraphPositionY',title:'Vertical position',description:'Move this node without dragging.',props:{text:own(ui.text,'positionY')?ui.text.positionY:String(current.nodeY),inputMode:'decimal',action:{type:'buffer',key:'positionY'},commitAction:{type:'position',key:'positionY'}}}]);
      if(model.mode==='schema'){
        action('adminNodeWorkflows','Workflows','schema',{type:'nodeWorkflows'},!model.busy);
        if(!model.instance&&['sthpw','config'].indexOf(current.identity.split('../../../../../../../../..')[0])<0)action('adminDeleteSearchType','Delete from project','close',{type:'deleteType'},edit);
      }
    }
    if(model.mode==='workflow'&&edge){
      const choices=(model.nodes||[]).filter(row=>!row.referenceOnly).map(row=>({value:row.identity,label:row.label||row.identity}));
      addForm(['from','to','from_attr','to_attr'].map(key=>({id:'adminWorkflowEdge_'+key,title:({from:'Source',to:'Destination',from_attr:'Output condition',to_attr:'Input name'})[key],description:'Native connection attributes.',kind:key==='from'||key==='to'?'Choice':'Field',options:choices,props:Object.assign({action:{type:'attribute',key}},key==='from'||key==='to'?{value:edge[key]||''}:{text:edge[key]||''})})));
      editor('attributes','Attributes (JSON)',model.attributes);
    }else if(model.mode==='workflow'&&current&&!readonly){
      nodes.push(sectionSelector('adminProcessPages',[{value:'parameters',label:tr('Parameters'),icon:'tune'},{value:'native_json',label:tr('Advanced JSON'),icon:'code'}],ui.processPage,rect(0,y,w,38),!model.busy,'processPage'));y+=46;
      if(ui.processPage==='parameters'){
        addForm(Process.fields(model,ui,language));
        const defaults=(model.processSettings||{}).default||{};
        if(['action','condition'].indexOf(model.processKind)>=0&&defaults.action!=='command')editor('script','Script body',defaults.script,'The code is stored with this process. Applying the draft does not run it.');
      }else{editor('settings','Native process settings',model.settings,'Advanced access to native data, including parameters of installed custom nodes. Standard settings are available in Parameters.');editor('attributes','Attributes (JSON)',model.attributes);}
    }else{
      if(model.mode==='schema'&&(model.instance||edge)){
        const connection=model.connection||{};
        if(model.instance){heading('schemaInstanceHeading','Many-to-many · new Search Type','This is a draft. The instance table and its key columns will be created only when you save the schema.');addForm([{id:'adminSchemaInstanceName',title:'Instance table name',props:{text:own(ui.text,'instance')?ui.text.instance:model.instance.split('../../../../../../../../..').pop(),action:{type:'buffer',key:'instance'},commitAction:{type:'commitInstance'}}}]);
          if(!edge)for(const link of model.instanceLinks||[])action('schemaInstanceLink_'+link.edgeIndex,link.to,'link',{type:'selectEdge',index:link.edgeIndex},!model.busy);
          action('adminSchemaRestoreDirect','Restore direct connection','undo',{type:'restoreDirect'});
        }
        if(edge){
          if(!model.instance)addForm([{kind:'Choice',id:'adminSchemaRelationship',title:'Relationship type',description:'Many-to-many creates a separate instance Search Type with two key connections.',options:[{value:'code',label:'code'},{value:'id',label:'id'}].concat([edge.from,edge.to].indexOf('*')<0?[{value:'many_to_many',label:'many_to_many'}]:[]),props:{value:edge.relationship||'code',action:{type:'relationship'}}}]);
          addForm([{kind:'Switch',id:'adminSchemaCreateColumns',title:'Create missing columns',description:"Choose existing columns below, or enter a new key column name. New columns are created on schema save, using the opposite key's type.",props:{checked:!!model.createColumns,action:{type:'createColumns'}}}]);
          action('adminSchemaReverse','Reverse connection','refresh',{type:'reverse'},edit&&!model.instance);action('adminSchemaRefreshColumns','Reload columns from server','refresh',{type:'refreshColumns'},!model.busy&&!model.columnsBusy);
          if(model.columnsError||model.columnsBusy){nodes.push(node('Area','adminSchemaColumnsStatus',rect(0,y,w,64),{label:tr('Columns'),text:tr(model.columnsError||'Loading data…'),readOnly:true,notice:true,color:model.columnsError?'error':'secondaryText'}));y+=72;}
          for(const side of [{key:'from_col',name:connection.from,title:'Source key column'},{key:'to_col',name:connection.to,title:'Destination key column'}]){
            const info=(model.columnCatalog||{})[side.name]||{},columns=info.columns||[],options=columns.map(row=>({value:row.name,label:row.name+' · '+(row.type||'')+(row.pending?' · '+tr('Pending'): '')}));
            addForm([{id:'adminSchema_'+side.key,title:side.title,description:side.name,props:{text:connection[side.key]||'',action:{type:'column',key:side.key}}},{kind:'Choice',id:'adminSchemaChoose_'+side.key,title:'Existing columns',options:[{value:'',label:tr('Choose a column')}].concat(options),props:{value:connection[side.key]||'',action:{type:'column',key:side.key}}}]);
            if(info.tableAvailable===false)heading('schemaAbsent_'+side.key,'Database table unavailable','The database table is absent. No table is created by reading columns.');
          }
          addForm([{id:'adminSchemaPath',title:'Relationship path',description:'Optional native path used to distinguish multiple relationships.',props:{text:edge.path||'',action:{type:'attribute',key:'path'}}}]);
        }
      }
      if(!readonly)editor('attributes','Attributes (JSON)',model.attributes);
    }
  }else if(model.mode==='workflow'&&model.ready){
    heading('pipelineSettingsHeading','Pipeline settings');
    addForm([{id:'adminPipelineName',title:'Name',field:'name',props:{text:model.document.name||''}},
      {id:'adminPipelineDescription',title:'Description',field:'description',kind:'Area',height:86,props:{text:model.document.description||''}},
      {id:'adminPipelineColor',title:'Color',field:'color',kind:'ColorChoice',props:{value:model.document.color||''}}]);
    heading('pipelineSearchTypeHeading','Search Type');nodes.push(label('adminWorkflowSearchType',rect(0,y,w,38),model.document.searchType||tr('No Search Type')));y+=46;
  }else heading('graphSelectHelp','Select a node or a connection','Its details appear here. Use Add node to extend the canvas.');
  return {nodes,height:y+12};
}
export function describe(model,ui,width,height,language){
  if(width<=0||height<=0)return {nodes:[]};
  const tr=text=>translate(text,language),workflow=model.mode==='workflow',narrow=width<800,edit=policy(model).editable&&!ui.confirmation;
  const noticeModel=Object.assign({},model,{error:model.error||ui.error});
  if(ui.confirmation==='remove')noticeModel.confirmationText=workflow?'Remove the selection from this workflow draft?':'Remove the selection from the schema draft? Search Types, tables and data will be kept.';
  if(ui.confirmation==='selection')noticeModel.confirmationText='Discard unapplied JSON changes?';
  const notice=notices(noticeModel,ui,width,language,undefined,ui.confirmation==='remove'?'Remove from canvas':undefined),nodes=notice.nodes;let y=notice.top;
  nodes.push(sectionSelector('adminGraphPages',[{value:'canvas',label:tr('Canvas'),icon:'schema'},{value:'technical',label:tr('Technical'),icon:'code'}],ui.page,rect(0,y,Math.min(width,320),38),!model.busy,'page'));y+=46;
  if(!model.ready){nodes.push(label('adminGraphEmpty',rect(12,y,width-24,80),tr('Select a workflow or create a new one.'),{wrap:true}));}
  const info=model.metadata.shared?'Shared pipeline: read-only. Create a project-owned pipeline to make project-specific changes.':!workflow&&model.identity&&!model.canWrite?'Built-in system schema · read-only':'';
  if(info){nodes.push(label('adminGraphReadOnly',rect(0,y,width,64),tr(info),Object.assign({wrap:true},muted)));y+=72;}
  const missing=workflow?(model.nodes||[]).filter(row=>row.referenceOnly).map(row=>row.identity):[];
  if(missing.length){nodes.push(node('Area','adminMissingProcesses',rect(0,y,width,68),{label:tr('Missing processes'),text:tr('Connections refer to missing processes')+': '+missing.join(', '),notice:true,readOnly:true,color:'error'}));y+=76;}
  if(narrow){nodes.push(sectionSelector('adminGraphPanels',[].concat(workflow?[{value:'catalog',label:tr('Workflows'),icon:'list'}]:[],[{value:'canvas',label:tr('Canvas'),icon:'schema'},{value:'properties',label:tr('Properties'),icon:'tune'}]),ui.panel,rect(0,y,width,38),!model.busy,'panel'));y+=46;}
  const h=Math.max(1,height-y),catalogWidth=workflow&&!narrow?(ui.catalogVisible?Math.min(ui.catalogWidth,width*.28):40):0,propertiesWidth=!narrow?(ui.propertiesVisible?Math.min(ui.propertiesWidth,width*.4):40):0;
  if(workflow&&(!narrow||ui.panel==='catalog')){
    const w=narrow?width:catalogWidth,children=[];
    if(narrow||ui.catalogVisible)children.push(label('adminWorkflowCatalogTitle',rect(8,4,w-56,30),tr('Workflows'),{weight:600}),node('Field','adminWorkflowSearch',rect(8,42,w-16,38),{text:ui.query,placeholder:tr('Find a workflow'),label:tr('Find a workflow'),action:{type:'query'}}),node('List','adminWorkflowCatalog',rect(8,88,w-16,h-96),{source:'graphPipelines',keyField:'identity',rowHeight:42,scrollbarId:'adminWorkflowCatalogScrollBar'}));
    if(!narrow)children.push(button('adminToggleWorkflowList',rect(w-38,0,38,38),tr(ui.catalogVisible?'Hide workflow list':'Show workflow list'),ui.catalogVisible?'chevron-left':'chevron-right',{type:'catalogVisible'},true,{iconOnly:true}));
    nodes.push(node('Box','adminWorkflowCatalogPanel',rect(0,y,w,h),{visible:ui.page==='canvas',background:'surfaceContainerLow',border:'outlineVariant',children}));
    if(!narrow&&ui.catalogVisible)nodes.push(node('Splitter','adminCatalogSplit',rect(w,y,10,h),{visible:ui.page==='canvas',text:tr('Workflow list width'),value:w,min:180,max:Math.min(420,width*.28),action:{type:'catalogSplit'}}));
  }
  const x=narrow?0:workflow?catalogWidth+10:0,graphWidth=narrow?width:Math.max(1,width-x-propertiesWidth-10);
  const graphNodes=(model.nodes||[]).map(row=>({identity:row.identity,label:row.label||row.identity,nodeX:row.nodeX,nodeY:row.nodeY,color:row.color||'',kind:workflow&&row.kind==='process'?'manual':row.kind,referenceOnly:!!row.referenceOnly,pendingCreation:!!model.document.newTypes&&own(model.document.newTypes,row.identity)}));
  const graphEdges=(model.edges||[]).map((row,index)=>({from:row.from,to:row.to,edgeIndex:index,relationship:row.relationship||'',from_attr:row.from_attr||'',to_attr:row.to_attr||'',label:workflow?row.from_attr||'':row.relationship||'code',color:row.color||''}));
  nodes.push(node('Graph','adminGraphCanvas',rect(x,y,graphWidth,h),{visible:ui.page==='canvas'&&(!narrow||ui.panel==='canvas'),help:false,label:tr(workflow?'Workflow':'Project schema'),nodes:graphNodes,edges:graphEdges,selectedNode:model.selectedNode||'',selectedNodes:model.selectedNodes||[],selectedEdge:model.selectedEdge,readOnly:!edit,selectionEnabled:!model.busy,resetKey:model.identity||'draft:'+model.document.searchType,language,action:{type:'graph'}}));
  if(!narrow||ui.panel==='properties'){
    const w=narrow?width:propertiesWidth,px=narrow?0:width-w,children=[];
    if(narrow||ui.propertiesVisible){const inner=inspector(model,ui,w-12,language);children.push(node('Scroll','adminGraphPropertiesScroll',rect(12,46,w-24,h-58),{contentHeight:inner.height,resetKey:ui.inspector+':'+ui.processPage+':'+model.selectedNode+':'+model.selectedEdge,scrollbarId:'adminGraphPropertiesScrollBar',children:inner.nodes}));}
    if(!narrow)children.push(button('adminToggleGraphProperties',rect(0,0,38,38),tr(ui.propertiesVisible?'Hide properties':'Show properties'),ui.propertiesVisible?'chevron-right':'chevron-left',{type:'propertiesVisible'},true,{iconOnly:true}));
    if(narrow||ui.propertiesVisible)children.push(button('adminGraphAddNode',rect(44,0,w-52,38),tr(ui.inspector==='add_node'?'Selection':'Add node'),ui.inspector==='add_node'?'tune':'add',{type:'inspector',value:ui.inspector==='add_node'?'selection':'add_node'},!model.busy));
    nodes.push(node('Box','adminGraphProperties',rect(px,y,w,h),{visible:ui.page==='canvas',background:'surfaceContainerLow',border:'outlineVariant',children}));
    if(!narrow&&ui.propertiesVisible)nodes.push(node('Splitter','adminGraphSplitHandle',rect(px-10,y,10,h),{visible:ui.page==='canvas',text:tr('Properties panel width'),value:w,min:240,max:Math.min(640,width*.4),reverse:true,action:{type:'propertiesSplit'}}));
  }
  if(ui.page==='technical')nodes.push(node('Area','adminGraphXmlEditor',rect(0,y,width,Math.max(1,h-46)),{label:tr('Native XML'),text:own(ui.text,'xml')?ui.text.xml:model.xml||'',monospace:true,readOnly:!edit,action:{type:'buffer',key:'xml'}}),button('adminGraphApplyXml',rect(0,height-38,Math.min(240,width),38),tr('Apply XML'),'check',{type:'apply',key:'xml'},edit&&own(ui.text,'xml')));
  if(ui.page==='canvas'&&(!narrow||ui.panel==='canvas')){
    // Layout commands share the graph's unused toolbar space after zoom controls.
    const toolbarX=x+230,available=graphWidth-230;
    if(available>130){nodes.push(node('Choice','adminGraphLayoutStyle',rect(toolbarX,y,Math.max(80,available-46),38),{label:tr('Automatic layout'),options:[{value:'flow',label:tr('Directed flow')},{value:'network',label:tr('Network clusters')},{value:'grid',label:tr('Alphabetical grid')}],value:ui.arrange,action:{type:'arrange'},enabled:edit}),button('adminArrangeGraph',rect(x+graphWidth-38,y,38,38),tr('Arrange nodes'),'hierarchy',{type:'layout'},edit&&(model.nodes||[]).length>0,{iconOnly:true}));}
    else nodes.push(button('adminArrangeGraph',rect(x+graphWidth-38,y,38,38),tr('Arrange nodes'),'hierarchy',{type:'layout'},edit&&(model.nodes||[]).length>0,{iconOnly:true}));
  }
  return {nodes};
}
