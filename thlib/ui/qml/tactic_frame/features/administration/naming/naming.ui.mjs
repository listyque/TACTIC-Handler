import {node} from "../../../core/frame.mjs";
import {rect, label, muted, notices, toolbar as documentToolbar, policy, sectionSelector} from "../admin.document.mjs";
import {form} from "../admin.form.mjs";
import {translate} from "../admin.strings.mjs";
const button = (id, bounds, text, icon, action, enabled, extra) => node("Button", id, bounds, Object.assign({text, icon, action, enabled}, extra || {}));
export function toolbar(model, ui, width, language) {
  const tr = text => translate(text, language), actions = documentToolbar(model, ui, width, language), edit = !model.busy && !model.uncertain && model.canWrite && !ui.confirmation;
  actions.nodes = actions.nodes.filter(row => row.id !== "adminDocumentStatus");
  actions.nodes.push(button("namingCreate", rect(46, 0, 38, 38), tr("Create naming rule"), "add", {type: "create"}, edit, {iconOnly: true}), button("namingDuplicate", rect(90, 0, 38, 38), tr("Duplicate selected rule"), "copy", {type: "duplicate"}, edit && model.ready, {iconOnly: true}));
  return actions;
}
export function title(row, language) {const record = row.document || {}, match = /snapshot\.context\)\s*==\s*['"]?([\w/.-]+)/.exec(record.condition || ""); return record.context || (match && match[1]) || record.script_path || translate(record.latest_versionless || record.current_versionless ? "Versionless" : "Default", language);}
export function describe(model, ui, width, height, language) {
  if (width <= 0 || height <= 0) return {nodes: []};
  const tr = text => translate(text, language), local = model.previewMode === "local", noticeModel = Object.assign({}, model, {error: model.error || ui.error});
  if (ui.confirmation === "execute") noticeModel.confirmationText = "Run custom naming code? This uses the normal server environment, not an isolated sandbox. Scripts and classes can change data or files.";
  if (ui.confirmation === "save") noticeModel.confirmationText = "Update project naming rule? This changes future check-ins in the current project. Existing files are kept.";
  const notice = notices(noticeModel, ui, width, language, "Discard unsaved naming changes?", ui.confirmation === "execute" ? "Evaluate with custom code" : undefined), nodes = notice.nodes;
  const y = notice.top, h = height-y, split = width >= 800, left = split ? Math.min(ui.catalogWidth, width * .4) : width, editing = split || ui.editing;
  if (h < 220) return {nodes: [node("Scroll", "namingPageScroll", rect(0,0,width,height), {contentHeight: 400+y, children: describe(model,ui,width-16,400+y,language).nodes})]};
  if (split || !ui.editing) nodes.push(node("Box", "namingCatalogPanel", rect(0,y,left,h), {background:"surfaceContainerLow", border:"outlineVariant", children:[label("namingCatalogTitle",rect(12,8,left-24,28),tr("Naming rules"),{fontSize:15,weight:600}),node("List","namingRules",rect(12,44,left-24,h-56),{source:"namingRules",keyField:"identity",rowHeight:86,scrollbarId:"namingRulesScrollBar"})].concat(model.rules.length?[]:[label("namingRulesEmpty",rect(12,52,left-24,100),tr("No rules for this search type"),Object.assign({wrap:true},muted))])}));
  if(split)nodes.push(node("Splitter","namingSplitHandle",rect(left,y,10,h),{text:tr("Naming rules panel width"),value:left,min:180,max:width*.4,action:{type:"split"}}));
  if (!editing) return {nodes};
  const bounds=rect(split?left+10:0,y,split?width-left-10:width,h), w=bounds.width-40, children=[];let top=12;
  if(!split){children.push(button("namingBack",rect(12,top,110,36),tr("Back"),"chevron-left",{type:"back"},!model.busy&&!!model.identity));top+=44;}
  children.push(label("namingTargetTitle",rect(12,top,w,26),model.targetTitle||model.searchType||tr("Naming editor"),{fontSize:15,weight:600}),label("namingTargetType",rect(12,top+30,w,22),model.project+" / "+model.searchType,muted));top+=60;
  if(!model.ready)children.push(label("namingSelectHelp",rect(12,top,w,80),tr("Select a rule or create a new one."),Object.assign({wrap:true},muted)));
  else {
    children.push(sectionSelector("namingPages",[{value:"rule",label:tr("Naming rule"),icon:"edit"},{value:"preview",label:tr("Naming preview"),icon:"search"},{value:"advanced",label:tr("Advanced fields"),icon:"tune"}],ui.page,rect(12,top,bounds.width-24,38),!model.busy,"page",tr("Naming sections")));top+=46;
    const fields=[], text=key=>Object.prototype.hasOwnProperty.call(ui.text,key)?ui.text[key]:String(model.document[key]||"");
    const field=(key,title,description,area)=>({id:"naming_"+key,title,description,kind:area?"Area":"Field",height:area?82:38,field:key,props:{text:text(key),action:{type:"text",field:key},commitAction:{type:"commit"}}});
    if(ui.page==="rule") {
      fields.push({kind:"Heading",id:"namingRuleHeading",title:model.identity||"New naming rule"},
        {id:"namingSearchType",title:"Search Type",props:{text:model.searchType,readOnly:true}},field("context","Rule context (empty means any)","Use a context or a native wildcard such as publish/*.",false),
        {kind:"Choice",id:"namingCheckin",title:"Check-in type",field:"checkin_type",options:[{value:"auto",label:tr("Auto")},{value:"strict",label:tr("Strict")},{value:"",label:tr("Unspecified")}],props:{value:model.document.checkin_type||""}},
        field("dir_naming","Directory naming","",true),field("file_naming","File naming","",true));
      for(const flag of [["latest_versionless","Latest versionless"],["current_versionless","Current versionless"],["manual_version","Manual version"]])fields.push({kind:"Switch",id:"naming_"+flag[0],title:flag[1],field:flag[0],props:{checked:!!model.document[flag[0]]}});
    } else if(ui.page==="advanced") {
      fields.push({kind:"Heading",id:"namingAdvancedHeading",title:"Advanced fields"});
      for(const row of [["snapshot_type","Snapshot type","Empty matches any snapshot type."],["base_dir_alias","Base directory alias","Repository alias used by native check-in."],["sandbox_dir_naming","Sandbox directory naming","The sandbox path expression; empty uses Directory naming."],["sandbox_dir_alias","Sandbox directory alias","Sandbox repository alias used by native check-in."],["ingest_rule_code","Ingest rule code","Optional ingest rule associated with this naming rule."],["condition","Condition","A native TACTIC expression evaluated on the object and snapshot."],["script_path","Script path","Existing server script overriding directory and file naming."],["class_name","Class name","Installed naming class implementing get_dir and get_file."]])fields.push(field(row[0],row[1],row[2],["condition","sandbox_dir_naming"].indexOf(row[0])>=0));
    } else {
      fields.push({kind:"Heading",id:"namingPreviewHeading",title:"Naming preview",description:local?"Local rule simulation":"Evaluate the draft on a real object with the native TACTIC engine. Preview does not check in a file."});
      if(!local)fields.push({kind:"Choice",id:"namingSampleObject",title:"Search Object",options:model.items.map(row=>({value:row.key,label:row.label})),props:{value:model.sample.key,action:{type:"sample",field:"key"}}});
      for(const row of [["file","Example file"],["process","Process"],["context","Preview context"],["snapshotType","Snapshot type"],["version","Version"],["fileType","File type"]]) {
        if(local&&["process","snapshotType"].indexOf(row[0])>=0&&model.typeMode)continue;
        const version = row[0] === "version";
        fields.push({id:"namingSample_"+row[0],title:row[1],props:{text:version && ui.sampleVersion !== null ? ui.sampleVersion : String(model.sample[row[0]]===undefined?"":model.sample[row[0]]),inputMode:version?"numeric":"text",action:version?{type:"version"}:{type:"sample",field:row[0]},commitAction:version?{type:"commitVersion"}:null}});
      }
    }
    const body=form(fields,w,language,policy(model).editable&&!ui.confirmation);let bottom=body.height;
    if(ui.page==="preview") {
      if(!local) {
        if(model.itemCount>50){body.nodes.push(button("namingObjectsPrevious",rect(0,bottom,100,36),tr("Previous"),"chevron-left",{type:"items",offset:model.itemOffset-50},!model.busy&&model.itemOffset>0),label("namingObjectsPage",rect(108,bottom,Math.max(0,w-216),36),String(model.itemOffset+1)+"–"+(model.itemOffset+model.items.length)+" / "+model.itemCount,{align:"center"}),button("namingObjectsNext",rect(w-100,bottom,100,36),tr("Next"),"chevron-right",{type:"items",offset:model.itemOffset+50},!model.busy&&model.itemOffset+model.items.length<model.itemCount));bottom+=44;}
        body.nodes.push(button("namingEvaluate",rect(0,bottom,w,38),tr("Evaluate naming"),"search",{type:"evaluate"},policy(model).editable&&!!model.sample.key),button("namingEvaluateCustom",rect(0,bottom+46,w,38),tr("Evaluate with custom code"),"code",{type:"evaluate",execute:true},policy(model).editable&&!!model.sample.key));bottom+=96;
      }
      for(const result of model.previewResults||[]) {
        body.nodes.push(label("namingResult_"+result.mode,rect(0,bottom,w,26),tr({version:"Version",latest:"Latest versionless",current:"Current versionless",local:"Local rule simulation"}[result.mode]||result.mode),{weight:600}),node("Area","namingPath_"+result.mode,rect(0,bottom+32,w,100),{text:result.path||"",label:tr("Naming result"),readOnly:true,monospace:true}));bottom+=140;
        const detail=[result.status||"",result.directory?tr("Directory naming")+": "+result.directory:"",result.file?tr("File naming")+": "+result.file:"",result.sandbox?tr("Sandbox directory naming")+": "+result.sandbox:"",result.matches===false?tr("This draft is not selected for these parameters by native naming lookup.")+" "+(result.selectedRule||""):""].filter(Boolean).join("\n");
        if(detail){body.nodes.push(node("Area","namingResultDetails_"+result.mode,rect(0,bottom,w,112),{text:detail,label:tr("Naming result"),readOnly:true,notice:true}));bottom+=120;}
        if(result.collisions&&result.collisions.length){body.nodes.push(node("Area","namingCollisions_"+result.mode,rect(0,bottom,w,120),{text:tr("Existing files already use this path:")+"\n"+result.collisions.map(row=>row.key+" · "+row.snapshot).join("\n"),label:tr("Existing files"),readOnly:true,color:"error"}));bottom+=128;}
      }
    }
    children.push(node("Scroll","namingFieldsScroll",rect(12,top,bounds.width-24,Math.max(1,h-top-12)),{contentHeight:bottom,resetKey:ui.page+":"+model.identity,scrollbarId:"namingFieldsScrollBar",children:body.nodes}));
  }
  nodes.push(node("Box","namingEditorPanel",bounds,{background:"surfaceContainerLow",border:"outlineVariant",children}));
  return {nodes};
}
export function row(listNode, record, model, language) {
  const width=listNode.width-16,doc=record.document||{},tr=text=>translate(text,language);
  return {nodes:[node("Action","namingRule_"+record.identity,rect(0,0,width,82),{text:title(record,language),selected:model.identity===record.identity,enabled:!model.busy&&(!model.uncertain||model.identity===record.identity),normalColor:"surfaceContainerHigh",selectedColor:"contentSelection",children:[label("namingRuleTitle_"+record.identity,rect(12,6,width-24,24),title(record,language),{weight:600}),label("namingRuleSummary_"+record.identity,rect(12,32,width-24,20),doc.file_naming||doc.script_path||doc.dir_naming||"",muted),label("namingRuleIdentity_"+record.identity,rect(12,56,width-24,20),record.identity+" · "+(doc.checkin_type||tr("Unspecified")),muted)],action:{type:"select",identity:record.identity}})]};
}
