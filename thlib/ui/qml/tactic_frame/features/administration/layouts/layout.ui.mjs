import {node} from '../../../core/frame.mjs';
import {rect,label,muted,notices,toolbar as documentToolbar,policy,sectionSelector} from '../admin.document.mjs';
import {form} from '../admin.form.mjs';
import {translate} from '../admin.strings.mjs';
import * as Document from './layout.document.mjs';
import * as Preview from './layout.preview.mjs';
import {pending} from './layout.state.mjs';
const button=(id,bounds,text,icon,action,enabled,extra)=>node('Button',id,bounds,Object.assign({text,icon,action,enabled},extra||{}));
export const labels={group:'Group',view:'Reusable view',text:'Text',title:'Title',description:'Description',image:'Image',link:'Link',button:'Button',metadata:'Metadata','snapshot-details':'Snapshot details','snapshot-size':'File size','snapshot-summary':'Snapshot summary','branch-summary':'Branch summary','file-offline':'File Offline','item-menu':'Item actions','quick-actions':'Snapshot actions',knowledge:'Knowledge Base',relations:'Relationship actions',all:'All items',main:'Main object',children:'Child object',process:'Process',relation:'Relation',versions:'Versions',snapshot:'Snapshot',file:'File',inspect:'Object details',operate:'Object actions',preview:'File preview',tasks:'Tasks',notes:'Notes',upload:'Add files',create:'Create related object',cover:'Fill the image area',contain:'Show the whole image',stretch:'Fill the cell',start:'Start',center:'Center',end:'End',normal:'Normal',muted:'Muted',strong:'Strong'};
export function choices(values,language){return values.map(value=>({value,label:translate(labels[value]||value||'None',language)}));}
export function model(raw,ui){
 let layout={elements:[],columns:12,flow:'grid',collection:'grid',tracks:'',card_width:280},layoutError=raw.parseError?'Invalid configuration XML':'';
 if(!layoutError&&raw.tree)try{layout=Document.describe(raw.tree,raw.view);}catch(error){layoutError=String(error.message||error);}
 if(!layoutError&&(!Number.isInteger(layout.columns)||layout.columns<1||layout.columns>12||!Number.isFinite(layout.card_width)||layout.elements.some(row=>['row','column','span','rows','columns','height','layer'].some(key=>!Number.isFinite(row[key])))))layoutError='Invalid layout size';
 if(!layoutError){
  const names=[];
  for(const item of layout.elements){if(!item.name||names.indexOf(item.name)>=0){layoutError='Invalid or duplicate layout element name';break;}names.push(item.name);}
  if(layout.elements.length>128)layoutError='Layout supports at most 128 elements';
  for(const item of layout.elements){const seen=[item.name];let parent=item.parent;while(parent){if(seen.indexOf(parent)>=0||seen.length>=8){layoutError='Invalid or cyclic layout container';break;}seen.push(parent);const container=layout.elements.find(row=>row.name===parent);parent=container?container.parent:'';}}
 }
 const record=((raw.sampleItems||[])[0]||{}).record||{},bindings=[''].concat(Object.keys((raw.preview||{}).columns||record).filter(key=>key.indexOf('__')!==0).map(key=>'record.'+key),['node.title','node.subtitle','node.preview.image','node.note_count','node.task_count','node.branch.count','node.snapshot_display.version','node.snapshot_display.author']);
 const types=(raw.searchTypes||[]).slice().sort((a,b)=>a.label.toLowerCase()<b.label.toLowerCase()?-1:a.label.toLowerCase()>b.label.toLowerCase()?1:0);
 return Object.assign({},raw,{ready:!!raw.configuration,canLoad:!!raw.canLoad,canWrite:!!raw.canWrite,searchTypes:types,bindings,dirty:!!raw.dirty||pending(ui),pendingText:pending(ui),layout,layoutError,document:{},identity:raw.view||'',saveAllowed:!!raw.checked&&raw.checked===raw.xml&&!layoutError&&!pending(ui),error:raw.error||ui.error,message:raw.message||''});
}
export function toolbar(model,ui,width,language){const tr=text=>translate(text,language),result=documentToolbar(model,ui,width,language),edit=policy(model).editable&&!ui.confirmation;result.nodes=result.nodes.filter(row=>row.id!=='adminDocumentStatus');result.nodes.push(button('layoutCheck',rect(46,0,38,38),tr('Check and preview'),'check',{type:'check'},edit&&!model.layoutError&&!pending(ui),{iconOnly:true}),button('layoutHelp',rect(90,0,38,38),tr('Layout guide'),'help',{type:'help'},true,{iconOnly:true}),button('layoutOpenView',rect(134,0,38,38),tr(model.externalView?'Open view in browser':'Open view'),'open-in-new',{type:'openView'},edit&&!model.dirty&&!!(model.configuration&&model.configuration.resolved&&model.configuration.resolved.configured),{iconOnly:true}));return result;}
export function models(model){return {layoutElements:model.layout.elements};}
export function row(list,record,model,ui,language){
 const width=list.width-16,tr=text=>translate(text,language),id='layoutElement_'+record.name;
 return {nodes:[node('Action',id,rect(0,0,width,70),{text:record.title||record.name,selected:ui.selected===record.name,normalColor:'surfaceContainerHigh',selectedColor:'contentSelection',dragValue:policy(model).editable&&!pending(ui)?record.name:null,dragStartAction:{type:'select',name:record.name},children:[label(id+'Title',rect(record.parent?22:10,4,width-(record.parent?32:20),28),(record.parent?'↳ ':'')+(record.title||record.name),{weight:600}),label(id+'Kind',rect(10,36,width-20,24),tr(labels[record.kind]||record.kind),muted)],action:{type:'select',name:record.name}})]};
}
function propertyFields(model,ui,language){
 const tr=text=>translate(text,language),item=model.layout.elements.find(row=>row.name===ui.selected);if(!item)return [];
 const edit=policy(model).editable,enabled=edit&&!pending(ui),fields=[];
 function text(field,title,value,description,name){
  const key=item.name+':'+field,buffered=field==='title'||field==='when';
  return {id:'layoutProperty_'+field.replace(/:/g,'_'),title,description,props:{text:buffered&&Object.prototype.hasOwnProperty.call(ui.text,key)?ui.text[key]:value===undefined?'':String(value),enabled:buffered?edit&&Object.keys(ui.text).every(value=>value===key):enabled,action:buffered?{type:'text',field,key,name}:{type:'change',field,name},commitAction:buffered?{type:'finishText',key}:null}};
 }
 function choice(field,title,value,options,description,name){return {id:'layoutProperty_'+field.replace(/:/g,'_'),title,description,kind:'Choice',options,props:{value,enabled,action:{type:'change',field,name}}};}
 function integer(field,title,value,description){const key=item.name+':'+field;return {id:'layoutProperty_'+field,title,description,props:{text:Object.prototype.hasOwnProperty.call(ui.text,key)?ui.text[key]:String(value),enabled:edit,action:{type:'buffer',key},commitAction:{type:'number',key,field},inputMode:'numeric'}};}
 const bindings=[{value:'',label:tr('Fixed text')}].concat((model.bindings||[]).filter(Boolean).map(value=>({value,label:tr(({'node.title':'Object title','node.subtitle':'Object description','node.preview.image':'Object preview','node.note_count':'Number of notes','node.task_count':'Number of tasks','node.branch.count':'Number of children','node.snapshot_display.version':'Snapshot version','node.snapshot_display.author':'Snapshot author'})[value]||value.replace(/^record\./,''))})));
 fields.push({kind:'Heading',id:'layoutElementHeading',title:item.title||item.name},text('title','Label',item.title),choice('kind','Widget',item.kind,choices(Document.widgets,language)));
 if(['text','title','description','image','link','button'].indexOf(item.kind)>=0){
  fields.push({kind:'Heading',id:'layoutContentHeading',title:'Content'},choice('option:bind','Data binding',item.options.bind||'',bindings,'Choose which object value to display'));
  if(!item.options.bind)fields.push(text('option:text',item.kind==='image'?'Image URL':'Text',item.options.text||''));
  if(item.kind==='image'){if(item.role!=='preview')fields.push(integer('height','Image height',item.height));fields.push(choice('option:fit','Image fit',item.options.fit||'cover',choices(['cover','contain'],language)));}
  if(item.kind==='link'||item.kind==='button')fields.push(text('option:href','Link URL',item.options.href||''));
  if(item.kind==='button')fields.push(choice('option:action','Action',item.options.action||'',choices([''].concat(Document.actions),language)),choice('option:badge','Badge binding',item.options.badge||'',bindings.map(row=>row.value?row:{value:'',label:tr('No badge')}),'Choose a number to show on the button'),text('option:icon','Icon',item.options.icon||''));
 }
 if(item.kind==='view')fields.push(text('option:view','Reusable view',item.options.view||''));
 const parentOptions=[{value:'',label:tr('View root')}].concat(model.layout.elements.filter(row=>row.kind==='group'&&row.name!==item.name).map(row=>({value:row.name,label:row.title||row.name}))),parent=model.layout.elements.find(row=>row.name===item.parent),grid=(parent?parent.flow:model.layout.flow)==='grid';
 fields.push({kind:'Heading',id:'layoutPositionHeading',title:'Position'},choice('parent','Container',item.parent,parentOptions));
 if(grid)for(const key of ['row','column','span','rows'])fields.push(integer(key,({row:'Row',column:'Column',span:'Column span',rows:'Row span'})[key],item[key]));
 else fields.push({kind:'Heading',id:'layoutSharedPositionHelp',title:'Shared item layout',description:'Positions follow shared item styles. Choose Grid in the parent container for placement by rows and columns.'});
 fields.push(integer('layer','Layer',item.layer,'Higher layers appear in front. Use the same grid cells to place text or buttons over an image.'),{kind:'Heading',id:'layoutAdvancedHeading',title:'More element settings'},
  {kind:'Switch',id:'layoutPropertyVisible',title:'Visible',props:{checked:!item.hidden,enabled,action:{type:'change',field:'hidden',invert:true}}},choice('variant','Item variant',item.variant,choices(Document.variants,language)),text('option:bind','Custom data binding',item.options.bind||''));
 // The same value has two captions, so controls keep distinct stable identities.
 fields[fields.length-1].id='layoutCustomBinding';
 if(item.kind==='link'||item.kind==='button')fields.push(choice('option:href_bind','Link URL binding',item.options.href_bind||'',bindings));
 fields.push(choice('role','Style role',item.role,Object.keys(Document.roles).map(value=>({value,label:tr(Document.roles[value])}))));
 if(item.kind==='group')fields.push(choice('flow','Child layout',item.flow,[{value:'grid',label:tr('Grid')},{value:'contents',label:tr('Shared item layout')}]),integer('columns','Grid columns',item.columns));
 fields.push(choice('tag','Markup tag',item.tag,['div','span','strong','small'].map(value=>({value,label:value}))),text('when','Display conditions',item.when.join(' '),'Limit the element to desktop, mobile or particular items'),choice('align','Alignment',item.align,choices(['stretch','start','center','end'],language)),choice('tone','Text style',item.tone,choices(['normal','muted','strong'],language)));
 return fields;
}
export function describe(model,ui,width,height,language){
 if(width<=0||height<=0)return {nodes:[]};
 if(height<400)return {nodes:[node('Scroll','layoutPageScroll',rect(0,0,width,height),{contentHeight:640,scrollbarId:'layoutPageScrollBar',children:describe(model,ui,width-16,640,language).nodes})]};
 const tr=text=>translate(text,language),edit=policy(model).editable&&!ui.confirmation,noticeModel=Object.assign({},model);
 if(ui.confirmation==='remove')noticeModel.confirmationText='Remove this element and its children?';
 const notice=notices(noticeModel,ui,width,language,undefined,ui.confirmation==='remove'?'Remove element':undefined),nodes=notice.nodes;let y=notice.top;
 nodes.push(label('layoutGuideHeading',rect(0,y,width,28),tr('Build your own view'),{fontSize:16,weight:600}),label('layoutGuideText',rect(0,y+34,width,width<520?62:36),tr('1. Choose a starting point · 2. Arrange elements · 3. Check and save'),Object.assign({wrap:true},muted)));y+=width<520?104:78;
 nodes.push(sectionSelector('layoutPages',[{value:'design',label:tr('Design')},{value:'configuration',label:tr('Configuration')},{value:'xml',label:tr('Source XML')},{value:'changes',label:tr('Configuration changes')},{value:'resolved',label:tr('Resolved preview')}],ui.page,rect(0,y,width,38),!model.busy,'page'));y+=46;
 if(model.sampleError){nodes.push(node('Area','layoutSampleError',rect(0,y,width,58),{label:tr('Preview data could not be loaded'),text:tr('Preview data could not be loaded')+': '+model.sampleError,readOnly:true,notice:true}));y+=66;}
 const h=Math.max(1,height-y),layout=model.layout,selected=layout.elements.find(row=>row.name===ui.selected);
 if(ui.page==='xml'){
  nodes.push(node('Code','layoutXmlSource',rect(0,y,width,h),{text:model.xml||'',language,syntax:'xml',readOnly:!edit,service:'sourceEditor',bufferKey:[model.project,model.searchType,model.view,model.source].join(':'),action:{type:'xml'},helpAction:{type:'help'}}));return {nodes};
 }
 if(ui.page==='changes'){nodes.push(node('Area','layoutChanges',rect(0,y,width,h),{text:model.diff||tr('Check and preview the draft before saving.'),label:tr('Configuration changes'),monospace:true,readOnly:true}));return {nodes};}
 if(ui.page==='configuration'){
  const clean=!model.busy&&!model.dirty&&!model.uncertain,configuration=model.configuration||{},views=configuration.layout_views||['continuous_example','table_example','cards_example'],sourceOptions=(configuration.sources||[]).map(row=>({value:row.id,label:String(row.id)+' · '+tr('Priority')+' '+(row.priority===null?'':row.priority)})).concat([{value:'',label:tr('New override')}]);
  const fields=[{kind:'Heading',id:'layoutContextHeading',title:'Configuration'},
   {kind:'Choice',id:'layoutSearchType',title:'Search Type',options:model.searchTypes||[],props:{value:model.searchType,enabled:clean,action:{type:'context',field:'searchType'}}},
   {kind:'Choice',id:'layoutView',title:'Configuration view',options:views.map(value=>({value,label:tr(({continuous_example:'Tree example',table_example:'Table example',cards_example:'Cards example'})[value]||value)})),props:{value:model.view,enabled:clean,action:{type:'context',field:'view'}}},
   {kind:'Choice',id:'layoutSource',title:'Configuration source',options:sourceOptions,props:{value:model.source,enabled:clean,action:{type:'source'}}},
   {kind:'Heading',id:'layoutNewViewHeading',title:'Create custom view',description:'Start from a template or copy this view. Give your view a unique name.'},
   {id:'layoutNewName',title:'View name',props:{text:ui.newName,enabled:edit&&clean,action:{type:'newName'}}},
   {kind:'Choice',id:'layoutTemplate',title:'Layout template',options:[{value:'blank',label:tr('Blank view')},{value:'continuous',label:tr('Continuous Tree')},{value:'cards',label:tr('Cards')},{value:'table',label:tr('Table View')},{value:'copy',label:tr('Copy current view')}],props:{value:ui.template,enabled:edit&&clean,action:{type:'template'}}},
   {kind:'Button',id:'layoutCreateView',title:'Create custom view',props:{icon:'add',enabled:edit&&clean,action:{type:'newView'}}}];
  if(!model.layoutError){
   const integer=(key,title)=>({id:'layoutRoot_'+key,title,props:{text:Object.prototype.hasOwnProperty.call(ui.text,'root:'+key)?ui.text['root:'+key]:String(layout[key]),enabled:edit,action:{type:'buffer',key:'root:'+key},commitAction:{type:'number',key:'root:'+key,name:'',field:key},inputMode:'numeric'}});
   fields.push({kind:'Heading',id:'layoutCollectionHeading',title:'Collection layout'},
    {kind:'Choice',id:'layoutCollection',title:'Collection layout',options:[{value:'grid',label:tr('Cards')},{value:'list',label:tr('List')},{value:'tree',label:tr('Continuous Tree')},{value:'table',label:tr('Table View')}],props:{value:layout.collection,enabled:edit&&!pending(ui),action:{type:'change',name:'',field:'collection'}}});
   if(layout.collection==='grid')fields.push(integer('card_width','Card width'));
   fields.push({kind:'Choice',id:'layoutFlow',title:'Container layout',options:[{value:'grid',label:tr('Grid')},{value:'contents',label:tr('Shared item layout')}],props:{value:layout.flow,enabled:edit&&!pending(ui),action:{type:'change',name:'',field:'flow'}}},integer('columns','Grid columns'),{id:'layoutTracks',title:'Column tracks',description:'Optional sizes such as 128px 1fr auto',props:{text:layout.tracks||'',enabled:edit&&!pending(ui),action:{type:'change',name:'',field:'tracks'}}});
  }
  const body=form(fields,width-16,language,edit);nodes.push(node('Scroll','layoutConfigurationScroll',rect(0,y,width,h),{contentHeight:body.height,scrollbarId:'layoutConfigurationScrollBar',children:body.nodes}));return {nodes};
 }
 if(ui.page==='resolved'){
  const resolved=model.preview&&(model.preview.item_layout||(model.preview.table||{}).item_layout);
  if(!resolved){nodes.push(label('layoutResolvedHelp',rect(12,y,width-24,96),tr('Check and preview the draft before saving.'),Object.assign({wrap:true},muted)));return {nodes};}
  const children=[label('layoutResolvedNotice',rect(0,0,width-16,44),tr('Read-only preview. Changes have not been saved.'),Object.assign({wrap:true},muted))];let top=52;
  const samples=model.sampleItems&&model.sampleItems.length?model.sampleItems:[Preview.sample(model,ui,language)];
  samples.forEach((sample,index)=>{const body=Preview.describe(resolved,sample,width-32,'',language,width,model.assetBase,'layoutResolved_'+index);children.push(node('Box','layoutResolvedItem_'+index,rect(0,top,width-16,body.height+16),{background:'surfaceContainerLow',border:'outlineVariant',children:[node('Box','layoutResolvedContent_'+index,rect(8,8,width-32,body.height),{children:body.nodes})]}));top+=body.height+28;});
  nodes.push(node('Scroll','layoutResolvedScroll',rect(0,y,width,h),{contentHeight:top,scrollbarId:'layoutResolvedScrollBar',children}));return {nodes};
 }
 if(model.layoutError){nodes.push(node('Area','layoutInvalid',rect(0,y,width,h),{text:tr(model.layoutError)+'. '+tr('Use Source XML or create a view from a layout template.'),label:tr('Layout Editor'),readOnly:true,notice:true,color:'error'}));return {nodes};}
 const wide=width>=1000,left=wide?Math.min(ui.catalogWidth,width*.24):width,properties=wide?Math.min(ui.propertiesWidth,width*.34):width;
 if(!wide){nodes.push(sectionSelector('layoutPanels',[{value:'elements',label:tr('Elements')},{value:'preview',label:tr('Item preview')},{value:'settings',label:tr('Element settings')}],ui.panel,rect(0,y,width,38),!model.busy,'panel'));y+=46;}
 const bodyHeight=Math.max(1,height-y);
 if(wide||ui.panel==='elements'){
  const w=left,children=[label('layoutElementsHeading',rect(12,8,w-24,28),tr('Elements'),{weight:600}),node('Choice','layoutAddWidget',rect(12,44,w-24,38),{label:tr('Add widget'),value:'',options:[{value:'',label:tr('Add widget')}].concat(choices(Document.widgets,language)),enabled:edit&&!pending(ui),action:{type:'add'}}),node('List','layoutElementsList',rect(12,90,w-24,bodyHeight-146),{source:'layoutElements',keyField:'name',rowHeight:74,scrollbarId:'layoutElementsScrollBar'}),button('layoutEarlier',rect(12,bodyHeight-44,(w-32)/2,36),tr('Move element earlier'),'chevron-up',{type:'change',field:'order',value:-1},edit&&!!selected&&!pending(ui),{iconOnly:true}),button('layoutLater',rect((w+8)/2,bodyHeight-44,(w-32)/2,36),tr('Move element later'),'chevron-down',{type:'change',field:'order',value:1},edit&&!!selected&&!pending(ui),{iconOnly:true})];
  nodes.push(node('Box','layoutElementsPanel',rect(0,y,w,bodyHeight),{background:'surfaceContainerLow',border:'outlineVariant',children}));
  if(wide)nodes.push(node('Splitter','layoutElementsSplit',rect(w,y,10,bodyHeight),{text:tr('Elements panel width'),value:w,min:180,max:Math.min(420,width*.24),action:{type:'catalogSplit'}}));
 }
 if(wide||ui.panel==='settings'){
  const w=properties,x=wide?width-w:0,fields=propertyFields(model,ui,language),body=form(fields,w-40,language,edit&&!pending(ui));
  if(selected){body.nodes.push(button('layoutRemoveElement',rect(0,body.height,w-40,38),tr('Remove element'),'delete',{type:'remove'},edit&&!pending(ui)));body.height+=46;}
  else{body.nodes.push(label('layoutSelectHelp',rect(0,0,w-40,120),tr('Select an element or add a new widget.'),Object.assign({wrap:true},muted)));body.height=128;}
  nodes.push(node('Box','layoutSettingsPanel',rect(x,y,w,bodyHeight),{background:'surfaceContainerLow',border:'outlineVariant',children:[node('Scroll','layoutSettingsScroll',rect(12,12,w-24,bodyHeight-24),{contentHeight:body.height,resetKey:ui.selected,scrollbarId:'layoutSettingsScrollBar',children:body.nodes})]}));
  if(wide)nodes.push(node('Splitter','layoutSettingsSplit',rect(x-10,y,10,bodyHeight),{text:tr('Element settings width'),value:w,min:240,max:Math.min(520,width*.34),reverse:true,action:{type:'propertiesSplit'}}));
 }
 if(wide||ui.panel==='preview'){
  const x=wide?left+10:0,w=wide?Math.max(1,width-left-properties-20):width,children=[label('layoutPreviewHeading',rect(12,8,w-24,28),tr('Item preview'),{weight:600}),node('Choice','layoutSampleVariant',rect(12,44,w-24,38),{label:tr('Preview item type'),value:ui.sampleVariant,options:choices(Document.variants.filter(value=>value!=='all'),language),action:{type:'sampleVariant'}})];
  const previewWidth=Math.max(1,Math.min(w-40,layout.collection==='grid'?numberWidth(layout.card_width):w-40)),body=Preview.describe(layout,Preview.sample(model,ui,language),previewWidth,ui.selected,language,width,model.assetBase),previewNodes=[node('Box','layoutPreviewItem',rect(0,0,previewWidth,body.height+16),{background:'surfaceContainerHigh',children:body.nodes})];let top=body.height+28;
  if(!layout.elements.length){previewNodes.push(label('layoutAddHelp',rect(0,top,w-40,90),tr('Add an image, text or button to begin.'),Object.assign({wrap:true},muted)));top+=98;}
  if(selected){const parent=layout.elements.find(row=>row.name===selected.parent),grid=(parent?parent.flow:layout.flow)==='grid',columns=parent?parent.columns:layout.columns;
   if(grid){const count=Math.min(12,Math.max(4,...layout.elements.filter(row=>row.parent===selected.parent).map(row=>row.row+row.rows))),cell=(w-40)/Math.max(1,columns);previewNodes.push(label('layoutGridHeading',rect(0,top,w-40,28),tr('Place on the grid'),{weight:600}));top+=36;
    for(let row=1;row<=count;row++)for(let column=1;column<=columns;column++)previewNodes.push(button('layoutGrid_'+row+'_'+column,rect((column-1)*cell,top+(row-1)*32,Math.max(1,cell-3),29),String((row-1)*columns+column),'',{type:'move',row,column},edit&&!pending(ui),{highlighted:selected.row===row&&selected.column===column,dropAction:{type:'drop',row,column}}));top+=count*32+8;
    const moves=[['up',-1,0,'chevron-up'],['down',1,0,'chevron-down'],['left',0,-1,'chevron-left'],['right',0,1,'chevron-right']],size=(w-58)/4;moves.forEach((move,index)=>previewNodes.push(button('layoutMove_'+move[0],rect(index*(size+6),top,size,36),tr(({up:'Move up',down:'Move down',left:'Move left',right:'Move right'})[move[0]]),move[3],{type:'move',row:selected.row+move[1],column:selected.column+move[2]},edit&&!pending(ui),{iconOnly:true})));top+=44;
   }
  }
  children.push(node('Scroll','layoutPreviewScroll',rect(12,90,w-24,bodyHeight-102),{contentHeight:top,scrollbarId:'layoutPreviewScrollBar',children:previewNodes}));
  nodes.push(node('Box','layoutPreviewPanel',rect(x,y,w,bodyHeight),{background:'surfaceContainerLow',border:'outlineVariant',children}));
 }
 return {nodes};
}
function numberWidth(value){return Number.isFinite(Number(value))?Math.max(1,Math.min(1200,Number(value))):280;}
