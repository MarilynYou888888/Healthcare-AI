/* File bytes stay in this dedicated worker. Never upload, evaluate formulas or follow workbook links. */
importScripts('/vendor/xlsx.full.min.js', '/vendor/papaparse.min.js');
let limits; // Loaded from the same policy module as validation and the UI.
function fail(message) { throw new Error(message); }
async function inspectZip(bytes) {
  const v = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  if (bytes.length < 22 || v.getUint32(0,true) !== 0x04034b50) fail('This is not an XLSX workbook. Save a values-only .xlsx copy and retry.');
  let end = -1;
  for (let i=bytes.length-22; i>=Math.max(0,bytes.length-65557); i--) if(v.getUint32(i,true)===0x06054b50){end=i;break;}
  if(end<0 || v.getUint16(end+4,true) || v.getUint16(end+6,true)) fail('Unsupported or damaged workbook archive. Save a new XLSX copy.');
  const count=v.getUint16(end+10,true); let pos=v.getUint32(end+16,true), expanded=0;
  if(count===65535 || count>10000) fail('Workbook archive has too many parts. Export only the needed sheets.');
  const names=[],parts=[];
  for(let i=0;i<count;i++) {
    if(pos+46>end || v.getUint32(pos,true)!==0x02014b50) fail('Workbook archive is damaged. Save a new XLSX copy.');
    const flags=v.getUint16(pos+8,true), size=v.getUint32(pos+24,true), compressed=v.getUint32(pos+20,true);
    const n=v.getUint16(pos+28,true), extra=v.getUint16(pos+30,true), comment=v.getUint16(pos+32,true);
    if(flags&1 || size===0xffffffff || compressed===0xffffffff) fail('Encrypted or ZIP64 workbooks are not supported. Export an unencrypted XLSX.');
    expanded+=size;
    if(expanded>limits.expandedBytes) fail('Workbook exceeds the 100 MiB expanded-content limit. Export fewer sheets.');
    if(pos+46+n+extra+comment>end) fail('Workbook archive is damaged.');
    const name=new TextDecoder().decode(bytes.subarray(pos+46,pos+46+n));
    names.push(name);
    const offset=v.getUint32(pos+42,true),method=v.getUint16(pos+10,true);
    if(offset+30>bytes.length || v.getUint32(offset,true)!==0x04034b50) fail('Workbook archive contains a damaged entry.');
    const start=offset+30+v.getUint16(offset+26,true)+v.getUint16(offset+28,true);
    if(start+compressed>bytes.length || ![0,8].includes(method)) fail('Unsupported workbook compression. Save a new XLSX copy.');
    parts.push({name,start,compressed,size,method});
    pos+=46+n+extra+comment;
  }
  if(!names.includes('[Content_Types].xml') || !names.includes('xl/workbook.xml')) fail('File is not a supported XLSX workbook.');
  if(names.some(n=>/vbaProject|macrosheets|externalLinks/i.test(n))) fail('Macros or external workbook links are not supported. Export a values-only XLSX.');
  // Verify actual streamed expansion, not only untrusted ZIP size declarations.
  let actualTotal=0;
  for(const part of parts) {
    let stream=new Blob([bytes.subarray(part.start,part.start+part.compressed)]).stream();
    if(part.method===8) stream=stream.pipeThrough(new DecompressionStream('deflate-raw'));
    const reader=stream.getReader();let actual=0,content='';
    while(true) {
      const {value,done}=await reader.read();if(done)break;
      actual+=value.length;actualTotal+=value.length;
      if(actualTotal>limits.expandedBytes || actual>part.size) {await reader.cancel();fail('Workbook expanded content exceeds its declared size or the 100 MiB limit. Export fewer sheets.');}
      if(part.name==='[Content_Types].xml')content+=new TextDecoder().decode(value);
    }
    if(actual!==part.size) fail('Workbook archive contains inconsistent sizes. Save a new XLSX copy.');
    if(/<Override[^>]+(?:macroEnabled|vbaProject)/i.test(content)) fail('Macros are not supported. Export a values-only XLSX.');
  }
}
function parseCsv(bytes) {
  let text;
  try { text=new TextDecoder('utf-8',{fatal:true}).decode(bytes); } catch { fail('CSV must use UTF-8 encoding. Choose CSV UTF-8 when saving.'); }
  if(text.includes('\0')) fail('CSV contains binary content. Save as CSV UTF-8.');
  const parsed=Papa.parse(text,{dynamicTyping:false,skipEmptyLines:false});
  const errors=parsed.errors.filter(e=>e.code!=='UndetectableDelimiter');
  if(errors.length) fail(`CSV row ${(errors[0].row??0)+1}: ${errors[0].message} Save a well-formed CSV with matching quotes.`);
  let cells=0;
  const rows=parsed.data.map(row=>row.map(value=>{ if(value!=='') cells++; return {v:value,t:'s'}; }));
  while(rows.length && rows.at(-1).every(cell=>cell.v==='')) rows.pop();
  if(cells>limits.cells || rows.length>limits.rows+1 || rows.some(r=>r.length>limits.columns)) fail('CSV exceeds 50,000 data rows, 100 columns, or 500,000 populated cells. Split the file.');
  return [{name:'CSV table',hidden:false,rows,merges:[]}];
}
async function parseXlsx(bytes) {
  await inspectZip(bytes);
  const book=XLSX.read(bytes,{type:'array',cellNF:true,cellText:true,cellFormula:true,bookVBA:false,dense:true});
  let populated=0;
  return book.SheetNames.map((name,i)=>{
    const sheet=book.Sheets[name], ref=sheet['!ref'];
    if(!ref) return {name,hidden:!!book.Workbook?.Sheets?.[i]?.Hidden,rows:[],merges:[]};
    const range=XLSX.utils.decode_range(ref);
    if(range.e.r>limits.rows || range.e.c>=limits.columns) fail(`Sheet “${name}” exceeds 50,000 data rows or 100 columns. Export only the needed table.`);
    const rows=[];
    for(let r=0;r<=range.e.r;r++) {
      const row=[];
      for(let c=0;c<=range.e.c;c++) {
        const cell=sheet['!data']?.[r]?.[c] ?? sheet[r]?.[c] ?? sheet[XLSX.utils.encode_cell({r,c})];
        if(!cell) { row.push({v:'',t:'s'}); continue; }
        if(cell.v!==undefined || cell.f) populated++;
        if(populated>limits.cells) fail('Workbook exceeds 500,000 populated cells. Export fewer sheets.');
        let date=null;
        if(cell.t==='n' && XLSX.SSF.is_date(cell.z??'')) {
          const d=XLSX.SSF.parse_date_code(cell.v,{date1904:!!book.Workbook?.WBProps?.date1904});
          if(d && !(d.y===1900 && d.m===2 && d.d===29)) date=`${String(d.y).padStart(4,'0')}-${String(d.m).padStart(2,'0')}-${String(d.d).padStart(2,'0')}`;
        }
        row.push({v:cell.v===undefined?'':String(cell.v),t:cell.t,w:cell.w??'',percent:cell.t==='n' && /%/.test(cell.z??''),date,formula:!!cell.f});
      }
      rows.push(row);
    }
    return {name,hidden:!!book.Workbook?.Sheets?.[i]?.Hidden,rows,merges:sheet['!merges']??[]};
  });
}
self.onmessage=async ({data})=>{
  try {
    limits ??= (await import('/import-schema.js')).LIMITS;
    if(data.file.size>limits.fileBytes) fail('File exceeds 10 MiB. Export a smaller CSV or XLSX.');
    const extension=data.file.name.split('.').pop().toLowerCase();
    if(!['csv','xlsx'].includes(extension)) fail('Choose a .csv or .xlsx file. Macro-enabled files are not supported.');
    const bytes=new Uint8Array(await data.file.arrayBuffer());
    const sheets=extension==='csv'?parseCsv(bytes):await parseXlsx(bytes);
    const fingerprint=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),b=>b.toString(16).padStart(2,'0')).join('');
    postMessage({sheets,name:data.file.name,synthetic:fingerprint==='2cad194bfea8cdb69281c50669856484b1b33ac0a7cb3340c9c22e7f124bd52e'});
  } catch(error) { postMessage({error:error.message?.startsWith('Unsupported') || error.message?.match(/^(This|Workbook|File|CSV|Sheet|Choose|Encrypted|Macros)/) ? error.message : 'This file could not be read. Save a new, unencrypted CSV UTF-8 or XLSX with one rectangular table per sheet.'}); }
};
